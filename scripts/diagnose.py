"""
Comprehensive Backend Diagnostic Script
Audits Pinecone, PostgreSQL, Embeddings, and RAG pipeline.
"""
import sys
import os

# Force the correct backend on the path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_path)
# Remove any other paths that might have 'app' packages
for p in list(sys.path):
    if p != backend_path and os.path.exists(os.path.join(p, "app", "config.py")):
        sys.path.remove(p)

import asyncio
import json
from app.config import settings

print("=" * 70)
print("BACKEND DIAGNOSTIC REPORT")
print("=" * 70)

# ────────────────────────────────────────────
# 1. CONFIG AUDIT
# ────────────────────────────────────────────
print("\n[1] CONFIG AUDIT")
print(f"  PINECONE_API_KEY: {'SET (' + settings.PINECONE_API_KEY[:10] + '...)' if settings.PINECONE_API_KEY else 'MISSING'}")
print(f"  PINECONE_INDEX_NAME: {settings.PINECONE_INDEX_NAME}")
print(f"  PINECONE_ENVIRONMENT: {settings.PINECONE_ENVIRONMENT}")
print(f"  OPENAI_API_KEY: {'SET' if settings.OPENAI_API_KEY else 'MISSING'}")
print(f"  DATABASE_URL: {settings.DATABASE_URL}")
print(f"  REDIS_URL: {settings.REDIS_URL}")

# ────────────────────────────────────────────
# 2. PINECONE AUDIT
# ────────────────────────────────────────────
print("\n[2] PINECONE AUDIT")
try:
    from pinecone import Pinecone
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    
    # List all indexes
    indexes = pc.list_indexes()
    print(f"  Available indexes: {[idx.name for idx in indexes]}")
    
    for idx_info in indexes:
        if idx_info.name == settings.PINECONE_INDEX_NAME:
            print(f"  Target index: {idx_info.name}")
            print(f"    Dimension: {idx_info.dimension}")
            print(f"    Metric: {idx_info.metric}")
            print(f"    Host: {idx_info.host}")
            
            # Check dimension mismatch
            if idx_info.dimension != 384:
                print(f"  ⚠️  DIMENSION MISMATCH: Index has {idx_info.dimension}, BGE needs 384!")
            else:
                print(f"  ✅ Dimension correct (384)")
    
    # Get index stats
    index = pc.Index(settings.PINECONE_INDEX_NAME)
    stats = index.describe_index_stats()
    print(f"\n  Index Stats:")
    print(f"    Total vectors: {stats.total_vector_count}")
    print(f"    Namespaces: {dict(stats.namespaces)}")
    print(f"    Dimension: {stats.dimension}")
    
    # List ALL vectors (fetch by listing)
    print(f"\n  Vector ID Listing:")
    try:
        # Try to list vector IDs
        id_list = index.list()
        all_ids = []
        for page in id_list:
            if isinstance(page, list):
                all_ids.extend(page)
            elif isinstance(page, str):
                all_ids.append(page)
        print(f"    Found {len(all_ids)} vector IDs: {all_ids[:20]}")
    except Exception as e:
        print(f"    list() failed: {e}")
        
    # Try fetching some known IDs
    print(f"\n  Fetching vectors by known IDs:")
    test_ids = [
        "vec_kb_product_personal_loan_001",
        "vec_kb_policy_late_payment_001",
        "vec_kb_faq_payment_methods_001",
        "kb_product_personal_loan_001",
        "kb_loan_002",
    ]
    try:
        fetch_result = index.fetch(ids=test_ids)
        print(f"    Requested: {test_ids}")
        found = list(fetch_result.vectors.keys())
        print(f"    Found: {found}")
        for vid, vec in fetch_result.vectors.items():
            meta = vec.metadata if vec.metadata else {}
            dim = len(vec.values) if vec.values else 0
            print(f"      {vid}: dim={dim}, metadata_keys={list(meta.keys())}, record_id={meta.get('record_id','?')}, title={meta.get('title','?')[:50]}")
    except Exception as e:
        print(f"    Fetch failed: {e}")

    # Do a dummy query to see what comes back
    print(f"\n  Dummy Query Test (zero vector):")
    try:
        dummy_results = index.query(
            vector=[0.0] * 384,
            top_k=5,
            include_metadata=True,
        )
        for m in dummy_results.matches:
            meta = m.metadata or {}
            print(f"    {m.id}: score={m.score:.4f}, record_id={meta.get('record_id','?')}, title={meta.get('title','?')[:60]}")
    except Exception as e:
        print(f"    Dummy query failed: {e}")
        # Try with 1536 in case old index
        try:
            dummy_results = index.query(
                vector=[0.0] * 1536,
                top_k=5,
                include_metadata=True,
            )
            print(f"    ⚠️  Query with 1536 dims WORKED! Index dimension is 1536, not 384!")
            for m in dummy_results.matches:
                meta = m.metadata or {}
                print(f"      {m.id}: score={m.score:.4f}, record_id={meta.get('record_id','?')}")
        except Exception as e2:
            print(f"    1536 query also failed: {e2}")

