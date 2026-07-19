"""
Pinecone Client — Vector Database

Provides:
- Pinecone index initialization
- Upsert, query, and delete operations
- Metadata-filtered similarity search
- Used by RAG service for knowledge base retrieval
"""

import logging
from pinecone import Pinecone, ServerlessSpec

from app.config import settings

logger = logging.getLogger(__name__)


# --- Global Client ---
pc: Pinecone | None = None
index = None


def init_pinecone():
    """Initialize Pinecone client and ensure index exists. Called on app startup."""
    global pc, index

    try:
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)

        # Create index if it doesn't exist
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        
        active_index_name = settings.PINECONE_INDEX_NAME
        if active_index_name not in existing_indexes:
            # Self-healing fallback to 'loan-kb' if it exists
            if "loan-kb" in existing_indexes:
                logger.warning(f"Configured Pinecone index '{active_index_name}' not found, but 'loan-kb' exists. Falling back to 'loan-kb'.")
                active_index_name = "loan-kb"
            else:
                logger.info(f"Index '{active_index_name}' not found. Attempting to create it...")
                try:
                    pc.create_index(
                        name=active_index_name,
                        dimension=384, # BAAI/bge-small-en-v1.5 dimension
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud="aws",
                            region=settings.PINECONE_ENVIRONMENT,
                        ),
                    )
                    logger.info(f"Successfully created Pinecone index: {active_index_name}")
                except Exception as ce:
                    logger.error(f"Failed to create Pinecone index '{active_index_name}': {ce}")
                    # Refresh list and check again. If it was created by another worker/race, it's fine.
                    existing_indexes = [idx.name for idx in pc.list_indexes()]
                    if active_index_name not in existing_indexes:
                        raise ce

        index = pc.Index(active_index_name)
        logger.info(f"✅ Successfully bound to Pinecone index: {active_index_name}")
    except Exception as e:
        logger.error(f"❌ Pinecone initialization failed: {e}")
        index = None
        raise e


def get_pinecone_index():
    """Get the Pinecone index. Raises if not initialized."""
    if index is None:
        raise RuntimeError("Pinecone not initialized. Call init_pinecone() first.")
    return index


# --- Operations ---
def upsert_vectors(vectors: list[dict]):
    """
    Upsert vectors into Pinecone.
    
    Args:
        vectors: List of dicts with keys: id, values, metadata
    
    Example:
        upsert_vectors([{
            "id": "kb_loan_001_chunk_0",
            "values": [0.1, 0.2, ...],  # 1536-dim embedding
            "metadata": {
                "record_id": "kb_loan_001",
                "category": "policy",
                "product_type": "personal_loan",
                "language": "en",
                "title": "Late Payment Policy",
                "content_preview": "First 200 chars..."
            }
        }])
    """
    idx = get_pinecone_index()
    # Pinecone recommends batches of 100
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]
        idx.upsert(vectors=batch)


def query_vectors(
    query_embedding: list[float],
    top_k: int = 10,
    filter_dict: dict | None = None,
    include_metadata: bool = True,
) -> list[dict]:
    """
    Query Pinecone for similar vectors.
    
    Args:
        query_embedding: 1536-dim query vector
        top_k: Number of results to return
        filter_dict: Pinecone metadata filter (e.g., {"category": "faq"})
        include_metadata: Whether to return metadata with results
    
    Returns:
        List of matches with id, score, and metadata
    """
    idx = get_pinecone_index()
    results = idx.query(
        vector=query_embedding,
        top_k=top_k,
        filter=filter_dict,
        include_metadata=include_metadata,
    )
    return [
        {
            "id": match.id,
            "score": match.score,
            "metadata": match.metadata if include_metadata else {},
        }
        for match in results.matches
    ]


def delete_vectors(ids: list[str]):
    """Delete vectors by ID."""
    idx = get_pinecone_index()
    idx.delete(ids=ids)


def delete_all_vectors():
    """Delete all vectors in the index. Use with caution."""
    idx = get_pinecone_index()
    idx.delete(delete_all=True)
