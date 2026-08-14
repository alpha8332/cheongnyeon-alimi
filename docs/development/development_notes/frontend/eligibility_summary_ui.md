# Frontend Eligibility Summary UI 개발 기록

## 작업 정보

- 작업일: `2026-08-10`~`2026-08-14`
- 담당 영역: Frontend
- 상태: completed
- 현재 권위 계약: [Integration 08 Eligibility Evidence](../../develop_plan/integration/08_eligibility_evidence_summary.md)
- 관련 계획: [Frontend 07 계획](../../develop_plan/frontend/07_eligibility_summary_ui.md)

## 목적

정책 상세의 `핵심 신청 조건`을 Integration 08 승인 계약으로 표시하고,
필수·제외·우대·필요 서류·자동 분류 불가 조건과 근거 원문을 사용자가 직접
확인할 수 있게 한다. 이 UI는 최종 신청 가능 여부나 개인 조건 일치 여부를
판정하지 않는다.

## Forest 범위

- Integration 08 승인 DTO의 Frontend 소비
- 정책 상세 조건·서류·문의처·evidence 표시
- 단위·Mock Browser·Real API 조건부 회귀
- DTL4-5~6의 과거 proposal 정리와 계약 정합성 확인

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE7-00~05 | completed | 승인 DTO·UI·단위·Browser 구현 |
| DTL4-5 | completed | 중복 proposal 구현 제거 |
| DTL4-6 | completed | 잔여 E2E·API hook·CSS·문서 정리 |

## 구현 내용

- `frontend/src/types/policy.ts`: `EligibilitySummaryDto`와 coverage enum
- `frontend/src/components/policy/EligibilitySummary.tsx`: coverage 안내, 섹션 목록, evidence와 원문 링크
- `frontend/src/pages/user/ProgramDetailPage.tsx`: 상세 응답의 summary 렌더링
- `frontend/src/mocks/policyContract.ts`: 승인 DTO 기반 Mock detail
- `data/fixtures/contracts/eligibility_evidence_cases.json`: 공통 계약 fixture
- `frontend/tests/eligibilitySummary.test.ts`: 표시 계약 단위 테스트
- `frontend/e2e/eligibility-summary-ui.spec.ts`: complete·partial·unknown, evidence, 모바일·검색 회귀와 Real API 조건부 검증
- `frontend/e2e/week4-regression.spec.ts`: 상세 → 근거 → 공식 원문 Critical Path B

## 표시 계약

| 필드 | 표시 규칙 |
| --- | --- |
| `coverage` | `complete`·`partial`·`unknown`을 비단정 안내 문구로 표시 |
| `requirements` | 필수 조건 목록 |
| `exclusions` | 제외 조건 목록 |
| `preferences` | 우대 조건 목록 |
| `documents` | 필요 서류 목록 |
| `unknowns` | 자동 분류할 수 없어 원문 확인이 필요한 조건 |
| `contacts` | 공개된 문의처 |
| `evidence` | 근거 문구, 수집 시각, 안전한 공식 원문 링크 |

빈 목록과 `unknown`은 임의로 보완하지 않는다. 증거가 없으면 원문 확인 안내만
표시하며, 비밀값·내부 식별자·Raw 응답은 노출하지 않는다.

## DTL4-5 계약 정리

과거 FE7 proposal의 `status`·`required_documents`·`unknown_conditions`와
Integration 08의 `coverage`·`documents`·`unknowns`가 중복되어 있었다.
DTL4-5에서 실제 소비 중인 Integration 08 DTO를 권위로 확정하고 사용되지 않는
proposal 타입·컴포넌트·fixture·단위 테스트를 제거했다.

## DTL4-6 회귀 정리

코드 정리 뒤에도 과거 proposal의 fixture id `9101`~`9103`, summary 전용
새로고침 오류 hook, 개인 조건 비교 배지, 전용 Toast E2E와 CSS가 남아 있음을
발견했다. 다음과 같이 승인 계약으로 다시 정렬했다.

- `eligibility-summary-ui.spec.ts`를 현재 seed와 DTO 기반 시나리오로 교체
- `week4-regression.spec.ts`의 Path B를 seed policy id 1과 현재 문구로 수정
- 더 이상 존재하지 않는 summary refetch option·Mock 오류 hook 제거
- 전용 `eligibility-detail-toast-a11y.spec.ts`와 미사용 proposal CSS 제거
- Real API 수동 가이드와 회귀 기록에서 비교·새로고침 설명 제거

## 주요 변경 파일

- `frontend/src/api/policies.ts`
- `frontend/src/styles/theme.css`
- `frontend/e2e/eligibility-summary-ui.spec.ts`
- `frontend/e2e/week4-regression.spec.ts`
- `frontend/e2e/eligibility-detail-toast-a11y.spec.ts` (삭제)
- `docs/development/frontend_real_api_manual_testing_guide.md`

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| Frontend unit | 162 passed |
| lint | passed |
| production build | passed |
| Mock Browser 전체 분할 실행 | 79 passed, 11 conditional skips |
| Eligibility UI + Week 4 regression | 10 passed, 2 Real API conditional skips |
| 현재 계약 문자열·fixture id 잔재 검색 | active source/test 0건 |

조건부 skip은 `VITE_USE_MOCK=false`와 실제 Backend가 필요한 DTL4-7 항목이다.
Mock 실행의 실패나 미실행으로 통과 처리하지 않았다.

## 설계 결정

- 승인 DTO에 개인 프로필 비교 결과가 없으므로 일치·불일치 배지를 표시하지 않는다.
- 상세 응답 외 별도 eligibility refetch 계약이 없으므로 카드 전용 새로고침을 제공하지 않는다.
- evidence 링크는 공식 원문 확인 수단이며 신청 가능 판정 근거로 단정하지 않는다.
- 향후 필드 변경은 `docs/api/policies.md`, 공통 fixture, Backend schema와 Frontend 타입·Mock·테스트를 같은 Slice에서 함께 변경한다.

## 남은 작업

DTL4-7에서 실제 PostgreSQL·FastAPI·React를 연결해 조건부 Real API Browser
시나리오와 세 Critical Path를 검증한다.
