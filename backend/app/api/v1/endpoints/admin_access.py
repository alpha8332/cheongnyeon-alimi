from ipaddress import ip_address
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_admin_payload
from app.schemas.admin_access import (
    AdminPinChange,
    AdminSessionCreate,
    AdminSessionResponse,
    AdminErrorResponse,
)
from app.services.admin_access import (
    AdminAuthNotConfiguredError,
    InvalidCurrentAdminPinError,
    ReusedAdminPinError,
    change_admin_pin,
    verify_admin_pin,
    create_admin_session_token,
    is_rate_limited,
    record_failed_attempt,
    reset_failed_attempts,
    get_admin_token_secret,
    get_or_create_admin_auth_state,
)

router = APIRouter()


def is_local_admin_client(client_host: str) -> bool:
    """기본 개발 PIN을 허용할 실제 loopback/TestClient 요청인지 판정한다."""
    normalized = client_host.strip().lower()
    if normalized in {"localhost", "testclient"}:
        return True

    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


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
    db: Session = Depends(get_db),
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
    allow_local_default_pin = is_local_admin_client(client_ip)
    auth_state = get_or_create_admin_auth_state(
        db,
        allow_local_default_pin=allow_local_default_pin,
    )
    if auth_state is not None and auth_state in db.new:
        db.commit()
        db.refresh(auth_state)
    is_valid = auth_state is not None and verify_admin_pin(
        body.pin,
        pin_hash=auth_state.pin_hash,
    )
    token_signing_ready = get_admin_token_secret() is not None
    if not is_valid or not token_signing_ready:
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
    token = create_admin_session_token(
        expires_minutes=settings.ADMIN_SESSION_EXPIRE_MINUTES,
        session_generation=auth_state.session_generation,
    )

    return AdminSessionResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in_sec,
        role="admin",
    )


@router.put(
    "/pin",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    summary="관리자 PIN 변경",
    responses={
        204: {"description": "PIN 변경 및 기존 관리자 세션 무효화 완료"},
        401: {"model": AdminErrorResponse, "description": "현재 PIN 불일치"},
        409: {"model": AdminErrorResponse, "description": "현재 PIN 재사용"},
        422: {"description": "PIN 형식 유효성 검사 실패"},
    },
)
def update_admin_pin(
    body: AdminPinChange,
    request: Request,
    _: Dict[str, Any] = Depends(get_current_admin_payload),
    db: Session = Depends(get_db),
) -> Response:
    client_ip = request.client.host if request.client else "127.0.0.1"
    try:
        change_admin_pin(
            db,
            current_pin=body.current_pin,
            new_pin=body.new_pin,
            allow_local_default_pin=is_local_admin_client(client_ip),
        )
        db.commit()
    except InvalidCurrentAdminPinError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {
                    "message": "Current admin PIN is invalid.",
                    "details": {},
                }
            },
        )
    except ReusedAdminPinError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "message": "New admin PIN must differ from the current PIN.",
                    "details": {},
                }
            },
        )
    except AdminAuthNotConfiguredError:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {
                    "message": "Administrator authentication is not configured.",
                    "details": {},
                }
            },
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    summary="관리자 세션 및 권한 상태 확인 (보호 라우트)",
    responses={
        200: {"description": "관리자 세션 유효"},
        401: {"description": "인증 토큰 누락 또는 유효하지 않음/만료됨"},
        403: {"description": "관리자 권한 부족"},
    },
)
def get_current_admin_info(
    admin_payload: Dict[str, Any] = Depends(get_current_admin_payload),
) -> Dict[str, Any]:
    """
    관리자 세션 토큰 유효성 및 권한을 검증하는 샘플/확인용 보호 엔드포인트.
    get_current_admin_payload dependency를 사용하여 401/403 권한 경계를 보장한다.
    """
    return {
        "role": admin_payload.get("role", "admin"),
        "expires_at": admin_payload.get("expires_at"),
        "status": "authenticated",
    }
