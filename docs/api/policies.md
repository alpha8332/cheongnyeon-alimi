# Policy API 계약

## 계약 정보

- Base path: `/api/v1/policies`
- 인증: 현재 없음
- 응답 형식: JSON
- 정렬: 정책 목록은 기본 `id` 오름차순, 자연어 검색은 요청한 결정적 정렬
- 데이터 기준: `NormalizedProgram` 1.0.0·1.1.0·1.2.0 전환 호환

일반 사용자 Policy API는 Raw provenance를 반환하지 않는다. 목록과 상세는
기본적으로 `valid` 정책만 노출하며 `include_partial=true`일 때
`valid`·`partial`을 함께 허용한다. `invalid` 정책은 어떤 경우에도 공개하지
않는다.

모든 사용자 목록·상세·자연어 검색·추천은 검증을 마치고 원자적으로 활성화된
공개 dataset의 membership에 포함된 정책만 반환한다. 로컬 수집, 과거 개발
데이터와 수동 수집 결과는 `policies`에 보존될 수 있지만 membership 승격 전에는
이 API에서 조회되지 않는다. active dataset이 없으면 임의의 DB row로 대체하지
않고 빈 결과 또는 상세 404를 반환한다.

모든 사용자 목록·상세·자연어 검색·추천은 `inactive_at IS NULL`인 행 중
`application_end`가 없거나 Asia/Seoul 오늘 이상인 정책만 반환한다. 종료일
경과와 inactive 행은 명시적 `status=closed`에도 공개하지 않으며 관리자
읽기 전용 API와 DB에는 감사 이력으로 보존한다.

## 정책 자연어 검색

```http
GET /api/v1/policies/search
```

### Query

| 이름 | 타입 | 기본값 | 규칙 |
| --- | --- | --- | --- |
| `q` | string | 빈 문자열 | 자연어 검색어 (최대 200자). 명시 조건이 있으면 생략 가능 |
| `keyword` | string | 없음 | 명시적 키워드 필터 (최대 100자) |
| `region` | string | 없음 | 명시적 지역 alias/name 문자열 (최대 100자) |
| `age` | integer | 없음 | 명시적 만 연령 (0~150세) |
| `category` | enum | 없음 | 명시적 카테고리 |
| `status` | enum | 없음 | 명시적 신청 상태 (`open`, `closed`, `scheduled`) |
| `include_partial` | boolean | `true` | partial 정책 포함 여부 (기본값: true) |
| `page` | integer | `1` | 1 이상 |
| `limit` | integer | `20` | 1~100 |
| `sort` | enum | `default` | `default`, `title_asc`, `title_desc`, `deadline_asc`, `deadline_desc`, `collected_desc`, `collected_asc` |

`q`가 비어 있으면 `keyword`, `region`, `age`, `category`, `status` 중 하나
이상의 명시 조건이 필요하다. 자연어 검색어와 명시 조건이 모두 없으면 `422`를
반환한다. 따라서 홈에서는 지역이나 관심 분야만 선택해도 검색할 수 있지만,
아무 조건도 없는 전체 정책 요청으로 이 endpoint를 사용하지 않는다.

프로필 우선순위 보정이 필요하면 같은 검색 필드와 다음 `preferences`를 JSON으로
보내는 `POST /api/v1/policies/search`를 사용한다.

```json
{
  "q": "대학생 지원",
  "include_partial": true,
  "page": 1,
  "limit": 20,
  "sort": "default",
  "preferences": {
    "region": "경상남도 양산시",
    "age": 25,
    "categories": ["education", "welfare"]
  }
}
```

`preferences.categories`는 최대 7개의 복수 관심 분야를 OR로 평가한다. 프로필은
명시적 검색 조건을 추가하거나 자연어에서 해석한 지역·분야를 덮지 않고, 후보의
결정적 관련도와 추천 이유만 보정한다. `preferences`가 없으면 GET과 같은 결과
계약을 사용한다.

`region`을 명시적으로 전달하거나 `q`에서 지역을 해석한 경우, 다른 지역으로
확인된 `mismatch`는 반환하지 않는다. 지역 근거가 없는 `unknown`은 공개
bootstrap처럼 지역 필드가 누락된 전국 단위 정책의 발견 가능성을 보존하기
위해 낮은 우선순위의 미확인 후보로 남긴다. 응답의 `verdicts.region`,
`reason_codes=REGION_UNKNOWN`, `unconfirmed_conditions`로 확인된 지역 일치와
명확히 구분하며 실제 거주지 자격은 공식 원문에서 확인해야 한다.

