# Frontend Real API 수동 테스트 가이드 (localhost:8000)

## 문서 정보

- 작성일: 2026-08-12
- 담당 영역: Frontend
- 목적: `VITE_USE_MOCK=false` + Backend(`http://127.0.0.1:8000`) 환경에서
  Playwright Real API golden skip 시나리오를 **브라우저 수동 검증**으로
  대체하기 위한 절차
- 관련 E2E: Forest별 `test.skip(VITE_USE_MOCK !== 'false')` 7건 + week4 1건
- 상태: 검증 절차 문서 (자동 E2E pass를 대체하지 않음)

## 선행 조건

### 1. Backend·DB

- Backend API가 `http://127.0.0.1:8000`에서 응답한다.
- PostgreSQL에 Release 데이터(또는 팀 합의 Seed)가 적재되어 있다.
- 아래 API path가 404가 **아니어야** Real API golden을 수동으로 pass할 수 있다.

| 영역 | HTTP | Path | 비고 |
| --- | --- | --- | --- |
| Policy 목록·상세 | GET | `/api/v1/policies`, `/api/v1/policies/{id}` | Release 1·User Features |
| Policy 검색 | GET | `/api/v1/policies/search` | golden query |
| 추천 | POST | `/api/v1/recommendations` | W4-G0 proposal — Backend merge 여부 확인 |
| Policy 상세 + summary | GET | `/api/v1/policies/{id}` (`eligibility_summary` nested) | Backend Integration 08 merge 여부 |
| Admin session | POST | `/api/v1/admin/session` | PIN login |
| CollectionRun | GET/POST | `/api/v1/admin/collection-runs` | 목록·상세·수동 실행 |
| Admin policy data | GET | `/api/v1/admin/policies` | Integration 09 AO1 |
| Admin log files·events | GET/POST/DELETE | `/api/v1/admin/log-files` … | Integration 09 AO2~AO3 |

Integration 09·08 Backend path가 아직 merge되지 않았다면 해당 시나리오는
**BLOCKED**로 기록하고 Mock skip 상태를 유지한다
([Integration Fix and Regression 개발 기록](development_notes/frontend/integration_and_regression.md)).

### 2. Frontend 실행

```powershell
cd frontend
$env:VITE_USE_MOCK = 'false'
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run dev
```

브라우저: `http://127.0.0.1:3000` (`frontend/README.md` dev origin).

### 3. 관리자 PIN

- 로컬 development·localhost: **최초 PIN `0000`** (4자리, 아이디 없음).
- 연속 실패 시 **429 cooldown** — PIN 입력·로그인 버튼 비활성 + Toast/inline 안내.
- 세션 만료(401): Toast + `/admin/login` redirect
  (`useAdminUnauthorizedRedirect`).

### 4. DevTools 권장

- **Network** 탭: `Fetch/XHR` 필터, `api/v1` 요청 status·response body 확인.
- **Application → Local Storage**: `cheongnyeon-alimi.user-local.v1` (북마크·조건).
- Admin session은 **in-memory** — full reload 후 admin deep link는 login redirect될 수
  있음. SPA 내비게이션(로그인 → 링크 클릭)을 권장.

### 5. 라우트 주의 (계획 문서 vs 실제)

| 사용자 표현 | 실제 Frontend route |
| --- | --- |
| `/admin/collection-runs` | **`/admin/runs`** (목록), **`/admin/runs/{runId}`** (상세) |
| 정책 검색 | **`/search`** (`PolicySearchPage`) |
| 정책 목록 | `/programs` (`SearchPage`, FE1 legacy) |

---

## 공통 오류 UX (Real API)

| HTTP | 대표 화면 | Frontend UX |
| --- | --- | --- |
| 401 | Admin API | Toast(세션 만료) + `/admin/login` redirect |
| 409 | 수동 실행·log archive delete | Toast(conflict), dialog 유지 |
| 422 | validation (PIN 형식, filter, refetch) | inline alert 또는 Toast(validation) |
| 429 | Admin login | inline alert + PIN·버튼 disable(cooldown) |
| 503 / 5xx | Policy·Admin·Recommendation | retryable Toast + **다시 시도** / table 유지 |
| 404 | Policy·Run detail | EmptyState / ErrorState |

---

## 시나리오 1 — Policy Search golden (Release 1 / W4-I3)

