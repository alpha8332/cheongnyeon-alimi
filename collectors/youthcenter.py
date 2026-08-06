"""Ontong Youth policy API collector."""

from __future__ import annotations

import json
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


SOURCE_ID = "youthcenter-api"
SOURCE_URL = "https://www.youthcenter.go.kr/go/ythip/getPlcy"
COLLECTOR_VERSION = "youthcenter-api/1.0"


class YouthCenterCollector:
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
        self._api_key = api_key
        self._http_client = http_client or HttpClient()
        self._store = store or RawDocumentStore()
        self._now = now

    def collect(
        self,
        options: CollectionOptions | None = None,
    ) -> CollectionResult:
        selected = options or CollectionOptions()
        response = self._http_client.get(
            source_id=self.source_id,
            url=SOURCE_URL,
            query=query_with_secret(
                "apiKeyNm",
                self._api_key,
                {
                    "pageNum": selected.page,
                    "pageSize": selected.limit,
                    "rtnType": "json",
                },
            ),
        )
        ensure_secret_not_in_payload(
            source_id=self.source_id,
            source_url=SOURCE_URL,
            response=response,
            secret=self._api_key,
        )
        parsed_items, total_count = self._parse_items(response)
        items = parsed_items[: selected.limit]
        prepared_items: list[tuple[str, bytes]] = []
        for item in items:
            external_id = item.get("plcyNo")
            if (
                not isinstance(external_id, str)
                or not external_id
                or any(
                    character.isspace() for character in external_id
                )
            ):
                raise safe_parse_error(
                    source_id=self.source_id,
                    source_url=SOURCE_URL,
                    response=response,
                    reason="policy item is missing a valid external ID",
                )
            prepared_items.append(
                (
                    external_id,
                    json.dumps(
                        item,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ).encode("utf-8"),
                )
            )
        collected_at = self._now()
        content_type = response_content_type(
            response,
            default="application/json",
        )
        list_document = RawPolicyDocument.from_bytes(
            source_id=self.source_id,
            source_type=SourceType.API,
            document_role=RawDocumentRole.LIST_RESPONSE,
            external_id=None,
            parent_document_id=None,
            source_url=SOURCE_URL,
            collected_at=collected_at,
            content_type=content_type,
            raw_format=RawFormat.JSON,
            raw_payload=response.body,
            http_status=response.status,
            collector_version=COLLECTOR_VERSION,
        )
        stored_paths = [self._store.save(list_document)]
        for external_id, item_payload in prepared_items:
            item_document = RawPolicyDocument.from_bytes(
                source_id=self.source_id,
                source_type=SourceType.API,
                document_role=RawDocumentRole.LIST_ITEM,
                external_id=external_id,
                parent_document_id=list_document.document_id,
                source_url=SOURCE_URL,
                collected_at=collected_at,
                content_type="application/json",
                raw_format=RawFormat.JSON,
                raw_payload=item_payload,
                http_status=response.status,
                collector_version=COLLECTOR_VERSION,
            )
            stored_paths.append(self._store.save(item_document))

        return CollectionResult(
            source_id=self.source_id,
            request_count=1,
            item_count=len(items),
            detail_count=0,
            stored_paths=tuple(stored_paths),
            page=selected.page,
            page_size=selected.limit,
            total_count=total_count,
            external_ids=tuple(
                external_id for external_id, _ in prepared_items
            ),
            list_response_document_id=list_document.document_id,
        )

    def _parse_items(
        self,
        response: TransportResponse,
    ) -> tuple[list[dict[str, object]], int]:
        try:
            payload = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=SOURCE_URL,
                response=response,
                reason="response is not valid JSON",
            ) from None
        if not isinstance(payload, dict):
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=SOURCE_URL,
                response=response,
                reason="response JSON root must be an object",
            )

        result_code = str(payload.get("resultCode", ""))
        if result_code != "200":
            self._raise_application_error(result_code, response)
        result = payload.get("result")
        if not isinstance(result, dict):
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=SOURCE_URL,
                response=response,
                reason="response is missing the result object",
            )
        raw_items = result.get("youthPolicyList")
        if not isinstance(raw_items, list):
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=SOURCE_URL,
                response=response,
                reason="response is missing the policy list",
            )
        if not raw_items:
            raise EmptyResponseError(
                source_id=self.source_id,
                safe_url=SOURCE_URL,
                reason="source returned an empty policy list",
                status=response.status,
            )
        if not all(isinstance(item, dict) for item in raw_items):
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=SOURCE_URL,
                response=response,
                reason="policy list contains a non-object item",
            )
        pagination = result.get("pagging")
        if not isinstance(pagination, dict):
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=SOURCE_URL,
                response=response,
                reason="response is missing pagination metadata",
            )
        try:
            total_count = int(pagination.get("totCount"))
        except (TypeError, ValueError):
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=SOURCE_URL,
                response=response,
                reason="response has invalid total count",
            ) from None
        if total_count < len(raw_items):
            raise safe_parse_error(
                source_id=self.source_id,
                source_url=SOURCE_URL,
                response=response,
                reason="response total count is smaller than item count",
            )
        return raw_items, total_count

    def _raise_application_error(
        self,
        result_code: str,
        response: TransportResponse,
    ) -> None:
        error_type: type[
            AuthenticationError | RateLimitError | ClientResponseError
        ]
        if result_code in {"401", "403"}:
            error_type = AuthenticationError
            reason = "source rejected application authentication"
        elif result_code == "429":
            error_type = RateLimitError
            reason = "source application rate limit was reached"
        else:
            error_type = ClientResponseError
            reason = "source returned an application error"
        raise error_type(
            source_id=self.source_id,
            safe_url=SOURCE_URL,
            reason=reason,
            status=response.status,
        )


def create_youthcenter_collector() -> YouthCenterCollector:
    return YouthCenterCollector(
        api_key=required_secret("YOUTHCENTER_API_KEY"),
        http_client=HttpClient(config=http_config_from_environment()),
    )
