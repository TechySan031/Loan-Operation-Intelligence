"""
Knowledge Service — KB Ingestion & CRUD (Q2)

Handles:
- Bulk record ingestion (parse → clean → PII detect → chunk → embed → store)
- CRUD operations on KB records
- Re-embedding on content updates
- Statistics and reporting

Ingestion pipeline:
1. Validate incoming records
2. Run PII detection (Presidio) → flag and create clean version
3. Chunk long content using configured strategy
4. Generate embeddings (OpenAI)
5. Store records in PostgreSQL
6. Upsert vectors in Pinecone
"""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.knowledge import KBRecord
from app.schemas.knowledge import KBRecordCreate, KBRecordUpdate
from app.services.rag_service import RAGService
from app.utils.pii import detect_pii, redact_pii
from app.utils.chunking import chunk_text
from app.core.pinecone_client import upsert_vectors, delete_vectors

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Knowledge base management service.
    
    Usage:
        service = KnowledgeService(db)
        await service.ingest_records(records=[...], embed=True, detect_pii=True)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rag = RAGService(db)

    async def ingest_records(
        self,
        records: list[KBRecordCreate],
        embed: bool = True,
        detect_pii_flag: bool = True,
    ) -> dict:
        """
        Bulk ingest KB records through the full pipeline.
        
        Returns summary: {ingested: int, chunks_created: int, pii_flagged: int, errors: list}
        """
        ingested = 0
        chunks_created = 0
        pii_flagged = 0
        errors = []
        vectors_to_upsert = []

        for record in records:
            try:
                # Step 1: PII Detection
                contains_pii = False
                content_clean = record.content
                if detect_pii_flag:
                    pii_results = detect_pii(record.content)
                    if pii_results:
                        contains_pii = True
                        content_clean = redact_pii(record.content, pii_results)
                        pii_flagged += 1

                # Step 2: Chunk content
                chunks = chunk_text(
                    text=record.content,
                    category=record.category,
                )

                for i, chunk in enumerate(chunks):
                    chunk_record_id = f"{record.record_id}_chunk_{i}" if len(chunks) > 1 else record.record_id
                    embedding_id = f"vec_{chunk_record_id}"

                    # Step 3: Create DB record
                    db_record = KBRecord(
                        id=uuid.uuid4(),
                        record_id=chunk_record_id,
                        title=record.title,
                        content=chunk["text"],
                        content_clean=redact_pii(chunk["text"], detect_pii(chunk["text"])) if contains_pii else chunk["text"],
                        category=record.category,
                        subcategory=record.subcategory,
                        source=record.source,
                        source_url=record.source_url,
                        version=record.version,
                        contains_pii=contains_pii,
                        metadata_=record.metadata,
                        chunk_id=f"chunk_{i}",
                        parent_doc_id=record.record_id,
                        embedding_id=embedding_id,
                        token_count=chunk["token_count"],
                        language=record.language,
                    )
                    self.db.add(db_record)
                    chunks_created += 1

                    # Step 4: Prepare vector for Pinecone
                    if embed:
                        embedding = await self.rag.embed_text(chunk["text"])
                        vectors_to_upsert.append({
                            "id": embedding_id,
                            "values": embedding,
                            "metadata": {
                                "record_id": chunk_record_id,
                                "title": record.title,
                                "content": chunk["text"][:500],  # Preview
                                "category": record.category,
                                "subcategory": record.subcategory or "",
                                "source": record.source,
                                "source_url": record.source_url or "",
                                "language": record.language,
                                "product_type": record.metadata.get("product_type", []) if record.metadata else [],
                                "applicable_market": record.metadata.get("applicable_market", "all") if record.metadata else "all",
                            },
                        })

                ingested += 1

            except Exception as e:
                errors.append({"record_id": record.record_id, "error": str(e)})
                logger.error(f"Failed to ingest {record.record_id}: {e}")

        # Step 5: Commit to DB
        await self.db.flush()

        # Step 6: Upsert vectors to Pinecone
        if vectors_to_upsert:
            upsert_vectors(vectors_to_upsert)

        return {
            "ingested": ingested,
            "chunks_created": chunks_created,
            "pii_flagged": pii_flagged,
            "vectors_upserted": len(vectors_to_upsert),
            "errors": errors,
        }

    async def list_records(
        self,
        category: str | None = None,
        language: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """List KB records with optional filters and pagination."""
        query = select(KBRecord)
        count_query = select(func.count(KBRecord.id))

        if category:
            query = query.where(KBRecord.category == category)
            count_query = count_query.where(KBRecord.category == category)
        if language:
            query = query.where(KBRecord.language == language)
            count_query = count_query.where(KBRecord.language == language)

        total = (await self.db.execute(count_query)).scalar()
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        records = result.scalars().all()

        return {
            "records": records,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_record(self, record_id: str) -> KBRecord | None:
        """Get a single KB record by record_id."""
        result = await self.db.execute(
            select(KBRecord).where(KBRecord.record_id == record_id)
        )
        return result.scalar_one_or_none()

    async def update_record(self, record_id: str, update: KBRecordUpdate) -> KBRecord | None:
        """Update a KB record. Re-embeds if content changes."""
        record = await self.get_record(record_id)
        if not record:
            return None

        update_data = update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(record, key, value)

        # Re-embed if content changed
        if "content" in update_data:
            embedding = await self.rag.embed_text(update_data["content"])
            upsert_vectors([{
                "id": record.embedding_id,
                "values": embedding,
                "metadata": {
                    "record_id": record.record_id,
                    "title": record.title,
                    "content": record.content[:500],
                    "category": record.category,
                },
            }])

        await self.db.flush()
        return record

    async def delete_record(self, record_id: str):
        """Delete a KB record and its Pinecone vector."""
        record = await self.get_record(record_id)
        if record:
            if record.embedding_id:
                delete_vectors([record.embedding_id])
            await self.db.delete(record)
            await self.db.flush()

    async def get_stats(self) -> dict:
        """Get KB statistics."""
        total = (await self.db.execute(select(func.count(KBRecord.id)))).scalar()
        
        # Category breakdown
        cat_query = select(KBRecord.category, func.count(KBRecord.id)).group_by(KBRecord.category)
        cat_result = await self.db.execute(cat_query)
        categories = {row[0]: row[1] for row in cat_result.all()}

        return {
            "total_records": total,
            "categories": categories,
        }
