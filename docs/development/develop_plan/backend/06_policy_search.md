# Backend 06 Policy Search Forest 개발 계획

## 계획 정보

- 번호: Backend 06
- 담당 영역: Backend
- 상태: approved
- 승인: Gate G1 (`2026-08-04`)
- 작업 브랜치: `feature/backend/policy-search`
- 현재 Slice: B1 pending (W3-B0 completed)
- 공유 Forest:
  Frontend Policy Search (Frontend 04 초안),
  [Policy Search Data Foundation](../integration/03_policy_search_data_foundation.md),
  [Release Dataset Bootstrap](../data/02_release_dataset_bootstrap.md)
- 선행 Forest:
  [Policy Search Data Foundation](../integration/03_policy_search_data_foundation.md)
- 후속 Forest:
  Integration 04 Real Data Acceptance (`v0.1.0` 실데이터 인수)
- 대상 인계사항: `R1-SEARCH-IMPLEMENTATION`

## 목적

PostgreSQL 기반 실데이터 정책 검색 Backend 서비스 및 API 계약(W3-B0)을 정의하고 구현하는 백엔드 Forest 계획이다. 한국어 자연어 검색어(`q`) 및 명시적 구조화 필터(지역, 연령, 상태, 카테고리, 키워드)를 결정적 한국어 파싱 규칙으로 처리하여 PostgreSQL search projection을 조회하고, 기존 공개 DTO(`PolicyRead`) 기반의 검색 결과와 Nullable 4차원 판정 코드(`verdicts`), 머신 판독용 미확인 이유 코드(`unconfirmed_conditions`), 4단계 결정적 정렬 및 페이징을 제공하는 검색 API를 완성한다.

## 범위

- Gate G1 승인 검색 API Endpoint 및 Method 스펙 (`GET /api/v1/policies/search`)
- Flat Structure Query Parameter Pydantic 모델 (`q` 공백 제거 후 1자 이상 200자 이하 필수, 명시적 필터 파라미터 `keyword`[100자], `region`[100자], `age`, `category`, `status`, `include_partial`, `page`, `limit`)
- 자연어 `q` 해석 조건과 명시적 필터 파라미터 간의 Override 규칙 (`explicit` 파라미터가 `q`에서 해석된 동일 차원 조건을 override)
- Region / Age / Status / Category 차원별 Nullable 4값 (`match | mismatch | unknown | null`) 판정 규칙
  - `null`: 해당 차원이 검색 조건에 적용되지 않음
  - `unknown`: 조건은 적용됐지만 정책 데이터에 판정 근거가 없음 (partial/missing)
  - `unknown_count`: `null`을 제외하고 `unknown`인 차원의 개수
  - Confirmed `mismatch`: 검색 결과에서 DB Level로 항상 확정 제외 (별도 제어 플래그 비제공)
  - `include_partial` 정책: 검색 API (`GET /api/v1/policies/search`) 기본값 `include_partial=true`로 후보에 포함 (기존 목록 API `GET /api/v1/policies` 기본값 `false`는 유지)
- 자연어 해석 결과 응답 구조 (`interpreted_conditions`: `q_raw`, `q_clean`, `conditions[]`, `override_fields[]`, `uninterpreted_terms[]`)
- 해석 오류 및 에러 응답 규격:
  - 명시적 `region`이 `unmapped` 또는 `ambiguous`: `400 Bad Request`
  - `q`에서 추출한 `region`이 `unmapped` 또는 `ambiguous`: 임의 선택 없이 해석 경고 및 candidate로 반환
  - 사용할 수 있는 검색 term이 전혀 없음: `400 Bad Request`
  - 정상 해석되었으나 결과가 없음: `200 OK`, `total=0`, `items=[]` (404가 아님)
  - `400`/`404`: `{"error":{"message":"...","details":{...}}}`
  - `422`: FastAPI validation `detail[]`
  - `500`: 내부 정보 제거 공통 오류 응답
