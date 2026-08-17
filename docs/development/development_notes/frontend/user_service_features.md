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

## UX slice — 북마크 폴더·저장 모달 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: localStorage schema v2, 북마크 폴더 CRUD(브라우저), 폴더 탭 필터, 저장 모달

### 구현

- `userLocalStorage` schema v2: `bookmark_folders`, `bookmarks[{policy_id,folder_id}]`. v1 `favorites[]`는 read 시 `기본 폴더`로 migrate.
- `userFavoritesStorage`: `createBookmarkFolder`, `setBookmarkPolicy`, `removeBookmarkPolicy`, `getPolicyIdsForFolder`.
- `BookmarkFolderPickerModal`: 저장·폴더 변경·해제·모달 내 새 폴더 생성.
- `FavoriteToggleButton`: 클릭 시 모달 오픈 (즉시 toggle 제거).
- `FavoritesPage`: 폴더 탭·`+ 새 폴더 만들기`·폴더별 policy grid.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 167 pass |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (user-service·week4·recommendation-ui) | 31 pass, 3 skip (Real API) |
| `python3 scripts/validate_docs.py` | pass |

### UX slice — 월간 그리드 마감 달력 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: `/calendar` list view → ICS/Google Calendar 스타일 monthly grid

### 구현

- `calendarMonthGrid.ts`: Sunday-start 42-cell grid, month navigation, today/outside-month styling.
- `calendarPolicyEvents.ts`: `application_start`·`application_end` 이벤트 수집 (closed·상시 제외, FE5-03 end 규칙 유지 + start 추가).
- `CalendarMonthView`, `CalendarDayDetailDialog`: 월 헤더·뱃지·`+N개 더보기`·일정 상세 modal. *(2026-07-28 Apple 2패널 slice에서 `CalendarMonthView`·툴바/사이드바로 확장)*
- `CalendarPage`: scope toggle(북마크/전체) 유지, grid 항상 렌더.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 172 pass (+ calendar grid/events unit) |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (calendar paths in user-service·week4) | pass |
| `python3 scripts/validate_docs.py` | pass |

### 설계·후속

- `application_start` 표시는 slice 요청 반영; W4-G0 baseline은 end-only D-Day — Integration 후속 확인 권장.
- 주간/일간 뷰·드래그 reorder·전용 Backend calendar API는 범위 밖.
- Mock Seed open 정책에 `application_end`가 없어 E2E는 empty grid·badge absence 검증 위주.

## UX slice — 북마크 폴더 그리드 탐색기 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: `/favorites` 파일 매니저 스타일 폴더 그리드·브레드크럼·정렬·뷰 전환

### 구현

- `BookmarkExplorerToolbar`: `< 북마크 / 폴더명` 브레드크럼, 이름순·담긴 개수순 정렬, 그리드/리스트 뷰 토글.
- `BookmarkFolderGrid`: dashed `+ 새 폴더` 카드, 파스텔 폴더 SVG 카드, `이름 (개수)` 라벨(날짜 미표시), ☆ pin(sessionStorage)·`···` 메뉴.
- `BookmarkCreateFolderDialog`: 새 폴더 생성 modal.
- `FavoritesPage`: root=폴더 그리드, folder 진입=정책 카드; localStorage v2 schema 변경 없음. pin·view mode는 sessionStorage.

### 검증 (실행 후 기록)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 179 pass (+ bookmark explorer sort unit) |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (user-service·week4 bookmark paths) | 19 pass, 2 skip (Real API) |
| `python3 scripts/validate_docs.py` | pass |

### 설계·후속

- ~~폴더 rename/delete~~ → **2026-07-28 후속 slice**에서 delete 구현; rename·schema `pinned` 필드는 여전히 범위 밖. pin은 session-only.
- `BookmarkFolderPickerModal`(저장 modal) 계약 유지.

## UX slice — 북마크 폴더 더보기 메뉴·삭제 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: `BookmarkFolderGrid` `···` 메뉴 UX, 사용자 폴더 삭제(기본 폴더 보호)

### 구현

- `useDismissOnOutsidePress`: 메뉴 `mousedown` 바깥 클릭·`Escape` 닫기.
- `BookmarkFolderGrid`/`FolderCardMenu`: 구분선 + `폴더 삭제`(danger). `DEFAULT_BOOKMARK_FOLDER_ID`(`기본 폴더`)는 항목 미노출.
- `deleteBookmarkFolder`·`isDeletableBookmarkFolder`: localStorage v2에서 folder·해당 bookmarks 제거.
- `BookmarkDeleteFolderDialog`: "정말 이 폴더를 삭제하시겠습니까?" 확인 후 삭제; 취소 시 상태 유지.
- `FavoritesPage`: 삭제 중인 폴더 열람 시 root 복귀, pin session 정리.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 203 pass (+ deleteBookmarkFolder unit) |
| `npm run lint` | pass |
| `npm run build` | pass |
| `python3 scripts/validate_docs.py` | pass |

