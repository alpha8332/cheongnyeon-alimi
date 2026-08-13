"""Loopback-only ingest endpoint for actual RYP6 Browser observations."""

from __future__ import annotations

import argparse
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors.regional_expansion import (  # noqa: E402
    RegionalBatchCheckpoint,
    RegionalBrowserCaptureStore,
    RegionalCheckpointStore,
)
from collectors.storage import RawDocumentStore  # noqa: E402


MAX_BODY_BYTES = 2_000_000


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--token", required=True)
    parser.add_argument("--raw-root", type=Path, default=Path("runtime/raw"))
    parser.add_argument(
        "--checkpoint-root",
        type=Path,
        default=Path("runtime/decisions/regional-checkpoints"),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not 1024 <= args.port <= 65535 or not args.token:
        return 2

    class Handler(BaseHTTPRequestHandler):
        server_version = "RegionalBrowserCapture/1.0"

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/shutdown":
                if not self._authorized():
                    self._reply(403, {"status": "forbidden"})
                    return
                self._reply(200, {"status": "stopping"})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            if self.path not in {"/capture", "/discover", "/failure"} or not self._authorized():
                self._reply(404, {"status": "not_found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 1 <= length <= MAX_BODY_BYTES:
                    raise ValueError("capture body length is invalid")
                capture: Any = json.loads(self.rfile.read(length))
                if not isinstance(capture, dict):
                    raise ValueError("capture body must be an object")
                if self.path == "/discover":
                    result = None
                    checkpoint = _store_discovery(
                        capture,
                        checkpoint_root=args.checkpoint_root,
                    )
                elif self.path == "/failure":
                    result = None
                    checkpoint = _store_failure(
                        capture,
                        checkpoint_root=args.checkpoint_root,
                    )
                else:
                    result, checkpoint = _store_capture(
                        capture,
                        raw_root=args.raw_root,
                        checkpoint_root=args.checkpoint_root,
                    )
            except Exception as error:  # noqa: BLE001 - isolate each capture request
                self._reply(400, {"status": "rejected", "error": str(error)})
                return
            self._reply(
                200,
                {
                    "status": "stored",
                    "source_id": capture.get("source_id"),
                    "page": capture.get("page"),
                    "details": 0 if result is None else result.item_count,
                    "total": checkpoint.total_count,
                    "discovered": len(checkpoint.discovered_ids),
                    "captured": len(checkpoint.captured_ids),
                    "pending_ids": _pending_detail_ids(checkpoint),
                },
            )

        def log_message(self, format: str, *values: object) -> None:
            del format, values

        def _authorized(self) -> bool:
            return self.headers.get("Authorization") == f"Bearer {args.token}"

        def _reply(self, status: int, value: dict[str, Any]) -> None:
            payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"regional Browser capture endpoint ready: port={args.port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


def _store_capture(
    capture: dict[str, Any],
    *,
    raw_root: Path,
    checkpoint_root: Path,
) -> tuple[Any, RegionalBatchCheckpoint]:
    source_id = capture.get("source_id")
    if not isinstance(source_id, str):
        raise ValueError("capture source_id is required")
    raw_store = RegionalBrowserCaptureStore(
        source_id,
        store=RawDocumentStore(raw_root),
    )
    page, total_count, has_next, discovered_ids = (
        raw_store.checkpoint_metadata(capture)
    )
    checkpoint_store = RegionalCheckpointStore(checkpoint_root)
    checkpoint = checkpoint_store.load(source_id)
    if checkpoint is None:
        checkpoint = RegionalBatchCheckpoint.initial(source_id)
    captured_before = set(checkpoint.captured_ids)
    if page == checkpoint.next_page:
        checkpoint = checkpoint.discover(
            page=page,
            external_ids=discovered_ids,
            total_count=total_count,
            has_next=has_next,
        )
    elif page == checkpoint.next_page - 1 and not set(discovered_ids).issubset(
        checkpoint.discovered_ids
    ):
        checkpoint = checkpoint.amend_discovery(
            page=page,
            external_ids=discovered_ids,
            total_count=total_count,
            has_next=has_next,
        )
    elif not (
        page < checkpoint.next_page
        and set(discovered_ids).issubset(checkpoint.discovered_ids)
        and (total_count is None or total_count == checkpoint.total_count)
    ):
        raise ValueError("capture page does not match checkpoint")
    detail_ids = tuple(item["external_id"] for item in capture["items"])
    new_detail_ids = tuple(
        external_id
        for external_id in detail_ids
        if external_id not in captured_before
    )
    if new_detail_ids:
        checkpoint = checkpoint.capture(new_detail_ids)
    result = raw_store.save(capture)
    try:
        checkpoint_store.save(checkpoint)
    except Exception:
        raw_store.remove_result(result)
        raise
    return result, checkpoint


def _pending_detail_ids(checkpoint: RegionalBatchCheckpoint) -> list[str]:
    completed = set(checkpoint.captured_ids) | {
        external_id for external_id, _outcome in checkpoint.decisions
    }
    return [
        external_id
        for external_id in checkpoint.discovered_ids
        if external_id not in completed
    ]


def _store_discovery(
    capture: dict[str, Any], *, checkpoint_root: Path
) -> RegionalBatchCheckpoint:
    source_id = capture.get("source_id")
    if not isinstance(source_id, str):
        raise ValueError("discovery source_id is required")
    page = capture.get("page")
    total_count = capture.get("total_count")
    has_next = capture.get("has_next")
    discovered_ids = capture.get("discovered_ids")
    if (
        not isinstance(page, int)
        or not isinstance(has_next, bool)
        or not isinstance(discovered_ids, list)
        or not discovered_ids
        or not all(isinstance(value, str) for value in discovered_ids)
    ):
        raise ValueError("discovery capture is incomplete")
    store = RegionalCheckpointStore(checkpoint_root)
    checkpoint = store.load(source_id) or RegionalBatchCheckpoint.initial(source_id)
    if page == checkpoint.next_page:
        checkpoint = checkpoint.discover(
            page=page,
            external_ids=discovered_ids,
            total_count=total_count,
            has_next=has_next,
        )
    elif not (
        page < checkpoint.next_page
        and set(discovered_ids).issubset(checkpoint.discovered_ids)
        and (total_count is None or total_count == checkpoint.total_count)
    ):
        raise ValueError("discovery page does not match checkpoint")
    store.save(checkpoint)
    return checkpoint


def _store_failure(
    capture: dict[str, Any], *, checkpoint_root: Path
) -> RegionalBatchCheckpoint:
    source_id = capture.get("source_id")
    if not isinstance(source_id, str):
        raise ValueError("failure source_id is required")
    page = capture.get("page")
    total_count = capture.get("total_count")
    has_next = capture.get("has_next")
    discovered_ids = capture.get("discovered_ids")
    failed_id = capture.get("failed_id")
    if (
        not isinstance(page, int)
        or not isinstance(has_next, bool)
        or not isinstance(discovered_ids, list)
        or not discovered_ids
        or not isinstance(failed_id, str)
        or failed_id not in discovered_ids
    ):
        raise ValueError("failure capture is incomplete")
    store = RegionalCheckpointStore(checkpoint_root)
    checkpoint = store.load(source_id) or RegionalBatchCheckpoint.initial(source_id)
    if page == checkpoint.next_page:
        checkpoint = checkpoint.discover(
            page=page,
            external_ids=discovered_ids,
            total_count=total_count,
            has_next=has_next,
        )
    elif not (
        page < checkpoint.next_page
        and set(discovered_ids).issubset(checkpoint.discovered_ids)
    ):
        raise ValueError("failure page does not match checkpoint")
    if failed_id not in dict(checkpoint.decisions):
        checkpoint = checkpoint.decide({failed_id: "failed"})
    store.save(checkpoint)
    return checkpoint


if __name__ == "__main__":
    raise SystemExit(main())
