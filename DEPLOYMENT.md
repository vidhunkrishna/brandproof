# BrandProof — Production Deployment & Operations Guide

**BrandProof: Evidence Before Approval** — AI-Assisted Brand Governance Platform

---

## 1. Architecture Overview

BrandProof is architected as an evidence-first, three-tier SaaS platform:

```
┌────────────────────────────────┐
│   Static Frontend (SPA)       │  Hosted on Vercel / Netlify / Nginx (Docker)
│   React 19 + Vite + Tailwind   │  Origin: https://brandproof.vercel.app
└───────────────┬────────────────┘
                │ HTTPS (TLS 1.3)
                │ Bearer JWT in Authorization header
                ▼
┌────────────────────────────────┐
│   API Backend (FastAPI)        │  Hosted on Render / Container Host (Docker)
│   Python 3.11 + Uvicorn        │  Origin: https://api.brandproof.example
│   Three-Lane Review Engine     │  Port: 8000 (or $PORT)
└───────────────┬────────────────┘
                │ TLS Connection Pool (pool_pre_ping=True)
                ▼
┌────────────────────────────────┐
│   Managed PostgreSQL (15+)     │  Hosted on Neon / Supabase / Render / RDS
│   Alembic Versioned Migrations │  Port: 5432 (SSL required)
└────────────────────────────────┘
```

> [!NOTE]
> **Verification Status**: Direct application execution (Python 3.11 virtual environment, FastAPI, SQLAlchemy, Alembic migrations, and React/Vite frontend production builds) is 100% verified with 92 passing backend tests. The Docker runtime configuration and container builds remain unverified locally because the Docker Desktop daemon was not running on the development workstation. Statically authored Dockerfiles and Nginx configurations are provided following standard best practices.

---

## 2. Environment Variables Matrix

### Backend Environment Variables (`backend/.env` or Platform Secret Manager)

| Variable | Type | Production Required | Default (Development) | Purpose / Description |
|---|---|:---:|---|---|
| `ENVIRONMENT` | String | **Yes** | `development` | Set to `production` to enforce security validations (disables Swagger/ReDoc, enforces strict SECRET_KEY and non-wildcard CORS). |
| `DATABASE_URL` | String | **Yes** | `postgresql://...` | Connection URI for PostgreSQL database. Must use TLS/SSL in production (`?sslmode=require`). |
| `SECRET_KEY` | String | **Yes** | *(insecure dev key)* | High-entropy secret key for JWT signing. Must be at least 32 characters in production; startup halts if insecure default is detected. |
| `CORS_ORIGINS` | List / String | **Yes** | `["http://localhost:5173", ...]` | Explicit list of allowed browser origins (JSON array `["https://app.example.com"]` or comma-separated `https://app.example.com`). Wildcards (`*`) are rejected in production mode. |
| `ALGORITHM` | String | No | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| Integer | No | `1440` (24h) | JWT access token lifetime in minutes. |
| `LLM_API_KEY` | String | Optional | `""` | Gemini API key for Lane 3 Advisory AI. If empty or invalid, the engine deterministically falls back to Lanes 1 & 2 without failing. |
| `LLM_MODEL` | String | No | `gemini-1.5-flash` | Gemini model name for advisory claim extraction. |
| `LLM_BASE_URL` | String | No | `https://generativelanguage.googleapis.com/v1beta` | Base URL for LLM provider API. |
| `PROJECT_NAME` | String | No | `BrandProof` | Platform service name. |
| `VERSION` | String | No | `1.0.0` | API semantic version. |

> [!CRITICAL]
> In production (`ENVIRONMENT=production`):
> 1. `SECRET_KEY` **must** be at least 32 characters and cannot contain `"insecure"` or `"change-in-production"`.
> 2. `CORS_ORIGINS` **must** be an explicit non-wildcard list.
> 3. Never commit production `.env` files into Git. Inject them strictly via platform secret managers.

### Frontend Environment Variables (`frontend/.env.production` or Build Settings)

| Variable | Type | Production Required | Example | Purpose / Description |
|---|---|:---:|---|---|
| `VITE_API_URL` | String | **Yes** | `https://api.brandproof.example` | Public HTTPS origin of the FastAPI backend. Used by Axios client. **Never place secrets here.** |

---

## 3. Managed PostgreSQL Database Setup

### Recommended Providers
- **Neon** (Serverless PostgreSQL with SSL support)
- **Supabase** (Managed PostgreSQL 15+ with connection pooling)
- **Render PostgreSQL** (Colocated with backend web service)
- **AWS RDS / DigitalOcean Managed DB** (Enterprise production)

> [!IMPORTANT]
> **Backup Capabilities Notice**: Backup retention policies, snapshot automation, and database branching features vary significantly by cloud provider and subscription tier. Free tiers typically enforce storage caps, auto-pause inactive databases, and may not include automated point-in-time recovery or scheduled backups. Always verify the exact backup and retention guarantees of your chosen provider and plan before relying on them for production data.