### 설계·후속

- 폴더 rename·다른 폴더로 bookmark 일괄 이동은 범위 밖.
- 삭제 시 folder 내 bookmark는 제거(다른 폴더로 merge하지 않음).

## UX slice — macOS/Apple Calendar 2패널 마감 달력 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: `/calendar` 단순 월간 격자 → macOS Calendar 스타일 2패널(사이드바 필터·미니 달력 + 메인 뷰)

### 구현

- `AppleCalendarLayout`: 좌측 분야 체크박스 필터(`calendarCategoryTheme.ts`)·미니 월간 picker, 좁은 화면 drawer 토글.
- `CalendarToolbar`: `Month YYYY` 타이틀, Day/Week/Month/Year 세그먼트, `< Today >` 탐색(`calendarViewNavigation.ts`).
- `CalendarMonthView`·`CalendarWeekView`·`CalendarDayView`·`CalendarYearView`: all-day 카테고리 칩 row, 오늘 빨간 원형 뱃지, `.monthly-calendar__grid`·`.calendar-event-badge` E2E selector 유지.
- `CalendarEventChip`·`CalendarEventDetailDialog`: 칩 클릭 시 정책명·신청 기간·지원 대상·신청 링크 modal. 일별 modal(`CalendarDayDetailDialog`) 유지.
- `CalendarPage`: scope toggle(북마크/전체) 유지, 카테고리 필터 후 `calendarPolicyEvents` 매핑.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 184 pass (+ calendar category/view navigation unit) |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (user-service·week4 calendar paths) | 4 pass, 1 skip (Real API) |
| `python3 scripts/validate_docs.py` | pass |

### 설계·후속

- Backend `end_date`/`apply_period` 필드 없음 — 기존 `application_start`·`application_end`만 사용(FE5-03 계약).
- Week/Day/Year는 타임라인 슬롯 없이 all-day 칩·목록 중심 MVP; 시간대별 스케줄·드래그 reorder·전용 calendar API는 범위 밖.
- Mock Seed에 `application_end` open 정책이 없어 E2E는 empty grid·badge absence 위주.
- `MonthlyCalendarGrid.tsx` 제거 — `CalendarMonthView`로 대체.

## UX slice — 마감 달력 일정 칩 텍스트·스타일 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: 날짜 칸·all-day·주/일 뷰 일정 칩 텍스트를 정책명(`title`)으로 통일, 말줄임·compact 스타일 개선

### 구현

- `CalendarEventChip`: 달력 칸 칩 기본 라벨을 `policy.title`로 고정(`showKindLabel`은 modal 헤더 전용). `calendar-event-chip__text` ellipsis.
- `CalendarMonthView`: `showTitle={false}`(신청 마감 고정 문구) 제거.
- `theme.css`: compact 칩 padding·font-size·min-height, 카테고리 색상 유지, flex `min-width: 0` truncate.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 184 pass |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (calendar paths) | 4 pass |
| `python3 scripts/validate_docs.py` | pass |

### 설계·후속

- `CalendarDayDetailDialog` 일별 modal 내 kind 뱃지(신청 시작·마감)는 날짜 칸 칩 범위 밖 — 유지.
- Mock Seed에 calendar 이벤트 없어 E2E는 badge count·grid visibility 위주.

## UX slice — 마감 달력 이벤트 미노출 버그 수정 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: Apple Calendar UI 개편 후 날짜 셀 칩 미렌더링·데이터 매핑 정상화

### 원인·수정

- **button 중첩**: `CalendarEventChip`(button)이 `monthly-calendar__day-button`(button) 내부에 있어 브라우저가 칩을 렌더하지 않음 → 날짜 선택 button과 칩을 형제 노드로 분리(`CalendarMonthView`).
- **ISO 날짜**: `application_end`/`application_start`가 `YYYY-MM-DDTHH:mm:ss` 형태일 때 `isValidYmd` 실패·그리드 `YYYY-MM-DD` 키 불일치 → `normalizePolicyYmd`(`policyDeadline.ts`) 도입, `calendarPolicyEvents`·D-Day 계산에 적용.
- **정책명 폴백**: `getPolicyDisplayTitle` — `title` → `policy_name`/`name`/`polyBizSjnm`/`plcyNm` → `category_text` → `'정책'`, HTML strip.
- **분야 필터**: API unknown category가 필터에서 전부 제외되던 문제 → unknown을 `other`로 매칭.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 189 pass (+ calendar event mapping unit) |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (calendar paths) | 4 pass |
| `python3 scripts/validate_docs.py` | pass |

