import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

from .core.config import settings
from .core.logging import setup_logging
from .db.mongodb import connect_to_mongo, close_mongo_connection
from .api.endpoints import (
    industries,
    sessions,
    files,
    kpis,
    column_mapping,
    dashboard,
    advisor
)

# Setup logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title="ESG Analysis Platform API",
    description="API for ESG metrics tracking, analysis, and advisory",
    version="1.0.0",
)

# Configure CORS
origins = []
try:
    # Parse CORS origins from string or use default
    if isinstance(settings.CORS_ORIGINS, str):
        origins = json.loads(settings.CORS_ORIGINS)
    else:
        origins = settings.CORS_ORIGINS
except json.JSONDecodeError:
    logger.warning(f"Invalid CORS_ORIGINS format: {settings.CORS_ORIGINS}. Using default.")
    origins = ["http://localhost:3000", "http://localhost:8501"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection events
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Include API routers
app.include_router(industries.router, prefix="/api/industries", tags=["industries"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(kpis.router, prefix="/api/kpis", tags=["kpis"])
app.include_router(column_mapping.router, prefix="/api/mapping", tags=["column_mapping"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(advisor.router, prefix="/api/advisor", tags=["advisor"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "ESG Analysis Platform API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
