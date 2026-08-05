# Frontend Policy Search Forest 개발 기록

## 작업 정보

- 기간: 2026-08-05
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/policy-search`
- 관련 계획:
  [Policy Search Forest 개발 계획](../../develop_plan/frontend/04_policy_search.md)
- 현재 Slice: FE4-13 pending (Mock contract tests)

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
| FE4-13 | pending | Mock contract tests (`npm test`) |

## 구현 내용

### FE4-11 — Types promote

W3-F0 draft에서 Gate G1 최종 계약 타입을 production 경로로 승격했다.
실행 helper(parse/build URL, HTTP mapper)는 FE4-14·FE4-19에서 구현한다.

### FE4-12 — MSW fixtures M1–M6

Gate G1 Mock spec M1–M6을 canonical Seed 기반 nested `PolicySearchHit`
fixture와 handler 함수로 구현했다. `policy_id` 참조 fixture JSON과 TypeScript
scenario registry를 함께 두었으며, MSW worker 연결은 FE4-14에서 수행한다.

- `handlePolicySearchMock()` — flat query in → `200` nested response 또는 `422`
- defaults: `include_partial=true`, `page=1`, `limit=20`
- M5: trim 후 빈 `q` → 422
- M1–M4, M6: Forest plan 표 시나리오 query signature 매칭

## 주요 변경 파일

| 파일 | 변경 |
| --- | --- |
| `frontend/src/types/policySearch.ts` | FE4-11 — API contract types |
| `frontend/src/mocks/policySearchRequest.ts` | FE4-12 — query resolve·422 validation |
| `frontend/src/mocks/policySearchFixtures.ts` | FE4-12 — M1–M6 scenario registry |
| `frontend/src/mocks/policySearchHandlers.ts` | FE4-12 — mock handler entry |
| `frontend/src/mocks/fixtures/policySearch/*.json` | FE4-12 — scenario fixture JSON |
| `docs/development/develop_plan/frontend/04_policy_search.md` | FE4-11·FE4-12 완료 갱신 |

## 설계 결정

- MSW npm 패키지는 아직 설치하지 않았다. 기존 list/detail Mock과 동일하게 handler
  함수를 먼저 두고, FE4-14 SearchBar·URL Slice에서 MSW worker를 연결한다.
- Fixture policy envelope는 `mockPolicies`(canonical Seed)에서 materialize하여
  Seed 변경 시 public `PolicyDto` shape drift를 줄인다.
- Backend `GET /api/v1/policies/search` 구현 커밋(`49c56cf`~)은 현재 브랜치 HEAD에
  없으므로 Mock은 Backend 06 계획·승격 타입(`@/types/policySearch`)을 권위로 한다.

## 검증 결과

```text
python3 scripts/validate_docs.py  — passed
cd frontend && npm run build      — passed
cd frontend && npm run lint       — passed
```

`npm test` search contract 자동화는 FE4-13에서 추가한다. MSW browser smoke는
FE4-14에서 수행한다.

## 남은 작업

- FE4-13: Mock contract tests (`npm test`)
- FE4-14~: Search UI·URL sync (MSW worker)
- FE4-22: Backend endpoint 실 API Client (endpoint merge 후)

## Backend·Data 3주차 통합 확인 (FE4-12 착수 전)

| 항목 | HEAD (`0c68c5b`) | 비고 |
| --- | --- | --- |
| Data DT2 profile (`3cd6b89`) | 포함 | release dataset quality profile |
| Search foundation (evaluation, projection ORM) | 포함 | HTTP endpoint 아님 |
| Backend search endpoint (`49c56cf`, `01035da`) | **미포함** | `feature/backend/policy-search-impl` 계열 |
| Frontend `@/types/policySearch` vs Backend 06 plan | **구조 일치** | `unknown_count`, nullable verdicts, `interpreted_conditions` |
