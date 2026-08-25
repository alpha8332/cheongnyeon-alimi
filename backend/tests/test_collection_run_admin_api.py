import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.models.collection_run import CollectionRun
from app.services.admin_access import clear_rate_limit_state
from app.api.deps import get_current_admin_payload
from app.api.v1.endpoints.collection_run_admin import router as collection_run_admin_router
from app.services.collection_queue import CollectionQueuePublishError

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state(db):
    clear_rate_limit_state()
    original_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = "development"

    # Override get_db dependency to use the test SQLite db session
    app.dependency_overrides[get_db] = lambda: db

    yield

    clear_rate_limit_state()
    settings.ENVIRONMENT = original_env
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def admin_token():
    response = client.post("/api/v1/admin/session", json={"pin": "0000"})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def collection_queue_publisher(monkeypatch):
    task = Mock()
    monkeypatch.setattr(
        "app.api.v1.endpoints.collection_run_admin.publish_collection_run",
        task,
    )
    return task


@pytest.fixture
def sample_collection_runs(db):
    # Clean up existing test runs
    db.query(CollectionRun).delete()
    db.commit()

    run1 = CollectionRun(
        run_id=uuid.uuid4(),
        source_id="youthcenter",
        run_type="collection",
        trigger_type="admin",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        finished_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        status="succeeded",
        requested_count=100,
        raw_document_count=100,
        extracted_count=98,
        accepted_count=95,
        inserted_count=80,
        updated_count=15,
        failed_count=0,
    )

    # Stale run (started 3 hours ago, still running)
    run2 = CollectionRun(
        run_id=uuid.uuid4(),
        source_id="bokjiro",
        run_type="runtime_import",
        trigger_type="scheduler",
        started_at=datetime.now(timezone.utc) - timedelta(hours=3),
        finished_at=None,
        status="running",
        requested_count=50,
        raw_document_count=50,
        extracted_count=45,
        accepted_count=40,
        inserted_count=30,
        updated_count=10,
        failed_count=0,
    )

    db.add(run1)
    db.add(run2)
    db.commit()
    db.refresh(run1)
    db.refresh(run2)
    return [run1, run2]


def test_list_collection_runs_missing_token_401():
    """Authorization 헤더 없이 GET /api/v1/admin/collection-runs 요청 시 401 Unauthorized 반환."""
    response = client.get("/api/v1/admin/collection-runs")
    assert response.status_code == 401


def test_list_collection_runs_non_admin_403(monkeypatch):
    """서명은 정상이지만 role != 'admin'인 유저가 접근 시 403 Forbidden 반환."""
    assert client.post("/api/v1/admin/session", json={"pin": "0000"}).status_code == 200
    expires_at = int(datetime.now(timezone.utc).timestamp()) + 3600
    monkeypatch.setattr(
        "app.api.deps.verify_admin_session_token",
        lambda token, **kwargs: {
            "sub": "user123",
            "role": "user",
            "expires_at": expires_at,
        },
    )

    response = client.get(
        "/api/v1/admin/collection-runs",
        headers={"Authorization": "Bearer fake_user_token"},
    )
    assert response.status_code == 403


