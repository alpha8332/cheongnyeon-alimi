"""Source-owned mapping into the shared eligibility evidence contract."""

from __future__ import annotations

import re
from typing import Any

from collectors.bokjiro import SOURCE_ID as BOKJIRO_SOURCE_ID
from collectors.cheonan_youthcenter import SOURCE_ID as CHEONAN_SOURCE_ID
from collectors.eligibility import (
    EligibilityCategory,
    EligibilityCoverage,
    EligibilityEvidenceItem,
    EligibilitySummary,
    EvidenceLocatorType,
    EvidenceReference,
    InstitutionalContact,
    InstitutionalContactKind,
    RequiredDocument,
)
from collectors.extracted import ExtractedPolicy
from collectors.regional_expansion import REGIONAL_EXPANSION_SPECS
from collectors.youthcenter import SOURCE_ID as YOUTHCENTER_SOURCE_ID


_DETAIL_SELECTOR = "#bo_v_con"
REGIONAL_ELIGIBILITY_SOURCE_IDS = frozenset(REGIONAL_EXPANSION_SPECS)
ELIGIBILITY_SOURCE_IDS = frozenset(
    {
        YOUTHCENTER_SOURCE_ID,
        BOKJIRO_SOURCE_ID,
        CHEONAN_SOURCE_ID,
        *REGIONAL_ELIGIBILITY_SOURCE_IDS,
    }
)


def map_eligibility(policy: ExtractedPolicy) -> EligibilitySummary:
    """Dispatch one extracted policy to its source-owned mapper."""

    if policy.source_id == YOUTHCENTER_SOURCE_ID:
        return map_youthcenter_eligibility(policy)
    if policy.source_id == BOKJIRO_SOURCE_ID:
        return map_bokjiro_eligibility(policy)
    if policy.source_id == CHEONAN_SOURCE_ID:
        return map_cheonan_eligibility(policy)
    if policy.source_id in REGIONAL_ELIGIBILITY_SOURCE_IDS:
        return map_regional_eligibility(policy)
    raise ValueError("eligibility mapper is not registered for this source")


def map_regional_eligibility(
    policy: ExtractedPolicy,
) -> EligibilitySummary:
    """Map explicit extractor fields shared by the 13 regional sources."""

    if policy.source_id not in REGIONAL_ELIGIBILITY_SOURCE_IDS:
        raise ValueError("regional eligibility mapper received another source")
    requirements = tuple(
        _api_condition(policy, category, text, locator)
        for category, text, locator in (
            (
                EligibilityCategory.AGE,
                _source_text(policy.age_text),
                "extracted.age_text",
            ),
            (
                EligibilityCategory.OTHER,
                _source_text(policy.eligibility_text),
                "extracted.eligibility_text",
            ),
        )
        if text is not None
    )
    exclusion = _source_text(policy.extra.get("exclusion_conditions"))
    exclusions = (
        ()
        if exclusion is None
        else (
            _api_condition(
                policy,
                EligibilityCategory.OTHER,
                exclusion,
                "extra.exclusion_conditions",
            ),
        )
    )
    document = _source_text(policy.extra.get("required_documents"))
    documents = (
        ()
        if document is None
        else (
            RequiredDocument(
                text=document,
                evidence=(
                    _api_evidence(policy, "extra.required_documents"),
                ),
            ),
        )
    )
    contact = _supported_institutional_contact(
        _source_text(policy.extra.get("institutional_contact"))
    )
    contacts = (
        ()
        if contact is None
        else (
            InstitutionalContact(
                kind=(
                    InstitutionalContactKind.PHONE
                    if any(character.isdigit() for character in contact)
                    else InstitutionalContactKind.OFFICIAL_CHANNEL
                ),
                label="기관 문의처",
                value=contact,
                evidence=(
                    _api_evidence(policy, "extra.institutional_contact"),
                ),
            ),
        )
    )
    has_content = any((requirements, exclusions, documents, contacts))
    return EligibilitySummary(
        coverage=(
            EligibilityCoverage.PARTIAL
            if has_content
            else EligibilityCoverage.UNKNOWN
        ),
        requirements=requirements,
        exclusions=exclusions,
        preferences=(),
        documents=documents,
        unknowns=(),
        institutional_contacts=contacts,
    )