### 설계·후속

- FE5-03 계약: `application_status: closed` 정책은 calendar slot 미생성 유지 — Mock seed id 1(합성 청년 주거)은 closed라 E2E empty grid 가능.
- closed 마감일도 달력에 표시하려면 FE5-03·Integration 합의 후 별도 slice.

## UX slice — 정책 상세 가독성·구조화 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: `/programs/:id` Summary Header·섹션 카드·Sticky Action Bar, 기존 `EligibilitySummary`·API schema 유지

### 구현

- `PolicyDetailSummaryHeader`: 상태/D-Day/카테고리 뱃지, 4대 메타 그리드(신청 기간·연령·지역·소득), 지원 혜택 하이라이트.
- `PolicyDetailSection`·`policyDetailContent.ts`: HTML strip·bullet 렌더, `getPolicyDisplayTitle`·소득(`eligibility_summary.income`) 추출.
- `PolicyDetailStickyActions`: 북마크(폴더 modal)·공식 신청·ICS 고정 하단 CTA. `FavoriteToggleButton` `labeled` prop.
- `ProgramDetailPage`: 자격/지원/신청/기관 섹션 분리, `📄 정책 정보` 메타 Card·`EligibilitySummary` 하단 유지.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 193 pass (+ policy detail content unit) |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (eligibility-summary-ui·week4 Path B·policy-search 7b·ICS) | 10 pass, 1 skip (Real API) |
| `python3 scripts/validate_docs.py` | pass |

### 설계·후속

- API에 `target_age`/`apply_period`/`policy_name` 단독 필드 없음 — `PolicyDto`·`eligibility_summary` 기존 계약 사용.
- 소득은 `eligibility_summary.requirements(income)` 우선; 없으면 `eligibility_text` 키워드·`'소득 기준 미확인'`.
- CTA 라벨 `원문 링크 열기` → `공식 신청 사이트 바로가기`(sticky); E2E selector 갱신.

## UX slice — 정책 목록·상세 가독성/스타일 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: 목록 카드 신청기간 포맷, 상세 메타 줄바꿈, 카테고리·상태 뱃지 달력 테마 일원화, 본문 ordered/bullet 리스트

### 구현

- `policyDisplay.ts`: `formatPolicyDateDot`, `formatApplicationPeriodCard`·`formatApplicationPeriodDisplay` — ISO·비정형 날짜를 `YYYY.MM.DD`로 정규화.
- `PolicyCategoryBadge`·`PolicyStatusBadge`: `calendarCategoryTheme`·`getPolicyStatusBadge` 재사용, 목록(`PolicyCard`·`PolicySearchResultCard`·`RecommendationResultCard`)·상세 header 공통.
- `PolicyDetailSummaryHeader`: 메타 값 `value-stack`/`value-line` 분리(개행·` · ` 구분).
- `policyDetailContent.splitPolicyTextToItems`: 번호·bullet·세미콜론 분리; `PolicyDetailTextContent` `preferOrdered`로 지원/신청 섹션 ordered list.
- `theme.css`: `.policy-card__period`, badge·meta stack·ordered list 스타일.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 198 pass (+ date format·text split unit) |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (eligibility-summary-ui·week4·policy-search-audit) | 20 pass, 3 skip (Real API) |
| `python3 scripts/validate_docs.py` | pass |

### 설계·후속

- API·schema 변경 없음 — 기존 `application_start`/`application_end`·본문 text 필드만 소비.
- 원문이 단일 문단이면 bullet/ordered 분리 없이 paragraph 유지.
- `RecommendationItemDto`에 `source_name`/`collected_at` 없음 — badge·기간 표시용 `toPolicyDto`는 최소 필드만 매핑.

## UX slice — 홈 마감 정책 제외·뱃지 테마 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: 홈 첫 화면 featured 카드 마감 필터, 상태·분야 뱃지 컬러 정교화

### 구현

