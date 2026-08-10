# Frontend Eligibility Summary UI Forest 개발 계획

## 계획 정보

- 번호: Frontend 07
- 담당 영역: Frontend
- 상태: draft
- 계획일: `2026-08-11`
- 대상 Release: `v0.5.0`
- 공통 시작 커밋: `22118b8e618c3b15464865be3113157888197a02`
- 4주차 대응: `W4-FE1`, Critical Path B (`week_04_v0_5_0.md`)
- 선행 Forest:
  [Integration 05 Contract Baseline](../integration/05_v0_5_0_contract_baseline.md),
  [Integration 08 Eligibility Evidence](../integration/08_eligibility_evidence_summary.md)
  (ES2 Backend DTO)
- 후속 Forest: Integration 07 Release 2 Feature Acceptance
- 권장 브랜치: `feature/frontend/eligibility-summary`
- 현재 Slice: FE7-00 draft (계획 수립)

## 목적

정책 상세에 `핵심 신청 조건` 카드를 추가해 필수·제외·우대·서류·확인 필요
항목을 evidence와 함께 표시하고, 로컬 사용자 조건이 있을 때 비교 상태만
제공한다. 최종 신청 가능 여부를 단정하지 않는다.

## 범위

- Integration 08 eligibility summary DTO TypeScript 소비
- `ProgramDetailPage` 핵심 신청 조건 카드 UI
- 필수·제외·우대·서류·unknown 섹션 시각 구분
- Source URL·수집 시각·원문 이동 링크
- 로컬 조건(FE5-02) 대비 `조건상 일치|불일치|추가 확인 필요` badge
- partial·unknown·empty·error·긴 문장 표시
- Mock-first → actual API 연결과 Browser E2E

## 범위 밖

- Data Extractor·Normalizer·evidence 수집 (Integration 08 ES1)
- Backend 상세 DTO 구현 (Integration 08 ES2)
- LLM 요약·자격 자동 판정 UI
- 추천 결과 UI (Frontend 06)

## 선행 조건

- W4-G0 eligibility summary 필드·`complete|partial|unknown` 의미 확정
- 기존 `eligibility_text` 호환·폐기 여부 소비자 검토
- Policy detail API numeric id·`include_partial` opt-in 유지 (Frontend 01)

## 공통 설계 원칙

- 카드 제목 기본: `핵심 신청 조건`; `신청 가능`/`불가` 단정 금지.
- evidence 없는 항목은 확인 필요로 표시하고 임의 구조화하지 않는다.
- 개인 비교는 FE5 conditions와 연동하되 서버 전송 없음.
- 기존 Release 1 상세 필드(출처·수집 시각) 레이아웃 유지.

## 공통 API 오류 Toast·접근성 (W4-F5·W4-F8)

자격요건 카드(FE7)는 Policy detail fetch 실패·summary block 오류에 공통 Toast를
사용한다. 전체 회귀는 [Frontend 09 FE9-02](09_integration_and_regression.md).

### API 오류 Toast

| HTTP | UX | 재시도 | 비고 |
| --- | --- | --- | --- |
| `404` | detail not found shell (기존) | no | summary block hide |
| `422` | validation inline (include_partial 등) | no | |
| `5xx` | retryable Toast on summary refetch | yes | detail 본문은 유지 |
| partial envelope | 카드 내부 partial banner | no | `complete\|partial\|unknown` |

- eligibility evidence fetch 실패 시 항목별 fallback copy; stack trace 비노출.
- Toast dedupe 3s; 카드 내부 error와 global Toast 중복 금지.

### 키보드·모바일 접근성 (a11y)

- 긴 조건 문장: wrap·expand toggle, `aria-expanded` on truncate control.
- evidence link: visible focus ring, 새 탭 `rel="noopener noreferrer"`.
- comparison badge: text+icon, color-only 금지.
- section heading hierarchy (`h2` card → `h3` section).
- 모바일: section stack, horizontal scroll on wide evidence table 금지.

## Slice 계획

4주차 `W4-FE1`을 FE7-xx로 분해한다. Integration 08 ES3 Frontend 책임과
대응한다.

| Integration 08 | FE7 Slice | 책임 |
| --- | --- | --- |
| ES0 | FE7-00 | DTO·Mock·표본 fixture |
| ES3 | FE7-01 | 상세 카드 shell·layout |
| ES3 | FE7-02 | requirements/exclusions/documents/unknown |
| ES3 | FE7-03 | 로컬 조건 비교 badge |
| ES3 | FE7-04 | evidence·원문 링크 |
| ES4 | FE7-05 | Real API·Browser E2E |
| W4-F5·F8 | FE7-06 | Detail Toast·a11y |

