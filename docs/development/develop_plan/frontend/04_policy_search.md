# Frontend Policy Search Forest 개발 계획

## 계획 정보

- 번호: Frontend 04
- 상태: approved
- 승인: Gate G1 (`2026-08-04`)
- 담당 영역: Frontend
- Forest: Policy Search (자연어·조건 검색 UI)
- 권장 브랜치: `feature/frontend/policy-search`
- 공통 시작 커밋: 인수인계 문서
  [`week_03_search_contract_handoff.md`](../../weekly_plan/week_03_search_contract_handoff.md)를
  마지막으로 변경한 커밋 (`d3fde3e0912a1a54a27f32d157941be58ecc8660`)
- Gate: DT2·Gate G1 (Backend 06·Frontend 04·Data 권고안 공동 검토)
- 현재 Slice: FE4-21 pending (FE4-20 completed)
- 선행 Forest: Frontend 01 Policy Discovery (completed),
  Integration 03 Policy Search Data Foundation (completed)
- 후속 Forest: Integration 04 Release 1 Acceptance (Team Leader)
- 대응 개발 기록:
  `docs/development/development_notes/frontend/policy_search.md`

## 목적

Backend 06 **Gate G1 승인 계약**에 맞춰 자연어 `q`와 flat query parameter 검색
API를 Frontend가 오해 없이 소비하도록, 승인된 TypeScript request·response
**pure type 기준선**, URL state 분리 원칙, Mock·UI Slice 계획과 Browser 검증
계획을 구현한다.

Frontend는 자연어 parser를 만들지 않는다. 지역·연령·카테고리·신청 상태는 Backend
`MatchVerdict`(`match|mismatch|unknown|null`)와 `DimensionVerdicts`를 그대로
표시하고, `null`(미적용)과 `unknown`(근거 없음)을 전국·무제한으로 추정하지 않는다.

## 범위

### W3-F0 (completed `2026-08-04` — 계획·pure type 승인 기준선)

- Gate G1 승인 계약과 동기화된 `frontend/src/types/policySearch.ts` 등 production types
- URL에 Backend 응답 JSON(interpreted blob) **저장 금지** 명세
- Mock 데이터셋 시나리오 표 (구현 금지)
- Display·Error UX **문서** (실행 helper 금지)
- Browser·반응형·접근성 **검증 계획** (실행은 G1 이후)

### G1 승인 후 본 구현 (FE4-11~FE4-24)

Mock-first 순서: Types promote → MSW fixtures → contract test → UI → real API.

- Types promote, MSW M1–M6, `npm test` Mock 계약 테스트 (W3-F2A)
- SearchBar·URL Sync·Pagination·Filter Chip(remove/edit/add)
- Loading/Empty/Error shell, Partial/Unknown 배지, Reason/Uninterpreted UX
- Home → `/search` IA, 검색 결과 → 상세(`include_partial`) 연결
- 실 API Client (W3-F2), Browser/a11y (W3-I2), 통합 수정 (W3-F3)

## 범위 밖

- Frontend 전용 자연어 parser·토큰화·규칙 엔진
- Backend 06 Repository·Service·API·테스트 구현
- Data DT3 수집·bootstrap·Schema·Fixture·Seed 변경
- MSW·API Client·프로덕션 UI component **G1 승인 전** 구현
- URL query string에 Backend 응답 JSON 직렬화
- LLM·벡터 검색 UI
- 즐겨찾기·알림·캘린더·관리자 CollectionRun UI

## 선행 조건

- [Gate G1 인수인계](../../weekly_plan/week_03_search_contract_handoff.md) 고정 계약 준수
- Frontend 01: `PolicyDto`(=`PolicyRead`), `/api/v1/policies`, pagination,
  numeric `id`, `include_partial` opt-in 완료
- Integration 03: search projection·`match|mismatch|unknown` primitive 완료
- Data 02 DT2: actual profile·Data 권고안·Schema 영향 판정 완료

## Gate G1 통합 API 계약 (Frontend 소비 기준)

