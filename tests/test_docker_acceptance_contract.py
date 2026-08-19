from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))


def test_service_database_is_internal_and_not_published():
    database = COMPOSE["services"]["database"]

    assert "ports" not in database
    assert database["networks"] == ["database"]
    assert COMPOSE["networks"]["database"]["internal"] is True


def test_health_dependency_chain_is_fail_closed():
    services = COMPOSE["services"]

    assert services["restore"]["depends_on"]["database"]["condition"] == (
        "service_healthy"
    )
    assert services["migrate"]["depends_on"]["database"]["condition"] == (
        "service_healthy"
    )
    assert services["backend"]["depends_on"]["migrate"]["condition"] == (
        "service_completed_successfully"
    )
    assert services["frontend"]["depends_on"]["backend"]["condition"] == (
        "service_healthy"
    )


def test_profiles_and_test_volume_are_isolated():
    services = COMPOSE["services"]

    assert services["restore"]["profiles"] == ["restore"]
    assert services["database-test"]["profiles"] == ["test"]
    assert services["database-test"]["volumes"] != services["database"]["volumes"]
    assert services["database-test"]["networks"] == ["database-test"]
    assert COMPOSE["networks"]["database-test"]["internal"] is True


def test_images_are_pinned_and_application_users_are_non_root():
    backend_dockerfile = (ROOT / "backend" / "Dockerfile").read_text(
        encoding="utf-8"
    )
    frontend_dockerfile = (ROOT / "frontend" / "Dockerfile").read_text(
        encoding="utf-8"
    )
    compose_text = (ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert "python:3.14.5-slim-bookworm@sha256:" in backend_dockerfile
    assert "USER 10001:10001" in backend_dockerfile
    assert "node:22.22.0-bookworm-slim@sha256:" in frontend_dockerfile
    assert "USER node" in frontend_dockerfile
    assert "postgres:18.4-bookworm@sha256:" in compose_text


def test_docker_context_rules_exclude_local_artifacts():
    for relative_path in (
        ".dockerignore",
        "backend/Dockerfile.dockerignore",
        "frontend/Dockerfile.dockerignore",
    ):
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "*.dump" in content
        assert "*.log" in content
        assert ".env" in content