except Exception as e:
    print(f"  ❌ Pinecone error: {e}")
    import traceback
    traceback.print_exc()

# ────────────────────────────────────────────
# 3. EMBEDDING AUDIT
# ────────────────────────────────────────────
print("\n[3] EMBEDDING AUDIT")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    
    test_text = "What is the late payment penalty?"
    embedding = model.encode(test_text, normalize_embeddings=True).tolist()
    print(f"  Model: BAAI/bge-small-en-v1.5")
    print(f"  Test text: '{test_text}'")
    print(f"  Embedding dimension: {len(embedding)}")
    print(f"  First 5 values: {embedding[:5]}")
    print(f"  Norm (should be ~1.0): {sum(x*x for x in embedding)**0.5:.6f}")
    
    # Test batch
    texts = ["payment", "loan", "penalty"]
    batch = model.encode(texts, normalize_embeddings=True).tolist()
    print(f"  Batch test: {len(batch)} embeddings, dims={[len(e) for e in batch]}")
    
    if len(embedding) == 384:
        print(f"  ✅ Embedding dimension correct (384)")
    else:
        print(f"  ⚠️  DIMENSION MISMATCH: Got {len(embedding)}, expected 384")

except Exception as e:
    print(f"  ❌ Embedding error: {e}")

# ────────────────────────────────────────────
# 4. POSTGRESQL AUDIT
# ────────────────────────────────────────────
print("\n[4] POSTGRESQL AUDIT")

async def audit_postgres():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker
    
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with Session() as db:
        # Check tables
        result = await db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        tables = [row[0] for row in result.all()]
        print(f"  Tables: {tables}")
        
        # Check KB records
        result = await db.execute(text("SELECT COUNT(*) FROM kb_records"))
        count = result.scalar()
        print(f"  KB Records count: {count}")
        
        if count > 0:
            result = await db.execute(text(
                "SELECT record_id, title, category, embedding_id, language FROM kb_records ORDER BY created_at DESC LIMIT 20"
            ))
            rows = result.all()
            print(f"  KB Records (most recent):")
            for r in rows:
                print(f"    {r[0]}: title='{r[1][:40]}', cat={r[2]}, embed_id={r[3]}, lang={r[4]}")
        
        # Check for duplicates
        result = await db.execute(text(
            "SELECT record_id, COUNT(*) FROM kb_records GROUP BY record_id HAVING COUNT(*) > 1"
        ))
        dupes = result.all()
        if dupes:
            print(f"  ⚠️  DUPLICATES found: {dupes}")
        else:
            print(f"  ✅ No duplicate record_ids")
        
        # Check calls table
        result = await db.execute(text("SELECT COUNT(*) FROM calls"))
        print(f"  Calls count: {result.scalar()}")
        
        # Check nudges table
        result = await db.execute(text("SELECT COUNT(*) FROM nudges"))
        print(f"  Nudges count: {result.scalar()}")
        
        # Check business_rules table
        result = await db.execute(text("SELECT COUNT(*) FROM business_rules"))
        print(f"  Business Rules count: {result.scalar()}")
    
    await engine.dispose()

asyncio.run(audit_postgres())

# ────────────────────────────────────────────
# 5. RAG PIPELINE END-TO-END TRACE
# ────────────────────────────────────────────
print("\n[5] RAG PIPELINE END-TO-END TRACE")

async def trace_rag_pipeline():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from app.services.rag_service import RAGService
    import time
    
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession)
    
    async with Session() as db:
        rag = RAGService(db)
        
        test_queries = [
            "What is the late payment penalty?",
            "How can I pay my EMI?",
            "What is the personal loan interest rate?",
        ]
        
        for query in test_queries:
            print(f"\n  Query: '{query}'")
            
            # Step 1: Embed
            t0 = time.time()
            embedding = await rag.embed_text(query)
            t1 = time.time()
            print(f"    [Embed] dim={len(embedding)}, time={((t1-t0)*1000):.1f}ms")
            
            # Step 2: Pinecone query
            try:
                from app.core.pinecone_client import query_vectors, init_pinecone, index as pc_index
                
                # Init if needed
                if pc_index is None:
                    init_pinecone()
                
                t2 = time.time()
                raw_results = query_vectors(
                    query_embedding=embedding,
                    top_k=5,
                    filter_dict=None,
                )
                t3 = time.time()
                print(f"    [Pinecone] {len(raw_results)} results, time={((t3-t2)*1000):.1f}ms")
                
                for i, r in enumerate(raw_results):
                    meta = r.get("metadata", {})
                    print(f"      [{i}] id={r['id']}, score={r['score']:.4f}, record_id={meta.get('record_id','?')}, title={meta.get('title','?')[:50]}")
                
            except Exception as e:
                print(f"    [Pinecone] ERROR: {e}")
    
    await engine.dispose()

asyncio.run(trace_rag_pipeline())

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