def test_list_collection_runs_success(admin_token, sample_collection_runs):
    """정상 관리자 토큰으로 GET /api/v1/admin/collection-runs 조회 성공 및 페이징 검증."""
    response = client.get(
        "/api/v1/admin/collection-runs?page=1&size=20",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["size"] == 20
    assert len(data["items"]) == 2


def test_list_collection_runs_with_filters(admin_token, sample_collection_runs):
    """source_id 및 status 필터링 동작 검증."""
    # source_id = youthcenter 필터
    resp = client.get(
        "/api/v1/admin/collection-runs?source_id=youthcenter",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["source_id"] == "youthcenter"

    # status = running 필터
    resp_running = client.get(
        "/api/v1/admin/collection-runs?status=running",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_running.status_code == 200
    items_running = resp_running.json()["items"]
    assert len(items_running) == 1
    assert items_running[0]["status"] == "running"
    assert items_running[0]["is_stale"] is True  # 3시간 전 시작된 running이므로 is_stale == True


def test_get_collection_run_detail_success(admin_token, sample_collection_runs):
    """GET /api/v1/admin/collection-runs/{run_id} 단건 상세 조회 200 OK 성공."""
    target_run = sample_collection_runs[0]
    response = client.get(
        f"/api/v1/admin/collection-runs/{target_run.run_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == str(target_run.run_id)
    assert data["source_id"] == "youthcenter"
    assert data["inserted_count"] == 80
    assert data["updated_count"] == 15
    assert data["is_stale"] is False


def test_get_collection_run_detail_not_found_404(admin_token):
    """존재하지 않는 run_id 조회의 경우 404 Not Found 반환."""
    random_uuid = uuid.uuid4()
    response = client.get(
        f"/api/v1/admin/collection-runs/{random_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == f"Collection run '{random_uuid}' not found."


def test_collection_run_admin_route_protection_dependencies():
    """CollectionRun 관리자 라우트에 get_current_admin_payload dependency가 포함되었는지 회귀 검사."""
    for route in collection_run_admin_router.routes:
        dep_functions = [dep.call for dep in route.dependant.dependencies]
        assert get_current_admin_payload in dep_functions


def test_trigger_collection_run_success_202(
    admin_token,
    db,
    collection_queue_publisher,
):
    """POST /api/v1/admin/collection-runs 수동 수집 기동 요청 성공시 202 Accepted 반환 및 DB 레코드 생성."""
    response = client.post(
        "/api/v1/admin/collection-runs",
        json={"source_id": "cheonan-youthcenter-web", "requested_count": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["source_id"] == "cheonan-youthcenter-web"
    assert data["status"] == "queued"
    assert data["run_type"] == "collection"
    assert data["trigger_type"] == "admin"
    assert "run_id" in data

    # DB에 생성되었는지 검증
    run_in_db = db.query(CollectionRun).filter(CollectionRun.run_id == uuid.UUID(data["run_id"])).first()
    assert run_in_db is not None
    assert run_in_db.status == "queued"
    assert run_in_db.requested_count == 1
    collection_queue_publisher.assert_called_once_with(
        uuid.UUID(data["run_id"]),
        "cheonan-youthcenter-web",
        1,
    )


def test_trigger_collection_run_active_conflict_409(
    admin_token,
    db,
    collection_queue_publisher,
):
    """동일 source_id에 2시간 미만의 진행 중인 running 수집이 존재할 경우 409 Conflict 반환."""
    # 30분 전에 시작된 running 수집 생성
    active_run = CollectionRun(
        run_id=uuid.uuid4(),
        source_id="cheonan-youthcenter-web",
        run_type="collection",
        trigger_type="admin",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        finished_at=None,
        status="running",
    )
    db.add(active_run)
    db.commit()

    # 동일 source_id에 대해 수동 수집 요청
    response = client.post(
        "/api/v1/admin/collection-runs",
        json={"source_id": "cheonan-youthcenter-web"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert "currently in progress" in data["error"]["message"]
    assert data["error"]["details"]["active_run_id"] == str(active_run.run_id)
    collection_queue_publisher.assert_not_called()


def test_trigger_collection_run_stale_active_allows_new_trigger(
    admin_token,
    db,
    collection_queue_publisher,
):
    """3시간 전 시작되어 Stale 상태인 running 수집이 존재할 경우 409 없이 202 성공 처리."""
    stale_run = CollectionRun(
        run_id=uuid.uuid4(),
        source_id="cheonan-youthcenter-web",
        run_type="collection",
        trigger_type="admin",
        started_at=datetime.now(timezone.utc) - timedelta(hours=3),
        finished_at=None,
        status="running",
    )
    db.add(stale_run)
    db.commit()

    # 동일 source_id에 대해 수동 수집 요청
    response = client.post(
        "/api/v1/admin/collection-runs",
        json={"source_id": "cheonan-youthcenter-web", "requested_count": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 202
    assert response.json()["source_id"] == "cheonan-youthcenter-web"
    collection_queue_publisher.assert_called_once()
    db.refresh(stale_run)
    assert stale_run.status == "failed"
    assert stale_run.error_type == "StaleCollectionRunReplaced"


def test_trigger_collection_run_queued_conflict_409(
    admin_token,
    db,
    collection_queue_publisher,
):
    active_run = CollectionRun(
        source_id="cheonan-youthcenter-web",
        run_type="collection",
        trigger_type="admin",
        status="queued",
    )
    db.add(active_run)
    db.commit()

    response = client.post(
        "/api/v1/admin/collection-runs",
        json={"source_id": "cheonan-youthcenter-web"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["details"]["active_run_id"] == str(
        active_run.run_id
    )
    collection_queue_publisher.assert_not_called()


def test_trigger_collection_run_broker_failure_closes_run_503(
    admin_token,
    db,
    collection_queue_publisher,
):
    collection_queue_publisher.side_effect = CollectionQueuePublishError(
        "ConnectionError"
    )

    response = client.post(
        "/api/v1/admin/collection-runs",
        json={"source_id": "cheonan-youthcenter-web", "requested_count": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 503
    run = db.query(CollectionRun).one()
    assert run.status == "failed"
    assert run.finished_at is not None
    assert run.failed_count == 1
    assert run.error_type == "CollectionQueuePublishError"


def test_trigger_collection_run_invalid_payload_422(admin_token):
    """requested_count가 범위 밖(0 또는 501 이상)일 때 422 Unprocessable Entity 반환."""
    resp_zero = client.post(
        "/api/v1/admin/collection-runs",
        json={"requested_count": 0},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_zero.status_code == 422

    resp_too_large = client.post(
        "/api/v1/admin/collection-runs",
        json={"requested_count": 501},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_too_large.status_code == 422

    resp_unknown_source = client.post(
        "/api/v1/admin/collection-runs",
        json={"source_id": "unknown-source"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_unknown_source.status_code == 422
