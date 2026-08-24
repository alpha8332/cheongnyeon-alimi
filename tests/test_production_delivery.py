from __future__ import annotations

import json
import sys
import tempfile
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[1]
for import_root in (ROOT, ROOT / "backend"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.database import Base
from app.models.collection_run import CollectionRun
from scripts.build_production_release_manifest import build_manifest
from scripts.build_public_bootstrap_dataset import (
    DEFAULT_CONTRACT,
    load_source_contract,
    verify_release,
    write_release,
)
from scripts.build_public_dataset_pointer import build_pointer, validate_pointer
from scripts.promote_public_dataset import (
    DatasetPromotionError,
    assert_published_source_coverage,
    assert_promotable_runs,
)
COMPOSE = yaml.safe_load(
    (ROOT / "compose.production.yaml").read_text(encoding="utf-8")
)


def public_program() -> dict[str, object]:
    fixture = ROOT / "data/fixtures/normalized/programs.json"
    program = deepcopy(json.loads(fixture.read_text(encoding="utf-8"))[0])
    program["source_id"] = "bokjiro-central-welfare-api"
    program["source_name"] = "한국사회보장정보원 중앙부처복지서비스"
    program["external_id"] = "TEST-PRODUCTION-001"
    program["source_url"] = "https://example.invalid/public/TEST-PRODUCTION-001"
    for collection_name in (
        "requirements", "exclusions", "preferences", "documents", "unknowns",
        "institutional_contacts",
    ):
        for item in program["eligibility_summary"][collection_name]:
            for evidence in item["evidence"]:
                evidence["source_id"] = program["source_id"]
                evidence["source_url"] = program["source_url"]
    for provenance in program["provenance"]:
        provenance["source_url"] = "https://example.invalid/public"
    return program


def _collection_run(
    *,
    status: str,
    started_at: datetime,
    is_complete_snapshot: bool | None = None,
    source_id: str = "bokjiro-central-welfare-api",
) -> CollectionRun:
    return CollectionRun(
        run_id=uuid4(),
        source_id=source_id,
        run_type="collection",
        trigger_type="scheduler",
        status=status,
        is_complete_snapshot=(
            status == "succeeded"
            if is_complete_snapshot is None
            else is_complete_snapshot
        ),
        started_at=started_at,
        finished_at=(started_at + timedelta(minutes=1)),
        requested_count=1,
        raw_document_count=1,
        extracted_count=1,
        accepted_count=1 if status == "succeeded" else 0,
        partial_count=0,
        invalid_count=0 if status == "succeeded" else 1,
        duplicate_count=0,
        rejected_count=0,
        inserted_count=1 if status == "succeeded" else 0,
        updated_count=0,
        unchanged_count=0,
        skipped_count=0,
        failed_count=0,
    )


def test_production_compose_uses_release_images_and_one_public_gateway():
    services = COMPOSE["services"]
    assert all("build" not in service for service in services.values())
    assert "${BACKEND_IMAGE:?" in services["backend"]["image"]
    assert "${FRONTEND_IMAGE:?" in services["frontend"]["image"]
    assert "ports" not in services["backend"]
    assert "ports" not in services["frontend"]
    assert "ports" not in services["database"]
    assert services["nginx"]["ports"] == [
        "127.0.0.1:${NGINX_HOST_PORT:-8080}:8080"
    ]
    assert services["nginx"]["user"] == "101:101"
    assert COMPOSE["networks"]["database"]["internal"] is True
    assert COMPOSE["networks"]["queue"]["internal"] is True


def test_production_chain_migrates_and_verifies_before_serving():
    services = COMPOSE["services"]
    assert services["migrate"]["depends_on"]["database"]["condition"] == (
        "service_healthy"
    )
    migrate_command = services["migrate"]["command"][-1]
    assert migrate_command.index("alembic upgrade head") < migrate_command.index(
        "python -m app.cli.import_regions"
    )
    bootstrap = services["public-dataset-bootstrap"]
    assert bootstrap["depends_on"]["migrate"]["condition"] == (
        "service_completed_successfully"
    )
    assert bootstrap["volumes"][0]["read_only"] is True
    assert bootstrap["command"][-1].index("--verify-manifest") < (
        bootstrap["command"][-1].index("app.cli.import_public_dataset")
    )
    assert services["backend"]["depends_on"]["public-dataset-bootstrap"][
        "condition"
    ] == "service_completed_successfully"
    assert "collector-egress" in services["collection-worker"]["networks"]
    assert "collector-egress" not in services["backend"]["networks"]


def test_nginx_routes_api_and_frontend_with_health_endpoint():
    config = (ROOT / "deployment/nginx/nginx.conf").read_text(encoding="utf-8")
    assert "location = /health" in config
    assert "location /api/" in config
    assert "proxy_pass http://backend_upstream;" in config
    assert "location /" in config
    assert "proxy_pass http://frontend_upstream;" in config


def test_latest_partial_or_failed_collection_blocks_promotion():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    succeeded = _collection_run(status="succeeded", started_at=now)
    partial = _collection_run(
        status="partial_failure", started_at=now + timedelta(minutes=2)
    )
    with Session(engine) as session:
        session.add_all((succeeded, partial))
        session.commit()
        try:
            assert_promotable_runs(
                session,
                source_ids={"bokjiro-central-welfare-api"},
                run_ids=[succeeded.run_id],
            )
        except DatasetPromotionError as exc:
            assert "not the latest" in str(exc)
        else:
            raise AssertionError("an older success must not be promoted")
        try:
            assert_promotable_runs(
                session,
                source_ids={"bokjiro-central-welfare-api"},
                run_ids=[partial.run_id],
            )
        except DatasetPromotionError as exc:
            assert "partial_failure" in str(exc)
        else:
            raise AssertionError("a partial collection must not be promoted")


def test_latest_clean_success_authorizes_exact_source_set():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    run = _collection_run(
        status="succeeded", started_at=datetime.now(timezone.utc)
    )
    with Session(engine) as session:
        session.add(run)
        session.commit()
        evidence = assert_promotable_runs(
            session,
            source_ids={"bokjiro-central-welfare-api"},
            run_ids=[run.run_id],
        )
    assert evidence == {"bokjiro-central-welfare-api": str(run.run_id)}


def test_latest_clean_success_authorizes_all_public_sources():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    bokjiro = _collection_run(status="succeeded", started_at=now)
    incheon = _collection_run(
        status="succeeded",
        started_at=now,
        source_id="data-go-kr-incheon-youth-programs",
    )
    youthcenter = _collection_run(
        status="succeeded",
        started_at=now,
        source_id="youthcenter-api",
    )
    with Session(engine) as session:
        session.add_all((bokjiro, youthcenter, incheon))
        session.commit()
        evidence = assert_promotable_runs(
            session,
            source_ids={
                "bokjiro-central-welfare-api",
                "youthcenter-api",
                "data-go-kr-incheon-youth-programs",
            },
            run_ids=[bokjiro.run_id, youthcenter.run_id, incheon.run_id],
        )
    assert evidence == {
        "bokjiro-central-welfare-api": str(bokjiro.run_id),
        "youthcenter-api": str(youthcenter.run_id),
        "data-go-kr-incheon-youth-programs": str(incheon.run_id),
    }


def test_promotion_requires_every_licensed_source_in_the_artifact():
    required = {
        "bokjiro-central-welfare-api",
        "youthcenter-api",
        "data-go-kr-incheon-youth-programs",
    }
    manifest: dict[str, object] = {
        "sources": [
            {"source_id": "bokjiro-central-welfare-api", "row_count": 457},
            {"source_id": "youthcenter-api", "row_count": 2000},
        ]
    }

    try:
        assert_published_source_coverage(manifest, source_ids=required)
    except DatasetPromotionError as exc:
        assert "data-go-kr-incheon-youth-programs" in str(exc)
    else:
        raise AssertionError("a Source-missing artifact must not be promoted")

    sources = manifest["sources"]
    assert isinstance(sources, list)
    sources.append(
        {
            "source_id": "data-go-kr-incheon-youth-programs",
            "row_count": 10,
        }
    )
    assert_published_source_coverage(manifest, source_ids=required)


def test_limited_success_cannot_be_promoted_as_complete_snapshot():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    run = _collection_run(
        status="succeeded",
        started_at=datetime.now(timezone.utc),
        is_complete_snapshot=False,
    )
    with Session(engine) as session:
        session.add(run)
        session.commit()
        try:
            assert_promotable_runs(
                session,
                source_ids={"bokjiro-central-welfare-api"},
                run_ids=[run.run_id],
            )
        except DatasetPromotionError as exc:
            assert "not a complete source snapshot" in str(exc)
        else:
            raise AssertionError("a limited success must not be promoted")


def test_pointer_and_production_manifest_bind_all_release_identities():
    contract = load_source_contract(DEFAULT_CONTRACT)
    with tempfile.TemporaryDirectory() as temporary_directory:
        output = Path(temporary_directory)
        _, manifest_path, _ = write_release(
            records=[public_program()],
            contract=contract,
            contract_path=DEFAULT_CONTRACT,
            output_dir=output,
            dataset_version="public-bootstrap-20260824-abcdef0",
            generated_at="2026-08-24T00:00:00Z",
            git_sha="a" * 40,
        )
        verify_release(manifest_path)
        pointer = build_pointer(
            manifest_path=manifest_path,
            manifest_url=(
                "https://github.com/example/project/releases/download/"
                "dataset-public-bootstrap-20260824-abcdef0/"
                "public-bootstrap-20260824-abcdef0.manifest.json"
            ),
            updated_at="2026-08-24T01:00:00Z",
        )
        validate_pointer(pointer)
        pointer_path = output / "public-dataset-pointer.json"
        pointer_path.write_text(json.dumps(pointer), encoding="utf-8")
        release = build_manifest(
            release_version="v1.0.0",
            git_sha="b" * 40,
            backend_name="ghcr.io/example/project-backend",
            backend_digest="sha256:" + "c" * 64,
            frontend_name="ghcr.io/example/project-frontend",
            frontend_digest="sha256:" + "d" * 64,
            dataset_pointer_path=pointer_path,
            generated_at="2026-08-24T02:00:00Z",
        )
    assert release["alembic_revision"] == "20260824_0011"
    assert release["dataset"]["version"] == pointer["dataset_version"]
    assert release["images"]["backend"]["digest"] == "sha256:" + "c" * 64


def test_ci_release_and_rollback_workflows_are_fail_closed():
    workflows = ROOT / ".github/workflows"
    ci = (workflows / "ci.yml").read_text(encoding="utf-8")
    release = (workflows / "production-release.yml").read_text(encoding="utf-8")
    dataset = (workflows / "public-dataset-release.yml").read_text(encoding="utf-8")
    rollback = (workflows / "public-dataset-rollback.yml").read_text(encoding="utf-8")
    assert "python -m pytest -q" in ci
    assert "npm run lint" in ci and "npm run build" in ci
    assert "docker/build-push-action@v7" in release
    assert "provenance: true" in release and "sbom: true" in release
    assert "docker compose -f compose.production.yaml up --detach --wait" in release
    assert "scripts/promote_public_dataset.py" in dataset
    assert "runs-on: ubuntu-latest" in dataset
    assert "environment: production-data" in dataset
    assert "scripts/run_complete_collection.py" in dataset
    assert "python -m app.cli.import_regions" in dataset
    assert dataset.index("python -m app.cli.import_regions") < dataset.index(
        "scripts/run_complete_collection.py"
    )
    assert "scripts/audit_public_dataset_parity.py" in dataset
    assert "--require-parity" in dataset
    assert "python -m app.cli.import_public_dataset" in dataset
    assert dataset.index("promote_public_dataset.py") < dataset.index(
        "python -m app.cli.import_public_dataset"
    ) < dataset.index("audit_public_dataset_parity.py")
    assert dataset.index("audit_public_dataset_parity.py") < dataset.index(
        'gh release create "dataset-${DATASET_VERSION}"'
    )
    assert "youthcenter-api" in dataset
    assert "data-go-kr-incheon-youth-programs" in dataset
    assert dataset.count('--collection-run-id "$') == 3
    assert "BOKJIRO_API_KEY: ${{ secrets.BOKJIRO_API_KEY }}" in dataset
    assert "YOUTHCENTER_API_KEY: ${{ secrets.YOUTHCENTER_API_KEY }}" in dataset
    assert "PRODUCTION_DATASET_DATABASE_URL" not in dataset
    assert "self-hosted" not in dataset
    assert "postgres:" in dataset and "redis:" in dataset
    assert 'kill -0 "$worker_pid"' in dataset
    assert 'cat "$RUNNER_TEMP/collection-worker.log"' in dataset
    assert "if ! collection_json=$(" in dataset
    assert "grep -qE ' ready\\.$'" in dataset
    assert "inspect ping" not in dataset
    assert dataset.index("--verify-manifest") < dataset.rindex("dataset-latest")
    assert "scripts/build_public_dataset_pointer.py" in rollback
    assert rollback.index("--verify-manifest") < rollback.index("--clobber")
