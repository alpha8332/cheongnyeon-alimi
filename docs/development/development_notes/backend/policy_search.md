# Backend 06 Policy Search Forest 개발 기록

## 작업 정보

- 기간: 2026-08-04
- 담당 영역: Backend
- 상태: in-progress
- 브랜치: `feature/backend/policy-search-impl`
- 선행 Forest: [Policy Search Data Foundation](../../develop_plan/integration/03_policy_search_data_foundation.md)
- 관련 계획: [Backend 06 Policy Search Forest 개발 계획](../../develop_plan/backend/06_policy_search.md)
- 현재 Slice: B3 pending (B2 completed)

## 목적

PostgreSQL 기반 실데이터 정책 검색 Backend 서비스 및 API 구현을 완수하기 위한 개발 기록이다. 한국어 자연어 검색어(`q`) 및 명시적 파라미터(`keyword`, `region`, `age`, `category`, `status`)를 규칙 기반으로 파싱하는 자연어 구조화 파서 구현, PostgreSQL Search Projection 기반의 Query Builder 및 4단계 결정적 정렬 구현, `GET /api/v1/policies/search` API Endpoint 및 DTO 직렬화 구현 결과를 기록한다.

## Forest 범위

- Gate G1 승인 검색 API Endpoint 및 Method 스펙 (`GET /api/v1/policies/search`)
- Flat Structure Query Parameter Pydantic 모델 및 Gate G1 DTO (`PolicySearchQueryParams`, `PolicySearchResponse`, `InterpretedConditions`, `DimensionVerdicts`)
- 자연어 `q` 파서 및 명시적 필터 파라미터 `explicit` override 규칙 서비스 (`parse_search_query`)
- Region / Age / Status / Category 차원별 Nullable 4값 (`match | mismatch | unknown | null`) 판정 규칙
- PostgreSQL Query Builder 및 4단계 결정적 정렬 (`score DESC` ➔ `unknown_count ASC` ➔ `status` ➔ `policy.id ASC`)
- 단위 테스트 및 백엔드 통합 검증

## Slice 진행 현황

| Slice | 목표 | 상태 | 검증 내용 |
| --- | --- | --- | --- |
| **W3-B0** | 검색 API 및 Repository 계약 초안 작성 | completed | Gate G1 최종 계약 승인 (`2026-08-04`) |
| **B1** | 자연어 해석 및 규칙 기반 구조화 서비스 구현 | completed | `policy_search_parser.py` 구현 및 단위 테스트 통과 (4 passed) |
| **B2** | PostgreSQL 검색 Repository 및 Query Builder 구현 | completed | `PolicySearchRepository.search_policies` 및 4단계 정렬 테스트 통과 (3 passed) |
| **B3** | Policy Search API Endpoint 및 DTO 구현 | pending | Slice B2 완료 후 진행 예정 |
| **B4** | PostgreSQL 통합, 정렬/페이징 & API 호환성 검증 | pending | Slice B3 완료 후 진행 예정 |

## 구현 내용

### Slice B1 - 자연어 해석 및 규칙 기반 구조화 서비스 (`app/services/policy_search_parser.py`)

1. **DTO 모델 확장 (`app/schemas/policy_search.py`)**:
   - Gate G1 승인 스펙에 맞춰 `SearchDimension`, `ConditionItem`, `InterpretedConditions`, `DimensionVerdicts`, `UnconfirmedCondition`, `PolicySearchResultItem`, `PolicySearchResponse` Pydantic DTO 선언.
2. **자연어 파서 함수 (`parse_search_query`)**:
   - `q` 검색어 전처리 (`q.strip()` 및 다중 공백 정리 `q_clean`).
   - 규칙 기반 연령(age), 신청상태(status), 카테고리(category), 지역(region) 자동 추출.
   - 명시적 쿼리 파라미터(`keyword`, `region`, `age`, `category`, `status`) 입력 시 `source="explicit"`로 `q` 파싱 조건을 override 처리하고 `override_fields` 리스트에 기록.
   - 행정구역 매핑 상태(`resolved`, `ambiguous`, `unmapped`) 및 후보군(`candidates[]`) 추출.
   - 파싱에 소비되지 않은 독립 토큰을 `uninterpreted_terms`에 수집.

### Slice B2 - PostgreSQL 검색 Repository 및 Query Builder (`app/repositories/policy_search.py`)

1. **`search_policies` Query Builder 구현**:
   - `InterpretedConditions`와 `include_partial`, `page`, `limit` 파라미터를 받아 `mismatch` 항목을 제외한 전체 검색 결과를 필터링 및 조율.
   - `status`, `age`, `category`, `region` 4개 차원에 대해 조건 미선택 시 `null`, 조건 합치 시 `match`, 불일치 시 `mismatch`(확정 제외), 근거 부족 시 `unknown` 처리.
   - `closed` 신청상태 정책은 명시적 `status=closed` 지정 시에만 노출되도록 기본 제외 필터링.
2. **4단계 결정적 정렬 (Deterministic 4-step Sort)**:
   - 1순위: `score DESC` (관련도 점수 내림차순)
   - 2순위: `unknown_count ASC` (verdicts 내 null 제외 unknown 차원 개수 오름차순)
   - 3순위: `status` 우선순위 (`open` > `scheduled` > `null/unknown` > `closed`)
   - 4순위: `policy.id ASC` (결정적 tie-breaker)
3. **`total` 및 페이징**:
   - pagination 적용 전 전체 결과 건수 `total` 계산 및 `page`, `limit` 슬라이싱 반환.

## 주요 변경 파일

- `backend/app/repositories/policy_search.py`: `search_policies` Repository Query Builder 메서드 추가
- `backend/tests/test_policy_search_repository_builder.py`: Query Builder 4단계 정렬 및 필터링 테스트
- `docs/development/development_notes/backend/policy_search.md`: Backend 06 개발 기록 (Slice B2 누적)

## 설계 결정

1. **단일 파싱 정본 위치**:
   - Frontend 전용 파서를 두지 않고 Backend `parse_search_query`를 파싱 및 구조화의 단일 정본 기준으로 사용.
2. **Nullable 4차원 Verdicts & Query-level Warnings 분리**:
   - 자연어 해석 단계의 경고(`resolution="unmapped"`/`"ambiguous"`)는 `InterpretedConditions.conditions[]`에만 기술하고 개별 정책 row-level `unconfirmed_conditions[]`와 명확히 구분함.

## 검증 결과

- `python -m pytest tests/test_policy_search_parser.py`: 4 passed (100% 통과)
- `python -m pytest`: 90 passed, 12 skipped (전체 백엔드 테스트 스위트 회귀 없음)

## 남은 작업

- **Slice B2**: PostgreSQL 검색 Repository 및 4단계 결정적 정렬 Builder 구현
- **Slice B3**: Policy Search API Endpoint (`GET /api/v1/policies/search`) 핸들러 구현
- **Slice B4**: PostgreSQL 통합 검증 및 전체 회귀 테스트