Backend 06 W3-B0와 **필드명·nullable·default 100% 일치**를 목표로 한다.

### Endpoint

```http
GET /api/v1/policies/search
```

### Request — flat query parameters

| Parameter | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `q` | string | yes | — | trim 후 비어 있으면 422; **권장 최대 200자** |
| `keyword` | string \| null | no | null | 미파싱 키워드 텍스트 매칭; **권장 최대 100자** |
| `region` | string \| null | no | null | 행정구역 **alias 또는 canonical name**; **권장 최대 100자** |
| `age` | integer \| null | no | null | 0–150 |
| `category` | enum \| null | no | null | PolicyCategory |
| `status` | enum \| null | no | null | ApplicationStatus |
| `include_partial` | boolean | no | **true** | partial 후보 포함 |
| `page` | integer | no | 1 | ≥ 1 |
| `limit` | integer | no | **20** | 1–100 |

**명시적 flat filter 우선:** `keyword`·`region`·`age`·`category`·`status`를 URL
또는 요청에 명시하면, Backend가 `q`에서 해석한 **동일 dimension**을 override한다.
응답 `interpreted_conditions.override_fields`에 override된 dimension이 기록된다.

TypeScript: `PolicySearchQueryParams`, `POLICY_SEARCH_DEFAULTS`,
`POLICY_SEARCH_QUERY_LIMITS` (`frontend/src/types/policySearch.ts`).

### Response

Pagination envelope는 `PolicyListResponse`와 동일 (`total`, `page`, `limit`,
`items`). 최상위에 NL 해석 블록 `interpreted_conditions`가 포함된다.

**`interpreted_conditions` (response top-level)**

| Field | Type | Notes |
| --- | --- | --- |
| `q_raw` | string | 요청 `q` 원문 |
| `q_clean` | string | Backend 정규화·trim 후 문자열 |
| `conditions` | array | 해석된 조건 목록 (아래) |
| `override_fields` | dimension[] | explicit filter가 `q` 해석을 덮어쓴 dimension |
| `uninterpreted_terms` | string[] | `q`에서 매핑되지 않은 토큰 |

**`conditions[]` 요소**

| Field | Type | Notes |
| --- | --- | --- |
| `dimension` | enum | `keyword` \| `region` \| `age` \| `category` \| `status` |
| `value` | string \| integer | dimension별 추출·명시 값, null 아님 |
| `source` | enum | `q` \| `explicit` |
| `resolution` | enum | `resolved` \| `unmapped` \| `ambiguous` |
| `candidates` | string[] | `ambiguous` 시 후보 (예: region alias) |

각 `items[]` 요소는 **중첩(Nested) DTO**: `policy`(PolicyRead/`PolicyDto`) +
검색 확장 필드:

| Field | Type | Notes |
| --- | --- | --- |
| `policy` | PolicyRead | 목록·상세와 동일 공개 필드 envelope |
| `score` | number | Backend 정렬용; **Release 1 UI 숫자 미표시**, 요청 간 비교 금지 |
| `verdicts` | `DimensionVerdicts` | `region`, `age`, `status`, `category` 각 `MatchVerdict \| null` |
| `unknown_count` | integer | 적용된 verdict 중 `unknown` 개수, Backend tie-breaker |
| `reason_codes` | `ReasonCode[]` | Backend reason code (확장 가능 string) |
| `message` | string | 사람이 읽을 수 있는 추천 요약 |
| `unconfirmed_conditions` | object[] | `{ field, reason_code, message }` per-row 미확인 조건 |

**`DimensionVerdicts` nullable 의미**

| 값 | 의미 |
| --- | --- |
| `null` | 해당 dimension 조건이 이번 검색에 **적용되지 않음** |
| `match` / `mismatch` | 조건 적용 + 정책 근거로 판정 |
| `unknown` | 조건은 적용됐으나 정책 데이터에 근거 **없음** |

