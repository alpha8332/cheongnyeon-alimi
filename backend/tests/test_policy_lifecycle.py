from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.models.policy import Policy
from app.repositories.policy import PolicyRepository
from app.services.runtime_importer import _snapshot_lifecycle_is_complete
from app.services.seed_importer import ImportResult, import_programs
from collectors.runtime import RuntimeReplayResult


def _policy_values(
    external_id: str,
    *,
    application_end: date | None = None,
    inactive_at: datetime | None = None,
    data_quality_status: str = "valid",
) -> dict[str, object]:
    observed = datetime(2026, 8, 24, tzinfo=timezone.utc)
    return {
        "schema_version": "1.2.0",
        "source_id": "lifecycle-source",
        "source_name": "Lifecycle source",
        "external_id": external_id,
        "title": f"Policy {external_id}",
        "categories": [],
        "keywords": [],
        "life_stages": [],
        "target_groups": [],
        "regions": [],
        "education_statuses": [],
        "employment_statuses": [],
        "required_conditions": [],
        "preferred_conditions": [],
        "excluded_conditions": [],
        "source_url": f"https://example.test/{external_id}",
        "collected_at": observed,
        "provenance": [
            {
                "raw_document_id": "a" * 32,
                "document_role": "list_item",
                "content_hash": f"sha256:{'b' * 64}",
                "collected_at": observed.isoformat(),
                "source_url": f"https://example.test/{external_id}",
            }
        ],
        "data_quality_status": data_quality_status,
        "application_end": application_end,
        "last_seen_at": observed,
        "last_verified_at": observed,
        "inactive_at": inactive_at,
    }


def _normalized_program(external_id: str) -> dict[str, object]:
    observed = "2026-08-24T00:00:00+00:00"
    return {
        "schema_version": "1.2.0",
        "source_id": "lifecycle-source",
        "source_name": "Lifecycle source",
        "external_id": external_id,
        "title": f"Policy {external_id}",
        "organization": None,
        "summary": None,
        "category_text": None,
        "categories": [],
        "keywords": [],
        "life_stages": [],
        "target_groups": [],
        "application_period_text": None,
        "application_start": None,
        "application_end": None,
        "application_schedule": None,
        "application_status": None,
        "region_text": None,
        "regions": [],
        "region_rules": [],
        "coverage_scope": "unknown",
        "age_min": None,
        "age_max": None,
        "age_condition_text": None,
        "eligibility_text": None,
        "eligibility_summary": {
            "coverage": "unknown",
            "requirements": [],
            "exclusions": [],
            "preferences": [],
            "documents": [],
            "unknowns": [],
            "institutional_contacts": [],
        },
        "support_content": None,
        "application_method": None,
        "education_statuses": [],
        "employment_statuses": [],
        "required_conditions": [],
        "preferred_conditions": [],
        "excluded_conditions": [],
        "source_url": f"https://example.test/{external_id}",
        "collected_at": observed,
        "provenance": [
            {
                "raw_document_id": "a" * 32,
                "document_role": "list_item",
                "content_hash": f"sha256:{'b' * 64}",
                "collected_at": observed,
                "source_url": f"https://example.test/{external_id}",
            }
        ],
        "data_quality_status": "partial",
    }


def test_public_repository_excludes_expired_and_inactive_rows(
    db,
    activate_all_policies,
) -> None:
    db.add_all(
        [
            Policy(**_policy_values("active")),
            Policy(
                **_policy_values(
                    "expired",
                    application_end=date.today() - timedelta(days=1),
                )
            ),
            Policy(
                **_policy_values(
                    "inactive",
                    inactive_at=(
                        datetime(2026, 8, 24, tzinfo=timezone.utc)
                        + timedelta(hours=1)
                    ),
                )
            ),
        ]
    )
    db.commit()
    activate_all_policies()

    page = PolicyRepository(db).list(
        quality_statuses=("valid",),
        page=1,
        limit=10,
    )

    assert page.total == 1
    assert [policy.external_id for policy in page.items] == ["active"]


def test_successful_reappearance_clears_inactive_and_refreshes_verification(
    db,
) -> None:
    old = datetime(2026, 8, 24, tzinfo=timezone.utc)
    policy = Policy(
        **_policy_values(
            "returns",
            inactive_at=old + timedelta(hours=1),
            data_quality_status="partial",
        )
    )
    db.add(policy)
    db.commit()

    result = import_programs(db, [_normalized_program("returns")])
    db.refresh(policy)

    assert result.updated == 1
    assert policy.inactive_at is None
    assert policy.last_seen_at.replace(tzinfo=timezone.utc) == old
    assert policy.last_verified_at.replace(tzinfo=timezone.utc) >= old


def test_only_complete_successful_snapshot_allows_missing_inactivation() -> None:
    replay = RuntimeReplayResult(
        source_id="lifecycle-source",
        raw_document_count=1,
        extracted_count=1,
        valid_count=1,
        partial_count=0,
        invalid_count=0,
        programs=(),
        issues=(),
        source_snapshot_complete=True,
    )
    success = ImportResult(total=1, accepted=1, committed=True)

    assert _snapshot_lifecycle_is_complete(replay, database=success)
    assert not _snapshot_lifecycle_is_complete(
        replace(replay, source_snapshot_complete=False),
        database=success,
    )
    assert not _snapshot_lifecycle_is_complete(
        replace(replay, invalid_count=1),
        database=success,
    )
    assert not _snapshot_lifecycle_is_complete(
        replay,
        database=replace(success, rejected=1, committed=False),
    )
