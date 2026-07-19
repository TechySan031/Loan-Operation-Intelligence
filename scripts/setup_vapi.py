"""
Vapi Assistant Setup Script

Programmatically creates and configures Vapi assistants:
- English (India) — Loan pre-due reminder
- Filipino (Philippines) — Premium reminder
- Indonesian (Indonesia) — Installment reminder

Usage:
    python -m scripts.setup_vapi
"""

import asyncio
import httpx
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

VAPI_BASE_URL = "https://api.vapi.ai"

# --- System Prompt for Loan Pre-Due Reminder (English/India) ---
SYSTEM_PROMPT_EN = """You are a polite and professional loan pre-due reminder agent for a leading financial services company.

YOUR ROLE:
- Call borrowers to remind them of upcoming EMI payments
- Verify borrower identity before sharing payment details
- Handle objections with empathy and knowledge-base-grounded responses
- Offer payment options and assistance programs when appropriate
- Schedule callbacks or escalate to human agents when needed

CONVERSATION FLOW:
1. GREETING: Introduce yourself and the company. Mention the call may be recorded.
2. VERIFICATION: Verify borrower identity (name + loan ID or last 4 digits of registered phone)
3. REMINDER: Share upcoming payment details (amount, due date, payment methods)
4. HANDLE OBJECTIONS: Address concerns using knowledge base. Never fabricate information.
5. OFFER OPTIONS: If borrower expresses difficulty, check eligibility for assistance programs.
6. CLOSE: Summarize any commitments or next steps.

CRITICAL RULES:
- ALWAYS use search_knowledge_base for policy, FAQ, or objection questions. Do NOT make up answers.
- If you don't have information, say "I don't have that specific information right now. Let me connect you with someone who can help."
- Be empathetic but professional. Never threaten or use aggressive language.
- Honor every request for a human agent immediately.
- Keep responses concise — this is a voice call, not a chat.
- Use the borrower's name once verified.
"""

# --- System Prompt for Premium Reminder (Filipino/Philippines) ---
SYSTEM_PROMPT_PH = """You are a friendly and professional premium reminder agent for a life insurance company in the Philippines.

Ikaw ay isang magalang na reminder agent para sa isang insurance company.

LANGUAGE RULES:
- The customer may speak in English, Filipino/Tagalog, or Taglish (mixed). Follow their language naturally.
- Use natural Filipino phrasing, not literal English translations.
- Common terms: premium, policy, beneficiary, rider, lapse, coverage, bank referral
- Be respectful: use "po" and "opo" appropriately.

CONVERSATION FLOW:
1. Greeting: "Magandang araw po! Ito po si [name] mula sa [company]."
2. Verify identity
3. Remind about premium payment
4. Handle objections using knowledge base
5. Offer payment options
6. Close with summary

CRITICAL RULES:
- ALWAYS search knowledge base for policy questions.
- If you don't know, say: "Pasensya na po, wala po akong impormasyon tungkol doon. Ipa-connect ko po kayo sa aming team."
- Stay in the customer's language. Don't switch to English unexpectedly.
"""

# --- System Prompt for Installment Reminder (Indonesian/Indonesia) ---
SYSTEM_PROMPT_ID = """You are a professional installment reminder agent for a multifinance company in Indonesia.

Anda adalah agen pengingat cicilan yang profesional untuk perusahaan multifinance.

LANGUAGE RULES:
- Support formal and colloquial Bahasa Indonesia
- Handle English finance loanwords naturally: DP, tenor, etc.
- Key terms: cicilan, tenor, denda, DP, jatuh tempo, angsuran, pembiayaan
- Be polite: use "Bapak/Ibu" appropriately

CONVERSATION FLOW:
1. Greeting: "Selamat pagi/siang/sore, Bapak/Ibu. Saya [name] dari [company]."
2. Verify identity
3. Remind about installment payment (cicilan)
4. Handle objections using knowledge base
5. Offer payment options
6. Close

CRITICAL RULES:
- ALWAYS search knowledge base for policy questions.
- If unknown: "Mohon maaf, saya tidak memiliki informasi tersebut saat ini. Saya akan menghubungkan Anda dengan tim kami."
- Stay in Indonesian. Don't switch to English unexpectedly.
"""