TypeScript: `PolicySearchHit`, `PolicySearchResponse`,
`PolicySearchInterpretedConditions`, `InterpretedCondition`, `UnconfirmedCondition`,
`MatchVerdict`, `DimensionVerdicts`, `ReasonCode`.

### 기존 목록 API와 경계

| 구분 | 경로 | 역할 |
| --- | --- | --- |
| 목록·exact filter | `GET /api/v1/policies` | pagination, exact filter, `include_partial` default **false** |
| 상세 | `GET /api/v1/policies/{id}` | numeric DB id |
| 자연어 검색 | `GET /api/v1/policies/search` | flat `q` + filters, ranked hits |

- `/programs`: exact filter + client-side keyword — 검색 API **대체 아님**
- `/search` (계획): NL 검색 전용; G1 승인 후 route 추가

### 정렬(Sort) 정책 (Release 1)

Release 1 정렬은 Backend의 `score DESC` → `unknown_count ASC` → 상태 우선순위
→ `policy.id ASC` 4단계 고정이며 Frontend 별도 sort UI·query parameter는
제공하지 않는다. 결과 순서는 Backend ranked list를 그대로 표시한다.
**`score`와 `unknown_count` 숫자는 Release 1 화면에 노출하지 않으며**, 서로
다른 검색 요청 사이에서 score를 비교·캐시 키로 사용하지 않는다.

`q`, explicit filter 또는 `limit`가 바뀌면 Frontend URL state의 `page`를 1로
재설정한다. 단순 page 이동은 다른 검색 조건을 바꾸지 않는다.

## URL State 분리 원칙 (G1 고정)

### URL에 저장하는 것

`q`, `keyword`, `region`, `age`, `category`, `status`, `include_partial`,
`page`, `limit` — 사용자 입력과 **명시적 flat filter**만.

TypeScript: `PolicySearchUrlQueryState` (`policySearchUrlState.ts`).

### URL에 저장하지 않는 것

- Backend 응답 `interpreted_conditions`, `verdicts`, `reason_codes`, `message`,
  `unconfirmed_conditions`, per-item `score`
- NL 해석 결과 전체 JSON blob (`interpreted` query param **사용 금지**)

Filter Chip UI는 URL flat params + **최신 검색 응답 in-memory state**로
렌더한다. 공유 URL은 입력·필터만 복원하고, Chip verdict 스타일은 재검색 후
Backend 응답으로 갱신한다.

**예시 URL**

```text
/search?q=천안+24세+청년+지원금&region=천안시&age=24&include_partial=true&page=1
/search?q=복지+생활&keyword=지원금&page=1
```

## 공통 설계 원칙

- Frontend는 `q` 원문만 전달; NL parser **금지**
- `MatchVerdict`: `unknown` ≠ 전국, ≠ 제한 없음
- `partial`(`data_quality_status`) ≠ `unknown`(`verdict`)
- `invalid` 비공개; draft types는 production import **금지**
- G1 승인 전 parse/build/map HTTP helper **구현 금지**

## Release 1 주차 Slice 매핑

[3주차 Release 1](../../weekly_plan/week_03_release_1.md) Frontend 단계와
본 Forest Slice 대응 관계다.

| 3주차 | Frontend 04 Slice | 내용 |
| --- | --- | --- |
| W3-F0 | FE4-00~FE4-04 | 계획·pure type·Mock 명세·Browser 계획 |
| W3-F1 | FE4-14~FE4-21 | NL 전달·query state·조건 UI·pagination·홈/상세 연결 (MSW) |
| W3-F2A | FE4-13 | 승인 Mock 계약 `npm test` |
| W3-F2 | FE4-22 | Backend endpoint 실 API Client |
| W3-F3 | FE4-24 | 통합 중 조건·empty·error UI 수정 |
| W3-I2 | FE4-23 | 실제 API Browser·golden query (Integration 04와 연계) |

## Slice 계획

W3-F0 Slice(FE4-00~FE4-04)는 문서·pure type만. **FE4-11 이후는
`G1_APPROVED` 후 Mock-first 순서로 착수**한다.

