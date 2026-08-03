"""Source-specific Raw interpretation into the common extracted contract."""

from __future__ import annotations

import json
import urllib.parse
import xml.etree.ElementTree as ElementTree
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from typing import Any

from collectors.bokjiro import SOURCE_ID as BOKJIRO_SOURCE_ID
from collectors.extracted import (
    ExtractedCoverageScope,
    ExtractedPolicy,
    ExtractedRegionRelation,
    ExtractionError,
    SourceRegionEvidence,
    SourceProvenance,
)
from collectors.profile import SourceFieldProfile, build_field_profile
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
)
from collectors.youthcenter import SOURCE_ID as YOUTHCENTER_SOURCE_ID


YOUTHCENTER_SOURCE_NAME = "온통청년 청년정책 API"
BOKJIRO_SOURCE_NAME = "복지로 중앙부처 복지서비스 API"

_APPLICATION_PERIOD_CODES = {
    "0057001": "특정기간",
    "0057002": "상시",
    "0057003": "마감",
}
_SENSITIVE_QUERY_NAMES = {
    "apikey",
    "apikeynm",
    "openapivlak",
    "servicekey",
}
_YOUTHCENTER_REGION_SCHEME = "kr-bjd-prefix5"


class YouthCenterExtractor:
    source_id = YOUTHCENTER_SOURCE_ID

    def extract(
        self,
        documents: Iterable[RawPolicyDocument],
    ) -> tuple[ExtractedPolicy, ...]:
        source_documents = _source_documents(documents, self.source_id)
        list_responses = _list_responses(source_documents, RawFormat.JSON)
        items = _unique_documents(
            source_documents,
            RawDocumentRole.LIST_ITEM,
            RawFormat.JSON,
        )
        unsupported_details = [
            document
            for document in source_documents
            if document.document_role
            is RawDocumentRole.DETAIL_RESPONSE
        ]
        if unsupported_details:
            raise ExtractionError(
                "youthcenter-api does not support detail Raw documents"
            )

        policies: list[ExtractedPolicy] = []
        for item in items:
            parent = _parent_list_response(item, list_responses)
            fields = _json_object(item)
            external_id = _required_external_id(item, fields.get("plcyNo"))
            provenance = _provenance(parent, item)
            application_period = _present_text(fields.get("aplyYmd"))
            if application_period is None:
                application_period = _APPLICATION_PERIOD_CODES.get(
                    _present_text(fields.get("aplyPrdSeCd")) or ""
                )
            coverage_scope, region_evidence = _youth_region_evidence(
                fields.get("zipCd")
            )
            policies.append(
                ExtractedPolicy(
                    source_id=self.source_id,
                    source_name=YOUTHCENTER_SOURCE_NAME,
                    external_id=external_id,
                    title=_present_text(fields.get("plcyNm")),
                    organization=(
                        _present_text(fields.get("operInstCdNm"))
                        or _present_text(fields.get("rgtrInstCdNm"))
                    ),
                    summary=_present_text(fields.get("plcyExplnCn")),
                    category_text=_present_text(fields.get("lclsfNm")),
                    keywords=_split_text_values(
                        fields.get("mclsfNm"),
                        fields.get("plcyKywdNm"),
                    ),
                    application_period_text=application_period,
                    region_text=_present_text(fields.get("zipCd")),
                    coverage_scope_hint=coverage_scope,
                    region_evidence=region_evidence,
                    age_text=_youth_age_text(fields),
                    eligibility_text=_join_text(
                        fields.get("ptcpPrpTrgtCn"),
                        fields.get("addAplyQlfcCndCn"),
                    ),
                    support_content=_present_text(
                        fields.get("plcySprtCn")
                    ),
                    application_method=_present_text(
                        fields.get("plcyAplyMthdCn")
                    ),
                    source_url=_first_public_url(
                        fields.get("refUrlAddr1"),
                        fields.get("aplyUrlAddr"),
                        fields.get("refUrlAddr2"),
                        fallback=item.source_url,
                    ),
                    collected_at=max(
                        entry.collected_at
                        for entry in provenance
                    ),
                    provenance=provenance,
                    extra={
                        "source_fields": {
                            "list_item": deepcopy(fields),
                            "detail_response": None,
                        }
                    },
                )
            )
        return tuple(policies)

    def profiles(
        self,
        documents: Iterable[RawPolicyDocument],
    ) -> tuple[SourceFieldProfile, ...]:
        source_documents = _source_documents(documents, self.source_id)
        records = [
            _json_object(document)
            for document in _unique_documents(
                source_documents,
                RawDocumentRole.LIST_ITEM,
                RawFormat.JSON,
            )
        ]
        return (
            build_field_profile(
                source_id=self.source_id,
                document_role=RawDocumentRole.LIST_ITEM,
                records=records,
            ),
        )