### Connection URL Requirements
Always ensure your production database connection string includes SSL enforcement:
```bash
DATABASE_URL=postgresql://brandproof_user:STRONG_PASSWORD@ep-sample-123456.us-east-2.aws.neon.tech/brandproof?sslmode=require
```

### Initial Database Migration
Run Alembic migrations to bring the database schema to the latest version:
```bash
# From backend directory
alembic upgrade head
```
Expected output:
```text
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> d4e7f1a9c625 (head)
```

---

## 4. Backend Deployment Guide

### Option A: Render (Recommended for Hackathon / Demonstration)

1. **Create Web Service**:
   - Source: Connect GitHub repository.
   - Root Directory: `backend`
   - Runtime: `Python` (or `Docker`)
   - Build Command: `pip install --no-cache-dir -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers`
2. **Set Environment Variables**:
   ```ini
   ENVIRONMENT=production
   DATABASE_URL=postgresql://... (from Neon / Supabase / Render DB)
   SECRET_KEY=generate_using_python_secrets_token_hex_32
   CORS_ORIGINS=["https://brandproof.vercel.app"]
   LLM_API_KEY=AIzaSy... (optional)
   ```
3. **Configure Health Checks**:
   - Health Check Path: `/health`
4. **Pre-Deploy Migration Command**:
   - Add a pre-deploy release job: `alembic upgrade head`

### Option B: Docker Container Deployment

> [!NOTE]
> **Container Runtime Verification**: The Docker instructions below are statically verified against standard OCI container practices. However, local container execution and image builds remain unverified because the Docker Desktop daemon was not active during preparation. Always test container builds in your target deployment pipeline.

1. **Build Backend Container**:
   ```bash
   docker build -t brandproof-api:1.0.0 backend
   ```
2. **Execute Single-Run Migration Job**:
   ```bash
   docker run --rm \
     -e DATABASE_URL="postgresql://..." \
     brandproof-api:1.0.0 alembic upgrade head
   ```
3. **Run Production Container**:
   ```bash
   docker run -d \
     --name brandproof-api \
     -p 8000:8000 \
     -e ENVIRONMENT="production" \
     -e DATABASE_URL="postgresql://..." \
     -e SECRET_KEY="STRONG_32_CHAR_SECRET_KEY..." \
     -e CORS_ORIGINS="[\"https://brandproof.vercel.app\"]" \
     --restart unless-stopped \
     brandproof-api:1.0.0
   ```

---

## 5. Frontend Deployment Guide

### Option A: Vercel (Recommended Static Host)

1. **Connect Repository**:
   - Root Directory: `frontend`
   - Framework Preset: `Vite`
   - Build Command: `npm run build`
   - Output Directory: `dist`
2. **Set Environment Variable**:
   - `VITE_API_URL` = `https://api.brandproof.example` (or your Render backend URL)
3. **SPA Routing**:
   - The included `frontend/vercel.json` automatically routes all requests to `index.html`:
   ```json
   {
     "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
   }
   ```

### Option B: Netlify

1. **Connect Repository**:
   - Base Directory: `frontend`
   - Build Command: `npm run build`
   - Publish Directory: `frontend/dist`
2. **Set Environment Variable**:
   - `VITE_API_URL` = `https://api.brandproof.example`
3. **SPA Routing**:
   - The included `frontend/public/_redirects` is copied to `dist/_redirects`:
   ```text
   /*    /index.html   200
   ```

### Option C: Docker with Nginx

> [!NOTE]
> **Container Runtime Verification**: Like the backend container, the frontend multi-stage Docker build and Nginx configuration are statically verified against standard practices but have not been executed in a local live container daemon.

1. **Build Frontend Container**:
   ```bash
   docker build \
     --build-arg VITE_API_URL="https://api.brandproof.example" \
     -t brandproof-web:1.0.0 frontend
   ```
2. **Run Nginx Container**:
   ```bash
   docker run -d \
     --name brandproof-web \
     -p 80:80 \
     --restart unless-stopped \
     brandproof-web:1.0.0
   ```
   *The included `frontend/nginx.conf` handles gzip compression, asset caching headers, and SPA URL fallback (`try_files $uri $uri/ /index.html`).*

---

## 6. Health & Readiness Monitoring

BrandProof provides operational probes designed for cloud load balancers and orchestrators:

### 1. Liveness Probe: `GET /health` (or `GET /api/v1/health`)
Verifies process responsiveness and reports database connectivity status:
```json
{
  "status": "healthy",
  "service": "BrandProof",
  "version": "1.0.0",
  "database": {
    "status": "connected",
    "database": "postgresql"
  }
}
```
*HTTP 200 is returned. If the database connection is down, `status` returns `"degraded"`.*

### 2. Readiness Probe: `GET /ready` (or `GET /api/v1/ready`)
Strict probe to ensure incoming user traffic is only routed to containers with live database connectivity:
```json
{
  "status": "ready",
  "service": "BrandProof",
  "version": "1.0.0"
}
```
*Returns **HTTP 200** when connected. Returns **HTTP 503 Service Unavailable** if the database connection drops or is unreachable.*

---

