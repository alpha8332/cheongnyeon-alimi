from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone

from collectors.extracted import ExtractedPolicy, ExtractionError
from collectors.extractors import BokjiroExtractor, YouthCenterExtractor
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
)


COLLECTED_AT = datetime(2026, 7, 26, 7, 30, tzinfo=timezone.utc)
YOUTH_URL = "https://www.youthcenter.go.kr/go/ythip/getPlcy"
BOKJIRO_LIST_URL = (
    "https://apis.data.go.kr/B554287/"
    "NationalWelfareInformationsV001/NationalWelfarelistV001"
)
BOKJIRO_DETAIL_URL = (
    "https://apis.data.go.kr/B554287/"
    "NationalWelfareInformationsV001/NationalWelfaredetailedV001"
)


def raw_document(
    *,
    number: int,
    source_id: str,
    role: RawDocumentRole,
    payload: bytes,
    raw_format: RawFormat,
    source_url: str,
    external_id: str | None = None,
    parent_document_id: str | None = None,
    collected_at: datetime = COLLECTED_AT,
) -> RawPolicyDocument:
    return RawPolicyDocument.from_bytes(
        document_id=f"{number:032x}",
        source_id=source_id,
        source_type=SourceType.API,
        document_role=role,
        external_id=external_id,
        parent_document_id=parent_document_id,
        source_url=source_url,
        collected_at=collected_at,
        content_type=(
            "application/json"
            if raw_format is RawFormat.JSON
            else "application/xml"
        ),
        raw_format=raw_format,
        raw_payload=payload,
        http_status=200,
        collector_version="test/1.0",
    )


def youth_documents() -> list[RawPolicyDocument]:
    parent = raw_document(
        number=1,
        source_id="youthcenter-api",
        role=RawDocumentRole.LIST_RESPONSE,
        payload=b'{"resultCode":200}',
        raw_format=RawFormat.JSON,
        source_url=YOUTH_URL,
    )
    first_fields = {
        "plcyNo": "R000000001",
        "plcyNm": "Policy one",
        "operInstCdNm": "",
        "rgtrInstCdNm": "Fallback organization",
        "lclsfNm": "주거",
        "mclsfNm": "주거비 지원",
        "plcyKywdNm": "보조금",
        "aplyYmd": "",
        "aplyPrdSeCd": "0057002",
        "zipCd": "11110,11140",
        "sprtTrgtAgeLmtYn": "Y",
        "sprtTrgtMinAge": "19",
        "sprtTrgtMaxAge": "34",
        "ptcpPrpTrgtCn": "청년",
        "addAplyQlfcCndCn": "추가 조건",
        "plcySprtCn": "지원 내용",
        "plcyAplyMthdCn": "",
        "jobCd": "0013010",
        "refUrlAddr1": "https://example.test/policy/1",
    }
    second_fields = {
        "plcyNo": "R000000002",
        "plcyNm": "Policy two",
        "operInstCdNm": "Organization",
        "aplyYmd": "20260101 ~ 20261231",
        "sprtTrgtAgeLmtYn": "N",
        "plcySprtCn": "Known support",
        "optional": "",
    }
    return [
        parent,
        *[
            raw_document(
                number=index + 1,
                source_id="youthcenter-api",
                role=RawDocumentRole.LIST_ITEM,
                payload=json.dumps(
                    fields,
                    ensure_ascii=False,
                ).encode("utf-8"),
                raw_format=RawFormat.JSON,
                source_url=YOUTH_URL,
                external_id=fields["plcyNo"],
                parent_document_id=parent.document_id,
            )
            for index, fields in enumerate(
                (first_fields, second_fields),
                start=1,
            )
        ],
    ]


