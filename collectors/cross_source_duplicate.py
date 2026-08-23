"""Conservative cross-source duplicate decisions for regional policies."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unicodedata
import urllib.parse
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from collectors.extracted import SourceProvenance
from collectors.normalized import NormalizedProgram
from collectors.registry import SOURCE_ID_PATTERN


AGGREGATOR_SOURCE_IDS = frozenset(
    {"youthcenter-api", "bokjiro-central-welfare-api"}
)
_DOCUMENT_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


class CrossSourceDuplicateError(ValueError):
    """Cross-source evidence or baseline data is not safe to compare."""


class DuplicateOutcome(str, Enum):
    ACCEPTED_REGIONAL = "accepted_regional"
    EXCLUDED_AGGREGATOR_DUPLICATE = "excluded_aggregator_duplicate"
    DUPLICATE_REVIEW_REQUIRED = "duplicate_review_required"


@dataclass(frozen=True, slots=True)
class PolicyIdentity:
    source_id: str
    external_id: str

    def __post_init__(self) -> None:
        if not SOURCE_ID_PATTERN.fullmatch(self.source_id):
            raise CrossSourceDuplicateError("invalid policy source identity")
        if not self.external_id or any(
            character.isspace() for character in self.external_id
        ):
            raise CrossSourceDuplicateError("invalid external policy identity")

    def to_dict(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "external_id": self.external_id,
        }


@dataclass(frozen=True, slots=True)
class AnnouncementIdentity:
    issuer: str
    announcement_id: str

    def __post_init__(self) -> None:
        if not _comparison_text(self.issuer) or not _comparison_text(
            self.announcement_id
        ):
            raise CrossSourceDuplicateError(
                "announcement identity requires issuer and ID"
            )

    @property
    def key(self) -> tuple[str, str]:
        return (
            _comparison_text(self.issuer),
            _comparison_text(self.announcement_id),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "issuer": self.issuer,
            "announcement_id": self.announcement_id,
        }


@dataclass(frozen=True, slots=True)
class DuplicateEvidence:
    aggregator_references: tuple[PolicyIdentity, ...] = ()
    canonical_urls: tuple[str, ...] = ()
    announcement_identities: tuple[AnnouncementIdentity, ...] = ()
    field_locators: tuple[tuple[str, str], ...] = ()
    provenance: tuple[SourceProvenance, ...] = ()

    def __post_init__(self) -> None:
        locators = dict(self.field_locators)
        if len(locators) != len(self.field_locators):
            raise CrossSourceDuplicateError(
                "duplicate evidence locators must be unique"
            )
        populated = {
            "aggregator_references": bool(self.aggregator_references),
            "canonical_urls": bool(self.canonical_urls),
            "announcement_identities": bool(self.announcement_identities),
        }
        if any(name not in locators for name, present in populated.items() if present):
            raise CrossSourceDuplicateError(
                "every duplicate identity evidence requires a locator"
            )
        if not self.provenance:
            raise CrossSourceDuplicateError(
                "duplicate evidence requires Raw provenance"
            )
        normalized_urls = tuple(_canonical_url(value) for value in self.canonical_urls)
        if any(value is None for value in normalized_urls):
            raise CrossSourceDuplicateError(
                "duplicate evidence contains an invalid canonical URL"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "aggregator_references": [
                value.to_dict() for value in self.aggregator_references
            ],
            "canonical_urls": list(self.canonical_urls),
            "announcement_identities": [
                value.to_dict() for value in self.announcement_identities
            ],
            "field_locators": dict(self.field_locators),
            "provenance": [value.to_dict() for value in self.provenance],
        }


@dataclass(frozen=True, slots=True)
class BaselineRecord:
    identity: PolicyIdentity
    title: str
    organization: str | None
    canonical_region_keys: tuple[str, ...]
    application_start: date | None
    application_end: date | None
    support_content: str | None
    canonical_urls: tuple[str, ...]
    announcement_identities: tuple[AnnouncementIdentity, ...] = ()
    database_row_id: int | None = None

    def __post_init__(self) -> None:
        if self.identity.source_id not in AGGREGATOR_SOURCE_IDS:
            raise CrossSourceDuplicateError(
                "baseline record must belong to an approved aggregator"
            )
        if not _comparison_text(self.title):
            raise CrossSourceDuplicateError("baseline title is required")
        if self.database_row_id is not None and self.database_row_id <= 0:
            raise CrossSourceDuplicateError("invalid baseline database row ID")
        if len(set(self.canonical_region_keys)) != len(
            self.canonical_region_keys
        ):
            raise CrossSourceDuplicateError(
                "baseline canonical regions must be unique"
            )
        if any(_canonical_url(value) is None for value in self.canonical_urls):
            raise CrossSourceDuplicateError(
                "baseline contains an invalid canonical URL"
            )

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
        *,
        canonical_region_keys: Iterable[str] = (),
        database_row_id: int | None = None,
    ) -> BaselineRecord:
        try:
            source_id = value["source_id"]
            external_id = value["external_id"]
            title = value["title"]
        except KeyError:
            raise CrossSourceDuplicateError(
                "baseline policy mapping is incomplete"
            ) from None
        if not all(isinstance(item, str) for item in (source_id, external_id, title)):
            raise CrossSourceDuplicateError(
                "baseline policy identity fields must be strings"
            )
        source_urls = tuple(
            item
            for item in (
                value.get("source_url"),
                value.get("application_method"),
            )
            if isinstance(item, str) and _canonical_url(item) is not None
        )
        return cls(
            identity=PolicyIdentity(source_id, external_id),
            title=title,
            organization=_optional_text(value.get("organization")),
            canonical_region_keys=tuple(sorted(set(canonical_region_keys))),
            application_start=_optional_date(value.get("application_start")),
            application_end=_optional_date(value.get("application_end")),
            support_content=_optional_text(value.get("support_content")),
            canonical_urls=source_urls,
            database_row_id=database_row_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.identity.to_dict(),
            "database_row_id": self.database_row_id,
            "comparison_fingerprint": self.comparison_fingerprint,
        }

    @property
    def comparison_fingerprint(self) -> str:
        payload = {
            "title": _comparison_text(self.title),
            "organization": _comparison_text(self.organization),
            "canonical_region_keys": self.canonical_region_keys,
            "application_start": (
                self.application_start.isoformat()
                if self.application_start is not None
                else None
            ),
            "application_end": (
                self.application_end.isoformat()
                if self.application_end is not None
                else None
            ),
            "support_content": _comparison_text(self.support_content),
            "canonical_urls": tuple(
                sorted(_canonical_url(value) for value in self.canonical_urls)
            ),
            "announcement_identities": tuple(
                sorted(value.key for value in self.announcement_identities)
            ),
        }
        return "sha256:" + hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class BaselineDescriptor:
    source_id: str
    snapshot_id: str
    snapshot_collected_at: datetime
    snapshot_policy_count: int
    database_checked_at: datetime
    database_policy_count: int

    def __post_init__(self) -> None:
        if self.source_id not in AGGREGATOR_SOURCE_IDS:
            raise CrossSourceDuplicateError(
                "baseline descriptor source is not approved"
            )
        if not _DOCUMENT_ID_PATTERN.fullmatch(self.snapshot_id):
            raise CrossSourceDuplicateError("invalid baseline snapshot ID")
        for value in (self.snapshot_collected_at, self.database_checked_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise CrossSourceDuplicateError(
                    "baseline timestamps require a timezone"
                )
        if self.snapshot_policy_count <= 0 or self.database_policy_count <= 0:
            raise CrossSourceDuplicateError(
                "baseline source must contain snapshot and database policies"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "snapshot_id": self.snapshot_id,
            "snapshot_collected_at": self.snapshot_collected_at.isoformat(),
            "snapshot_policy_count": self.snapshot_policy_count,
            "database_checked_at": self.database_checked_at.isoformat(),
            "database_policy_count": self.database_policy_count,
        }


@dataclass(frozen=True, slots=True)
class AggregatorBaseline:
    descriptors: tuple[BaselineDescriptor, ...]
    records: tuple[BaselineRecord, ...]

    def __post_init__(self) -> None:
        descriptor_sources = tuple(value.source_id for value in self.descriptors)
        if set(descriptor_sources) != AGGREGATOR_SOURCE_IDS or len(
            descriptor_sources
        ) != len(AGGREGATOR_SOURCE_IDS):
            raise CrossSourceDuplicateError(
                "baseline requires one descriptor for each approved aggregator"
            )
        identities = tuple(value.identity for value in self.records)
        if len(set(identities)) != len(identities):
            raise CrossSourceDuplicateError(
                "baseline policy identities must be unique"
            )
        record_counts = {
            source_id: sum(
                value.identity.source_id == source_id for value in self.records
            )
            for source_id in AGGREGATOR_SOURCE_IDS
        }
        if any(
            descriptor.database_policy_count != record_counts[descriptor.source_id]
            for descriptor in self.descriptors
        ):
            raise CrossSourceDuplicateError(
                "baseline descriptor counts do not match records"
            )

    @property
    def baseline_id(self) -> str:
        payload = {
            "descriptors": [
                value.to_dict()
                for value in sorted(self.descriptors, key=lambda item: item.source_id)
            ],
            "records": [
                value.to_dict()
                for value in sorted(
                    self.records,
                    key=lambda item: (
                        item.identity.source_id,
                        item.identity.external_id,
                    ),
                )
            ],
        }
        return hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:32]

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "descriptors": [
                value.to_dict()
                for value in sorted(self.descriptors, key=lambda item: item.source_id)
            ],
        }


@dataclass(frozen=True, slots=True)
class DuplicateDecision:
    candidate: PolicyIdentity
    candidate_collected_at: datetime
    outcome: DuplicateOutcome
    reason_codes: tuple[str, ...]
    match_fields: tuple[str, ...]
    matched_policies: tuple[PolicyIdentity, ...]
    candidate_fingerprint: str

    @property
    def accepted(self) -> bool:
        return self.outcome is DuplicateOutcome.ACCEPTED_REGIONAL

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict(),
            "candidate_collected_at": self.candidate_collected_at.isoformat(),
            "outcome": self.outcome.value,
            "accepted": self.accepted,
            "reason_codes": list(self.reason_codes),
            "match_fields": list(self.match_fields),
            "matched_policies": [
                value.to_dict() for value in self.matched_policies
            ],
            "candidate_fingerprint": self.candidate_fingerprint,
        }


def evaluate_cross_source_duplicate(
    candidate: NormalizedProgram,
    evidence: DuplicateEvidence,
    baseline: AggregatorBaseline | None,
) -> DuplicateDecision:
    """Decide whether one regionally accepted policy may be imported."""
    if evidence.provenance != candidate.provenance:
        raise CrossSourceDuplicateError(
            "duplicate evidence provenance must match the candidate"
        )
    identity = PolicyIdentity(candidate.source_id, candidate.external_id or "")
    fingerprint = _fingerprint(candidate)
    if baseline is None:
        return _decision(
            identity,
            candidate,
            DuplicateOutcome.DUPLICATE_REVIEW_REQUIRED,
            ("aggregator_baseline_unavailable",),
            (),
            (),
            fingerprint,
        )

    records = baseline.records
    explicit_matches = tuple(
        record
        for record in records
        if record.identity in evidence.aggregator_references
    )
    if explicit_matches:
        return _matched_decision(
            identity,
            candidate,
            explicit_matches,
            "aggregator_external_id_match",
            ("source_id", "external_id"),
            fingerprint,
        )

    candidate_urls = {
        value
        for raw_url in evidence.canonical_urls
        if (value := _canonical_url(raw_url)) is not None
    }
    url_matches = tuple(
        record
        for record in records
        if candidate_urls.intersection(
            value
            for raw_url in record.canonical_urls
            if (value := _canonical_url(raw_url)) is not None
        )
    )
    if len(url_matches) == 1:
        return _matched_decision(
            identity,
            candidate,
            url_matches,
            "canonical_url_match",
            ("canonical_url",),
            fingerprint,
        )
    if url_matches:
        return _decision(
            identity,
            candidate,
            DuplicateOutcome.DUPLICATE_REVIEW_REQUIRED,
            ("canonical_url_matches_multiple_policies",),
            ("canonical_url",),
            url_matches,
            fingerprint,
        )

    candidate_announcements = {
        value.key for value in evidence.announcement_identities
    }
    announcement_matches = tuple(
        record
        for record in records
        if candidate_announcements.intersection(
            value.key for value in record.announcement_identities
        )
    )
    if announcement_matches:
        return _matched_decision(
            identity,
            candidate,
            announcement_matches,
            "official_announcement_id_match",
            ("announcement_issuer", "announcement_id"),
            fingerprint,
        )

    fingerprint_matches = tuple(
        record for record in records if _fingerprint_fields_match(candidate, record)
    )
    if fingerprint_matches:
        return _decision(
            identity,
            candidate,
            DuplicateOutcome.DUPLICATE_REVIEW_REQUIRED,
            ("full_fingerprint_match_requires_review",),
            (
                "title",
                "organization",
                "canonical_region",
                "application_period",
                "support_content",
            ),
            fingerprint_matches,
            fingerprint,
        )

    title_matches = tuple(
        record
        for record in records
        if _comparison_text(record.title) == _comparison_text(candidate.title)
    )
    if title_matches and any(
        _comparison_is_incomplete(candidate, record) for record in title_matches
    ):
        return _decision(
            identity,
            candidate,
            DuplicateOutcome.DUPLICATE_REVIEW_REQUIRED,
            ("same_title_with_incomplete_comparison_evidence",),
            ("title",),
            title_matches,
            fingerprint,
        )
    if title_matches:
        return _decision(
            identity,
            candidate,
            DuplicateOutcome.ACCEPTED_REGIONAL,
            ("same_title_but_material_fields_differ",),
            ("title",),
            title_matches,
            fingerprint,
        )
    contained_title_matches = tuple(
        record
        for record in records
        if _material_title_containment(candidate.title, record.title)
    )
    if contained_title_matches:
        return _decision(
            identity,
            candidate,
            DuplicateOutcome.DUPLICATE_REVIEW_REQUIRED,
            ("material_title_containment_requires_review",),
            ("title",),
            contained_title_matches,
            fingerprint,
        )
    return _decision(
        identity,
        candidate,
        DuplicateOutcome.ACCEPTED_REGIONAL,
        ("no_cross_source_candidate",),
        (),
        (),
        fingerprint,
    )


@dataclass(frozen=True, slots=True)
class CrossSourceDecisionManifest:
    source_id: str
    baseline: AggregatorBaseline
    decisions: tuple[DuplicateDecision, ...]
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not SOURCE_ID_PATTERN.fullmatch(self.source_id):
            raise CrossSourceDuplicateError("invalid decision manifest source")
        if not self.decisions or any(
            decision.candidate.source_id != self.source_id
            for decision in self.decisions
        ):
            raise CrossSourceDuplicateError(
                "decision manifest requires same-source decisions"
            )

    @property
    def manifest_id(self) -> str:
        return hashlib.sha256(
            json.dumps(
                self.to_dict(include_manifest_id=False),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:32]

    def to_dict(self, *, include_manifest_id: bool = True) -> dict[str, Any]:
        outcomes = {
            outcome.value: sum(
                decision.outcome is outcome for decision in self.decisions
            )
            for outcome in DuplicateOutcome
        }
        value = {
            "schema_version": self.schema_version,
            "source_id": self.source_id,
            "baseline": self.baseline.to_dict(),
            "counts": outcomes,
            "decisions": [decision.to_dict() for decision in self.decisions],
        }
        if include_manifest_id:
            value["manifest_id"] = self.manifest_id
        return value


class CrossSourceDecisionManifestStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def save(self, manifest: CrossSourceDecisionManifest) -> Path:
        target = self.root / manifest.source_id / f"{manifest.manifest_id}.json"
        try:
            target.resolve().relative_to(self.root)
        except ValueError:
            raise CrossSourceDuplicateError(
                "decision manifest path escapes its root"
            ) from None
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            _verify_existing_manifest(target, manifest)
            return target
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".decision-", suffix=".tmp", dir=target.parent
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(
                    manifest.to_dict(),
                    stream,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary_path, target)
        except FileExistsError:
            _verify_existing_manifest(target, manifest)
            return target
        except OSError:
            raise CrossSourceDuplicateError(
                "decision manifest could not be stored"
            ) from None
        finally:
            temporary_path.unlink(missing_ok=True)
        return target


def _verify_existing_manifest(
    path: Path, manifest: CrossSourceDecisionManifest
) -> None:
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise CrossSourceDuplicateError(
            "existing decision manifest cannot be verified"
        ) from None
    if existing != manifest.to_dict():
        raise CrossSourceDuplicateError(
            "existing decision manifest content does not match"
        )


def _matched_decision(
    identity: PolicyIdentity,
    candidate: NormalizedProgram,
    records: tuple[BaselineRecord, ...],
    reason: str,
    fields: tuple[str, ...],
    fingerprint: str,
) -> DuplicateDecision:
    return _decision(
        identity,
        candidate,
        DuplicateOutcome.EXCLUDED_AGGREGATOR_DUPLICATE,
        (reason,),
        fields,
        records,
        fingerprint,
    )


def _decision(
    identity: PolicyIdentity,
    candidate: NormalizedProgram,
    outcome: DuplicateOutcome,
    reasons: tuple[str, ...],
    fields: tuple[str, ...],
    records: Iterable[BaselineRecord],
    fingerprint: str,
) -> DuplicateDecision:
    return DuplicateDecision(
        candidate=identity,
        candidate_collected_at=candidate.collected_at,
        outcome=outcome,
        reason_codes=reasons,
        match_fields=fields,
        matched_policies=tuple(
            sorted(
                (record.identity for record in records),
                key=lambda value: (value.source_id, value.external_id),
            )
        ),
        candidate_fingerprint=fingerprint,
    )


def _fingerprint_fields_match(
    candidate: NormalizedProgram, record: BaselineRecord
) -> bool:
    candidate_regions = _program_region_keys(candidate)
    fields = (
        (_comparison_text(candidate.title), _comparison_text(record.title)),
        (
            _comparison_text(candidate.organization),
            _comparison_text(record.organization),
        ),
        (candidate_regions, record.canonical_region_keys),
        (
            (candidate.application_start, candidate.application_end),
            (record.application_start, record.application_end),
        ),
        (
            _comparison_text(candidate.support_content),
            _comparison_text(record.support_content),
        ),
    )
    return all(left and right and left == right for left, right in fields)


def _material_title_containment(left: str, right: str) -> bool:
    left_value = _comparison_text(left)
    right_value = _comparison_text(right)
    if left_value == right_value:
        return False
    shorter, longer = sorted((left_value, right_value), key=len)
    return len(shorter) >= 5 and shorter in longer


def _comparison_is_incomplete(
    candidate: NormalizedProgram, record: BaselineRecord
) -> bool:
    return any(
        not left or not right
        for left, right in (
            (
                _comparison_text(candidate.organization),
                _comparison_text(record.organization),
            ),
            (_program_region_keys(candidate), record.canonical_region_keys),
            (
                (candidate.application_start, candidate.application_end)
                if candidate.application_start and candidate.application_end
                else (),
                (record.application_start, record.application_end)
                if record.application_start and record.application_end
                else (),
            ),
            (
                _comparison_text(candidate.support_content),
                _comparison_text(record.support_content),
            ),
        )
    )


def _fingerprint(candidate: NormalizedProgram) -> str:
    payload = {
        "title": _comparison_text(candidate.title),
        "organization": _comparison_text(candidate.organization),
        "canonical_regions": _program_region_keys(candidate),
        "application_start": (
            candidate.application_start.isoformat()
            if candidate.application_start is not None
            else None
        ),
        "application_end": (
            candidate.application_end.isoformat()
            if candidate.application_end is not None
            else None
        ),
        "support_content": _comparison_text(candidate.support_content),
    }
    return "sha256:" + hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _program_region_keys(program: NormalizedProgram) -> tuple[str, ...]:
    return tuple(
        sorted(
            f"{rule.region_scheme}:{rule.region_code}"
            for rule in program.region_rules
            if rule.relation.value == "include"
            and rule.resolution_status.value == "matched"
            and rule.region_scheme is not None
            and rule.region_code is not None
        )
    )


def _comparison_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return "".join(
        character.casefold()
        for character in unicodedata.normalize("NFKC", value)
        if character.isalnum()
    )


def _canonical_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = urllib.parse.urlsplit(value.strip())
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    query = urllib.parse.urlencode(
        sorted(
            (key, item)
            for key, item in urllib.parse.parse_qsl(
                parsed.query, keep_blank_values=True
            )
            if not key.lower().startswith("utm_")
        ),
        doseq=True,
    )
    path = parsed.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, query, "")
    )


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _optional_date(value: Any) -> date | None:
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    raise CrossSourceDuplicateError("baseline date must be ISO date or null")
