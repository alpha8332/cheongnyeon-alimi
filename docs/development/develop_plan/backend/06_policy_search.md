# Backend 06 Policy Search Forest 개발 계획

## 계획 정보

- 번호: Backend 06
- 담당 영역: Backend
- 상태: draft
- 작업 브랜치: `feature/backend/policy-search`
- 공유 Forest:
  Frontend Policy Search (Frontend 04 초안),
  [Policy Search Data Foundation](../integration/03_policy_search_data_foundation.md),
  [Release Dataset Bootstrap](../data/02_release_dataset_bootstrap.md)
- 선행 Forest:
  [Policy Search Data Foundation](../integration/03_policy_search_data_foundation.md)
- 후속 Forest:
  Integration 04 Real Data Acceptance (`v0.1.0` 실데이터 인수)
- 대상 인계사항: `R1-SEARCH-DATA-SEMANTICS`

## 목적

PostgreSQL 기반 실데이터 정책 검색 Backend 서비스 및 API 계약(W3-B0)을 정의하고 구현하는 백엔드 Forest 계획이다. 한국어 자연어 검색어(`q`) 및 명시적 구조화 필터(지역, 연령, 상태, 카테고리, 키워드)를 결정적 한국어 파싱 규칙으로 처리하여 PostgreSQL search projection을 조회하고, 기존 공개 DTO(`PolicyRead`) 기반의 검색 결과와 판정 코드(`verdicts`), 머신 판독용 이유 코드(`reason_codes`), 미확인 조건(`unconfirmed_conditions`), 4단계 결정적 정렬 및 페이징을 제공하는 검색 API를 완성한다.

## 범위

- Gate G1 승인 검색 API Endpoint 및 Method 스펙 (`GET /api/v1/policies/search`)
- Flat Structure Query Parameter Pydantic 모델 (`q` 공백 제거 1자 이상 필수, 명시적 필터 파라미터 `keyword`, `region`, `age`, `category`, `status`, `include_partial`, `page`, `limit`)
- 자연어 `q` 해석 조건과 명시적 필터 파라미터 간의 Override 규칙
- Region / Age / Status / Category 차원별 3값 (`match | mismatch | unknown`) 판정 규칙
  - Confirmed `mismatch`: 검색 결과에서 DB Level로 항상 확정 제외 (별도 제어 플래그 비제공)
  - `unknown`: 추정 없이 미확인 후보로 결과에 보존·포함 (동일 text relevance를 가진 `match`보다 낮게 정렬)
  - `partial` 정책: 검색 API(`GET /api/v1/policies/search`) 기본값 `include_partial=true`로 후보에 포함 (기존 목록 API `GET /api/v1/policies` 기본값 `false`는 유지)
- 신청 상태 (`status`) 기본 노출 범위 (`open` → `scheduled` → `unknown` 기본 포함; `closed`는 기본 제외하며 명시 요청 시에만 포함)
- 기존 공개 계약 DTO (`policy: PolicyRead`) 재사용 및 검색 메타데이터 (`score`, `verdicts`, `reason_codes`, `message`, `unconfirmed_conditions`) 추가
- 4단계 결정적 정렬 규칙 (`score DESC` ➔ `unknown_count ASC` ➔ `status 우선순위` ➔ `policy.id ASC`)
- HTTP 상태 코드 (`400`, `404`, `422`, `500`) 및 빈 결과 (`total: 0`, `items: []`) 응답 구조 명세
- URL Query State 관리 원칙 (사용자 입력과 명시적 필터만 URL에 저장하며 interpreted condition 전체 JSON은 저장하지 않음)
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
- Gate G1 인수인계 통합안 검토 및 승인 대기

## 공통 설계 원칙

