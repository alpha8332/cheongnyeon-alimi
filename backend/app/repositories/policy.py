from dataclasses import dataclass
from typing import Any

from sqlalchemy import ColumnElement, cast, exists, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.models.policy import Policy
from app.repositories.policy_lifecycle import public_policy_predicates
from app.repositories.public_dataset import (
    active_public_dataset_membership_predicate,
)


@dataclass(frozen=True)
class PolicyPage:
    total: int
    items: tuple[Policy, ...]


def _policy_order_by(sort: str) -> tuple[Any, ...]:
    """Return deterministic public policy ordering for an allowlisted sort."""
    if sort == "title_asc":
        return (func.lower(Policy.title).asc(), Policy.id.asc())
    if sort == "title_desc":
        return (func.lower(Policy.title).desc(), Policy.id.asc())
    if sort == "deadline_asc":
        return (Policy.application_end.asc().nulls_last(), Policy.id.asc())
    if sort == "deadline_desc":
        return (Policy.application_end.desc().nulls_last(), Policy.id.asc())
    if sort == "collected_desc":
        return (Policy.collected_at.desc(), Policy.id.asc())
    if sort == "collected_asc":
        return (Policy.collected_at.asc(), Policy.id.asc())
    return (Policy.id.asc(),)


def _json_array_contains(
    column: Any,
    value: str,
    *,
    dialect_name: str,
) -> ColumnElement[bool]:
    if dialect_name == "postgresql":
        return column.op("@>")(cast([value], JSONB))

    array_items = func.json_each(column).table_valued("value").alias()
    return exists(
        select(1)
        .select_from(array_items)
        .where(array_items.c.value == value)
    )


class PolicyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.dialect_name = db.get_bind().dialect.name

    def list(
        self,
        *,
        quality_statuses: tuple[str, ...],
        page: int,
        limit: int,
        category: str | None = None,
        region: str | None = None,
        application_status: str | None = None,
        sort: str = "default",
    ) -> PolicyPage:
        predicates: list[ColumnElement[bool]] = [
            Policy.data_quality_status.in_(quality_statuses),
            *public_policy_predicates(),
            active_public_dataset_membership_predicate(Policy.id),
        ]
        if category is not None:
            predicates.append(
                _json_array_contains(
                    Policy.categories,
                    category,
                    dialect_name=self.dialect_name,
                )
            )
        if region is not None:
            predicates.append(
                _json_array_contains(
                    Policy.regions,
                    region,
                    dialect_name=self.dialect_name,
                )
            )
        if application_status is not None:
            predicates.append(
                Policy.application_status == application_status
            )

        total = self.db.scalar(
            select(func.count(Policy.id)).where(*predicates)
        )
        items = self.db.scalars(
            select(Policy)
            .where(*predicates)
            .order_by(*_policy_order_by(sort))
            .offset((page - 1) * limit)
            .limit(limit)
        ).all()
        return PolicyPage(
            total=int(total or 0),
            items=tuple(items),
        )

    def get_by_id(
        self,
        policy_id: int,
        *,
        quality_statuses: tuple[str, ...],
    ) -> Policy | None:
        return self.db.scalar(
            select(Policy).where(
                Policy.id == policy_id,
                Policy.data_quality_status.in_(quality_statuses),
                *public_policy_predicates(),
                active_public_dataset_membership_predicate(Policy.id),
            )
        )
