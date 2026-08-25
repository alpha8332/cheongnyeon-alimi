"""Protected, read-only collector operation status endpoint."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_payload
from app.core.database import get_db
from app.schemas.admin_collector import AdminCollectorStatusResponse
from app.services.admin_collector import get_admin_collector_status


router = APIRouter()


@router.get(
    "",
    response_model=AdminCollectorStatusResponse,
    summary="등록 수집기와 중앙 실행 환경 상태 조회",
    responses={
        200: {"description": "비밀값을 제외한 수집기 운영 상태"},
        401: {"description": "관리자 토큰 미제공 또는 유효하지 않음"},
        403: {"description": "관리자 권한 부족"},
    },
)
def read_admin_collectors(
    db: Session = Depends(get_db),
    _admin_payload: dict[str, Any] = Depends(get_current_admin_payload),
) -> AdminCollectorStatusResponse:
    return get_admin_collector_status(db)

