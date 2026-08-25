from datetime import datetime, timedelta, timezone

from collectors import default_registry

from app.models.collection_run import CollectionRun
from app.models.policy import Policy
from app.models.public_dataset import (
    PublicDatasetInstallation,
    PublicDatasetMembership,
)
from app.services.collector_runtime_status import CollectorWorkerProbe
from app.services.collector_catalog import COLLECTOR_CATALOG
from app.services.manual_collection_contract import MANUAL_COLLECTION_SOURCE_IDS


API_PATH = "/api/v1/admin/collectors"


def _admin_headers(client) -> dict[str, str]:
    response = client.post("/api/v1/admin/session", json={"pin": "0000"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _ready_probe() -> CollectorWorkerProbe:
    return CollectorWorkerProbe(
        broker_available=True,
        worker_count=1,
        registered_source_ids=frozenset(default_registry.source_ids()),
        credential_configured={
            "bokjiro-central-welfare-api": True,
            "youthcenter-api": False,
        },
    )


def test_collector_catalog_matches_registered_and_manual_sources():
    catalog_ids = tuple(item.source_id for item in COLLECTOR_CATALOG)
    assert catalog_ids == default_registry.source_ids()
    assert catalog_ids == MANUAL_COLLECTION_SOURCE_IDS


def test_admin_collectors_requires_authentication(client):
    response = client.get(API_PATH)
    assert response.status_code == 401


def test_admin_collectors_reports_safe_runtime_states(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.admin_collector.probe_collector_workers",
        _ready_probe,
    )

    response = client.get(API_PATH, headers=_admin_headers(client))

    assert response.status_code == 200
    payload = response.json()
    assert payload["queue"] == {
        "queue_name": "collection",
        "broker_available": True,
        "worker_available": True,
        "worker_count": 1,
    }
    assert len(payload["collectors"]) == 11
    by_source = {item["source_id"]: item for item in payload["collectors"]}
    assert by_source["bokjiro-central-welfare-api"]["runtime_status"] == "ready"
    assert by_source["bokjiro-central-welfare-api"]["credential_status"] == "configured"
    assert by_source["youthcenter-api"]["runtime_status"] == "configuration_required"
    assert by_source["youthcenter-api"]["credential_status"] == "missing"
    assert by_source["regional-busan-youth-platform"]["credential_status"] == "not_required"

    serialized = response.text
    assert "API_KEY" not in serialized
    assert "credential_configured" not in serialized


def test_admin_collectors_reports_public_membership_and_run_history(
    client,
    db,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.admin_collector.probe_collector_workers",
        _ready_probe,
    )
    now = datetime.now(timezone.utc)
    policy = Policy(
        source_id="youthcenter-api",
        source_name="온통청년",
        external_id="collector-status-1",
        title="수집기 상태 테스트 정책",
        source_url="https://example.invalid/policy",
        collected_at=now,
        data_quality_status="valid",
    )
    db.add(policy)
    db.flush()
    installation = PublicDatasetInstallation(
        dataset_version="collector-status-test",
        manifest_sha256="a" * 64,
        artifact_sha256="b" * 64,
        expected_policy_count=1,
        status="active",
        activated_at=now,
    )
    db.add(installation)
    db.flush()
    db.add(
        PublicDatasetMembership(
            dataset_version=installation.dataset_version,
            source_id=policy.source_id,
            external_id=policy.external_id,
            policy_id=policy.id,
        )
    )
    run = CollectionRun(
        source_id="youthcenter-api",
        run_type="collection",
        trigger_type="admin",
        started_at=now - timedelta(hours=3),
        status="running",
        requested_count=25,
        inserted_count=3,
    )
    db.add(run)
    db.commit()

    response = client.get(API_PATH, headers=_admin_headers(client))

    assert response.status_code == 200
    by_source = {
        item["source_id"]: item for item in response.json()["collectors"]
    }
    youthcenter = by_source["youthcenter-api"]
    assert youthcenter["public_policy_count"] == 1
    assert youthcenter["active_run"]["run_id"] == str(run.run_id)
    assert youthcenter["active_run"]["is_stale"] is True
    assert youthcenter["last_run"]["inserted_count"] == 3
    assert by_source["cheonan-youthcenter-web"]["public_policy_count"] == 0


def test_admin_collectors_marks_worker_offline(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.admin_collector.probe_collector_workers",
        lambda: CollectorWorkerProbe(
            broker_available=False,
            worker_count=0,
            registered_source_ids=frozenset(),
            credential_configured={},
        ),
    )

    response = client.get(API_PATH, headers=_admin_headers(client))

    assert response.status_code == 200
    payload = response.json()
    assert payload["queue"]["broker_available"] is False
    assert payload["queue"]["worker_available"] is False
    assert {item["runtime_status"] for item in payload["collectors"]} == {
        "unavailable"
    }
