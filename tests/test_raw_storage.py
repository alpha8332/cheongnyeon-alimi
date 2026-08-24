from __future__ import annotations

import json
import re
import tempfile
import unittest
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from collectors.raw import (
    RawDocumentRole,
    RawDocumentValidationError,
    RawFormat,
    RawPolicyDocument,
    SourceType,
)
from collectors.storage import RawDocumentStore, RawStorageError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "data/schema/raw_policy_document.schema.json"
COLLECTED_AT = datetime(2026, 7, 26, 15, 30, tzinfo=timezone.utc)
LIST_DOCUMENT_ID = "1" * 32
ITEM_DOCUMENT_ID = "2" * 32
DETAIL_DOCUMENT_ID = "3" * 32


def make_document(
    *,
    document_id: str = LIST_DOCUMENT_ID,
    document_role: RawDocumentRole = RawDocumentRole.LIST_RESPONSE,
    external_id: str | None = None,
    parent_document_id: str | None = None,
    raw_format: RawFormat = RawFormat.JSON,
    content_type: str = "application/json",
    raw_payload: bytes = b'{"result":{"items":[]}}',
) -> RawPolicyDocument:
    return RawPolicyDocument.from_bytes(
        document_id=document_id,
        source_id="test-source",
        source_type=SourceType.API,
        document_role=document_role,
        external_id=external_id,
        parent_document_id=parent_document_id,
        source_url="https://example.test/policies",
        collected_at=COLLECTED_AT,
        content_type=content_type,
        raw_format=raw_format,
        raw_payload=raw_payload,
        http_status=200,
        collector_version="test-collector/1",
    )


def schema_errors(
    instance: Any,
    schema: dict[str, Any],
    path: str = "$",
) -> list[str]:
    errors: list[str] = []
    expected_types = schema.get("type")
    if expected_types is not None:
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        if not any(
            _matches_json_type(instance, expected_type)
            for expected_type in expected_types
        ):
            return [f"{path}: type"]

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: const")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: enum")

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: minLength")
        if len(instance) > schema.get("maxLength", len(instance)):
            errors.append(f"{path}: maxLength")
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, instance) is None:
            errors.append(f"{path}: pattern")
        if schema.get("format") == "date-time":
            try:
                parsed = datetime.fromisoformat(
                    instance.replace("Z", "+00:00")
                )
                if parsed.tzinfo is None or parsed.utcoffset() is None:
                    raise ValueError
            except ValueError:
                errors.append(f"{path}: date-time")
        if schema.get("format") == "uri":
            parsed_uri = urllib.parse.urlsplit(instance)
            if not parsed_uri.scheme or not parsed_uri.netloc:
                errors.append(f"{path}: uri")

    if isinstance(instance, int) and not isinstance(instance, bool):
        if instance < schema.get("minimum", instance):
            errors.append(f"{path}: minimum")
        if instance > schema.get("maximum", instance):
            errors.append(f"{path}: maximum")

    if isinstance(instance, dict):
        required = set(schema.get("required", []))
        for missing in required - set(instance):
            errors.append(f"{path}.{missing}: required")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for extra in set(instance) - set(properties):
                errors.append(f"{path}.{extra}: additionalProperties")
        for name, value in instance.items():
            if name in properties:
                errors.extend(
                    schema_errors(value, properties[name], f"{path}.{name}")
                )

    for condition in schema.get("allOf", []):
        conditional_schema = condition.get("if")
        if conditional_schema is None or not schema_errors(
            instance,
            conditional_schema,
            path,
        ):
            errors.extend(
                schema_errors(instance, condition.get("then", {}), path)
            )
    return errors


def _matches_json_type(instance: Any, expected_type: str) -> bool:
    checks = {
        "null": instance is None,
        "object": isinstance(instance, dict),
        "array": isinstance(instance, list),
        "string": isinstance(instance, str),
        "integer": isinstance(instance, int)
        and not isinstance(instance, bool),
        "number": isinstance(instance, (int, float))
        and not isinstance(instance, bool),
        "boolean": isinstance(instance, bool),
    }
    return checks.get(expected_type, False)


class RawPolicyDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_json_xml_and_csv_examples_pass_json_schema(self) -> None:
        list_response = make_document(
            raw_payload=(
                b'{"result":{"youthPolicyList":'
                b'[{"plcyNo":"R202600001"}]}}'
            )
        )
        list_item = make_document(
            document_id=ITEM_DOCUMENT_ID,
            document_role=RawDocumentRole.LIST_ITEM,
            external_id="R202600001",
            parent_document_id=LIST_DOCUMENT_ID,
            raw_payload=b'{"plcyNo":"R202600001"}',
        )
        detail_response = make_document(
            document_id=DETAIL_DOCUMENT_ID,
            document_role=RawDocumentRole.DETAIL_RESPONSE,
            external_id="WLF000001",
            raw_format=RawFormat.XML,
            content_type="application/xml",
            raw_payload=(
                b"<wantedDtl><servId>WLF000001</servId></wantedDtl>"
            ),
        )
        csv_response = make_document(
            document_id="4" * 32,
            raw_format=RawFormat.CSV,
            content_type="text/csv; charset=cp949",
            raw_payload="연번,정책명\n1,청년정책\n".encode("cp949"),
        )

        for document in (
            list_response,
            list_item,
            detail_response,
            csv_response,
        ):
            with self.subTest(role=document.document_role.value):
                self.assertEqual(
                    [],
                    schema_errors(document.to_dict(), self.schema),
                )

    def test_python_and_json_schema_field_sets_match(self) -> None:
        self.assertEqual(
            RawPolicyDocument.FIELD_NAMES,
            frozenset(self.schema["required"]),
        )
        self.assertEqual(
            RawPolicyDocument.FIELD_NAMES,
            frozenset(self.schema["properties"]),
        )
        self.assertEqual(
            RawPolicyDocument.SCHEMA_VERSION,
            self.schema["properties"]["schema_version"]["const"],
        )

    def test_schema_rejects_invalid_role_relationship(self) -> None:
        invalid = make_document(
            document_id=ITEM_DOCUMENT_ID,
            document_role=RawDocumentRole.LIST_ITEM,
            external_id="R202600001",
            parent_document_id=LIST_DOCUMENT_ID,
        ).to_dict()
        invalid["parent_document_id"] = None

        errors = schema_errors(invalid, self.schema)

        self.assertTrue(
            any("parent_document_id: type" in error for error in errors)
        )

    def test_raw_bytes_round_trip_without_json_or_xml_reformatting(self) -> None:
        raw_payload = (
            b'{\n  "title": "\\uc815\\ucc45", '
            b'"items": [1, 2], "empty": ""\n}\n'
        )
        document = make_document(raw_payload=raw_payload)

        restored = RawPolicyDocument.from_dict(document.to_dict())

        self.assertEqual(raw_payload, restored.raw_bytes)
        self.assertEqual(document.content_hash, restored.content_hash)

    def test_same_bytes_have_same_hash_across_documents(self) -> None:
        first = make_document(raw_payload=b"same raw bytes")
        second = make_document(
            document_id=DETAIL_DOCUMENT_ID,
            document_role=RawDocumentRole.DETAIL_RESPONSE,
            external_id="same-id",
            raw_payload=b"same raw bytes",
        )

        self.assertEqual(first.content_hash, second.content_hash)

    def test_tampered_hash_or_length_is_rejected(self) -> None:
        valid = make_document().to_dict()
        cases = (
            ("content_hash", f"sha256:{'0' * 64}"),
            ("byte_length", valid["byte_length"] + 1),
        )

        for field, value in cases:
            with self.subTest(field=field):
                tampered = dict(valid)
                tampered[field] = value
                with self.assertRaises(RawDocumentValidationError):
                    RawPolicyDocument.from_dict(tampered)

    def test_source_url_rejects_query_credentials_without_exposing_them(
        self,
    ) -> None:
        with self.assertRaises(RawDocumentValidationError) as raised:
            RawPolicyDocument.from_bytes(
                document_id=LIST_DOCUMENT_ID,
                source_id="test-source",
                source_type=SourceType.API,
                document_role=RawDocumentRole.LIST_RESPONSE,
                external_id=None,
                parent_document_id=None,
                source_url=(
                    "https://example.test/policies?apiKeyNm=secret-value"
                ),
                collected_at=COLLECTED_AT,
                content_type="application/json",
                raw_format=RawFormat.JSON,
                raw_payload=b"{}",
                http_status=200,
                collector_version="test-collector/1",
            )

        self.assertNotIn("secret-value", str(raised.exception))


class RawDocumentStoreTests(unittest.TestCase):
    def test_save_and_load_round_trip_stays_below_root(self) -> None:
        document = make_document()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "runtime/raw"
            store = RawDocumentStore(root)

            stored_path = store.save(document)
            loaded = store.load(stored_path)

            self.assertTrue(stored_path.is_relative_to(store.root))
            self.assertEqual(document, loaded)
            self.assertEqual(
                (
                    "test-source/list_response/2026/07/26/"
                    f"{LIST_DOCUMENT_ID}.json"
                ),
                stored_path.relative_to(store.root).as_posix(),
            )
            self.assertEqual([], list(root.rglob("*.tmp")))

    def test_existing_document_is_not_overwritten(self) -> None:
        document = make_document()
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = RawDocumentStore(temporary_directory)
            store.save(document)

            with self.assertRaises(RawStorageError):
                store.save(document)

    def test_load_rejects_path_outside_configured_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            store_root = temporary_root / "runtime/raw"
            store_root.mkdir(parents=True)
            outside = temporary_root / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            store = RawDocumentStore(store_root)

            with self.assertRaises(RawStorageError):
                store.load(outside)

    def test_source_id_cannot_create_a_traversal_path(self) -> None:
        with self.assertRaises(RawDocumentValidationError):
            RawPolicyDocument.from_bytes(
                document_id=LIST_DOCUMENT_ID,
                source_id="../outside",
                source_type=SourceType.API,
                document_role=RawDocumentRole.LIST_RESPONSE,
                external_id=None,
                parent_document_id=None,
                source_url="https://example.test/policies",
                collected_at=COLLECTED_AT,
                content_type="application/json",
                raw_format=RawFormat.JSON,
                raw_payload=b"{}",
                http_status=200,
                collector_version="test-collector/1",
            )


if __name__ == "__main__":
    unittest.main()
