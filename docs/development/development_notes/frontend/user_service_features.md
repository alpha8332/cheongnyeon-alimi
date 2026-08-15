# Frontend User Service Features Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11 (FE5-07 Browser E2E: 2026-08-12)
- 담당 영역: Frontend
- 상태: completed
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [User Service Features Forest 개발 계획](../../develop_plan/frontend/05_user_service_features.md)
- 현재 Slice: FE5-07 completed (Forest Browser 검증 완료)

## 목적

브라우저 전용 사용자 조건·즐겨찾기 저장(FE5-00)·즐겨찾기 UI(FE5-01)·저장
조건 UI(FE5-02)를 구현한다.

## Forest 범위

이 기록은 Frontend 05 Slice 구현·검증 결과를 누적한다. Integration 05
W4-G0 승인 전 key·version은 proposal로 문서화한다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE5-00 | completed | versioned localStorage types·utils·unit test |
| FE5-01 | completed | favorites toggle·`/favorites`·card·detail sync |
| FE5-02 | completed | 저장 조건 UI·conditions-only clear |
| FE5-03 | completed | KST D-Day·`/calendar` 마감 달력 |
| FE5-04 | completed | 북마크 마감 임박 in-app `/notifications` |
| FE5-05 | completed | `.ics` 다운로드(상세) |
| FE5-08 | completed | localStorage 전체 삭제 UX |
| FE5-06 | completed | cross-route policy identity·nav |
| FE5-07 | completed | Playwright Browser·a11y·cross-route E2E |

## 구현 내용

### FE5-00 — versioned localStorage 계약

- `frontend/src/types/userLocalStorage.ts`
- `frontend/src/utils/userLocalStorage.ts`
- corrupt/version/shape → reset persist; storage unavailable → in-memory default

### FE5-01 — 즐겨찾기 UI·State

- `frontend/src/utils/userFavoritesStorage.ts`
  - `readFavoritePolicyIds`, `toggleFavoritePolicyId`, `subscribeFavoritePolicyIds`
  - cross-tab `storage` event 구독
- `frontend/src/hooks/useFavorites.ts`
  - `useSyncExternalStore`로 card·detail·favorites page state 동기화
- `frontend/src/components/policy/FavoriteToggleButton.tsx`
  - ☆/★ toggle, `aria-pressed`, click propagation 차단
- `frontend/src/pages/user/FavoritesPage.tsx`
  - bookmark id별 `getPolicyById(id, include_partial=true)` 병렬 fetch
  - empty·loading·error·missing id 안내
- `PolicyCard`, `ProgramDetailPage`에 toggle 연결
- 서버 즐겨찾기 API·계정 동기화 없음 (copy 명시)

### FE5-02 — 저장 조건 UI·State

- `frontend/src/utils/userConditionsStorage.ts`
  - `readSavedConditions`, `saveSavedConditions`, `clearSavedConditions`
  - `subscribeSavedConditions` + stable snapshot cache (`useSyncExternalStore` 호환)
  - cross-tab `storage` event 구독
- `frontend/src/hooks/useSavedConditions.ts`
- `frontend/src/components/user/SavedConditionsPanel.tsx`
  - region·age·category 편집·저장·조건-only 초기화
  - 브라우저-only·서버/URL 미저장 copy
- ~~`HomePage`에 panel 연결~~ → **2026-07-28 UX slice**: `/profile` `UserProfilePage`로 이전 (홈에서는 제거)
- `clearSavedConditions`는 `conditions: null`만 기록, `favorites` 유지

### FE5-03 — KST D-Day·달력 보기

- `frontend/src/utils/policyDeadline.ts`
  - `Asia/Seoul` KST date-only D-Day (`getPolicyDeadlineInfo`, `getDDayLabel`)
  - 종료일 null·상시·closed → calendar slot 생성 금지
- `frontend/src/utils/policyDisplay.ts` — `getDDayLabel` re-export
- `frontend/src/pages/user/CalendarPage.tsx` — `/calendar` 북마크·전체 정책 마감 목록
- `frontend/src/App.tsx` — `/calendar` route
- `frontend/tests/policyDeadline.test.ts`

### FE5-04 — 앱 내부 마감 임박 알림

- `frontend/src/utils/favoriteDeadlineAlerts.ts` — 북마크 ∩ D-7 이내 intersection
- `frontend/src/pages/user/NotificationsPage.tsx` — in-app 목록(외부 push 없음)
- `frontend/tests/favoriteDeadlineAlerts.test.ts`

### FE5-05 — `.ics` 다운로드

- `frontend/src/utils/policyIcs.ts` — RFC5545 subset escape·all-day VEVENT
- `frontend/src/components/user/PolicyIcsDownloadButton.tsx`
- `ProgramDetailPage` detail action (종료일 없으면 disabled)
- `frontend/tests/policyIcs.test.ts`

### FE5-08 — 사용자 localStorage 전체 초기화

- `frontend/src/utils/userDataReset.ts` — `resetAllUserLocalStorage` + subscriber notify
- `frontend/src/components/user/UserDataResetPanel.tsx` — 이중 confirm, favorites footer
- `FavoritesPage` footer wiring
- `frontend/tests/userDataReset.test.ts`

### FE5-06 — route 간 상태 일치

- `frontend/src/utils/userRouteIdentity.ts` — cross-route path constants·detail path
- `frontend/src/utils/policyDetailNavigation.ts` — `buildRecommendationItemDetailPath`
- 추천 결과·PolicyCard·Calendar detail link가 동일 numeric `policy.id` 사용
- `AppShellLayout` — `/recommendations`·`/calendar` sidebar nav
- `frontend/tests/userRouteIdentity.test.ts`
- `frontend/tests/recommendationDetailNavigation.test.ts`

## 설계 결정

| 항목 | 결정 | 근거 |
| --- | --- | --- |
| State 동기화 | `useSyncExternalStore` + module listeners | FE5-01 card·detail·page 동일 id without global Zustand |
| Favorites fetch | per-id `getPolicyById`, `include_partial=true` | partial bookmark 노출; 목록 API filter by id 없음 |
| Missing policy | note + skip render | API 404 id는 grid에서 제외, count 안내 |
| Key·version | FE5-00 proposal 유지 | W4-G0 승인 전 |
| Conditions object | `UserSavedConditions` 단일 계약 | FE6·FE7과 동일 `{region,age,category}` 공유 |
| Conditions clear | `conditions` 필드만 null | FE5-08 전체 삭제와 UX·범위 구분 |
| D-Day 기준 | KST date-only (`Intl` `Asia/Seoul`) | 로컬 timezone drift 방지 |
| In-app 알림 | 북마크 ∩ D-7, 종료일 필수 | 외부 push·Service Worker 없음 |
| `.ics` | all-day DATE, DTEND+1 | W4-G0 proposal; calendar client별 해석 차이 FE5-07 |
| Cross-route identity | numeric `policy.id` + shared detail path helper | search·recommend·favorites·calendar |

### FE5-07 — Browser·a11y·회귀 (Playwright)

- `frontend/e2e/user-service-features.spec.ts`
  - Mock-first 13 scenarios: 저장 조건 save/reload, 북마크 cross-route·reload,
    조건-only clear(북마크 유지), favorites/calendar/notifications empty·loading,
    localStorage 전체 reset→reload, ICS disabled(종료일 없음), sidebar nav,
    favorite keyboard Enter, mobile viewport(640px sidebar hidden), home→search golden
  - Real API favorites persistence: `VITE_USE_MOCK=false` 환경에서만 실행(skip)
- Mock Seed에 `application_end`+open 정책이 없어 달력·알림 D-7 positive case는
  empty shell 검증으로 대체(Integration actual 데이터 연결 시 FE9 회귀에서 보강).

## 주요 변경 파일