def map_youthcenter_eligibility(policy: ExtractedPolicy) -> EligibilitySummary:
    """Map only unambiguous OnTongYouth source fields."""

    fields = _api_source_fields(
        policy,
        YOUTHCENTER_SOURCE_ID,
        "list_item",
        allow_missing=True,
    )
    requirements: list[EligibilityEvidenceItem] = []
    unknowns: list[EligibilityEvidenceItem] = []

    age_text = _source_text(policy.age_text)
    age_evidence = tuple(
        _api_evidence(policy, field_name)
        for field_name in (
            "sprtTrgtAgeLmtYn",
            "sprtTrgtMinAge",
            "sprtTrgtMaxAge",
        )
        if _source_text(fields.get(field_name)) is not None
    )
    if age_text is not None and age_evidence:
        requirements.append(
            EligibilityEvidenceItem(
                category=EligibilityCategory.AGE,
                text=age_text,
                evidence=age_evidence,
            )
        )
    additional = _source_text(fields.get("addAplyQlfcCndCn"))
    if additional is not None:
        requirements.append(
            _api_condition(
                policy,
                EligibilityCategory.OTHER,
                additional,
                "addAplyQlfcCndCn",
            )
        )
    target = _source_text(fields.get("ptcpPrpTrgtCn"))
    if target is not None:
        unknowns.append(
            _api_condition(
                policy,
                EligibilityCategory.OTHER,
                target,
                "ptcpPrpTrgtCn",
            )
        )
    document_text = _source_text(fields.get("sbmsnDcmntCn"))
    documents = (
        ()
        if document_text is None
        else (
            RequiredDocument(
                text=document_text,
                evidence=(_api_evidence(policy, "sbmsnDcmntCn"),),
            ),
        )
    )
    has_content = any((requirements, unknowns, documents))
    return EligibilitySummary(
        coverage=(
            EligibilityCoverage.PARTIAL
            if has_content
            else EligibilityCoverage.UNKNOWN
        ),
        requirements=tuple(requirements),
        exclusions=(),
        preferences=(),
        documents=documents,
        unknowns=tuple(unknowns),
        institutional_contacts=(),
    )


def map_bokjiro_eligibility(policy: ExtractedPolicy) -> EligibilitySummary:
    """Map Bokjiro target text while retaining selection text as unknown."""

    fields = _api_source_fields(
        policy,
        BOKJIRO_SOURCE_ID,
        "detail_response",
        allow_missing=True,
    )
    target = _source_text(fields.get("tgtrDtlCn"))
    criteria = _source_text(fields.get("slctCritCn"))
    requirements = (
        ()
        if target is None
        else (
            _api_condition(
                policy,
                EligibilityCategory.OTHER,
                target,
                "tgtrDtlCn",
            ),
        )
    )
    unknowns = (
        ()
        if criteria is None
        else (
            _api_condition(
                policy,
                EligibilityCategory.OTHER,
                criteria,
                "slctCritCn",
            ),
        )
    )
    return EligibilitySummary(
        coverage=(
            EligibilityCoverage.PARTIAL
            if requirements or unknowns
            else EligibilityCoverage.UNKNOWN
        ),
        requirements=requirements,
        exclusions=(),
        preferences=(),
        documents=(),
        unknowns=unknowns,
        institutional_contacts=(),
    )


