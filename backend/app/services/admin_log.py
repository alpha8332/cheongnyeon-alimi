import json
import logging
import os
import uuid
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from app.core.logging_config import LOG_DIR
from app.schemas.admin_log import (
    LogDeleteResponse,
    LogEventItem,
    LogEventListResponse,
    LogFileItem,
    LogFileListResponse,
    LogRotateResponse,
)

# 인메모리 감사 기록 저장소 (Audit Trail)
AUDIT_TRAIL: List[dict] = []


def is_safe_filename(file_id: str) -> bool:
    """Path Traversal 방지를 위한 안전한 파일명 검증."""
    if ".." in file_id or "/" in file_id or "\\" in file_id:
        return False
    # app.log 또는 app.log.1, app.log.2 형태만 허용
    return file_id == "app.log" or file_id.startswith("app.log.")


def list_log_files_service(log_dir: Path = LOG_DIR) -> LogFileListResponse:
    """안전한 로그 파일 목록 스캔 서비스."""
    log_files: List[LogFileItem] = []
    if not log_dir.exists():
        return LogFileListResponse(files=[])

    for entry in sorted(log_dir.glob("app.log*"), key=lambda p: p.name):
        if entry.is_file():
            stat = entry.stat()
            is_active = entry.name == "app.log"
            log_files.append(
                LogFileItem(
                    file_id=entry.name,
                    filename=entry.name,
                    size_bytes=stat.st_size,
                    is_active=is_active,
                    modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                )
            )

    return LogFileListResponse(files=log_files)


