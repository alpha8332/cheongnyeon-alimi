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
    assert summary["coverage"] in ("complete", "partial", "unknown")
    assert "requirements" in summary
    assert "exclusions" in summary
    assert "preferences" in summary
    assert "documents" in summary
    assert "unknowns" in summary
    assert "institutional_contacts" in summary
