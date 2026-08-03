"""Versioned administrative-region reference models and exact resolvers."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from datetime import date
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any


class RegionReferenceError(ValueError):
    """Raised when a region reference violates its integrity contract."""


class RegionStatus(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"


class RegionLevel(str, Enum):
    COUNTRY = "country"
    PROVINCE = "province"
    DISTRICT = "district"


class RegionResolutionStatus(str, Enum):
    MATCHED = "matched"
    UNMAPPED = "unmapped"
    AMBIGUOUS = "ambiguous"


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGIONS_PATH = ROOT / "data/seeds/administrative_regions.json"
DEFAULT_ALIASES_PATH = (
    ROOT / "data/seeds/administrative_region_aliases.json"
)


def normalize_region_key(value: str) -> str:
    """Normalize Unicode and whitespace without fuzzy or prefix inference."""

    if not isinstance(value, str):
        raise TypeError("region key must be a string")
    return " ".join(unicodedata.normalize("NFKC", value).split())


def _optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise RegionReferenceError("validity date must be an ISO date or null")
    return date.fromisoformat(value)


@dataclass(frozen=True, slots=True)
class AdministrativeRegion:
    scheme: str
    code: str
    name: str
    full_name: str
    level: RegionLevel
    status: RegionStatus
    parent_code: str | None
    aggregate_parent_code: str | None
    valid_from: date | None
    valid_to: date | None
    source_parent_code: str | None
    external_codes: tuple[tuple[str, str], ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AdministrativeRegion":
        external = value.get("external_codes", {})
        if not isinstance(external, dict):
            raise RegionReferenceError("external_codes must be an object")
        return cls(
            scheme=value["scheme"],
            code=value["code"],
            name=value["name"],
            full_name=value["full_name"],
            level=RegionLevel(value["level"]),
            status=RegionStatus(value["status"]),
            parent_code=value.get("parent_code"),
            aggregate_parent_code=value.get("aggregate_parent_code"),
            valid_from=_optional_date(value.get("valid_from")),
            valid_to=_optional_date(value.get("valid_to")),
            source_parent_code=value.get("source_parent_code"),
            external_codes=tuple(sorted(external.items())),
        )

    def external_code(self, scheme: str) -> str | None:
        return dict(self.external_codes).get(scheme)


@dataclass(frozen=True, slots=True)
class AdministrativeRegionAlias:
    scheme: str
    alias: str
    region_code: str
    kind: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AdministrativeRegionAlias":
        return cls(
            scheme=value["scheme"],
            alias=normalize_region_key(value["alias"]),
            region_code=value["region_code"],
            kind=value["kind"],
        )


@dataclass(frozen=True, slots=True)
class RegionResolution:
    status: RegionResolutionStatus
    candidates: tuple[AdministrativeRegion, ...]


class RegionReference:
    """Validated in-memory view of the PSF2 region and alias seeds."""

    def __init__(
        self,
        *,
        scheme: str,
        regions: tuple[AdministrativeRegion, ...],
        aliases: tuple[AdministrativeRegionAlias, ...],
    ) -> None:
        self.scheme = scheme
        self.regions = regions
        self.aliases = aliases
        self._by_code = {region.code: region for region in regions}
        if len(self._by_code) != len(regions):
            raise RegionReferenceError("duplicate region code")
        if any(region.scheme != scheme for region in regions):
            raise RegionReferenceError("mixed region schemes")
        if any(alias.scheme != scheme for alias in aliases):
            raise RegionReferenceError("mixed alias schemes")

        self._validate_regions()
        alias_index: dict[str, set[str]] = {}
        external_index: dict[tuple[str, str], set[str]] = {}
        seen_aliases: set[tuple[str, str, str]] = set()
        for alias in aliases:
            if alias.region_code not in self._by_code:
                raise RegionReferenceError("alias references an unknown region")
            identity = (alias.alias, alias.region_code, alias.kind)
            if identity in seen_aliases:
                raise RegionReferenceError("duplicate region alias")
            seen_aliases.add(identity)
            alias_index.setdefault(alias.alias, set()).add(alias.region_code)
        for region in regions:
            for external_scheme, external_code in region.external_codes:
                external_index.setdefault(
                    (external_scheme, external_code), set()
                ).add(region.code)
        self._alias_index = alias_index
        self._external_index = external_index

    @classmethod
    def from_seed_files(
        cls,
        regions_path: Path,
        aliases_path: Path,
    ) -> "RegionReference":
        regions_doc = json.loads(regions_path.read_text(encoding="utf-8"))
        aliases_doc = json.loads(aliases_path.read_text(encoding="utf-8"))
        if regions_doc["scheme"] != aliases_doc["scheme"]:
            raise RegionReferenceError("region and alias schemes differ")
        return cls(
            scheme=regions_doc["scheme"],
            regions=tuple(
                AdministrativeRegion.from_dict(item)
                for item in regions_doc["regions"]
            ),
            aliases=tuple(
                AdministrativeRegionAlias.from_dict(item)
                for item in aliases_doc["aliases"]
            ),
        )

    def _validate_regions(self) -> None:
        root_codes = {
            region.code for region in self.regions
            if region.level is RegionLevel.COUNTRY
        }
        if root_codes != {"0000000000"}:
            raise RegionReferenceError("exactly one canonical country root required")
        for region in self.regions:
            if region.valid_from and region.valid_to:
                if region.valid_from > region.valid_to:
                    raise RegionReferenceError("invalid region validity interval")
            for parent in (region.parent_code, region.aggregate_parent_code):
                if parent is not None and parent not in self._by_code:
                    raise RegionReferenceError("region references an unknown parent")
                if parent == region.code:
                    raise RegionReferenceError("region cannot parent itself")

        state: dict[str, int] = {}

        def visit(code: str) -> None:
            marker = state.get(code, 0)
            if marker == 1:
                raise RegionReferenceError("region parent cycle")
            if marker == 2:
                return
            state[code] = 1
            region = self._by_code[code]
            for parent in (region.parent_code, region.aggregate_parent_code):
                if parent is not None:
                    visit(parent)
            state[code] = 2

        for code in self._by_code:
            visit(code)

    def get(self, code: str) -> AdministrativeRegion | None:
        return self._by_code.get(code)

    def ancestors(self, code: str) -> tuple[AdministrativeRegion, ...]:
        region = self._by_code.get(code)
        if region is None:
            raise KeyError(code)
        result: list[AdministrativeRegion] = []
        seen = {code}
        parent_code = region.aggregate_parent_code or region.parent_code
        while parent_code is not None:
            if parent_code in seen:
                raise RegionReferenceError("region parent cycle")
            seen.add(parent_code)
            parent = self._by_code[parent_code]
            result.append(parent)
            parent_code = parent.aggregate_parent_code or parent.parent_code
        return tuple(result)

    def resolve_alias(
        self, alias: str, *, active_only: bool = True
    ) -> RegionResolution:
        codes = self._alias_index.get(normalize_region_key(alias), set())
        candidates = self._resolve_codes(codes, active_only=active_only)
        return self._resolution(candidates)

    def resolve_external_code(
        self,
        external_scheme: str,
        external_code: str,
        *,
        active_only: bool = True,
    ) -> RegionResolution:
        codes = self._external_index.get(
            (external_scheme, normalize_region_key(external_code)), set()
        )
        candidates = self._resolve_codes(codes, active_only=active_only)
        return self._resolution(candidates)

    def _resolve_codes(
        self, codes: set[str], *, active_only: bool
    ) -> tuple[AdministrativeRegion, ...]:
        candidates = (
            self._by_code[code]
            for code in sorted(codes)
        )
        if active_only:
            candidates = (
                item for item in candidates
                if item.status is RegionStatus.ACTIVE
            )
        return tuple(candidates)

    @staticmethod
    def _resolution(
        candidates: tuple[AdministrativeRegion, ...],
    ) -> RegionResolution:
        if not candidates:
            status = RegionResolutionStatus.UNMAPPED
        elif len(candidates) == 1:
            status = RegionResolutionStatus.MATCHED
        else:
            status = RegionResolutionStatus.AMBIGUOUS
        return RegionResolution(status=status, candidates=candidates)


@lru_cache(maxsize=1)
def default_region_reference() -> RegionReference:
    """Load and cache the repository's versioned canonical region seeds."""

    return RegionReference.from_seed_files(
        DEFAULT_REGIONS_PATH,
        DEFAULT_ALIASES_PATH,
    )