def bokjiro_documents() -> list[RawPolicyDocument]:
    parent = raw_document(
        number=10,
        source_id="bokjiro-central-welfare-api",
        role=RawDocumentRole.LIST_RESPONSE,
        payload=b"<wantedList><resultCode>0</resultCode></wantedList>",
        raw_format=RawFormat.XML,
        source_url=BOKJIRO_LIST_URL,
    )
    first_item = raw_document(
        number=11,
        source_id="bokjiro-central-welfare-api",
        role=RawDocumentRole.LIST_ITEM,
        payload=(
            "<servList>"
            "<servId>WLF000001</servId>"
            "<servNm>List title</servNm>"
            "<jurMnofNm>List ministry</jurMnofNm>"
            "<intrsThemaArray>일자리,생활지원</intrsThemaArray>"
            "<lifeArray>청년</lifeArray>"
            "<servDgst>List support</servDgst>"
            "<servDtlLink>https://example.test/service/1</servDtlLink>"
            "</servList>"
        ).encode(),
        raw_format=RawFormat.XML,
        source_url=BOKJIRO_LIST_URL,
        external_id="WLF000001",
        parent_document_id=parent.document_id,
    )
    second_item = raw_document(
        number=12,
        source_id="bokjiro-central-welfare-api",
        role=RawDocumentRole.LIST_ITEM,
        payload=(
            "<servList>"
            "<servId>WLF000002</servId>"
            "<servNm>List-only title</servNm>"
            "<jurMnofNm>List-only ministry</jurMnofNm>"
            "<servDgst>List-only support</servDgst>"
            "<optional></optional>"
            "</servList>"
        ).encode(),
        raw_format=RawFormat.XML,
        source_url=BOKJIRO_LIST_URL,
        external_id="WLF000002",
        parent_document_id=parent.document_id,
    )
    detail = raw_document(
        number=13,
        source_id="bokjiro-central-welfare-api",
        role=RawDocumentRole.DETAIL_RESPONSE,
        payload=(
            "<wantedDtl>"
            "<resultCode>0</resultCode>"
            "<servId>WLF000001</servId>"
            "<servNm>Detail title</servNm>"
            "<jurMnofNm>Detail ministry</jurMnofNm>"
            "<tgtrDtlCn>Target detail</tgtrDtlCn>"
            "<slctCritCn>Selection detail</slctCritCn>"
            "<alwServCn>Detail support</alwServCn>"
            "<servSeCode>010</servSeCode>"
            "<servSeCode>020</servSeCode>"
            "<servSeDetailNm>문의</servSeDetailNm>"
            "<servSeDetailNm>사이트</servSeDetailNm>"
            "</wantedDtl>"
        ).encode(),
        raw_format=RawFormat.XML,
        source_url=BOKJIRO_DETAIL_URL,
        external_id="WLF000001",
        collected_at=COLLECTED_AT + timedelta(seconds=1),
    )
    return [parent, first_item, second_item, detail]


class YouthCenterExtractorTests(unittest.TestCase):
    def test_extracts_common_fields_and_preserves_raw_source_fields(
        self,
    ) -> None:
        policies = YouthCenterExtractor().extract(youth_documents())

        self.assertEqual(2, len(policies))
        first = policies[0]
        self.assertIsInstance(first, ExtractedPolicy)
        self.assertEqual("Fallback organization", first.organization)
        self.assertEqual("상시", first.application_period_text)
        self.assertEqual("19세 ~ 34세", first.age_text)
        self.assertEqual("청년\n추가 조건", first.eligibility_text)
        self.assertEqual("https://example.test/policy/1", first.source_url)
        self.assertEqual(2, len(first.provenance))
        self.assertEqual(
            [
                RawDocumentRole.LIST_RESPONSE,
                RawDocumentRole.LIST_ITEM,
            ],
            [entry.document_role for entry in first.provenance],
        )
        source_fields = first.extra["source_fields"]["list_item"]
        self.assertEqual("", source_fields["operInstCdNm"])
        self.assertEqual("0013010", source_fields["jobCd"])
        self.assertEqual("주거비 지원", source_fields["mclsfNm"])
        self.assertIsNone(
            first.extra["source_fields"]["detail_response"]
        )
        self.assertEqual("연령 제한 없음", policies[1].age_text)
        self.assertIsNone(policies[1].category_text)
        self.assertEqual(
            "Known support",
            policies[1].support_content,
        )

    def test_profiles_missing_and_empty_fields_separately(self) -> None:
        profile = YouthCenterExtractor().profiles(
            youth_documents()
        )[0]
        fields = {
            field.field_name: field
            for field in profile.fields
        }

        self.assertEqual(2, profile.document_count)
        self.assertEqual(1, fields["lclsfNm"].present_count)
        self.assertEqual(1, fields["lclsfNm"].missing_count)
        self.assertEqual(0.5, fields["lclsfNm"].presence_rate)
        self.assertEqual(1, fields["operInstCdNm"].empty_count)
        self.assertEqual(0.5, fields["operInstCdNm"].empty_rate)
        self.assertEqual(("string",), fields["plcyNo"].observed_types)

    def test_rejects_payload_and_raw_external_id_mismatch(self) -> None:
        documents = youth_documents()
        bad_item = raw_document(
            number=4,
            source_id="youthcenter-api",
            role=RawDocumentRole.LIST_ITEM,
            payload=b'{"plcyNo":"OTHER"}',
            raw_format=RawFormat.JSON,
            source_url=YOUTH_URL,
            external_id="R000000003",
            parent_document_id=documents[0].document_id,
        )

        with self.assertRaises(ExtractionError):
            YouthCenterExtractor().extract([documents[0], bad_item])


