import hashlib
import hmac
import time
from typing import Dict, Tuple, Optional

from app.core.config import settings

# SHA-256 hash of default local PIN '0000'
DEFAULT_LOCAL_PIN_HASH = "9af15b336e6a9619928537df30b2e6a2376569fcf9d7e773eccede65606529a0"

# In-memory rate limiting state for failed login attempts (ip -> (attempts, lock_until_timestamp))
_failed_attempts: Dict[str, Tuple[int, float]] = {}


def get_effective_pin_hash() -> Optional[str]:
    """
    유효한 관리자 PIN 해시를 반환한다.
    - ADMIN_PIN_HASH가 설정되어 있으면 그 값을 사용.
    - 미설정 시 development/local/test 환경이면 최초 PIN '0000' 해시를 사용.
    - production 등 외부 배포 환경에서 미설정이면 None을 반환(fail-closed).
    """
    if settings.ADMIN_PIN_HASH:
        return settings.ADMIN_PIN_HASH.lower()

    if settings.ENVIRONMENT.lower() in ("development", "local", "test"):
        return DEFAULT_LOCAL_PIN_HASH

    return None


def verify_admin_pin(pin: str) -> bool:
    """
    입력된 4자리 PIN의 SHA-256 해시값을 유효 해시와 비교한다.
    """
    effective_hash = get_effective_pin_hash()
    if not effective_hash:
        # Fail-closed: production에서 설정 미비 시 모든 PIN 거부
        return False

    input_hash = hashlib.sha256(pin.encode("utf-8")).hexdigest().lower()
    return hmac.compare_digest(input_hash, effective_hash)


def is_rate_limited(ip: str) -> Tuple[bool, int]:
    """
    IP별 반복 로그인 실패에 따른 Rate Limit / Cooldown 여부를 검사한다.
    Returns: (is_limited, remaining_lockout_seconds)
    """
    now = time.time()
    if ip not in _failed_attempts:
        return False, 0

    attempts, lock_until = _failed_attempts[ip]
    if now < lock_until:
        remaining = int(lock_until - now) + 1
        return True, remaining

    if now >= lock_until and attempts >= settings.ADMIN_MAX_LOGIN_ATTEMPTS:
        # Cooldown expired, reset
        _failed_attempts.pop(ip, None)
        return False, 0

    return False, 0


def record_failed_attempt(ip: str) -> Tuple[int, bool]:
    """
    로그인 실패 기록을 남기고, 최대 횟수 초과 시 락아웃을 설정한다.
    Returns: (current_attempts, is_now_locked)
    """
    now = time.time()
    attempts, lock_until = _failed_attempts.get(ip, (0, 0.0))
    attempts += 1

    locked = False
    if attempts >= settings.ADMIN_MAX_LOGIN_ATTEMPTS:
        lock_until = now + settings.ADMIN_LOCKOUT_SECONDS
        locked = True

    _failed_attempts[ip] = (attempts, lock_until)
    return attempts, locked


def reset_failed_attempts(ip: str) -> None:
    """로그인 성공 시 실패 카운트를 초기화한다."""
    _failed_attempts.pop(ip, None)


def clear_rate_limit_state() -> None:
    """테스트용 rate limit 전체 초기화."""
    _failed_attempts.clear()
