# Frontend 07 Eligibility Summary UI 계획

## 계획 정보

- 번호: Frontend 07
- 담당 영역: Frontend
- 상태: completed
- 대상 Release: `v0.5.0`
- 권위 계약: [Integration 08 Eligibility Evidence](../integration/08_eligibility_evidence_summary.md)
- 후속 검증: DTL4-7 Real API E2E

## 목적

정책 상세에서 구조화된 핵심 신청 조건과 공식 근거를 표시한다. 사용자가
필수·제외·우대 조건, 필요 서류, 자동 분류 불가 조건과 문의처를 확인하도록
돕되 최종 신청 가능 여부는 판정하지 않는다.

## 공통 설계 원칙

| 구분 | 필드·규칙 |
| --- | --- |
| 상태 | `coverage`: `complete`·`partial`·`unknown` |
| 조건 | `requirements`, `exclusions`, `preferences` |
| 추가 확인 | `documents`, `unknowns`, `contacts` |
| 근거 | `evidence`의 문구·수집 시각·공식 원문 URL |
| 안전 | 비밀값·내부 식별자·Raw 응답 비노출 |
| 문구 | 신청 가능·불가를 단정하지 않고 원문 확인을 안내 |

## 범위

- `PolicyDto.eligibility_summary` TypeScript 계약
- `ProgramDetailPage`의 핵심 신청 조건 영역
- coverage 안내와 조건별 섹션
- evidence와 공식 원문 링크
- complete·partial·unknown Mock fixture와 단위·Browser 검증
- 실제 Backend 연결 시 조건부 Real API Browser 검증

## 범위 밖

- Extractor·Normalizer·evidence 수집
- Backend 상세 DTO와 DB mapping
- LLM 기반 신청 가능 판정
- 로컬 사용자 조건과의 자동 일치·불일치 비교
- 별도 eligibility summary 재생성·새로고침 API
- 검색 목록 응답에 summary 전문 포함

## 선행 조건

- Integration 08의 `EligibilitySummaryDto`와 Policy detail 응답이 확정돼야 한다.
- 공통 계약 fixture와 Backend schema·Frontend type이 동일해야 한다.
- Real API 검증에는 PostgreSQL test DB, Alembic head, FastAPI와 Chromium이 필요하다.

## Slice 계획

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE7-00 | completed | 승인 DTO·Mock·공통 fixture |
| FE7-01 | completed | 상세 페이지 카드와 coverage 안내 |
| FE7-02 | completed | 조건·서류·unknown·문의처 섹션 |
| FE7-03 | completed | evidence와 공식 원문 링크 |
| FE7-04 | completed | 단위·키보드·모바일 검증 |
| FE7-05 | completed | Mock Browser와 Real API 조건부 시나리오 |
| DTL4-5 | completed | 과거 proposal과 승인 DTO 중복 제거 |
| DTL4-6 | completed | 남은 E2E·API hook·CSS·문서 회귀 정리 |

## 권위 파일

- `backend/app/schemas/policy.py`
- `frontend/src/types/policy.ts`
- `frontend/src/components/policy/EligibilitySummary.tsx`
- `frontend/src/mocks/policyContract.ts`
- `data/fixtures/contracts/eligibility_evidence_cases.json`
- `frontend/tests/eligibilitySummary.test.ts`
- `frontend/e2e/eligibility-summary-ui.spec.ts`
- `frontend/e2e/week4-regression.spec.ts`

## 검증 계획

```powershell
Set-Location frontend
npm test
npm run lint
npm run build
npm run test:e2e
Set-Location ..
python scripts/validate_docs.py
```

전체 Browser 명령이 실행기 시간 제한에 걸리면 spec 그룹별로 분할하되, 모든
활성 spec의 종료 코드와 조건부 skip 수를 합산해 기록한다. `VITE_USE_MOCK=false`
시나리오는 실제 PostgreSQL·FastAPI가 준비된 DTL4-7에서 실행한다.

## Forest 완료 기준

- 승인 DTO와 TypeScript·Mock·UI가 동일한 필드명과 null/빈 목록 규칙을 사용한다.
- complete·partial·unknown과 evidence 원문 이동을 Browser에서 확인한다.
- 개인 조건 비교나 별도 refetch처럼 승인되지 않은 동작이 남아 있지 않다.
- unit·lint·build·Mock Browser와 문서 검증이 통과한다.
- Real API 조건부 항목의 실행 조건과 후속 Slice가 명시된다.

## 위험과 미확정 사항

- 실제 Backend를 연결하는 조건부 Browser 11건은 DTL4-7 실행 대상으로 남아 있다.
- 승인 DTO에 개인 비교나 강제 재구조화 계약이 추가되면 계약 문서와 세 영역
  소비 테스트를 먼저 함께 갱신해야 한다.

## 관련 문서

- [Eligibility Summary UI 개발 기록](../../development_notes/frontend/eligibility_summary_ui.md)
- [Integration 08 Eligibility](../integration/08_eligibility_evidence_summary.md)
- [Policy API 계약](../../../api/policies.md)
- [Frontend Real API 수동 테스트 가이드](../../frontend_real_api_manual_testing_guide.md)
