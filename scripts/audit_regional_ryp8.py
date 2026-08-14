"""Audit RYP8 field states, failed identities, and closed history."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors.regional_expansion import RegionalCheckpointStore  # noqa: E402
from collectors.regional_ryp8_audit import (  # noqa: E402
    CLOSED_HISTORY_SOURCE_IDS,
    build_regional_ryp8_audit,
)
from collectors.runtime import replay_runtime_raw  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", default="runtime/raw")
    parser.add_argument(
        "--checkpoint-root",
        default="runtime/decisions/regional-checkpoints",
    )
    parser.add_argument(
        "--review-audit",
        default="runtime/decisions/regional-review-audit.json",
    )
    parser.add_argument(
        "--output",
        default="runtime/decisions/regional-ryp8-audit.json",
    )
    parser.add_argument("--expected-outcomes", required=True)
    parser.add_argument("--max-legacy-null-slots", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checkpoint_root = Path(args.checkpoint_root)
    checkpoint_store = RegionalCheckpointStore(checkpoint_root)
    try:
        review_audit: Any = json.loads(
            Path(args.review_audit).read_text(encoding="utf-8")
        )
        expected_outcomes: Any = json.loads(args.expected_outcomes)
        checkpoints: dict[str, dict[str, Any]] = {}
        for path in sorted(checkpoint_root.glob("*.json")):
            checkpoint = checkpoint_store.load(path.stem)
            if checkpoint is not None:
                checkpoints[path.stem] = checkpoint.to_dict()
        closed_replays = {}
        for source_id in CLOSED_HISTORY_SOURCE_IDS:
            checkpoint = checkpoint_store.load(source_id)
            if checkpoint is None:
                raise ValueError("closed-history checkpoint is missing")
            replay = replay_runtime_raw(
                raw_root=args.raw_root,
                source_id=source_id,
                limit=len(checkpoint.captured_ids),
                checkpoint_root=checkpoint_root,
            )
            closed_replays[source_id] = replay.regional_decisions
        report = build_regional_ryp8_audit(
            review_audit=review_audit,
            checkpoints=checkpoints,
            closed_replays=closed_replays,
            expected_outcomes=expected_outcomes,
            max_legacy_null_slots=args.max_legacy_null_slots,
        )
        _atomic_write(Path(args.output), report)
    except Exception as error:  # noqa: BLE001 - stable CLI failure boundary
        print(
            f"regional RYP8 audit failed: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 1
    print(
        "regional RYP8 audit "
        f"data_ready={str(report['data_ready']).lower()} "
        f"legacy_null_slots={report['legacy_null_slots']} "
        f"failed={report['failure_classification']['failed_count']} "
        f"classified={report['failure_classification']['classified_count']} "
        f"blockers={','.join(report['blockers']) or 'none'} "
        f"output={args.output}"
    )
    return 0


def _atomic_write(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