### G1 후 실행 순서 (Mock-first)

```text
FE4-11 Types promote
  → FE4-12 MSW fixtures
  → FE4-13 Contract tests (W3-F2A)
  → FE4-14 SearchBar + URL (MSW)
  → FE4-15 Loading / Empty / Error shell
  → FE4-16 Pagination
  → FE4-17 Filter Chips (remove + edit/add)
  → FE4-18 Partial / Unknown badges
  → FE4-19 Reason & Uninterpreted UX
  → FE4-20 Home → /search IA
  → FE4-21 Search → Detail link
  → FE4-22 Real API Client (W3-F2)
  → FE4-23 Browser / a11y 실행
  → FE4-24 W3-F3 통합 수정
```

---

### FE4-00 — Forest 계획 등록 (W3-F0)

| 항목 | 내용 |
| --- | --- |
| **목표** | Frontend 04 Forest 계획 확정 및 문서 색인 |
| **변경 파일** | 본 문서, `develop_plan/README.md`, `docs/index.md` |
| **검증** | `python3 scripts/validate_docs.py` |
| **완료 기준** | 문서 검증 통과 |

---

### FE4-01 — Gate G1 타입 초안 (W3-F0)

| 항목 | 내용 |
| --- | --- |
| **목표** | Backend DTO와 100% 정렬된 pure TypeScript types |
| **변경 파일** | `frontend/src/types/draft/policySearch.contract.ts`, `policySearchUrlState.ts`, `policySearchDisplay.ts`, `policySearchErrors.ts`, `draft/README.md` |
| **세부 작업** | `PolicySearchQueryParams`, `PolicySearchInterpretedConditions`, `PolicySearchHit` (nested `policy`, `unknown_count`), `PolicySearchResponse`, nullable `DimensionVerdicts` (+ `category`), `UnconfirmedCondition`, `ReasonCode`, `PolicySearchUrlQueryState`, `POLICY_SEARCH_QUERY_LIMITS`; 실행 함수 **없음** |
| **검증** | `npm run build`; Backend W3-B0 diff |
| **완료 기준** | G1 체크리스트 #1–#7 필드명 일치 |

---

### FE4-02 — Mock 데이터셋 명세 (W3-F0, 문서만)

| 항목 | 내용 |
| --- | --- |
| **목표** | G1 승인 Mock이 반영해야 할 Data DT2 표본 시나리오 |
| **변경 파일** | 본 문서 § Mock 시나리오 |
| **세부 작업** | flat params + response `verdicts`/`reason_codes`/`unconfirmed_conditions` parity; **MSW 구현 금지** |
| **검증** | Data actual profile 대조 리뷰 |
| **완료 기준** | M1–M6 표 리뷰 가능 |

**Mock 시나리오**

| ID | q / params | 기대 verdicts | items | 비고 |
| --- | --- | --- | --- | --- |
| M1 | q=서울 주거, region=서울특별시 | region match | 온통청년 valid | baseline |
| M2 | q=전국 청년 | region unknown | mixed | unknown banner |
| M3 | q=25세 일자리, age=25 | age match | employment | |
| M4 | q=복지로 생활 | multi unknown | partial only | 복지로 10건 |
| M5 | q=(empty trim) | — | 422 | validation |
| M6 | q=지원금&keyword=지원금 | text match | partial | q 필수 계약; keyword explicit |

---

### FE4-03 — Display·Error UX 명세 (W3-F0, 문서만)

| 항목 | 내용 |
| --- | --- |
| **목표** | 배지·Reason·Error copy를 타입 상수와 1:1 고정 |
| **변경 파일** | `policySearchDisplay.ts` (labels only), `policySearchErrors.ts` (types only), 본 문서 § Display·§ Error |
| **세부 작업** | `MATCH_VERDICT_*`, partial/unknown 배지 semantic; HTTP→UI 표 (helper 구현 G1 후) |
| **완료 기준** | partial≠unknown; 복지로 unknown copy review |

**배지 semantic**

