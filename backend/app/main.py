from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import check_db_connection
from app.api.routes import auth, guidelines, facts, documents, submissions, disputes, guideline_health

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="BrandProof: Evidence Before Approval — AI-Assisted Brand Governance Platform",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

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


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "tagline": "Evidence Before Approval",
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs"
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
