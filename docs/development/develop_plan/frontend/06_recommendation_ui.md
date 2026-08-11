# Frontend Recommendation UI Forest 개발 계획

## 계획 정보

- 번호: Frontend 06
- 담당 영역: Frontend
- 상태: draft
- 계획일: `2026-08-11`
- 대상 Release: `v0.5.0`
- 공통 시작 커밋: `22118b8e618c3b15464865be3113157888197a02`
- 4주차 대응: `W4-F3`, Critical Path C (`week_04_v0_5_0.md`)
- 선행 Forest:
  [Integration 05 Contract Baseline](../integration/05_v0_5_0_contract_baseline.md),
  [Integration 08 Eligibility Evidence](../integration/08_eligibility_evidence_summary.md),
  Backend 추천 API (Integration 06 R1)
- 후속 Forest: Integration 07 Release 2 Feature Acceptance
- 권장 브랜치: `feature/frontend/recommendation`
- 현재 Slice: FE6-04 completed (FE6-05 draft)

## 목적

W4-G0 승인 결정적 추천 API 계약을 Frontend TypeScript·Mock·UI로 소비하고,
조건 입력·추천 결과·이유·미확정 조건을 검색 route와 구분해 표시한다.
추천 UI는 자격 충족이나 수혜 가능성을 단정하지 않는다.

## 범위

- 추천 request·response DTO TypeScript 소비와 Mock API Client
- 사용자 조건 입력·수정 UI (Frontend 05 localStorage와 연동)
- 추천 결과 목록·loading·empty·error·partial shell
- `reason_codes`·`message`·미확정 조건·제외 이유 표시
- API 오류·재시도 토스트 (W4-F5)
- 긴 지역 목록 축약 (W4-F5)
- `/search`와 추천 route·상태 경계 문서화
- 실 API 연결과 Browser E2E (Integration 06 R3)

## 범위 밖

- 추천 Backend service·repository·OpenAPI 구현 (Integration 06 R1)
- ML·LLM·벡터·행동 학습 UI
- 점수를 자격 확률로 표시
- Frontend NL parser
- 자격요건 Source 수집·`핵심 신청 조건` 카드 (Frontend 07)

## 선행 조건

- Integration 05 `W4-G0_APPROVED`와 추천 DTO·비단정 문구 확정
- Integration 08 조건 구조·`조건상 일치|불일치|추가 확인 필요` 소비 검토
- Frontend 05 FE5-02 저장 조건 계약(또는 Mock-only 조건 form) 합의
- Release 1 golden 검색 회귀 기준선 유지

## 공통 설계 원칙

- 추천 score는 요청 간 절대 비교·자격 확률로 노출하지 않는다.
- Backend `MatchVerdict`·미확정 의미를 Policy Search와 동일하게 표시한다.
- 조건은 localStorage 또는 in-memory form에서만 관리하고 URL·서버에 영구 저장하지 않는다.
- Mock·실 API Client는 동일 public DTO만 사용한다.

## Slice 계획

4주차 Frontend `W4-F3`를 FE6-xx 실행 단위로 나눈다. Integration 06 R2와
1:1 대응하되 Frontend 파일·route·Browser 검증 책임만 포함한다.

| Integration 06 | FE6 Slice | 책임 |
| --- | --- | --- |
| R0 | FE6-00 | DTO·Mock·route 계약 |
| R2 (조건) | FE6-01 | 조건 입력·localStorage 연동 | completed |
| R2 (결과) | FE6-02 | 추천 결과·이유 UI | completed |
| R2 (오류) | FE6-03 | 오류·재시도·미확정 UX | completed |
| W4-F5 | FE6-04 | 지역 축약·접근성 | completed |
| R3 | FE6-05 | Real API·Browser E2E |

**W4-G0 미승인:** OpenAPI·TypeScript 초안만 작성하고 DTO 필드를 임의 추가하지 않는다.

---

### FE6-00 — 추천 DTO·Mock·route 계약 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | W4-G0 추천 response/request를 TypeScript·Mock handler·route shell로 고정 |
| **예상 변경 파일** | `types/recommendation.ts`, `api/recommendation.ts`, `mocks/recommendationHandlers.ts`, `App.tsx` route placeholder |
| **선행** | Integration 06 R0, W4-G0 추천 DTO 초안 |
| **인터페이스** | Backend OpenAPI와 1:1 field; 추천 전용 route (예: `/recommendations`) |
| **검증** | contract unit test; `npm run build` |
| **완료 기준** | Mock 200/422/empty; `/search` route와 분리 문서화 |

---