- 미확인 조건 객체 배열 (`unconfirmed_conditions[]`: `field`, `reason_code`, `message`) 및 확장 가능한 `reason_codes` 목록 명세
- `score` 계약 (Backend 내부 ranking float, 높을수록 관련도 높음, 요청간 비교 불가, Release 1 UI 미노출)
- 기존 공개 계약 DTO (`policy: PolicyRead`) 재사용 및 검색 메타데이터 추가
- 4단계 결정적 정렬 규칙 (`score DESC` ➔ `unknown_count ASC` ➔ `status 우선순위` ➔ `policy.id ASC`)
- `total` 정의 (pagination 적용 전 필터링 결과 수)
- URL Query State 관리 원칙 (사용자 입력과 명시적 필터만 URL에 저장)
- 기존 목록·상세 API (`/api/v1/policies`) 호환성 보존
- PostgreSQL index & query plan 재검토 및 통합 테스트

## 범위 밖

- Frontend UI 화면 및 React 검색 컴포넌트 (Frontend 04 담당)
- 사용자 검색 시점에 외부 Source API 직접 호출 (Collector/Data 담당)
- LLM 및 벡터 DB 검색 (`v0.1.0` 필수 범위 밖)
- 임의의 Schema, Fixture, Seed, DB Enum 변경

## 선행 조건

- Integration 03 (Policy Search Data Foundation) 완료
- `week_03_search_contract_handoff.md` 공통 커밋 기준 분기
- Gate G1 인수인계 통합안 승인 완료 (`2026-08-04`)

## 공통 설계 원칙

- **PostgreSQL 전용 검색**: 사용자 검색 시 외부 API를 호출하지 않으며 PostgreSQL DB Search Projection만 조회한다.
- **단일 파싱 기준**: Backend가 자연어 파싱 및 구조화 조건 결정의 단일 정본 기준이며 Frontend 전용 파서를 두지 않는다.
- **`q` 필수 및 Flat 구조**: `GET /api/v1/policies/search` 요청의 `q` 파라미터는 공백 제거(`q.strip()`) 후 최소 1자 이상 필수(최대 200자)이며, 미입력/빈 값 시 `422 Unprocessable Entity`를 반환한다.
- **명시 필터 Override**: 쿼리 파라미터로 명시 전달된 `region`, `age`, `category`, `status`, `keyword` 등은 `q`에서 해석된 동등 차원의 조건을 덮어쓴다.
- **Nullable 4값 판정 및 Partial 보존**: Confirmed `mismatch`는 DB level에서 항상 제외하고, `unknown`은 포함하되 match보다 낮게 정렬한다. 적용되지 않은 차원은 `null`로 표현한다. 복지로 표본 보존을 위해 검색 API의 `include_partial` 기본값은 `true`로 설정한다.
- **기존 공개 DTO 재사용**: 검색 결과 아이템은 기존 정책 DTO인 `policy: PolicyRead`를 100% 재사용하여 하위 호환성을 유지한다.

## Slice 계획

### W3-B0 - 검색 API 및 Repository 계약 초안 작성

- 상태: completed (`2026-08-04`)
- 목적: Gate G1 승인을 위한 W3-B0 검색 Request/Response DTO, 4값(Nullable) 판정 규칙, 해석 경고/오류 처리 및 API 스펙 초안 작성
- 산출물:
  - `docs/development/develop_plan/backend/06_policy_search.md` 개발 계획 및 W3-B0 계약 초안
  - Gate G1 통합안 스펙 명세
- 완료 기준:
  - Backend·Frontend·Data 3자 검토 가능한 스펙 완성 및 `W3-B0_READY` 보고 준비

### B1 - 자연어 해석 및 규칙 기반 구조화 서비스 구현

- 상태: pending (Gate G1 approved)
- 목적: 한국어 자연어 `q` 및 명시적 파라미터를 파싱하고 override 규칙을 적용하는 Service 구현
- 산출물:
  - `backend/app/services/policy_search_parser.py`
  - 파싱 단위 테스트
- 선행 조건: Gate G1 (`G1_APPROVED`) 승인
- 완료 기준: 키워드, 지역, 연령, 상태 조건 파싱 및 override 규칙 정확 적용

### B2 - PostgreSQL 검색 Repository 및 Query Builder 구현

- 상태: draft
- 목적: Search projection 테이블 조회, mismatch 제외, unknown/partial 처리 및 4단계 결정적 정렬 Builder 구현
- 산출물:
  - `backend/app/repositories/policy_search_repository.py`
  - Repository 단위 및 통합 테스트
