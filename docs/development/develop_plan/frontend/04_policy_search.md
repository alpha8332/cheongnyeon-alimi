# Frontend Policy Search Forest 개발 계획

## 계획 정보

- 번호: Frontend 04
- 상태: draft
- 담당 영역: Frontend
- Forest: Policy Search (자연어·조건 검색 UI)
- 권장 브랜치: `feature/frontend/policy-search`
- 공통 시작 커밋: 인수인계 문서
  [`week_03_search_contract_handoff.md`](../../weekly_plan/week_03_search_contract_handoff.md)를
  마지막으로 변경한 커밋 (`d3fde3e0912a1a54a27f32d157941be58ecc8660`)
- Gate: DT2·Gate G1 (Backend 06·Frontend 04·Data 권고안 공동 검토)
- 현재 Slice: W3-F0 (G1 통합안 타입·계획 동기화) — **본 구현 금지**
- 선행 Forest: Frontend 01 Policy Discovery (completed),
  Integration 03 Policy Search Data Foundation (completed)
- 후속 Forest: Integration 04 Release 1 Acceptance (Team Leader)
- 대응 개발 기록 (G1 승인·`in-progress` 전환 시 생성):
  `docs/development/development_notes/frontend/policy_search.md`

## 목적

Backend 06 **Gate G1 통합안**에 맞춰 자연어 `q`와 flat query parameter 검색 API를
Frontend가 오해 없이 소비하도록, Gate G1 전에 TypeScript request·response
**pure type 초안**, URL state 분리 원칙, Mock·UI Slice 계획, Browser 검증
**계획**을 고정한다.

Frontend는 자연어 parser를 만들지 않는다. 지역·연령·신청 상태는 Backend
`MatchVerdict`(`match|mismatch|unknown`)와 `DimensionVerdicts`를 그대로
표시하고, unknown을 전국·무제한으로 추정하지 않는다.

## 범위

### W3-F0 (현재 — 계획·pure type 초안만)

- Gate G1 통합 Backend 계약과 동기화된 `frontend/src/types/draft/*`
- URL에 Backend 응답 JSON(interpreted blob) **저장 금지** 명세
- Mock 데이터셋 시나리오 표 (구현 금지)
- Display·Error UX **문서** (실행 helper 금지)
- Browser·반응형·접근성 **검증 계획** (실행은 G1 이후)

### G1 승인 후 본 구현 (별도 Slice)

- SearchBar·URL Sync·Filter Chip·Partial/Unknown 배지·Reason/Uninterpreted UX
- MSW Mock·검색 API Client·`/search` route
- Browser·a11y 검증 실행 및 개발 기록

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
| `q` | string | yes | — | trim 후 비어 있으면 422 |
| `keyword` | string \| null | no | null | 미파싱 키워드 텍스트 매칭 |
| `region` | string \| null | no | null | canonical region name |
| `age` | integer \| null | no | null | 0–150 |
| `category` | enum \| null | no | null | PolicyCategory |
| `status` | enum \| null | no | null | ApplicationStatus |
| `include_partial` | boolean | no | **true** | partial 후보 포함 |
| `page` | integer | no | 1 | ≥ 1 |
| `limit` | integer | no | **20** | 1–100 |

TypeScript: `PolicySearchQueryParams`, `POLICY_SEARCH_DEFAULTS`
(`frontend/src/types/draft/policySearch.contract.ts`).

### Response

Pagination envelope는 `PolicyListResponse`와 동일 (`total`, `page`, `limit`,
`items`).

각 `items[]` 요소는 **중첩(Nested) DTO**: `policy`(PolicyRead/`PolicyDto`) +
검색 확장 필드:

| Field | Type | Notes |
| --- | --- | --- |
| `policy` | PolicyRead | 목록·상세와 동일 공개 필드 envelope |
| `score` | number | 관련도 점수 (Backend 결정적 tie-breaker) |
| `verdicts` | `DimensionVerdicts` | `region`, `age`, `status` 각 `MatchVerdict` |
| `reason_codes` | `ReasonCode[]` | Backend reason enum 코드 |
| `message` | string | 사람이 읽을 수 있는 추천 요약 |
| `unconfirmed_conditions` | string[] | 해당 행에서 미확인 dimension 목록 |