- `isHomeFeaturedPolicy`(`policyDeadline.ts`): `closed`·`scheduled`·KST 지난 마감일 제외; `open`·`always`만 홈 featured.
- `HomePage`: `usePoliciesQuery({ status: 'open', limit: 12 })` + client filter → 최대 3건 `PolicyCard`.
- `getPolicyStatusBadge` variant: `always`(민트)·`open`(블루)·`hot`/`closed`(레드)·`warn`·`muted`.
- `PolicyStatusBadge`·`PolicyCategoryBadge`: status 전용 CSS + category는 `calendar-chip--*` CSS 변수 1:1 유지.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 199 pass (+ home featured filter unit) |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (user-service-features·week4-regression) | 19 pass, 2 skip (Real API) |
| `python3 scripts/validate_docs.py` | pass |

### 설계·후속

- ~~홈 default view 맞춤 추천~~ → **2026-07-28 후속 slice**에서 저장 조건 연동 구현(아래).
- `/programs` 전체 목록·검색 결과는 마감 정책 포함 유지(본 slice는 홈 default view만).

## UX slice — 홈 저장 조건 맞춤 추천 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: `HomePage` default view 추천 정책 — FE5 `UserSavedConditions`(region·age·category) + FE6 Recommendation API

### 구현

- `useHomeRecommendedPolicies`: 저장 조건 있음 → `postRecommendations(toRecommendationRequestFromConditions)`; 없음 → `usePoliciesQuery(status: open)` 폴백.
- 저장 조건 있을 때만 `"저장된 조건으로 추천된 정책입니다."` 캡션 노출; 없으면 추천 안내 문구 미노출.
- `isHomeRecommendablePolicy` / `isHomeFeaturedPolicy`: `closed`·`scheduled`·지난 마감 제외; `open`·`always`만.
- `recommendationItemToPolicyDto` 공통 util 추출 — 홈 `PolicyCard`·`/recommendations` 카드 공유.
- 추천 API 오류 시 캡션 없이 open 목록 폴백.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 207 pass (+ homeRecommendedPolicies unit) |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (user-service-features·week4-regression Path C) | pass |
| `python3 scripts/validate_docs.py` | pass |

### 설계·후속

- 홈 추천은 `/recommendations`와 동일 Recommendation API·공식 3필드만 사용; 임의 매칭 조건 추가 없음.
- 저장 조건 있으나 결과 0건일 때 empty copy만 표시(랜덤 폴백으로 대체하지 않음).
- Recommendation API는 `status` 미전달 시 closed 후보도 반환할 수 있음 — 홈은 `isHomeRecommendablePolicy`로 추가 제외(`/recommendations`와 목록 차이).

## UX slice — 정책 상세 헤더 레이아웃·액션 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: `PolicyDetailSummaryHeader` 북마크·헤더 내 액션 바, ○ 요약 분리·compact 날짜 정규화

### 구현

- `PolicyDetailSummaryHeader`: 뱃지+제목 행 우측 `FavoriteToggleButton`(폴더 modal 연동), 주관기관 아래 `PolicyDetailHeaderActions`.
- `PolicyDetailHeaderActions`: `공식 신청 사이트 바로가기 ↗`(gradient·`source_url` 새 탭), `캘린더 (.ics) 다운로드 📅`(기존 `policyIcs` util).
- `splitCircleBulletLines`: `○` 구분 요약·메타 텍스트 줄바꿈; `normalizePeriodTextDates`에 `YYYYMMDD` → `YYYY.MM.DD`.
- 하단 고정 `PolicyDetailStickyActions` 제거 — 액션을 헤더 카드 내부로 통합.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 200 pass (+ ○ split·compact date unit) |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (eligibility-summary-ui·week4·policy-search·user-service detail paths) | 34 pass, 4 skip (Real API) |
| `python3 scripts/validate_docs.py` | pass |

### 설계·후속

- Slice의 `apply_url` 필드는 API에 없음 — 공식 링크는 기존 `PolicyDto.source_url` 사용.
- ICS는 `application_end` 없으면 disabled 유지(FE5-05 계약).

## UX slice — 홈 검색 통합·레이아웃 (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`
- **범위**: 와이드스크린 메인 중앙 정렬, 홈 내 NL 검색 결과·필터 칩, `/search` → `/?q=` redirect, 프로필 저장 조건 API merge

### 구현

