# Frontend Policy Search Forest 개발 기록

## 작업 정보

- 기간: 2026-08-05
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/policy-search`
- 관련 계획:
  [Policy Search Forest 개발 계획](../../develop_plan/frontend/04_policy_search.md)
- 현재 Slice: FE4-14 pending (SearchBar & URL, MSW worker)

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
| FE4-14 | pending | SearchBar·URL·MSW worker |

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
받는다. FE4-14 MSW wiring에서 `mockPolicies`를 주입한다.

## 주요 변경 파일

| 파일 | 변경 |
| --- | --- |
| `frontend/tests/policySearch.contract.test.ts` | FE4-13 — contract tests |
| `frontend/tsconfig.test.json` | search mock compile include |
| `frontend/package.json` | `npm test` glob for all contract tests |
| `frontend/src/mocks/policySearchHandlers.ts` | policies 주입 시그니처 |
| `frontend/src/mocks/policySearchRequest.ts` | `ResolvedPolicySearchQuery` 타입 수정 |
| `frontend/src/mocks/*.ts`, `frontend/src/types/policySearch.ts` | Node test용 relative import |
| `docs/development/develop_plan/frontend/04_policy_search.md` | FE4-13 completed |

## 설계 결정

- Node `npm test`는 `@/` path alias 없이 relative import로 컴파일한다. Vite
  app build는 기존 `@/`·`@seed` alias를 유지한다.
- JSON fixture drift test는 manifest.json을 index로 TS registry와 deep equal
  비교한다.

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

- FE4-14: MSW worker + SearchBar·URL sync
- FE4-22: Backend endpoint merge 후 실 API Client
