"""Host-invoked administrator PIN recovery command.

The new PIN and its confirmation are read from standard input so credentials do
not appear in process arguments or shell history.
"""

import re
import secrets
import sys

from app.core.database import SessionLocal
from app.services.admin_access import reset_admin_pin


PIN_PATTERN = re.compile(r"^\d{4}$")


def main() -> int:
    new_pin = sys.stdin.readline().rstrip("\r\n")
    confirmation = sys.stdin.readline().rstrip("\r\n")

    if not PIN_PATTERN.fullmatch(new_pin):
        print("PIN reset failed: PIN must contain exactly 4 digits.", file=sys.stderr)
        return 2
    if not secrets.compare_digest(new_pin, confirmation):
        print("PIN reset failed: confirmation does not match.", file=sys.stderr)
        return 2

    try:
        with SessionLocal.begin() as db:
            reset_admin_pin(db, new_pin=new_pin)
    except Exception as exc:
        print(
            f"PIN reset failed: {type(exc).__name__}.",
            file=sys.stderr,
        )
        return 1
    finally:
        new_pin = ""
        confirmation = ""

    print("Administrator PIN reset completed; existing sessions are invalid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
