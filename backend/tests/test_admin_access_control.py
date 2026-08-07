import hashlib
import time
import hmac
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.services.admin_access import (
    clear_rate_limit_state,
    create_admin_session_token,
    verify_admin_session_token,
    get_admin_token_secret,
    calculate_cooldown_seconds,
)
from app.api.deps import get_current_admin_payload
from app.api.v1.endpoints.admin_access import router as admin_router

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    clear_rate_limit_state()
    original_env = settings.ENVIRONMENT
    original_hash = settings.ADMIN_PIN_HASH
    original_secret = settings.ADMIN_TOKEN_SECRET
    yield
    clear_rate_limit_state()
    settings.ENVIRONMENT = original_env
    settings.ADMIN_PIN_HASH = original_hash
    settings.ADMIN_TOKEN_SECRET = original_secret


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

    # 발급된 토큰이 검증을 통과하는지 확인
    payload = verify_admin_session_token(data["access_token"])
    assert payload is not None
    assert payload["role"] == "admin"


def test_admin_session_invalid_pin_401():
    """잘못된 PIN(예: 9999) 입력 시 401 Unauthorized 반환 및 사유 최소화."""
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


def test_progressive_lockout_calculation():
    """실패 횟수에 따른 점진적 쿨다운 시간(5, 10, 30, 60, 120, 300초) 계산 함수 검증."""
    assert calculate_cooldown_seconds(4) == 0
    assert calculate_cooldown_seconds(5) == 5
    assert calculate_cooldown_seconds(6) == 10
    assert calculate_cooldown_seconds(7) == 30
    assert calculate_cooldown_seconds(8) == 60
    assert calculate_cooldown_seconds(9) == 120
    assert calculate_cooldown_seconds(10) == 300
    assert calculate_cooldown_seconds(15) == 300


def test_admin_session_progressive_rate_limit_429():
    """5회차 실패 시 점진적 락아웃(첫 락아웃 5초) 적용 및 429 반환 검증."""
    settings.ENVIRONMENT = "development"
    settings.ADMIN_PIN_HASH = None

    for i in range(4):
        resp = client.post("/api/v1/admin/session", json={"pin": "9999"})
        assert resp.status_code == 401

    # 5번째 실패 시 점진적 락아웃(5초) 적용 -> 429
    resp_lockout = client.post("/api/v1/admin/session", json={"pin": "9999"})
    assert resp_lockout.status_code == 429
    cooldown = resp_lockout.json()["error"]["details"]["cooldown_seconds"]
    assert cooldown == 5

    # 락아웃 지속 중에는 올바른 PIN '0000' 요청도 429로 거부
    resp_blocked = client.post("/api/v1/admin/session", json={"pin": "0000"})
    assert resp_blocked.status_code == 429


def test_admin_token_verification_cases():
    """서명 토큰의 검증, 만료 및 변조 탐지 테스트."""
    valid_token = create_admin_session_token(expires_minutes=10)
    payload = verify_admin_session_token(valid_token)
    assert payload is not None
    assert payload["role"] == "admin"

    expired_token = create_admin_session_token(expires_minutes=-5)
    assert verify_admin_session_token(expired_token) is None

    parts = valid_token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.invalid_signature"
    assert verify_admin_session_token(tampered_token) is None

    assert verify_admin_session_token("invalid_token_format") is None


def test_admin_token_custom_secret():
    """ADMIN_TOKEN_SECRET 설정 시 커스텀 시크릿으로 서명 및 검증."""
    settings.ADMIN_TOKEN_SECRET = "custom_secret_key_for_testing_123"
    token = create_admin_session_token(expires_minutes=5)
    payload = verify_admin_session_token(token)
    assert payload is not None

    settings.ADMIN_TOKEN_SECRET = "different_secret_key_456"
    assert verify_admin_session_token(token) is None


def test_credential_non_exposure_in_errors():
    """인증 실패 응답 및 예외 응답에 PIN 원문 및 시크릿이 노출되지 않는지 검사."""
    settings.ENVIRONMENT = "development"
    settings.ADMIN_PIN_HASH = None

    secret_pin = "9876"
    response = client.post("/api/v1/admin/session", json={"pin": secret_pin})
    assert response.status_code == 401
    resp_text = response.text

    assert secret_pin not in resp_text
    assert settings.SECRET_KEY not in resp_text


# --- Slice A2 & A3: 권한 경계 및 OpenAPI 보안 명세 테스트 ---


def test_protected_route_missing_token_401():
    """Authorization 헤더 없이 보호 라우트 GET /api/v1/admin/me 접근 시 401 Unauthorized 반환."""
    response = client.get("/api/v1/admin/me")
    assert response.status_code == 401


def test_protected_route_invalid_token_401():
    """변조되거나 유효하지 않은 Bearer 토큰으로 GET /api/v1/admin/me 접근 시 401 Unauthorized 반환."""
    response = client.get(
        "/api/v1/admin/me",
        headers={"Authorization": "Bearer invalid_admin_token_xyz"},
    )
    assert response.status_code == 401


def test_protected_route_non_admin_role_403(monkeypatch):
    """서명은 유효하지만 역할(role)이 admin이 아닌 사용자 접근 시 403 Forbidden 반환."""
    expires_at = int(time.time()) + 3600
    non_admin_payload = {"sub": "user123", "role": "user", "expires_at": expires_at}

    monkeypatch.setattr(
        "app.api.deps.verify_admin_session_token",
        lambda token: non_admin_payload,
    )

    response = client.get(
        "/api/v1/admin/me",
        headers={"Authorization": "Bearer fake_user_token"},
    )
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Admin authorization required."


def test_protected_route_valid_admin_token_200():
    """정상 세션 생성 후 발급받은 Bearer 토큰으로 GET /api/v1/admin/me 접근 시 200 OK 성공."""
    settings.ENVIRONMENT = "development"
    settings.ADMIN_PIN_HASH = None

    login_resp = client.post("/api/v1/admin/session", json={"pin": "0000"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    me_resp = client.get(
        "/api/v1/admin/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["role"] == "admin"
    assert data["status"] == "authenticated"


def test_protected_route_dependency_leak_detection():
    """관리자 전용 보호 라우트에 get_current_admin_payload dependency가 누락되지 않고 등록되었는지 검사."""
    protected_routes = [route for route in admin_router.routes if route.path == "/me"]
    assert len(protected_routes) == 1

    route = protected_routes[0]
    dep_functions = [dep.call for dep in route.dependant.dependencies]
    assert get_current_admin_payload in dep_functions


def test_openapi_security_scheme_registered():
    """OpenAPI 명세에 HTTPBearer security scheme이 정상 등록되어 있는지 검사."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    assert "components" in schema
    assert "securitySchemes" in schema["components"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]
    assert schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
