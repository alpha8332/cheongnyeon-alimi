import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.policy import Policy, utc_now
from app.repositories.policy_search import PolicySearchRepository


POLICY_SEARCH_PROJECTION_VERSION = "1.0.0"
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class SearchStorageSyncResult:
    region_rules_changed: bool
    document_changed: bool

    @property
    def changed(self) -> bool:
        return self.region_rules_changed or self.document_changed


@dataclass(frozen=True)
class ProjectionRebuildResult:
    total: int
    updated: int
    unchanged: int


def _normalized_fragment(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = _WHITESPACE.sub(
        " ",
        unicodedata.normalize("NFKC", value),
    ).strip()
    return normalized or None


def _joined_text(*values: Any) -> str:
    fragments: list[str] = []
    seen: set[str] = set()

    def append(candidate: Any) -> None:
        if isinstance(candidate, str):
            normalized = _normalized_fragment(candidate)
            if normalized is not None and normalized not in seen:
                seen.add(normalized)
                fragments.append(normalized)
        elif isinstance(candidate, Iterable):
            for item in candidate:
                append(item)

    for value in values:
        append(value)
    return " ".join(fragments)


def build_policy_search_document(
    policy: Mapping[str, Any],
) -> dict[str, str]:
    """Build the versioned, source-neutral Korean search projection."""
    title_text = _joined_text(policy.get("title"))
    keyword_text = _joined_text(
        policy.get("category_text"),
        policy.get("categories", ()),
        policy.get("keywords", ()),
    )
    summary_text = _joined_text(policy.get("summary"))
    eligibility_text = _joined_text(
        policy.get("life_stages", ()),
        policy.get("target_groups", ()),
        policy.get("age_condition_text"),
        policy.get("eligibility_text"),
        policy.get("education_statuses", ()),
        policy.get("employment_statuses", ()),
        policy.get("required_conditions", ()),
        policy.get("preferred_conditions", ()),
        policy.get("excluded_conditions", ()),
    )
    support_text = _joined_text(policy.get("support_content"))
    return {
        "title_text": title_text,
        "keyword_text": keyword_text,
        "summary_text": summary_text,
        "eligibility_text": eligibility_text,
        "support_text": support_text,
        "search_text": _joined_text(
            title_text,
            keyword_text,
            summary_text,
            eligibility_text,
            support_text,
        ),
        "projection_version": POLICY_SEARCH_PROJECTION_VERSION,
    }


def synchronize_policy_search_storage(
    db: Session,
    *,
    policy_id: int,
    policy: Mapping[str, Any],
    updated_at: datetime,
) -> SearchStorageSyncResult:
    repository = PolicySearchRepository(db)
    region_rules = policy.get("region_rules", ())
    if not isinstance(region_rules, Sequence):
        raise TypeError("region_rules must be a sequence")
    rules_changed = repository.replace_region_rules(
        policy_id,
        region_rules,
    )
    document_changed = repository.synchronize_document(
        policy_id,
        build_policy_search_document(policy),
        updated_at=updated_at,
    )
    return SearchStorageSyncResult(
        region_rules_changed=rules_changed,
        document_changed=document_changed,
    )


def rebuild_policy_search_documents(
    db: Session,
    *,
    policy_ids: Sequence[int] | None = None,
    updated_at: datetime | None = None,
) -> ProjectionRebuildResult:
    """Rebuild projections in the caller-owned transaction."""
    statement = select(Policy).order_by(Policy.id)
    if policy_ids is not None:
        statement = statement.where(Policy.id.in_(policy_ids))
    policies = db.scalars(statement).all()
    repository = PolicySearchRepository(db)
    write_instant = updated_at or utc_now()
    updated = 0
    for policy in policies:
        values = {
            column.name: getattr(policy, column.name)
            for column in Policy.__table__.columns
        }
        if repository.synchronize_document(
            policy.id,
            build_policy_search_document(values),
            updated_at=write_instant,
        ):
            updated += 1
    return ProjectionRebuildResult(
        total=len(policies),
        updated=updated,
        unchanged=len(policies) - updated,
    )