| 상태 | 배지 | 의미 |
| --- | --- | --- |
| `partial` (quality) | 정보 일부 누락 | Schema-valid, 필드 일부 null |
| `unknown` (verdict) | 정보 미확인 | dimension 판정 불가 |
| row alert | 자격요건 직접 확인 필요 | 복지로형 multi-unknown |

**Reason-code fallback (G1)**

`ReasonCode`는 확장 가능한 string이다. FE4-19 UI는 알려진 code에만 전용 copy를
매핑하고, **알 수 없는 code**가 와도 throw·blank 하지 않고 Backend가 제공한
`message`(또는 `unconfirmed_conditions[].message`, error body)를 그대로 표시한다.

**Error UX (G1 후 mapHttpStatus 구현)**

| HTTP/상황 | kind | retry | filter chips 유지 | Notes |
| --- | --- | --- | --- | --- |
| loading | — | — | — | — |
| 400 | bad_request | no | yes | 해석 불가; 명시적 region `unmapped`/`ambiguous` |
| empty q (422) | validation | no | no | trim 후 공백 |
| 200 total=0 | empty_results | no | yes | 정상 빈 결과 |
| 422 | validation | no | yes | q 누락·공백, 길이·타입·범위·enum |
| 404 | not_found | no | no | 잘못된 route/version |
| 5xx/network | server/network | yes | yes | 재시도 가능 |

---

### FE4-04 — Browser·접근성 검증 계획 (W3-F0)

| 항목 | 내용 |
| --- | --- |
| **목표** | G1 이후 실행할 checklist (≥15 cases) |
| **세부 작업** | viewport 390/1440; keyboard SearchBar·Chip remove·pagination; screen reader verdict/partial labels; **W3-F0 실행 기록 금지** |
| **완료 기준** | FE4-23에서 복사 가능 |

**Golden Query Empty UX (FE4-15 구현 copy 초안)**

결과 `total=0`일 때 존재하지 않는 정책을 생성·단정하지 않고, 해석된 조건
요약·데이터 범위 제약·조건 수정 안내를 표시한다. golden query
(`천안 사는 27살 청년 월세 지원…`) empty 시나리오는 FE4-23 Browser
checklist에 포함한다.

---

### FE4-11 — Types promote (G1 후) — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | draft types → production `types/policySearch.ts` |
| **변경 파일** | `frontend/src/types/policySearch.ts`, `policySearchErrors.ts`, `policySearchUrlState.ts` (신규); `types/draft/*` 정리 |
| **선행** | `G1_APPROVED` |
| **세부 작업** | nested `PolicySearchHit`, `PolicySearchInterpretedConditions`, nullable `DimensionVerdicts`, `UnconfirmedCondition`, `ReasonCode`, defaults `limit=20` promote |
| **검증** | `npm run build` |
| **완료 기준** | production import 허용; contract·error·URL draft 파일 제거 |

---

### FE4-12 — MSW fixtures (G1 후) — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | FE4-02 Mock spec M1–M6 MSW 구현 |
| **변경 파일** | `frontend/src/mocks/policySearchHandlers.ts`, `policySearchFixtures.ts`, `policySearchRequest.ts`, `fixtures/policySearch/*.json` |
| **선행** | FE4-11 |
| **세부 작업** | nested `PolicySearchHit`; dev/test only; `GET /api/v1/policies/search`; default `limit=20`, `include_partial=true` |
| **검증** | `npm run build`; handler 함수 smoke (MSW worker는 FE4-14) |
| **완료 기준** | M1–M6 handler pass |

---

### FE4-13 — Mock contract tests / W3-F2A (G1 후) — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | 승인 Mock 계약 자동 테스트 (`npm test`) |
| **변경 파일** | `frontend/tests/policySearch.contract.test.ts`, `frontend/tsconfig.test.json`, `frontend/package.json` |
| **선행** | FE4-11, FE4-12 |
| **세부 작업** | request flat param resolve; nested response envelope; M1–M6; TS/JSON drift; defaults `include_partial=true`, `limit=20` |
| **검증** | `npm test` (16 tests: policy list 7 + policy search 9) |
| **완료 기준** | W3-F2A Gate G2 Frontend Mock 준비 충족 |