- 선행 조건: B1 완료
- 완료 기준: `score DESC` ➔ `unknown_count ASC` ➔ `status` ➔ `policy.id ASC` 정렬 및 PostgreSQL query plan 정상 동작

### B3 - Policy Search API Endpoint 및 DTO 구현

- 상태: draft
- 목적: `GET /api/v1/policies/search` Endpoint 및 Pydantic DTO, 예외 처리 핸들러 구현
- 산출물:
  - `backend/app/api/v1/endpoints/policy_search.py`
  - `backend/app/schemas/policy_search.py`
  - API Endpoint 테스트
- 선행 조건: B2 완료
- 완료 기준: Request 검증, `q` 검증, PolicyRead 감싸기 Response 직렬화, HTTP `400`, `422`, `500` 예외 처리 및 OpenAPI 문서 갱신

### B4 - PostgreSQL 통합, 정렬/페이징 & API 호환성 검증

- 상태: draft
- 목적: 실제 PostgreSQL 적재 데이터 대상 전체 통합 테스트 및 기존 API 호환성 검증
- 산출물:
  - 통합 테스트 스위트 및 Backend 개발 기록 `docs/development/development_notes/backend/policy_search.md`
- 선행 조건: B3 완료
- 완료 기준: 회귀 테스트 통과, 문서 검증(`validate_docs.py`) 통과 및 `v0.1.0` 검색 준비 완료

---

## W3-B0 계약 초안 (Gate G1 제출용)

### 1. 검색 API Endpoint & Method

- **Endpoint**: `GET /api/v1/policies/search`
- **호출 구조**: Flat Query Parameters (`q`, `keyword`, `region`, `age`, `category`, `status`, `include_partial`, `page`, `limit`)

### 2. Request Query Parameters (`PolicySearchQueryParams`)

```python
from pydantic import BaseModel, Field
from app.schemas.policy import ApplicationStatus, PolicyCategory

class PolicySearchQueryParams(BaseModel):
    q: str = Field(
        ...,
        description="자연어 검색어 (공백 제거 후 1자 이상 필수, 권장 최대 200자, 미입력/빈값 시 422 반환)",
        max_length=200
    )
    keyword: str | None = Field(
        default=None,
        description="명시적 키워드 필터 (q의 키워드 조건 override, 권장 최대 100자)",
        max_length=100
    )
    region: str | None = Field(
        default=None,
        description="명시적 지역 alias/name 문자열 (q의 지역 조건 override, 권장 최대 100자)",
        max_length=100
    )
    age: int | None = Field(
        default=None,
        ge=0,
        le=150,
        description="명시적 만 연령 (q의 연령 조건 override)"
    )
    category: PolicyCategory | None = Field(
        default=None,
        description="명시적 정책 카테고리 (q의 카테고리 override)"
    )
    status: ApplicationStatus | None = Field(
        default=None,
        description="신청 상태 필터 (open, scheduled, closed)"
    )
    include_partial: bool = Field(
        default=True,
        description="partial 데이터 포함 여부 (검색 API 기본값: true)"
    )
    page: int = Field(default=1, ge=1, description="페이지 번호")
    limit: int = Field(default=20, ge=1, le=100, description="페이지당 결과 수")
```

### 3. Response DTO (`PolicySearchResponse`)

