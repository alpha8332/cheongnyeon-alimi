# Frontend Policy Discovery Forest 개발 기록

## 작업 정보

- 기간: 2026-07-28
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/policy-discovery`
- 관련 계획:
  [Policy Discovery Forest 개발 계획](../../develop_plan/frontend/01_policy_discovery.md)
- 현재 Slice: FE 2 policy-discovery

## 목적

`NormalizedProgram` 1.0.0 Schema와 `initial_programs.json` canonical Seed를
Frontend TypeScript 타입·Mock·와이어프레임 UI로 소비하고, Data 6 Frontend
공동 계약 검토를 기록한다.

## Forest 범위

Frontend Foundation(FE 1)은 PR #14로 `develop`에 병합되었다. FE 2에서는
정책 타입, Seed Mock, 목록·상세·필터 UI, Loading/Empty/Error 상태와
관리자 provenance 표시를 구현했다. Backend API 실연동은 범위 밖이다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE 1 | completed | 라우터, 레이아웃, 기본 UI 컴포넌트 |
| FE 2 | in-progress | 타입·Mock·정책 목록·상세·필터·예외 UI 구현 |

## 구현 내용

### FE 2 - Data 6 Frontend 공동 계약 검토

[Fixture와 Seed 계약](../../../data/fixture_seed_contract.md)의 Frontend
검토 결과 6항목(null·빈 배열, categories, schedule/status, partial,
source_id+external_id, provenance)을 기록하고 Frontend 상태를 `reviewed`로
갱신했다. Schema·Seed·Fixture는 변경하지 않았다.

### FE 2 - TypeScript 타입과 Mock

- `frontend/src/types/policy.ts`: `NormalizedProgram` 1.0.0 인터페이스와 enum
- `frontend/src/mocks/programs.ts`: `data/seeds/initial_programs.json` 직접
  import
- `frontend/src/api/programs.ts`: Mock/Backend API 공용 fetch 레이어

### FE 2 - 와이어프레임 UI

- `PolicyCard`: D-Day, 다중 category 태그, 기관명, partial 배지
- `SearchPage`: 검색·지역·카테고리·연령 client-side 필터, 목록 그리드
- `ProgramDetailPage`: 지원내용, 신청 기간, schedule/status 분리, null
  fallback, 원문 링크
- `DataQualityPage`: provenance·품질 상태 관리자 표시
- Loading / Empty / Error 공통 컴포넌트

### FE 2 - 식별·라우팅

상세 경로 ID는 `{source_id}--{external_id}` 단일 파라미터를 사용한다.
Mock과 향후 Backend API 모두 `source_id + external_id` lookup을 유지한다.

## 주요 변경 파일

- `docs/data/fixture_seed_contract.md`
- `docs/development/develop_plan/frontend/01_policy_discovery.md`
- `frontend/src/types/policy.ts`
- `frontend/src/mocks/programs.ts`
- `frontend/src/api/programs.ts`
- `frontend/src/utils/programId.ts`
- `frontend/src/utils/policyDisplay.ts`
- `frontend/src/utils/policyFilters.ts`
- `frontend/src/components/policy/*`
- `frontend/src/components/common/LoadingState.tsx`
- `frontend/src/components/common/EmptyState.tsx`
- `frontend/src/components/common/ErrorState.tsx`
- `frontend/src/pages/user/HomePage.tsx`
- `frontend/src/pages/user/SearchPage.tsx`
- `frontend/src/pages/user/ProgramDetailPage.tsx`
- `frontend/src/pages/admin/DataQualityPage.tsx`
- `frontend/src/hooks/useProgramsQuery.ts`
- `frontend/src/lib/queryClient.ts`
- `frontend/src/main.tsx`
- `frontend/vite.config.ts`
- `frontend/tsconfig.app.json`

## 설계 결정

- Seed JSON은 Vite alias `@seed`로 repo root `data/seeds/`에서 직접 import해
  canonical Seed와 byte 동기화를 유지한다.
- `VITE_USE_MOCK !== 'false'`일 때 Mock을 사용하고, Backend API 준비 후 동일
  `getPrograms`/`getProgramByIdentity` 함수로 전환한다.
- 일반 사용자 UI에는 provenance를 노출하지 않고 `DataQualityPage`에만
  표시한다.

## 검증 결과

- `python3 scripts/validate_docs.py`: 통과 (2026-07-28)
- `npm run build` (frontend): 통과 (2026-07-28)
- `npm run lint` (frontend): 통과 (2026-07-28)
- 브라우저 수동 UI 테스트: 미실행

## 남은 작업

- Backend policy API 연동과 응답 envelope 확정
- Data 6 Backend 공동 승인 후 Forest 완료 처리
- 즐겨찾기, 알림, 캘린더 등 후속 Frontend Slice
