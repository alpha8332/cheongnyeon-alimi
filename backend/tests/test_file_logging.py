import json
import logging
import tempfile
from pathlib import Path
from app.core.logging_config import RedactingJsonFormatter, setup_file_logging


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
