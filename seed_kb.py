import json
import requests

API_URL = "https://loan-operation-intelligence-production.up.railway.app/api/knowledge/ingest"

with open("data/knowledge_base/loan_kb_en.json", "r", encoding="utf-8") as f:
    records = json.load(f)

payload = {
    "records": records,
    "embed": True,
    "detect_pii": True
}

print(f"Uploading {len(records)} records...")

response = requests.post(API_URL, json=payload)

import sys
# Set stdout encoding to utf-8 for Windows console support
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Status Code:", response.status_code)
print("Response:")
try:
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception:
    print(response.text)
print("=" * 60)