- **PostgreSQL 전용 검색**: 사용자 검색 시 외부 API를 호출하지 않으며 PostgreSQL DB Search Projection만 조회한다.
- **단일 파싱 기준**: Backend가 자연어 파싱 및 구조화 조건 결정의 단일 정본 기준이며 Frontend 전용 파서를 두지 않는다.
- **`q` 필수 및 Flat 구조**: `GET /api/v1/policies/search` 요청의 `q` 파라미터는 공백 제거(`q.strip()`) 후 최소 1자 이상 필수이며, 누락 시 `422 Unprocessable Entity`를 반환한다.
- **명시 필터 Override**: 쿼리 파라미터로 명시 전달된 `region`, `age`, `category`, `status` 등은 `q`에서 해석된 동등 차원의 조건을 덮어쓴다.
- **3값 판정 및 Partial 보존**: Confirmed `mismatch`는 DB level에서 항상 제외하고, `unknown`은 포함하되 match보다 낮게 정렬한다. 복지로 표본 보존을 위해 검색 API의 `include_partial` 기본값은 `true`로 설정한다.
- **기존 공개 DTO 재사용**: 검색 결과 아이템은 기존 정책 DTO인 `policy: PolicyRead`를 100% 재사용하여 하위 호환성을 유지한다.

## Slice 계획

### W3-B0 - 검색 API 및 Repository 계약 초안 작성

- 상태: in-progress
- 목적: Gate G1 승인을 위한 W3-B0 검색 Request/Response DTO, 3값 판정 규칙 및 API 스펙 초안 작성
- 산출물:
  - `docs/development/develop_plan/backend/06_policy_search.md` 개발 계획 및 W3-B0 계약 초안
  - Gate G1 통합안 스펙 명세
- 완료 기준:
  - Backend·Frontend·Data 3자 검토 가능한 스펙 완성 및 `W3-B0_READY` 보고 준비

### B1 - 자연어 해석 및 규칙 기반 구조화 서비스 구현

- 상태: draft
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
- 완료 기준: Request 검증, `q` 검증, PolicyRead 감싸기 Response 직렬화, HTTP `422`, `500` 예외 처리 및 OpenAPI 문서 갱신

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
class PolicySearchQueryParams(BaseModel):
    q: str = Field(..., description="자연어 검색어 (공백 제거 후 1자 이상 필수, 미입력 시 422 반환)")
    keyword: str | None = Field(default=None, description="명시적 키워드 필터 (q의 키워드 조건 override)")
    region: str | None = Field(default=None, description="명시적 지역 코드/이름 (q의 지역 조건 override)")
    age: int | None = Field(default=None, ge=0, le=150, description="명시적 만 연령 (q의 연령 조건 override)")
    category: PolicyCategory | None = Field(default=None, description="명시적 정책 카테고리 (q의 카테고리 override)")
    status: ApplicationStatus | None = Field(default=None, description="신청 상태 필터 (open, scheduled, closed)")
    include_partial: bool = Field(default=True, description="partial 데이터 포함 여부 (검색 API 기본값: true)")
    page: int = Field(default=1, ge=1, description="페이지 번호")
    limit: int = Field(default=20, ge=1, le=100, description="페이지당 결과 수")
```

### 3. Response DTO (`PolicySearchResponse`)

```python
class DimensionVerdicts(BaseModel):
    region: Literal["match", "mismatch", "unknown"]
    age: Literal["match", "mismatch", "unknown"]
    status: Literal["match", "mismatch", "unknown"]
    category: Literal["match", "mismatch", "unknown"]

class UnconfirmedCondition(BaseModel):
    field: str
    reason: str

class PolicySearchResultItem(BaseModel):
    policy: PolicyRead  # 기존 공개 정책 DTO 100% 재사용
    score: float = Field(..., description="검색 관련도 점수")
    verdicts: DimensionVerdicts = Field(..., description="차원별 match/mismatch/unknown 판정")
    reason_codes: list[str] = Field(default_factory=list, description="머신 판독용 이유 코드 목록 (예: ['REGION_MATCH', 'AGE_MATCH'])")
    message: str = Field(..., description="사용자 표시용 조건 판정 요약 메시지")
    unconfirmed_conditions: list[UnconfirmedCondition] = Field(default_factory=list, description="원문 데이터 미비로 인한 unknown 설명 목록")

class InterpretedConditions(BaseModel):
    q_raw: str
    q_clean: str
    interpreted_keywords: list[str]
    interpreted_region: str | None
    interpreted_age: int | None
    interpreted_category: PolicyCategory | None
    interpreted_status: ApplicationStatus | None
    override_fields: list[str] = Field(default_factory=list, description="명시적 필터 파라미터로 override된 차원 목록")

