# Frontend Eligibility Summary UI Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [Eligibility Summary UI Forest 개발 계획](../../develop_plan/frontend/07_eligibility_summary_ui.md)
- 현재 Slice: FE7-00 completed

## 목적

정책 상세 `핵심 신청 조건` 카드(FE7)의 TypeScript DTO·Mock detail envelope
기준선(FE7-00)을 Integration 08 W4-G0 proposal과 Backend draft에 맞춰
구현한다.

## Forest 범위

이 기록은 Frontend 07 Slice 구현·검증 결과를 누적한다. W4-G0 승인 전
`eligibility_summary` nested 구조는 proposal이며 UI(FE7-01+)는 이 Slice에서
범위 밖이다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE7-00 | completed | DTO·Mock fixtures·contract tests |
| FE7-01 | pending | ProgramDetailPage 카드 shell |
| FE7-02 | pending | requirements/exclusions/documents/unknown 섹션 |

## 구현 내용

### FE7-00 — Eligibility summary DTO·Mock

- `frontend/src/types/eligibilitySummary.ts`
  - `EligibilitySummaryDto`, `ItemConditionDto`, `ItemDocumentDto`,
    `ItemEvidenceDto`, `InstitutionalContactDto`
  - `status`: `complete` \| `partial` \| `unknown`
  - category: Integration 08 W4-G0 분류(age·region·income·…·other)
- `frontend/src/types/policy.ts`
  - optional `eligibility_summary` on `PolicyDto`
  - `PolicyDetailDto` detail envelope alias
- `frontend/src/mocks/policyDetailFixtures.ts`
  - complete·partial·unknown Mock detail envelope 각 1건 (id 9101~9103)
- `frontend/src/mocks/eligibilitySummaryContract.ts`
  - Integration 08 / Backend draft shape assertion
  - evidence public key only (`source_id`, `source_url`, `collected_at`)
- `frontend/tests/eligibilitySummary.contract.test.ts`

### 계약 정렬 메모 (Backend draft vs Integration 08)

| 영역 | Integration 08 W4-G0 | Backend draft (`policy-recommendation`) | FE7-00 |
| --- | --- | --- | --- |
| `ItemEvidence` | snippet·field·selector 후보 | `source_id`, `source_url`, `collected_at` only | Backend draft 따름 |
| `institutional_contacts` | 표에 없음 | list on summary | 포함 (Backend draft) |
| Detail field | proposal | `PolicyRead.eligibility_summary` optional | `PolicyDto` optional |

Real API `eligibility_summary`는 로컬 Backend merge 전까지 detail 응답에
없을 수 있다. FE7-05에서 `origin/feature/backend/policy-recommendation`
merge 후 재검증.

## 설계 결정

- List·search 응답은 `eligibility_summary`를 생략하거나 `null`로 두고,
  detail Mock fixture만 구조화 summary를 포함한다.
- W4-G0 evidence 확장(snippet·selector)은 Gate 승인·Backend OpenAPI 반영
  후 타입을 확장한다(FE7-04·FE7-05).
- 기존 `eligibility_text` 필드는 유지; FE7-01에서 카드와 notice 역할 분리.

## 주요 변경 파일

- `frontend/src/types/eligibilitySummary.ts`
- `frontend/src/types/policy.ts`
- `frontend/src/mocks/policyDetailFixtures.ts`
- `frontend/src/mocks/eligibilitySummaryContract.ts`
- `frontend/tests/eligibilitySummary.contract.test.ts`
- `frontend/tsconfig.test.json`

## 검증 결과

- `npm run test` (frontend): **88 passed** (eligibility contract 7건 포함)
- `npm run lint`: passed
- `npm run build`: passed
- `python scripts/validate_docs.py`: passed

## 남은 작업

- FE7-01: `EligibilitySummaryCard`·`ProgramDetailPage` wiring
- FE7-05: Real detail API·Browser E2E
- W4-G0 Gate 승인 후 `docs/api/policies.md` detail `eligibility_summary` 절 추가

## 관련 문서

- [Integration 08 Eligibility Evidence](../../develop_plan/integration/08_eligibility_evidence_summary.md)
- [User Service Features (FE5)](../../develop_plan/frontend/05_user_service_features.md)
