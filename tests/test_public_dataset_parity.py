from __future__ import annotations

import json
import sys
from copy import deepcopy
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[1]
for import_root in (ROOT, ROOT / "backend"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.database import Base  # noqa: E402
from app.models.policy import Policy  # noqa: E402
from app.models.public_dataset import (  # noqa: E402
    PublicDatasetInstallation,
    PublicDatasetMembership,
)
from collectors.normalized import NormalizedProgram  # noqa: E402
from scripts import audit_public_dataset_parity as parity_module  # noqa: E402
from scripts.audit_public_dataset_parity import (  # noqa: E402
    audit_database,
    build_report,
)
from scripts.build_public_bootstrap_dataset import (  # noqa: E402
    DEFAULT_CONTRACT,
    load_source_contract,
)


FIXTURE_PATH = ROOT / "data/fixtures/normalized/programs.json"


def _policy(
    policy_id: int,
    *,
    source_id: str,
    title: str,
    summary: str = "공개 정책 요약",
    application_end: date | None = None,
) -> Policy:
    program = deepcopy(json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))[0])
    program["source_id"] = source_id
    program["source_name"] = source_id
    program["external_id"] = f"POLICY-{policy_id}"
    program["title"] = title
    program["summary"] = summary
    program["source_url"] = f"https://example.invalid/policies/{policy_id}"
    for collection_name in (
        "requirements",
        "exclusions",
        "preferences",
        "documents",
        "unknowns",
        "institutional_contacts",
    ):
        for item in program["eligibility_summary"][collection_name]:
            for evidence in item["evidence"]:
                evidence["source_id"] = source_id
                evidence["source_url"] = program["source_url"]
    for provenance in program["provenance"]:
        provenance["source_url"] = program["source_url"]
    program["application_end"] = (
        application_end.isoformat() if application_end is not None else None
    )
    values = {
        field_name: program[field_name]
        for field_name in NormalizedProgram.FIELD_NAMES
        if field_name != "region_rules"
    }
    for field_name in ("application_start", "application_end"):
        if values[field_name] is not None:
            values[field_name] = date.fromisoformat(values[field_name])
    values["collected_at"] = datetime.fromisoformat(program["collected_at"])
    return Policy(id=policy_id, **values)


def test_parity_report_fails_closed_on_source_and_safety_gaps():
    contract = load_source_contract(DEFAULT_CONTRACT)
    policies = [
        _policy(
            1,
            source_id="youthcenter-api",
            title="공통 청년 정책",
        ),
        _policy(
            2,
            source_id="youthcenter-api",
            title="연락처 포함 정책",
            summary="담당자 test@example.com",
        ),
        _policy(
            3,
            source_id="regional-busan-youth-platform",
            title="공통 청년 정책",
        ),
        _policy(
            4,
            source_id="regional-busan-youth-platform",
            title="부산 고유 정책",
        ),
    ]

    report = build_report(
        policies,
        rules_by_policy={},
        contract=contract,
        as_of=date(2026, 8, 24),
    )

    assert report["summary"] == {
        "parity_status": "blocked",
        "user_visible_row_count": 4,
        "public_source_candidate_row_count": 2,
        "publishable_row_count": 1,
        "excluded_source_row_count": 2,
        "content_safety_excluded_row_count": 1,
        "content_safety_reason_row_counts": {"email": 1},
        "exact_title_review_count": 1,
        "unique_title_gap_count": 1,
        "parity_gap_row_count": 3,
    }
    busan = next(
        item
        for item in report["sources"]
        if item["source_id"] == "regional-busan-youth-platform"
    )
    assert busan["reason_code"] == "no_explicit_open_license"
    assert busan["exact_title_review_count"] == 1
    assert busan["unique_title_gap_count"] == 1


def test_parity_report_passes_when_every_visible_record_is_publishable():
    contract = load_source_contract(DEFAULT_CONTRACT)
    report = build_report(
        [
            _policy(
                1,
                source_id="bokjiro-central-welfare-api",
                title="공개 정책",
            )
        ],
        rules_by_policy={},
        contract=contract,
        as_of=date(2026, 8, 24),
    )

    assert report["summary"]["parity_status"] == "pass"
    assert report["summary"]["parity_gap_row_count"] == 0


def test_database_audit_uses_active_membership_and_public_lifecycle(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "parity.sqlite3"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            [
                _policy(
                    1,
                    source_id="bokjiro-central-welfare-api",
                    title="현재 정책",
                ),
                _policy(
                    2,
                    source_id="bokjiro-central-welfare-api",
                    title="과거 정책",
                    application_end=date(2026, 8, 23),
                ),
                _policy(
                    3,
                    source_id="regional-busan-youth-platform",
                    title="비공개 로컬 정책",
                ),
            ]
        )
        session.add(
            PublicDatasetInstallation(
                dataset_version="public-bootstrap-20260824-abcdef0",
                manifest_sha256="a" * 64,
                artifact_sha256="b" * 64,
                expected_policy_count=2,
                status="active",
                activated_at=datetime(2026, 8, 24, 0, 0),
            )
        )
        session.add_all(
            [
                PublicDatasetMembership(
                    dataset_version="public-bootstrap-20260824-abcdef0",
                    source_id="bokjiro-central-welfare-api",
                    external_id="POLICY-1",
                    policy_id=1,
                ),
                PublicDatasetMembership(
                    dataset_version="public-bootstrap-20260824-abcdef0",
                    source_id="bokjiro-central-welfare-api",
                    external_id="POLICY-2",
                    policy_id=2,
                ),
            ]
        )
        session.commit()
    engine.dispose()

    monkeypatch.setattr(
        parity_module,
        "policy_to_normalized_program",
        lambda policy, _rules: {"source_id": policy.source_id},
    )
    report = audit_database(
        database_url,
        contract=load_source_contract(DEFAULT_CONTRACT),
        as_of=date(2026, 8, 24),
    )

    assert report["summary"]["parity_status"] == "pass"
    assert report["summary"]["user_visible_row_count"] == 1
    assert report["comparison_contract"]["dataset_scope"] == (
        "active_public_dataset_membership"
    )
