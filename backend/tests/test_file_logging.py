import json
import logging
import tempfile
from pathlib import Path
from app.core.logging_config import RedactingJsonFormatter, setup_file_logging
from app.main import resolve_request_id


def test_redacting_json_formatter_masking():
    """RedactingJsonFormatter가 민감 정보(PIN, token, password, secret)를 ***REDACTED***로 마스킹하는지 검증."""
    formatter = RedactingJsonFormatter()

    record = logging.LogRecord(
        name="cheongnyeon-alimi",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg='User authenticated with {"pin": "0000", "token": "secret-admin-token-12345", "password": "supersecretpassword"}',
        args=(),
        exc_info=None,
    )

    formatted_str = formatter.format(record)
    assert formatted_str is not None

    log_json = json.loads(formatted_str)
    assert "timestamp" in log_json
    assert log_json["level"] == "INFO"
    assert "event" in log_json

    # 원문 민감 비밀 문자열이 비노출되고 ***REDACTED***로 치환되었는지 검증
    assert "0000" not in formatted_str
    assert "secret-admin-token-12345" not in formatted_str
    assert "supersecretpassword" not in formatted_str
    assert "***REDACTED***" in formatted_str


def test_redacting_json_formatter_masks_raw_and_sql_parameters():
    formatter = RedactingJsonFormatter()
    record = logging.LogRecord(
        name="cheongnyeon-alimi",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg=(
            'collector payload {"raw_payload": "full-source-document", '
            '"sql_parameters": "resident-registration-number"}'
        ),
        args=(),
        exc_info=None,
    )

    formatted_str = formatter.format(record)

    assert "full-source-document" not in formatted_str
    assert "resident-registration-number" not in formatted_str
    assert formatted_str.count("***REDACTED***") == 2


def test_redacting_json_formatter_preserves_safe_correlation_fields():
    formatter = RedactingJsonFormatter()
    record = logging.LogRecord(
        name="cheongnyeon-alimi",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="collection_step_completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-safe"
    record.collection_run_id = "run-safe"
    record.source_id = "source-safe"
    record.duration_ms = 12.5

    log_json = json.loads(formatter.format(record))

    assert log_json["request_id"] == "req-safe"
    assert log_json["collection_run_id"] == "run-safe"
    assert log_json["source_id"] == "source-safe"
    assert log_json["duration_ms"] == 12.5


def test_request_id_accepts_only_bounded_opaque_values():
    assert resolve_request_id("req-client_01") == "req-client_01"
    generated = resolve_request_id("unsafe request id with spaces")
    assert generated.startswith("req-")
    assert "unsafe" not in generated


def test_setup_file_logging_creates_file():
    """setup_file_logging 함수 실행 시 지정된 경로에 app.log가 생성되는지 검증."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_log_dir = Path(temp_dir)
        logger = setup_file_logging(logger_name="test_temp_logger", log_dir=temp_log_dir)

        logger.info("Test log entry for file creation check")

        log_file = temp_log_dir / "app.log"
        assert log_file.exists()

        content = log_file.read_text(encoding="utf-8")
        assert "Test log entry for file creation check" in content

        # Windows 파일 lock 해제를 위해 handler 닫기 및 정리
        handlers_to_remove = list(logger.handlers)
        for handler in handlers_to_remove:
            handler.close()
            logger.removeHandler(handler)
