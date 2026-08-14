"""Write the read-only RYP9 checkpoint redecision audit."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for import_root in (ROOT, BACKEND_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from app.core.config import settings  # noqa: E402
from app.core.database import create_db_engine, create_session_factory  # noqa: E402
from app.services.aggregator_baseline import load_aggregator_baseline  # noqa: E402
from collectors.regional_expansion import RegionalCheckpointStore  # noqa: E402
from collectors.regional_ryp9_audit import build_regional_ryp9_audit  # noqa: E402
from collectors.runtime import replay_runtime_raw  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("runtime/raw"))
    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        default=Path("runtime/decisions/regional-checkpoints"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runtime/decisions/regional-ryp9-audit.json"),
    )
    args = parser.parse_args()
    engine = create_db_engine(settings.DATABASE_URL, sql_echo=False)
    session = create_session_factory(engine)()
    try:
        baseline = load_aggregator_baseline(session, raw_root=args.raw_root)
        session.rollback()
        store = RegionalCheckpointStore(args.checkpoint_root)
        checkpoints = {}
        replays = {}
        for path in sorted(args.checkpoint_root.glob("*.json")):
            checkpoint = store.load(path.stem)
            if checkpoint is None:
                continue
            checkpoints[path.stem] = checkpoint.to_dict()
            replay = replay_runtime_raw(
                raw_root=args.raw_root,
                source_id=path.stem,
                limit=len(checkpoint.captured_ids),
                duplicate_baseline=baseline,
                checkpoint_root=args.checkpoint_root,
            )
            replays[path.stem] = {
                "regional_decisions": list(replay.regional_decisions),
                "duplicate_decisions": list(replay.duplicate_decisions),
            }
        report = build_regional_ryp9_audit(
            checkpoints=checkpoints,
            replays=replays,
        )
        _atomic_write(args.output, report)
    except Exception as exc:  # noqa: BLE001 - CLI reports a stable error boundary
        print(f"regional RYP9 audit failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()
        engine.dispose()
    print(
        "regional RYP9 audit "
        f"transitions={report['transition_count']} "
        f"ready_for_redecision={str(report['ready_for_redecision']).lower()} "
        f"blockers={','.join(report['blockers']) or 'none'} "
        f"output={args.output}"
    )
    return 0


def _atomic_write(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
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
