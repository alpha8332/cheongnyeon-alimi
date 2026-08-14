# 관리자 파일 로그 및 감사 API 계약 (Admin Logs API Contract)

## 개요

이 문서는 인증된 시스템 관리자가 서버에 보존된 UTF-8 JSON Lines 구조화 파일 로그를 조회하고, 회전 완료된 Archive 로그 파일을 안전하게 삭제하며 Audit 감사 이력을 생성하기 위한 API 계약을 정의한다.

- **보안 규칙**: `Authorization: Bearer <admin_token>` 세션 토큰 인증 필수 (미인증 시 `401 Unauthorized`, 권한 부족 시 `403 Forbidden`).
- **안전 수칙**:
  - 현재 기록 중인 활성 파일(`app.log`)은 직접 삭제할 수 없으며 (시도 시 `400 Bad Request`), 회전 완료된 Archive 파일만 삭제를 허용한다.
  - Path Traversal 공격을 방지하기 위해 허용된 로그 디렉터리 내부 파일명만 지원한다.
  - Archive 파일 삭제 시 별도의 Audit Trail(`AdminAuditEvent`)에 삭제 감사 기록을 필수 생성한다.

---

## 1. 로그 파일 목록 조회

- **Endpoint**: `GET /api/v1/admin/logs/files`
- **인증**: 필요 (`Authorization: Bearer <admin_token>`)

### 성공 응답 (200 OK)

```json
{
  "files": [
    {
      "file_id": "app.log",
      "filename": "app.log",
      "size_bytes": 1024,
      "is_active": true,
      "modified_at": "2026-08-11T12:00:00Z"
    },
    {
      "file_id": "app.log.1",
      "filename": "app.log.1",
      "size_bytes": 10485760,
      "is_active": false,
      "modified_at": "2026-08-10T12:00:00Z"
    }
  ]
}
```

---

## 2. 파싱된 로그 이벤트 목록 조회

- **Endpoint**: `GET /api/v1/admin/logs/events`
- **인증**: 필요 (`Authorization: Bearer <admin_token>`)

### 쿼리 파라미터 (Query Parameters)

| 파라미터 | 타입 | 필수 여부 | 기본값 | 제약 조건 / 예시 | 설명 |
| --- | --- | --- | --- | --- | --- |
| `file_id` | `string` | 선택 | `app.log` | `app.log`, `app.log.1` | 조회 대상 파일 ID |
| `page` | `integer` | 선택 | `1` | `ge=1` | 페이지 번호 |
| `limit` | `integer` | 선택 | `20` | `ge=1, le=100` | 페이지 당 항목 수 |
| `level` | `string` | 선택 | `null` | `INFO`, `ERROR`, `CRITICAL` | 로그 레벨 필터 |
| `component` | `string` | 선택 | `null` | `api`, `collector` | 컴포넌트 필터 |
| `q` | `string` | 선택 | `null` | 예: `unhandled` | 이벤트 검색어 |

### 성공 응답 (200 OK)

```json
{
  "total": 1,
  "page": 1,
  "limit": 20,
  "events": [
    {
      "timestamp": "2026-08-11T12:00:00Z",
      "level": "INFO",
      "component": "api",
      "event": "GET /api/v1/admin/logs/files - Status: 200 - Completed in 1.20ms",
      "request_id": null,
      "collection_run_id": null,
      "source_id": null,
      "duration_ms": null,
      "error_type": null
    }
  ]
}
```

---

## 3. 회전된 Archive 로그 파일 삭제 (감사 기록 생성)

- **Endpoint**: `DELETE /api/v1/admin/logs/archives/{file_id}`
- **인증**: 필요 (`Authorization: Bearer <admin_token>`)

### 성공 응답 (200 OK)

```json
{
  "file_id": "app.log.1",
  "deleted": true,
  "audit_id": "audit-a1b2c3d4",
  "message": "Log archive file 'app.log.1' deleted successfully."
}
```

---

## 4. 현재 로그 rotate 정리

- **Endpoint**: `POST /api/v1/admin/logs/rotate-current`
- **인증**: 필요 (`Authorization: Bearer <admin_token>`)
- **의미**: 활성 `app.log`를 직접 삭제하지 않는다. 기존 numbered archive를
  이동·정리하지 않는 고유 임시 archive로 먼저 회전하고, 그 작업으로 생성된
  archive만 삭제한다. 기존 archive는 보존하며 작업별 Audit Trail을 남긴다.

### 성공 응답 (200 OK)

```json
{
  "rotated_file_id": "app.log",
  "deleted_archive_file_id": "app.log.rotate-a1b2c3d4",
  "audit_id": "audit-a1b2c3d4",
  "message": "Current log rotated and its generated archive deleted successfully."
}
```

---

## 5. 오류 응답 규격 (Error Responses)

* **400 Bad Request**: 활성 파일(`app.log`) 직접 삭제 시도 또는 Path Traversal 시도 시
* **401 Unauthorized**: 세션 토큰 미제공 또는 만료 시
* **403 Forbidden**: 관리자 권한이 유효하지 않은 경우
* **404 Not Found**: 존재하지 않는 로그 파일 삭제/조회 시
