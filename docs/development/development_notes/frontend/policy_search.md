# Frontend Policy Search Forest 개발 기록

## 작업 정보

- 기간: 2026-08-05
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/policy-search`
- 관련 계획:
  [Policy Search Forest 개발 계획](../../develop_plan/frontend/04_policy_search.md)
- 현재 Slice: FE4-12 pending (MSW fixtures)

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
| FE4-12 | pending | MSW fixtures M1–M6 |

## 구현 내용

### FE4-11 — Types promote

W3-F0 draft에서 Gate G1 최종 계약 타입을 production 경로로 승격했다.
실행 helper(parse/build URL, HTTP mapper)는 FE4-14·FE4-19에서 구현한다.

## 주요 변경 파일

| 파일 | 변경 |
| --- | --- |
| `frontend/src/types/policySearch.ts` | 신규 — API contract types |
| `frontend/src/types/policySearchErrors.ts` | 신규 — error presentation types |
| `frontend/src/types/policySearchUrlState.ts` | 신규 — URL state types |
| `frontend/src/types/draft/policySearch.contract.ts` | 삭제 (승격) |
| `frontend/src/types/draft/policySearchErrors.ts` | 삭제 (승격) |
| `frontend/src/types/draft/policySearchUrlState.ts` | 삭제 (승격) |
| `frontend/src/types/draft/policySearchDisplay.ts` | import 경로 → `@/types/policySearch` |
| `frontend/src/types/draft/README.md` | display draft만 유지 안내 |
| `docs/development/develop_plan/frontend/04_policy_search.md` | FE4-11 완료·경로 갱신 |
| `docs/development/development_notes/frontend/policy_search.md` | 본 기록 |
| `docs/index.md` | 개발 기록 색인·인계 보드 갱신 |
| `CHANGELOG.md` | FE4-11 types promote 요약 |

## 설계 결정

- Contract·error·URL types는 draft와 동일한 3-file 구조로 production에 배치했다.
  Forest 계획의 `policySearch.ts` 중심 promote와 호환되며 import 경로를
  역할별로 분리한다.
- `policySearchDisplay.ts`는 FE4-18 배지 UI 전까지 draft에 유지한다. label
  상수는 API contract와 분리된 pre-UI 자산이다.
- `PolicySearchHit.unknown_count`는 Backend G1 checklist #13과 동일하게
  promote했다.

## 검증 결과

```text
python3 scripts/validate_docs.py  — passed
cd frontend && npm run build      — passed
cd frontend && npm run lint       — passed
```

MSW·contract test·Browser 검증은 FE4-12 이후 Slice에서 수행한다.

## 남은 작업

- FE4-12: Mock M1–M6 MSW handler
- FE4-13: Mock contract tests (`npm test`)
- FE4-14~: Search UI·URL sync (MSW only)
- FE4-22: Backend endpoint 실 API Client (endpoint 준비 후)