지역 계층은 양방향 발견 규칙을 사용한다. 사용자가 시·군·구를 선택하면 그
지역에 직접 지정된 정책과 상위 시·도 정책을 함께 반환한다. 사용자가 광역
시·도를 선택하면 해당 광역 지역에 직접 지정된 정책뿐 아니라 하위 시·군·구에
지정된 정책도 반환한다. 단, 하위 한 지역의 `exclude` 규칙만으로 광역 전체를
제외하지 않는다.

검색 관련도가 같으면 요청 지역에 직접 적용되는 좁은 범위 정책을 여러 지역을
열거한 정책, 전국 정책, 지역 미확정 정책보다 먼저 정렬한다.

### 응답

```json
{
  "total": 1,
  "page": 1,
  "limit": 20,
  "interpreted_conditions": {
    "q_raw": "천안 사는 27살 청년 단기숙소 지원 받을 수 있나?",
    "q_clean": "천안 사는 27살 청년 단기숙소 지원 받을 수 있나?",
    "conditions": [
      {
        "dimension": "age",
        "value": 27,
        "source": "q",
        "resolution": "resolved",
        "candidates": []
      },
      {
        "dimension": "category",
        "value": "housing",
        "source": "q",
        "resolution": "resolved",
        "candidates": []
      },
      {
        "dimension": "keyword",
        "value": "단기숙소",
        "source": "q",
        "resolution": "resolved",
        "candidates": []
      },
      {
        "dimension": "region",
        "value": "충청남도 천안시",
        "source": "q",
        "resolution": "resolved",
        "candidates": ["충청남도 천안시"]
      }
    ],
    "override_fields": [],
    "uninterpreted_terms": ["청년", "지원"]
  },
  "items": [
    {
      "policy": {
        "schema_version": "1.2.0",
        "id": 1,
        "title": "청년단기숙소 지원사업"
      },
      "verdicts": {
        "region": "match",
        "age": "match",
        "category": "match",
        "status": null
      },
      "unconfirmed_conditions": [],
      "reason_codes": ["AGE_MATCH", "CATEGORY_MATCH", "REGION_MATCH"],
      "message": "청년단기숙소 지원사업 - 판정 완료",
      "score": 15.0,
      "unknown_count": 0
    }
  ]
}
```

### 자연어 term 결합과 관련도

- `사는`, `받을`, `수`, `있나`처럼 검색 대상을 특정하지 않는 대화형 filler는
  `uninterpreted_terms`와 검색 후보 조건에서 제외한다. filler만 있고 구조화
  조건·검색 term이 하나도 없으면 `400 Bad Request`를 반환한다.
- `단기숙소`, `월세`, `적금`처럼 category를 구조화하는 구체 표현은 같은
  `source="q"`의 `keyword` 조건으로도 보존한다. 명시적 `keyword`가 있으면
  기존 override 규칙에 따라 자연어 keyword를 대체한다.
- 구체 keyword 또는 일반어가 아닌 독립 term이 있으면 각 구체 term은 모두
  정책의 search projection·제목·요약 중 하나에 일치해야 한다. 한 term은 세
  필드 중 하나만 일치해도 된다.
- `청년`, `지원`, `정책`, `사업` 같은 일반 term만 있는 탐색은 기존 발견
  가능성을 위해 term 중 하나가 일치하는 후보를 허용한다.
- 이 규칙은 후보 집합만 제한한다. 최종 결정적 정렬은 `score DESC`, 지역
  직접성·적용 범위, `unknown_count ASC`, 상태, `policy.id ASC` 순서다.
- `sort=title_*`는 한국어 제목, `deadline_*`는 신청 종료일,
  `collected_*`는 수집 시각을 기준으로 정렬한다. 마감일 미확정 정책은
  `deadline_asc`와 `deadline_desc` 모두 확정 날짜 뒤에 두고, 모든 모드에서
  최종 identity tie-break를 적용한다.

## 정책 목록

```http
GET /api/v1/policies
```

### Query

| 이름 | 타입 | 기본값 | 규칙 |
| --- | --- | --- | --- |
| `page` | integer | `1` | 1 이상 |
| `limit` | integer | `10` | 1~100 |
| `category` | enum | 없음 | `categories`의 정확한 원소 |
| `region` | string | 없음 | `regions`의 정확한 원소, 1~100자 |
| `status` | enum | 없음 | `open`, `closed`, `scheduled` |
| `include_partial` | boolean | `false` | `true`면 partial 포함 |

