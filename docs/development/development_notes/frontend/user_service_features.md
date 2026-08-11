# Frontend User Service Features Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [User Service Features Forest 개발 계획](../../develop_plan/frontend/05_user_service_features.md)
- 현재 Slice: FE5-01 completed

## 목적

브라우저 전용 사용자 조건·즐겨찾기 저장(FE5-00)과 즐겨찾기 UI·동기
state(FE5-01)를 구현한다.

## Forest 범위

이 기록은 Frontend 05 Slice 구현·검증 결과를 누적한다. Integration 05
W4-G0 승인 전 key·version은 proposal로 문서화한다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE5-00 | completed | versioned localStorage types·utils·unit test |
| FE5-01 | completed | favorites toggle·`/favorites`·card·detail sync |
| FE5-02 | pending | 저장 조건 UI·State |

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

## 설계 결정

| 항목 | 결정 | 근거 |
| --- | --- | --- |
| State 동기화 | `useSyncExternalStore` + module listeners | FE5-01 card·detail·page 동일 id without global Zustand |
| Favorites fetch | per-id `getPolicyById`, `include_partial=true` | partial bookmark 노출; 목록 API filter by id 없음 |
| Missing policy | note + skip render | API 404 id는 grid에서 제외, count 안내 |
| Key·version | FE5-00 proposal 유지 | W4-G0 승인 전 |

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

## 검증 결과

```text
cd frontend && npm test   — passed (63 unit tests, FE5-00·FE5-01 snapshot cache 포함)
cd frontend && npm run lint — passed
cd frontend && npm run build — passed
python3 scripts/validate_docs.py — passed
```

Browser 수동 toggle·reload·Playwright E2E는 FE5-07 범위이며 FE5-01에서
실행하지 않았다.

### FE5-01 hotfix — `/`·`/favorites` 404-like error boundary

- **원인**: `App.tsx` 라우트 누락이 아니라 `useFavorites`의
  `useSyncExternalStore`가 `getFavoritePolicyIdsSnapshot`에서 매번 새 배열
  참조를 반환해 React가 무한 re-render → layout `errorElement`(`NotFoundPage`)
  노출. `/search`는 `useFavorites` 미사용으로 정상.
- **수정**: `userFavoritesStorage.ts`에 snapshot cache·동일 내용 참조 유지
  (`syncFavoritePolicyIdsSnapshotFromStorage`, `EMPTY_FAVORITES_SNAPSHOT`).
- **라우트**: `App.tsx` index `/` → `HomePage`, `favorites` → `FavoritesPage`
  기존 등록 유지. Vite dev server SPA fallback 이상 없음(HTTP 200 확인).

## 남은 작업

- FE5-02: conditions editor·conditions-only clear
- FE5-07: Browser·Playwright favorites 시나리오
- W4-G0 승인 시 key·version 동기화

## 관련 문서

- [User Service Features 계획](../../develop_plan/frontend/05_user_service_features.md)
- [v0.5.0 Contract Baseline](../../develop_plan/integration/05_v0_5_0_contract_baseline.md)
