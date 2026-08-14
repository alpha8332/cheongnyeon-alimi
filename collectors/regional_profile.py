"""Approved regional Source profile loading and deterministic replay."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from collectors.errors import CollectorConfigurationError
from collectors.regional_sources import RegionalSourceInventoryValidator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY_PATH = (
    ROOT / "data/reference/regional_youth_policy_sources.json"
)
ACTION_KINDS = frozenset(
    {
        "goto",
        "click",
        "fill",
        "select",
        "paginate",
        "observe_list",
        "observe_detail",
    }
)


class RegionalProfileError(CollectorConfigurationError):
    """A regional profile cannot be loaded or replayed safely."""


@dataclass(frozen=True, slots=True)
class RegionalAction:
    kind: str
    target: str
    value: str | None

    def __post_init__(self) -> None:
        if self.kind not in ACTION_KINDS:
            raise RegionalProfileError("regional action kind is invalid")
        if not isinstance(self.target, str) or not self.target.strip():
            raise RegionalProfileError("regional action target is invalid")
        if self.value is not None and (
            not isinstance(self.value, str) or not self.value
        ):
            raise RegionalProfileError("regional action value is invalid")


@dataclass(frozen=True, slots=True)
class RegionalRequestBudget:
    max_list_requests: int
    max_detail_requests: int
    minimum_interval_seconds: float


@dataclass(frozen=True, slots=True)
class RegionalSourceProfile:
    source_id: str
    home_url: str
    collection_mode: str
    approved_list_urls: tuple[str, ...]
    approved_detail_url_patterns: tuple[str, ...]
    request_budget: RegionalRequestBudget
    actions: tuple[RegionalAction, ...]
    sample_external_id: str
    sample_title: str

    def action(self, kind: str) -> RegionalAction:
        selected = tuple(action for action in self.actions if action.kind == kind)
        if len(selected) != 1:
            raise RegionalProfileError(
                f"regional profile requires exactly one {kind} action"
            )
        return selected[0]


@dataclass(frozen=True, slots=True)
class RegionalActionObservation:
    kind: str
    target: str
    value: str | None = None


def load_approved_regional_profile(
    source_id: str,
    *,
    inventory_path: str | Path = DEFAULT_INVENTORY_PATH,
) -> RegionalSourceProfile:
    """Load one approved profile after schema and domain validation."""
    try:
        candidate = json.loads(
            Path(inventory_path).read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise RegionalProfileError(
            "regional Source inventory could not be loaded"
        ) from None

    issues = RegionalSourceInventoryValidator(
        require_decisions=True
    ).issues(candidate)
    if issues:
        raise RegionalProfileError(
            "regional Source inventory failed validation"
        )

    matches = [
        source
        for source in candidate["sources"]
        if source["source_id"] == source_id
    ]
    if len(matches) != 1:
        raise RegionalProfileError(
            "approved regional Source profile was not found"
        )
    source = matches[0]
    if source["status"] != "approved":
        raise RegionalProfileError("regional Source is not approved")
    discovery = source["discovery"]
    budget = source["request_budget"]
    if discovery["status"] != "extraction_ready" or budget is None:
        raise RegionalProfileError(
            "regional Source profile is not extraction ready"
        )
    return RegionalSourceProfile(
        source_id=source_id,
        home_url=source["home_url"],
        collection_mode=discovery["collection_mode"],
        approved_list_urls=tuple(source["approved_list_urls"]),
        approved_detail_url_patterns=tuple(
            source["approved_detail_url_patterns"]
        ),
        request_budget=RegionalRequestBudget(
            max_list_requests=budget["max_list_requests"],
            max_detail_requests=budget["max_detail_requests"],
            minimum_interval_seconds=budget["minimum_interval_seconds"],
        ),
        actions=tuple(
            RegionalAction(
                kind=action["kind"],
                target=action["target"],
                value=action["value"],
            )
            for action in discovery["actions"]
        ),
        sample_external_id=discovery["sample_external_id"],
        sample_title=discovery["sample_title"],
    )


def replay_profile_actions(
    profile: RegionalSourceProfile,
    observations: Iterable[RegionalActionObservation | Mapping[str, Any]],
) -> tuple[RegionalActionObservation, ...]:
    """Reject drift instead of treating an incomplete replay as zero items."""
    selected = tuple(_observation(value) for value in observations)
    expected = tuple(
        RegionalActionObservation(
            kind=action.kind,
            target=action.target,
            value=action.value,
        )
        for action in profile.actions
    )
    if selected != expected:
        raise RegionalProfileError("regional action profile replay drifted")
    if not any(value.kind == "observe_detail" for value in selected):
        raise RegionalProfileError(
            "regional action profile replay did not reach a detail"
        )
    return selected


def _observation(
    value: RegionalActionObservation | Mapping[str, Any],
) -> RegionalActionObservation:
    if isinstance(value, RegionalActionObservation):
        return value
    try:
        return RegionalActionObservation(
            kind=value["kind"],
            target=value["target"],
            value=value.get("value"),
        )
    except (KeyError, TypeError):
        raise RegionalProfileError(
            "regional action observation is invalid"
        ) from None
