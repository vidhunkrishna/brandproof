import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import check_db_connection
from app.api.routes import auth, guidelines, facts, documents, submissions, disputes, guideline_health, factwatch, visual, analytics

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="BrandProof: Evidence Before Approval — AI-Assisted Brand Governance Platform",
    version=settings.VERSION,
    docs_url=None if settings.ENVIRONMENT.lower() == "production" else "/docs",
    redoc_url=None if settings.ENVIRONMENT.lower() == "production" else "/redoc"
)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(guidelines.router, prefix=settings.API_V1_PREFIX)
app.include_router(facts.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(submissions.router, prefix=settings.API_V1_PREFIX)
app.include_router(disputes.router, prefix=settings.API_V1_PREFIX)
app.include_router(guideline_health.router, prefix=settings.API_V1_PREFIX)
app.include_router(factwatch.router, prefix=settings.API_V1_PREFIX)
app.include_router(visual.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "tagline": "Evidence Before Approval",
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs" if settings.ENVIRONMENT.lower() != "production" else None
    }


@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
def health_check():
    db_health = check_db_connection()
    return {
        "status": "healthy" if db_health.get("status") == "connected" else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_health
    }


@app.get("/ready", tags=["Health"])
@app.get(f"{settings.API_V1_PREFIX}/ready", tags=["Health"])
def readiness_check():
    """Readiness is strict: deployments should receive traffic only with a database connection."""
    db_health = check_db_connection()
    if db_health.get("status") != "connected":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"status": "not_ready", "database": db_health})
    return {"status": "ready", "service": settings.PROJECT_NAME, "version": settings.VERSION}
