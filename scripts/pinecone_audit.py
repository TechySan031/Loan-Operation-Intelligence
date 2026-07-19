"""Pinecone-only deep audit — list all vectors, metadata, IDs."""
import sys, os
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_path)
for p in list(sys.path):
    if p != backend_path and os.path.exists(os.path.join(p, "app", "config.py")):
        sys.path.remove(p)

from app.config import settings
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index(settings.PINECONE_INDEX_NAME)

print(f"Index: {settings.PINECONE_INDEX_NAME}")
stats = index.describe_index_stats()
print(f"Total vectors: {stats.total_vector_count}")
print(f"Dimension: {stats.dimension}")
print(f"Namespaces: {dict(stats.namespaces)}")

# Try listing with pagination
print("\n--- Listing vector IDs ---")
try:
    results = index.list(limit=100)
    all_ids = []
    for page in results:
        if isinstance(page, list):
            all_ids.extend(page)
        elif isinstance(page, str):
            all_ids.append(page)
    if not all_ids:
        # Try namespace
        results = index.list(namespace="", limit=100)
        for page in results:
            if isinstance(page, list):
                all_ids.extend(page)
            elif isinstance(page, str):
                all_ids.append(page)
    print(f"Vector IDs from list(): {all_ids}")
except Exception as e:
    print(f"list() error: {e}")

# Brute force: query with random vectors to discover IDs
print("\n--- Discovery via query ---")
model = SentenceTransformer("BAAI/bge-small-en-v1.5")

queries = [
    "late payment penalty fee",
    "personal loan interest rate",
    "home loan eligibility",
    "EMI payment methods UPI",
    "prepayment foreclosure charges",
    "grace period",
    "business loan",
    "hardship program",
    "escalation criteria",
    "compliance RBI guidelines",
    "objection handling dispute",
    "loan restructuring tenure",
]

discovered_ids = set()
for q in queries:
    emb = model.encode(q, normalize_embeddings=True).tolist()
    results = index.query(vector=emb, top_k=10, include_metadata=True)
    for m in results.matches:
        discovered_ids.add(m.id)

print(f"Total unique IDs discovered: {len(discovered_ids)}")
for vid in sorted(discovered_ids):
    print(f"  {vid}")

# Fetch all discovered vectors with full metadata
print("\n--- Full vector details ---")
if discovered_ids:
    fetch = index.fetch(ids=list(discovered_ids))
    for vid, vec in fetch.vectors.items():
        meta = vec.metadata or {}
        dim = len(vec.values) if vec.values else 0
        print(f"\n  ID: {vid}")
        print(f"    dim: {dim}")
        for k, v in meta.items():
            val_str = str(v)[:100]
            print(f"    {k}: {val_str}")

# Test: query with a real embedding
print("\n--- Semantic search test ---")
test_q = "What is the late payment penalty?"
emb = model.encode(test_q, normalize_embeddings=True).tolist()
results = index.query(vector=emb, top_k=5, include_metadata=True)
print(f"Query: '{test_q}'")
for i, m in enumerate(results.matches):
    meta = m.metadata or {}
    print(f"  [{i}] id={m.id}, score={m.score:.4f}, record_id={meta.get('record_id','?')}, title={meta.get('title','?')[:60]}")

print("\nDone.")
