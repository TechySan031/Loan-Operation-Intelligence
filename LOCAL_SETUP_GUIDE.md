# 🛠️ Loan Operation Intelligence — Local Setup & Development Guide

Welcome! This guide walks you through setting up and running the **Loan Operation Intelligence** platform locally on your machine.

---

## 📋 System Requirements & Prerequisites

Before starting, ensure you have the following installed:

1. **Git**: [Download Git](https://git-scm.com/)
2. **Python 3.11 or 3.12**: [Download Python](https://www.python.org/downloads/) *(Ensure "Add Python to PATH" is checked during installation on Windows)*
3. **Node.js (v18.x or v20.x)**: [Download Node.js](https://nodejs.org/) *(Includes npm)*
4. **PostgreSQL & Redis**:
   - **Local option**: Install PostgreSQL (port `5432`) and Redis (port `6379`) natively or via Docker.
   - **Cloud option**: Use managed free tiers like [Neon](https://neon.tech/) or [Supabase](https://supabase.com/) for PostgreSQL, and [Upstash](https://upstash.com/) for Redis.
5. **Ngrok (Optional)**: Needed only if you wish to test live Vapi voice calls connected to your local backend.

---

## 📥 Step 1: Clone the Repository

Open your terminal or command prompt and run:

```bash
git clone https://github.com/TechySan031/Loan-Operation-Intelligence.git
cd "Loan Operation Intelligence"
```

---

## ⚙️ Step 2: Configure Environment Variables

1. Create your local `.env` file by copying the included `.env.example`:

   **On Windows (PowerShell):**
   ```powershell
   Copy-Item .env.example .env
   ```

   **On macOS / Linux:**
   ```bash
   cp .env.example .env
   ```

2. Open `.env` in a text editor (e.g. VS Code, Notepad) and configure your credentials:

   | Key | Description | Example |
   |---|---|---|
   | `DATABASE_URL` | PostgreSQL AsyncPG connection string | `postgresql+asyncpg://postgres:password@localhost:5432/loan_intelligence` |
   | `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
   | `OPENAI_API_KEY` | OpenAI API key for embeddings & GPT-4o RAG | `sk-proj-...` |
   | `PINECONE_API_KEY` | Pinecone API key for vector retrieval | `pcsk_...` |
   | `PINECONE_INDEX_NAME` | Name of your Pinecone index | `loan-kb` |
   | `NEXT_PUBLIC_VAPI_PUBLIC_KEY` | Vapi web public key for voice assistant | `e770183a-...` |
   | `VAPI_API_KEY` | Vapi private API key | `caee70cd-...` |

---

## 🐍 Step 3: Backend Setup (FastAPI)

1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:

   **On Windows (PowerShell):**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   *(If PowerShell gives an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

   **On macOS / Linux:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. Verify backend:
   - API Root / Swagger Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health Readiness Probe: [http://localhost:8000/api/health/ready](http://localhost:8000/api/health/ready)

---

## 💻 Step 4: Frontend Setup (Next.js)

1. Open a **second terminal** and navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

4. Verify frontend:
   - Open your browser to: [http://localhost:3000](http://localhost:3000)
   - You can access the Operations Console, Knowledge Base, Semantic Search, and Analytics dashboards.

---

## 🎙️ Step 5: Connecting Live Voice Calls via Ngrok (Optional)

If you are testing the **Vapi Voice Agent** making live calls to your local machine:

1. Expose your backend port 8000:
   ```bash
   ngrok http 8000
   ```
2. Copy the resulting public HTTPS URL (e.g. `https://your-domain.ngrok-free.app`).
3. Set your webhook endpoint in Vapi to:
   ```text
   https://your-domain.ngrok-free.app/api/tools/lookup-borrower
   ```
4. Now the voice agent can call your local database tools in real-time to verify accounts.

---

## 🔍 Architecture & Port Summary

| Service | Port | Description |
|---|---|---|
| **Frontend** | `3000` | Next.js 15 UI Dashboard |
| **Backend** | `8000` | FastAPI Server & REST APIs |
| **PostgreSQL** | `5432` | Relational database (Borrowers, Call Logs, Policies) |
| **Redis** | `6379` | Real-time Pub/Sub, Nudge streams & caching |

---

## ❓ Troubleshooting

* **CORS Errors**: The backend allows `localhost:3000` and `localhost:3001` by default. If your frontend runs on a different port, update `allow_origins` in `backend/app/main.py`.
* **Database Connection Issues**: Make sure your PostgreSQL server is active and the database specified in `DATABASE_URL` exists.
* **ModuleNotFoundError**: Ensure your virtual environment is active (`.venv`) before running `pip install` or `uvicorn`.
