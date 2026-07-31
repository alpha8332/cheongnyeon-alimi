import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

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
    db.commit()

    timestamps = {
        (policy.source_id, policy.external_id): policy.updated_at
        for policy in db.scalars(select(Policy)).all()
    }
    db.commit()
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


def test_import_programs_enforces_timestamp_order_and_nondecreasing_updates(
    db,
):
    program = seed_programs()[0]
    first_instant = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)

    with patch(
        "app.services.seed_importer.utc_now",
        return_value=first_instant,
    ):
        first = import_programs(db, [program])

    policy = db.scalar(select(Policy))
    assert first.inserted == 1
    assert policy.created_at == policy.updated_at
    created_at = policy.created_at
    updated_at = policy.updated_at
    db.commit()

    with patch(
        "app.services.seed_importer.utc_now",
        return_value=datetime(2026, 7, 30, 2, 0, tzinfo=timezone.utc),
    ):
        unchanged = import_programs(db, [program])

    policy = db.scalar(select(Policy))
    assert unchanged.unchanged == 1
    assert policy.created_at == created_at
    assert policy.updated_at == updated_at
    db.commit()

    changed_program = dict(program)
    changed_program["title"] = "시계 역행 중 변경된 합성 정책명"
    with patch(
        "app.services.seed_importer.utc_now",
        return_value=datetime(2026, 7, 30, 0, 0, tzinfo=timezone.utc),
    ):
        changed_during_clock_rollback = import_programs(
            db,
            [changed_program],
        )

    policy = db.scalar(select(Policy))
    assert changed_during_clock_rollback.updated == 1
    assert policy.created_at == created_at
    assert policy.updated_at == updated_at
    db.commit()

    changed_program["title"] = "시계 정상화 후 변경된 합성 정책명"
    with patch(
        "app.services.seed_importer.utc_now",
        return_value=datetime(2026, 7, 30, 3, 0, tzinfo=timezone.utc),
    ):
        changed_after_clock_recovery = import_programs(
            db,
            [changed_program],
        )

    policy = db.scalar(select(Policy))
    assert changed_after_clock_recovery.updated == 1
    assert policy.created_at == created_at
    assert policy.updated_at > updated_at


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
    assert result.skipped == 1
    assert result.rejected == 1
    assert result.inserted == 0
    assert result.failed == 0
    assert "missing_external_id" in {
        issue.code for issue in result.issues
    }
    assert db.query(Policy).count() == 0


def test_database_write_failure_is_counted_without_payload_exposure(db):
    program = seed_programs()[0]
    program["data_quality_status"] = "unknown"

    result = import_programs(db, [program])

    assert result.rejected == 1
    assert result.failed == 0
    assert result.inserted == 0
    assert result.issues[0].code == "schema_enum"
    assert result.issues[0].path == "$[0].data_quality_status"
    assert db.query(Policy).count() == 0


def test_schema_failure_rejects_the_whole_batch_without_coercion(db):
    programs = seed_programs()[:2]
    programs[1].pop("application_start")

    result = import_programs(db, programs)

    assert result.total == 2
    assert result.validated == 2
    assert result.rejected == 1
    assert result.inserted == 0
    assert result.committed is False
    assert any(
        issue.code == "schema_required"
        and issue.path == "$[1].application_start"
        for issue in result.issues
    )
    assert db.query(Policy).count() == 0


def test_invalid_quality_status_is_rejected_with_no_partial_write(db):
    programs = seed_programs()[:2]
    programs[1]["data_quality_status"] = "invalid"

    result = import_programs(db, programs)

    assert result.rejected == 1
    assert result.inserted == 0
    assert result.committed is False
    assert db.query(Policy).count() == 0


def test_dry_run_projects_results_and_rolls_back(db):
    result = import_programs(db, seed_programs(), dry_run=True)

    assert result.validated == 4
    assert result.inserted == 4
    assert result.rejected == 0
    assert result.failed == 0
    assert result.dry_run is True
    assert result.committed is False
    assert db.query(Policy).count() == 0


def test_database_failure_rolls_back_prior_batch_writes(db):
    programs = seed_programs()[:2]
    from app.services import seed_importer

    portable_upsert = seed_importer._portable_upsert
    calls = 0

    def fail_second_write(session, values):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise SQLAlchemyError(
                "postgresql://user:do-not-print@example.invalid/db"
            )
        return portable_upsert(session, values)

    with patch(
        "app.services.seed_importer._portable_upsert",
        side_effect=fail_second_write,
    ):
        result = import_programs(db, programs)

    assert result.inserted == 0
    assert result.updated == 0
    assert result.failed == 1
    assert result.committed is False
    assert result.issues[0].code == "database_write_failed"
    assert result.issues[0].error_type == "SQLAlchemyError"
    assert "do-not-print" not in repr(result)
    assert db.query(Policy).count() == 0


def test_seed_root_must_be_an_array(db, tmp_path):
    seed_path = tmp_path / "invalid-root.json"
    seed_path.write_text("{}", encoding="utf-8")

    result = import_seed_data(db, seed_path)

    assert result.total == 0
    assert result.rejected == 1
    assert result.issues[0].code == "seed_root_not_array"
    assert result.issues[0].path == "$"
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