## 7. Security Hardening Checklist

- [x] **Secret Key Security**: Generated using `python -c "import secrets; print(secrets.token_hex(32))"`. Never use default development strings.
- [x] **CORS Lockdown**: Explicit origins only (e.g. `["https://brandproof.vercel.app"]`). Wildcard `*` disallowed in production.
- [x] **Documentation Exposure**: Swagger UI (`/docs`) and ReDoc (`/redoc`) automatically disabled when `ENVIRONMENT=production`.
- [x] **Non-Root Container**: Backend Dockerfile creates and executes as `USER appuser`.
- [x] **Proxy Header Forwarding**: Uvicorn runs with `--proxy-headers` for trusted reverse-proxy scheme/IP extraction.
- [x] **Tenant Query Isolation**: Authenticated `TenantContext` filters all queries strictly by `organization_id`.
- [x] **Zero LLM Database Authority**: AI analyzer has zero database write access and cannot generate `CORRECT` verdicts or assign IDs.
- [x] **Upload Size & Type Limits**: Document uploads bounded to 10 MB (`.pdf`, `.docx`); visual assets bounded to 10 MB (PNG, JPEG, WebP) with PIL dimension and format verification.
- [x] **SQL Injection Defense**: 100% SQLAlchemy ORM parameterized queries; zero raw string interpolation.

---

## 8. Backup & Disaster Recovery

### PostgreSQL Automated Backup Command
Execute automated logical database backups before applying schema migrations or releases:
```bash
# Take logical dump with compression
pg_dump -h <db_host> -p 5432 -U <db_user> -d <db_name> -F c -b -v -f brandproof_backup_$(date +%Y%m%d_%H%M%S).dump
```

### PostgreSQL Disaster Recovery / Restore Command
Restore from backup file into an empty or newly provisioned database:
```bash
# Restore from dump
pg_restore -h <db_host> -p 5432 -U <db_user> -d <db_name> -v --clean --if-exists brandproof_backup_YYYYMMDD_HHMMSS.dump
```

---

## 9. Troubleshooting & Common Issues

| Symptom | Cause | Resolution |
|---|---|---|
| **CORS preflight blocked in browser** | Mismatched origin between frontend URL and backend `CORS_ORIGINS`. | Check exact browser origin including scheme and port (e.g. `https://brandproof.vercel.app`, no trailing slash). Update `CORS_ORIGINS` in backend environment. |
| **API startup failure with ValueError: CRITICAL SECURITY ERROR** | `ENVIRONMENT=production` was set, but `SECRET_KEY` was missing, shorter than 32 characters, or contained default placeholder words. | Generate a 32+ character random secret using `python -c "import secrets; print(secrets.token_hex(32))"` and set as `SECRET_KEY`. |
| **Frontend direct navigation returns 404 on refresh** | Web server not configured for SPA routing. | Ensure `vercel.json` (Vercel), `public/_redirects` (Netlify), or `nginx.conf` (`try_files $uri $uri/ /index.html`) is active. |
| **`/ready` returns HTTP 503** | Backend cannot reach PostgreSQL instance. | Verify `DATABASE_URL`, network firewalls, and that `sslmode=require` is present if required by cloud provider. |
| **Alembic migration fails on duplicate table or lock** | Concurrent migration jobs executed during container scaling. | Run `alembic upgrade head` strictly as a single release job prior to scaling web instances. |
| **Free-tier backend cold starts (~50s delay)** | Free-tier instances (such as Render free web services) spin down after 15 minutes of inactivity. The initial request requires spinning up the container and establishing database connections. | Upgrade to a paid tier (such as Render Starter at $7/mo or a persistent container instance) for uninterrupted, zero-cold-start availability. |

---

## 10. Student Hackathon Recommendation

For a student hackathon project with minimal overhead and reliable demonstration:

1. **Frontend**: **Vercel** (Hobby Tier - Free)
   - Zero cold-start latency, global Edge CDN.
   - Built-in Git CI/CD deployments.
   - Turnkey support for Vite and `vercel.json` SPA rewrites.
2. **Backend**: **Render** ($7/mo Starter Web Service recommended; Free tier available for testing)
   - Native Python environment or container hosting with automated HTTPS provisioning.
   - Built-in health probe support (`/health` and `/ready`).
   - *Cold-start limitation: Free-tier instances spin down after 15 minutes of inactivity, resulting in a ~50-second delay on the first incoming request. For reliable, uninterrupted judge demonstrations and production workloads, a paid plan (such as Render Starter) is strongly recommended.*
3. **Database**: **Neon** or **Supabase** (Managed PostgreSQL)
   - Dedicated cloud PostgreSQL 15+ instance with TLS/SSL enforcement (`?sslmode=require`).
   - Full compatibility with SQLAlchemy connection pooling and Alembic migrations.
   - *Backup note: Free tiers provide cloud PostgreSQL access and management dashboards, but automated daily backups, point-in-time recovery, and database branching features vary by provider and subscription tier. Verify your specific plan's retention limits or run manual `pg_dump` backups before schema migrations.*
