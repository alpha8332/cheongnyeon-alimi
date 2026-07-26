from unittest.mock import patch

def test_health_check_connected(client):
    """
    DB 연결 성공 시 Health Check 200 OK 및 connected 응답 검증
    """
    with patch("app.api.v1.endpoints.health.check_db_connection", return_value=True):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
        assert "app" in data

def test_root_health_shortcut(client):
    """
    루트 GET /health 숏컷 엔드포인트 동작 검증
    """
    with patch("app.api.v1.endpoints.health.check_db_connection", return_value=True):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"

def test_health_check_disconnected(client):
    """
    DB 연결 실패 시 Health Check 503 Service Unavailable 응답 검증
    """
    with patch("app.api.v1.endpoints.health.check_db_connection", return_value=False):
        response = client.get("/api/v1/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "error"
        assert data["database"] == "disconnected"