**대응 E2E:** `policy-search-audit.spec.ts` test 8,
`eligibility-summary-ui.spec.ts` test 10~11,
`week4-regression.spec.ts` Real API skip

### URL

```
http://127.0.0.1:3000/search?q=%EC%B2%9C%EC%95%88+%EC%82%AC%EB%8A%94+27%EC%82%B4+%EC%B2%AD%EB%85%84+%EB%8B%A8%EA%B8%B0%EC%88%99%EC%86%8C+%EC%A7%80%EC%9B%90+%EB%B0%9B%EC%9D%84+%EC%88%98+%EC%9E%88%EB%82%98%3F
```

(검색어: `천안 사는 27살 청년 단기숙소 지원 받을 수 있나?`)

또는 `/search` 접속 후 **정책 검색어** 입력 → **검색하기**.

### 조작

1. 검색 결과 로딩(`검색 결과 로딩 중` aria-label) 종료 대기.
2. **검색 결과** region에서 첫 카드 확인.
3. (선택) 우측 **검색 조건 분석** sidebar 확인.
4. 첫 결과 카드 클릭 → 상세 이동.

### 기대 (Backend·DB 정상)

| 단계 | Network | 화면 |
| --- | --- | --- |
| 검색 | `GET /api/v1/policies/search?q=…` **200** | 결과 카드 ≥1, 첫 카드에 **청년단기숙소 지원사업** |
| | | region `note`: **실제 자격 충족을 확정하지 않습니다** |
| | | sidebar **검색 조건 분석**: 정책명·27세/연령·천안/지역 |
| 상세 | `GET /api/v1/policies/{id}?include_partial=true` **200** | URL `/programs/{id}?include_partial=true` |
| | | **📄 정책 정보**, 데이터 출처 **온통청년 청년정책 API**, 수집 시각 **KST** |
| | | 일정 **상시**, 접수 **접수 중**, non-definitive `note` |
| | | **원문 링크 열기** 버튼 |

### API·데이터 미비 시

- **200 + total=0**: Empty shell — DB snapshot·query contract 불일치.
- **503**: Error shell + **다시 시도** (retryable Toast 가능).
- **422**: validation alert (잘못된 q 등).

---

## 시나리오 2 — Eligibility Summary (자격 요건 요약)

**대응 E2E:** `eligibility-summary.spec.ts`의 Real API 조건부 4건,
`eligibility-summary-ui.spec.ts`의 현재 계약 회귀

### URL

시나리오 1과 동일하게 검색 → 첫 결과 상세, 또는 알려진 policy id:

```
http://127.0.0.1:3000/programs/{id}
```

(`include_partial=true` 필요 시 쿼리 추가)

### 조작

1. 상세 로딩 종료(`정책 상세를 불러오는 중입니다.` 사라짐).
2. **핵심 신청 조건** 카드 영역 확인.
3. coverage 안내와 필수·제외·우대·필요 서류·확인 필요 섹션을 확인.
4. evidence의 **원문 링크 열기**를 눌러 공식 URL 이동을 확인.

### 기대 (summary API merge됨)

| 단계 | Network | 화면 |
| --- | --- | --- |
| 최초 로드 | `GET /api/v1/policies/{id}` **200**, body에 `eligibility_summary` | coverage 안내, requirements·evidence·공식 원문 링크 |
| | | `note`: **최종 신청 가능 여부를 확정하지 않습니다** |
| partial | | 일부 조건은 원문 확인이 필요하다는 안내 |
| unknown | | 구조화할 수 없는 조건과 공식 원문 확인 안내 |

### API·데이터 미비 시

- `coverage=unknown`: 빈 값을 추정하지 않고 원문 확인 안내와 `unknowns`를 표시한다.
- evidence URL이 없으면 임의 링크를 만들지 않는다.
- 개인 조건 비교와 eligibility 전용 새로고침은 현재 승인 계약에 없다.

---

## 시나리오 3 — Recommendation UI (맞춤 추천)

**대응 E2E:** `recommendation-ui.spec.ts` test 13

### URL

```
http://127.0.0.1:3000/recommendations
```

### 조작

1. **맞춤 추천 조건 편집** form:
   - 지역: `천안시`
   - 연령: `27`
   - 관심 분야: `주거` (housing)
