# Frontend Policy Search Forest 개발 기록

## 작업 정보

- 기간: 2026-08-05 ~ 2026-08-06
- 담당 영역: Frontend
- 상태: completed
- 구현 브랜치: `feature/frontend/policy-search`
- DT7D 통합 재검증 브랜치: `feature/data/release-dataset-bootstrap`
- 관련 계획:
  [Policy Search Forest 개발 계획](../../develop_plan/frontend/04_policy_search.md)
- 현재 Slice: FE4-24 completed (DT7D integration correction)

## 목적

Gate G1 승인 Backend 06 Policy Search 계약을 Frontend TypeScript production
타입으로 소비 가능하게 승격하고, Mock-first Search UI Slice를 구현한다.

## Forest 범위

- Gate G1 `GET /api/v1/policies/search` request·response TypeScript contract
- URL state·client error presentation types
- Mock-first Search UI, API Client, Browser 검증 (후속 Slice)

Frontend NL parser, Backend search endpoint 구현, Data Schema·Fixture·Seed
변경은 이 Forest 범위 밖이다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE4-14~17 | completed | Search UI core |
| FE4-18 | completed | Partial/Unknown badges |
| FE4-19 | completed | Reason sidebar + Uninterpreted UX |
| FE4-20 | completed | Home → `/search?q=` golden flow |
| FE4-21 | completed | Search hit → detail + include_partial |

## 구현 내용

### FE4-21 — Search → Detail link

#### PolicySearchResultCard

- 카드 전체·화살표 → `Link`로 `/programs/{id}` 이동
- `buildPolicySearchHitDetailPath(hit, searchIncludePartial)` 사용
- hover/focus 시 sidebar 선택 유지 (FE4-19 Reason panel)

#### include_partial 전달

- hit `data_quality_status === 'partial'` 또는 검색 URL `include_partial=true`이면
  `/programs/{id}?include_partial=true`

#### 공유 util

- `policyDetailNavigation.ts`: `buildProgramDetailRoutePath`, `shouldPassIncludePartialOnDetail`
- `PolicyCard`도 동일 util 사용 (Discovery 목록과 경로 규칙 일치)

### FE4-20 — Home → `/search` IA

#### HomePage hero 검색

- submit/Enter → `buildPolicySearchEntryPath(q)` → `navigate('/search?q=…')`
- 빈 q submit 시 이동하지 않음 (Policy Search 422 계약)

#### 추천 검색어 칩

- `HOME_RECOMMENDED_SEARCHES`: 천안시 24세 청년 지원금, 청년도약계좌, 서울 주거, 전국 청년
- 칩 클릭 → 동일 `/search?q=` 진입

#### Route 경계

- `/search?q=` — NL Policy Search (FE4-14~)
- `/programs?search=` — 목록 exact filter + client keyword (`SearchPage`, Forest 범위 밖 유지)
- `/search` route는 `App.tsx`에 등록 (계획서 `routes/index.tsx` 대응)

### FE4-19 — Reason & Uninterpreted UX (우측 사이드바)

#### 레이아웃

- `PolicySearchPage`: Desktop 2열 (`primary` + `340px` sticky sidebar)
- `app-shell__main` max-width 1440px on `/search`
- `@1100px` 이하: sidebar가 primary 아래로 stack

#### SearchReasonBlock

- `interpreted_conditions.conditions[]` + 선택 정책 verdict checklist
- 선택 정책 `message` / `reason_codes` fallback (`resolvePolicySearchReasonMessage`)
- 카드 클릭 선택 → sidebar verdict 갱신

#### UninterpretedNotice

- `uninterpreted_terms` amber box (preview `.uninterpreted` 스타일)
- `※ '토큰'은 조건 Chip으로 파싱되지 않아 키워드 매칭만 적용됩니다.`

#### UnconfirmedBanner

- query-level `ambiguous` / `unmapped` resolution 경고

#### Utils

