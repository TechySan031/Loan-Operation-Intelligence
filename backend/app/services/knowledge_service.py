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
        logger.info("Starting Ingestion: Beginning knowledge base bulk upload...")
        ingested = 0
        chunks_created = 0
        pii_flagged = 0
        errors = []
        vectors_to_upsert = []
        
        db_records = []
        texts_to_embed = []
        chunk_mappings = []

        for record in records:
            try:
                # Idempotency: Clean up existing database chunks and Pinecone vectors for this document
                existing_query = select(KBRecord).where(KBRecord.parent_doc_id == record.record_id)
                existing_result = await self.db.execute(existing_query)
                existing_records = existing_result.scalars().all()
                if existing_records:
                    logger.info(f"Idempotency Cleanup: Removing {len(existing_records)} existing chunks for '{record.record_id}'...")
                    vids_to_delete = [r.embedding_id for r in existing_records if r.embedding_id]
                    if vids_to_delete:
                        try:
                            delete_vectors(vids_to_delete)
                        except Exception as pe:
                            logger.warning(f"Failed to delete old Pinecone vectors for '{record.record_id}': {pe}")
                    for r in existing_records:
                        await self.db.delete(r)
                    await self.db.flush()

                # Stage 1: PII Detection
                logger.info(f"PII detection: Checking record '{record.record_id}'...")
                contains_pii = False
                if detect_pii_flag:
                    pii_results = detect_pii(record.content)
                    if pii_results:
                        contains_pii = True
                        pii_flagged += 1

                # Stage 2: Chunking
                logger.info(f"Chunking: Splitting record '{record.record_id}'...")
                chunks = chunk_text(
                    text=record.content,
                    category=record.category,
                )

                for i, chunk in enumerate(chunks):
                    chunk_record_id = f"{record.record_id}_chunk_{i}" if len(chunks) > 1 else record.record_id
                    embedding_id = f"vec_{chunk_record_id}"

                    # Run chunk-level PII detection/redaction only if the parent contains PII
                    chunk_content_clean = chunk["text"]
                    if contains_pii:
                        chunk_pii_results = detect_pii(chunk["text"])
                        chunk_content_clean = redact_pii(chunk["text"], chunk_pii_results)

                    # Stage 3: DB Record creation (staged in list)
                    db_record = KBRecord(
                        id=uuid.uuid4(),
                        record_id=chunk_record_id,
                        title=record.title,
                        content=chunk["text"],
                        content_clean=chunk_content_clean,
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
                    db_records.append(db_record)
                    chunks_created += 1

                    if embed:
                        texts_to_embed.append(chunk["text"])
                        chunk_mappings.append({
                            "embedding_id": embedding_id,
                            "chunk_record_id": chunk_record_id,
                            "title": record.title,
                            "chunk_text": chunk["text"],
                            "category": record.category,
                            "subcategory": record.subcategory,
                            "source": record.source,
                            "source_url": record.source_url,
                            "language": record.language,
                            "metadata": record.metadata,
                        })

                ingested += 1

            except Exception as e:
                errors.append({"record_id": record.record_id, "error": str(e)})
                logger.error(f"Failed to process record {record.record_id} during staging: {e}", exc_info=True)

        # Stage 4: Embedding (Batch call)
        if embed and texts_to_embed:
            logger.info(f"Embedding: Generating embeddings for {len(texts_to_embed)} chunks in batch...")
            try:
                embeddings = await self.rag.embed_batch(texts_to_embed)
                
                for mapping, embedding in zip(chunk_mappings, embeddings):
                    vectors_to_upsert.append({
                        "id": mapping["embedding_id"],
                        "values": embedding,
                        "metadata": {
                            "record_id": mapping["chunk_record_id"],
                            "title": mapping["title"],
                            "content": mapping["chunk_text"][:500],  # Preview
                            "category": mapping["category"],
                            "subcategory": mapping["subcategory"] or "",
                            "source": mapping["source"],
                            "source_url": mapping["source_url"] or "",
                            "language": mapping["language"],
                            "product_type": mapping["metadata"].get("product_type", []) if mapping["metadata"] else [],
                            "applicable_market": mapping["metadata"].get("applicable_market", "all") if mapping["metadata"] else "all",
                        },
                    })
            except Exception as e:
                logger.error(f"Embedding failed: {e}", exc_info=True)
                raise Exception(f"Batch embedding generation failed: {str(e)}")

        # Add staged records to session
        if db_records:
            for rec in db_records:
                self.db.add(rec)

        # Stage 5: DB Flush
        logger.info("DB Flush: Flushing records to database...")
        try:
            await self.db.flush()
        except Exception as e:
            logger.error(f"DB Flush failed: {e}", exc_info=True)
            raise Exception(f"Database flush failed: {str(e)}")

        # Stage 6: DB Commit
        logger.info("DB Commit: Committing database transaction...")
        try:
            await self.db.commit()
        except Exception as e:
            logger.error(f"DB Commit failed: {e}", exc_info=True)
            raise Exception(f"Database commit failed: {str(e)}")

        # Stage 7: Pinecone Upsert
        if vectors_to_upsert:
            logger.info(f"Pinecone Upsert: Upserting {len(vectors_to_upsert)} vectors to index...")
            try:
                upsert_vectors(vectors_to_upsert)
            except Exception as e:
                logger.error(f"Pinecone Upsert failed: {e}", exc_info=True)
                raise Exception(f"Pinecone vector upsert failed: {str(e)}")

        logger.info("Finished: Ingestion pipeline completed successfully.")

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