2. **추천 받기** 클릭.
3. 결과 카드에서 **지역** 표시 확인 — regions ≥3이면 **더 보기** / **접기** toggle.
4. (선택) 결과 카드 → 상세, 북마크 toggle.

### 기대

| 단계 | Network | 화면 |
| --- | --- | --- |
| submit | `POST /api/v1/recommendations` **200** | **추천 결과** region, `article.recommendation-result-card` ≥1 |
| | | disclaimer: **자격을 확정하지 않으며** |
| long regions | | `서울, … 외 N곳` + **더 보기** → 전체 펼침 → **접기** |
| empty | **200** total=0 | empty shell (Mock: `MOCK_EMPTY` region) |

### API·데이터 미비 시

- **404/503**: ErrorState + **다시 시도** / Toast
- **422**: validation Toast (age·limit 경계)

---

## 시나리오 4 — User Service (북마크·달력·알림)

**대응 E2E:** `user-service-features.spec.ts` test 14 (+ calendar/notifications Mock paths)

### 4-A 북마크 persistence (Real API golden)

**URL:** `http://127.0.0.1:3000/`

1. **주요 정책** 카드 로딩 대기.
2. 첫 카드 **북마크 추가** (☆).
3. sidebar **북마크** → `/favorites`.
4. **F5 새로고침** — 북마크 유지 확인.

**기대:** localStorage `cheongnyeon-alimi.user-local.v1`에 policy id 저장;
`/favorites`에 동일 카드. Policy API `GET /api/v1/policies/{id}` **200**
(북마크 상세 로드).

### 4-B 마감 달력

**URL:** `http://127.0.0.1:3000/calendar`

1. **북마크** tab (기본) — 북마크한 정책 중 `application_end` 있는 항목만 표시.
2. **전체 정책** tab → `GET /api/v1/policies?limit=100&include_partial=true` **200**.

**기대:** KST 기준 날짜 bucket 또는 **표시할 신청 마감일이 있는 정책이 없습니다.**
(closed·종료일 null 정책은 slot 없음 — `policyDeadline` 계약).

### 4-C 알림

**URL:** `http://127.0.0.1:3000/notifications`

1. 북마크 없음 → empty: **북마크한 정책이 없습니다…**
2. 북마크 + D-7 이내 마감 정책 있으면 알림 카드; 없으면 **마감 임박 알림이 없습니다…**

**Network:** 북마크 id마다 `GET /api/v1/policies/{id}` (React Query).

### 4-D ICS 다운로드 (Real data)

상세 페이지 **캘린더 (.ics) 다운로드**:

- **enabled:** `application_end` 있고 `application_status !== 'closed'`
- **disabled:** 종료일 없음 또는 closed — title 안내

---

## 시나리오 5 — Admin CollectionRun (수집 실행)

**대응 E2E:** `admin-collection-run.spec.ts` test 9

> Frontend route: **`/admin/runs`** (API path: `/api/v1/admin/collection-runs`)

### URL

```
http://127.0.0.1:3000/admin/login
```

### 조작

1. **관리자 PIN (4자리)** `0000` → **로그인**.
2. **실행 기록** → `/admin/runs`.
3. 테이블 첫 **run_id** 링크 클릭 → `/admin/runs/{runId}`.
4. (선택) **수동 실행 요청** → dialog **실행** → list refresh.

### 기대

| 단계 | Network | 화면 |
| --- | --- | --- |
| login | `POST /api/v1/admin/session` **200** | `/admin` redirect, Bearer token in-memory |
| list | `GET /api/v1/admin/collection-runs?page=…` **200** | **CollectionRun 실행 기록** table |
| detail | `GET /api/v1/admin/collection-runs/{id}` **200** | **실행 상세**, `run_id` 필드 |
| manual trigger | `POST /api/v1/admin/collection-runs` **202** | **수동 실행을 요청했습니다 (run_id: …)** |
| running 존재 | | **수동 실행 요청** disabled |

### API·데이터 미비 시

- **401**: login redirect
- **409**: 수동 실행 conflict Toast
- list **503**: Toast + retry, table stale 유지 가능

---

## 시나리오 6 — Admin Observability (정책·Log)

**대응 E2E:** `admin-observability-ui.spec.ts` test 13

### 6-A 정책 데이터

