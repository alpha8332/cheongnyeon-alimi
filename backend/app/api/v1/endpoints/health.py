from fastapi import APIRouter, Response, status
from app.core.config import settings
from app.core.database import check_db_connection

router = APIRouter()


@router.get("/health", summary="Health Check API")
def check_health(response: Response):
    db_connected = check_db_connection()

    if not db_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "error",
            "database": "disconnected",
            "app": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
        }

    return {
        "status": "ok",
        "database": "connected",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }
