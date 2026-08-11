# Frontend User Service Features Forest 개발 계획

## 계획 정보

- 번호: Frontend 05
- 담당 영역: Frontend
- 상태: draft
- 계획일: `2026-08-07`
- Slice 계획 갱신: `2026-08-11`
- 구현 시작: `2026-08-11` (FE5-00)
- 대상 Release: `v0.5.0`
- 공통 시작 커밋: `22118b8e618c3b15464865be3113157888197a02`
- 4주차 대응: `W4-F4`, Critical Path C (`week_04_v0_5_0.md`)
- 선행 Forest: Integration 05 Contract Baseline
- 후속 Forest: Integration 07 Release 2 Feature Acceptance
- 권장 브랜치: `feature/frontend/user-service-features`
- 현재 Slice: FE5-06 completed (FE5-07 draft)

## 목적

일반 사용자 계정 없이 브라우저에 최소 조건과 즐겨찾기를 저장하고, 정책의
신청 종료일을 기반으로 D-Day·앱 내부 알림·`.ics` 다운로드를 제공한다.

## 범위

- versioned localStorage 사용자 조건과 즐겨찾기
- 저장 데이터 검증, 손상 복구, version 불일치 초기화와 전체 삭제
- 정책 identity 기반 즐겨찾기 추가·해제
- `Asia/Seoul` 기준 D-Day와 날짜 미상·상시·마감 상태
- 즐겨찾기 정책의 앱 내부 마감 임박 알림
- 정책별 `.ics` 생성·다운로드와 안전한 텍스트 escaping
- 검색·추천·상세 route 간 상태 일치
- loading·empty·error·partial, 키보드·모바일 기본 검증

## 범위 밖

- 회원가입·로그인·서버 저장과 다중 기기 동기화
- 외부 push·이메일·SMS와 Service Worker 알림
- 외부 캘린더 계정 OAuth·자동 등록
- Source에 종료일이 없는 정책의 임의 D-Day 생성

## 선행 조건

- Integration 05의 `W4-G0_APPROVED`와 localStorage·날짜 계약이 필요하다.
- Policy identity와 신청기간 상태의 현재 API 의미를 확인한다.
- 지원 Browser와 `.ics` 다운로드 검증 방법을 합의한다.

## 공통 설계 원칙

- 저장 데이터는 최소화하고 사용자가 한 번에 초기화할 수 있게 한다.
- 날짜 미상·상시 정책에 임의 마감일을 만들지 않는다.
- localStorage 오류가 검색·상세 기본 기능을 막지 않게 격리한다.
- 앱 내부 알림은 외부 전송이나 background notification을 의미하지 않는다.

## Slice 계획

4주차 [`week_04_v0_5_0.md`](../../weekly_plan/week_04_v0_5_0.md) 사용자 Frontend
(`W4-F4`)를 FE5-xx 실행 단위로 나눈다. U0~U3 Forest 묶음과 대응 관계는
아래 표를 따른다.

| Forest 묶음 | FE5 Slice | 4주차 | 책임 |
| --- | --- | --- | --- |
| U0 | FE5-00 | F4 | versioned localStorage 계약 | completed |
| U1 | FE5-01 | F4 | 즐겨찾기 UI·State | completed |
| U1 | FE5-02 | F4 | 저장 조건 UI·State | completed |
| U2 | FE5-03 | F4 | KST D-Day·달력 보기 | completed |
| U2 | FE5-04 | F4 | 앱 내부 마감 임박 알림 | completed |
| U3 | FE5-05 | F4 | `.ics` 다운로드 | completed |
| U1~U3 | FE5-06 | F4 | route 간 상태 일치 | completed |
| U0 | FE5-08 | F4 | 사용자 localStorage 전체 초기화 UX | completed |
| W4-F5 | FE5-07 | F5 | Browser·a11y·Release 1 회귀 |

**W4-G0 미승인:** localStorage key·version·KST 날짜 규칙은 Integration 05
초안을 proposal로만 기록한다. Gate 승인 전 임의 key를 production 상수로
고정하지 않는다.

**Mock-first:** W4-G0 대기 중에도 FE5-00·FE5-01은 Policy API numeric id만
사용하므로 Mock policy detail과 병렬 가능(week_04 실행 원칙 5·7).

---

### FE5-00 — versioned localStorage 계약 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | browser-only user payload key·schema_version·허용 필드·corrupt recovery |
| **예상 변경 파일** | `types/userLocalStorage.ts`, `utils/userLocalStorage.ts` |
| **선행** | Policy `id` numeric contract (Frontend 01) |
| **인터페이스** | `favorites: number[]`, `conditions: {region,age,category}|null`, `updated_at` |
| **검증** | unit test (normalize·parse); SSR/no-storage graceful |
| **완료 기준** | corrupt·wrong version → reset; 검색·상세 flow 차단 없음 |

2026-08-11 구현: key `cheongnyeon-alimi.user-local.v1`, schema version `1`(W4-G0
proposal). `readUserLocalStorage`는 corrupt·unsupported version·invalid shape 시
default payload로 reset persist. storage unavailable 시 in-memory default만
반환. 후속 Slice(FE5-01~)는 `updateUserLocalStorage`·`clearUserLocalStorage`를
사용한다.

---

### FE5-01 — 즐겨찾기 UI·State — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | Policy id toggle·`/favorites` list·card·detail 동기 state |
| **예상 변경 파일** | `utils/userFavoritesStorage.ts`, `hooks/useFavorites.ts`, `FavoriteToggleButton.tsx`, `FavoritesPage.tsx`, `PolicyCard.tsx`, `ProgramDetailPage.tsx` |
| **선행** | FE5-00 |
| **세부 작업** | ☆/★ toggle; per-id detail fetch; no server sync copy |
| **검증** | unit test; Browser toggle·reload |
| **완료 기준** | 목록·상세·북마크 동일 id 상태 |

2026-08-11 구현: `useSyncExternalStore` 기반 `useFavorites`, `FavoriteToggleButton`을
PolicyCard·ProgramDetailPage에 연결. `/favorites`는 id별 `getPolicyById(include_partial=true)`
병렬 fetch. storage `storage` 이벤트로 탭 간 favorites 동기화.

2026-08-11 hotfix: `getFavoritePolicyIdsSnapshot`이 매 렌더 새 배열 참조를 반환해
`/`·`/favorites`에서 error boundary(404 UI)가 발생하던 문제를 snapshot cache로
수정. `App.tsx` 라우트 등록은 변경 없음.

---

### FE5-02 — 저장 조건 UI·State — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | region·age·category 저장·복원·**조건 필드만** 초기화 |
| **예상 변경 파일** | `utils/userConditionsStorage.ts`, conditions editor UI |
| **선행** | FE5-00 |
| **세부 작업** | FE6 recommendation·FE7 comparison과 동일 conditions 객체 공유; **즐겨찾기·알림 cache는 유지** |
| **검증** | unit + Browser reload |
| **완료 기준** | URL·서버·log에 조건 영구 저장 없음; favorites unchanged after conditions-only clear |

2026-08-11 구현: `userConditionsStorage` + `useSavedConditions` +
`SavedConditionsPanel`(홈 `/`). `saveSavedConditions`·`clearSavedConditions`는
FE5-00 `UserSavedConditions` 계약만 사용. 조건 초기화 시 favorites 유지.
Browser reload 검증은 FE5-07 범위.

---

### FE5-03 — D-Day·달력 보기 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | `Asia/Seoul` D-Day·마감·상시·미상; 즐겨찾기/전체 달력 route |
| **예상 변경 파일** | `utils/policyDeadline.ts`, `CalendarPage.tsx`, 기존 `getDDayLabel` 통합 |
| **선행** | FE5-01, Policy API 신청기간 의미 |
| **세부 작업** | 종료일 null → D-Day·달력 slot 생성 금지 |
| **검증** | unit KST boundary; Browser |
| **완료 기준** | week_04 날짜 미상·상시 규칙 준수 |

2026-08-11 구현: `policyDeadline.ts`(KST `Intl`), `CalendarPage` `/calendar`,
`policyDisplay.getDDayLabel` 통합, `PolicyCard` 마감 임박 tag. unit
`policyDeadline.test.ts`. Browser 검증은 FE5-07.

---

### FE5-04 — 앱 내부 알림 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | 즐겨찾기 ∩ 마감 임박 정책을 `/notifications` in-app 목록 |
| **예상 변경 파일** | `NotificationsPage.tsx`, `utils/favoriteDeadlineAlerts.ts` |
| **선행** | FE5-01, FE5-03 |
| **세부 작업** | 외부 push·Service Worker 없음 |
| **검증** | unit intersection logic; Browser |
| **완료 기준** | 비즐겨찾기·무기한 정책 알림 없음 |

2026-08-11 구현: `favoriteDeadlineAlerts.ts`, `NotificationsPage` in-app 목록.
unit `favoriteDeadlineAlerts.test.ts`. Browser 검증은 FE5-07.

---

### FE5-05 — `.ics` 다운로드 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | 정책별 마감 `.ics` 생성·download·RFC5545 subset escaping |
| **예상 변경 파일** | `utils/policyIcs.ts`, detail·favorites action button |
| **선행** | FE5-03, W4-G0 날짜 계약 |
| **검증** | unit escape; 대표 calendar client import |
| **완료 기준** | 종료일 없으면 버튼 disabled |

2026-08-11 구현: `policyIcs.ts`, `PolicyIcsDownloadButton`, `ProgramDetailPage`
detail action. favorites 목록 action은 FE5-07 Browser 회귀와 함께 검토.
unit `policyIcs.test.ts`.

---

### FE5-06 — route 간 상태 일치 — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | search·recommend·detail·favorites·calendar에서 동일 policy identity |
| **예상 변경 파일** | shared navigation utils, store hydrate on route enter |
| **선행** | FE5-01·02, Frontend 06 FE6-02 (추천) |
| **검증** | Browser cross-route scenario |
| **완료 기준** | favorite toggle이 route 이동 후 유지 |

2026-08-11 구현: `userRouteIdentity.ts`, `buildRecommendationItemDetailPath`,
추천 결과 `FavoriteToggleButton`, AppShell `/recommendations`·`/calendar` nav.
unit `userRouteIdentity.test.ts`, `recommendationDetailNavigation.test.ts`.
Browser cross-route 시나리오는 FE5-07.

---

### FE5-07 — Browser·a11y·회귀 — draft

| 항목 | 내용 |
| --- | --- |
| **목표** | W4-F5 loading·empty·error·partial·keyboard·mobile; Release 1 golden |
| **예상 변경 파일** | Playwright user-service spec, a11y copy |
| **선행** | FE5-01~06 |
| **검증** | `npm run test:e2e`; home→search golden |
| **완료 기준** | Forest Browser 완료 기준·W4-I2 사용자 E2E 준비 |

---

### FE5-08 — 사용자 localStorage 전체 초기화 UX — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | 즐겨찾기·저장 조건·앱 내부 알림 derived state·localStorage payload **전체 삭제** UX |
| **예상 변경 파일** | `UserDataResetPanel.tsx`, `clearUserLocalStorage()`, settings 또는 `/favorites` footer |
| **선행** | FE5-00, FE5-01~04 (초기화 대상 state 존재) |
| **세부 작업** | 이중 확인 dialog(「모든 북마크·조건·알림 설정이 삭제됩니다」); `USER_LOCAL_STORAGE_KEY` remove; in-memory Zustand/store reset; **서버 API 호출 없음** |
| **초기화 범위** | `favorites[]`, `conditions`, `schema_version` key 삭제; D-Day·알림·`.ics`는 저장 데이터 없음 — UI cache만 refresh |
| **검증** | unit `clearUserLocalStorage`; Browser: reset → favorites empty → notifications empty → reload 유지 |
| **완료 기준** | week_04 Forest 범위 「전체 삭제」; FE5-02 conditions-only clear와 UX·copy 구분; 검색·상세 기본 flow 차단 없음 |

**FE5-02 vs FE5-08:**

| Slice | 삭제 범위 | UX 위치 |
| --- | --- | --- |
| FE5-02 | `conditions` 필드만 null | 조건 편집 UI |
| FE5-08 | key 전체 remove (favorites+conditions) | 설정·북마크 footer 등 명시적 위험 action |

2026-08-11 구현: `userDataReset.ts`, `UserDataResetPanel`, `FavoritesPage`
footer. unit `userDataReset.test.ts`. Browser reset→reload 검증은 FE5-07.

---

### U0 - 로컬 저장 계약

- FE5-00·FE5-08. key, schema version, 허용 필드, corrupt recovery와 **전체 삭제**.

### U1 - 조건과 즐겨찾기

- FE5-01·FE5-02·FE5-06. identity 일치.

### U2 - D-Day와 내부 알림

- FE5-03·FE5-04. KST·즐겨찾기 기반 in-app only.

### U3 - 캘린더와 Browser 인수

- FE5-05·FE5-07·FE5-08. `.ics`, Browser 회귀, 전체 초기화.

전체 cross-Forest 회귀는 [Frontend 09 FE9-02](09_integration_and_regression.md).

## Forest 완료 기준

- 새로고침 후 조건·즐겨찾기가 계약대로 복원됨
- 손상·구버전 저장 데이터가 안전하게 복구 또는 초기화됨
- D-Day·알림이 KST와 Source 날짜 경계를 지키고 날짜를 추정하지 않음
- `.ics`가 대표 정책과 특수문자 표본에서 유효하게 생성됨
- localStorage 외 서버·로그·URL에 사용자 조건을 영구 저장하지 않음
- Frontend unit·lint·build·Browser 검증과 문서 검증 통과

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

## 위험과 미확정 사항

- localStorage key·version·최대 저장량과 migration 정책은 W4-G0 전 미확정이다.
- `.ics`의 all-day event와 마감일 포함 범위는 캘린더별 해석 차이가 있어 대표
  client에서 확인해야 한다.
- Source 신청기간이 null인 정책은 D-Day·알림 대상에서 제외해야 하며 임의
  보강은 Data 계약 변경 없이는 허용하지 않는다.

## 관련 문서

- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
- [Frontend 06 Recommendation UI](06_recommendation_ui.md)
- [Frontend 07 Eligibility Summary UI](07_eligibility_summary_ui.md)
- [Frontend 09 Integration and Regression](09_integration_and_regression.md)
- [v0.5.0 Contract Baseline](../integration/05_v0_5_0_contract_baseline.md)
- [Recommendation Vertical Slice](../integration/06_recommendation_vertical_slice.md)
- [Policy API 계약](../../../api/policies.md)
