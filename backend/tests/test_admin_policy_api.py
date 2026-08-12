from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.services.seed_importer import import_seed_data
from app.models.policy import Policy

client = TestClient(app)

SEED_FILE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "seeds"
    / "initial_programs.json"
)


@pytest.fixture(autouse=True)
def setup_seed_data(db):
    app.dependency_overrides[get_db] = lambda: db
    import_seed_data(db, SEED_FILE_PATH)
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def admin_token():
    """테스트용 관리자 인증 세션 토큰 생성 픽스처."""
    response = client.post("/api/v1/admin/session", json={"pin": "0000"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_get_admin_policies_unauthorized_401():
    """인증 헤더 없이 /api/v1/admin/policies 접근 시 401 Unauthorized 반환."""
    response = client.get("/api/v1/admin/policies")
    assert response.status_code == 401


def test_get_admin_policies_success(admin_token):
    """관리자 인증 성공 후 정책 데이터 표 목록 조회 (Read-Only) 검증."""
    response = client.get(
        "/api/v1/admin/policies?page=1&limit=5",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "items" in data
    assert len(data["items"]) <= 5
    if data["items"]:
        first = data["items"][0]
        assert "id" in first
        assert "source_id" in first
        assert "title" in first
        assert "data_quality_status" in first


def test_get_admin_policies_allowlist_sort_and_limit(admin_token):
    """Allowlist 정렬 및 limit 조절 테스트."""
    response = client.get(
        "/api/v1/admin/policies?sort_by=collected_at&order=asc&limit=100",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 100


def test_get_admin_policy_detail_success(admin_token, db):
    """관리자 인증 성공 후 정책 데이터 단건 상세 조회 검증."""
    policy = db.query(Policy).first()
    assert policy is not None

    response = client.get(
        f"/api/v1/admin/policies/{policy.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == policy.id
    assert data["title"] == policy.title
    assert "source_url" in data
    assert "required_conditions" in data


def test_get_admin_policy_detail_not_found_404(admin_token):
    """존재하지 않는 정책 ID 조회 시 404 Not Found 반환."""
    response = client.get(
        "/api/v1/admin/policies/999999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
