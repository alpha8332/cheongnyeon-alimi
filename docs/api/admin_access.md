# 관리자 인증 API 계약 (Admin Access Control)

## 개요

이 문서는 `cheongnyeon-alimi` 백엔드의 관리자 전용 세션 생성, PIN 변경 및
인증·권한 API 계약을 정의한다. PIN과 access token은 URL, 로그 또는 응답에
기록하지 않는다.

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
  "access_token": "<redacted>",
  "token_type": "bearer",
  "expires_in": 3600,
  "role": "admin"
}
```

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `access_token` | `string` | 세션 세대가 결합된 관리자 서명 토큰 |
| `token_type` | `string` | 토큰 인증 타입 (`"bearer"`) |
| `expires_in` | `integer` | 토큰 유효 기간 (초 단위, 기본 3600초/60분) |
| `role` | `string` | 부여된 역할 (`"admin"`) |

---

## 2. 관리자 PIN 변경

- **Endpoint**: `PUT /api/v1/admin/pin`
- **Content-Type**: `application/json`
- **인증**: Bearer 토큰 필요

```json
{
  "current_pin": "<four-digits>",
  "new_pin": "<four-digits>"
}
```

두 필드는 정확히 4자리 숫자여야 한다. 현재 PIN이 일치하고 새 PIN이 다를 때
`204 No Content`를 반환한다. 변경 transaction에서 PIN verifier를 salted PBKDF2로
교체하고 session generation을 증가시키므로, 변경 요청에 사용한 토큰을 포함한
기존 관리자 토큰은 즉시 무효가 된다. Frontend는 성공 후 세션을 지우고 새 PIN
로그인을 요구한다.

- 현재 PIN 불일치: `401 Unauthorized`
- 현재 PIN 재사용: `409 Conflict`
- 형식 오류: `422 Unprocessable Entity`

PIN을 잊은 경우 이 API를 우회하거나 복구 PIN을 제공하지 않는다. 서버 PC에서
`reset_admin_pin.bat`을 실행하는 host-only 절차를 사용한다.

---

## 3. 관리자 권한 상태 확인 (보호 라우트 샘플)

- **Endpoint**: `GET /api/v1/admin/me`
- **인증**: Bearer 토큰 필요 (`Authorization: Bearer <access_token>`)

### 요청 헤더 (Headers)

```text
Authorization: Bearer <access-token>
```

### 응답 (Response)

#### 200 OK (인증 및 권한 확인 성공)

```json
{
  "role": "admin",
  "expires_at": 1770475800,
  "status": "authenticated"
}
```

---

## 4. 오류 응답 표준 (Error Responses)

#### 401 Unauthorized (인증 실패 / 헤더 누락 / 토큰 만료)

- 세션 생성 시: 잘못된 PIN 또는 배포 환경의 인증 비활성화 (Fail-closed)
- 보호 라우트 접근 시: Authorization 헤더 누락, 서명 변조, 또는 토큰 만료

```json
{
  "detail": "Invalid or expired admin session token."
}
```

#### 403 Forbidden (권한 부족)

유효한 토큰이지만 관리자 역할(`role == "admin"`)이 아니거나 관리자 API 접근 권한이 부족한 경우 반환한다.

```json
{
  "detail": "Admin authorization required."
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

## 5. PIN 저장 및 환경별 검증 규칙

최초 로그인에서 기존 `ADMIN_PIN_HASH`를 DB의 singleton 관리자 인증 상태로
초기화한다. 이후 변경·복구한 PIN verifier와 session generation은 DB에 저장되므로
정책·CollectionRun Volume을 유지한 재시작에서도 그대로 유지된다. 환경변수의
기존 SHA-256 verifier는 최초 bootstrap 호환용으로만 읽고, 변경·복구 시에는
salted PBKDF2 verifier로 승격한다. PIN 평문은 저장하지 않는다.

1. **로컬 / 개발 환경 (`ENVIRONMENT` = `development` / `local` / `test`)**:
   - `ADMIN_PIN_HASH` 환경변수가 설정되지 않고 실제 요청 client가 loopback인 경우에만
     로컬 시연용 최초 PIN `0000`을 허용한다. 외부 client 요청에는 개발 환경이어도
     기본 PIN을 허용하지 않는다.
2. **배포 / 프로덕션 환경 (`ENVIRONMENT` = `production`)**:
   - 명시적 `ADMIN_PIN_HASH`가 지정되지 않은 경우 **Fail-closed** 정책을 적용하여 `0000`을 포함한 모든 PIN 로그인을 `401`로 즉시 거부한다.
   - `ADMIN_TOKEN_SECRET`을 별도로 지정해야 하며, 미설정 시 공용 `SECRET_KEY`로
     fallback하지 않고 세션 발급을 거부한다.
