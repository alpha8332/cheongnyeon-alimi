"""Build and verify a default-deny public normalized bootstrap dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import uuid
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import create_db_engine  # noqa: E402
from app.models.policy import Policy  # noqa: E402
from app.models.policy_search import PolicyRegionRule  # noqa: E402
from collectors.normalized import (  # noqa: E402
    NormalizedProgram,
    NormalizedProgramValidationError,
)
from collectors.validation import (  # noqa: E402
    JsonSchemaValidator,
    NormalizedProgramValidator,
)


DEFAULT_CONTRACT = ROOT / "data/reference/public_policy_dataset_sources.json"
DEFAULT_CONTRACT_SCHEMA = (
    ROOT / "data/schema/public_policy_dataset_sources.schema.json"
)
DEFAULT_MANIFEST_SCHEMA = (
    ROOT / "data/schema/public_policy_dataset_manifest.schema.json"
)
DEFAULT_NORMALIZED_SCHEMA = ROOT / "data/schema/normalized_program.schema.json"
DEFAULT_OUTPUT_DIR = ROOT / "runtime/public_dataset"
MANIFEST_VERSION = "1.0.0"
EMAIL_PATTERN = re.compile(
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE
)
PERSONAL_MOBILE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?82[- .]?)?0?1(?:0|1|6|7|8|9)"
    r"[- .]?\d{3,4}[- .]?\d{4}(?!\d)"
)


class PublicDatasetError(ValueError):
    """Raised when a public dataset would violate its release contract."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", help="read-only source database URL")
    parser.add_argument("--source-contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dataset-version")
    parser.add_argument("--generated-at")
    parser.add_argument("--git-sha")
    parser.add_argument("--previous-dataset-version")
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--verify-manifest",
        type=Path,
        help="verify an existing manifest and its sibling dataset",
    )
    return parser


