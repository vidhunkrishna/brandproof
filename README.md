# BrandProof

> **Evidence Before Approval** — AI-assisted brand governance platform that validates marketing content against an organisation's approved brand guidelines, facts, and terminology before publication.

Built for **CodeNexus India 2026 Hackathon — Round 2**.

---

## 🚀 Key Value Proposition

BrandProof replaces generic AI content generation with **evidence-driven, explainable brand review**:
- **Lane 1: Deterministic Engine** — Rapid rule evaluation (terminology, prohibited phrases, qualifiers, numerical bounds).
- **Lane 2: Grounded Fact Checker** — Direct verification against PostgreSQL-backed approved facts with temporal validity and scoping.
- **Lane 3: Advisory AI Analysis** — Contextual claim extraction, nuanced claim detection, and wording recommendations via configurable external LLM (with zero authority to approve or fabricate facts).
- **Five Deterministic Verdicts**: `CORRECT`, `CONTRADICTED`, `OUTDATED`, `UNSUPPORTED`, `UNVERIFIABLE`.
- **Audit-Grade Lineage**: Every verdict links directly to primary database records with version and approval metadata.

---

## 🛠️ Technology Stack

| Tier | Technologies |
| :--- | :--- |
| **Frontend** | React 19, Vite, Tailwind CSS, React Router DOM, Axios, Lucide Icons |
| **Backend** | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn |
| **Database** | PostgreSQL 18 (with tenant isolation by `organization_id`) |
| **AI Layer** | Configurable external LLM API (Google Gemini / OpenAI compatible) with graceful deterministic fallback |
| **Document Processing** | `pypdf`, `python-docx` for automated guideline extraction into staging queue |

---

## 📁 Repository Structure

```text
brandproof/
├── frontend/                     # React + Vite + Tailwind CSS Application
│   ├── src/
│   │   ├── api/                  # Axios HTTP client & API bindings
│   │   ├── components/           # Reusable UI widgets & status badges
│   │   ├── pages/                # Page views (Auth, Dashboard, Submissions, KB)
│   │   ├── App.jsx               # Main React entrypoint
│   │   └── main.jsx              # React DOM mounting
│   ├── package.json
│   └── .env.example
├── backend/                      # FastAPI Modular Monolith Backend
│   ├── app/
│   │   ├── main.py               # Application entrypoint & health checks
│   │   ├── core/                 # App configuration & DB session engine
│   │   ├── models/               # SQLAlchemy ORM models (Org, Facts, Findings)
│   │   ├── schemas/              # Pydantic v2 validation schemas
│   │   ├── api/routes/           # REST API endpoints (Auth, Guidelines, Review)
│   │   ├── services/             # Core business & governance logic
│   │   ├── review_engine/        # 3-Lane Review Pipeline
│   │   └── document_processing/  # PDF & DOCX guideline parsers
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile
│   └── .env.example
├── docs/                         # Architecture documentation & submission specs
├── .gitignore                    # Python, Node, Environment & IDE exclusions
└── README.md
```

---

## ⚡ Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 20+** and **npm**
- **PostgreSQL 15+** running locally or via Docker

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your PostgreSQL credentials and LLM API Key
   ```

5. **Start the backend server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - API Root: `http://localhost:8000/`
   - Health Check: `http://localhost:8000/health`
   - Interactive Swagger Docs: `http://localhost:8000/docs`

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

4. **Start the development server**:
   ```bash
   npm run dev
   ```
   - Application URL: `http://localhost:5173/`

---

## 🔒 Security Principles

- **Zero LLM Database Authority**: The external LLM cannot create, approve, or alter database facts.
- **Tenant Isolation**: Every database query filters on `organization_id` derived securely from the validated JWT token.
- **Deterministic-Only Fallback**: If the LLM is unavailable or times out, the review engine falls back to deterministic checks (Lane 1 & Lane 2) without crashing.
- **Auditable Reviews**: All approval actions, overrides, and disputes are logged with reviewer metadata.

---

## 🏆 CodeNexus 2026 Commitments

- **Round 2 Deliverable**: Full MVP containing Three-Lane Review Engine, 5 Verdicts, Grounded Evidence, Human Review Queue, and Governance Dashboard.
- **Round 3 Planned Commitments**: Guideline Health, Visual Brand Checks, and FactWatch (reserved for Round 3).
