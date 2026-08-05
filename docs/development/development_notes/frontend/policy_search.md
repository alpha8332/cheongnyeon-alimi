# Frontend Policy Search Forest 개발 기록

## 작업 정보

- 기간: 2026-08-05
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/policy-search`
- 관련 계획:
  [Policy Search Forest 개발 계획](../../develop_plan/frontend/04_policy_search.md)
- 현재 Slice: FE4-16 pending (Pagination)

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
| FE4-16 | pending | Pagination |

## 구현 내용

### FE4-15 — Loading / Empty / Error shell

#### SearchBar bugfix

- `key={searchParams.toString()}` → `key={urlState.q}` 로 변경: 검색 완료 후에도
  입력 수정·지우기 가능
- 로딩 중 input disable 제거; submit 버튼만 `isSubmitting` 시 disable
- ✕ 지우기 버튼 추가

#### Shell UI

- `PolicySearchLoadingShell`: spinner + skeleton card grid
- `PolicySearchEmptyShell`: Golden Query Empty UX (`total=0`)
- `PolicySearchErrorShell`: 422/5xx/network + retry
- `utils/policySearchErrors.ts`: FE4-03 Error UX 표
- empty/error 시 SearchBar·UrlFilterChips 유지

#### Golden Query Empty UX copy

- title: 「조건에 맞는 정책을 찾지 못했습니다」
- 존재하지 않는 정책 단정 금지, interpreted summary, Seed 데이터 범위 안내

## 주요 변경 파일

| 파일 | 변경 |
| --- | --- |
| `frontend/src/components/policySearch/SearchBar.tsx` | bugfix + clear |
| `frontend/src/components/policySearch/PolicySearch*Shell.tsx` | FE4-15 |
| `frontend/src/utils/policySearchErrors.ts` | mapper |
| `frontend/src/api/policySearchApiError.ts` | error class |
| `frontend/tests/policySearch.errors.test.ts` | mapper tests |
| `frontend/src/pages/user/PolicySearchPage.tsx` | shell wiring |

## 설계 결정

- SearchBar는 `key={urlState.q}` + 내부 state: URL `q` 변경(뒤로/앞으로·submit) 시에만
  remount, 타이핑 중에는 remount 없음
- Error mapper는 FE4-03 표를 `PolicySearchErrorPresentation`으로 구현; FE4-19에서
  reason code copy 확장

## 검증 결과

```text
python3 scripts/validate_docs.py  — passed
cd frontend && npm run build      — passed
cd frontend && npm run lint       — passed
cd frontend && npm test           — passed (19/19)
```

Browser M5 422·empty scenario는 이번 세션에서 수동 확인하지 않았다.

## Backend·Data 3주차 통합 확인

| 항목 | HEAD | 비고 |
| --- | --- | --- |
| Backend search HTTP endpoint | ❌ 미포함 | Mock-first |
| `@/types/policySearch` vs Backend 06 plan | ✅ 구조 일치 | staging parity는 FE4-22 |

## 남은 작업

- FE4-16: Pagination
- FE4-17~21: Filter Chips, badges, Home IA, Detail link
- FE4-22: Real API Client
