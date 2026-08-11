# 관리자 읽기 전용 정책 데이터 표 API 계약 (Admin Policies API Contract)

## 개요

이 문서는 인증된 시스템 관리자가 PostgreSQL에 적재된 정책 데이터를 CSV형 표 형식으로 안전하게 탐색하고 row 상세를 읽기 전용(Read-Only)으로 조회하기 위한 API 계약을 정의한다.

- **보안 규칙**: `Authorization: Bearer <admin_token>` 세션 토큰 인증 필수 (미인증 시 `401 Unauthorized`, 권한 부족 시 `403 Forbidden`).
- **안전성 수칙**: 데이터 수정/삭제/생성 경로가 존재하지 않으며, 승인된 Allowlist 컬럼 기반 정렬 및 필터링만 허용하여 SQL 주입 공격을 원천 차단한다.

---

## 1. 관리자 정책 데이터 표 목록 조회 (Read-Only)

- **Endpoint**: `GET /api/v1/admin/policies`
- **인증**: 필요 (`Authorization: Bearer <admin_token>`)

### 쿼리 파라미터 (Query Parameters)

| 파라미터 | 타입 | 필수 여부 | 기본값 | 제약 조건 / 예시 | 설명 |
| --- | --- | --- | --- | --- | --- |
| `page` | `integer` | 선택 | `1` | `ge=1` | 페이지 번호 |
| `limit` | `integer` | 선택 | `10` | `ge=1, le=100` | 페이지 당 항목 수 (최대 100) |
| `sort_by` | `string` | 선택 | `id` | `id`, `created_at`, `updated_at`, `title`, `collected_at` | Allowlist 정렬 컬럼 |
| `order` | `string` | 선택 | `desc` | `asc`, `desc` | 정렬 순서 |
| `category` | `string` | 선택 | `null` | 예: `housing`, `finance` | 카테고리 필터 |
| `region` | `string` | 선택 | `null` | 예: `서울특별시` | 지역 필터 |
| `source_id` | `string` | 선택 | `null` | 예: `initial_programs` | 수집 출처 ID 필터 |
| `status` | `string` | 선택 | `null` | `open`, `closed`, `scheduled` | 신청 상태 필터 |
| `data_quality_status` | `string` | 선택 | `null` | `valid`, `partial` | 데이터 품질 상태 필터 |

---

### 성공 응답 (200 OK)

```json
{
  "total": 1,
  "page": 1,
  "limit": 10,
  "items": [
    {
      "id": 1,
      "source_id": "initial_programs",
      "source_name": "초기 정규화 fixture",
      "external_id": "SYN-YOUTH-001",
      "title": "청년 월세 특별지원",
      "organization": "합성 주거기관",
      "categories": ["housing"],
      "regions": ["서울특별시"],
      "data_quality_status": "valid",
      "application_status": "open",
      "application_start": "2026-01-01",
      "application_end": "2026-12-31",
      "collected_at": "2026-07-26T06:00:00Z",
      "created_at": "2026-08-01T00:00:00Z",
      "updated_at": "2026-08-01T00:00:00Z"
    }
  ]
}
```

---

## 2. 관리자 정책 데이터 단건 상세 조회 (Read-Only)

- **Endpoint**: `GET /api/v1/admin/policies/{policy_id}`
- **인증**: 필요 (`Authorization: Bearer <admin_token>`)

### 성공 응답 (200 OK)

```json
{
  "id": 1,
  "source_id": "initial_programs",
  "source_name": "초기 정규화 fixture",
  "external_id": "SYN-YOUTH-001",
  "title": "청년 월세 특별지원",
  "organization": "합성 주거기관",
  "summary": "무주택 청년 월세 보조금 지원",
  "category_text": "주거",
  "categories": ["housing"],
  "region_text": "서울시",
  "regions": ["서울특별시"],
  "age_min": 19,
  "age_max": 34,
  "age_condition_text": "19세 ~ 34세",
  "eligibility_text": "무주택 청년",
  "support_content": "월 20만원 지원",
  "application_method": "온라인 신청",
  "education_statuses": [],
  "employment_statuses": [],
  "required_conditions": ["무주택자"],
  "preferred_conditions": [],
  "excluded_conditions": [],
  "source_url": "https://fixture.invalid/youthcenter/getPlcy",
  "data_quality_status": "valid",
  "application_status": "open",
  "application_start": "2026-01-01",
  "application_end": "2026-12-31",
  "collected_at": "2026-07-26T06:00:00Z",
  "created_at": "2026-08-01T00:00:00Z",
  "updated_at": "2026-08-01T00:00:00Z"
}
```

---

## 3. 오류 응답 규격 (Error Responses)

* **401 Unauthorized**: 세션 토큰 미제공 또는 만료된 경우
* **403 Forbidden**: 관리자 권한이 유효하지 않은 경우
* **404 Not Found**: 존재하지 않는 `policy_id` 조회 시
