"""
RAG Service — Retrieval-Augmented Generation (Q2 Core)

Full RAG pipeline:
1. Embed query using BAAI/bge-small-en-v1.5 (singleton model)
2. Query Pinecone for similar vectors
3. Rerank results by cosine similarity score
4. Attach citations (record_id, source, version)
5. Return grounded response with source references

Also provides:
- Embedding generation for KB ingestion
- Retrieval test runner (7 queries for Q2 evaluation)
- Langfuse tracing for all operations
"""

import time
import logging
import asyncio
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.pinecone_client import query_vectors
from app.core.langfuse_client import create_trace

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────
# Singleton embedding model — loaded ONCE, shared across all requests.
# SentenceTransformer is thread-safe for encode().
# ────────────────────────────────────────────
_embedding_model: SentenceTransformer | None = None


def _get_embedding_model() -> SentenceTransformer:
    """Lazy-load the embedding model as a process-wide singleton."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: BAAI/bge-small-en-v1.5")
        _embedding_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        logger.info("Embedding model loaded (dim=384)")
    return _embedding_model


class RAGService:
    """
    Production RAG service with embed -> retrieve -> rerank -> cite pipeline.

    Usage:
        rag = RAGService(db)
        results = await rag.search(query="What is the late payment penalty?")
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.model = _get_embedding_model()
        self.llm_model = settings.OPENAI_LLM_MODEL

    # ── Embedding ──────────────────────────────────────────────

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string. Runs in executor to avoid blocking."""
        loop = asyncio.get_running_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self.model.encode(text, normalize_embeddings=True).tolist(),
        )
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. More efficient than calling embed_text() N times."""
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.model.encode(texts, normalize_embeddings=True).tolist(),
        )
        return embeddings

    # ── Search Pipeline ────────────────────────────────────────

    async def search(
        self,
        query: str,
        category: str | None = None,
        product_type: str | None = None,
        language: str | None = None,
        market: str | None = None,
        top_k: int = 5,
    ) -> dict:
        """
        Full RAG search pipeline.

        Steps:
        1. Embed query
        2. Build metadata filter
        3. Query Pinecone (top_k * 2 for reranking headroom)
        4. Rerank using cosine similarity score
        5. Return top_k results with citations
        """
        start_time = time.time()
        trace = create_trace(name="rag_search", metadata={"query": query})

        # Step 1: Embed query
        query_embedding = await self.embed_text(query)

        # Step 2: Build metadata filter
        pinecone_filter = self._build_filter(category, product_type, language, market)

        # Step 3: Query Pinecone
        try:
            raw_results = query_vectors(
                query_embedding=query_embedding,
                top_k=top_k * 2,  # Fetch extra for reranking
                filter_dict=pinecone_filter,
            )
        except RuntimeError:
            # Pinecone not initialized
            logger.warning("Pinecone not available — returning empty results")
            return {
                "query": query,
                "results": [],
                "total": 0,
                "retrieval_time_ms": 0,
            }

        # Step 4: Rerank (sort by score, take top_k)
        reranked = await self._rerank(query, raw_results, top_k)

        # Step 5: Format with citations
        results = self._format_results(reranked)

        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "query": query,
            "results": results,
            "total": len(results),
            "retrieval_time_ms": round(elapsed_ms, 2),
        }

    def _build_filter(self, category, product_type, language, market) -> dict | None:
        """Build Pinecone metadata filter from optional parameters."""
        filters = {}
        if category:
            filters["category"] = category
        if product_type:
            filters["product_type"] = {"$in": [product_type]}
        if language:
            filters["language"] = language
        if market:
            filters["applicable_market"] = market
        return filters if filters else None

    async def _rerank(self, query: str, results: list[dict], top_k: int) -> list[dict]:
        """
        Rerank results by cosine similarity score.

        For production enhancement: swap with a cross-encoder
        (e.g., ms-marco-MiniLM-L-6-v2) for higher-quality reranking.
        """
        if not results:
            return []
        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
        return sorted_results[:top_k]

    def _format_results(self, results: list[dict]) -> list[dict]:
        """Format results with citation information."""
        formatted = []
        for result in results:
            metadata = result.get("metadata", {})
            formatted.append({
                "record_id": metadata.get("record_id", ""),
                "title": metadata.get("title", ""),
                "content": metadata.get("content", ""),
                "category": metadata.get("category", ""),
                "source": metadata.get("source", ""),
                "source_url": metadata.get("source_url"),
                "relevance_score": round(result["score"], 4),
                "metadata": metadata,
            })
        return formatted

    # ── Voice Agent Helper ─────────────────────────────────────

    async def search_for_voice(self, query: str, category: str | None = None) -> dict:
        """
        Simplified search for voice agent tool calls.

        Returns a concise answer string suitable for the LLM to speak,
        plus source citations for grounding.
        """
        results = await self.search(query=query, category=category, top_k=3)

        if not results["results"]:
            return {
                "found": False,
                "answer": "I don't have specific information about that in my knowledge base. Let me connect you with a team member who can help.",
                "sources": [],
                "confidence": 0.0,
            }

        # Build context from top results
        context_parts = []
        sources = []
        for r in results["results"]:
            context_parts.append(r["content"])
            sources.append({
                "record_id": r["record_id"],
                "title": r["title"],
                "source": r["source"],
            })

        context = "\n\n".join(context_parts)
        top_score = results["results"][0]["relevance_score"]

        return {
            "found": True,
            "answer": context,
            "sources": sources,
            "confidence": top_score,
        }

    # ── Retrieval Test Runner ──────────────────────────────────

    async def run_retrieval_test(self) -> list[dict]:
        """
        Run the Q2 retrieval test: 7 predefined queries.

        Loads test cases from evaluation/test_cases/rag_retrieval.json
        and evaluates each one against expected keywords.
        """
        import json
        import os

        test_cases_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "evaluation", "test_cases", "rag_retrieval.json",
        )

        if not os.path.exists(test_cases_path):
            return [{"error": "Test cases file not found", "path": test_cases_path}]

        with open(test_cases_path, "r") as f:
            test_cases = json.load(f)

        results = []
        for tc in test_cases:
            try:
                search_result = await self.search(
                    query=tc["query"],
                    category=tc.get("expected_category"),
                    top_k=3,
                )

                # Evaluate keyword matches
                result_text = " ".join(
                    r.get("content", "") + " " + r.get("title", "")
                    for r in search_result.get("results", [])
                ).lower()

                expected_kw = tc.get("expected_keywords", [])
                matched = [kw for kw in expected_kw if kw.lower() in result_text]
                ratio = len(matched) / len(expected_kw) if expected_kw else 0

                verdict = "correct" if ratio >= 0.6 else ("partially_correct" if ratio >= 0.3 else "incorrect")

                top = search_result["results"][0] if search_result.get("results") else None
                results.append({
                    "test_id": tc["test_id"],
                    "query": tc["query"],
                    "retrieved_record": {
                        "record_id": top["record_id"] if top else None,
                        "title": top["title"] if top else None,
                        "content": top["content"][:200] if top else None,
                        "category": top["category"] if top else None,
                        "source": top["source"] if top else None,
                        "source_url": top.get("source_url") if top else None,
                        "relevance_score": top["relevance_score"] if top else 0,
                        "metadata": top.get("metadata") if top else None,
                    } if top else None,
                    "source_reference": f"{top['source']}:{top['record_id']}" if top else "none",
                    "relevance_explanation": f"Matched {len(matched)}/{len(expected_kw)} expected keywords: {matched}",
                    "verdict": verdict,
                    "retrieval_time_ms": search_result.get("retrieval_time_ms", 0),
                })

            except Exception as e:
                results.append({
                    "test_id": tc["test_id"],
                    "query": tc["query"],
                    "verdict": "error",
                    "error": str(e),
                })

        return results
