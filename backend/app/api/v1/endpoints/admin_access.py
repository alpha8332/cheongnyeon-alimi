from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.admin_access import (
    AdminSessionCreate,
    AdminSessionResponse,
    AdminErrorResponse,
)
from app.services.admin_access import (
    verify_admin_pin,
    create_admin_session_token,
    is_rate_limited,
    record_failed_attempt,
    reset_failed_attempts,
)

router = APIRouter()


@router.post(
    "/session",
    response_model=AdminSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="관리자 세션 생성 (PIN 로그인)",
    responses={
        401: {"model": AdminErrorResponse, "description": "인증 실패 (잘못된 PIN 또는 fail-closed)"},
        403: {"model": AdminErrorResponse, "description": "권한 부족"},
        429: {"model": AdminErrorResponse, "description": "반복 실패로 인한 점진적 요청 제한 (5->10->30->60->120->300초)"},
        422: {"description": "PIN 형식 유효성 검사 실패 (4자리 숫자 아님)"},
    },
)
def create_admin_session(
    body: AdminSessionCreate,
    request: Request,
) -> AdminSessionResponse | JSONResponse:
    client_ip = request.client.host if request.client else "127.0.0.1"

    # 1. Rate Limit 검사
    limited, cooldown = is_rate_limited(client_ip)
    if limited:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "message": "Too many failed login attempts. Please try again later.",
                    "details": {"cooldown_seconds": cooldown},
                }
            },
        )

    # 2. PIN 검증 (fail-closed 및 로컬 0000 규칙 포함)
    is_valid = verify_admin_pin(body.pin)
    if not is_valid:
        attempts, locked, cooldown_sec = record_failed_attempt(client_ip)
        if locked:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "message": f"Too many failed login attempts. Account temporarily locked for {cooldown_sec} seconds.",
                        "details": {"cooldown_seconds": cooldown_sec},
                    }
                },
            )
        # 구체적 오류 사유(비밀번호 틀림 vs 서비스 미설정)를 외부 노출하지 않고 일관되게 401 반환
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {
                    "message": "Invalid admin PIN or authentication disabled.",
                    "details": {},
                }
            },
        )

    # 3. 로그인 성공: 카운터 리셋 및 서명 토큰 발급
    reset_failed_attempts(client_ip)
    expires_in_sec = settings.ADMIN_SESSION_EXPIRE_MINUTES * 60
    token = create_admin_session_token(expires_minutes=settings.ADMIN_SESSION_EXPIRE_MINUTES)

    return AdminSessionResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in_sec,
        role="admin",
    )
