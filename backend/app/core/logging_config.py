import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE_PATH = LOG_DIR / "app.log"

# 민감 키어 목록
REDACT_KEYS = {
    "pin",
    "token",
    "password",
    "secret",
    "api_key",
    "authorization",
    "raw_document",
    "raw_payload",
    "sql_parameter",
    "sql_parameters",
}


def sanitize_value(key: str, value: Any) -> Any:
    """민감 키어가 포함된 데이터인 경우 ***REDACTED***로 치환."""
    if isinstance(key, str) and any(rk in key.lower() for rk in REDACT_KEYS):
        return "***REDACTED***"

    if isinstance(value, dict):
        return {k: sanitize_value(k, v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_value(key, item) if isinstance(item, dict) else item for item in value]
    elif isinstance(value, str):
        # 메시지 문자열에 포함된 비밀 정보 마스킹
        lower_val = value.lower()
        if any(rk in lower_val for rk in REDACT_KEYS):
            # "pin": "0000" 형태 마스킹
            import re
            return re.sub(
                r'("(?:pin|token|password|secret|api_key|authorization|raw_document|raw_payload|sql_parameter|sql_parameters)"\s*:\s*)"[^"]+"',
                r'\1"***REDACTED***"',
                value,
                flags=re.IGNORECASE,
            )
    return value


class RedactingJsonFormatter(logging.Formatter):
    """
    JSON Lines 형식으로 로그 이벤트를 구조화하고,
    비밀번호, 토큰, PIN 등 민감 정보를 ***REDACTED***로 마스킹하는 포맷터.
    """

    def format(self, record: logging.LogRecord) -> str:
        event_msg = record.getMessage()
        sanitized_msg = sanitize_value("event", event_msg)

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "component": getattr(record, "component", "app"),
            "event": sanitized_msg,
        }

        # 선택적 correlation 정보 추가
        if hasattr(record, "request_id"):
            log_data["request_id"] = sanitize_value("request_id", record.request_id)
        if hasattr(record, "collection_run_id"):
            log_data["collection_run_id"] = sanitize_value(
                "collection_run_id", record.collection_run_id
            )
        if hasattr(record, "source_id"):
            log_data["source_id"] = sanitize_value("source_id", record.source_id)
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "error_type"):
            log_data["error_type"] = sanitize_value("error_type", record.error_type)

        return json.dumps(log_data, ensure_ascii=False)


def setup_file_logging(logger_name: str = "cheongnyeon-alimi", log_dir: Path = LOG_DIR) -> logging.Logger:
    """
    구조화된 UTF-8 파일 로거 설정.
    - 파일 크기 10MB 기준 rotation, 최대 5개 archive 보존.
    - stdout과 중복 없이 병행 기록.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    file_path = log_dir / "app.log"

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # 중복 handler 추가 방지
    file_handler_exists = any(isinstance(h, RotatingFileHandler) for h in logger.handlers)
    if not file_handler_exists:
        file_handler = RotatingFileHandler(
            filename=file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(RedactingJsonFormatter())
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)

    return logger
