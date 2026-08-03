"""Build deterministic policy-region seeds from the locked official snapshot."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "data" / "reference" / "administrative_regions"
REGION_OUTPUT = ROOT / "data" / "seeds" / "administrative_regions.json"
ALIAS_OUTPUT = ROOT / "data" / "seeds" / "administrative_region_aliases.json"
ROOT_CODE = "0000000000"
PREFIX5_SCHEME = "kr-bjd-prefix5"
CURATED_ALIASES = {
    ROOT_CODE: ("전국", "대한민국"),
    "4400000000": ("충남",),
    "4413000000": ("천안",),
}


class RegionBuildError(RuntimeError):
    """Raised when the locked reference cannot produce a safe seed."""


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _read_reference(snapshot_date: str) -> tuple[dict[str, Any], list[dict[str, str]]]:
    compact = snapshot_date.replace("-", "")
    manifest_path = REFERENCE_DIR / f"legal_dong_codes_{compact}.manifest.json"
    csv_path = REFERENCE_DIR / f"legal_dong_codes_{compact}.csv.gz"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with gzip.open(csv_path, "rb") as source:
        csv_bytes = source.read()
    digest = hashlib.sha256(csv_bytes).hexdigest()
    if digest != manifest["normalized_csv_sha256"]:
        raise RegionBuildError("reference snapshot checksum mismatch")
    rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8"))))
    if len(rows) != manifest["record_count"]:
        raise RegionBuildError("reference snapshot count mismatch")
    if len({row["code"] for row in rows}) != len(rows):
        raise RegionBuildError("reference snapshot contains duplicate codes")
    return manifest, rows


def _region_level(code: str) -> str:
    if code == ROOT_CODE:
        return "country"
    if code.endswith("00000000"):
        return "province"
    return "district"


def _build_regions(
    manifest: dict[str, Any], rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    selected = [row for row in rows if row["code"].endswith("00000")]
    by_code = {row["code"]: row for row in selected}
    active_by_full_name: dict[tuple[str, str], list[str]] = {}
    for row in selected:
        if row["status"] == "active":
            key = (row["parent_code"], row["full_name"])
            active_by_full_name.setdefault(key, []).append(row["code"])

    regions: list[dict[str, Any]] = [
        {
            "aggregate_parent_code": None,
            "code": ROOT_CODE,
            "external_codes": {},
            "full_name": "대한민국",
            "level": "country",
            "name": "대한민국",
            "parent_code": None,
            "scheme": manifest["scheme"],
            "source_parent_code": None,
            "status": "active",
            "valid_from": None,
            "valid_to": None,
        }
    ]
    for row in selected:
        source_parent = row["parent_code"] or None
        parent = source_parent
        if parent == ROOT_CODE or parent in by_code:
            pass
        elif row["status"] == "retired" and parent is None:
            pass
        else:
            raise RegionBuildError(f"orphan official parent for {row['code']}")

        aggregate_parent = None
        parts = row["full_name"].split()
        if row["status"] == "active" and len(parts) >= 3:
            candidates = active_by_full_name.get(
                (source_parent or "", " ".join(parts[:-1])), []
            )
            if len(candidates) > 1:
                raise RegionBuildError(
                    f"ambiguous aggregate parent for {row['code']}"
                )
            if candidates:
                aggregate_parent = candidates[0]

        regions.append(
            {
                "aggregate_parent_code": aggregate_parent,
                "code": row["code"],
                "external_codes": {
                    PREFIX5_SCHEME: row["code"][:5]
                },
                "full_name": row["full_name"],
                "level": _region_level(row["code"]),
                "name": row["lowest_name"],
                "parent_code": parent,
                "scheme": manifest["scheme"],
                "source_parent_code": source_parent,
                "status": row["status"],
                "valid_from": row["valid_from"] or None,
                "valid_to": row["valid_to"] or None,
            }
        )
    return sorted(regions, key=lambda item: item["code"])


def _build_aliases(
    scheme: str, regions: list[dict[str, Any]]
) -> list[dict[str, str]]:
    aliases: set[tuple[str, str, str]] = set()
    for region in regions:
        aliases.add((region["full_name"], region["code"], "official_full"))
        aliases.add((region["name"], region["code"], "official_short"))
    for region_code, values in CURATED_ALIASES.items():
        if not any(region["code"] == region_code for region in regions):
            raise RegionBuildError(f"curated alias target missing: {region_code}")
        for value in values:
            aliases.add((value, region_code, "curated"))
    return [
        {
            "alias": alias,
            "kind": kind,
            "region_code": region_code,
            "scheme": scheme,
        }
        for alias, region_code, kind in sorted(aliases)
    ]


def _write_or_check(path: Path, payload: bytes, *, check: bool) -> None:
    if check:
        if not path.exists() or path.read_bytes() != payload:
            raise RegionBuildError(f"generated seed is stale: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-date", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    try:
        manifest, source_rows = _read_reference(args.snapshot_date)
        regions = _build_regions(manifest, source_rows)
        aliases = _build_aliases(manifest["scheme"], regions)
        common = {
            "schema_version": "1.0.0",
            "scheme": manifest["scheme"],
            "snapshot_date": manifest["snapshot_date"],
            "source_page_url": manifest["source_page_url"],
            "license_name": manifest["license_name"],
            "license_url": manifest["license_url"],
        }
        region_doc = {**common, "regions": regions}
        alias_doc = {**common, "aliases": aliases}
        _write_or_check(REGION_OUTPUT, _json_bytes(region_doc), check=args.check)
        _write_or_check(ALIAS_OUTPUT, _json_bytes(alias_doc), check=args.check)
    except (OSError, KeyError, ValueError, RegionBuildError) as exc:
        print(f"region seed build failed: {exc}", file=sys.stderr)
        return 1

    action = "Verified" if args.check else "Wrote"
    print(f"{action} {len(regions)} regions and {len(aliases)} aliases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