class PolicySearchResponse(BaseModel):
    total: int
    page: int
    limit: int
    interpreted_conditions: InterpretedConditions
    items: list[PolicySearchResultItem]
```

### 4. 3값 판정, Partial 처리 및 정렬 세부 규칙

- **`q` 검증**: 자연어 검색 필수 endpoint이므로 `q`는 `q.strip()` 처리 후 1자 이상이어야 함. 미입력 또는 빈 공백인 경우 `422 Unprocessable Entity`를 반환함.
- **Confirmed `mismatch`**: 지역, 연령, 상태 조건이 명확히 불일치하는 정책은 DB Query level에서 항상 확정 제외함 (별도 `include_mismatch` 플래그 비제공).
- **`unknown` 처리**: 원문 데이터 부족으로 판단이 불가능한 차원은 제외하지 않고 미확인 후보로 결과에 포함하되, 동일 text relevance를 가진 `match` 항목보다 나중에 정렬함 (`unknown 수 ASC`).
- **`include_partial` 기본값**: 복지로 수집 표본 10건이 모두 `partial` 데이터이므로, 검색 API (`GET /api/v1/policies/search`)의 기본값은 `true`로 설정함 (기존 목록 API `GET /api/v1/policies` 기본값 `false`는 유지).
- **신청 상태 기본 노출**: `open` → `scheduled` → `unknown` 상태 정책을 기본 노출하며, `closed` (마감) 정책은 기본 제외하고 명시 요청(`status=closed` 등) 시에만 포함함.
- **최종 4단계 결정적 정렬**:
  1. `score DESC` (관련도 점수 내림차순)
  2. `unknown 수 ASC` (unknown 판정 차원 개수 오름차순)
  3. `status 우선순위` (`open` > `scheduled` > `unknown` > `closed`)
  4. `policy.id ASC` (결정적 tie-breaker)
- **URL Query State 관리**: Frontend 및 URL에는 사용자가 직접 입력한 파라미터(`q`, `region`, `age` 등)만 보존하며, Backend 응답인 `interpreted_conditions` 전체 JSON을 URL state로 저장하지 않음.

### 5. 오류 및 예외 처리

- `422 Unprocessable Entity`: `q` 누락/빈문자열, 파라미터 범위 위반(page < 1, limit < 1 등), Enum 타입 불일치 시 상세 Pydantic validation error 구조 반환
- `200 OK (Empty)`: 정상 파싱되었으나 검색 조건 충족 정책이 없는 경우 `total: 0`, `items: []` 반환
- `400 Bad Request`: 잘못된 쿼리 구문 또는 미지원 필터 조합 요청 시
- `404 Not Found`: 검색 자원 또는 올바르지 않은 API 버전 경로 요청 시
- `500 Internal Server Error`: DB 연결 실패 또는 서버 예외 발생 시 표준 Error DTO 반환

---

## 검증 계획

- `python scripts/validate_docs.py`: 문서 구문, 내부 상대 링크 및 거버넌스 규칙 검증
- `git diff --check`: 트레일링 공백 및 개행 검증
- `git status --short`: 임시 산출물 및 불필요 파일 비생성 검증

## Forest 완료 기준

- Backend 06 계획 문서(`06_policy_search.md`) G1 통합안 반영 작성 및 문서 색인 등록
- W3-B0 계약 초안 및 Gate G1 제출용 준비 완료 (`W3-B0_READY`)
- `python scripts/validate_docs.py` 통과

## 위험과 미확정 사항

1. 자연어 검색어 `q`에서 행정구역명을 유도할 때 법정동 계층(시/도 vs 시/군/구) 매핑 정확도 범위
2. `GET /api/v1/policies/search` 쿼리 파라미터 중 `category` 다중 선택 지원 여부 (v0.1.0은 단일 category 우선 지원)

## 관련 문서

- [3주차 검색 계약 Gate G1 인수인계](../../weekly_plan/week_03_search_contract_handoff.md)
- [Policy Search Data Foundation Forest 개발 계획](../integration/03_policy_search_data_foundation.md)
- [Policy API 계약](../../../api/policies.md)
- [Policy DB 매핑](../../../architecture/policy_database_mapping.md)