def map_cheonan_eligibility(policy: ExtractedPolicy) -> EligibilitySummary:
    """Map only approved source fields without inferring eligibility facts."""

    if policy.source_id != CHEONAN_SOURCE_ID:
        raise ValueError("Cheonan eligibility mapper received another source")
    source_fields = policy.extra.get("source_fields")
    if not isinstance(source_fields, dict):
        raise ValueError("Cheonan source fields are missing")
    detail = source_fields.get("detail_response")
    if not isinstance(detail, dict):
        raise ValueError("Cheonan detail source fields are missing")
    sections = detail.get("sections")
    contacts = detail.get("institutional_contact")
    if not isinstance(sections, dict) or not isinstance(contacts, dict):
        raise ValueError("Cheonan eligibility source fields are invalid")

    evidence = (
        EvidenceReference(
            source_id=policy.source_id,
            source_url=policy.source_url,
            collected_at=policy.collected_at,
            locator_type=EvidenceLocatorType.CSS_SELECTOR,
            locator=_DETAIL_SELECTOR,
        ),
    )
    requirements = _condition_items(sections, "eligibility", evidence)
    exclusions = _condition_items(
        sections,
        "excluded_conditions",
        evidence,
    )
    unknowns = _condition_items(sections, "other_conditions", evidence)
    documents = tuple(
        RequiredDocument(text=value, evidence=evidence)
        for value in _string_values(sections.get("required_documents"))
    )
    institutional_contacts = (
        *(
            InstitutionalContact(
                kind=InstitutionalContactKind.PHONE,
                label="대표전화",
                value=value,
                evidence=evidence,
            )
            for value in _string_values(contacts.get("phone_numbers"))
        ),
        *(
            InstitutionalContact(
                kind=InstitutionalContactKind.OFFICIAL_CHANNEL,
                label="공식 문의 채널",
                value=value,
                evidence=evidence,
            )
            for value in _string_values(contacts.get("channels"))
        ),
    )
    has_eligibility_content = any(
        (requirements, exclusions, documents, unknowns)
    )
    return EligibilitySummary(
        coverage=(
            EligibilityCoverage.PARTIAL
            if has_eligibility_content
            else EligibilityCoverage.UNKNOWN
        ),
        requirements=requirements,
        exclusions=exclusions,
        preferences=(),
        documents=documents,
        unknowns=unknowns,
        institutional_contacts=institutional_contacts,
    )


def _condition_items(
    sections: dict[str, Any],
    key: str,
    evidence: tuple[EvidenceReference, ...],
) -> tuple[EligibilityEvidenceItem, ...]:
    return tuple(
        EligibilityEvidenceItem(
            category=EligibilityCategory.OTHER,
            text=value,
            evidence=evidence,
        )
        for value in _string_values(sections.get(key))
    )


def _string_values(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item and item == item.strip()
        for item in value
    ):
        raise ValueError("Cheonan eligibility values must be normalized strings")
    return tuple(value)


def _api_source_fields(
    policy: ExtractedPolicy,
    expected_source_id: str,
    role: str,
    *,
    allow_missing: bool = False,
) -> dict[str, Any]:
    if policy.source_id != expected_source_id:
        raise ValueError("eligibility mapper received another source")
    source_fields = policy.extra.get("source_fields")
    if not isinstance(source_fields, dict):
        raise ValueError("API source fields are missing")
    selected = source_fields.get(role)
    if selected is None and allow_missing:
        return {}
    if not isinstance(selected, dict):
        raise ValueError("API eligibility source fields are invalid")
    return selected


def _api_condition(
    policy: ExtractedPolicy,
    category: EligibilityCategory,
    text: str,
    locator: str,
) -> EligibilityEvidenceItem:
    return EligibilityEvidenceItem(
        category=category,
        text=text,
        evidence=(_api_evidence(policy, locator),),
    )


def _api_evidence(
    policy: ExtractedPolicy,
    locator: str,
) -> EvidenceReference:
    return EvidenceReference(
        source_id=policy.source_id,
        source_url=policy.source_url,
        collected_at=policy.collected_at,
        locator_type=EvidenceLocatorType.SOURCE_FIELD,
        locator=locator,
    )


def _source_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("eligibility source text must be a string")
    selected = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    return None if selected in {"", "-", "--"} else selected


def _supported_institutional_contact(value: str | None) -> str | None:
    """Keep public contact text while excluding email and personal mobile data."""

    if value is None:
        return None
    selected = re.sub(r"\b[^\s@]+@[^\s@]+\b", "", value)
    selected = re.sub(
        r"(?<!\d)(?:\+?82[-.\s]?(?:\(0\))?[-.\s]?10|01[016789])"
        r"[-.\s]?\d{3,4}[-.\s]?\d{4}(?!\d)",
        "",
        selected,
    )
    selected = re.sub(
        r"\s*[/|,;]?\s*(?:담당자(?:\s*연락처)?|휴대전화|핸드폰)\s*$",
        "",
        selected,
    )
    selected = re.sub(r"\s*[/|,;]\s*(?=$|\n)", "", selected)
    selected = "\n".join(line.strip(" /|,;") for line in selected.splitlines())
    selected = "\n".join(line for line in selected.splitlines() if line)
    return selected or None
