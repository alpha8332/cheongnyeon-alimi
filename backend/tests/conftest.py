from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.policy import Policy
from app.models.public_dataset import (
    PublicDatasetInstallation,
    PublicDatasetMembership,
)


test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def activate_all_policies(db):
    """Explicitly publish policies created by a public API unit test."""

    def activate(
        dataset_version: str = "public-bootstrap-20260824-test000",
    ) -> None:
        policies = tuple(db.scalars(select(Policy)).all())
        if not policies:
            raise AssertionError("no policies are available to publish")
        if any(not policy.external_id for policy in policies):
            raise AssertionError("published test policies require external_id")

        db.execute(
            update(PublicDatasetInstallation)
            .where(PublicDatasetInstallation.status == "active")
            .values(status="installed", activated_at=None)
        )
        installation = PublicDatasetInstallation(
            dataset_version=dataset_version,
            manifest_sha256="a" * 64,
            artifact_sha256="b" * 64,
            expected_policy_count=len(policies),
            status="active",
            activated_at=datetime.now(timezone.utc),
        )
        db.add(installation)
        db.flush()
        db.add_all(
            PublicDatasetMembership(
                dataset_version=dataset_version,
                source_id=policy.source_id,
                external_id=policy.external_id,
                policy_id=policy.id,
            )
            for policy in policies
        )
        db.commit()

    return activate
