"""
KB Ingestion Script

Loads knowledge base content from data/ directory,
processes through the ingestion pipeline, and populates
PostgreSQL + Pinecone.

Usage:
    python -m scripts.ingest_kb
"""

import asyncio
import json
import sys
import os

# Force the correct backend on the path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_path)
for p in list(sys.path):
    if p != backend_path and os.path.exists(os.path.join(p, "app", "config.py")):
        sys.path.remove(p)


async def main():
    """Ingest all KB records from data/knowledge_base/ directory."""
    from app.core.database import init_db, async_session_factory
    from app.core.pinecone_client import init_pinecone
    from app.services.knowledge_service import KnowledgeService
    from app.schemas.knowledge import KBRecordCreate

    # Initialize infrastructure
    await init_db()
    init_pinecone()

    # Load KB records from JSON files
    kb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_base")
    
    all_records = []
    for filename in os.listdir(kb_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(kb_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_records.extend(data)
                else:
                    all_records.append(data)

    print(f"Found {len(all_records)} KB records to ingest")

    # Convert to Pydantic models
    records = [KBRecordCreate(**record) for record in all_records]

    # Ingest
    async with async_session_factory() as session:
        from sqlalchemy import delete
        from app.models.knowledge import KBRecord
        
        # Clear existing knowledge records to prevent duplicate key violations on retry
        await session.execute(delete(KBRecord))
        
        service = KnowledgeService(session)
        result = await service.ingest_records(
            records=records,
            embed=True,
            detect_pii_flag=False,
        )
        await session.commit()

    print(f"Ingestion complete: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
