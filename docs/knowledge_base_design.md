# Knowledge Base Design (Q2)

## Schema

See `backend/app/models/knowledge.py` for the full ORM model.

## Category Taxonomy

| Category | Subcategories | Description |
|----------|--------------|-------------|
| product | personal_loan, home_loan, auto_loan, business_loan | Loan product information |
| policy | payment_terms, late_payment, prepayment, foreclosure, grace_period | Business policies |
| faq | payment_methods, account_access, statement_queries | Frequently asked questions |
| objection | financial_difficulty, dispute_charges, service_complaint | Objection handling scripts |
| compliance | rbi_guidelines, fair_practice_code, disclosure_requirements | Regulatory requirements |
| payment | methods, hardship_programs, restructuring, emi_holiday | Payment information |
| escalation | criteria, transfer_scripts, supervisor_protocols | Escalation handling |

## Chunking Strategy

| Category | Max Tokens | Overlap | Atomic |
|----------|-----------|---------|--------|
| faq | 500 | 0 | Yes |
| objection | 500 | 0 | Yes |
| policy | 400 | 50 | No |
| product | 500 | 75 | No |
| compliance | 300 | 50 | No |

## Retrieval Pipeline

Query → Embed (OpenAI) → Pinecone Search (top_k=10, metadata filter) → Rerank (top 3) → Cite → Response

## PII Detection

Using Microsoft Presidio to detect and redact: PERSON, PHONE_NUMBER, EMAIL_ADDRESS, CREDIT_CARD, LOCATION

## Retrieval Test Results

See `evaluation/results/` for test outputs.
