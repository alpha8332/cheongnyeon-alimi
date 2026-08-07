import hashlib
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.admin_access import clear_rate_limit_state

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    clear_rate_limit_state()
    original_env = settings.ENVIRONMENT
    original_hash = settings.ADMIN_PIN_HASH
    yield
    clear_rate_limit_state()
    settings.ENVIRONMENT = original_env
    settings.ADMIN_PIN_HASH = original_hash


def test_admin_session_success_local_default_pin():
    """개발/로컬 환경에서 기본 4자리 PIN '0000'으로 관리자 세션 생성 성공."""
    settings.ENVIRONMENT = "development"
    settings.ADMIN_PIN_HASH = None

    response = client.post("/api/v1/admin/session", json={"pin": "0000"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"
    assert data["expires_in"] == 3600


def test_admin_session_invalid_pin_401():
    """잘못된 PIN(예: 9999) 입력 시 401 Unauthorized 반환."""
    settings.ENVIRONMENT = "development"
    settings.ADMIN_PIN_HASH = None

    response = client.post("/api/v1/admin/session", json={"pin": "9999"})
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["message"] == "Invalid admin PIN or authentication disabled."


@pytest.mark.parametrize("invalid_pin", ["123", "12345", "abcd", "", "000a"])
def test_admin_session_invalid_format_422(invalid_pin):
    """4자리 숫자가 아닌 PIN 입력 시 Pydantic 422 Unprocessable Entity 반환."""
    response = client.post("/api/v1/admin/session", json={"pin": invalid_pin})
    assert response.status_code == 422


def test_admin_session_production_fail_closed():
    """Production 환경에서 ADMIN_PIN_HASH 미설정 시 기본 PIN '0000' 요청도 401 fail-closed 거부."""
    settings.ENVIRONMENT = "production"
    settings.ADMIN_PIN_HASH = None

    response = client.post("/api/v1/admin/session", json={"pin": "0000"})
    assert response.status_code == 401


def test_admin_session_custom_hash_success():
    """명시적 ADMIN_PIN_HASH(예: 1234 해시) 설정 시 해당 PIN으로만 성공."""
    settings.ENVIRONMENT = "production"
    settings.ADMIN_PIN_HASH = hashlib.sha256(b"1234").hexdigest()

    # 0000 요청 -> 실패 401
    resp_fail = client.post("/api/v1/admin/session", json={"pin": "0000"})
    assert resp_fail.status_code == 401

    # 1234 요청 -> 성공 200
    resp_ok = client.post("/api/v1/admin/session", json={"pin": "1234"})
    assert resp_ok.status_code == 200
    assert resp_ok.json()["role"] == "admin"


def test_admin_session_rate_limit_429():
    """5회 연속 로그인 실패 시 429 Too Many Requests 반환 및 lockout 적용."""
    settings.ENVIRONMENT = "development"
    settings.ADMIN_PIN_HASH = None

    for i in range(5):
        resp = client.post("/api/v1/admin/session", json={"pin": "9999"})
        if i < 4:
            assert resp.status_code == 401
        else:
            # 5번째 실패 시 429 락아웃 전환
            assert resp.status_code == 429

    # 6번째 요청도 429로 거부
    resp_blocked = client.post("/api/v1/admin/session", json={"pin": "0000"})
    assert resp_blocked.status_code == 429
    assert resp_blocked.json()["error"]["details"]["cooldown_seconds"] > 0