class BokjiroExtractorTests(unittest.TestCase):
    def test_combines_detail_and_keeps_list_only_values(self) -> None:
        policies = BokjiroExtractor().extract(bokjiro_documents())

        self.assertEqual(2, len(policies))
        detailed, list_only = policies
        self.assertIsInstance(detailed, ExtractedPolicy)
        self.assertEqual("Detail title", detailed.title)
        self.assertEqual("Detail ministry", detailed.organization)
        self.assertEqual(
            "Target detail\nSelection detail",
            detailed.eligibility_text,
        )
        self.assertEqual("Detail support", detailed.support_content)
        self.assertEqual(3, len(detailed.provenance))
        self.assertEqual(
            COLLECTED_AT + timedelta(seconds=1),
            detailed.collected_at,
        )
        detail_fields = detailed.extra["source_fields"][
            "detail_response"
        ]
        self.assertEqual(["010", "020"], detail_fields["servSeCode"])
        self.assertEqual(
            ["문의", "사이트"],
            detail_fields["servSeDetailNm"],
        )

        self.assertEqual("List-only title", list_only.title)
        self.assertEqual("List-only ministry", list_only.organization)
        self.assertEqual("List-only support", list_only.support_content)
        self.assertEqual(2, len(list_only.provenance))
        self.assertIsNone(
            list_only.extra["source_fields"]["detail_response"]
        )
        self.assertEqual(
            "",
            list_only.extra["source_fields"]["list_item"]["optional"],
        )

    def test_profiles_optional_and_repeated_xml_fields(self) -> None:
        list_profile, detail_profile = BokjiroExtractor().profiles(
            bokjiro_documents()
        )
        list_fields = {
            field.field_name: field
            for field in list_profile.fields
        }
        detail_fields = {
            field.field_name: field
            for field in detail_profile.fields
        }

        self.assertEqual(2, list_profile.document_count)
        self.assertEqual(1, list_fields["lifeArray"].missing_count)
        self.assertEqual(0.5, list_fields["lifeArray"].presence_rate)
        self.assertEqual(1, list_fields["optional"].empty_count)
        self.assertEqual(1, detail_profile.document_count)
        self.assertEqual(
            ("array",),
            detail_fields["servSeCode"].observed_types,
        )

    def test_rejects_mismatched_detail_payload_id(self) -> None:
        documents = bokjiro_documents()
        bad_detail = raw_document(
            number=14,
            source_id="bokjiro-central-welfare-api",
            role=RawDocumentRole.DETAIL_RESPONSE,
            payload=(
                "<wantedDtl><servId>OTHER</servId></wantedDtl>"
            ).encode(),
            raw_format=RawFormat.XML,
            source_url=BOKJIRO_DETAIL_URL,
            external_id="WLF000001",
        )

        with self.assertRaises(ExtractionError):
            BokjiroExtractor().extract(
                [*documents[:-1], bad_detail]
            )


if __name__ == "__main__":
    unittest.main()
