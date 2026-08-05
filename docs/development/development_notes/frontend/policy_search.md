# Frontend Policy Search Forest 개발 기록

## 작업 정보

- 기간: 2026-08-05
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/policy-search`
- 관련 계획:
  [Policy Search Forest 개발 계획](../../develop_plan/frontend/04_policy_search.md)
- 현재 Slice: FE4-18 pending (Partial / Unknown badges)

## 목적

Gate G1 승인 Backend 06 Policy Search 계약을 Frontend TypeScript production
타입으로 소비 가능하게 승격하고, Mock-first Search UI Slice를 구현한다.

## Forest 범위

- Gate G1 `GET /api/v1/policies/search` request·response TypeScript contract
- URL state·client error presentation types
- Mock-first Search UI, API Client, Browser 검증 (후속 Slice)

Frontend NL parser, Backend search endpoint 구현, Data Schema·Fixture·Seed
변경은 이 Forest 범위 밖이다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE4-14 | completed | SearchBar·URL sync·Mock fetch |
| FE4-15 | completed | Loading/Empty/Error shell + SearchBar bugfix |
| FE4-16 | completed | Pagination + URL page sync + stale guard |
| FE4-17 | completed | InterpretedConditionChips remove/edit/add + URL sync |

## 구현 내용

### FE4-17 — Filter Chips remove + edit/add

#### InterpretedConditionChips

- `interpreted_conditions.conditions` + URL flat param mirror로 칩 렌더
- ✕ remove: URL flat param 제거 후 재검색 (`removePolicySearchFilter`)
- 칩 클릭 edit / 「+ 조건 추가」: `ConditionEditorDrawer`로
  `region`·`age`·`status`·`category`·`keyword` flat param 갱신
- filter 변경(삭제·수정·추가) 시 `page=1` 자동 reset (`withPolicySearchPage`)
- q에서만 해석된 조건(source=`q`, URL param 없음)은 ✕ remove 비활성;
  verdict/resolution 스타일은 in-memory 응답 기준

#### MatchVerdict / resolution 칩 스타일

- `chip--match` / `chip--unknown` / `chip--mismatch`
- `chip--ambiguous` / `chip--unmapped` (interpretation resolution)
- URL JSON blob 저장 없음 (G1 flat param only)

#### Fallback

- 응답 없음(loading/error/initial) 시 URL flat param만으로 read-only 칩 구성
- error/empty shell에서도 칩 UI 유지 (FE4-03 Error UX 표)

### FE4-16 — Pagination

(이전 Slice — SearchPagination, stale guard, URL `page` sync)

### FE4-15 — Loading / Empty / Error shell

(SearchBar bugfix, shell UI, Golden Query Empty UX copy)

## 주요 변경 파일

| 파일 | 변경 |
| --- | --- |
| `frontend/src/components/policySearch/InterpretedConditionChips.tsx` | FE4-17 interactive chips |
| `frontend/src/components/policySearch/ConditionEditorDrawer.tsx` | FE4-17 add/edit drawer |
| `frontend/src/utils/interpretedConditionChips.ts` | FE4-17 chip builder + verdict aggregate |
| `frontend/src/utils/policySearchFilterMutations.ts` | FE4-17 URL filter remove/update |
| `frontend/src/pages/user/PolicySearchPage.tsx` | FE4-17 wiring |
| `frontend/src/styles/theme.css` | FE4-17 chip verdict variants + chip-x |
| `frontend/tests/policySearch.filterMutations.test.ts` | FE4-17 mutation tests |
| `frontend/src/components/policySearch/SearchPagination.tsx` | FE4-16 |
| `frontend/tests/policySearch.pagination.test.ts` | FE4-16 |

## 설계 결정

- Chip remove는 URL flat param이 있는 경우만 허용; q-only 해석 조건은 검색어 수정 안내
- Verdict 색상은 items[] verdict aggregate(match > unknown > mismatch); keyword dimension 제외
- `UrlFilterChips.tsx` / `buildUrlFilterChips`는 FE4-17에서 supersede (미삭제, 후속 정리 가능)

## 검증 결과

```text
python3 scripts/validate_docs.py  — passed
cd frontend && npm run build      — passed
cd frontend && npm run lint       — passed
cd frontend && npm test           — passed (29/29)
```

Browser remove region·edit age 시나리오는 이번 세션에서 수동 확인하지 않았다.

## Backend·Data 3주차 통합 확인

| 항목 | HEAD | 비고 |
| --- | --- | --- |
| Backend search HTTP endpoint | ❌ 미포함 | Mock-first |
| `@/types/policySearch` vs Backend 06 plan | ✅ 구조 일치 | staging parity는 FE4-22 |

## 남은 작업

- FE4-18~21: badges, Reason UX, Home IA, Detail link
- FE4-22: Real API Client
