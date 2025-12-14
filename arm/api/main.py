"""
Automatic Ripping Machine - FastAPI Application
Main entry point for the modern async REST API
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import logging
import sys
from pathlib import Path

from .config import settings
from .database import init_db, close_db

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.get_log_level()),
    format='[%(asctime)s] %(levelname)s ARM-API: %(name)s.%(funcName)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown.

    Startup:
    - Initialize database connection pool
    - Create tables if they don't exist
    - Start background tasks (job monitoring, etc.)

    Shutdown:
    - Close database connections
    - Stop background tasks gracefully
    """
    logger.info("Starting ARM FastAPI application...")
    logger.info(f"Database URL: {settings.get_database_url()}")
    logger.info(f"Login disabled: {settings.is_login_disabled()}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # TODO: Start background tasks
    # - Job progress monitoring
    # - Log parsing
    # - System health checks

    yield

    # Shutdown
    logger.info("Shutting down ARM FastAPI application...")
    await close_db()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url=None,  # Disable default docs, we'll add custom ones
    redoc_url=None,
    lifespan=lifespan,
)


# ============================================================================
# Middleware
# ============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests (except health checks)."""
    if request.url.path != f"{settings.API_V1_PREFIX}/health":
        logger.debug(f"{request.method} {request.url.path}")

    response = await call_next(request)
    return response


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested URL {request.url.path} was not found",
            "path": request.url.path
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler."""
    logger.error(f"Internal error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }
    )


# ============================================================================
# Health Check & Info Endpoints
# ============================================================================

@app.get(f"{settings.API_V1_PREFIX}/health", tags=["system"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": "connected"
    }


@app.get(f"{settings.API_V1_PREFIX}/info", tags=["system"])
async def api_info():
    """
    API information endpoint.

    Returns:
        dict: API configuration and status
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs_url": f"{settings.API_V1_PREFIX}/docs",
        "redoc_url": f"{settings.API_V1_PREFIX}/redoc",
        "openapi_url": f"{settings.API_V1_PREFIX}/openapi.json",
        "login_disabled": settings.is_login_disabled(),
    }


@app.get("/", tags=["system"])
async def root():
    """
    Root endpoint - redirects to API docs.

    Returns:
        dict: Welcome message with links
    """
    return {
        "message": "Automatic Ripping Machine API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }


# ============================================================================
# Custom Documentation Endpoints
# ============================================================================

@app.get(f"{settings.API_V1_PREFIX}/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI endpoint."""
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        title=f"{settings.PROJECT_NAME} - Swagger UI",
        swagger_favicon_url="/static/img/favicon.ico"
    )


@app.get(f"{settings.API_V1_PREFIX}/redoc", include_in_schema=False)
async def custom_redoc_html():
    """Custom ReDoc endpoint."""
    return get_redoc_html(
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        title=f"{settings.PROJECT_NAME} - ReDoc",
        redoc_favicon_url="/static/img/favicon.ico"
    )


@app.get(f"{settings.API_V1_PREFIX}/openapi.json", include_in_schema=False)
async def get_openapi():
    """OpenAPI schema endpoint."""
    from fastapi.openapi.utils import get_openapi as generate_openapi
    return generate_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )


# ============================================================================
# Mount Static Files (for legacy UI during transition)
# ============================================================================

# Get the path to the UI static folder
ui_static_path = Path(__file__).parent.parent / "ui" / "static"
if ui_static_path.exists():
    app.mount("/static", StaticFiles(directory=str(ui_static_path)), name="static")
    logger.info(f"Mounted static files from {ui_static_path}")
else:
    logger.warning(f"Static files directory not found: {ui_static_path}")


# ============================================================================
# Register API Routers
# ============================================================================

# Import routers here to avoid circular imports
# Routers will be created in the next steps

# from .routers import auth, jobs, settings_router, logs, drives, notifications, realtime

# app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["authentication"])
# app.include_router(jobs.router, prefix=f"{settings.API_V1_PREFIX}/jobs", tags=["jobs"])
# app.include_router(settings_router.router, prefix=f"{settings.API_V1_PREFIX}/settings", tags=["settings"])
# app.include_router(logs.router, prefix=f"{settings.API_V1_PREFIX}/logs", tags=["logs"])
# app.include_router(drives.router, prefix=f"{settings.API_V1_PREFIX}/drives", tags=["drives"])
# app.include_router(notifications.router, prefix=f"{settings.API_V1_PREFIX}/notifications", tags=["notifications"])
# app.include_router(realtime.router, prefix=f"{settings.API_V1_PREFIX}/realtime", tags=["realtime"])

logger.info("API routers registered (will be added in next steps)")


# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting development server...")
    logger.info(f"Server will run on http://{settings.HOST}:{settings.PORT}")
    logger.info(f"API docs: http://{settings.HOST}:{settings.PORT}{settings.API_V1_PREFIX}/docs")

    uvicorn.run(
        "arm.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,  # Enable auto-reload for development
        log_level=settings.get_log_level().lower(),
    )
