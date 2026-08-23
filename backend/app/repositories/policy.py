from dataclasses import dataclass
from typing import Any

from sqlalchemy import ColumnElement, cast, exists, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.models.policy import Policy
from app.repositories.policy_lifecycle import public_policy_predicates


@dataclass(frozen=True)
class PolicyPage:
    total: int
    items: tuple[Policy, ...]


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
    ) -> PolicyPage:
        predicates: list[ColumnElement[bool]] = [
            Policy.data_quality_status.in_(quality_statuses),
            *public_policy_predicates(),
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
            .order_by(Policy.id.asc())
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
            )
        )