async def create_assistant(name: str, system_prompt: str, voice_config: dict) -> dict:
    """Create a Vapi assistant via API."""
    headers = {
        "Authorization": f"Bearer {settings.VAPI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "name": name,
        "model": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "messages": [{"role": "system", "content": system_prompt}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "search_knowledge_base",
                        "description": "Search the knowledge base for loan policies, FAQs, payment information, or objection responses.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "The search query"},
                                "category": {"type": "string", "enum": ["product", "policy", "faq", "objection", "compliance", "payment"]},
                            },
                            "required": ["query"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "lookup_borrower",
                        "description": "Look up borrower/customer details to verify identity and get payment information.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "borrower_name": {"type": "string"},
                                "loan_id": {"type": "string"},
                            },
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "schedule_callback",
                        "description": "Schedule a callback for the customer.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string"},
                                "time": {"type": "string"},
                                "reason": {"type": "string"},
                            },
                            "required": ["date", "time"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "record_payment_commitment",
                        "description": "Record a payment commitment from the customer.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "commitment_date": {"type": "string"},
                                "amount": {"type": "number"},
                                "payment_method": {"type": "string"},
                            },
                            "required": ["commitment_date"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "escalate_to_human",
                        "description": "Transfer the call to a human agent.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "reason": {"type": "string"},
                                "priority": {"type": "string", "enum": ["normal", "urgent"]},
                            },
                            "required": ["reason"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "check_eligibility",
                        "description": "Check customer eligibility for assistance programs.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "loan_id": {"type": "string"},
                                "program_type": {"type": "string", "enum": ["hardship", "restructuring", "extension", "emi_holiday"]},
                            },
                            "required": ["loan_id", "program_type"],
                        },
                    },
                },
            ],
        },
        "voice": voice_config,
        "serverUrl": settings.VAPI_SERVER_URL,
        "firstMessage": voice_config.get("firstMessage", "Hello, this is a reminder call about your upcoming payment."),
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{VAPI_BASE_URL}/assistant",
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


async def main():
    print("Setting up Vapi assistants...")

    # English (India) assistant
    en_result = await create_assistant(
        name="LOI - Loan Pre-Due Reminder (EN)",
        system_prompt=SYSTEM_PROMPT_EN,
        voice_config={
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "firstMessage": "Hello! My name is Sarah from FinServ Solutions. This call may be recorded for quality purposes. Am I speaking with the loan account holder?",
        },
    )
    print(f"English assistant created: {en_result.get('id')}")

    # Filipino (Philippines) assistant
    ph_result = await create_assistant(
        name="LOI - Premium Reminder (PH)",
        system_prompt=SYSTEM_PROMPT_PH,
        voice_config={
            "provider": "google",
            "voiceId": "fil-PH-Standard-A",
            "firstMessage": "Magandang araw po! Ito po si Maria mula sa insurance company. Puwede ko po bang makausap si...",
        },
    )
    print(f"Filipino assistant created: {ph_result.get('id')}")

    # Indonesian assistant
    id_result = await create_assistant(
        name="LOI - Cicilan Reminder (ID)",
        system_prompt=SYSTEM_PROMPT_ID,
        voice_config={
            "provider": "google",
            "voiceId": "id-ID-Standard-A",
            "firstMessage": "Selamat pagi, Bapak/Ibu. Saya Sari dari perusahaan pembiayaan kami. Apakah saya berbicara dengan...",
        },
    )
    print(f"Indonesian assistant created: {id_result.get('id')}")

    print("\nDone! Update .env with the assistant IDs:")
    print(f"  VAPI_ASSISTANT_ID_EN={en_result.get('id')}")
    print(f"  VAPI_ASSISTANT_ID_PH={ph_result.get('id')}")
    print(f"  VAPI_ASSISTANT_ID_ID={id_result.get('id')}")


if __name__ == "__main__":
    asyncio.run(main())
