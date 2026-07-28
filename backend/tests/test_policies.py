import pytest
import json
from pathlib import Path

from sqlalchemy import select

from app.models.policy import Policy
from app.services.seed_importer import import_programs, import_seed_data

SEED_FILE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "seeds" / "initial_programs.json"


def seed_programs():
    return json.loads(SEED_FILE_PATH.read_text(encoding="utf-8"))


def test_import_seed_and_upsert(db):
    """Seed 파일 적재 및 Re-import 시 Upsert 동작 검증 (1-A, 2-A)"""
    first = import_seed_data(db, SEED_FILE_PATH)
    assert first.total == 4
    assert first.inserted == 4
    assert first.updated == 0
    assert first.unchanged == 0
    assert first.skipped == 0
    assert first.failed == 0
    assert db.query(Policy).count() == 4

    timestamps = {
        (policy.source_id, policy.external_id): policy.updated_at
        for policy in db.scalars(select(Policy)).all()
    }
    second = import_seed_data(db, SEED_FILE_PATH)
    assert second.total == 4
    assert second.inserted == 0
    assert second.updated == 0
    assert second.unchanged == 4
    assert second.skipped == 0
    assert second.failed == 0
    assert db.query(Policy).count() == 4
    assert timestamps == {
        (policy.source_id, policy.external_id): policy.updated_at
        for policy in db.scalars(select(Policy)).all()
    }


def test_import_programs_distinguishes_updated_from_unchanged(db):
    programs = seed_programs()
    first = import_programs(db, programs)
    programs[0]["title"] = "변경된 합성 정책명"
    second = import_programs(db, programs)

    assert first.inserted == 4
    assert second.inserted == 0
    assert second.updated == 1
    assert second.unchanged == 3
    assert db.scalar(
        select(Policy.title).where(
            Policy.source_id == programs[0]["source_id"],
            Policy.external_id == programs[0]["external_id"],
        )
    ) == "변경된 합성 정책명"


def test_import_programs_preserves_source_scoped_identity(db):
    program = seed_programs()[0]
    other_source = dict(program)
    other_source["source_id"] = "bokjiro-central-welfare-api"

    result = import_programs(db, [program, other_source])

    assert result.inserted == 2
    assert db.query(Policy).count() == 2


def test_current_api_sources_reject_null_external_id(db):
    programs = seed_programs()[:2]
    programs[0]["source_id"] = "youthcenter-api"
    programs[0]["external_id"] = None
    programs[1]["source_id"] = "bokjiro-central-welfare-api"
    programs[1]["external_id"] = ""

    result = import_programs(db, programs)

    assert result.total == 2
    assert result.skipped == 2
    assert result.inserted == 0
    assert result.failed == 0
    assert {issue.code for issue in result.issues} == {"missing_external_id"}
    assert db.query(Policy).count() == 0


def test_database_write_failure_is_counted_without_payload_exposure(db):
    program = seed_programs()[0]
    program["data_quality_status"] = "unknown"

    result = import_programs(db, [program])

    assert result.failed == 1
    assert result.inserted == 0
    assert result.issues[0].code == "database_write_failed"
    assert result.issues[0].error_type == "StatementError"
    assert db.query(Policy).count() == 0


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