- `frontend/src/utils/userFavoritesStorage.ts`
- `frontend/src/hooks/useFavorites.ts`
- `frontend/src/components/policy/FavoriteToggleButton.tsx`
- `frontend/src/pages/user/FavoritesPage.tsx`
- `frontend/src/components/policy/PolicyCard.tsx`
- `frontend/src/pages/user/ProgramDetailPage.tsx`
- `frontend/src/styles/theme.css`
- `frontend/tests/userFavoritesStorage.test.ts`
- `frontend/tests/helpers/memoryStorage.ts`
- `frontend/src/utils/userConditionsStorage.ts`
- `frontend/src/hooks/useSavedConditions.ts`
- `frontend/src/components/user/SavedConditionsPanel.tsx`
- `frontend/src/pages/user/HomePage.tsx`
- `frontend/tests/userConditionsStorage.test.ts`
- `frontend/src/utils/policyDeadline.ts`
- `frontend/src/utils/favoriteDeadlineAlerts.ts`
- `frontend/src/utils/policyIcs.ts`
- `frontend/src/utils/userDataReset.ts`
- `frontend/src/pages/user/CalendarPage.tsx`
- `frontend/src/pages/user/NotificationsPage.tsx`
- `frontend/src/components/user/PolicyIcsDownloadButton.tsx`
- `frontend/src/components/user/UserDataResetPanel.tsx`
- `frontend/tests/policyDeadline.test.ts`
- `frontend/tests/favoriteDeadlineAlerts.test.ts`
- `frontend/tests/policyIcs.test.ts`
- `frontend/tests/userDataReset.test.ts`
- `frontend/src/utils/userRouteIdentity.ts`
- `frontend/src/layouts/AppShellLayout.tsx`
- `frontend/tests/userRouteIdentity.test.ts`
- `frontend/tests/recommendationDetailNavigation.test.ts`
- `frontend/e2e/user-service-features.spec.ts`

## 검증 결과

```text
cd frontend && npm test   — 159 passed
cd frontend && npm run lint — passed
cd frontend && npm run build — passed
cd frontend && npm run test:e2e -- e2e/user-service-features.spec.ts — 13 passed, 1 skipped (Real API)
python3 scripts/validate_docs.py — passed
```

Browser cross-route·Playwright E2E는 FE5-07에서 실행 완료.

### FE5-01 hotfix — `/`·`/favorites` 404-like error boundary

- **원인**: `App.tsx` 라우트 누락이 아니라 `useFavorites`의
  `useSyncExternalStore`가 `getFavoritePolicyIdsSnapshot`에서 매번 새 배열
  참조를 반환해 React가 무한 re-render → layout `errorElement`(`NotFoundPage`)
  노출. `/search`는 `useFavorites` 미사용으로 정상.
- **수정**: `userFavoritesStorage.ts`에 snapshot cache·동일 내용 참조 유지
  (`syncFavoritePolicyIdsSnapshotFromStorage`, `EMPTY_FAVORITES_SNAPSHOT`).
- **라우트**: `App.tsx` index `/` → `HomePage`, `favorites` → `FavoritesPage`
  기존 등록 유지. Vite dev server SPA fallback 이상 없음(HTTP 200 확인).

## UX slice — 사이드 네비게이션·프로필 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: sidebar 메뉴 순서·라벨 정리, `/profile` 사용자 프로필, `내 조건 저장` 홈→프로필 이전

### 구현

- `AppShellLayout`: 홈 → 맞춤 추천 → 정책 목록 → 북마크 → 달력 → 알림 → (spacer) → 관리자 → 사용자 프로필. sidebar `정책 검색` 링크 제거 (`/search` route·홈 hero 검색은 유지).
- `UserProfilePage` (`/profile`): `SavedConditionsPanel` 단독 배치.
- `HomePage`: `SavedConditionsPanel` 제거.
- `userRouteIdentity`: `USER_CROSS_ROUTE_PATHS.profile` 추가.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 162 pass |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (user-service·week4·recommendation-ui) | 30 pass, 3 skip (Real API) |
| `python3 scripts/validate_docs.py` | pass |

### 설계 유지

- `localStorage` key·`UserSavedConditions` 계약·`useSavedConditions` hook 변경 없음.
- `UserDataResetPanel`(북마크 페이지) 위치는 본 slice 범위 밖 — favorites footer 유지.

## 남은 작업

- W4-G0 승인 시 key·version·KST 규칙 동기화
- Real API E2E(`VITE_USE_MOCK=false`) 및 D-7 알림 positive Browser case는
  Backend actual Policy API·Seed 마감일 데이터 준비 후 FE9 또는 별도 회귀에서 실행

## 관련 문서

- [User Service Features 계획](../../develop_plan/frontend/05_user_service_features.md)
- [v0.5.0 Contract Baseline](../../develop_plan/integration/05_v0_5_0_contract_baseline.md)