`category`는 `housing`, `finance`, `welfare`, `employment`, `startup`,
`education`, `other` 중 하나다. category와 region은 배열 원소의 완전 일치
필터다. 예를 들어 `finance`는 일치하지만 `fin`은 일치하지 않고,
`서울특별시`는 일치하지만 `서울`은 일치하지 않는다. 원문
`category_text`·`region_text`의 부분 문자열 검색은 이 endpoint의 기본 필터가
아니다.

### 응답

```json
{
  "total": 1,
  "page": 1,
  "limit": 10,
  "items": [
    {
      "schema_version": "1.2.0",
      "source_id": "youthcenter-api",
      "source_name": "온통청년 청년정책 API",
      "external_id": "SYN-YOUTH-001",
      "title": "합성 청년 주거 지원",
      "organization": "합성 주거기관",
      "summary": null,
      "category_text": "주거",
      "categories": ["housing"],
      "application_period_text": "2026. 7. 1. ~ 2026. 12. 31.",
      "application_start": "2026-07-01",
      "application_end": "2026-12-31",
      "application_schedule": "fixed_period",
      "application_status": "open",
      "region_text": "서울시",
      "regions": ["서울특별시"],
      "age_min": 19,
      "age_max": 34,
      "age_condition_text": "19세 ~ 34세",
      "eligibility_text": "합성 청년 대상",
      "support_content": "합성 월 지원",
      "application_method": "온라인 신청",
      "education_statuses": [],
      "employment_statuses": [],
      "required_conditions": [],
      "preferred_conditions": [],
      "excluded_conditions": [],
      "source_url": "https://fixture.invalid/youth/001",
      "collected_at": "2026-07-26T06:00:00Z",
      "data_quality_status": "valid",
      "id": 1,
      "created_at": "2026-07-29T00:00:00Z",
      "updated_at": "2026-07-29T00:00:00Z"
    }
  ]
}
```

`total`은 pagination 적용 전 필터 결과 수다. 요청 page가 결과 범위를
벗어나면 `total`은 유지되고 `items`는 빈 배열이다.

`collected_at`, `created_at`, `updated_at`은 timezone-aware date-time이다.
PostgreSQL Session timezone에 따라 같은 절대 시각이 `+00:00` 또는 `+09:00`
등 다른 offset으로 표현될 수 있으므로 소비자는 offset 문자열이 아니라
절대 시각으로 해석한다. 최초 Importer insert에서는 `created_at`과
`updated_at`이 같은 logical write instant이고, unchanged import는 두 값을
보존한다. 실제 update에서도 `updated_at`은 이전 값보다 감소하지 않지만
시스템 시각 역행을 보정한 경우 이전 값과 같을 수 있으므로 strict 증가를
가정하지 않는다.

## 정책 상세

```http
GET /api/v1/policies/{policy_id}
```

| 이름 | 위치 | 타입 | 기본값 | 규칙 |
| --- | --- | --- | --- | --- |
| `policy_id` | path | integer | 없음 | 조회할 DB ID |
| `include_partial` | query | boolean | `false` | partial 상세 허용 |

응답 DTO는 목록의 `items` 원소에 `eligibility_summary`를 추가한
`PolicyDetailRead`다. partial 정책 ID를 기본 요청으로 조회하면 404이며,
`include_partial=true`일 때만 조회할 수 있다. 요약의 배열과 coverage는 항상
존재하고, 내부 Raw provenance는 포함하지 않는다.

## 오류

| 상태 | 조건 | 응답 기준 |
| --- | --- | --- |
| `404` | ID가 없거나 요청 품질 범위에서 숨겨짐 | `{"detail":"Policy not found"}` |
| `422` | page·limit 범위, category·status enum 또는 query 타입 위반 | FastAPI validation 오류 |
| `500` | 처리되지 않은 서버 오류 | 내부 상세를 제외한 공통 오류 응답 |

404는 실제 ID 부재와 품질 정책에 따른 비노출을 구분하지 않는다.
422는 query뿐 아니라 `policy_id` path 타입 위반에도 같은 FastAPI validation
오류 형식을 사용하며 최상위 `detail`은 오류 object의 배열이다.

