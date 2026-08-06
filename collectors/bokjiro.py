"""Bokjiro central-government welfare service API collector."""

from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ElementTree
from collections.abc import Callable
from datetime import datetime

from collectors.base import CollectionOptions, CollectionResult
from collectors.config import http_config_from_environment, required_secret
from collectors.errors import (
    AuthenticationError,
    ClientResponseError,
    EmptyResponseError,
    RateLimitError,
)
from collectors.http import HttpClient, TransportResponse
from collectors.raw import (
    RawDocumentRole,
    RawFormat,
    RawPolicyDocument,
    SourceType,
    utc_now,
)
from collectors.source_common import (
    ensure_secret_not_in_payload,
    query_with_secret,
    response_content_type,
    safe_parse_error,
)
from collectors.storage import RawDocumentStore


SOURCE_ID = "bokjiro-central-welfare-api"
LIST_URL = (
    "https://apis.data.go.kr/B554287/"
    "NationalWelfareInformationsV001/NationalWelfarelistV001"
)
DETAIL_URL = (
    "https://apis.data.go.kr/B554287/"
    "NationalWelfareInformationsV001/NationalWelfaredetailedV001"
)
COLLECTOR_VERSION = "bokjiro-central-welfare-api/1.0"


class BokjiroCollector:
    source_id = SOURCE_ID

    def __init__(
        self,
        *,
        api_key: str,
        http_client: HttpClient | None = None,
        store: RawDocumentStore | None = None,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        if not api_key:
            raise ValueError("api_key cannot be empty")
        self._api_key = urllib.parse.unquote(api_key)
        self._http_client = http_client or HttpClient()
        self._store = store or RawDocumentStore()
        self._now = now

    def collect(
        self,
        options: CollectionOptions | None = None,
    ) -> CollectionResult:
        selected = options or CollectionOptions()
        list_response = self._http_client.get(
            source_id=self.source_id,
            url=LIST_URL,
            query=query_with_secret(
                "serviceKey",
                self._api_key,
                {
                    "callTp": "L",
                    "pageNo": selected.page,
                    "numOfRows": selected.limit,
                    "srchKeyCode": "003",
                },
            ),
        )
        ensure_secret_not_in_payload(
            source_id=self.source_id,
            source_url=LIST_URL,
            response=list_response,
            secret=self._api_key,
        )
        list_root = self._parse_success_xml(list_response, LIST_URL)
        service_elements = self._service_elements(
            list_root,
            list_response,
        )[: selected.limit]
        total_count = self._total_count(list_root, list_response)
        collected_at = self._now()
        list_document = RawPolicyDocument.from_bytes(
            source_id=self.source_id,
            source_type=SourceType.API,
            document_role=RawDocumentRole.LIST_RESPONSE,
            external_id=None,
            parent_document_id=None,
            source_url=LIST_URL,
            collected_at=collected_at,
            content_type=response_content_type(
                list_response,
                default="application/xml",
            ),
            raw_format=RawFormat.XML,
            raw_payload=list_response.body,
            http_status=list_response.status,
            collector_version=COLLECTOR_VERSION,
        )
        stored_paths = [self._store.save(list_document)]
        service_ids: list[str] = []
        for element, service_id in service_elements:
            item_document = RawPolicyDocument.from_bytes(
                source_id=self.source_id,
                source_type=SourceType.API,
                document_role=RawDocumentRole.LIST_ITEM,
                external_id=service_id,
                parent_document_id=list_document.document_id,
                source_url=LIST_URL,
                collected_at=collected_at,
                content_type="application/xml",
                raw_format=RawFormat.XML,
                raw_payload=ElementTree.tostring(
                    element,
                    encoding="utf-8",
                ),
                http_status=list_response.status,
                collector_version=COLLECTOR_VERSION,
            )
            stored_paths.append(self._store.save(item_document))
            if service_id not in service_ids:
                service_ids.append(service_id)

        detail_count = min(selected.detail_limit, len(service_ids))
        detail_document_ids: list[str] = []
        for service_id in service_ids[:detail_count]:
            detail_response = self._http_client.get(
                source_id=self.source_id,
                url=DETAIL_URL,
                query=query_with_secret(
                    "serviceKey",
                    self._api_key,
                    {"callTp": "D", "servId": service_id},
                ),
            )
            ensure_secret_not_in_payload(
                source_id=self.source_id,
                source_url=DETAIL_URL,
                response=detail_response,
                secret=self._api_key,
            )
            detail_root = self._parse_success_xml(
                detail_response,
                DETAIL_URL,
            )
            returned_service_id = _first_text(detail_root, "servId")
            if returned_service_id != service_id:
                raise safe_parse_error(
                    source_id=self.source_id,
                    source_url=DETAIL_URL,
                    response=detail_response,
                    reason="detail response external ID does not match request",
                )
            detail_document = RawPolicyDocument.from_bytes(
                source_id=self.source_id,
                source_type=SourceType.API,
                document_role=RawDocumentRole.DETAIL_RESPONSE,
                external_id=service_id,
                parent_document_id=None,
                source_url=DETAIL_URL,
                collected_at=self._now(),
                content_type=response_content_type(
                    detail_response,
                    default="application/xml",
                ),
                raw_format=RawFormat.XML,
                raw_payload=detail_response.body,
                http_status=detail_response.status,
                collector_version=COLLECTOR_VERSION,
            )
            stored_paths.append(self._store.save(detail_document))
            detail_document_ids.append(detail_document.document_id)

        return CollectionResult(
            source_id=self.source_id,
            request_count=1 + detail_count,
            item_count=len(service_elements),
            detail_count=detail_count,
            stored_paths=tuple(stored_paths),
            page=selected.page,
            page_size=selected.limit,
            total_count=total_count,
            external_ids=tuple(service_ids),
            list_response_document_id=list_document.document_id,
            detail_document_ids=tuple(detail_document_ids),
        )

    def _total_count(
        self,
        root: ElementTree.Element,
        response: TransportResponse,
    ) -> int:
        try:
            total_count = int(_first_text(root, "totalCount") or "")
        except ValueError:
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=LIST_URL,
                response=response,
                reason="response has invalid total count",
            ) from None
        if total_count < 0:
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=LIST_URL,
                response=response,
                reason="response has invalid total count",
            )
        return total_count

    def _parse_success_xml(
        self,
        response: TransportResponse,
        source_url: str,
    ) -> ElementTree.Element:
        try:
            root = ElementTree.fromstring(response.body)
        except (ElementTree.ParseError, UnicodeDecodeError):
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=source_url,
                response=response,
                reason="response is not valid XML",
            ) from None
        result_code = _first_text(root, "resultCode")
        if result_code != "0":
            self._raise_application_error(
                result_code or "",
                response,
                source_url,
            )
        return root

    def _service_elements(
        self,
        root: ElementTree.Element,
        response: TransportResponse,
    ) -> list[tuple[ElementTree.Element, str]]:
        results: list[tuple[ElementTree.Element, str]] = []
        for element in root.iter():
            service_id = _direct_child_text(element, "servId")
            if service_id is not None:
                results.append((element, service_id))
        if not results:
            raise EmptyResponseError(
                source_id=self.source_id,
                safe_url=LIST_URL,
                reason="source returned an empty service list",
                status=response.status,
            )
        return results

    def _raise_application_error(
        self,
        result_code: str,
        response: TransportResponse,
        source_url: str,
    ) -> None:
        error_type: type[
            AuthenticationError | RateLimitError | ClientResponseError
        ]
        if result_code in {"30", "31"}:
            error_type = AuthenticationError
            reason = "source rejected application authentication"
        elif result_code == "22":
            error_type = RateLimitError
            reason = "source application rate limit was reached"
        else:
            error_type = ClientResponseError
            reason = "source returned an application error"
        raise error_type(
            source_id=self.source_id,
            safe_url=source_url,
            reason=reason,
            status=response.status,
        )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _direct_child_text(
    element: ElementTree.Element,
    name: str,
) -> str | None:
    for child in element:
        if _local_name(child.tag) == name and child.text:
            value = child.text.strip()
            return value or None
    return None


def _first_text(
    root: ElementTree.Element,
    name: str,
) -> str | None:
    for element in root.iter():
        if _local_name(element.tag) == name and element.text:
            value = element.text.strip()
            return value or None
    return None


def create_bokjiro_collector() -> BokjiroCollector:
    return BokjiroCollector(
        api_key=required_secret("BOKJIRO_API_KEY"),
        http_client=HttpClient(config=http_config_from_environment()),
    )
