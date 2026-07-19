# Voice Agent Design (Q1)

## Platform: Vapi.ai

## Conversation Flow

greeting → verify_identity → payment_reminder → handle_objection/answer_question → offer_options → collect_commitment/schedule_callback/escalate → wrap_up

## Tools (Function Calls)

| Tool | Description | Backend Handler |
|------|-------------|----------------|
| search_knowledge_base | RAG search for policies, FAQs, objections | RAG Service |
| lookup_borrower | Verify borrower identity | Mock CRM |
| schedule_callback | Schedule follow-up call | Call Service |
| record_payment_commitment | Record payment promise | Call Service |
| escalate_to_human | Transfer to human agent | Call Service |
| check_eligibility | Check hardship program eligibility | Rule Engine |

## Test Scenarios

See `evaluation/test_cases/voice_scenarios.json`