class BokjiroExtractor:
    source_id = BOKJIRO_SOURCE_ID

    def extract(
        self,
        documents: Iterable[RawPolicyDocument],
    ) -> tuple[ExtractedPolicy, ...]:
        source_documents = _source_documents(documents, self.source_id)
        list_responses = _list_responses(source_documents, RawFormat.XML)
        items = _unique_documents(
            source_documents,
            RawDocumentRole.LIST_ITEM,
            RawFormat.XML,
        )
        details = _documents_by_external_id(
            source_documents,
            RawDocumentRole.DETAIL_RESPONSE,
            RawFormat.XML,
        )
        item_ids = {
            item.external_id
            for item in items
        }
        orphan_details = set(details) - item_ids
        if orphan_details:
            raise ExtractionError(
                "Bokjiro detail Raw document has no matching list item"
            )

        policies: list[ExtractedPolicy] = []
        for item in items:
            parent = _parent_list_response(item, list_responses)
            list_fields = _xml_leaf_fields(item)
            external_id = _required_external_id(
                item,
                list_fields.get("servId"),
            )
            detail = details.get(external_id)
            detail_fields = (
                _xml_leaf_fields(detail)
                if detail is not None
                else None
            )
            if (
                detail is not None
                and _present_text(detail_fields.get("servId"))
                != external_id
            ):
                raise ExtractionError(
                    "Bokjiro detail payload external ID does not match Raw"
                )
            provenance = _provenance(
                parent,
                item,
                *(() if detail is None else (detail,)),
            )
            interest_values = _prefer_text_values(
                detail_fields,
                list_fields,
                "intrsThemaArray",
            )
            interest_text = (
                ",".join(interest_values)
                if interest_values
                else None
            )
            policies.append(
                ExtractedPolicy(
                    source_id=self.source_id,
                    source_name=BOKJIRO_SOURCE_NAME,
                    external_id=external_id,
                    title=_prefer(
                        detail_fields,
                        list_fields,
                        "servNm",
                    ),
                    organization=_prefer(
                        detail_fields,
                        list_fields,
                        "jurMnofNm",
                    ),
                    summary=(
                        _prefer(
                            detail_fields,
                            list_fields,
                            "wlfareInfoOutlCn",
                        )
                        or _present_text(list_fields.get("servDgst"))
                    ),
                    category_text=interest_text,
                    keywords=interest_values,
                    life_stages=_prefer_text_values(
                        detail_fields,
                        list_fields,
                        "lifeArray",
                    ),
                    target_groups=_prefer_text_values(
                        detail_fields,
                        list_fields,
                        "trgterIndvdlArray",
                    ),
                    application_period_text=None,
                    region_text=None,
                    age_text=None,
                    eligibility_text=_join_text(
                        None
                        if detail_fields is None
                        else detail_fields.get("tgtrDtlCn"),
                        None
                        if detail_fields is None
                        else detail_fields.get("slctCritCn"),
                    ),
                    support_content=(
                        _prefer(
                            detail_fields,
                            list_fields,
                            "alwServCn",
                        )
                        or _present_text(list_fields.get("servDgst"))
                    ),
                    application_method=None,
                    source_url=_first_public_url(
                        list_fields.get("servDtlLink"),
                        fallback=(
                            detail.source_url
                            if detail is not None
                            else item.source_url
                        ),
                    ),
                    collected_at=max(
                        entry.collected_at
                        for entry in provenance
                    ),
                    provenance=provenance,
                    extra={
                        "source_fields": {
                            "list_item": deepcopy(list_fields),
                            "detail_response": deepcopy(detail_fields),
                        }
                    },
                )
            )
        return tuple(policies)

    def profiles(
        self,
        documents: Iterable[RawPolicyDocument],
    ) -> tuple[SourceFieldProfile, ...]:
        source_documents = _source_documents(documents, self.source_id)
        item_records = [
            _xml_leaf_fields(document)
            for document in _unique_documents(
                source_documents,
                RawDocumentRole.LIST_ITEM,
                RawFormat.XML,
            )
        ]
        detail_records = [
            _xml_leaf_fields(document)
            for document in _unique_documents(
                source_documents,
                RawDocumentRole.DETAIL_RESPONSE,
                RawFormat.XML,
            )
        ]
        return (
            build_field_profile(
                source_id=self.source_id,
                document_role=RawDocumentRole.LIST_ITEM,
                records=item_records,
            ),
            build_field_profile(
                source_id=self.source_id,
                document_role=RawDocumentRole.DETAIL_RESPONSE,
                records=detail_records,
            ),
        )


