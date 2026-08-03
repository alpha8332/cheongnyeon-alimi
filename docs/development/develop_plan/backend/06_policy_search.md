# Backend 06 Policy Search Forest 개발 계획

## 계획 정보

- 번호: Backend 06
- 담당 영역: Backend
- 상태: in-progress
- 작업 브랜치: `feature/backend/policy-search`
- 개발 기록:
  [Backend Policy Search 개발 기록](../../development_notes/backend/policy_search.md)
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

PostgreSQL 기반 실데이터 정책 검색 Backend 서비스 및 API 계약(W3-B0)을 정의하고 구현하는 백엔드 Forest 계획이다. 한국어 자연어 검색어(`q`) 및 구조화 조건(지역, 연령, 상태, 카테고리, 키워드)을 결정적 한국어 규칙으로 파싱·구조화하여 PostgreSQL search projection을 조회하고, 검색 이유(`search_reasons`), 미확인 조건, 페이징 및 유연한 파라미터 호환성을 제공하는 검색 API를 완성한다.

## 범위

- 검색 API Endpoint 및 Method 스펙 (`POST /api/v1/policies/search` 기본 채택, 차후 `GET /api/v1/policies/search` 호환/전환이 용이하도록 DTO 및 Search Service 계층 분리)
- Pydantic Request/Response DTO 정의 (`PolicySearchRequest`, `PolicySearchResponse`, `ParsedSearchConditions`, `SearchReasonItem`, `UnconfirmedConditionItem` 등)
- 자연어 검색어 `q` 및 구조화 필터의 결정적 한국어 파싱 규칙
- Region/Age/Status 3값 (`match | mismatch | unknown`) 판정 규칙
  - Confirmed `mismatch`: 검색 결과에서 확정 제외
  - `unknown`: 추정 없이 미확인 후보로 결과에 보존·포함
  - `partial` 정책: 관련도 감점(penalty) 없이 결과 후보에 포함하되, 응답 DTO에 누락 사유(`missing_fields` / `reasons`)를 포함하여 사용자에게 전달
- 검색 결과 정렬 및 관련도 점수(Relevance score), 결정적 tie-breaker (`id` 오름차순), pagination
- 빈 결과, 해석 실패, 파라미터 검증 오류(`422`), 서버 내부 오류(`500`) DTO 및 HTTP 상태 코드 정의
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
- Backend 파서 및 DTO 설계에 대한 Gate G1 공동 검토 승인

## 공통 설계 원칙

- **PostgreSQL 전용 검색**: 사용자 검색 시 외부 API를 호출하지 않으며 PostgreSQL DB Projection만 조회한다.
- **단일 파싱 기준**: Backend가 자연어 파싱 및 구조화 조건 결정의 단일 정본 기준이며 Frontend 전용 파서를 두지 않는다.
- **API 메서드 유연성**: 복잡한 검색 DTO 및 자연어 교정을 위해 `POST /api/v1/policies/search`를 기본 채택하되, Search Service layer를 독립적으로 유연하게 설계하여 차후 `GET` query parameter 인터페이스 전환이 용이하도록 구현한다.
- **3값 판정 및 Partial 사유 전달**: 확정 불일치(`mismatch`)는 제외하고, `unknown`은 미확인 후보로 포함한다. `partial` 정책은 관련도 감점 없이 포함하되 응답 DTO에 누락 사유(`missing_fields`)를 명시하여 사용자에게 전달한다.

## Slice 계획

### W3-B0 - 검색 API 및 Repository 계약 초안 작성

- 상태: in-progress
- 목적: Gate G1 승인을 위한 W3-B0 검색 Request/Response DTO, 3값 판정 규칙 및 API 스펙 초안 작성
- 산출물:
  - `docs/development/develop_plan/backend/06_policy_search.md` 계획 및 W3-B0 계약 초안
  - Gate G1 공동 결정 필요 항목 정리
- 완료 기준:
  - Backend·Frontend·Data 3자 검토 가능한 스펙 완성 및 `W3-B0_READY` 보고 준비

### B1 - 자연어 해석 및 규칙 기반 구조화 서비스 구현

- 상태: draft
- 목적: 한국어 자연어 `q` 및 전달받은 파라미터를 결정적 규칙으로 파싱하는 Service 구현
- 산출물:
  - `backend/app/services/policy_search_parser.py`
  - 파싱 단위 테스트
- 선행 조건: Gate G1 (`G1_APPROVED`) 승인
- 완료 기준: 키워드, 지역, 연령, 상태 조건이 정확히 판정되고 파싱 실패 시 안전한 fallback 반환

### B2 - PostgreSQL 검색 Repository 및 Query Builder 구현

- 상태: draft
- 목적: Search projection 테이블 조회 및 3값 판정 filter, 정렬, pagination Query Builder 구현
- 산출물:
  - `backend/app/repositories/policy_search_repository.py`
  - Repository 단위 및 통합 테스트
- 선행 조건: B1 완료
- 완료 기준: `mismatch` 제외, `unknown` 보존, `partial` 누락 사유 연결 및 PostgreSQL query plan 정상 동작

### B3 - Policy Search API Endpoint 및 DTO 구현

- 상태: draft
- 목적: `POST /api/v1/policies/search` Endpoint 및 Pydantic DTO, 에러 핸들러 구현
- 산출물:
  - `backend/app/api/v1/endpoints/policy_search.py`
  - `backend/app/schemas/policy_search.py`
  - API Endpoint 테스트
- 선행 조건: B2 완료
- 완료 기준: Request 검증, Response DTO 직렬화, HTTP `422`, `500` 예외 처리 및 OpenAPI 문서 갱신

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