처리되지 않은 서버 오류의 공개 응답은 다음과 같다. 예외 메시지, DB 정보와
내부 stack trace는 응답에 포함하지 않는다.

```json
{
  "error": {
    "message": "Internal Server Error",
    "details": {}
  }
}
```

## 저장·검색 경계

- Normalized 1.2.0의 37개 논리 필드와 현재 DB 저장 필드의 전환 관계는
  [Policy 데이터베이스 매핑](../architecture/policy_database_mapping.md)을
  따른다.
- PostgreSQL category·region 필터는 JSONB `@>` 연산자를 사용해 배열 원소를
  정확히 검색하고 기존 GIN index와 호환된다.
- SQLite는 운영 대체 DB가 아니라 단위 테스트 경계이며 `json_each`로 같은
  원소 일치 의미를 검증한다.
- 자유 키워드, 원문 부분 문자열, 정렬 선택과 추천은 이 계약 범위가 아니다.
- `provenance`는 DB에 보존하지만 목록·상세 공개 DTO에서 제외한다.
- `keywords`, `life_stages`, `target_groups`, `coverage_scope`, `region_rules`는
  검색 내부 계약이며 이 기존 목록·상세 DTO에는 추가하지 않는다.
- `eligibility_summary`는 PostgreSQL JSONB에 저장하며 상세 DTO에만 노출한다.
  목록·검색 응답에는 포함하지 않는다.

## Frontend D6 인계

### TypeScript 기준

Frontend의 사용자 정책 화면은 canonical Seed의 `NormalizedProgram`이 아니라
아래 공개 API DTO를 기준으로 타입을 정의한다. 모든 key는 응답에 존재하며
선택 단일 값만 `null`일 수 있다. 배열은 값이 없어도 `[]`다.

```typescript
export type PolicyCategory =
  | 'housing'
  | 'finance'
  | 'welfare'
  | 'employment'
  | 'startup'
  | 'education'
  | 'other';

export type ApplicationSchedule =
  | 'fixed_period'
  | 'always'
  | 'until_budget_exhausted';

export type ApplicationStatus = 'open' | 'closed' | 'scheduled';
export type PublicDataQualityStatus = 'valid' | 'partial';

export interface PolicyDto {
  schema_version: '1.0.0' | '1.1.0' | '1.2.0';
  source_id: string;
  source_name: string;
  external_id: string | null;
  title: string;
  organization: string | null;
  summary: string | null;
  category_text: string | null;
  categories: PolicyCategory[];
  application_period_text: string | null;
  application_start: string | null;
  application_end: string | null;
  application_schedule: ApplicationSchedule | null;
  application_status: ApplicationStatus | null;
  region_text: string | null;
  regions: string[];
  age_min: number | null;
  age_max: number | null;
  age_condition_text: string | null;
  eligibility_text: string | null;
  support_content: string | null;
  application_method: string | null;
  education_statuses: string[];
  employment_statuses: string[];
  required_conditions: string[];
  preferred_conditions: string[];
  excluded_conditions: string[];
  source_url: string;
  collected_at: string;
  data_quality_status: PublicDataQualityStatus;
  id: number;
  created_at: string;
  updated_at: string;
}

export interface PolicyListResponse {
  total: number;
  page: number;
  limit: number;
  items: PolicyDto[];
}

export interface EligibilityEvidenceDto {
  source_id: string;
  source_url: string;
  collected_at: string;
  locator_type: 'source_field' | 'css_selector';
  locator: string;
}

export interface EligibilityConditionDto {
  category:
    | 'age' | 'region' | 'income' | 'asset' | 'employment'
    | 'education' | 'housing' | 'household' | 'other';
  text: string;
  evidence: EligibilityEvidenceDto[];
}

export interface EligibilityDocumentDto {
  text: string;
  evidence: EligibilityEvidenceDto[];
}

export interface InstitutionalContactDto {
  kind: 'phone' | 'official_channel';
  label: string;
  value: string;
  evidence: EligibilityEvidenceDto[];
}

export interface EligibilitySummaryDto {
  coverage: 'complete' | 'partial' | 'unknown';
  requirements: EligibilityConditionDto[];
  exclusions: EligibilityConditionDto[];
  preferences: EligibilityConditionDto[];
  documents: EligibilityDocumentDto[];
  unknowns: EligibilityConditionDto[];
  institutional_contacts: InstitutionalContactDto[];
}

export interface PolicyDetailDto extends PolicyDto {
  eligibility_summary: EligibilitySummaryDto;
}
```

