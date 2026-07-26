from typing import Any, Dict, Optional

class AppException(Exception):
    """
    최상위 커스텀 애플리케이션 예외
    """
    def __init__(
        self,
        message: str = "Internal Server Error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class DatabaseConnectionError(AppException):
    def __init__(self, message: str = "Database Connection Failed"):
        super().__init__(message=message, status_code=503)

class EntityNotFoundError(AppException):
    def __init__(self, entity_name: str = "Entity"):
        super().__init__(message=f"{entity_name} Not Found", status_code=404)