- `policySearchReasonHelpers.ts`: analysis rows, reason fallback, uninterpreted copy

### FE4-18 — Partial / Unknown badges

(PartialBadge, UnknownVerdictBadge, UnconfirmedConditionsBadge on cards)

## 주요 변경 파일

| 파일 | 변경 |
| --- | --- |
| `frontend/src/components/policySearch/PolicySearchSidebar.tsx` | FE4-19 layout shell |
| `frontend/src/components/policySearch/SearchReasonBlock.tsx` | FE4-19 |
| `frontend/src/components/policySearch/UninterpretedNotice.tsx` | FE4-19 |
| `frontend/src/components/policySearch/UnconfirmedBanner.tsx` | FE4-19 |
| `frontend/src/utils/policySearchReasonHelpers.ts` | FE4-19 pure helpers |
| `frontend/src/pages/user/PolicySearchPage.tsx` | FE4-19 2-col + selection |
| `frontend/src/components/policySearch/PolicySearchResultCard.tsx` | FE4-19 selectable |
| `frontend/tests/policySearch.reason.test.ts` | FE4-19 tests |
| `frontend/src/pages/user/HomePage.tsx` | FE4-20 hero + chips |
| `frontend/src/utils/policySearchNavigation.ts` | FE4-20 entry path helper |
| `frontend/tests/policySearch.navigation.test.ts` | FE4-20 tests |
| `frontend/src/utils/policyDetailNavigation.ts` | FE4-21 detail route helper |
| `frontend/src/components/policySearch/PolicySearchResultCard.tsx` | FE4-21 detail Link |
| `frontend/tests/policySearch.detailNavigation.test.ts` | FE4-21 tests |

## 설계 결정

- Home empty search는 `/programs`로 fallback하지 않고 no-op (Search API q 필수)
- Search result 카드 클릭은 상세 이동; sidebar 선택은 hover/focus로 유지
- partial 상세 404 방지: hit partial 또는 search include_partial opt-in 시 query 전달
- Reason panel은 카드 하단이 아닌 우측 sticky sidebar에 배치 (search_ux_preview 정렬)
  query-level ambiguous/unmapped + 선택 row `message` 중심
- unknown verdict copy는 「미확인」; 전국·무제한 추정 문구 금지

## 검증 결과

```text
python3 scripts/validate_docs.py  — passed
cd frontend && npm run build      — passed
cd frontend && npm run lint       — passed
cd frontend && npm test           — passed (43/43)
```

위 검증 결과와 Browser 미확인 기록은 `2026-08-05` Mock-first 구현 시점의
결과다.

## DT7D actual API 재검증 (`2026-08-06`)

- FE4-22 actual API Client가 `VITE_USE_MOCK=false`와
  `VITE_API_BASE_URL=http://127.0.0.1:8000`에서 동작함을 재확인했다.
- 검색·상세 화면에 “검색 결과는 정책 후보이며 실제 자격 충족을 확정하지
  않는다”는 공통 안내를 추가하고 문구 unit test를 고정했다.
- actual E2E에 새 golden exact query를 추가해 첫 결과
  `청년단기숙소 지원사업`, 조건 근거, 상세 출처·KST 수집 시각·상시·접수 중,
  원문 링크와 자격 비확정 안내를 검증했다.
- 인앱 Browser desktop과 390×844 viewport에서 같은 검색·상세 흐름을 수동
  확인했다.
- Mock E2E 최초 실행은 fixture의 미해석 term이 실제 API와 달라 1건 실패했고,
  실행 모드별 기대값으로 교정한 뒤 통과했다. actual E2E 최초 실행은 detail
  URL의 승인된 `include_partial=true` 전달을 누락해 1건 실패했고 기대 계약을
  바로잡은 뒤 통과했다.

## 남은 작업

- Frontend Forest 구현 Slice는 완료했다. QA·사용성 리뷰·보고서 독립 검증은
  Integration 04 IA3E~IA3F에서 수행한다.