```python
from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.policy import PolicyRead

SearchDimension = Literal["keyword", "region", "age", "category", "status"]

class ConditionItem(BaseModel):
    dimension: SearchDimension = Field(
        ..., description="해석된 차원 종류"
    )
    value: str | int = Field(..., description="추출 또는 명시 지정된 차원 값")
    source: Literal["q", "explicit"] = Field(
        ..., description="조건 출처 (q: 자연어 파싱, explicit: 명시적 쿼리 파라미터)"
    )
    resolution: Literal["resolved", "unmapped", "ambiguous"] = Field(
        ..., description="해석 결과 상태"
    )
    candidates: list[str] = Field(
        default_factory=list, description="매핑 후보 문자열 리스트 (ambiguous/unmapped 시 대안 제공)"
    )

class InterpretedConditions(BaseModel):
    q_raw: str = Field(..., description="사용자가 입력한 원본 자연어 검색어")
    q_clean: str = Field(..., description="전처리 및 공백 정리된 검색어")
    conditions: list[ConditionItem] = Field(
        default_factory=list, description="차원별 상세 해석 조건 목록"
    )
    override_fields: list[SearchDimension] = Field(
        default_factory=list, description="명시적 필터 파라미터로 override된 차원 이름 목록"
    )
    uninterpreted_terms: list[str] = Field(
        default_factory=list, description="구조화 조건으로 해석되지 않은 독립 단어/토큰 목록"
    )

class DimensionVerdicts(BaseModel):
    region: Literal["match", "mismatch", "unknown"] | None = Field(
        default=None, description="지역 판정 (null: 차원 미적용, match: 부합, mismatch: 불일치, unknown: 데이터 부족)"
    )
    age: Literal["match", "mismatch", "unknown"] | None = Field(
        default=None, description="연령 판정 (null: 차원 미적용, match: 부합, mismatch: 불일치, unknown: 데이터 부족)"
    )
    status: Literal["match", "mismatch", "unknown"] | None = Field(
        default=None, description="신청상태 판정 (null: 차원 미적용, match: 부합, mismatch: 불일치, unknown: 데이터 부족)"
    )
    category: Literal["match", "mismatch", "unknown"] | None = Field(
        default=None, description="카테고리 판정 (null: 차원 미적용, match: 부합, mismatch: 불일치, unknown: 데이터 부족)"
    )

class UnconfirmedCondition(BaseModel):
    field: str = Field(..., description="미확인 차원/필드명 (예: 'region', 'age')")
    reason_code: str = Field(..., description="확장 가능한 머신 판독용 미확인 사유 코드")
    message: str = Field(..., description="사용자 표시용 설명 메시지")

class PolicySearchResultItem(BaseModel):
    policy: PolicyRead  # 기존 공개 정책 DTO 100% 재사용
    score: float = Field(
        ...,
        description="Backend 내부 ranking 점수 (높을수록 관련도 높음, 다른 요청 간 점수 비교 불가, Release 1 UI 미표시)"
    )
    verdicts: DimensionVerdicts = Field(
        ..., description="차원별 match/mismatch/unknown/null 판정"
    )
    unknown_count: int = Field(
        ..., description="verdicts 중 null을 제외하고 unknown인 차원의 개수"
    )
    reason_codes: list[str] = Field(
        default_factory=list, description="머신 판독용 판정 이유 코드 목록 (예: ['REGION_MATCH', 'AGE_UNKNOWN'])"
    )
    message: str = Field(..., description="사용자 표시용 조건 판정 요약 메시지")
    unconfirmed_conditions: list[UnconfirmedCondition] = Field(
        default_factory=list, description="원문 데이터 미비로 인한 unknown 설명 목록"
    )

class PolicySearchResponse(BaseModel):
    total: int = Field(..., description="pagination 적용 전 필터링 조건을 만족하는 총 결과 수")
    page: int = Field(..., description="현재 페이지 번호")
    limit: int = Field(..., description="페이지당 결과 수")
    interpreted_conditions: InterpretedConditions = Field(..., description="자연어 및 명시 필터 해석 메타데이터")
    items: list[PolicySearchResultItem] = Field(default_factory=list, description="검색 결과 정책 목록")
```

### 4. `reason_code` 및 `unconfirmed_conditions` 코드 체계

`unconfirmed_conditions` 및 `reason_codes`는 머신 판독 및 사용자 안내를 위한 확장 가능한 문자열 코드 체계다. **기존 등록된 코드의 의미는 변경하지 않으며(하위 호환성 유지), 필요 시 새 코드를 추가 확정하는 규칙**을 따른다.

query-level 해석 경고와 row-level 정책 근거 부족은 서로 다른 위치에 둔다.
자연어 해석의 `unmapped`·`ambiguous`는
`interpreted_conditions.conditions[]`의 `resolution`·`candidates`로 전달하고,
`items[].unconfirmed_conditions[]`는 개별 정책의 지역·연령·상태·카테고리
근거가 부족한 경우에만 사용한다. top-level `unconfirmed_conditions`는
추가하지 않는다.