---

### FE7-00 — Eligibility summary DTO·Mock — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | W4-G0 `eligibility_summary` 후보 필드를 TypeScript·Mock detail envelope에 반영 |
| **예상 변경 파일** | `types/eligibilitySummary.ts`, `mocks/policyDetailFixtures.ts` |
| **선행** | Integration 08 ES0, W4-G0 필드 표 |
| **검증** | contract test vs OpenAPI draft |
| **완료 기준** | complete·partial·unknown fixture 각 1건 |

---

### FE7-01 — 핵심 신청 조건 카드 shell — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | `ProgramDetailPage`에 summary 카드 영역·loading·error·empty |
| **예상 변경 파일** | `EligibilitySummaryCard.tsx`, `ProgramDetailPage.tsx` |
| **선행** | FE7-00 |
| **세부 작업** | `POLICY_ELIGIBILITY_NOTICE`와 카드 역할 분리 |
| **검증** | Browser Mock detail |
| **완료 기준** | partial policy에서 카드·PartialBadge 공존 |

---

### FE7-02 — 조건 섹션 UI — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | requirements·exclusions·preferences·documents·unknown_conditions 목록 |
| **예상 변경 파일** | `EligibilitySectionList.tsx`, category label helpers |
| **선행** | FE7-01 |
| **세부 작업** | age·region·income 등 category badge; 긴 문장 wrap |
| **검증** | Mock complete·partial·unknown |
| **완료 기준** | 빈 배열 vs null 의미 Backend와 일치 |

---

### FE7-03 — 로컬 조건 비교 badge — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | FE5 `conditions` 있을 때 항목별 비교 상태 표시 |
| **예상 변경 파일** | `EligibilityComparisonBadge.tsx`, comparison util |
| **선행** | FE7-02, FE5-02 (또는 Mock conditions) |
| **검증** | unit test; Browser with saved conditions |
| **완료 기준** | `조건상 일치|불일치|추가 확인 필요` only |

---

### FE7-04 — evidence·공식 원문 링크 — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | 항목 evidence(source·collected_at·snippet)와 `source_url` CTA |
| **예상 변경 파일** | `EligibilityEvidenceLink.tsx` |
| **선행** | FE7-02 |
| **검증** | Browser; credential·internal id 비노출 checklist |
| **완료 기준** | evidence DTO에 없는 DB 필드 UI 미표시 |

---

### FE7-05 — Real API·Browser E2E — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | actual detail API → 카드 → 원문 링크 E2E |
| **예상 변경 파일** | API client, Playwright detail spec |
| **선행** | FE7-03·04, Integration 08 ES2 |
| **검증** | golden policy detail; Release 1 회귀 |
| **완료 기준** | Integration 08 ES4 Frontend 항목 충족 |

---

### FE7-06 — Detail API Toast·접근성 — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | FE7 카드·detail에 Toast·a11y 명세 적용 |
| **예상 변경 파일** | `EligibilitySummaryCard.tsx`, shared Toast, a11y CSS |
| **선행** | FE7-01~04 |
| **세부 작업** | 본 문서 「공통 API 오류 Toast·접근성」표 준수 |
| **검증** | Browser 5xx refetch; keyboard section nav; long text expand |
| **완료 기준** | W4-F5·F8 eligibility subset; [FE9-02](09_integration_and_regression.md) matrix B |

## 검증 계획

```powershell
Set-Location frontend
npm run test
npm run lint
npm run build
npm run test:e2e
Set-Location ..
python scripts/validate_docs.py
```

## Forest 완료 기준

- 대표 complete·partial·unknown 정책 Browser 검증
- UI copy가 W4-G0 비단정 원칙 준수
- Release 1 상세·검색 golden 회귀
- Integration 08 ES3·ES4 Frontend 완료 기준 충족

## 위험과 미확정 사항

- W4-G0 전 `eligibility_summary` nested 구조가 변경될 수 있다.
- Data 04 웹 Source 필드는 점진 적재; UI는 API null·partial을 허용해야 한다.
- FE5-02 없이 비교 badge는 Mock-only 조건으로 검증 가능.

## 관련 문서

- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
- [Integration 08 Eligibility](../integration/08_eligibility_evidence_summary.md)
- [User Service Features (FE5)](05_user_service_features.md)
- [Frontend 09 Integration and Regression](09_integration_and_regression.md)
- [Policy API 계약](../../../api/policies.md)