---

### FE4-14 — SearchBar & URL Sync (G1 후, MSW only) — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | `/search` route, controlled `q`, flat param URL round-trip |
| **변경 파일** | `PolicySearchPage.tsx`, `SearchBar.tsx`, `utils/policySearchUrl.ts`, `App.tsx` routes |
| **선행** | FE4-12, FE4-13 |
| **세부 작업** | parse/build URLSearchParams; **interpreted JSON URL 금지**; React Query + MSW; NL parser 없음 |
| **검증** | Browser URL share reload |
| **완료 기준** | q·filters URL 복원; MSW fetch 동작 |

---

### FE4-15 — Loading / Empty / Error shell (G1 후) — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | 검색 페이지 Loading·Empty·Error 상태 shell |
| **변경 파일** | `PolicySearchPage.tsx`, reuse `LoadingState`/`EmptyState`/`ErrorState`; `utils/policySearchErrors.ts` mapper |
| **선행** | FE4-14 |
| **세부 작업** | loading pending; 422/500 mapper (FE4-03 표); **Golden Query Empty UX** copy; empty_results 시 Chip 유지 |
| **검증** | MSW M5 empty/422; Browser empty scenario |
| **완료 기준** | Gate G3 loading·422·500 shell; golden empty copy 문서화 |

---

### FE4-16 — Pagination (G1 후) — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | 검색 결과 pagination UI 및 URL `page`/`limit` 연동 |
| **변경 파일** | `SearchPagination.tsx`, `PolicySearchPage.tsx`, `policySearchUrl.ts` |
| **선행** | FE4-15 |
| **세부 작업** | `page`/`limit` URL sync; stale response guard; Backend envelope `total`/`page`/`limit` 소비 |
| **검증** | `npm test` pagination cases; Browser page change |
| **완료 기준** | Release 1 pagination 요구 충족; sort UI 없음 (score order 유지) |

---

### FE4-17 — Filter Chips remove + edit/add (G1 후) — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | flat filter chips 표시·제거·수정·추가 후 재검색 |
| **변경 파일** | `InterpretedConditionChips.tsx`, `ConditionEditorDrawer.tsx` (또는 inline edit) |
| **선행** | FE4-16 |
| **세부 작업** | Chip = URL flat param mirror; ✕ remove; edit/add → `region`·`age`·`status`·`category` URL update; verdict styling from in-memory last response |
| **검증** | Browser: remove region; edit age → re-fetch |
| **완료 기준** | handoff “해석 조건 수정” 충족; URL JSON blob 금지 |

---

### FE4-18 — Partial / Unknown badges (G1 후) — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | `partial` quality vs `unknown` verdict 시각 분리 |
| **변경 파일** | `PolicySearchResultCard.tsx`, reuse `PartialBadge` |
| **선행** | FE4-15 |
| **세부 작업** | 복지로 표본: `[자격요건 직접 확인 필요]` + `unconfirmed_conditions` tooltip |
| **검증** | Browser M4 |
| **완료 기준** | unknown ≠ 전국 copy |

---

### FE4-19 — Reason & Uninterpreted UX (G1 후) — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | `reason_codes`·`message`·미파싱 keyword·global unconfirmed banner |
| **변경 파일** | `SearchReasonBlock.tsx`, `UninterpretedNotice.tsx`, `UnconfirmedBanner.tsx` |
| **선행** | FE4-18 |
| **세부 작업** | 우측 사이드바 Reason panel; amber uninterpreted box; query-level 경고는 `interpreted_conditions.conditions[]`, row-level 근거 부족은 `items[].unconfirmed_conditions[]`에서 표시 |
| **검증** | Browser M1–M4 |
| **완료 기준** | “왜 추천됐는가” per row |

---

