import hashlib
import hmac
import time
from typing import Dict, Tuple, Optional

from app.core.config import settings

# SHA-256 hash of default local PIN '0000'
DEFAULT_LOCAL_PIN_HASH = "9af15b336e6a9619928537df30b2e6a2376569fcf9d7e773eccede65606529a0"

# Progressive lockout cooldown steps in seconds (5회 이상 실패 시 순차 적용)
PROGRESSIVE_LOCKOUT_STEPS = [5, 10, 30, 60, 120, 300]

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
    원문 PIN은 로그나 예외 메시지에 남기지 않는다.
    """
    effective_hash = get_effective_pin_hash()
    if not effective_hash:
        # Fail-closed: production에서 설정 미비 시 모든 PIN 거부
        return False

    input_hash = hashlib.sha256(pin.encode("utf-8")).hexdigest().lower()
    return hmac.compare_digest(input_hash, effective_hash)


def get_admin_token_secret() -> bytes:
    """관리자 토큰 서명에 사용할 시크릿 바이트를 반환한다."""
    secret = settings.ADMIN_TOKEN_SECRET or settings.SECRET_KEY
    return secret.encode("utf-8")


def create_admin_session_token(expires_minutes: Optional[int] = None) -> str:
    """
    짧은 수명의 관리자 서명 토큰(HMAC-SHA256)을 생성한다.
    형식: admin.<expires_at_timestamp>.<signature_hex_16>
    """
    minutes = expires_minutes if expires_minutes is not None else settings.ADMIN_SESSION_EXPIRE_MINUTES
    expires_at = int(time.time()) + (minutes * 60)
    payload = f"admin:{expires_at}".encode("utf-8")
    secret = get_admin_token_secret()
    signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()[:16]
    return f"admin.{expires_at}.{signature}"


def verify_admin_session_token(token: str) -> Optional[dict]:
    """
    관리자 세션 토큰의 서명 및 만료 시간을 검증한다.
    유효한 경우 토큰 페이로드를 반환하고, 변조되거나 만료된 경우 None을 반환한다.
    """
    if not token or not isinstance(token, str):
        return None

    parts = token.strip().split(".")
    if len(parts) != 3 or parts[0] != "admin":
        return None

    try:
        expires_at = int(parts[1])
    except ValueError:
        return None

    # 만료 시간 검증
    if time.time() > expires_at:
        return None

    # 서명 검증
    payload = f"admin:{expires_at}".encode("utf-8")
    secret = get_admin_token_secret()
    expected_signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()[:16]

    if not hmac.compare_digest(parts[2], expected_signature):
        return None

    return {
        "sub": "admin",
        "role": "admin",
        "expires_at": expires_at,
    }


def calculate_cooldown_seconds(attempts: int) -> int:
    """실패 횟수에 따른 점진적 쿨다운 시간(5, 10, 30, 60, 120, 300초)을 계산한다."""
    if attempts < settings.ADMIN_MAX_LOGIN_ATTEMPTS:
        return 0
    step_index = attempts - settings.ADMIN_MAX_LOGIN_ATTEMPTS
    if step_index >= len(PROGRESSIVE_LOCKOUT_STEPS):
        return PROGRESSIVE_LOCKOUT_STEPS[-1]
    return PROGRESSIVE_LOCKOUT_STEPS[step_index]


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

    return False, 0


def record_failed_attempt(ip: str) -> Tuple[int, bool, int]:
    """
    로그인 실패 기록을 남기고, 5회 이상 실패 시 점진적 락아웃(5->10->30->60->120->300초)을 설정한다.
    Returns: (current_attempts, is_now_locked, cooldown_seconds)
    """
    now = time.time()
    attempts, lock_until = _failed_attempts.get(ip, (0, 0.0))
    attempts += 1

    cooldown = calculate_cooldown_seconds(attempts)
    locked = False
    if cooldown > 0:
        lock_until = now + cooldown
        locked = True

    _failed_attempts[ip] = (attempts, lock_until)
    return attempts, locked, cooldown


def reset_failed_attempts(ip: str) -> None:
    """로그인 성공 시 실패 카운트를 초기화한다."""
    _failed_attempts.pop(ip, None)


def clear_rate_limit_state() -> None:
    """테스트용 rate limit 전체 초기화."""
    _failed_attempts.clear()