| reason_code | 대기 차원/필드 | 의미 및 설명 |
| --- | --- | --- |
| `DATA_MISSING_REGION` | `region` | 정책 원문에 지역 제한 근거 데이터가 누락되어 판단 불가 (`unknown`) |
| `DATA_MISSING_AGE` | `age` | 정책 원문에 연령 제한 근거 데이터가 누락되어 판단 불가 (`unknown`) |
| `DATA_MISSING_STATUS` | `status` | 정책 원문에 신청 기간/상태 근거 데이터가 누락되어 판단 불가 (`unknown`) |
| `DATA_MISSING_CATEGORY` | `category` | 정책 원문에 카테고리 분류가 명확하지 않아 판단 불가 (`unknown`) |
| `PARTIAL_POLICY_DATA` | `general` | partial 품질 등급 정책으로 일부 차원 판정이 유보됨 |
| `REGION_AMBIGUOUS_PARSED` | `region` | 자연어 `q`에서 추출된 지역명이 다의적이거나 모호하여 후보 제공 |
| `REGION_UNMAPPED_PARSED` | `region` | 자연어 `q`에서 추출된 지역명이 기준 행정구역에 매핑되지 않음 |

### 5. 3값/4값 판정, Partial 처리 및 정렬 세부 규칙

- **`q` 검증**: 자연어 검색 필수 endpoint이므로 `q`는 `q.strip()` 처리 후 1자 이상 200자 이하이어야 함. 미입력 또는 빈 공백인 경우 `422 Unprocessable Entity`를 반환함.
- **명시적 Override**: `keyword`, `region`, `age`, `category`, `status`가 쿼리 파라미터로 직접 전달되면 `source="explicit"`가 되며 `q`에서 파싱된 동일 차원 조건을 덮어씀. (`override_fields`에 기록됨)
- **Confirmed `mismatch`**: 지역, 연령, 상태, 카테고리 조건이 명확히 불일치하는 정책은 DB Query level에서 항상 확정 제외함 (별도 `include_mismatch` 플래그 비제공).
- **`unknown` 및 `null` 처리**:
  - 검색 조건에 포함되지 않은 차원은 `verdicts`의 해당 필드가 `null`이 됨.
  - 검색 조건으로 지정되었으나 정책 원문 데이터 부족으로 판단 불가능한 차원은 `unknown`으로 기록함.
  - `unknown` 차원을 가진 정책은 확정 제외하지 않고 미확인 후보로 결과에 포함하되, 동일 text relevance를 가진 `match` 항목보다 나중에 정렬함 (`unknown_count ASC`).
- **`include_partial` 기본값**: 복지로 수집 표본 10건이 모두 `partial` 데이터이므로, 검색 API (`GET /api/v1/policies/search`)의 기본값은 `true`로 설정함 (기존 목록 API `GET /api/v1/policies` 기본값 `false`는 유지).
- **신청 상태 기본 노출**: `open` → `scheduled` → `application_status=null`
  정책을 기본 노출하며, `closed` (마감) 정책은 기본 제외하고 명시 요청
  (`status=closed` 등) 시에만 포함함. 여기서 null은 정렬을 위한 unknown
  bucket이며 `ApplicationStatus` 또는 DB enum에 `unknown` 값을 추가하지 않는다.
- **score 점수 정의**:
  - Backend 내부 PostgreSQL ranking/relevance 계산값 (float).
  - 높을수록 검색어 및 조건 관련도가 높음을 의미함.
  - 서로 다른 검색 요청 사이의 score 절대값을 직접 비교하는 것은 보장하지 않음.
  - Frontend는 Release 1 사용자 UI에 score 숫자를 직접 노출하지 않고 정렬용 순서로만 활용함.
- **최종 4단계 결정적 정렬**:
  1. `score DESC` (관련도 점수 내림차순)
  2. `unknown_count ASC` (`verdicts` 내 null을 제외한 unknown 차원 개수 오름차순)
  3. `status 우선순위` (`open` > `scheduled` > `null` unknown bucket > `closed`)
  4. `policy.id ASC` (결정적 tie-breaker)
- **`total` 정의**: 페이징(`page`, `limit`)이 적용되기 전, 필터링 조건(`mismatch` 제외, `status` 기본 필터 등)을 충족하는 전체 검색 결과 건수.
- **URL Query State 관리**: Frontend 및 URL에는 사용자가 직접 입력한 파라미터(`q`, `region`, `age` 등)만 보존하며, Backend 응답인 `interpreted_conditions` 전체 JSON을 URL state로 저장하지 않음.