### FE4-20 — Home → `/search` IA (G1 후) — completed

| 항목 | 내용 |
| --- | --- |
| **목표** | Release 1 golden flow 진입: 홈 검색 → `/search?q=` |
| **변경 파일** | `HomePage.tsx`, `routes/index.tsx` |
| **선행** | FE4-14 |
| **세부 작업** | 홈 hero submit → `/search?q=…`; `/programs?search=` client filter와 승인된 route 경계 문서화 |
| **검증** | Browser: 홈 → 검색 결과 (MSW) |
| **완료 기준** | `release_roadmap` “홈 검색→검색 결과” 1단계 |

---

### FE4-21 — Search → Detail link (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | 검색 hit → `ProgramDetailPage` 이동 및 `include_partial` 전달 |
| **변경 파일** | `PolicySearchResultCard.tsx`, link builder util |
| **선행** | FE4-18 |
| **세부 작업** | `hit.policy.id`; partial → `/programs/{id}?include_partial=true`; detail 404 UX; 출처·신청 기간·자격 확인 |
| **검증** | Browser: result → detail; partial 404 방지 |
| **완료 기준** | golden query “결과→상세” 단계 |

---

### FE4-22 — Real API Client / W3-F2 (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | `getPolicySearch()`, env gate, staging 연결 |
| **변경 파일** | `api/policySearch.ts`, `hooks/usePolicySearchQuery.ts`, env |
| **선행** | FE4-13, FE4-21 (UI MSW complete) |
| **세부 작업** | `VITE_USE_POLICY_SEARCH_MOCK=false`; flat query; error mapper |
| **검증** | staging smoke; 422/500 cases |
| **완료 기준** | W3-F2 Frontend 실 API 연결 |

---

### FE4-23 — Browser / a11y / 반응형 검증 실행 (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | FE4-04 checklist 실행·개발 기록·golden query |
| **변경 파일** | `development_notes/frontend/policy_search.md` |
| **선행** | FE4-22 |
| **세부 작업** | ≥15 cases; golden query manual; W3-I2 cross-ref (Integration 04) |
| **검증** | manual Browser; optional Playwright |
| **완료 기준** | Forest Browser evidence |

---

### FE4-24 — W3-F3 통합 수정 및 회귀 (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | Phase 3 통합 중 발견 bugfix: 조건 전달·empty·error·pagination 회귀 |
| **변경 파일** | 검색 UI·Client 관련 파일 (범위 내) |
| **선행** | FE4-22, Integration E2E feedback |
| **세부 작업** | QA smoke 재현 수정; `/programs` list API 회귀 없음 확인 |
| **검증** | `npm test`, `npm run build`, Browser 재검 |
| **완료 기준** | W3-F3 Gate G3 Frontend 항목 |

---

## 검증 계획

### W3-F0

```powershell
python3 scripts/validate_docs.py
cd frontend
npm run build
npm run lint
git diff --check
```

- Browser·MSW·UI: **미실행·미구현**

### G1 이후 Forest 완료

- FE4-13 `npm test` Mock contract (W3-F2A)
- FE4-04 checklist → FE4-23 실행
- Mock M1–M6 + Backend staging parity (FE4-22)
- 홈 → `/search` → 상세 golden flow (FE4-20, FE4-21)
- `/programs` list·detail API 회귀 없음 (FE4-24)

## Forest 완료 기준

- Gate G1 승인 및 `G1_APPROVED` 기록
- FE4-11~FE4-24 완료; 승인 타입·UI·Client 반영
- `/search` UX가 Data 표본·golden query 시나리오 통과
- `npm test` 검색 contract + Browser·a11y 개발 기록 (FE4-23)
- `docs/index.md` `R1-SEARCH-IMPLEMENTATION` 후속 반영

## 위험과 미확정 사항

DT2B에서 다음과 같이 분류했다.

