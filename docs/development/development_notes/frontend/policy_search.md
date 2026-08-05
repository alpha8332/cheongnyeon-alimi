# Frontend Policy Search Forest 개발 기록

## 작업 정보

- 기간: 2026-08-05
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/policy-search`
- 관련 계획:
  [Policy Search Forest 개발 계획](../../develop_plan/frontend/04_policy_search.md)
- 현재 Slice: FE4-15 pending (Loading / Empty / Error shell)

## 목적

Gate G1 승인 Backend 06 Policy Search 계약을 Frontend TypeScript production
타입으로 소비 가능하게 승격하고, Mock-first 구현(FE4-12~)의 기준선을 확정한다.

## Forest 범위

- Gate G1 `GET /api/v1/policies/search` request·response TypeScript contract
- URL state·client error presentation types
- Mock-first Search UI, MSW, API Client, Browser 검증 (후속 Slice)

Frontend NL parser, Backend search endpoint 구현, Data Schema·Fixture·Seed
변경은 이 Forest 범위 밖이다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| W3-F0 (FE4-00~04) | completed | pure type draft·Forest 계획·Mock 명세 |
| FE4-11 | completed | draft contract → production types promote |
| FE4-12 | completed | M1–M6 mock fixtures·handler |
| FE4-13 | completed | Mock contract tests (`npm test`) |
| FE4-14 | completed | SearchBar·URL sync·Mock fetch |
| FE4-15 | pending | Loading / Empty / Error shell |

## 구현 내용

### FE4-11 — Types promote

W3-F0 draft에서 Gate G1 최종 계약 타입을 production 경로로 승격했다.

### FE4-12 — MSW fixtures M1–M6

Gate G1 Mock spec M1–M6을 canonical Seed 기반 nested `PolicySearchHit`
fixture와 handler 함수로 구현했다.

### FE4-13 — Mock contract tests (W3-F2A)

`frontend/tests/policySearch.contract.test.ts`에 9개 계약 테스트를 추가했다.

- G1 endpoint·defaults (`limit=20`, `include_partial=true`)
- flat query resolve·URLSearchParams·422 validation
- TS scenario registry ↔ JSON fixture drift 검증 (M1–M4, M6)
- M1–M6 handler nested `PolicySearchResponse` envelope·verdict·`unknown_count`
- pagination·`include_partial=false` 경계

`npm test`는 policy list 7 + policy search 9 = **16 tests pass**.

`handlePolicySearchMock`은 canonical Seed `PolicyDto[]`를 두 번째 인자로
받는다. FE4-14에서 `getPolicySearch()`가 `mockPolicies`를 주입한다.

### FE4-14 — SearchBar & URL Sync

`/search` 라우트와 SearchBar·URL flat param 동기화를 구현했다.

- `utils/policySearchUrl.ts`: `parsePolicySearchUrl`, `buildPolicySearchUrlParams`,
  `toPolicySearchRequest` — interpreted blob URL 저장 없음
- `SearchBar.tsx`: controlled `q`, submit → URL `?q=...` 갱신
- `PolicySearchPage.tsx`: `search_ux_preview.html` 블루 테마 검색창·카드 레이아웃
  (프로토타입 JS 로직 제외)
- `api/policySearch.ts` + `usePolicySearchQuery`: React Query + `handlePolicySearchMock`
  (`mockPolicies` 주입). MSW npm 패키지는 미설치 — handler 직접 호출 패턴(FE4-12와 동일)
- `App.tsx`: `/search` route 등록

URL round-trip: `?q=서울+주거&region=서울특별시` 등 flat param reload 시
SearchBar·fetch query 복원 확인.

## 주요 변경 파일

| 파일 | 변경 |
| --- | --- |
| `frontend/src/utils/policySearchUrl.ts` | FE4-14 — URL parse/build |
| `frontend/src/components/policySearch/SearchBar.tsx` | FE4-14 — 검색창 |
| `frontend/src/pages/user/PolicySearchPage.tsx` | FE4-14 — 검색 페이지 |
| `frontend/src/api/policySearch.ts` | FE4-14 — Mock API client |
| `frontend/src/hooks/usePolicySearchQuery.ts` | FE4-14 — React Query hook |
| `frontend/src/App.tsx` | FE4-14 — `/search` route |
| `frontend/index.html` | Plus Jakarta Sans font |
| `frontend/tests/policySearch.contract.test.ts` | FE4-13 — contract tests |
| `frontend/tsconfig.test.json` | search mock compile include |
| `frontend/package.json` | `npm test` glob for all contract tests |
| `docs/development/develop_plan/frontend/04_policy_search.md` | FE4-14 completed |

## 설계 결정

- Node `npm test`는 `@/` path alias 없이 relative import로 컴파일한다. Vite
  app build는 기존 `@/`·`@seed` alias를 유지한다.
- JSON fixture drift test는 manifest.json을 index로 TS registry와 deep equal
  비교한다.
- FE4-14 Mock fetch는 MSW worker 대신 `getPolicySearch()` → `handlePolicySearchMock`
  직접 호출. MSW npm 패키지 설치·worker wiring은 후속 Slice에서 필요 시 검토.

## 검증 결과

```text
python3 scripts/validate_docs.py  — passed
cd frontend && npm run build      — passed
cd frontend && npm run lint       — passed
cd frontend && npm test           — passed (16/16)
```

## Backend·Data 3주차 통합 확인

| 항목 | HEAD | 비고 |
| --- | --- | --- |
| Data DT2 profile | ✅ | `3cd6b89` lineage |
| Backend search HTTP endpoint | ❌ 미포함 | Mock contract tests는 G1 타입·FE4-12 Mock 기준 |
| `@/types/policySearch` vs Backend 06 plan | ✅ 구조 일치 | staging parity는 FE4-22 |

## 남은 작업

- FE4-15: Loading / Empty / Error shell (`policySearchErrors` mapper)
- FE4-16~21: Pagination, Filter Chips, badges, Home IA, Detail link
- FE4-22: Backend endpoint merge 후 실 API Client
