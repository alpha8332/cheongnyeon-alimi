from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.administrative_region import (
    AdministrativeRegion,
    AdministrativeRegionAlias,
)
from app.models.policy_search import PolicyRegionRule, PolicySearchDocument


REGION_RULE_FIELDS = (
    "relation",
    "resolution_status",
    "region_scheme",
    "region_code",
    "source_code",
    "source_text",
)
SEARCH_DOCUMENT_FIELDS = (
    "title_text",
    "keyword_text",
    "summary_text",
    "eligibility_text",
    "support_text",
    "search_text",
    "projection_version",
)


def _rule_key(value: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(value.get(field) or "") for field in REGION_RULE_FIELDS)


def _normalized_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class PolicySearchRepository:
    """Store policy search relations without owning the transaction."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def region_rule_keys(self, policy_id: int) -> tuple[tuple[str, ...], ...]:
        rules = self.db.scalars(
            select(PolicyRegionRule).where(
                PolicyRegionRule.policy_id == policy_id
            )
        ).all()
        return tuple(
            sorted(
                _rule_key(
                    {
                        field: getattr(rule, field)
                        for field in REGION_RULE_FIELDS
                    }
                )
                for rule in rules
            )
        )

    def policy_region_rules(
        self,
        policy_id: int,
    ) -> tuple[PolicyRegionRule, ...]:
        return tuple(
            self.db.scalars(
                select(PolicyRegionRule)
                .where(PolicyRegionRule.policy_id == policy_id)
                .order_by(PolicyRegionRule.id)
            ).all()
        )

    def alias_candidates(
        self,
        *,
        scheme: str,
        alias: str,
        active_only: bool = True,
    ) -> tuple[AdministrativeRegion, ...]:
        statement = (
            select(AdministrativeRegion)
            .join(
                AdministrativeRegionAlias,
                (
                    AdministrativeRegionAlias.scheme
                    == AdministrativeRegion.scheme
                )
                & (
                    AdministrativeRegionAlias.region_code
                    == AdministrativeRegion.code
                ),
            )
            .where(
                AdministrativeRegionAlias.scheme == scheme,
                AdministrativeRegionAlias.alias == alias,
            )
            .order_by(AdministrativeRegion.code)
        )
        if active_only:
            statement = statement.where(
                AdministrativeRegion.status == "active"
            )
        return tuple(self.db.scalars(statement).unique().all())

    def regions_for_schemes(
        self,
        schemes: Sequence[str],
    ) -> tuple[AdministrativeRegion, ...]:
        selected_schemes = tuple(sorted(set(schemes)))
        if not selected_schemes:
            return ()
        return tuple(
            self.db.scalars(
                select(AdministrativeRegion)
                .where(AdministrativeRegion.scheme.in_(selected_schemes))
                .order_by(
                    AdministrativeRegion.scheme,
                    AdministrativeRegion.code,
                )
            ).all()
        )

    def search_document(
        self,
        policy_id: int,
    ) -> PolicySearchDocument | None:
        return self.db.get(PolicySearchDocument, policy_id)

    def replace_region_rules(
        self,
        policy_id: int,
        rules: Sequence[Mapping[str, Any]],
    ) -> bool:
        incoming_keys = tuple(sorted(_rule_key(rule) for rule in rules))
        if self.region_rule_keys(policy_id) == incoming_keys:
            return False

        self.db.execute(
            delete(PolicyRegionRule).where(
                PolicyRegionRule.policy_id == policy_id
            )
        )
        self.db.add_all(
            PolicyRegionRule(
                policy_id=policy_id,
                **{
                    field: rule.get(field)
                    for field in REGION_RULE_FIELDS
                },
            )
            for rule in rules
        )
        return True

    def synchronize_document(
        self,
        policy_id: int,
        values: Mapping[str, str],
        *,
        updated_at: datetime,
    ) -> bool:
        document = self.db.get(PolicySearchDocument, policy_id)
        if document is None:
            self.db.add(
                PolicySearchDocument(
                    policy_id=policy_id,
                    **{
                        field: values[field]
                        for field in SEARCH_DOCUMENT_FIELDS
                    },
                    updated_at=updated_at,
                )
            )
            return True

        if all(
            getattr(document, field) == values[field]
            for field in SEARCH_DOCUMENT_FIELDS
        ):
            return False

        for field in SEARCH_DOCUMENT_FIELDS:
            setattr(document, field, values[field])
        if _normalized_datetime(updated_at) > _normalized_datetime(
            document.updated_at
        ):
            document.updated_at = updated_at
        return True
