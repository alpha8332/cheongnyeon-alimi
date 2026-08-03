# Backend Policy Search Forest 개발 기록

## 작업 정보

- 기간: 2026-08-03
- 담당 영역: Backend
- 상태: in-progress
- 브랜치: `feature/backend/policy-search`
- 관련 계획:
  [Backend Policy Search Forest 개발 계획](../../develop_plan/backend/06_policy_search.md)
- 현재 Slice: W3-B0 completed, B1~B4 pending

## 목적

3주차 Gate G1 승인 및 실데이터 검색 기능을 위해 Backend 06 Policy Search Forest 개발 계획과 W3-B0 검색 API·Repository 계약 초안을 작성하고 문서화 검증을 완료한다.

## Forest 범위

- 검색 API Endpoint (`POST /api/v1/policies/search`) 및 Service DTO 레이어 유연성 설계
- 한국어 자연어 검색어 `q` 및 구조화 필터 Pydantic Request/Response DTO 정의
- Region/Age/Status 3값(`match | mismatch | unknown`) 판정 규칙 명세
- `mismatch` 제외, `unknown` 미확인 후보 포함, `partial` 정책 누락 사유(`missing_fields`) 전달 명세
- 검색 이유(`search_reasons`), 미확인 조건, 페이징 및 에러 DTO 스펙 명세
- 기존 목록·상세 API (`/api/v1/policies`) 호환성 보존
- 로컬 검증(`validate_docs.py`, `git diff --check`) 및 Gate G1 준비

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| W3-B0 | completed | Backend 06 개발 계획 및 W3-B0 계약 초안 작성, 인계 보드 업데이트 및 문서 검증 통과 |
| B1 | draft | Gate G1 승인 후 진행 예정 (자연어 파서 Service) |
| B2 | draft | Gate G1 승인 후 진행 예정 (PostgreSQL Repository & Query Builder) |
| B3 | draft | Gate G1 승인 후 진행 예정 (API Endpoint & DTO 직렬화) |
| B4 | draft | Gate G1 승인 후 진행 예정 (PostgreSQL 통합 및 회귀 검증) |

## 구현 내용

- [06_policy_search.md](../../develop_plan/backend/06_policy_search.md) 개발 계획서 생성을 통해 W3-B0 계약 초안을 명확히 정의함.
- `POST /api/v1/policies/search`를 기본 Endpoint로 채택하되, 서비스 계층(`PolicySearchService`) 입력을 DTO로 분리하여 차후 `GET` Query string 전환/지원이 용이하도록 작성함.
- `PolicySearchRequest`, `PolicySearchResponse`, `ParsedSearchConditions`, `SearchReasonItem`, `UnconfirmedConditionItem` 등의 Pydantic DTO 모델 초안 설계.
- Confirmed `mismatch`는 확정 제외, `unknown`은 미확인 후보 포함, `partial` 정책은 관련도 감점 없이 결과에 포함하되 `missing_fields` 사유를 응답 DTO에 실어 사용자에게 안내하도록 명세함.

## 설계 결정

- **Endpoint 메서드 유연성**: 복잡한 검색 DTO 및 파싱 교정을 지원하기 위해 `POST` 요청을 기본안으로 사용하되, 검색 서비스 로직을 독립 객체로 캡슐화하여 `GET` 파라미터 요청에도 동일하게 호환 가능하도록 설계.
- **Partial 정책 감점 정책**: 온통청년/복지로 수집 표본의 데이터 누락 특성을 고려하여 `partial` 데이터를 감점(penalty)하지 않고 포함하되, 응답 DTO의 `missing_fields` 배열을 통해 누락 사유만 사용자에게 투명하게 전달.

## 검증 결과

- `python scripts/validate_docs.py` 실행 결과: 통과 (`Documentation validation passed.`)
- `git diff --check` 실행 결과: 포맷 문제 0건
- `git status --short` 실행 결과: 임시/불필요 파일 생성 0건 확인

## 주요 변경 파일

- `docs/development/develop_plan/backend/06_policy_search.md`
- `docs/development/develop_plan/README.md`
- `docs/development/development_notes/README.md`
- `docs/development/development_notes/backend/policy_search.md`
- `docs/index.md`

## 남은 작업

- Gate G1 공동 검토(Data·Backend·Frontend 3자 검토) 및 승인 (`G1_APPROVED`)
- Gate G1 승인 후 Backend 06 본 구현 (Slice B1 ~ B4) 진행
