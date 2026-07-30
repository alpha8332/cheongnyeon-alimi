from pathlib import Path
from unittest.mock import Mock

from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.models.policy import Policy
from app.repositories.policy import (
    PolicyPage,
    PolicyRepository,
    _json_array_contains,
)
from app.services.seed_importer import import_seed_data
from app.services.policy import PolicyListRequest, PolicyService


SEED_FILE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "seeds"
    / "initial_programs.json"
)


def test_service_applies_consistent_public_quality_policy():
    repository = Mock()
    repository.list.return_value = PolicyPage(total=0, items=())
    repository.get_by_id.return_value = None
    service = PolicyService(repository)

    service.list(
        PolicyListRequest(
            page=1,
            limit=10,
            include_partial=False,
        )
    )
    service.get(1, include_partial=True)

    assert repository.list.call_args.kwargs["quality_statuses"] == (
        "valid",
    )
    assert repository.get_by_id.call_args.kwargs[
        "quality_statuses"
    ] == ("valid", "partial")


def test_repository_uses_exact_array_membership(db):
    import_seed_data(db, SEED_FILE_PATH)
    repository = PolicyRepository(db)

    finance = repository.list(
        quality_statuses=("valid", "partial"),
        page=1,
        limit=10,
        category="finance",
    )
    category_prefix = repository.list(
        quality_statuses=("valid", "partial"),
        page=1,
        limit=10,
        category="fin",
    )
    seoul = repository.list(
        quality_statuses=("valid",),
        page=1,
        limit=10,
        region="서울특별시",
    )
    region_prefix = repository.list(
        quality_statuses=("valid",),
        page=1,
        limit=10,
        region="서울",
    )

    assert finance.total == 2
    assert category_prefix.total == 0
    assert seoul.total == 1
    assert region_prefix.total == 0


def test_postgresql_array_membership_compiles_to_jsonb_contains():
    predicate = _json_array_contains(
        Policy.categories,
        "finance",
        dialect_name="postgresql",
    )
    statement = select(Policy.id).where(predicate)
    sql = str(statement.compile(dialect=postgresql.dialect()))

    assert "policies.categories @>" in sql
    assert " LIKE " not in sql


def test_list_api_filters_and_paginates(client, db):
    import_seed_data(db, SEED_FILE_PATH)

    first_page = client.get(
        "/api/v1/policies",
        params={"include_partial": "true", "page": 1, "limit": 1},
    )
    second_page = client.get(
        "/api/v1/policies",
        params={"include_partial": "true", "page": 2, "limit": 1},
    )
    category = client.get(
        "/api/v1/policies",
        params={"include_partial": "true", "category": "finance"},
    )
    region = client.get(
        "/api/v1/policies",
        params={"region": "서울특별시"},
    )
    region_prefix = client.get(
        "/api/v1/policies",
        params={"region": "서울"},
    )
    open_status = client.get(
        "/api/v1/policies",
        params={"status": "open"},
    )

    assert first_page.status_code == 200
    assert first_page.json()["total"] == 4
    assert len(first_page.json()["items"]) == 1
    assert second_page.json()["total"] == 4
    assert (
        first_page.json()["items"][0]["id"]
        != second_page.json()["items"][0]["id"]
    )
    assert category.json()["total"] == 2
    assert region.json()["total"] == 1
    assert region_prefix.json()["total"] == 0
    assert open_status.json()["total"] == 1
    assert all(
        "provenance" not in item
        for item in category.json()["items"]
    )


def test_partial_detail_requires_opt_in_and_invalid_is_never_public(
    client,
    db,
):
    import_seed_data(db, SEED_FILE_PATH)
    partial = db.scalar(
        select(Policy).where(
            Policy.data_quality_status == "partial"
        )
    )
    assert partial is not None

    default_detail = client.get(f"/api/v1/policies/{partial.id}")
    opted_in_detail = client.get(
        f"/api/v1/policies/{partial.id}",
        params={"include_partial": "true"},
    )

    assert default_detail.status_code == 404
    assert opted_in_detail.status_code == 200
    assert opted_in_detail.json()["data_quality_status"] == "partial"
    assert "provenance" not in opted_in_detail.json()

    partial.data_quality_status = "invalid"
    db.commit()
    hidden_invalid = client.get(
        f"/api/v1/policies/{partial.id}",
        params={"include_partial": "true"},
    )
    assert hidden_invalid.status_code == 404


def test_policy_api_404_and_query_validation(client, db):
    import_seed_data(db, SEED_FILE_PATH)

    missing = client.get("/api/v1/policies/999999")
    invalid_page = client.get("/api/v1/policies", params={"page": 0})
    invalid_limit = client.get(
        "/api/v1/policies",
        params={"limit": 101},
    )
    invalid_category = client.get(
        "/api/v1/policies",
        params={"category": "fin"},
    )
    invalid_status = client.get(
        "/api/v1/policies",
        params={"status": "unknown"},
    )

    assert missing.status_code == 404
    assert missing.json() == {"detail": "Policy not found"}
    assert invalid_page.status_code == 422
    assert invalid_limit.status_code == 422
    assert invalid_category.status_code == 422
    assert invalid_status.status_code == 422
