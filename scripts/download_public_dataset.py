"""Download a public dataset pointer and fail closed on every integrity check."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for import_root in (ROOT, ROOT / "backend", ROOT / "scripts"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from build_public_bootstrap_dataset import (  # noqa: E402
    DEFAULT_MANIFEST_SCHEMA,
    verify_release,
)
from build_public_dataset_pointer import sha256_file, validate_pointer  # noqa: E402
from collectors.validation import JsonSchemaValidator  # noqa: E402


def download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "cheongnyeon-alimi/1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise ValueError(f"download returned HTTP {response.status}")
        path.write_bytes(response.read())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pointer-url", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    try:
        args = parser.parse_args()
        args.output_dir.mkdir(parents=True, exist_ok=True)
        pointer_path = args.output_dir / "public-dataset-pointer.json"
        download(args.pointer_url, pointer_path)
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        validate_pointer(pointer)
        manifest_path = args.output_dir / "manifest.json"
        download(pointer["manifest_url"], manifest_path)
        if sha256_file(manifest_path) != pointer["manifest_sha256"]:
            raise ValueError("manifest sha256 mismatch")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        issues = JsonSchemaValidator(DEFAULT_MANIFEST_SCHEMA).schema_issues(manifest)
        if issues:
            raise ValueError("manifest schema validation failed before artifact download")
        artifact_url = urllib.parse.urljoin(
            pointer["manifest_url"], manifest["artifact"]["filename"]
        )
        download(artifact_url, args.output_dir / manifest["artifact"]["filename"])
        verified = verify_release(manifest_path)
        print(
            json.dumps(
                {
                    "status": "W6_P4_PUBLIC_DATASET_DOWNLOADED",
                    "dataset_version": verified["dataset_version"],
                    "row_count": verified["artifact"]["row_count"],
                },
                sort_keys=True,
            )
        )
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"W6_P4_PUBLIC_DATASET_DOWNLOAD_FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
