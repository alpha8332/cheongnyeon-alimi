from typing import Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse

from app.services.admin_access import verify_admin_session_token

# Authorization: Bearer <token> 추출 (자동 에러 대신 커스텀 JSON 에러 처리를 위해 auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_admin_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """
    관리자 전용 API 라우트를 보호하는 공통 FastAPI Dependency.
    - 헤더 누락 또는 토큰 무효/만료 시: HTTP 401 Unauthorized
    - 비관리자 역할(role != 'admin') 시: HTTP 403 Forbidden
    - 검증 성공 시: 디코딩된 admin 토큰 페이로드(dict) 반환
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_admin_session_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin authorization required.",
        )

    return payload
