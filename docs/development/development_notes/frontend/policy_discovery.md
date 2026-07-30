# Frontend Policy Discovery Forest 개발 기록

## 작업 정보

- 기간: 2026-07-28
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/policy-discovery`
- 관련 계획:
  [Policy Discovery Forest 개발 계획](../../develop_plan/frontend/01_policy_discovery.md)
- 현재 Slice: FE 2A Policy API contract alignment

## 목적

`initial_programs.json` canonical Seed를 공개 `PolicyDto`로 변환해
Frontend TypeScript 타입·Mock·실제 API Client·와이어프레임 UI가 같은
Policy API 계약을 소비하도록 맞추고 Data 6 Frontend 검토 결과를 기록한다.

## Forest 범위

Frontend Foundation(FE 1)은 PR #14로 `develop`에 병합되었다. FE 2에서는
정책 타입, Seed Mock, 목록·상세·필터 UI와 Loading/Empty/Error 상태를
구현했다. FE 2A에서는 Backend API가 확정한 공개 DTO·endpoint·pagination,
숫자 ID와 partial opt-in에 Mock과 실제 API Client를 맞춘다. 관리자
provenance 조회는 공개 API 범위 밖이다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE 1 | completed | 라우터, 레이아웃, 기본 UI 컴포넌트 |
| FE 2 | in-progress | 타입·Mock·정책 목록·상세·필터·예외 UI 구현 |
| FE 2A | in-progress | 공개 Policy API 계약 반영 완료, build·lint·소비 테스트 실행 대기 |

## 구현 내용

### FE 2 - Data 6 Frontend 공동 계약 검토

[Fixture와 Seed 계약](../../../data/fixture_seed_contract.md)의 Frontend
검토 결과 6항목(null·빈 배열, categories, schedule/status, partial,
source_id+external_id, provenance)을 기록하고 Frontend 상태를 `reviewed`로
갱신했다. Schema·Seed·Fixture는 변경하지 않았다.

### FE 2A - 공개 Policy API 계약 정합화

- 사용자 타입을 `NormalizedProgram`에서 공개 `PolicyDto`로 교체하고
  `provenance`와 `invalid`를 제거했다.
- canonical Seed는 내부 adapter에서만 provenance·invalid 입력 경계를
  인식하며 공개 Mock 객체에는 provenance가 존재하지 않는다.
- Mock과 실제 Client가 `PolicyListResponse` envelope,
  `/api/v1/policies`, 숫자 `id` 상세와 `include_partial` query를 공유한다.
- 기본 목록은 valid 2건만, 명시적 opt-in은 valid·partial 4건을 반환한다.
- partial 카드의 상세 링크는 `include_partial=true`를 유지해 목록·상세
  품질 경계를 일치시킨다.
- Vite 개발 서버를 Backend 기본 CORS 허용 origin과 같은 3000 포트로
  고정해 `VITE_USE_MOCK=false` 브라우저 전환 경계를 맞췄다.
- 공개 Data Quality 화면은 provenance를 가정하지 않고 valid·partial
  상태만 표시한다. provenance UI는 인증된 관리자 API가 생길 때 별도
  Forest에서 구현한다.
- 추가 라이브러리 없이 TypeScript 컴파일러와 Node 내장 테스트 러너로
  DTO 변환·pagination·partial·endpoint·숫자 ID 소비 테스트를 추가했다.

### FE 2 - TypeScript 타입과 Mock

- `frontend/src/types/policy.ts`: 공개 `PolicyDto`, `PolicyListResponse`와 enum
- `frontend/src/mocks/policies.ts`: canonical Seed를 공개 DTO로 변환한 Mock
- `frontend/src/api/policies.ts`: Mock/Backend API 공용 fetch 레이어

### FE 2 - 와이어프레임 UI

- `PolicyCard`: D-Day, 다중 category 태그, 기관명, partial 배지
- `SearchPage`: 검색·지역·카테고리·연령 client-side 필터, 목록 그리드
- `ProgramDetailPage`: 지원내용, 신청 기간, schedule/status 분리, null
  fallback, 원문 링크
- `DataQualityPage`: 공개 API의 valid·partial 품질 상태 표시
- Loading / Empty / Error 공통 컴포넌트

### FE 2 - 식별·라우팅

상세 경로는 API가 반환한 양의 정수 `id`를 사용한다. nullable
`external_id`와 `source_id` 조합은 화면 route나 React key로 사용하지 않는다.

## 주요 변경 파일

- `docs/data/fixture_seed_contract.md`
- `docs/development/develop_plan/frontend/01_policy_discovery.md`
- `frontend/src/types/policy.ts`
- `frontend/src/mocks/policyContract.ts`
- `frontend/src/mocks/policies.ts`
- `frontend/src/api/policyRequest.ts`
- `frontend/src/api/policies.ts`
- `frontend/src/utils/policyId.ts`
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
- `frontend/src/hooks/usePoliciesQuery.ts`
- `frontend/src/lib/queryClient.ts`
- `frontend/src/main.tsx`
- `frontend/vite.config.ts`
- `frontend/tsconfig.app.json`
- `frontend/tsconfig.test.json`
- `frontend/tests/policy-contract.test.ts`

## 설계 결정

- Seed JSON은 Vite alias `@seed`로 repo root `data/seeds/`에서 직접
  import하되 `PolicyDto` adapter를 통과시켜 DB 생성 필드를 추가하고
  provenance를 제거한다.
- `VITE_USE_MOCK !== 'false'`일 때 Mock을 사용하고, false이면 동일
  `getPolicies`/`getPolicyById` 소비 계약으로 Backend API를 호출한다.
- 공개 API에는 provenance가 없으므로 사용자·관리자 화면 모두 이를
  가정하지 않는다.

## 검증 결과

- `python3 scripts/validate_docs.py`: 통과 (2026-07-28)
- `npm run build` (frontend): 통과 (2026-07-28)
- `npm run lint` (frontend): 통과 (2026-07-28)
- 브라우저 수동 UI 테스트: 미실행
- FE 2A `npm test`, `npm run lint`, `npm run build`: 이 PC에 Node·npm이
  없어 미실행 (2026-07-30)
- FE 2A `python scripts/validate_docs.py`: 작업 완료 후 결과 기록 예정

## 남은 작업

- Node.js 환경에서 FE 2A 소비 테스트·lint·build 실행
- 검증 증거 확인 후 `INT-02-D0-FE`·`INT-02-D3-FE` 인계와 Data 6
  Frontend 상태 완료 처리
- 인증된 관리자 provenance API와 화면은 별도 관리자 Forest에서 결정
- 즐겨찾기, 알림, 캘린더 등 후속 Frontend Slice