**URL:** `http://127.0.0.1:3000/admin/policies` (로그인 후)

1. 테이블 **승인 Policy projection** caption·행 로드.
2. **제목** sort, pagination.
3. **정책 데이터 필터** → `data_quality_status: partial` → **필터 적용**.
4. `{title} 상세보기` → drawer **Policy row 상세** → **닫기**.

**Network:** `GET /api/v1/admin/policies?page=…` **200**,
`GET /api/v1/admin/policies/{id}` **200** (drawer).

### 6-B 구조화 Log

**URL:** `http://127.0.0.1:3000/admin/logs`

1. **Log files** summary + **Log events** table.
2. event row 선택 → detail panel (message, safe error_type, stack trace **없음**).
3. **새로고침** (explicit refresh).
4. **Log maintenance** (`aria-label`):
   - **현재 log rotate** → confirm → success message
   - **archive delete** → file 선택 → typed confirm → delete

**Network:**

- `GET /api/v1/admin/log-files` **200**
- `GET /api/v1/admin/log-events?…` **200**
- `POST /api/v1/admin/log-files/rotate-current` **200**
- `DELETE /api/v1/admin/log-files/{file_id}` **200** (또는 **409** active file)

### API·데이터 미비 시

- Admin policy·log path **404**: Integration 09 미merge — **BLOCKED**
- **401**: Toast + login redirect
- **409** archive: conflict Toast, dialog 유지

---

## 시나리오 7 — Week 4 회귀 (Real API subset)

**대응 E2E:** `week4-regression.spec.ts` Real API skip

Mock-first 5 path(A~Cross)는 `VITE_USE_MOCK=true` E2E로 cover됨.
Real API mode에서는 **최소 smoke**:

1. 시나리오 1 (golden search) pass
2. 시나리오 5 (admin login → runs list) pass
3. 시나리오 2 (detail summary card or empty) pass

전체 W4-I1 cross-flow(수동 실행→policies→logs)는 시나리오 5·6을 연속 수행.

---

## Real API E2E skip ↔ 수동 시나리오 매핑

| E2E spec | Test # | 수동 시나리오 |
| --- | --- | --- |
| `policy-search-audit.spec.ts` | 8 | 시나리오 1 |
| `eligibility-summary-ui.spec.ts` | 13 | 시나리오 2 |
| `recommendation-ui.spec.ts` | 13 | 시나리오 3 |
| `user-service-features.spec.ts` | 14 | 시나리오 4-A |
| `admin-collection-run.spec.ts` | 9 | 시나리오 5 |
| `admin-observability-ui.spec.ts` | 13 | 시나리오 6 |
| `week4-regression.spec.ts` | Real API | 시나리오 7 |

수동 pass 후 Playwright 재실행:

```powershell
cd frontend
$env:VITE_USE_MOCK = 'false'
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run test:e2e -- e2e/policy-search-audit.spec.ts
# … Forest별 spec
```

---

## 수동 검증 기록 템플릿

| 시나리오 | 일시 | Backend commit/branch | pass/fail/blocked | Network 메모 | 스크린샷 |
| --- | --- | --- | --- | --- | --- |
| 1 Search golden | | | | | |
| 2 Eligibility | | | | | |
| 3 Recommendation | | | | | |
| 4 User | | | | | |
| 5 CollectionRun | | | | | |
| 6 Admin observability | | | | | |

결과는 해당 Forest `development_notes/` 또는 W4-G3/G4 evidence board에
링크한다. **수동 pass만으로 E2E skip 해소를 자동 기록하지 않는다.**

---

## 관련 문서

- `frontend/README.md` — Mock/Real 전환
- [Policy API 계약](../api/policies.md)
- [Release 1 검증 증거 안내](../contest/release_1_evidence_guide.md) — golden query
- [Integration Fix and Regression 개발 기록](development_notes/frontend/integration_and_regression.md) — BLOCKER
- Forest별 development notes: [eligibility](development_notes/frontend/eligibility_summary_ui.md),
  [recommendation](development_notes/frontend/recommendation_ui.md),
  [admin observability](development_notes/frontend/admin_observability_ui.md),
  [collection run](development_notes/frontend/collection_run_admin_ui.md),
  [user service](development_notes/frontend/user_service_features.md),
  [policy search](development_notes/frontend/policy_search.md)
