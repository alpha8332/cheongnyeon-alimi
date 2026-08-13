"""Write the RYP7 regional review reason and field coverage report."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import TextIO

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors.regional_expansion import RegionalCheckpointStore  # noqa: E402
from collectors.regional_review_audit import (  # noqa: E402
    RegionalReviewAuditInput,
    build_regional_review_audit,
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
        "--output",
        default="runtime/decisions/regional-review-audit.json",
    )
    parser.add_argument("--as-of", required=True)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    args = build_parser().parse_args(argv)
    try:
        audit_date = date.fromisoformat(args.as_of)
        checkpoint_root = Path(args.checkpoint_root)
        checkpoint_store = RegionalCheckpointStore(checkpoint_root)
        inputs: list[RegionalReviewAuditInput] = []
        for path in sorted(checkpoint_root.glob("*.json")):
            checkpoint = checkpoint_store.load(path.stem)
            if checkpoint is None:
                continue
            replay = replay_runtime_raw(
                raw_root=args.raw_root,
                source_id=checkpoint.source_id,
                limit=len(checkpoint.captured_ids),
                checkpoint_root=checkpoint_root,
            )
            inputs.append(
                RegionalReviewAuditInput(
                    source_id=checkpoint.source_id,
                    checkpoint_complete=checkpoint.complete,
                    discovered_count=len(checkpoint.discovered_ids),
                    captured_count=len(checkpoint.captured_ids),
                    checkpoint_outcomes=tuple(
                        (external_id, outcome.value)
                        for external_id, outcome in checkpoint.decisions
                    ),
                    regional_decisions=replay.regional_decisions,
                )
            )
        report = build_regional_review_audit(inputs, audit_date=audit_date)
        output = Path(args.output)
        _atomic_write(output, report)
    except Exception as exc:
        print(
            f"regional review audit failed: {type(exc).__name__}: {exc}",
            file=stderr,
        )
        return 1
    totals = report["totals"]
    print(
        "regional review audit "
        f"sources={totals['source_count']} discovered={totals['discovered']} "
        f"review={totals['review']} failed={totals['failed']} "
        f"capture_evidence_gap_sources={totals['capture_evidence_gap_sources']} "
        f"checkpoint_decision_drift={totals['checkpoint_decision_drift']} "
        f"output={output}",
        file=stdout,
    )
    return 0


def _atomic_write(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        report, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(
            descriptor, "w", encoding="utf-8", newline="\n"
        ) as stream:
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
