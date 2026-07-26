"""Lossless Raw document model shared by source collectors."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import urllib.parse
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar

from collectors.registry import SOURCE_ID_PATTERN


DOCUMENT_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
CONTENT_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class RawDocumentValidationError(ValueError):
    """A Raw document violates the implemented contract."""


class SourceType(str, Enum):
    API = "api"
    WEB = "web"


class RawDocumentRole(str, Enum):
    LIST_RESPONSE = "list_response"
    LIST_ITEM = "list_item"
    DETAIL_RESPONSE = "detail_response"


class RawFormat(str, Enum):
    JSON = "json"
    XML = "xml"
    HTML = "html"


@dataclass(frozen=True, slots=True)
class RawPolicyDocument:
    """Raw bytes plus the metadata needed to replay their interpretation."""

    SCHEMA_VERSION: ClassVar[str] = "1.0.0"
    FIELD_NAMES: ClassVar[frozenset[str]] = frozenset(
        {
            "schema_version",
            "document_id",
            "source_id",
            "source_type",
            "document_role",
            "external_id",
            "parent_document_id",
            "source_url",
            "collected_at",
            "content_type",
            "raw_format",
            "raw_payload_base64",
            "content_hash",
            "byte_length",
            "http_status",
            "collector_version",
        }
    )

    document_id: str
    source_id: str
    source_type: SourceType
    document_role: RawDocumentRole
    external_id: str | None
    parent_document_id: str | None
    source_url: str
    collected_at: datetime
    content_type: str
    raw_format: RawFormat
    raw_payload_base64: str
    content_hash: str
    byte_length: int
    http_status: int
    collector_version: str

    def __post_init__(self) -> None:
        self._validate_metadata()
        payload = self._decode_payload()
        if len(payload) != self.byte_length:
            raise RawDocumentValidationError(
                "byte_length does not match the Raw payload"
            )
        if content_hash(payload) != self.content_hash:
            raise RawDocumentValidationError(
                "content_hash does not match the Raw payload"
            )

    @classmethod
    def from_bytes(
        cls,
        *,
        source_id: str,
        source_type: SourceType,
        document_role: RawDocumentRole,
        external_id: str | None,
        parent_document_id: str | None,
        source_url: str,
        collected_at: datetime,
        content_type: str,
        raw_format: RawFormat,
        raw_payload: bytes,
        http_status: int,
        collector_version: str,
        document_id: str | None = None,
    ) -> RawPolicyDocument:
        if not isinstance(raw_payload, bytes):
            raise RawDocumentValidationError("raw_payload must be bytes")
        return cls(
            document_id=document_id or uuid.uuid4().hex,
            source_id=source_id,
            source_type=source_type,
            document_role=document_role,
            external_id=external_id,
            parent_document_id=parent_document_id,
            source_url=source_url,
            collected_at=collected_at,
            content_type=content_type,
            raw_format=raw_format,
            raw_payload_base64=base64.b64encode(raw_payload).decode("ascii"),
            content_hash=content_hash(raw_payload),
            byte_length=len(raw_payload),
            http_status=http_status,
            collector_version=collector_version,
        )

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> RawPolicyDocument:
        if set(value) != cls.FIELD_NAMES:
            raise RawDocumentValidationError(
                "Raw document fields do not match schema version 1.0.0"
            )
        if value.get("schema_version") != cls.SCHEMA_VERSION:
            raise RawDocumentValidationError(
                "unsupported Raw document schema version"
            )
        try:
            collected_at_value = value["collected_at"]
            if not isinstance(collected_at_value, str):
                raise TypeError
            collected_at = datetime.fromisoformat(
                collected_at_value.replace("Z", "+00:00")
            )
            return cls(
                document_id=value["document_id"],
                source_id=value["source_id"],
                source_type=SourceType(value["source_type"]),
                document_role=RawDocumentRole(value["document_role"]),
                external_id=value["external_id"],
                parent_document_id=value["parent_document_id"],
                source_url=value["source_url"],
                collected_at=collected_at,
                content_type=value["content_type"],
                raw_format=RawFormat(value["raw_format"]),
                raw_payload_base64=value["raw_payload_base64"],
                content_hash=value["content_hash"],
                byte_length=value["byte_length"],
                http_status=value["http_status"],
                collector_version=value["collector_version"],
            )
        except (KeyError, TypeError, ValueError):
            raise RawDocumentValidationError(
                "Raw document contains an invalid field value"
            ) from None

    @property
    def raw_bytes(self) -> bytes:
        return self._decode_payload()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "document_id": self.document_id,
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "document_role": self.document_role.value,
            "external_id": self.external_id,
            "parent_document_id": self.parent_document_id,
            "source_url": self.source_url,
            "collected_at": self.collected_at.isoformat(),
            "content_type": self.content_type,
            "raw_format": self.raw_format.value,
            "raw_payload_base64": self.raw_payload_base64,
            "content_hash": self.content_hash,
            "byte_length": self.byte_length,
            "http_status": self.http_status,
            "collector_version": self.collector_version,
        }

    def to_json_bytes(self) -> bytes:
        return (
            json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")

    def _validate_metadata(self) -> None:
        if (
            not isinstance(self.document_id, str)
            or not DOCUMENT_ID_PATTERN.fullmatch(self.document_id)
        ):
            raise RawDocumentValidationError("invalid document_id")
        if (
            not isinstance(self.source_id, str)
            or not SOURCE_ID_PATTERN.fullmatch(self.source_id)
        ):
            raise RawDocumentValidationError("invalid source_id")
        if not isinstance(self.source_type, SourceType):
            raise RawDocumentValidationError("invalid source_type")
        if not isinstance(self.document_role, RawDocumentRole):
            raise RawDocumentValidationError("invalid document_role")
        self._validate_relationship()
        self._validate_source_url()
        if (
            not isinstance(self.collected_at, datetime)
            or self.collected_at.tzinfo is None
            or self.collected_at.utcoffset() is None
        ):
            raise RawDocumentValidationError(
                "collected_at must include a timezone"
            )
        if (
            not isinstance(self.content_type, str)
            or not self.content_type
            or len(self.content_type) > 255
            or any(character in self.content_type for character in "\r\n")
        ):
            raise RawDocumentValidationError("invalid content_type")
        if not isinstance(self.raw_format, RawFormat):
            raise RawDocumentValidationError("invalid raw_format")
        if (
            not isinstance(self.content_hash, str)
            or not CONTENT_HASH_PATTERN.fullmatch(self.content_hash)
        ):
            raise RawDocumentValidationError("invalid content_hash")
        if (
            not isinstance(self.byte_length, int)
            or isinstance(self.byte_length, bool)
            or self.byte_length < 0
        ):
            raise RawDocumentValidationError("invalid byte_length")
        if (
            not isinstance(self.http_status, int)
            or isinstance(self.http_status, bool)
            or not 200 <= self.http_status <= 299
        ):
            raise RawDocumentValidationError(
                "Raw documents require a successful HTTP status"
            )
        if (
            not isinstance(self.collector_version, str)
            or not self.collector_version
            or len(self.collector_version) > 128
            or any(
                character in self.collector_version for character in "\r\n"
            )
        ):
            raise RawDocumentValidationError("invalid collector_version")

    def _validate_relationship(self) -> None:
        external_id_valid = (
            isinstance(self.external_id, str)
            and bool(self.external_id)
            and not any(
                character.isspace() for character in self.external_id
            )
            and len(self.external_id) <= 512
        )
        parent_id_valid = (
            isinstance(self.parent_document_id, str)
            and bool(
                DOCUMENT_ID_PATTERN.fullmatch(self.parent_document_id)
            )
        )
        if self.document_role is RawDocumentRole.LIST_RESPONSE:
            if self.external_id is not None or self.parent_document_id is not None:
                raise RawDocumentValidationError(
                    "list_response cannot have relationship IDs"
                )
        elif self.document_role is RawDocumentRole.LIST_ITEM:
            if not external_id_valid or not parent_id_valid:
                raise RawDocumentValidationError(
                    "list_item requires external_id and parent_document_id"
                )
        elif self.document_role is RawDocumentRole.DETAIL_RESPONSE:
            if not external_id_valid or self.parent_document_id is not None:
                raise RawDocumentValidationError(
                    "detail_response requires only external_id"
                )

    def _validate_source_url(self) -> None:
        if not isinstance(self.source_url, str):
            raise RawDocumentValidationError("invalid source_url")
        try:
            parsed = urllib.parse.urlsplit(self.source_url)
            port = parsed.port
        except ValueError:
            raise RawDocumentValidationError("invalid source_url") from None
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or any(character.isspace() for character in self.source_url)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or (port is not None and not 1 <= port <= 65535)
        ):
            raise RawDocumentValidationError(
                "source_url must be an HTTPS URL without query or credentials"
            )

    def _decode_payload(self) -> bytes:
        if not isinstance(self.raw_payload_base64, str):
            raise RawDocumentValidationError(
                "raw_payload_base64 must be a string"
            )
        try:
            return base64.b64decode(
                self.raw_payload_base64,
                validate=True,
            )
        except (binascii.Error, ValueError):
            raise RawDocumentValidationError(
                "raw_payload_base64 is invalid"
            ) from None


def content_hash(raw_payload: bytes) -> str:
    if not isinstance(raw_payload, bytes):
        raise RawDocumentValidationError("raw_payload must be bytes")
    return f"sha256:{hashlib.sha256(raw_payload).hexdigest()}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
