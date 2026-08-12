from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.services.seed_importer import import_seed_data

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


def test_post_recommendations_success():
    """POST /api/v1/recommendations 추천 API 성공 및 응답 구조 검증."""
    response = client.post(
        "/api/v1/recommendations",
        json={
            "age": 25,
            "region": "서울특별시",
            "category": "finance",
            "status": "open",
            "limit": 5,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "evaluated_at" in data
    assert len(data["items"]) <= 5

    if data["items"]:
        first_item = data["items"][0]
        assert "score" in first_item
        assert "reasons" in first_item
        assert "unknown_conditions" in first_item
        assert "disclaimer" in first_item
        assert "자격을 확정하지 않으며" in first_item["disclaimer"]


def test_get_recommendations_success():
    """GET /api/v1/policies/recommendations Query Parameter 방식 추천 성공 검증."""
    response = client.get(
        "/api/v1/policies/recommendations?age=25&region=서울특별시&limit=3"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 3


def test_recommendation_deterministic_sorting():
    """동일 입력 시 추천 결과의 순서와 점수가 100% 결정적(Deterministic)인지 검증."""
    payload = {"age": 25, "region": "서울특별시", "limit": 10}
    resp1 = client.post("/api/v1/recommendations", json=payload).json()
    resp2 = client.post("/api/v1/recommendations", json=payload).json()

    assert len(resp1["items"]) == len(resp2["items"])
    for item1, item2 in zip(resp1["items"], resp2["items"]):
        assert item1["id"] == item2["id"]
        assert item1["score"] == item2["score"]


def test_recommendation_invalid_age_422():
    """연령(age) 범위 밖(121) 입력 시 422 Unprocessable Entity 반환."""
    response = client.post(
        "/api/v1/recommendations",
        json={"age": 121},
    )
    assert response.status_code == 422
