"""Build deterministic synthetic Data fixtures and the canonical seed."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors.bokjiro import SOURCE_ID as BOKJIRO_SOURCE_ID
from collectors.extractors import BokjiroExtractor, YouthCenterExtractor
from collectors.normalizer import Normalizer
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
)
from collectors.youthcenter import SOURCE_ID as YOUTHCENTER_SOURCE_ID

COLLECTED_AT = datetime(2026, 7, 26, 6, 0, tzinfo=timezone.utc)
DETAIL_COLLECTED_AT = datetime(
    2026,
    7,
    26,
    6,
    1,
    tzinfo=timezone.utc,
)
COLLECTOR_VERSION = "synthetic-fixture/1.0.0"

YOUTH_LIST_ID = "10000000000000000000000000000000"
YOUTH_ITEM_IDS = (
    "11000000000000000000000000000001",
    "11000000000000000000000000000002",
    "11000000000000000000000000000003",
)
BOKJIRO_LIST_ID = "20000000000000000000000000000000"
BOKJIRO_ITEM_IDS = (
    "21000000000000000000000000000001",
    "21000000000000000000000000000002",
)
BOKJIRO_DETAIL_ID = "22000000000000000000000000000001"

MANAGED_GLOBS = (
    "data/fixtures/raw/**/*.json",
    "data/fixtures/extracted/*.json",
    "data/fixtures/normalized/*.json",
    "data/fixtures/contracts/*.json",
    "data/fixtures/rejected/*.json",
    "data/seeds/initial_programs.json",
)


def build_outputs() -> dict[Path, bytes]:
    raw_outputs, documents = _build_raw_outputs()
    extracted = [
        *YouthCenterExtractor().extract(documents),
        *BokjiroExtractor().extract(documents),
    ]
    results = [Normalizer().normalize(policy) for policy in extracted]

    accepted = [
        result.program.to_dict()
        for result in results
        if result.program is not None
    ]
    rejected = [
        {
            "source_id": result.candidate.get("source_id"),
            "external_id": result.candidate.get("external_id"),
            "status": result.status.value,
            "candidate": result.candidate,
            "issues": [issue.to_dict() for issue in result.issues],
        }
        for result in results
        if result.program is None
    ]
    search_contract_cases = _search_contract_cases(accepted)
    recurrent_quality_cases = _recurrent_quality_cases()
    eligibility_contract_cases = _eligibility_contract_cases()

    return {
        **raw_outputs,
        Path("data/fixtures/extracted/policies.json"): _json_bytes(
            [policy.to_dict() for policy in extracted],
            pretty=True,
        ),
        Path("data/fixtures/normalized/programs.json"): _json_bytes(
            accepted,
            pretty=True,
        ),
        Path("data/fixtures/rejected/programs.json"): _json_bytes(
            rejected,
            pretty=True,
        ),
        Path(
            "data/fixtures/contracts/policy_search_region_cases.json"
        ): _json_bytes(search_contract_cases, pretty=True),
        Path(
            "data/fixtures/contracts/recurrent_quality_cases.json"
        ): _json_bytes(recurrent_quality_cases, pretty=True),
        Path(
            "data/fixtures/contracts/eligibility_evidence_cases.json"
        ): _json_bytes(eligibility_contract_cases, pretty=True),
        Path("data/seeds/initial_programs.json"): _json_bytes(
            accepted,
            pretty=True,
        ),
    }


def _eligibility_contract_cases() -> dict[str, Any]:
    def evidence(
        source_id: str,
        source_url: str,
        collected_at: str,
        locator_type: str,
        locator: str,
    ) -> list[dict[str, str]]:
        return [
            {
                "source_id": source_id,
                "source_url": source_url,
                "collected_at": collected_at,
                "locator_type": locator_type,
                "locator": locator,
            }
        ]

    def condition(
        category: str,
        text: str,
        source_id: str,
        source_url: str,
        collected_at: str,
        locator_type: str,
        locator: str,
    ) -> dict[str, Any]:
        return {
            "category": category,
            "text": text,
            "evidence": evidence(
                source_id,
                source_url,
                collected_at,
                locator_type,
                locator,
            ),
        }

    def document(
        text: str,
        source_id: str,
        source_url: str,
        collected_at: str,
        locator_type: str,
        locator: str,
    ) -> dict[str, Any]:
        return {
            "text": text,
            "evidence": evidence(
                source_id,
                source_url,
                collected_at,
                locator_type,
                locator,
            ),
        }

    def contact(
        kind: str,
        label: str,
        value: str,
        source_id: str,
        source_url: str,
        collected_at: str,
    ) -> dict[str, Any]:
        return {
            "kind": kind,
            "label": label,
            "value": value,
            "evidence": evidence(
                source_id,
                source_url,
                collected_at,
                "css_selector",
                "#bo_v_con",
            ),
        }

    contract_source_id = "eligibility-contract-fixture"
    contract_source = "https://fixture.invalid/eligibility/complete"
    web_source = "https://fixture.invalid/cheonan/notice/674"
    return {
        "contract_version": "1.0.0",
        "cases": [
            {
                "case_id": "complete_contract_fixture",
                "profile": "normal",
                "summary": {
                    "coverage": "complete",
                    "requirements": [
                        condition(
                            "age",
                            "만 19세 이상 34세 이하",
                            contract_source_id,
                            contract_source,
                            "2026-08-10T03:00:00+00:00",
                            "source_field",
                            "synthetic.requirements.age",
                        ),
                        condition(
                            "region",
                            "합성시 거주 청년",
                            contract_source_id,
                            contract_source,
                            "2026-08-10T03:00:00+00:00",
                            "source_field",
                            "synthetic.requirements.region",
                        ),
                    ],
                    "exclusions": [
                        condition(
                            "education",
                            "합성 재학생은 지원 대상에서 제외",
                            contract_source_id,
                            contract_source,
                            "2026-08-10T03:00:00+00:00",
                            "source_field",
                            "synthetic.exclusions.education",
                        )
                    ],
                    "preferences": [],
                    "documents": [
                        document(
                            "합성 거주 확인서",
                            contract_source_id,
                            contract_source,
                            "2026-08-10T03:00:00+00:00",
                            "source_field",
                            "synthetic.documents",
                        )
                    ],
                    "unknowns": [],
                    "institutional_contacts": [],
                },
            },
            {
                "case_id": "partial_web_source",
                "profile": "boundary",
                "summary": {
                    "coverage": "partial",
                    "requirements": [
                        condition(
                            "other",
                            "합성시에 거주하는 1인가구 청년",
                            "cheonan-youthcenter-web",
                            web_source,
                            "2026-08-10T04:00:00+00:00",
                            "css_selector",
                            "#bo_v_con",
                        )
                    ],
                    "exclusions": [
                        condition(
                            "other",
                            "타 지역 이사 시 합성 지원 종료",
                            "cheonan-youthcenter-web",
                            web_source,
                            "2026-08-10T04:00:00+00:00",
                            "css_selector",
                            "#bo_v_con",
                        )
                    ],
                    "preferences": [],
                    "documents": [
                        document(
                            "합성 거주 사실 확인서류",
                            "cheonan-youthcenter-web",
                            web_source,
                            "2026-08-10T04:00:00+00:00",
                            "css_selector",
                            "#bo_v_con",
                        )
                    ],
                    "unknowns": [
                        condition(
                            "other",
                            "설치 환경에 따라 합성 지원이 제한될 수 있음",
                            "cheonan-youthcenter-web",
                            web_source,
                            "2026-08-10T04:00:00+00:00",
                            "css_selector",
                            "#bo_v_con",
                        )
                    ],
                    "institutional_contacts": [
                        contact(
                            "phone",
                            "대표전화",
                            "041-000-0000",
                            "cheonan-youthcenter-web",
                            web_source,
                            "2026-08-10T04:00:00+00:00",
                        ),
                        contact(
                            "official_channel",
                            "공식 문의 채널",
                            "카카오채널",
                            "cheonan-youthcenter-web",
                            web_source,
                            "2026-08-10T04:00:00+00:00",
                        ),
                    ],
                },
            },
            {
                "case_id": "unknown_missing_source_fields",
                "profile": "missing",
                "summary": {
                    "coverage": "unknown",
                    "requirements": [],
                    "exclusions": [],
                    "preferences": [],
                    "documents": [],
                    "unknowns": [],
                    "institutional_contacts": [],
                },
            },
            {
                "case_id": "partial_long_condition",
                "profile": "long",
                "summary": {
                    "coverage": "partial",
                    "requirements": [],
                    "exclusions": [],
                    "preferences": [],
                    "documents": [],
                    "unknowns": [
                        condition(
                            "household",
                            (
                                "합성 기준연도의 가구 구성과 소득 산정 범위가 "
                                "신청자의 세대 분리 시점 및 주민등록 상태에 따라 "
                                "달라질 수 있으므로 공식 안내문과 접수 기관의 "
                                "확인이 필요합니다."
                            ),
                            BOKJIRO_SOURCE_ID,
                            "https://fixture.invalid/welfare/SYN-LONG-001",
                            "2026-08-10T05:00:00+00:00",
                            "source_field",
                            "tgtrDtlCn",
                        )
                    ],
                    "institutional_contacts": [],
                },
            },
            {
                "case_id": "partial_source_conflict",
                "profile": "conflict",
                "summary": {
                    "coverage": "partial",
                    "requirements": [],
                    "exclusions": [],
                    "preferences": [],
                    "documents": [],
                    "unknowns": [
                        condition(
                            "other",
                            "합성 API 원문: 신청기간은 8월 31일까지",
                            YOUTHCENTER_SOURCE_ID,
                            "https://fixture.invalid/policies/SYN-CONFLICT-001",
                            "2026-08-10T06:00:00+00:00",
                            "source_field",
                            "aplyYmd",
                        ),
                        condition(
                            "other",
                            "합성 웹 원문: 신청기간은 8월 20일까지",
                            "cheonan-youthcenter-web",
                            "https://fixture.invalid/cheonan/notice/conflict",
                            "2026-08-10T06:05:00+00:00",
                            "css_selector",
                            "#bo_v_con",
                        ),
                    ],
                    "institutional_contacts": [],
                },
            },
        ],
    }


def _recurrent_quality_cases() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "base_seed_indexes": [0, 1],
        "cases": [
            {
                "id": "same_snapshot",
                "operation": "rerun",
                "expected": {
                    "updated": 0,
                    "unchanged": 2,
                    "duplicate": 0,
                },
            },
            {
                "id": "collection_metadata_only",
                "operation": "patch",
                "target_index": 0,
                "patch": {
                    "collected_at": "2026-08-10T03:00:00+00:00",
                    "provenance_collected_at": (
                        "2026-08-10T03:00:00+00:00"
                    ),
                },
                "expected": {
                    "updated": 0,
                    "unchanged": 2,
                    "duplicate": 0,
                },
            },
            {
                "id": "single_business_field",
                "operation": "patch",
                "target_index": 0,
                "patch": {"title": "변경된 합성 반복 수집 정책"},
                "expected": {
                    "updated": 1,
                    "unchanged": 1,
                    "duplicate": 0,
                },
            },
            {
                "id": "duplicate_in_run",
                "operation": "append_duplicate",
                "target_index": 0,
                "expected": {
                    "accepted": 2,
                    "inserted": 2,
                    "duplicate": 1,
                    "stored": 2,
                    "issue_code": "duplicate_identity",
                    "issue_stage": "validate",
                },
            },
            {
                "id": "invalid_batch",
                "operation": "remove_required_field",
                "target_index": 1,
                "field": "application_start",
                "expected": {
                    "inserted": 0,
                    "rejected": 1,
                    "committed": False,
                    "issue_stage": "validate",
                },
            },
            {
                "id": "persist_failure",
                "operation": "fail_second_write",
                "expected": {
                    "inserted": 0,
                    "failed": 1,
                    "committed": False,
                    "issue_code": "database_write_failed",
                    "issue_stage": "persist",
                },
            },
        ],
    }


def _search_contract_cases(
    programs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    youth = next(
        program
        for program in programs
        if program["external_id"] == "SYN-YOUTH-001"
    )
    nationwide_source = next(
        program
        for program in programs
        if program["external_id"] == "SYN-YOUTH-002"
    )
    unknown_source = next(
        program
        for program in programs
        if program["external_id"] == "SYN-BOK-001"
    )

    def program_case(
        case_id: str,
        source: dict[str, Any],
        *,
        coverage_scope: str,
        region_text: str | None,
        regions: list[str],
        region_rules: list[dict[str, str | None]],
    ) -> dict[str, Any]:
        program = deepcopy(source)
        program["external_id"] = f"SYN-SEARCH-{case_id.upper()}"
        program["title"] = f"합성 검색 계약 {case_id}"
        program["summary"] = "합성 검색 계약 요약"
        program["keywords"] = ["청년", "주거"]
        program["life_stages"] = ["청년"]
        program["target_groups"] = ["청년가구"]
        program["coverage_scope"] = coverage_scope
        program["region_text"] = region_text
        program["regions"] = regions
        program["region_rules"] = region_rules
        return {"case_id": case_id, "program": program}

    def rule(
        *,
        relation: str,
        resolution_status: str,
        region_scheme: str | None,
        region_code: str | None,
        source_code: str | None,
        source_text: str | None,
    ) -> dict[str, str | None]:
        return {
            "relation": relation,
            "resolution_status": resolution_status,
            "region_scheme": region_scheme,
            "region_code": region_code,
            "source_code": source_code,
            "source_text": source_text,
        }

    scheme = "kr-bjd-20260803"
    return [
        program_case(
            "nationwide",
            nationwide_source,
            coverage_scope="nationwide",
            region_text="전국",
            regions=["전국"],
            region_rules=[],
        ),
        program_case(
            "regional_parent",
            youth,
            coverage_scope="regional",
            region_text="충청남도",
            regions=["충청남도"],
            region_rules=[
                rule(
                    relation="include",
                    resolution_status="matched",
                    region_scheme=scheme,
                    region_code="4400000000",
                    source_code="44000",
                    source_text="충청남도",
                )
            ],
        ),
        program_case(
            "regional_exact",
            youth,
            coverage_scope="regional",
            region_text="천안시",
            regions=["천안시"],
            region_rules=[
                rule(
                    relation="include",
                    resolution_status="matched",
                    region_scheme=scheme,
                    region_code="4413000000",
                    source_code="44130",
                    source_text="천안시",
                )
            ],
        ),
        program_case(
            "regional_exclusion",
            youth,
            coverage_scope="regional",
            region_text="충청남도, 아산시 제외",
            regions=["충청남도"],
            region_rules=[
                rule(
                    relation="include",
                    resolution_status="matched",
                    region_scheme=scheme,
                    region_code="4400000000",
                    source_code="44000",
                    source_text="충청남도",
                ),
                rule(
                    relation="exclude",
                    resolution_status="matched",
                    region_scheme=scheme,
                    region_code="4420000000",
                    source_code="44200",
                    source_text="아산시 제외",
                ),
            ],
        ),
        program_case(
            "unknown",
            unknown_source,
            coverage_scope="unknown",
            region_text=None,
            regions=[],
            region_rules=[],
        ),
        program_case(
            "ambiguous",
            unknown_source,
            coverage_scope="unknown",
            region_text="광주",
            regions=[],
            region_rules=[
                rule(
                    relation="include",
                    resolution_status="ambiguous",
                    region_scheme=None,
                    region_code=None,
                    source_code=None,
                    source_text="광주",
                )
            ],
        ),
        program_case(
            "retired_code",
            youth,
            coverage_scope="regional",
            region_text="충청남도 천안군",
            regions=["천안군"],
            region_rules=[
                rule(
                    relation="include",
                    resolution_status="matched",
                    region_scheme=scheme,
                    region_code="4405000000",
                    source_code="44050",
                    source_text="충청남도 천안군",
                )
            ],
        ),
    ]


def write_outputs(
    outputs: Mapping[Path, bytes],
    root: Path = ROOT,
) -> None:
    for relative_path, content in sorted(
        outputs.items(),
        key=lambda item: item[0].as_posix(),
    ):
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def check_outputs(
    outputs: Mapping[Path, bytes],
    root: Path = ROOT,
) -> tuple[str, ...]:
    problems: list[str] = []
    expected = set(outputs)
    actual = _managed_files(root)
    for relative_path in sorted(expected - actual):
        problems.append(f"missing: {relative_path.as_posix()}")
    for relative_path in sorted(actual - expected):
        problems.append(f"unexpected: {relative_path.as_posix()}")
    for relative_path in sorted(expected & actual):
        if (root / relative_path).read_bytes() != outputs[relative_path]:
            problems.append(f"outdated: {relative_path.as_posix()}")
    return tuple(problems)


def _build_raw_outputs(
) -> tuple[dict[Path, bytes], tuple[RawPolicyDocument, ...]]:
    youth_items = _youth_items()
    bokjiro_items = _bokjiro_items()
    youth_url = "https://fixture.invalid/youthcenter/getPlcy"
    bokjiro_list_url = "https://fixture.invalid/bokjiro/list"
    bokjiro_detail_url = "https://fixture.invalid/bokjiro/detail"

    documents: list[tuple[Path, RawPolicyDocument]] = []
    youth_list = RawPolicyDocument.from_bytes(
        document_id=YOUTH_LIST_ID,
        source_id=YOUTHCENTER_SOURCE_ID,
        source_type=SourceType.API,
        document_role=RawDocumentRole.LIST_RESPONSE,
        external_id=None,
        parent_document_id=None,
        source_url=youth_url,
        collected_at=COLLECTED_AT,
        content_type="application/json",
        raw_format=RawFormat.JSON,
        raw_payload=_json_bytes(
            {
                "result": {
                    "resultCode": "200",
                    "youthPolicyList": youth_items,
                }
            }
        ),
        http_status=200,
        collector_version=COLLECTOR_VERSION,
    )
    documents.append(
        (
            Path(
                "data/fixtures/raw/youthcenter-api/"
                "list_response.json"
            ),
            youth_list,
        )
    )
    for index, item in enumerate(youth_items):
        documents.append(
            (
                Path(
                    "data/fixtures/raw/youthcenter-api/"
                    f"list_item_{index + 1}.json"
                ),
                RawPolicyDocument.from_bytes(
                    document_id=YOUTH_ITEM_IDS[index],
                    source_id=YOUTHCENTER_SOURCE_ID,
                    source_type=SourceType.API,
                    document_role=RawDocumentRole.LIST_ITEM,
                    external_id=item["plcyNo"],
                    parent_document_id=YOUTH_LIST_ID,
                    source_url=youth_url,
                    collected_at=COLLECTED_AT,
                    content_type="application/json",
                    raw_format=RawFormat.JSON,
                    raw_payload=_json_bytes(item),
                    http_status=200,
                    collector_version=COLLECTOR_VERSION,
                ),
            )
        )

    bokjiro_list = RawPolicyDocument.from_bytes(
        document_id=BOKJIRO_LIST_ID,
        source_id=BOKJIRO_SOURCE_ID,
        source_type=SourceType.API,
        document_role=RawDocumentRole.LIST_RESPONSE,
        external_id=None,
        parent_document_id=None,
        source_url=bokjiro_list_url,
        collected_at=COLLECTED_AT,
        content_type="application/xml",
        raw_format=RawFormat.XML,
        raw_payload=(
            "<wantedList>"
            + "".join(bokjiro_items)
            + "</wantedList>"
        ).encode("utf-8"),
        http_status=200,
        collector_version=COLLECTOR_VERSION,
    )
    documents.append(
        (
            Path(
                "data/fixtures/raw/bokjiro-central-welfare-api/"
                "list_response.json"
            ),
            bokjiro_list,
        )
    )
    for index, item_xml in enumerate(bokjiro_items):
        external_id = f"SYN-BOK-{index + 1:03d}"
        documents.append(
            (
                Path(
                    "data/fixtures/raw/bokjiro-central-welfare-api/"
                    f"list_item_{index + 1}.json"
                ),
                RawPolicyDocument.from_bytes(
                    document_id=BOKJIRO_ITEM_IDS[index],
                    source_id=BOKJIRO_SOURCE_ID,
                    source_type=SourceType.API,
                    document_role=RawDocumentRole.LIST_ITEM,
                    external_id=external_id,
                    parent_document_id=BOKJIRO_LIST_ID,
                    source_url=bokjiro_list_url,
                    collected_at=COLLECTED_AT,
                    content_type="application/xml",
                    raw_format=RawFormat.XML,
                    raw_payload=item_xml.encode("utf-8"),
                    http_status=200,
                    collector_version=COLLECTOR_VERSION,
                ),
            )
        )

    detail_xml = _bokjiro_detail_xml()
    documents.append(
        (
            Path(
                "data/fixtures/raw/bokjiro-central-welfare-api/"
                "detail_response_1.json"
            ),
            RawPolicyDocument.from_bytes(
                document_id=BOKJIRO_DETAIL_ID,
                source_id=BOKJIRO_SOURCE_ID,
                source_type=SourceType.API,
                document_role=RawDocumentRole.DETAIL_RESPONSE,
                external_id="SYN-BOK-001",
                parent_document_id=None,
                source_url=bokjiro_detail_url,
                collected_at=DETAIL_COLLECTED_AT,
                content_type="application/xml",
                raw_format=RawFormat.XML,
                raw_payload=detail_xml.encode("utf-8"),
                http_status=200,
                collector_version=COLLECTOR_VERSION,
            ),
        )
    )

    return (
        {
            relative_path: document.to_json_bytes()
            for relative_path, document in documents
        },
        tuple(document for _, document in documents),
    )


def _youth_items() -> list[dict[str, str]]:
    common = {
        "rgtrInstCdNm": "합성 등록기관",
        "addAplyQlfcCndCn": "",
        "aplyUrlAddr": "",
        "refUrlAddr2": "",
    }
    return [
        {
            **common,
            "plcyNo": "SYN-YOUTH-001",
            "plcyNm": "<b>합성 청년 주거 지원</b>",
            "operInstCdNm": "합성 주거기관",
            "lclsfNm": "주거",
            "mclsfNm": "주거비 지원",
            "plcyKywdNm": "월세,보조금",
            "plcyExplnCn": "합성 청년 주거 정책 요약",
            "aplyYmd": "2026. 1. 1. ~ 2026. 6. 30.",
            "aplyPrdSeCd": "0057001",
            "zipCd": "서울시",
            "sprtTrgtAgeLmtYn": "Y",
            "sprtTrgtMinAge": "19",
            "sprtTrgtMaxAge": "34",
            "ptcpPrpTrgtCn": "합성 청년 대상",
            "plcySprtCn": "<p>합성 월 지원</p>",
            "plcyAplyMthdCn": "온라인 신청",
            "refUrlAddr1": "https://fixture.invalid/youth/001",
        },
        {
            **common,
            "plcyNo": "SYN-YOUTH-002",
            "plcyNm": "합성 상시 생활 지원",
            "operInstCdNm": "",
            "lclsfNm": "금융･복지･문화",
            "mclsfNm": "생활지원",
            "plcyKywdNm": "생활비",
            "plcyExplnCn": "합성 상시 생활 정책 요약",
            "aplyYmd": "",
            "aplyPrdSeCd": "0057002",
            "zipCd": "전국",
            "sprtTrgtAgeLmtYn": "N",
            "sprtTrgtMinAge": "",
            "sprtTrgtMaxAge": "",
            "ptcpPrpTrgtCn": "",
            "plcySprtCn": "합성 생활 지원",
            "plcyAplyMthdCn": "",
            "refUrlAddr1": "https://fixture.invalid/youth/002",
        },
        {
            **common,
            "plcyNo": "SYN-YOUTH-REJECTED",
            "plcyNm": "",
            "operInstCdNm": "합성 오류기관",
            "lclsfNm": "기타",
            "mclsfNm": "기타지원",
            "plcyKywdNm": "합성오류",
            "plcyExplnCn": "필수 제목이 없는 합성 정책 요약",
            "aplyYmd": "",
            "aplyPrdSeCd": "0057003",
            "zipCd": "전국",
            "sprtTrgtAgeLmtYn": "N",
            "sprtTrgtMinAge": "",
            "sprtTrgtMaxAge": "",
            "ptcpPrpTrgtCn": "",
            "plcySprtCn": "필수 제목이 없는 합성 실패 사례",
            "plcyAplyMthdCn": "",
            "refUrlAddr1": "https://fixture.invalid/youth/rejected",
        },
    ]


def _bokjiro_items() -> tuple[str, str]:
    return (
        (
            "<servList>"
            "<servId>SYN-BOK-001</servId>"
            "<servNm>합성 청년 자산 지원</servNm>"
            "<jurMnofNm>합성 복지부처</jurMnofNm>"
            "<intrsThemaArray>서민금융,생활지원</intrsThemaArray>"
            "<lifeArray>청년</lifeArray>"
            "<trgterIndvdlArray>저소득</trgterIndvdlArray>"
            "<servDgst>합성 목록 요약</servDgst>"
            "<servDtlLink>https://fixture.invalid/bokjiro/001"
            "</servDtlLink>"
            "</servList>"
        ),
        (
            "<servList>"
            "<servId>SYN-BOK-002</servId>"
            "<servNm>합성 목록 전용 지원</servNm>"
            "<jurMnofNm>합성 복지부처</jurMnofNm>"
            "<servDgst>상세가 없는 합성 목록 사례</servDgst>"
            "<servDtlLink>https://fixture.invalid/bokjiro/002"
            "</servDtlLink>"
            "</servList>"
        ),
    )


def _bokjiro_detail_xml() -> str:
    return (
        "<wantedDtl>"
        "<servId>SYN-BOK-001</servId>"
        "<servNm>합성 청년 자산 지원 상세</servNm>"
        "<jurMnofNm>합성 복지부처</jurMnofNm>"
        "<tgtrDtlCn>합성 지원 대상</tgtrDtlCn>"
        "<slctCritCn>합성 선정 기준</slctCritCn>"
        "<wlfareInfoOutlCn>합성 상세 정책 개요</wlfareInfoOutlCn>"
        "<intrsThemaArray>주거, 서민금융</intrsThemaArray>"
        "<lifeArray>청년</lifeArray>"
        "<trgterIndvdlArray>저소득 청년</trgterIndvdlArray>"
        "<alwServCn>합성 상세 지원 내용</alwServCn>"
        "<servSeCode>01</servSeCode>"
        "<servSeCode>02</servSeCode>"
        "</wantedDtl>"
    )


def _json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    options: dict[str, Any] = {
        "ensure_ascii": False,
        "sort_keys": True,
    }
    if pretty:
        options["indent"] = 2
    else:
        options["separators"] = (",", ":")
    return (json.dumps(value, **options) + "\n").encode("utf-8")


def _managed_files(root: Path) -> set[Path]:
    files: set[Path] = set()
    for pattern in MANAGED_GLOBS:
        files.update(
            path.relative_to(root)
            for path in root.glob(pattern)
            if path.is_file()
        )
    return files


def _parse_args(
    arguments: Iterable[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build or verify deterministic synthetic Data fixtures and seed."
        )
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--write",
        action="store_true",
        help="write generated Fixture and Seed files",
    )
    action.add_argument(
        "--check",
        action="store_true",
        help="verify committed files match deterministic generation",
    )
    return parser.parse_args(arguments)


def main(arguments: Iterable[str] | None = None) -> int:
    options = _parse_args(arguments)
    outputs = build_outputs()
    if options.write:
        write_outputs(outputs)
        print(f"Generated {len(outputs)} Fixture and Seed files.")
        return 0
    problems = check_outputs(outputs)
    if problems:
        print("Fixture and Seed validation failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print(f"Fixture and Seed validation passed ({len(outputs)} files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
