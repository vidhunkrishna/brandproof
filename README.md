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

## Deployment and operations

For complete step-by-step production setup, environment variable references, and cloud provider guides (Vercel, Render, Neon, Docker), see [DEPLOYMENT.md](DEPLOYMENT.md).

Set `ENVIRONMENT=production`, a strong unique `SECRET_KEY`, a production PostgreSQL `DATABASE_URL`, and explicit `CORS_ORIGINS`. Production startup rejects the placeholder secret and wildcard CORS. Configure the frontend with `VITE_API_URL=https://api.example.com`; the frontend host must return `index.html` for unknown application routes to support React Router refreshes.

Build the backend image with `docker build -t brandproof-api backend`. Apply migrations once as an explicit release job before scaling application replicas:

```bash
docker run --rm --env-file backend/.env brandproof-api alembic upgrade head
docker run --rm -p 8000:8000 --env-file backend/.env brandproof-api
```

Use `/health` for liveness and `/ready` for database-backed readiness. Back up PostgreSQL on a tested schedule (including restore drills); uploaded visual assets are intentionally not retained, only their review measurements and metadata are persisted.

Run verification locally with `cd backend && pytest -q`, `alembic heads`, and `cd frontend && npm run build`. GitHub Actions repeats the backend migration/test and frontend production build. Demo credentials are development-only and are seeded by the local development setup; never deploy them or any `.env` file as production credentials.

### Public deployment procedure

The recommended minimal production topology is: a managed PostgreSQL instance, one FastAPI container behind HTTPS, and a static frontend host (or the included Nginx frontend container). Keep the API and frontend on separate public origins and set `CORS_ORIGINS` to the exact frontend HTTPS origin.

1. Create a managed PostgreSQL database and a least-privilege application user. Store its TLS-enabled connection string only in the deployment platform's secret manager as `DATABASE_URL`; never put it in a repository file, image, or frontend variable.
2. Set backend runtime secrets: `ENVIRONMENT=production`, a randomly generated `SECRET_KEY`, `DATABASE_URL`, and `CORS_ORIGINS=["https://app.example.com"]`. Set optional `LLM_API_KEY` only in that secret manager.
3. Build and publish the API image: `docker build -t registry.example/brandproof-api:VERSION backend`. Run the migration command once as a release job: `docker run --rm --env-file runtime.env registry.example/brandproof-api:VERSION alembic upgrade head`. Do not run concurrent migration jobs.
4. Start the API with HTTPS termination at the platform/load balancer and route probes to `/health` (liveness) and `/ready` (database readiness). The included backend container listens on port 8000.
5. Build the frontend with the public API origin: `docker build --build-arg VITE_API_URL=https://api.example.com -t registry.example/brandproof-web:VERSION frontend`. Alternatively set that value in the static-host build environment. `VITE_*` values are public and must never contain secrets.
6. Deploy the frontend with an SPA rewrite rule. The included `frontend/nginx.conf` uses `try_files $uri $uri/ /index.html`, which preserves direct navigation to React Router URLs.
7. Smoke test over HTTPS: `GET /health`, `GET /ready`, login, submission creation, a protected cross-origin request from the deployed frontend, and a browser refresh on `/submissions`.

Before releasing, take a verified database backup, retain migration history, and have a tested restore procedure. Roll back application images independently from database migrations; only downgrade a migration after assessing data-loss implications.

## Security limitations

- JWTs are bearer tokens stored by the current demo frontend in browser storage; production should migrate to short-lived HttpOnly secure cookies or an equivalent managed session design.
- Rate limiting is not yet distributed or proxy-enforced. Configure it at the API gateway before public exposure.
- Visual checks provide sampled deterministic measurements. They do not provide OCR-based typography verification or pixel-perfect logo identity verification.

## 🏆 CodeNexus 2026 Commitments

- **Round 2 Deliverable**: Full MVP containing Three-Lane Review Engine, 5 Verdicts, Grounded Evidence, Human Review Queue, and Governance Dashboard.
- **Round 3 Deliverable**: Guideline Health, Visual Brand Checks, FactWatch, disputes, and governance analytics.
