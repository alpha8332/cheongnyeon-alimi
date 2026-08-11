from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.services.seed_importer import import_seed_data
from app.services.eligibility_evidence import build_eligibility_summary
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


def test_get_policy_detail_eligibility_summary(db):
    """GET /api/v1/policies/{id} 응답에 eligibility_summary 구조가 포함되는지 검증."""
    policy = db.query(Policy).first()
    assert policy is not None

    response = client.get(f"/api/v1/policies/{policy.id}")
    assert response.status_code == 200
    data = response.json()

    assert "eligibility_summary" in data
    summary = data["eligibility_summary"]
    assert summary is not None
    assert "status" in summary
    assert summary["status"] in ("complete", "partial", "unknown")
    assert "requirements" in summary
    assert "exclusions" in summary
    assert "preferences" in summary
    assert "required_documents" in summary
    assert "unknown_conditions" in summary
    assert "institutional_contacts" in summary


def test_build_eligibility_summary_structure(db):
    """build_eligibility_summary 서비스 함수의 구조화 및 Evidence 바인딩 검증."""
    policy = db.query(Policy).first()
    assert policy is not None

    summary = build_eligibility_summary(policy)
    assert summary.status in ("complete", "partial", "unknown")
    assert len(summary.unknown_conditions) >= 1

    if summary.requirements:
        first_req = summary.requirements[0]
        assert first_req.category in ("age", "region", "other")
        assert first_req.evidence is not None
        assert first_req.evidence.source_id == policy.source_id
        assert first_req.evidence.source_url == policy.source_url