| ID | DT2B 상태 | 승인 계약·후속 검증 |
| --- | --- | --- |
| G1-REASON | resolved | 알려진 code 전용 copy, 알 수 없는 code는 Backend message fallback; FE4-19 검증 |
| G1-UNK | resolved | unknown 후보 포함·감점과 미확인 표시; FE4-18·FE4-19 검증 |
| G1-ROUTE | resolved | `/search` 자연어 UX와 `/programs` 기존 목록을 병행; FE4-20 검증 |
| FF-REBASE | resolved | Frontend HEAD가 Data 브랜치에 병합됨 |
| category 다중 선택 | non-blocking | v0.1.0은 단일 category만 제공 |
| 지역 ambiguous 후보 표시 | implementation-risk | candidates를 임의 선택하지 않고 FE4-17·FE4-19에서 수정·경고 UX 검증 |

## 관련 문서

- [Gate G1 인수인계](../../weekly_plan/week_03_search_contract_handoff.md)
- [Data 02 개발 기록](../../development_notes/data/release_dataset_bootstrap.md)
- [Integration 03 Policy Search Data Foundation](../integration/03_policy_search_data_foundation.md)
- [Policy API (목록·상세)](../../../api/policies.md)
- [Policy Discovery (Frontend 01)](01_policy_discovery.md)
- Production types: `frontend/src/types/policySearch.ts`, `policySearchErrors.ts`, `policySearchUrlState.ts`
- Display label draft: `frontend/src/types/draft/policySearchDisplay.ts`

## Gate G1 Frontend 체크리스트 (Team Leader용)

| # | Frontend 초안 | Backend W3-B0 | Data 권고 |
| --- | --- | --- | --- |
| 1 | `PolicySearchQueryParams.q` required trim; limits q200/kw100/reg100 | same | NL 경계 |
| 2 | flat `keyword`·`region`·`age`·`category`·`status`; explicit override | same names/types | |
| 3 | `MatchVerdict` | evaluation enum | match/mismatch/unknown |
| 4 | `DimensionVerdicts` nullable; `region`·`age`·`status`·`category` | same | null vs unknown |
| 5 | `PolicySearchResponse.interpreted_conditions` | NL interpretation block | |
| 6 | `PolicySearchHit.unconfirmed_conditions` `{ field, reason_code, message }` | per-row unknowns | no national guess |
| 7 | `reason_codes`·`message`; ReasonCode extensible + message fallback | reason DTO | |
| 8 | `include_partial` default **true**; `limit` default **20** | same default | 복지로 10건 |
| 9 | 400/422/404/500 UX (문서) | error contract | |
| 10 | URL flat params only; no response JSON | — | no interpreted blob in URL |
| 11 | Mock M1–M6 (M6: q+keyword) | contract tests | actual profile |
| 12 | `score` ordering only; no UI numeric display | Backend rank | |
| 13 | `PolicySearchHit.unknown_count` integer | same response field | Backend tie-breaker, UI 숫자 미표시 |

## 기존 Frontend 구조 분석

| 경로 | 현재 역할 | Frontend 04 관계 |
| --- | --- | --- |
| `frontend/src/types/policy.ts` | `PolicyDto` = PolicyRead | `PolicySearchHit.policy` embed |
| `frontend/src/api/policies.ts` | list/detail | 유지; search 별도 |
| `frontend/src/pages/user/HomePage.tsx` | `/programs?search=` client filter | FE4-20 → `/search?q=` |
| `frontend/src/pages/user/SearchPage.tsx` | `/programs` exact+local filter | 검색 API 미사용; `/search`와 병행 |
| `frontend/src/types/policySearch.ts` | G1 search contract | FE4-14 UI·FE4-22 API import |
| `frontend/src/mocks/policySearchHandlers.ts` | M1–M6 mock handler | FE4-13 contract test |
| `frontend/src/types/policySearchErrors.ts` | Error presentation types | FE4-19 mapper |
| `frontend/src/types/policySearchUrlState.ts` | URL state types | FE4-14 parse/build |
| `frontend/src/types/draft/policySearchDisplay.ts` | Display labels (draft) | FE4-18 promote 예정 |