TypeScript: `PolicySearchHit`, `PolicySearchResponse`, `MatchVerdict`,
`DimensionVerdicts`, `ReasonCode`.

### 기존 목록 API와 경계

| 구분 | 경로 | 역할 |
| --- | --- | --- |
| 목록·exact filter | `GET /api/v1/policies` | pagination, exact filter, `include_partial` default **false** |
| 상세 | `GET /api/v1/policies/{id}` | numeric DB id |
| 자연어 검색 | `GET /api/v1/policies/search` | flat `q` + filters, ranked hits |

- `/programs`: exact filter + client-side keyword — 검색 API **대체 아님**
- `/search` (계획): NL 검색 전용; G1 승인 후 route 추가

## URL State 분리 원칙 (G1 고정)

### URL에 저장하는 것

`q`, `keyword`, `region`, `age`, `category`, `status`, `include_partial`,
`page`, `limit` — 사용자 입력과 **명시적 flat filter**만.

TypeScript: `PolicySearchUrlQueryState` (`policySearchUrlState.ts`).

### URL에 저장하지 않는 것

- Backend 응답 `verdicts`, `reason_codes`, `message`, `unconfirmed_conditions`
- NL 해석 결과 전체 JSON blob (`interpreted` query param **사용 금지**)
- per-item 판정·score

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

## Slice 계획

W3-F0 Slice는 문서·pure type만. FE4-06 이후는 `G1_APPROVED` 후 착수.

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
| **세부 작업** | `PolicySearchQueryParams`, `PolicySearchHit` (nested `policy`), `PolicySearchResponse`, `MatchVerdict`, `DimensionVerdicts`, `ReasonCode`, `PolicySearchUrlQueryState`; 실행 함수 **없음** |
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
| M6 | keyword=지원금 only | text match | partial | uninterpreted notice |

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

**Error UX (G1 후 mapHttpStatus 구현)**

| HTTP/상황 | kind | retry | filter chips 유지 |
| --- | --- | --- | --- |
| loading | — | — | — |
| empty q (422) | validation | no | no |
| 200 total=0 | empty_results | no | yes |
| 422 | validation | no | yes |
| 404 | not_found | no | no |
| 5xx/network | server/network | yes | yes |

---

### FE4-04 — Browser·접근성 검증 계획 (W3-F0)

| 항목 | 내용 |
| --- | --- |
| **목표** | G1 이후 실행할 checklist (≥15 cases) |
| **세부 작업** | viewport 390/1440; keyboard SearchBar·Chip remove·pagination; screen reader verdict/partial labels; **W3-F0 실행 기록 금지** |
| **완료 기준** | FE4-10에서 복사 가능 |

---

### FE4-05 — SearchBar & URL Sync (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | `/search` route, controlled `q`, flat param URL round-trip |
| **변경 파일** | `PolicySearchPage.tsx`, `SearchBar.tsx`, `utils/policySearchUrl.ts` (신규) |
| **세부 작업** | parse/build URLSearchParams; **interpreted JSON URL 금지**; submit → URL update → fetch |
| **검증** | Browser URL share reload |
| **완료 기준** | q·filters URL 복원; NL parser 없음 |

---

### FE4-06 — Filter Chip (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | flat filter chips `[지역: 천안시 ✕]` 렌더·제거·재검색 |
| **변경 파일** | `InterpretedConditionChips.tsx` |
| **세부 작업** | Chip = URL param mirror; ✕ removes param and re-queries; verdict styling from response `verdicts` in memory |
| **검증** | Browser: remove region → re-fetch |
| **완료 기준** | Chip state ≠ URL JSON blob |

---

### FE4-07 — Partial/Unknown 배지 (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | `data_quality_status: partial` vs `MatchVerdict: unknown` 시각 분리 |
| **변경 파일** | `PolicySearchResultCard.tsx`, reuse `PartialBadge` |
| **세부 작업** | 복지로 표본: `[자격요건 직접 확인 필요]` + `unconfirmed_conditions` tooltip |
| **검증** | Browser M4 |
| **완료 기준** | unknown ≠ 전국 copy |

