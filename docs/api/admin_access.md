# 관리자 인증 API 계약 (Admin Access Control)

## 개요

이 문서는 `cheongnyeon-alimi` 백엔드의 관리자 전용 세션 생성 및 인증·권한 API 계약을 정의한다.

---

## 1. 관리자 세션 생성 (로그인)

- **Endpoint**: `POST /api/v1/admin/session`
- **Content-Type**: `application/json`
- **인증**: 필요 없음 (Public)

### 요청 (Request Body)

```json
{
  "pin": "0000"
}
```

| 필드명 | 타입 | 필수 여부 | 제약 조건 | 설명 |
| --- | --- | --- | --- | --- |
| `pin` | `string` | **필수** | 정확히 4자리 숫자 (`^\d{4}$`) | 관리자 접근 4자리 PIN |

---

### 응답 (Response)

#### 200 OK (세션 생성 성공)

```json
{
  "access_token": "admin.1770475800.a1b2c3d4e5f67890",
  "token_type": "bearer",
  "expires_in": 3600,
  "role": "admin"
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `access_token` | `string` | 세션 발급 관리자 서명 토큰 (`admin.<expires_at>.<sig>`) |
| `token_type` | `string` | 토큰 인증 타입 (`"bearer"`) |
| `expires_in` | `integer` | 토큰 유효 기간 (초 단위, 기본 3600초/60분) |
| `role` | `string` | 부여된 역할 (`"admin"`) |

---

### 오류 응답 (Error Responses)

#### 401 Unauthorized (인증 실패 / Fail-closed)

PIN이 일치하지 않거나, 배포 환경에서 관리자 PIN 설정이 누락되어 접근이 비활성화된 경우 반환한다. (보안을 위해 내부 실패 사유는 상세 노출하지 않음)

```json
{
  "error": {
    "message": "Invalid admin PIN or authentication disabled.",
    "details": {}
  }
}
```

#### 403 Forbidden (권한 부족)

인증되지 않았거나 비관리자 역할로 보호된 관리자 라우트에 접근 시 반환한다.

```json
{
  "error": {
    "message": "Admin authorization required.",
    "details": {}
  }
}
```

#### 429 Too Many Requests (점진적 Rate Limit 및 Lockout)

동일 IP에서 5회 연속 로그인 실패 시 단계별 점진적 락아웃(5초 ➔ 10초 ➔ 30초 ➔ 60초 ➔ 120초 ➔ 300초)을 적용한다.

```json
{
  "error": {
    "message": "Too many failed login attempts. Account temporarily locked for 5 seconds.",
    "details": {
      "cooldown_seconds": 5
    }
  }
}
```

#### 422 Unprocessable Entity (형식 검증 실패)

PIN이 4자리 숫자가 아니거나 유효하지 않은 JSON 요청인 경우 반환한다.

---

## 2. 환경별 PIN 검증 규칙

1. **로컬 / 개발 환경 (`ENVIRONMENT` = `development` / `local` / `test`)**:
   - `ADMIN_PIN_HASH` 환경변수가 설정되지 않은 경우, 로컬 시연 편의를 위해 최초 기본 PIN `0000` (SHA-256 해시)을 허용한다.
2. **배포 / 프로덕션 환경 (`ENVIRONMENT` = `production`)**:
   - 명시적 `ADMIN_PIN_HASH`가 지정되지 않은 경우 **Fail-closed** 정책을 적용하여 `0000`을 포함한 모든 PIN 로그인을 `401`로 즉시 거부한다.