`PolicyDto`에는 `provenance`와 `invalid` 품질 상태가 없다. 상세 route와
React key는 nullable `external_id`나 source 조합이 아니라 API가 반환한 숫자
`id`를 사용한다. 상세 route는 `PolicyDetailDto`를 사용하며 목록 DTO에
`eligibility_summary`를 역으로 추가하지 않는다.

### API Client 전환 기준

```typescript
const list = await apiClient.get<PolicyListResponse>(
  '/api/v1/policies',
  {
    params: {
      page: 1,
      limit: 10,
      include_partial: false,
    },
  },
);

const detail = await apiClient.get<PolicyDto>(
  `/api/v1/policies/${policyId}`,
  {
    params: {
      include_partial: false,
    },
  },
);
```

- 목록 응답은 배열이 아니라 `total`, `page`, `limit`, `items` envelope다.
- 상세 endpoint는 `/api/v1/policies/{policy_id}`이며 `policy_id`는 DB 숫자
  ID다.
- `/api/v1/programs`와 source/external ID 조합 상세 endpoint는 구현돼 있지
  않다.
- `include_partial`의 기본값은 `false`다. partial 화면을 제공할 때 목록과
  상세 요청에 같은 값을 전달한다.
- 현재 API에는 자유 키워드·연령 query가 없다. Mock 전용 로컬 검색을 실제
  API 필터처럼 간주하지 않는다.

### Mock → API 전환

canonical Seed 4건을 Mock 사례로 사용할 수 있지만 다음 변환이 필요하다.

1. 일반 사용자 DTO에 없는 `provenance`를 제거한다.
2. 각 객체에 안정적인 양의 `id`와 timezone-aware `created_at`,
   `updated_at`을 추가한다.
3. 기본 목록은 `data_quality_status === "valid"`인 2건만 반환한다.
4. `include_partial=true`에서만 valid·partial 4건을 반환한다.
5. 목록은 `PolicyListResponse` envelope로 감싼다.
6. 상세는 숫자 `id`로 찾고 partial 기본 요청은 404와 같은 비노출 상태로
   처리한다.
7. 상세에만 Seed의 `eligibility_summary`를 추가하고 목록에서는 제거한다.

Frontend 소비 테스트는 최소한 다음 상태를 확인한다.

- loading, 빈 `items`, 404, 422와 500
- nullable 값의 명시적인 fallback과 빈 배열 렌더링
- `application_schedule`과 `application_status`의 구분
- partial 표시와 목록·상세 opt-in 일관성
- timezone offset 문자열이 달라도 같은 instant로 해석
- 공개 응답과 화면 상태에 provenance가 포함되지 않음
- 상세의 Eligibility Summary 7개 필드와 목록 비노출 경계

### 현재 Frontend 소비 경계

Frontend는 공개 `PolicyDto`, `/api/v1/policies`, pagination envelope, 숫자
`id`와 partial opt-in을 타입·API Client·화면에 반영한다.

- 사용자 DTO에서 `provenance`와 `invalid` 제거
- canonical Seed를 공개 DTO로 변환하면서 양의 `id`와 DB 시각 추가
- 기본 valid 2건, `include_partial=true`에서 valid·partial 4건 반환
- 목록·상세가 같은 partial opt-in을 사용하도록 상세 링크 query 유지
- TypeScript 소비 계약 테스트로 목록·상세 경계를 검증

목록 `PolicyDto`는 유지하고 상세 `PolicyDetailDto`에만
`eligibility_summary`를 제공한다. Frontend는 1.2.0 version과 제외 조건·필요
서류·문의처·공개 evidence를 표시한다. 공개 응답에는 내부 `provenance`가 없고
목록에는 상세 자격 요약이 포함되지 않는다.

## 통합 검증

`tests/integration/test_seed_to_policy_api.py`는 canonical Seed 4건을 실제
PostgreSQL에 적재하고 목록·상세 API를 호출해 다음 계약을 검증한다.

- 기본 valid 2건과 `include_partial=true`의 4건
- pagination과 category·region·status의 exact filter
- 목록 공개 필드의 Seed 값 보존, 상세 Eligibility Summary와 provenance 비노출
- partial 상세 opt-in, 404, query·path 422와 내부 상세가 없는 500 응답

테스트는 저장소의 합성 Seed와 로컬 테스트 DB만 사용하며 외부 API를 호출하지
않는다.
