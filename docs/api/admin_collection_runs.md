# 관리자 CollectionRun 이력 및 수동 실행 API 계약 (CollectionRun Admin API)

## 개요

이 문서는 `cheongnyeon-alimi` 백엔드의 관리자 전용 **CollectionRun 실행 이력 조회(목록·상세)**, **수동 수집 실행 요청(`202 Accepted`)**, **중복 실행 방지(`409 Conflict`)** 및 **Stale 판정 규칙**에 대한 API 계약을 정의한다.

모든 엔드포인트는 `Authorization: Bearer <access_token>` 관리자 서명 토큰을 요구한다.

---

## 1. CollectionRun 목록 조회

- **Endpoint**: `GET /api/v1/admin/collection-runs`
- **인증**: 필요 (`Authorization: Bearer <access_token>`, `role == 'admin'`)

### 쿼리 파라미터 (Query Parameters)

| 필드명 | 타입 | 기본값 | 제약 조건 / 예시 | 설명 |
| --- | --- | --- | --- | --- |
| `page` | `integer` | `1` | 1 이상 | 페이지 번호 |
| `size` | `integer` | `20` | 1 이상 100 이하 | 페이지 당 항목 수 |
| `source_id` | `string` | `null` | 예: `youthcenter-api` | 특정 수집원 ID 필터 |
| `status` | `string` | `null` | `queued`, `running`, `succeeded`, `partial_failure`, `failed` | 수집 상태 필터 |
| `run_type` | `string` | `null` | `seed_import`, `runtime_import`, `collection` | 실행 유형 필터 |
| `trigger_type` | `string` | `null` | `cli`, `scheduler`, `admin` | 트리거 주체 필터 |
| `start_date` | `string` | `null` | ISO-8601 (예: `2026-08-01T00:00:00Z`) | 시작일시 검색 범위 |
| `end_date` | `string` | `null` | ISO-8601 (예: `2026-08-10T23:59:59Z`) | 종료일시 검색 범위 |

### 정렬 규칙 (Sorting)

- 기본 정렬: `started_at DESC` (최신 실행순)

---

### 성공 응답 (200 OK)

```json
{
  "items": [
    {
      "run_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "source_id": "youthcenter-api",
      "run_type": "collection",
      "trigger_type": "admin",
      "started_at": "2026-08-10T12:00:00Z",
      "finished_at": "2026-08-10T12:05:30Z",
      "status": "succeeded",
      "is_stale": false,
      "inserted_count": 15,
      "updated_count": 5,
      "failed_count": 0,
      "error_type": null
    }
  ],
  "total": 42,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

---

## 2. CollectionRun 단건 상세 조회

- **Endpoint**: `GET /api/v1/admin/collection-runs/{run_id}`
- **인증**: 필요 (`Authorization: Bearer <access_token>`, `role == 'admin'`)

### 경로 파라미터 (Path Parameters)

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `run_id` | `UUID` | CollectionRun 식별자 (UUID v4) |

---

### 성공 응답 (200 OK)

```json
{
  "run_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "source_id": "cheonan-youthcenter-web",
  "run_type": "collection",
  "trigger_type": "admin",
  "started_at": "2026-08-10T12:00:00Z",
  "finished_at": "2026-08-10T12:05:30Z",
  "status": "succeeded",
  "is_stale": false,
  "requested_count": 100,
  "raw_document_count": 100,
  "extracted_count": 98,
  "accepted_count": 95,
  "partial_count": 10,
  "invalid_count": 3,
  "duplicate_count": 2,
  "rejected_count": 5,
  "inserted_count": 75,
  "updated_count": 20,
  "unchanged_count": 0,
  "skipped_count": 0,
  "failed_count": 0,
  "error_type": null
}
```

---

## 3. 수동 수집 실행 요청 (Trigger Manual Collection)

- **Endpoint**: `POST /api/v1/admin/collection-runs`
- **Content-Type**: `application/json`
- **인증**: 필요 (`Authorization: Bearer <access_token>`, `role == 'admin'`)

### 요청 바디 (Request Body)

```json
{
  "source_id": "cheonan-youthcenter-web",
  "requested_count": 100
}
```

| 필드명 | 타입 | 필수 여부 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `source_id` | `string` | 선택 | `cheonan-youthcenter-web` | 등록된 live Collector의 Source ID |
| `requested_count` | `integer` | 선택 | `100` | 단일 페이지 수집 요청 문서 수 (1~500) |

---

### 성공 응답 (202 Accepted)

수동 수집 요청을 PostgreSQL에 `queued`로 먼저 기록하고 Redis broker 발행까지
성공한 경우 반환한다. API process는 Collector를 직접 실행하지 않는다. 같은
`run_id`를 Celery task ID로 사용하며 worker의 실제 수집·Raw replay·DB 반영 뒤
`succeeded`·`partial_failure`·`failed` 중 하나로 종결된다. `202` 자체는 최종
성공을 뜻하지 않으므로 상세 endpoint에서 terminal 상태를 확인한다.

```json
{
  "run_id": "8f3a1b2c-9d4e-4f5a-8b7c-1d2e3f4a5b6c",
  "source_id": "cheonan-youthcenter-web",
  "run_type": "collection",
  "trigger_type": "admin",
  "status": "queued",
  "started_at": "2026-08-10T14:30:00Z",
  "message": "Manual collection run queued successfully."
}
```

---

## 4. Stale 및 중복 실행 판정 규칙

### Stale 판정 규칙
- **조건**: `status`가 `queued` 또는 `running`이고 `finished_at == null`인 상태에서, `started_at`으로부터 **2시간 (7,200초)** 경과 시.
- **표시**: 조회 API는 `is_stale = true`로 표시한다. 같은 Source의 새 요청이 들어오면 기존 stale 실행을 `failed`·`StaleCollectionRunReplaced`로 명시 종료한 뒤 새 실행을 접수한다.

### 중복·동시 실행 방지 (409 Conflict)
- 동일한 `source_id`에 `queued` 또는 `running` 실행이 존재하고 stale이 아니면
  **`409 Conflict`**를 반환한다. PostgreSQL partial unique index와 Source advisory
  lock이 API 동시 요청 race와 worker 겹침을 각각 차단한다.

---

## 5. 오류 응답 규격 (Error Responses)

#### 401 Unauthorized (인증 실패)
```json
{
  "detail": "Invalid or expired admin session token."
}
```

#### 403 Forbidden (권한 부족)
```json
{
  "detail": "Admin authorization required."
}
```

#### 404 Not Found (존재하지 않는 run_id)
```json
{
  "detail": "Collection run '3fa85f64-5717-4562-b3fc-2c963f66afa6' not found."
}
```

#### 409 Conflict (중복 수집 진행 중)
```json
{
  "error": {
    "message": "A collection run for source 'cheonan-youthcenter-web' is currently in progress.",
    "details": {
      "active_run_id": "8f3a1b2c-9d4e-4f5a-8b7c-1d2e3f4a5b6c",
      "started_at": "2026-08-10T14:30:00Z"
    }
  }
}
```

#### 422 Unprocessable Entity (유효성 실패)
잘못된 UUID 포맷, 무효한 쿼리 파라미터 수치 입력 시 반환한다.

#### 503 Service Unavailable (broker 발행 실패)

Redis에 task를 제한 재시도 후에도 발행하지 못하면 접수 row를 방치하지 않고
`failed`·`CollectionQueuePublishError`로 종료한 뒤 `503`을 반환한다. broker URL,
credential과 원문 예외 메시지는 응답·DB에 저장하지 않는다.
