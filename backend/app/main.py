"""
FastAPI application entry point for InsureGraph Pro
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.database import pg_manager, neo4j_manager, redis_manager
from app.core.rate_limit import RateLimitMiddleware
from app.core.logging import RequestLoggingMiddleware
from app.core.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events
    """
    # Startup: Initialize database connections
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📍 Environment: {settings.ENVIRONMENT}")

    # Try to connect to databases, but don't fail if they're not available
    pg_connected = False
    neo4j_connected = False
    redis_connected = False

    try:
        pg_manager.connect()
        pg_connected = True
        print("✅ PostgreSQL connected")
    except Exception as e:
        print(f"⚠️  PostgreSQL connection failed: {e}")

    try:
        await neo4j_manager.connect()
        neo4j_connected = True
        print("✅ Neo4j connected")
    except Exception as e:
        print(f"⚠️  Neo4j connection failed: {e}")

    try:
        redis_manager.connect()
        redis_connected = True
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")

    if not (pg_connected or neo4j_connected or redis_connected):
        print("⚠️  No database connections established - running in limited mode")

    yield

    # Shutdown: Close database connections
    print("🛑 Shutting down...")
    try:
        if pg_connected:
            pg_manager.disconnect()
        if neo4j_connected:
            await neo4j_manager.disconnect()
        if redis_connected:
            redis_manager.disconnect()
        print("✅ All connections closed")
    except Exception as e:
        print(f"⚠️  Error closing connections: {e}")


# FastAPI app instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="GraphRAG-powered insurance policy analysis platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ⚠️  Middleware execution order: Last added = First executed
# CORS must be added LAST to execute FIRST

# GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Security headers middleware
# Enable HSTS only in production (requires HTTPS)
app.add_middleware(
    SecurityHeadersMiddleware,
    enable_csp=True,
    enable_hsts=(settings.ENVIRONMENT == "production"),
    enable_frame_options=True,
)


# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)


# Rate limiting middleware
# ⚠️ In development: very high limit (10000/min) to avoid blocking dashboard polling
# ⚠️ In production: strict limit (100/min) for security
if settings.ENVIRONMENT == "production":
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
else:
    # Development: 10000 requests per minute (effectively unlimited for local dev)
    app.add_middleware(RateLimitMiddleware, max_requests=10000, window_seconds=60)


# ✅ CORS middleware - MUST BE ADDED LAST (executes FIRST)
# This ensures CORS headers are added before other middleware processing
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],  # Allows all headers
    expose_headers=["*"],  # Exposes all headers to browser
)


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for load balancer"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "disabled in production",
    }


# API v1 routers
from app.api.v1 import ingestion
from app.api.v1.router import api_router as v1_router
# from app.api.v1 import auth, compliance  # TODO: Add these routers

app.include_router(ingestion.router, prefix=f"{settings.API_V1_PREFIX}/policies", tags=["Ingestion"])
app.include_router(v1_router, prefix=settings.API_V1_PREFIX)
# app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
# app.include_router(compliance.router, prefix=f"{settings.API_V1_PREFIX}/compliance", tags=["Compliance"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch-all exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