- `theme.css`: `.app-shell__main` `margin-inline: auto`·`justify-self: center` (max-width 1200px, 검색 활성 1440px).
- `HomePage`: `PolicySearchPage` 검색 UI·결과·sidebar를 홈 URL state(`/?q=…`)로 통합; 기본 뷰(추천 칩·주요 정책) ↔ 검색 결과 전환.
- `PolicySearchRedirect`: legacy `/search` query preserve → home.
- `policySearchSavedConditions.ts`: URL에 없는 `region`·`age`·`category`를 `UserSavedConditions`에서 API 요청에 merge.
- `PolicySearchPage.tsx` 제거; `buildPolicySearchEntryPath` → `/?q=…`.

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 175 pass (+ saved conditions merge unit) |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (policy-search-audit·week4·user-service·recommendation-ui) | 41 pass, 4 skip (Real API) |
| `python3 scripts/validate_docs.py` | pass |

### 설계·후속

- FE4-20 golden flow는 동일(홈 검색 → 결과 → 상세); URL만 `/search` → `/`.
- `/programs?search=` exact list filter route는 유지.
- `search_ux_preview.html`(루트 untracked)은 참고용이며 본 slice 산출물 아님.

## UX slice — 홈·카드·북마크 문구·D-Day (2026-07-28)

- **브랜치**: `feature/frontend/style-and-ux-fixes`

| 항목 | 변경 |
| --- | --- |
| 홈 hint | `더 많은 정책 보기` 하단 문구를 검색창·정책 목록 안내로 갱신 |
| `/recommendations` | 상단 `policy-eligibility-notice`·`RecommendationUnconfirmedBanner` 제거 |
| `RecommendationResultCard` | `unknown_conditions` 노란색 `추가 확인 필요` 박스 제거 |
| 검색 결과 카드 | `자격요건 직접 확인 필요`·unknown verdict 뱃지 제거 (partial 뱃지 유지) |
| `PolicyCard` | 마감일 있는 open 정책에 별 위 `D-nn`/`D-Day` (`getPolicyCardDDayBadgeLabel`) |
| `/favorites` | `UserDataResetPanel` 제거 |

### 검증 (실행 완료)

| 항목 | 결과 |
| --- | --- |
| `npm test` | 215 passed |
| `npm run lint` | pass |
| `npm run build` | pass |
| `npm run test:e2e` (recommendation·policy-search·user-service) | 35 passed, 3 skipped |
| `python3 scripts/validate_docs.py` | pass |

## W5-F1 인수 보완 — actual API E2E 재검증 (`2026-08-17`)

Team Leader 인수 보류 대응. Backend `127.0.0.1:8000`·`VITE_USE_MOCK=false`
환경에서 Real API golden E2E 4건을 실행했다.

| Spec | Real API golden | 결과 |
| --- | --- | --- |
| `policy-search-audit.spec.ts` | #8 상세·상시·접수 중 | pass |
| `recommendation-ui.spec.ts` | #13 | pass |
| `eligibility-summary-ui.spec.ts` | #110 DTL4-7 conditional | pass |
| `user-service-features.spec.ts` | #15 favorites | pass |

동일 env로 4 spec 전체(44 tests) 실행 시 Mock Seed 제목·id에 의존하는
Mock-first 시나리오 14건은 실패한다(의도된 env 분리). Mock 회귀는
`VITE_USE_MOCK=true`(기본)로 별도 실행한다.

## W5-F1 E2E actual API 정리 (`2026-08-17`)

Mock 전용 시나리오를 `skipIfActualApi`로 분리하고 actual DB fixture
(`e2e/helpers/e2eMode.ts`)를 도입했다.

| Spec | Actual API 결과 (44 tests) |
| --- | --- |
| `policy-search-audit.spec.ts` | 11 pass (golden #8 포함) |
| `recommendation-ui.spec.ts` | 10 pass, 4 mock skip |
| `user-service-features.spec.ts` | 15 pass |
| `eligibility-summary-ui.spec.ts` | 3 pass, 3 mock skip |

**합계:** `VITE_USE_MOCK=false` + Backend `:8000` — **37 passed, 7 skipped, 0 failed**

Fixture: 정책 id `160` 청년단기숙소 지원사업, ICS disabled id `3`, 추천
조건 천안시·27·housing. (handoff 예시 id `15095`는 현재 snapshot에 없음)

## 남은 작업

- W4-G0 승인 시 key·version·KST 규칙 동기화
- Real API E2E(`VITE_USE_MOCK=false`) 및 D-7 알림 positive Browser case는
  Backend actual Policy API·Seed 마감일 데이터 준비 후 FE9 또는 별도 회귀에서 실행

## 관련 문서

- [User Service Features 계획](../../develop_plan/frontend/05_user_service_features.md)
- [v0.5.0 Contract Baseline](../../develop_plan/integration/05_v0_5_0_contract_baseline.md)
