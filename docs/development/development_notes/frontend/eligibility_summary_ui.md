# Frontend Eligibility Summary UI Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11 (FE7-05 Browser E2E: 2026-08-12)
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [Eligibility Summary UI Forest 개발 계획](../../develop_plan/frontend/07_eligibility_summary_ui.md)
- 현재 Slice: FE7-05 completed (FE7-06 draft)

## 목적

정책 상세 `핵심 신청 조건` 카드(FE7-01~04)를 Integration 08 W4-G0 proposal
DTO·Mock-first detail envelope에 맞춰 구현하고 Browser E2E(FE7-05)로 검증한다.

## Forest 범위

이 기록은 Frontend 07 Slice 구현·검증 결과를 누적한다. W4-G0 승인 전
`eligibility_summary` nested 구조는 proposal이며 Real API summary 필드는
Backend merge 후 Real API golden E2E에서 재검증한다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE7-00 | completed | DTO·Mock fixtures·contract tests |
| FE7-01 | completed | EligibilitySummaryCard shell·ProgramDetailPage wiring |
| FE7-02 | completed | EligibilitySectionList·category badge·long text expand |
| FE7-03 | completed | EligibilityComparisonBadge·local conditions compare util |
| FE7-04 | completed | EligibilityEvidenceLink·공식 원문 CTA |
| FE7-05 | completed | Playwright Browser E2E·search golden 회귀 |

## 구현 내용

### FE7-00 — Eligibility summary DTO·Mock

- `frontend/src/types/eligibilitySummary.ts`
- `frontend/src/mocks/policyDetailFixtures.ts` (id 9101~9103)
- `frontend/tests/eligibilitySummary.contract.test.ts`

### FE7-01~04 — 핵심 신청 조건 카드 UI

- `frontend/src/components/eligibility/EligibilitySummaryCard.tsx`
  - loading·error·empty shell, partial·unknown banner
  - `POLICY_ELIGIBILITY_NOTICE`와 역할 분리(정책 정보 카드 vs summary 카드)
- `frontend/src/components/eligibility/EligibilitySectionList.tsx`
  - requirements·exclusions·preferences·documents·unknown_conditions 섹션
  - category badge, 긴 문장 expand toggle (`aria-expanded`)
- `frontend/src/components/eligibility/EligibilityComparisonBadge.tsx`
- `frontend/src/components/eligibility/EligibilityEvidenceLink.tsx`
  - `source_id`·`collected_at`·`source_url` only; credential·internal id 미표시
- `frontend/src/utils/eligibilitySummaryDisplay.ts` — category label·text truncate
- `frontend/src/utils/eligibilityComparison.ts`
  - FE5 saved conditions 대비 age·region·category compare
  - copy: `조건상 일치|불일치|추가 확인 필요`
- `frontend/src/pages/user/ProgramDetailPage.tsx` — summary 카드 추가
- `frontend/src/mocks/policyContract.ts` — Mock detail fixture lookup wiring

### FE7-05 — Real API·Browser E2E (Playwright)

- `frontend/e2e/eligibility-summary-ui.spec.ts`
  - Mock-first 12 scenarios: complete·partial·unknown fixtures(9101~9103),
    seed policy empty summary, saved conditions comparison badges,
    evidence link `rel` attributes, keyboard·mobile, `/search` golden 회귀,
    search→detail navigation regression, mock detail envelope golden
  - Real API golden: `VITE_USE_MOCK=false` 환경에서만 실행(skip)
- Mock fixture에 120자 초과 문장 없음 — `더 보기`/`접기` expand toggle E2E는
  `eligibilitySummaryDisplay` unit test로 검증.
- Backend `eligibility_summary` 미merge — Real API golden은 summary card 또는
  empty state 분기만 검증.
- FE7-06 Toast·5xx refetch·section keyboard nav subset은 본 Slice 범위 밖.

### 계약 정렬 메모

| 영역 | FE7 proposal | Backend 상태 |
| --- | --- | --- |
| Detail `eligibility_summary` | optional nested | `feature/backend/policy-recommendation` 미merge |
| Evidence fields | `source_id`, `source_url`, `collected_at` | Backend draft 동일 |
| Mock Browser ids | 9101~9103 | `findMockPolicyById` fixture fallback |

Real API detail에 summary가 없으면 카드 empty state를 표시한다(FE7-05 Mock·Real API 분기 검증).

## 설계 결정

- List·search 응답은 `eligibility_summary`를 생략; detail Mock fixture(9101~9103)만
  구조화 summary를 포함.
- evidence 없는 항목은 UI에서 "원문 근거 확인 필요" copy; 임의 구조화하지 않음.
- age·region compare는 policy numeric bounds·regions 배열을 우선 사용; 복잡한
  income·asset category는 badge 미표시 또는 evidence null 시 `추가 확인 필요`.
- 카드 footer·banner copy는 W4-G0 비단정 원칙(신청 가능/불가 단정 금지) 준수.
- FE7-06 Toast·a11y subset은 본 Slice 범위 밖.

## 주요 변경 파일

- `frontend/src/components/eligibility/*.tsx`
- `frontend/src/utils/eligibilitySummaryDisplay.ts`
- `frontend/src/utils/eligibilityComparison.ts`
- `frontend/src/pages/user/ProgramDetailPage.tsx`
- `frontend/src/mocks/policyContract.ts`
- `frontend/src/styles/theme.css`
- `frontend/tests/eligibilityComparison.test.ts`
- `frontend/tests/policyMockDetail.test.ts`
- `frontend/tests/eligibilitySummary.contract.test.ts`
- `frontend/tsconfig.test.json`
- `frontend/e2e/eligibility-summary-ui.spec.ts`

## 검증 결과

```text
cd frontend && npm test   — 159 passed
cd frontend && npm run lint — passed
cd frontend && npm run test:e2e -- e2e/eligibility-summary-ui.spec.ts — 12 passed, 1 skipped (Real API)
python3 scripts/validate_docs.py — passed
```

Browser·Playwright E2E는 FE7-05에서 실행 완료.

## 남은 작업

- FE7-06: Detail Toast·a11y subset
- W4-G0 Gate 승인 후 `docs/api/policies.md` detail `eligibility_summary` 절 추가
- Backend Integration 08 ES2 merge 후 Real API eligibility summary golden 재검증

## 관련 문서

- [Integration 08 Eligibility Evidence](../../develop_plan/integration/08_eligibility_evidence_summary.md)
- [User Service Features (FE5)](../../develop_plan/frontend/05_user_service_features.md)