### FE6-01 — 조건 입력·localStorage 연동 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | region·age·category 조건 form과 Frontend 05 `conditions` 저장 연동 |
| **예상 변경 파일** | `RecommendationPage.tsx`, `RecommendationConditionForm.tsx`, FE5 storage util 소비 |
| **선행** | FE6-00, FE5-00 (localStorage contract) |
| **세부 작업** | form submit → 추천 API; 새로고침 복원; 전체 삭제 |
| **검증** | unit test (storage round-trip); Browser reload |
| **완료 기준** | 서버·URL에 조건 영구 저장 없음 |

2026-08-11 구현: `RecommendationConditionForm`, `savedConditionsForm` utils,
FE5 `useSavedConditions` 공유. submit → `postRecommendations`. unit
`savedConditionsForm.test.ts`. Browser reload는 FE6-05.

---

### FE6-02 — 추천 결과·이유 UI — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | 추천 hit 목록, `reason_codes`·`message`, row-level 미확정 조건 |
| **예상 변경 파일** | `RecommendationResultList.tsx`, `RecommendationResultCard.tsx`, reason helpers |
| **선행** | FE6-01 |
| **세부 작업** | Policy Search badge/reason 패턴 재사용; numeric policy id → `/programs/{id}` |
| **검증** | Mock fixtures M-rec1~n; Browser |
| **완료 기준** | 숫자 score·자격 단정 copy 없음 |

2026-08-11 구현: `RecommendationResultList`·`RecommendationResultCard`,
`recommendationReasonHelpers`, `buildRecommendationItemDetailPath`,
`FavoriteToggleButton` on results. score 미노출. Browser는 FE6-05.

---

### FE6-03 — API 오류·재시도·미확정 배너 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | 422/5xx mapper, retry, query-level·row-level unconfirmed banner |
| **예상 변경 파일** | `utils/recommendationErrors.ts`, toast/error shell components |
| **선행** | FE6-02 |
| **검증** | MSW 422/500; Browser |
| **완료 기준** | Policy Search error UX와 톤 일치 |

2026-08-11 구현: `recommendationErrors.ts`, Error/Empty/Loading shell,
`RecommendationUnconfirmedBanner` query-level + row-level unknown. unit
`recommendationErrors.test.ts`. MSW Browser는 FE6-05.

---

### FE6-04 — 지역 축약·기본 접근성 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | W4-F5 긴 지역 목록 truncate/expand, keyboard·mobile layout |
| **예상 변경 파일** | `RegionListCollapse.tsx`, theme CSS |
| **선행** | FE6-02 |
| **검증** | Browser 긴 지역 fixture; keyboard tab order |
| **완료 기준** | overflow without horizontal scroll on mobile |

2026-08-11 구현: `RegionListCollapse` on result cards, theme CSS mobile
word-break·toggle focus-visible. keyboard tab order Browser 검증은 FE6-05.

---

### FE6-05 — Real API·Browser E2E — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | PostgreSQL → FastAPI 추천 → React actual path |
| **예상 변경 파일** | API client env toggle, Playwright spec |
| **선행** | FE6-03·04, Integration 06 R1 merged |
| **검증** | `npm run test:e2e`; Release 1 golden search 회귀 |
| **완료 기준** | Integration 06 R3 인수 기준 Frontend 항목 충족 |

## 검증 계획

```powershell
Set-Location frontend
npm run test
npm run lint
npm run build
npm run test:e2e
Set-Location ..
python scripts/validate_docs.py
git diff --check
```

## Forest 완료 기준

- W4-G0 추천 DTO와 TypeScript·Mock·UI field 일치
- 조건·결과·이유·미확정이 Browser에서 W4-F3 요구 충족
- `/search` golden flow 회귀 유지
- localStorage 외 조건 영구 저장 없음
- `python scripts/validate_docs.py` 통과

## 위험과 미확정 사항

- 추천 score 공개 필드는 W4-G0에서 UI 노출 구간을 확정해야 한다.
- FE5-02 미완 시 조건 form을 Mock-only로 분리할지 병렬 합의 필요.
- Backend 추천 API 지연 시 Mock-first UI만 4주차 2일차(W4-G1)까지 가능.

## 관련 문서

- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
- [Integration 06 Recommendation](../integration/06_recommendation_vertical_slice.md)
- [User Service Features (FE5)](05_user_service_features.md)
- [Policy Search (FE4)](../frontend/04_policy_search.md)
- [v0.5.0 Contract Baseline](../integration/05_v0_5_0_contract_baseline.md)
- [Frontend 09 Integration and Regression](09_integration_and_regression.md)