def _canonical_json(value: Any, *, pretty: bool) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2 if pretty else None,
            sort_keys=True,
            separators=None if pretty else (",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_errors(path: Path, value: Any) -> tuple[str, ...]:
    return tuple(
        f"{issue.path}:{issue.code}"
        for issue in JsonSchemaValidator(path).schema_issues(value)
    )


def load_source_contract(path: Path) -> dict[str, Any]:
    contract = _load_json(path)
    errors = _schema_errors(DEFAULT_CONTRACT_SCHEMA, contract)
    if errors:
        raise PublicDatasetError(
            "source contract schema validation failed: " + ", ".join(errors)
        )
    allowed_fields = frozenset(
        contract["normalized_program"]["allowed_fields"]
    )
    if allowed_fields != NormalizedProgram.FIELD_NAMES:
        raise PublicDatasetError(
            "source contract allowed_fields must exactly match "
            "NormalizedProgram 1.2.0"
        )
    source_ids = [item["source_id"] for item in contract["included_sources"]]
    if len(source_ids) != len(set(source_ids)):
        raise PublicDatasetError("source contract contains duplicate source_id")
    return contract


def _json_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _region_rule_value(rule: PolicyRegionRule) -> dict[str, Any]:
    return {
        "relation": str(rule.relation),
        "resolution_status": str(rule.resolution_status),
        "region_scheme": rule.region_scheme,
        "region_code": rule.region_code,
        "source_code": rule.source_code,
        "source_text": rule.source_text,
    }


def policy_to_normalized_program(
    policy: Policy,
    region_rules: Sequence[PolicyRegionRule] = (),
) -> dict[str, Any]:
    candidate: dict[str, Any] = {}
    for field_name in sorted(NormalizedProgram.FIELD_NAMES):
        if field_name == "region_rules":
            candidate[field_name] = [
                _region_rule_value(rule) for rule in region_rules
            ]
            continue
        candidate[field_name] = _json_value(getattr(policy, field_name))
    if candidate["schema_version"] not in {"1.1.0", "1.2.0"}:
        raise PublicDatasetError(
            f"policy {policy.source_id}/{policy.external_id} has unsupported "
            "database schema version"
        )
    candidate["schema_version"] = NormalizedProgram.SCHEMA_VERSION
    schema_issues = NormalizedProgramValidator().schema_issues(candidate)
    if schema_issues:
        codes = ",".join(issue.code for issue in schema_issues)
        raise PublicDatasetError(
            f"policy {policy.source_id}/{policy.external_id} is invalid: {codes}"
        )
    try:
        return NormalizedProgram.from_dict(candidate).to_dict()
    except NormalizedProgramValidationError as exc:
        raise PublicDatasetError(
            f"policy {policy.source_id}/{policy.external_id} is invalid: {exc}"
        ) from exc


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for child in value.values():
            yield from _walk_strings(child)
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for child in value:
            yield from _walk_strings(child)


def content_safety_counts(
    records: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> dict[str, int | bool]:
    forbidden_keys = {
        value.casefold() for value in contract["content_rules"]["forbidden_query_keys"]
    }
    email_count = 0
    personal_mobile_count = 0
    forbidden_query_key_count = 0
    institutional_contact_count = 0
    for record in records:
        contacts = (
            record.get("eligibility_summary", {}).get(
                "institutional_contacts", []
            )
        )
        institutional_contact_count += len(contacts)
        for value in _walk_strings(record):
            email_count += len(EMAIL_PATTERN.findall(value))
            personal_mobile_count += len(PERSONAL_MOBILE_PATTERN.findall(value))
            parsed = urllib.parse.urlsplit(value)
            if parsed.scheme in {"http", "https"} and parsed.netloc:
                forbidden_query_key_count += sum(
                    key.casefold() in forbidden_keys
                    for key, _ in urllib.parse.parse_qsl(
                        parsed.query, keep_blank_values=True
                    )
                )
    return {
        "raw_payload_included": False,
        "database_dump_included": False,
        "institutional_contact_count": institutional_contact_count,
        "email_match_count": email_count,
        "personal_mobile_match_count": personal_mobile_count,
        "forbidden_query_key_match_count": forbidden_query_key_count,
    }


def enforce_content_safety(counts: Mapping[str, int | bool]) -> None:
    failures = {
        key: value
        for key, value in counts.items()
        if value not in {0, False}
    }
    if failures:
        raise PublicDatasetError(f"content safety check failed: {failures}")


def select_safe_records(
    records: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], dict[str, Any]]:
    accepted: list[Mapping[str, Any]] = []
    excluded_rows = 0
    reason_counts = Counter(
        {
            "institutional_contact": 0,
            "email": 0,
            "personal_mobile": 0,
            "forbidden_query_key": 0,
        }
    )
    count_to_reason = {
        "institutional_contact_count": "institutional_contact",
        "email_match_count": "email",
        "personal_mobile_match_count": "personal_mobile",
        "forbidden_query_key_match_count": "forbidden_query_key",
    }
    for record in records:
        counts = content_safety_counts([record], contract)
        reasons = {
            count_to_reason[key]
            for key, value in counts.items()
            if key in count_to_reason and value != 0
        }
        if reasons:
            excluded_rows += 1
            reason_counts.update(reasons)
        else:
            accepted.append(record)
    if not accepted:
        raise PublicDatasetError("all candidate rows failed content safety")
    return accepted, {
        "candidate_row_count": len(records),
        "published_row_count": len(accepted),
        "excluded_row_count": excluded_rows,
        "excluded_reason_row_counts": dict(sorted(reason_counts.items())),
    }


def load_records(
    database_url: str,
    contract: Mapping[str, Any],
    *,
    limit: int | None,
) -> list[dict[str, Any]]:
    if limit is not None and limit < 1:
        raise PublicDatasetError("limit must be positive")
    allowed_source_ids = tuple(
        item["source_id"] for item in contract["included_sources"]
    )
    engine = create_db_engine(database_url, sql_echo=False)
    try:
        with Session(engine) as session:
            statement = (
                select(Policy)
                .where(
                    Policy.source_id.in_(allowed_source_ids),
                    Policy.data_quality_status.in_(("valid", "partial")),
                )
                .order_by(Policy.source_id, Policy.external_id, Policy.id)
            )
            if limit is not None:
                statement = statement.limit(limit)
            policies = list(session.scalars(statement))
            if not policies:
                raise PublicDatasetError("no allowlisted public policy was found")
            policy_ids = [policy.id for policy in policies]
            rules_by_policy: dict[int, list[PolicyRegionRule]] = defaultdict(list)
            rules = session.scalars(
                select(PolicyRegionRule)
                .where(PolicyRegionRule.policy_id.in_(policy_ids))
                .order_by(PolicyRegionRule.policy_id, PolicyRegionRule.id)
            )
            for rule in rules:
                rules_by_policy[rule.policy_id].append(rule)
            return [
                policy_to_normalized_program(
                    policy, rules_by_policy.get(policy.id, ())
                )
                for policy in policies
            ]
    finally:
        engine.dispose()


def build_manifest(
    *,
    records: Sequence[Mapping[str, Any]],
    dataset_bytes: bytes,
    dataset_filename: str,
    dataset_version: str,
    generated_at: str,
    git_sha: str,
    previous_dataset_version: str | None,
    contract: Mapping[str, Any],
    contract_path: Path,
    safety_counts: Mapping[str, int | bool],
    selection: Mapping[str, Any],
) -> dict[str, Any]:
    source_counts = Counter(record["source_id"] for record in records)
    licenses = {
        source["source_id"]: source for source in contract["included_sources"]
    }
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "dataset_version": dataset_version,
        "generated_at": generated_at,
        "git_sha": git_sha,
        "previous_dataset_version": previous_dataset_version,
        "normalized_schema": {
            "version": NormalizedProgram.SCHEMA_VERSION,
            "path": "data/schema/normalized_program.schema.json",
            "sha256": _sha256_file(DEFAULT_NORMALIZED_SCHEMA),
        },
        "source_contract": {
            "version": contract["contract_version"],
            "path": "data/reference/public_policy_dataset_sources.json",
            "sha256": _sha256_file(contract_path),
        },
        "artifact": {
            "filename": dataset_filename,
            "sha256": _sha256_bytes(dataset_bytes),
            "bytes": len(dataset_bytes),
            "row_count": len(records),
        },
        "sources": [
            {
                "source_id": source_id,
                "row_count": source_counts[source_id],
                "license_name": licenses[source_id]["license_name"],
                "license_url": licenses[source_id]["license_url"],
                "attribution": licenses[source_id]["attribution"],
            }
            for source_id in sorted(source_counts)
        ],
        "selection": dict(selection),
        "content_safety": dict(safety_counts),
        "distribution_notice": (
            "Normalized facts from allowlisted public data only. Raw payloads, "
            "database dumps, secrets and non-allowlisted sources are excluded."
        ),
    }
    errors = _schema_errors(DEFAULT_MANIFEST_SCHEMA, manifest)
    if errors:
        raise PublicDatasetError(
            "generated manifest schema validation failed: " + ", ".join(errors)
        )
    return manifest


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.{uuid.uuid4().hex}.partial")
    try:
        partial.write_bytes(payload)
        partial.replace(path)
    finally:
        partial.unlink(missing_ok=True)