def get_log_events_service(
    file_id: str = "app.log",
    page: int = 1,
    limit: int = 20,
    level: Optional[str] = None,
    component: Optional[str] = None,
    query_str: Optional[str] = None,
    log_dir: Path = LOG_DIR,
) -> LogEventListResponse:
    """지정된 로그 파일에서 bounded JSON Lines 이벤트를 파싱 및 필터링하여 조회한다."""
    if not is_safe_filename(file_id):
        raise ValueError("Invalid or unsafe log file_id")

    target_file = log_dir / file_id
    if not target_file.exists() or not target_file.is_file():
        return LogEventListResponse(total=0, page=page, limit=limit, events=[])

    safe_limit = min(max(limit, 1), 100)
    safe_page = max(page, 1)

    parsed_events: List[LogEventItem] = []

    # 파일 읽기 및 JSON 파싱
    with open(target_file, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
                event_item = LogEventItem(
                    timestamp=data.get("timestamp", ""),
                    level=data.get("level", "INFO"),
                    component=data.get("component", "app"),
                    event=data.get("event", ""),
                    request_id=data.get("request_id"),
                    collection_run_id=data.get("collection_run_id"),
                    source_id=data.get("source_id"),
                    duration_ms=data.get("duration_ms"),
                    error_type=data.get("error_type"),
                )

                # 필터 적용
                if level and event_item.level.upper() != level.upper():
                    continue
                if component and event_item.component.lower() != component.lower():
                    continue
                if query_str and query_str.lower() not in event_item.event.lower():
                    continue

                parsed_events.append(event_item)
            except Exception:
                continue

    # 최신순 정렬 (역순)
    parsed_events.reverse()

    total = len(parsed_events)
    offset = (safe_page - 1) * safe_limit
    result_events = parsed_events[offset : offset + safe_limit]

    return LogEventListResponse(
        total=total,
        page=safe_page,
        limit=safe_limit,
        events=result_events,
    )


def delete_archived_log_file_service(
    file_id: str,
    admin_id: str = "admin",
    log_dir: Path = LOG_DIR,
) -> LogDeleteResponse:
    """
    회전 완료된 Archive 로그 파일만 안전하게 삭제하고 별도 감사 기록(Audit Trail)을 생성한다.
    - 활성 파일(app.log) 직접 삭제 차단
    - Path Traversal 방지
    """
    audit_id = f"audit-{uuid.uuid4().hex[:8]}"

    if not is_safe_filename(file_id):
        AUDIT_TRAIL.append({
            "audit_id": audit_id,
            "admin_id": admin_id,
            "file_id": file_id,
            "action": "delete_archive",
            "success": False,
            "reason": "Invalid or unsafe log file_id",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        raise ValueError("Invalid or unsafe log file_id")

    if file_id == "app.log":
        AUDIT_TRAIL.append({
            "audit_id": audit_id,
            "admin_id": admin_id,
            "file_id": file_id,
            "action": "delete_archive",
            "success": False,
            "reason": "Active log file 'app.log' cannot be directly deleted",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        raise PermissionError("Active log file 'app.log' cannot be directly deleted")

    target_file = log_dir / file_id
    if not target_file.exists() or not target_file.is_file():
        AUDIT_TRAIL.append({
            "audit_id": audit_id,
            "admin_id": admin_id,
            "file_id": file_id,
            "action": "delete_archive",
            "success": False,
            "reason": "File not found",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        raise FileNotFoundError(f"Log archive file '{file_id}' not found")

    try:
        os.remove(target_file)
        AUDIT_TRAIL.append({
            "audit_id": audit_id,
            "admin_id": admin_id,
            "file_id": file_id,
            "action": "delete_archive",
            "success": True,
            "reason": "Successfully deleted log archive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return LogDeleteResponse(
            file_id=file_id,
            deleted=True,
            audit_id=audit_id,
            message=f"Log archive file '{file_id}' deleted successfully.",
        )
    except Exception as e:
        AUDIT_TRAIL.append({
            "audit_id": audit_id,
            "admin_id": admin_id,
            "file_id": file_id,
            "action": "delete_archive",
            "success": False,
            "reason": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        raise e


def rotate_current_log_service(
    admin_id: str = "admin",
    log_dir: Path = LOG_DIR,
) -> LogRotateResponse:
    """Rotate the active log, delete only the generated archive, and audit it.

    Existing archives remain untouched. When the application file handler owns
    ``app.log``, its rollover operation is used so the Windows file handle is
    closed and reopened safely.
    """

    audit_id = f"audit-{uuid.uuid4().hex[:8]}"
    active_file = log_dir / "app.log"
    generated_archive = log_dir / f"app.log.rotate-{uuid.uuid4().hex[:8]}"
    log_dir.mkdir(parents=True, exist_ok=True)

    try:
        matching_handler = next(
            (
                handler
                for handler in logging.getLogger("cheongnyeon-alimi").handlers
                if isinstance(handler, RotatingFileHandler)
                and Path(handler.baseFilename).resolve() == active_file.resolve()
            ),
            None,
        )

        if matching_handler is not None:
            matching_handler.acquire()
            try:
                if matching_handler.stream is not None:
                    matching_handler.stream.flush()
                    matching_handler.stream.close()
                    matching_handler.stream = None
                active_file.replace(generated_archive)
                active_file.touch()
                matching_handler.stream = matching_handler._open()
            finally:
                matching_handler.release()
        else:
            active_file.touch(exist_ok=True)
            active_file.replace(generated_archive)
            active_file.touch()

        if not generated_archive.exists() or not generated_archive.is_file():
            raise RuntimeError("Log rotation did not create the expected archive")

        generated_archive.unlink()
        AUDIT_TRAIL.append({
            "audit_id": audit_id,
            "admin_id": admin_id,
            "file_id": "app.log",
            "archive_file_id": generated_archive.name,
            "action": "rotate_current_cleanup",
            "success": True,
            "reason": "Rotated active log and deleted the generated archive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return LogRotateResponse(
            rotated_file_id="app.log",
            deleted_archive_file_id=generated_archive.name,
            audit_id=audit_id,
            message="Current log rotated and its generated archive deleted successfully.",
        )
    except Exception as exc:
        AUDIT_TRAIL.append({
            "audit_id": audit_id,
            "admin_id": admin_id,
            "file_id": "app.log",
            "archive_file_id": generated_archive.name,
            "action": "rotate_current_cleanup",
            "success": False,
            "reason": type(exc).__name__,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        raise RuntimeError("Current log rotate-and-cleanup failed") from exc
