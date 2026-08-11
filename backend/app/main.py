import time
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.logging_config import setup_file_logging
from app.core.exceptions import AppException
from app.api.v1.api import api_router
from app.api.v1.endpoints.health import check_health

# Initialize Logger
setup_logging()
setup_file_logging()

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)


def custom_openapi():
    """Custom OpenAPI schema to register HTTPBearer security scheme for Admin Access Control."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version="0.5.0",
        description="Cheongnyeon-alimi API with Admin Access Control",
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your admin session token (admin.<expires_at>.<sig>)",
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# CORS Middleware
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Logging & Process Time Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Completed in {process_time:.2f}ms")
    return response


# Custom Exception Handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.error(f"AppException: {exc.message} (Status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "details": exc.details
            }
        }
    )


# Unhandled Exception Handler
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.critical(
        "Unhandled exception. error_type=%s",
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Internal Server Error",
                "details": {}
            }
        }
    )


# Include Routers
app.include_router(api_router, prefix="/api/v1")


# Root Health Check Shortcut (GET /health)
@app.get("/health", tags=["Health Check"], summary="Root Health Check Shortcut")
def root_health(response: JSONResponse):
    return check_health(response)


@app.get("/", include_in_schema=False)
def root():
    return {"message": f"Welcome to {settings.APP_NAME} API", "docs": "/docs"}
