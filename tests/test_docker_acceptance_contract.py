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

    assert services["schema-bootstrap"]["depends_on"]["database"]["condition"] == (
        "service_healthy"
    )
    assert services["restore"]["depends_on"]["database"]["condition"] == (
        "service_healthy"
    )
    assert services["migrate"]["depends_on"]["database"]["condition"] == (
        "service_healthy"
    )
    assert services["verify-restored"]["depends_on"]["database"]["condition"] == (
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

    assert services["schema-bootstrap"]["profiles"] == ["restore"]
    assert services["restore"]["profiles"] == ["restore"]
    assert services["verify-restored"]["profiles"] == ["restore"]
    assert services["public-dataset-bootstrap"]["profiles"] == ["bootstrap"]
    assert services["database-test"]["profiles"] == ["test"]
    assert services["database-test"]["volumes"] != services["database"]["volumes"]
    assert services["database-test"]["networks"] == ["database-test"]
    assert COMPOSE["networks"]["database-test"]["internal"] is True


def test_public_dataset_bootstrap_is_verified_read_only_and_database_only():
    service = COMPOSE["services"]["public-dataset-bootstrap"]
    command = service["command"][-1]

    assert service["depends_on"]["migrate"]["condition"] == (
        "service_completed_successfully"
    )
    assert service["networks"] == ["database"]
    assert service["read_only"] is True
    assert service["volumes"][0]["read_only"] is True
    assert "--verify-manifest /bootstrap/manifest.json" in command
    assert command.index("--verify-manifest") < command.index(
        "app.cli.import_public_dataset"
    )


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


def test_frontend_acceptance_image_is_forced_to_actual_api_mode():
    frontend_dockerfile = (ROOT / "frontend" / "Dockerfile").read_text(
        encoding="utf-8"
    )
    frontend_build_args = COMPOSE["services"]["frontend"]["build"]["args"]

    assert frontend_build_args["VITE_USE_MOCK"] == "${VITE_USE_MOCK:-false}"
    assert "ARG VITE_USE_MOCK=false" in frontend_dockerfile
    assert 'test "$VITE_USE_MOCK" = "false"' in frontend_dockerfile


def test_restore_bootstraps_snapshot_schema_before_transactional_data_load():
    restore_runner = (ROOT / "deployment" / "postgres" / "restore.ps1").read_text(
        encoding="utf-8"
    )
    restore_script = (ROOT / "deployment" / "postgres" / "restore.sh").read_text(
        encoding="utf-8"
    )
    schema_guard = (
        ROOT / "deployment" / "postgres" / "prepare_acceptance_schema.py"
    ).read_text(encoding="utf-8")

    assert restore_runner.index("run --rm schema-bootstrap") < restore_runner.index(
        "run --rm restore"
    )
    assert restore_runner.index("run --rm restore") < restore_runner.index(
        "run --rm verify-restored"
    )
    assert restore_runner.index("run --rm verify-restored") < restore_runner.index(
        "run --rm migrate"
    )
    assert COMPOSE["services"]["verify-restored"]["command"] == [
        "python",
        "/opt/acceptance/verify_restored_database.py",
    ]
    assert COMPOSE["services"]["migrate"]["command"][-1] == "alembic upgrade head"
    assert "--data-only" in restore_script
    assert "--disable-triggers" in restore_script
    assert "--single-transaction" in restore_script
    assert "alembic_version" not in restore_script.split("data_tables=", 1)[1].split(
        "\n", 1
    )[0]
    assert "connection.set_session(readonly=True, autocommit=True)" in schema_guard
    assert 'print(f"DEP3_SCHEMA_STATE={state}")' in schema_guard


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


def test_compose_env_initializer_keeps_pin_plaintext_out_of_file():
    initializer = (
        ROOT / "deployment" / "postgres" / "initialize_compose_env.ps1"
    ).read_text(encoding="utf-8")

    assert 'Read-Host "Acceptance admin PIN (4 digits)" -AsSecureString' in initializer
    assert "SHA256" in initializer
    assert '"ADMIN_PIN_HASH=$PinHash"' in initializer
    assert "ADMIN_PIN=$Pin" not in initializer
    assert "refusing overwrite" in initializer
    assert "RandomNumberGenerator" in initializer
    assert "Set-Acl" in initializer
    assert "check-ignore --quiet -- .env.compose" in initializer


def test_windows_one_command_bootstrap_is_fail_closed_and_cache_aware():
    runner = (ROOT / "scripts" / "run_docker.ps1").read_text(encoding="utf-8")
    batch = (ROOT / "run_docker.bat").read_text(encoding="utf-8")

    assert "-ExecutionPolicy Bypass" in batch
    assert "scripts\\run_docker.ps1" in batch
    assert "docker.exe" in runner
    assert '"compose",' in runner
    assert "at least 2 GiB" in runner
    assert "port $($PortCheck.Port) is already used" in runner
    assert "downloaded manifest SHA-256 mismatch" in runner
    assert "downloaded dataset SHA-256 mismatch" in runner
    assert "downloaded dataset byte count mismatch" in runner
    assert "latest.pointer.json" in runner
    assert "public-dataset-bootstrap" in runner
    assert '"run", "--rm", "migrate"' in runner
    assert "Wait-HttpHealth" in runner
    assert "Remove-DownloadDirectory" in runner
    assert '"$OwnershipProjectName`_acceptance-db"' in runner
    assert "[string]::IsNullOrWhiteSpace($ComposeProjectName)" in runner
    assert "docker volume rm" not in runner
    assert "down --volumes" not in runner
