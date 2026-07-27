import pytest
from pathlib import Path
from app.services.seed_importer import import_seed_data
from app.models.policy import Policy

SEED_FILE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "seeds" / "initial_programs.json"

def test_import_seed_and_upsert(db):
    """Seed 파일 적재 및 Re-import 시 Upsert 동작 검증 (1-A, 2-A)"""
    total, inserted, updated = import_seed_data(db, SEED_FILE_PATH)
    assert total == 4
    assert inserted == 4
    assert updated == 0
    assert db.query(Policy).count() == 4

    # 동일 Seed 재적재 시 Update 4건 발생
    total2, inserted2, updated2 = import_seed_data(db, SEED_FILE_PATH)
    assert total2 == 4
    assert inserted2 == 0
    assert updated2 == 4
    assert db.query(Policy).count() == 4

def test_get_policies_quality_filter(client, db):
    """품질 필터링 테스트 (3-A: 기본 valid만, include_partial=True시 partial 포함)"""
    import_seed_data(db, SEED_FILE_PATH)

    # 1. 기본 조회 (include_partial=False) -> valid 2건만 반환
    response = client.get("/api/v1/policies")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["data_quality_status"] == "valid" for item in data["items"])

    # 2. partial 포함 조회 (include_partial=True) -> valid 2건 + partial 2건 = 4건 반환
    response_partial = client.get("/api/v1/policies?include_partial=true")
    assert response_partial.status_code == 200
    data_partial = response_partial.json()
    assert data_partial["total"] == 4

def test_get_policy_detail_no_provenance(client, db):
    """일반 사용자 API 응답 패킷에 provenance 비노출 검증 (4-A)"""
    import_seed_data(db, SEED_FILE_PATH)
    first_policy = db.query(Policy).first()

    response = client.get(f"/api/v1/policies/{first_policy.id}")
    assert response.status_code == 200
    detail = response.json()
    assert "provenance" not in detail
    assert detail["title"] == first_policy.title

def test_policy_date_and_text(client, db):
    """Date 파싱 및 원문 Text 동시 보존 검증 (5-A)"""
    import_seed_data(db, SEED_FILE_PATH)
    valid_policy = db.query(Policy).filter(Policy.data_quality_status == "valid").first()

    response = client.get(f"/api/v1/policies/{valid_policy.id}")
    assert response.status_code == 200
    data = response.json()
    assert "application_period_text" in data
    assert "application_start" in data
    assert "application_end" in data