### 6. 해석 오류 의미 및 HTTP 에러 응답 규격

- **해석 오류 처리 규칙**:
  1. **명시적 region 해석 실패**: 명시적 쿼리 파라미터 `region`이 기준 행정구역에 매핑되지 않거나(`unmapped`), 둘 이상의 행정구역으로 모호한 경우(`ambiguous`) ➔ **HTTP `400 Bad Request`** 반환 (`details`에 candidates 또는 error 이유 포함).
  2. **자연어 `q` 추출 region 해석 경고**: `q`에서 파싱된 region이 `unmapped` 또는 `ambiguous`인 경우 ➔ 임의로 단일 지역을 선택하지 않고, **HTTP `200 OK` 응답 내 `interpreted_conditions.conditions[]`의 `resolution="unmapped"`/`"ambiguous"` 및 `candidates[]`로 query-level 경고를 전달**하며 정상 검색 진행. 개별 정책 근거 부족만 `items[].unconfirmed_conditions[]`로 전달함.
  3. **유효한 검색 term 전무**: 자연어 `q`가 무의미한 특수문자/공백으로만 이루어져 파싱된 키워드나 조건이 전혀 없고, 명시적 필터도 지정되지 않은 경우 ➔ **HTTP `400 Bad Request`** 반환.
  4. **검색 결과 없음**: 검색 조건이 정상 해석되었으나 조건을 충족하는 정책이 없는 경우 ➔ HTTP 404가 아닌 **HTTP `200 OK` (`total: 0`, `items: []`)** 반환.
- **HTTP Error Response Models**:
  - **400 Bad Request / 404 Not Found**:
    ```json
    {
      "error": {
        "message": "잘못된 검색 지역 조건입니다.",
        "details": {
          "field": "region",
          "value": "invalid_region_name",
          "resolution": "unmapped"
        }
      }
    }
    ```
  - **422 Unprocessable Entity (FastAPI Standard Validation Error)**:
    ```json
    {
      "detail": [
        {
          "loc": ["query", "q"],
          "msg": "field required",
          "type": "value_error.missing"
        }
      ]
    }
    ```
  - **500 Internal Server Error (공통 서버 오류)**:
    내부 스택트레이스 및 DB 디버그 정보가 제거된 공통 표준 구조 반환:
    ```json
    {
      "error": {
        "message": "서버 내부 오류가 발생했습니다.",
        "details": {}
      }
    }
    ```

---

## 검증 계획

- `python scripts/validate_docs.py`: 문서 구문, 내부 상대 링크 및 거버넌스 규칙 검증
- `git diff --check`: 트레일링 공백 및 개행 검증
- `git status --short`: 임시 산출물 및 불필요 파일 비생성 검증

## Forest 완료 기준

- Backend 06 계획 문서(`06_policy_search.md`) G1 최종 승인안 반영 작성 및 문서 색인 등록
- W3-B0 계약 승인 뒤 B1~B4 parser·Repository·Service·API 구현 완료
- 실제 PostgreSQL 대상 결정적 정렬·pagination·기존 Policy API 회귀 검증 통과
- Backend 단위·통합 테스트와 `python scripts/validate_docs.py` 통과

## 위험과 미확정 사항

DT2B에서 다음과 같이 분류했다.

| 항목 | DT2B 분류 | Release 1 처리 |
| --- | --- | --- |
| 자연어 지역 계층 매핑·ambiguous 후보 정확도 | implementation-risk | 임의 선택 없이 candidates를 반환하고 B1 parser·B4 실제 PostgreSQL 통합에서 검증 |
| `category` 다중 선택 | non-blocking | v0.1.0 request는 단일 `category`로 동결하고 다중 선택은 후속 검토 |

두 항목 모두 G1 승인이나 본 구현 시작을 막지 않는다. 구현 검증이 실패하면
Backend Forest 또는 Integration 04의 Release 1 blocker로 다시 분류한다.

## 관련 문서

- [3주차 검색 계약 Gate G1 인수인계](../../weekly_plan/week_03_search_contract_handoff.md)
- [Policy Search Data Foundation Forest 개발 계획](../integration/03_policy_search_data_foundation.md)
- [Policy API 계약](../../../api/policies.md)
- [Policy DB 매핑](../../../architecture/policy_database_mapping.md)