def _source_documents(
    documents: Iterable[RawPolicyDocument],
    source_id: str,
) -> list[RawPolicyDocument]:
    selected = [
        document
        for document in documents
        if document.source_id == source_id
    ]
    if not selected:
        raise ExtractionError(f"no Raw documents found for {source_id}")
    return selected


def _list_responses(
    documents: Sequence[RawPolicyDocument],
    expected_format: RawFormat,
) -> dict[str, RawPolicyDocument]:
    selected = _unique_documents(
        documents,
        RawDocumentRole.LIST_RESPONSE,
        expected_format,
    )
    return {
        document.document_id: document
        for document in selected
    }


def _unique_documents(
    documents: Sequence[RawPolicyDocument],
    role: RawDocumentRole,
    expected_format: RawFormat,
) -> list[RawPolicyDocument]:
    selected = [
        document
        for document in documents
        if document.document_role is role
    ]
    if any(document.raw_format is not expected_format for document in selected):
        raise ExtractionError(
            f"{role.value} Raw document has an unexpected format"
        )
    seen: set[str] = set()
    for document in selected:
        key = document.external_id or document.document_id
        if key in seen:
            raise ExtractionError(
                f"duplicate {role.value} Raw document"
            )
        seen.add(key)
    return selected


def _documents_by_external_id(
    documents: Sequence[RawPolicyDocument],
    role: RawDocumentRole,
    expected_format: RawFormat,
) -> dict[str, RawPolicyDocument]:
    selected = _unique_documents(documents, role, expected_format)
    return {
        document.external_id: document
        for document in selected
        if document.external_id is not None
    }


def _parent_list_response(
    item: RawPolicyDocument,
    list_responses: Mapping[str, RawPolicyDocument],
) -> RawPolicyDocument:
    if item.parent_document_id not in list_responses:
        raise ExtractionError(
            "list item does not reference an available list response"
        )
    return list_responses[item.parent_document_id]


