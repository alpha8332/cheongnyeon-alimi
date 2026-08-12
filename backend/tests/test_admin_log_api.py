from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.logging_config import LOG_DIR
from app.services.admin_log import AUDIT_TRAIL

client = TestClient(app)


@pytest.fixture
def admin_token():
    """테스트용 관리자 인증 세션 토큰 생성 픽스처."""
    response = client.post("/api/v1/admin/session", json={"pin": "0000"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_get_log_files_unauthorized_401():
    """인증 헤더 없이 /api/v1/admin/logs/files 접근 시 401 Unauthorized 반환."""
    response = client.get("/api/v1/admin/logs/files")
    assert response.status_code == 401


def test_get_log_files_success(admin_token):
    """관리자 인증 성공 후 로그 파일 목록 조회 검증."""
    response = client.get(
        "/api/v1/admin/logs/files",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert len(data["files"]) >= 1
    first_file = data["files"][0]
    assert "file_id" in first_file
    assert "is_active" in first_file


def test_get_log_events_success(admin_token):
    """파싱된 로그 이벤트 조회 및 필터링 검증."""
    response = client.get(
        "/api/v1/admin/logs/events?file_id=app.log&limit=10",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "events" in data


def test_delete_active_file_forbidden_400(admin_token):
    """활성 로그 파일(app.log) 직접 삭제 시도 시 400 Bad Request 차단 및 감사 기록 검증."""
    initial_audit_count = len(AUDIT_TRAIL)
    response = client.delete(
        "/api/v1/admin/logs/archives/app.log",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    # 별도 감사 기록 생성 확인
    assert len(AUDIT_TRAIL) > initial_audit_count
    last_audit = AUDIT_TRAIL[-1]
    assert last_audit["file_id"] == "app.log"
    assert last_audit["success"] is False


def test_delete_archived_file_success(admin_token, tmp_path):
    """회전 완료된 Archive 로그 파일(app.log.1) 삭제 성공 및 감사 기록 생성 검증."""
    # 테스트용 Archive 파일 생성
    archive_file = LOG_DIR / "app.log.999"
    archive_file.write_text('{"timestamp": "2026-08-11T00:00:00Z", "event": "test"}', encoding="utf-8")

    initial_audit_count = len(AUDIT_TRAIL)
    response = client.delete(
        f"/api/v1/admin/logs/archives/{archive_file.name}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True
    assert "audit_id" in data

    # 파일 삭제 확인
    assert not archive_file.exists()

    # 감사 기록 생성 확인
    assert len(AUDIT_TRAIL) > initial_audit_count
    last_audit = AUDIT_TRAIL[-1]
    assert last_audit["file_id"] == archive_file.name
    assert last_audit["success"] is True


def test_path_traversal_protection_400(admin_token):
    """Path Traversal 공격 시도 시 400 Bad Request 차단."""
    response = client.delete(
        "/api/v1/admin/logs/archives/..%2F..%2Fetc%2Fpasswd",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code in (400, 404)
