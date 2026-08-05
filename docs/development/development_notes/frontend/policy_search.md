# Frontend Policy Search Forest 개발 기록

## 작업 정보

- 기간: 2026-08-05
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/policy-search`
- 관련 계획:
  [Policy Search Forest 개발 계획](../../develop_plan/frontend/04_policy_search.md)
- 현재 Slice: FE4-19 pending (Reason & Uninterpreted UX)

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
| FE4-18 | completed | Partial/Unknown badges + unconfirmed tooltip |

## 구현 내용

### FE4-18 — Partial / Unknown badges

#### 배지 semantic 분리

- `PartialBadge`: `data_quality_status=partial` → 「정보 일부 누락」(amber)
- `UnknownVerdictBadge`: `unknown_count > 0` & non-partial → 「정보 미확인」(slate)
- `UnconfirmedConditionsBadge`: `unconfirmed_conditions[]` → 「자격요건 직접 확인 필요」
  + hover/focus tooltip (field별 message 목록)
- 카드 visual tag는 모집 상태(모집중·마감 임박)만 표시; partial/unknown과 분리

#### Display constants promote

- `frontend/src/constants/policySearchDisplay.ts` (draft `policySearchDisplay.ts` 승격)
- unknown copy: 전국·제한 없음 추정 금지 문구 포함

#### PolicySearchResultCard

- eligibility: unknown/unconfirmed 시 「일부 조건 정보 없음 · 원문 확인 필요」
- M4 복지로 표본: partial + multi-unknown + unconfirmed tooltip 동시 표시

### FE4-17 — Filter Chips

(InterpretedConditionChips, ConditionEditorDrawer, URL filter mutations)

## 주요 변경 파일

| 파일 | 변경 |
| --- | --- |
| `frontend/src/components/policySearch/PolicySearchResultCard.tsx` | FE4-18 badge wiring |
| `frontend/src/components/policySearch/PolicySearchBadges.tsx` / `.css` | FE4-18 unknown/unconfirmed |
| `frontend/src/components/policy/PartialBadge.tsx` | FE4-18 label fix |
| `frontend/src/constants/policySearchDisplay.ts` | FE4-18 promoted labels |
| `frontend/tests/policySearch.badges.test.ts` | FE4-18 badge helper tests |

## 설계 결정

- partial 정책은 품질 배지 + unconfirmed alert로 M4 표현; 별도 unknown verdict 배지는
  non-partial row에만 표시 (중복 방지)
- `PolicyCard` visual tag의 partial warn 라벨은 FE4-18 범위 밖 (Discovery UI 후속)

## 검증 결과

```text
python3 scripts/validate_docs.py  — passed
cd frontend && npm run build      — passed
cd frontend && npm run lint       — passed
cd frontend && npm test           — passed (33/33)
```

Browser M4(`?q=복지로+생활`) 시나리오는 이번 세션에서 수동 확인하지 않았다.

## Backend·Data 3주차 통합 확인

| 항목 | HEAD | 비고 |
| --- | --- | --- |
| Backend search HTTP endpoint | ❌ 미포함 | Mock-first |
| `@/types/policySearch` vs Backend 06 plan | ✅ 구조 일치 | staging parity는 FE4-22 |

## 남은 작업

- FE4-19~21: Reason UX, Home IA, Detail link
- FE4-22: Real API Client