def write_release(
    *,
    records: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
    contract_path: Path,
    output_dir: Path,
    dataset_version: str,
    generated_at: str,
    git_sha: str,
    previous_dataset_version: str | None = None,
) -> tuple[Path, Path, dict[str, Any]]:
    selected_records, selection = select_safe_records(records, contract)
    safety_counts = content_safety_counts(selected_records, contract)
    enforce_content_safety(safety_counts)
    dataset_filename = f"cheongnyeon-alimi-{dataset_version}.json"
    dataset_path = output_dir / dataset_filename
    manifest_path = output_dir / f"{dataset_version}.manifest.json"
    dataset_bytes = _canonical_json(list(selected_records), pretty=True)
    manifest = build_manifest(
        records=selected_records,
        dataset_bytes=dataset_bytes,
        dataset_filename=dataset_filename,
        dataset_version=dataset_version,
        generated_at=generated_at,
        git_sha=git_sha,
        previous_dataset_version=previous_dataset_version,
        contract=contract,
        contract_path=contract_path,
        safety_counts=safety_counts,
        selection=selection,
    )
    _atomic_write(dataset_path, dataset_bytes)
    _atomic_write(manifest_path, _canonical_json(manifest, pretty=True))
    return dataset_path, manifest_path, manifest


def verify_release(
    manifest_path: Path,
    *,
    contract_path: Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_source_contract(contract_path)
    manifest = _load_json(manifest_path)
    errors = _schema_errors(DEFAULT_MANIFEST_SCHEMA, manifest)
    if errors:
        raise PublicDatasetError(
            "manifest schema validation failed: " + ", ".join(errors)
        )
    dataset_path = manifest_path.parent / manifest["artifact"]["filename"]
    if not dataset_path.is_file():
        raise PublicDatasetError("dataset artifact is missing")
    if _sha256_file(dataset_path) != manifest["artifact"]["sha256"]:
        raise PublicDatasetError("dataset sha256 mismatch")
    if dataset_path.stat().st_size != manifest["artifact"]["bytes"]:
        raise PublicDatasetError("dataset byte count mismatch")
    if _sha256_file(contract_path) != manifest["source_contract"]["sha256"]:
        raise PublicDatasetError("source contract sha256 mismatch")
    if (
        _sha256_file(DEFAULT_NORMALIZED_SCHEMA)
        != manifest["normalized_schema"]["sha256"]
    ):
        raise PublicDatasetError("normalized schema sha256 mismatch")
    records = _load_json(dataset_path)
    if not isinstance(records, list):
        raise PublicDatasetError("dataset must be a JSON array")
    if len(records) != manifest["artifact"]["row_count"]:
        raise PublicDatasetError("dataset row count mismatch")
    allowed_source_ids = {
        source["source_id"] for source in contract["included_sources"]
    }
    validator = NormalizedProgramValidator()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise PublicDatasetError(f"dataset row {index} is not an object")
        if record.get("source_id") not in allowed_source_ids:
            raise PublicDatasetError(f"dataset row {index} source is not allowed")
        if validator.schema_issues(record):
            raise PublicDatasetError(f"dataset row {index} is invalid")
        try:
            NormalizedProgram.from_dict(dict(record))
        except NormalizedProgramValidationError as exc:
            raise PublicDatasetError(
                f"dataset row {index} is invalid"
            ) from exc
    safety_counts = content_safety_counts(records, contract)
    enforce_content_safety(safety_counts)
    if dict(safety_counts) != manifest["content_safety"]:
        raise PublicDatasetError("content safety manifest mismatch")
    return manifest


def _require_build_args(args: argparse.Namespace) -> None:
    missing = [
        name
        for name in ("database_url", "dataset_version", "generated_at", "git_sha")
        if not getattr(args, name)
    ]
    if missing:
        options = ", ".join(
            f"--{name.replace('_', '-')}" for name in missing
        )
        raise PublicDatasetError(
            "build mode requires: " + options
        )


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.verify_manifest is not None:
            manifest = verify_release(
                args.verify_manifest, contract_path=args.source_contract
            )
            print(
                json.dumps(
                    {
                        "status": "W6_P0_PUBLIC_DATASET_VERIFIED",
                        "dataset_version": manifest["dataset_version"],
                        "row_count": manifest["artifact"]["row_count"],
                        "sha256": manifest["artifact"]["sha256"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        _require_build_args(args)
        contract = load_source_contract(args.source_contract)
        records = load_records(
            args.database_url, contract, limit=args.limit
        )
        dataset_path, manifest_path, manifest = write_release(
            records=records,
            contract=contract,
            contract_path=args.source_contract,
            output_dir=args.output_dir,
            dataset_version=args.dataset_version,
            generated_at=args.generated_at,
            git_sha=args.git_sha,
            previous_dataset_version=args.previous_dataset_version,
        )
        print(
            json.dumps(
                {
                    "status": "W6_P0_PUBLIC_DATASET_CREATED",
                    "dataset_path": str(dataset_path),
                    "manifest_path": str(manifest_path),
                    "row_count": manifest["artifact"]["row_count"],
                    "sha256": manifest["artifact"]["sha256"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except (OSError, ValueError) as exc:
        print(f"W6_P0_PUBLIC_DATASET_FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
