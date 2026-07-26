import logging
import sys
from app.core.config import settings

def setup_logging():
    """
    애플리케이션 전역 로거 설정
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 중복 방지를 위한 핸들러 초기화
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]

logger = logging.getLogger("cheongnyeon-alimi")