- **기본 Endpoint**: `POST /api/v1/policies/search`
- **유연성 설계**: 서비스 레이어(`PolicySearchService`)의 입력을 독립적인 DTO 객체로 캡슐화하여, 향후 `GET /api/v1/policies/search?q=...&region=...` 형태의 쿼리 스트링 매핑 요청이 오더라도 동일 서비스 로직을 재사용할 수 있도록 작성한다.

### 2. Request DTO (`PolicySearchRequest`)

```python
class PolicySearchRequest(BaseModel):
    q: str | None = Field(default=None, description="자연어 검색어 (예: '서울 동작구 25세 취업준비생 지원금')")
    keyword: str | None = Field(default=None, description="명시적 키워드 필터")
    region_code: str | None = Field(default=None, description="행정구역 코드 (예: '1159000000')")
    age: int | None = Field(default=None, description="사용자 만 연령")
    category: str | None = Field(default=None, description="정책 카테고리")
    status: str | None = Field(default=None, description="신청 상태 (open, scheduled, closed)")
    include_partial: bool = Field(default=True, description="partial 정책 포함 여부 (기본 true)")
    page: int = Field(default=1, ge=1, description="페이지 번호")
    limit: int = Field(default=20, ge=1, le=100, description="페이지당 결과 수")
```

### 3. Response DTO (`PolicySearchResponse`)

```python
class SearchReasonItem(BaseModel):
    field: str  # region, age, status, keyword 등
    status: str  # match, unknown
    message: str  # 예: "연령 조건(만 25세)이 정책 범위(만 19세~34세)에 부합합니다."

class UnconfirmedConditionItem(BaseModel):
    field: str
    reason: str  # 예: "지역 제한 조건이 원문에 명시되지 않아 unknown으로 다룹니다."

class PolicySearchResultItem(BaseModel):
    id: int
    title: str
    summary: str | None
    organization_name: str | None
    region_code: str | None
    region_name: str | None
    min_age: int | None
    max_age: int | None
    application_status: str
    data_quality_status: str  # valid, partial
    missing_fields: list[str] = Field(default_factory=list, description="partial 정책의 정보 누락 사유 목록")
    search_reasons: list[SearchReasonItem]
    unconfirmed_conditions: list[UnconfirmedConditionItem]

class ParsedSearchConditions(BaseModel):
    parsed_keywords: list[str]
    parsed_region_code: str | None
    parsed_age: int | None
    parsed_status: str | None

class PolicySearchResponse(BaseModel):
    total_count: int
    page: int
    limit: int
    parsed_conditions: ParsedSearchConditions
    items: list[PolicySearchResultItem]
```

### 4. 3값 판정, Partial 처리 및 정렬 세부 규칙

- **`mismatch`**: 지역, 연령, 상태 조건이 명확히 불일치하는 정책은 DB Query level에서 확정 제외한다.
- **`unknown`**: 원문 데이터 부족으로 판단이 불가능한 항목은 제외하지 않고 미확인 후보로 검색 결과에 포함하며, `unconfirmed_conditions` 항목에 사유를 명시한다.
- **`partial`**: 온통청년/복지로 수집 표본 중 일부 필수 필드가 누락된 `partial` 데이터는 관련도 감점(penalty) 없이 검색 후보에 포함하되, `missing_fields` 배열(예: `["application_period", "min_age"]`)을 통해 사용자에게 누락 사실만 안내한다.
- **신청 상태 기본 정렬**: `open` (모집중) > `scheduled` (모집예정) > `unknown` (상태미확인) > `closed` (마감) 순으로 기본 정렬하며, 동일 정렬 순위 내에서는 `id` 오름차순(결정적 tie-breaker)을 적용한다.
- **Pagination 계산**: `offset = (page - 1) * limit` 방식을 사용하며 `total_count`, `page`, `limit` 정보를 응답 상위에 포함한다.

### 5. 오류 및 예외 처리

- `422 Unprocessable Entity`: Request DTO 파라미터 타입 및 범위를 벗어난 경우 Pydantic 검증 오류 반환
- `200 OK (Empty)`: 검색 조건에 일치하는 정책이 없는 경우 `total_count: 0`, `items: []`로 정상 응답 반환
- `500 Internal Server Error`: DB 연결 장애 또는 시스템 예외 발생 시 표준 Error DTO 반환

---

## 검증 계획

- `python scripts/validate_docs.py`: 문서 구문, 내부 상대 링크 및 거버넌스 규칙 검증
- `git diff --check`: 트레일링 공백 및 개행 검증
- `git status --short`: 임시 산출물 및 불필요 파일 비생성 검증

## Forest 완료 기준

- Backend 06 계획 문서(`06_policy_search.md`) 작성 및 문서 색인 등록
- W3-B0 계약 초안 및 Gate G1 제출용 준비 완료 (`W3-B0_READY`)
- `python scripts/validate_docs.py` 통과

## 위험과 미확정 사항

1. 자연어 검색어 `q`에서 행정구역명을 유도할 때 법정동 계층(시/도 vs 시/군/구) 매핑 정확도 범위
2. `POST` 요청 body 방식과 `GET` query parameter 방식 간의 OpenAPI documentation 표기 방식

## 관련 문서

- [3주차 검색 계약 Gate G1 인수인계](../../weekly_plan/week_03_search_contract_handoff.md)
- [Policy Search Data Foundation Forest 개발 계획](../integration/03_policy_search_data_foundation.md)
- [Policy API 계약](../../../api/policies.md)
- [Policy DB 매핑](../../../architecture/policy_database_mapping.md)