---

### FE4-08 — Reason & Uninterpreted UX (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | `reason_codes`·`message`·미파싱 keyword notice |
| **변경 파일** | `SearchReasonBlock.tsx`, `UninterpretedNotice.tsx` |
| **세부 작업** | 카드 하단 Reason; amber box for unparsed keywords (`keyword` param / Backend hint) |
| **검증** | Browser M1–M4 |
| **완료 기준** | "왜 추천됐는가" per row |

---

### FE4-09 — Query State & API Client & MSW (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | `getPolicySearch()`, React Query hook, MSW M1–M6 |
| **변경 파일** | `api/policySearch.ts`, `mocks/policySearchHandlers.ts`, promote `types/policySearch.ts` |
| **세부 작업** | flat query serialization; `include_partial` default true; error mapper from FE4-03 표 |
| **검증** | Mock offline + staging smoke |
| **완료 기준** | `VITE_USE_POLICY_SEARCH_MOCK` gate |

---

### FE4-10 — Browser·a11y·반응형 검증 실행 (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | FE4-04 checklist 실행·개발 기록 |
| **변경 파일** | `development_notes/frontend/policy_search.md` |
| **완료 기준** | Forest 완료 evidence |

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

- FE4-04 checklist 전항목
- Mock M1–M6 + Backend staging parity
- `/programs` list API 회귀 없음

## Forest 완료 기준

- Gate G1 승인 및 `G1_APPROVED` 기록
- 승인 타입이 production·Client·UI에 반영
- `/search` UX가 Data 표본 시나리오 통과
- Browser·a11y 검증 개발 기록
- `docs/index.md` `R1-SEARCH-DATA-SEMANTICS` 후속 반영

## 위험과 미확정 사항

| ID | 항목 | 영향 | 재개 조건 |
| --- | --- | --- | --- |
| G1-REASON | `reason_codes` enum 목록 | copy mapping | Backend W3-B0 |
| G1-UNK | unknown 포함·감점 | 복지로 10건 | Data 권고 + G1 |
| G1-ROUTE | `/search` vs `/programs` IA | navigation | Team Leader |
| FF-REBASE | Backend merge 후 rebase | branch | handoff § rebase |

## 관련 문서

- [Gate G1 인수인계](../../weekly_plan/week_03_search_contract_handoff.md)
- [Data 02 개발 기록](../../development_notes/data/release_dataset_bootstrap.md)
- [Integration 03 Policy Search Data Foundation](../integration/03_policy_search_data_foundation.md)
- [Policy API (목록·상세)](../../../api/policies.md)
- [Policy Discovery (Frontend 01)](01_policy_discovery.md)
- W3-F0 draft types: `frontend/src/types/draft/`

## Gate G1 Frontend 체크리스트 (Team Leader용)

| # | Frontend 초안 | Backend W3-B0 | Data 권고 |
| --- | --- | --- | --- |
| 1 | `PolicySearchQueryParams.q` | required trim | NL 경계 |
| 2 | flat `keyword`·`region`·`age`·`category`·`status` | same names/types | |
| 3 | `MatchVerdict` | evaluation enum | match/mismatch/unknown |
| 4 | `DimensionVerdicts` | region·age·status | |
| 5 | `PolicySearchHit.unconfirmed_conditions` | per-row unknowns | no national guess |
| 6 | `reason_codes`·`message` | reason DTO | |
| 7 | `include_partial` default **true** | same default | 복지로 10건 |
| 8 | 422/404/500 UX (문서) | error contract | |
| 9 | URL flat params only | — | no response JSON in URL |
| 10 | Mock M1–M6 | contract tests | actual profile |

## 기존 Frontend 구조 분석

| 경로 | 현재 역할 | Frontend 04 관계 |
| --- | --- | --- |
| `frontend/src/types/policy.ts` | `PolicyDto` = PolicyRead | `PolicySearchHit.policy` embed |
| `frontend/src/api/policies.ts` | list/detail | 유지; search 별도 |
| `frontend/src/pages/user/SearchPage.tsx` | `/programs` local filter | 검색 API 미사용 |
| `frontend/src/types/draft/*` | G1 pure types | production import 금지 |