def _json_object(document: RawPolicyDocument) -> dict[str, Any]:
    try:
        value = json.loads(document.raw_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ExtractionError("list item Raw payload is not valid JSON") from None
    if not isinstance(value, dict):
        raise ExtractionError("list item JSON payload must be an object")
    return value


def _xml_leaf_fields(
    document: RawPolicyDocument,
) -> dict[str, str | list[str]]:
    try:
        root = ElementTree.fromstring(document.raw_bytes)
    except (ElementTree.ParseError, UnicodeDecodeError):
        raise ExtractionError("Raw payload is not valid XML") from None
    values: defaultdict[str, list[str]] = defaultdict(list)
    for element in root.iter():
        if len(element) == 0:
            values[_local_name(element.tag)].append(
                "" if element.text is None else element.text
            )
    return {
        field_name: entries[0] if len(entries) == 1 else entries
        for field_name, entries in values.items()
    }


def _required_external_id(
    document: RawPolicyDocument,
    payload_value: Any,
) -> str:
    if (
        not isinstance(payload_value, str)
        or payload_value.strip() != document.external_id
    ):
        raise ExtractionError(
            "payload external ID does not match Raw metadata"
        )
    if document.external_id is None:
        raise ExtractionError("Raw external ID is missing")
    return document.external_id


def _provenance(
    *documents: RawPolicyDocument,
) -> tuple[SourceProvenance, ...]:
    return tuple(
        SourceProvenance.from_raw(document)
        for document in documents
    )


def _present_text(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value


def _join_text(*values: Any) -> str | None:
    selected = [
        value
        for value in (_present_text(item) for item in values)
        if value is not None
    ]
    return "\n".join(selected) if selected else None


def _split_text_values(*values: Any) -> tuple[str, ...]:
    selected: list[str] = []

    def append(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                append(item)
            return
        if not isinstance(value, str):
            return
        for token in value.split(","):
            normalized = token.strip()
            if normalized and normalized not in selected:
                selected.append(normalized)

    for value in values:
        append(value)
    return tuple(selected)


def _youth_region_evidence(
    value: Any,
) -> tuple[
    ExtractedCoverageScope,
    tuple[SourceRegionEvidence, ...],
]:
    text = _present_text(value)
    if text is None:
        return ExtractedCoverageScope.UNKNOWN, ()
    if text.strip() == "전국":
        return ExtractedCoverageScope.NATIONWIDE, ()

    codes = _split_text_values(text)
    if not codes or any(
        len(code) != 5 or not code.isascii() or not code.isdigit()
        for code in codes
    ):
        return ExtractedCoverageScope.UNKNOWN, ()
    return (
        ExtractedCoverageScope.REGIONAL,
        tuple(
            SourceRegionEvidence(
                relation=ExtractedRegionRelation.INCLUDE,
                external_scheme=_YOUTHCENTER_REGION_SCHEME,
                source_code=code,
                source_text=None,
            )
            for code in codes
        ),
    )


def _prefer(
    preferred: Mapping[str, Any] | None,
    fallback: Mapping[str, Any],
    field_name: str,
) -> str | None:
    if preferred is not None:
        value = _present_text(preferred.get(field_name))
        if value is not None:
            return value
    return _present_text(fallback.get(field_name))


def _prefer_text_values(
    preferred: Mapping[str, Any] | None,
    fallback: Mapping[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    preferred_values = _split_text_values(
        None if preferred is None else preferred.get(field_name)
    )
    return (
        preferred_values
        if preferred_values
        else _split_text_values(fallback.get(field_name))
    )


def _youth_age_text(fields: Mapping[str, Any]) -> str | None:
    limit = _present_text(fields.get("sprtTrgtAgeLmtYn"))
    if limit == "N":
        return "연령 제한 없음"
    minimum = _present_text(fields.get("sprtTrgtMinAge"))
    maximum = _present_text(fields.get("sprtTrgtMaxAge"))
    if minimum is not None and maximum is not None:
        return f"{minimum}세 ~ {maximum}세"
    if minimum is not None:
        return f"{minimum}세 이상"
    if maximum is not None:
        return f"{maximum}세 이하"
    return None


def _first_public_url(*values: Any, fallback: str) -> str:
    for value in values:
        if not isinstance(value, str) or not value.strip():
            continue
        parsed = urllib.parse.urlsplit(value)
        try:
            port = parsed.port
        except ValueError:
            continue
        query_names = {
            name.casefold()
            for name, _ in urllib.parse.parse_qsl(
                parsed.query,
                keep_blank_values=True,
            )
        }
        if (
            parsed.scheme.lower() in {"http", "https"}
            and parsed.hostname
            and parsed.username is None
            and parsed.password is None
            and (port is None or 1 <= port <= 65535)
            and not query_names.intersection(_SENSITIVE_QUERY_NAMES)
        ):
            return value
    return fallback


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
