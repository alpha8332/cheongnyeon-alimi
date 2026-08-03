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
- 현재 Slice: W3-F0 (계획·소비 초안) — **본 구현 금지**
- 선행 Forest: Frontend 01 Policy Discovery (completed),
  Integration 03 Policy Search Data Foundation (completed)
- 후속 Forest: Integration 04 Release 1 Acceptance (Team Leader)
- 대응 개발 기록 (G1 승인·`in-progress` 전환 시 생성):
  `docs/development/development_notes/frontend/policy_search.md`

## 목적

Backend 06이 제공할 **자연어 `q` + 구조화 조건** 검색 API를 Frontend가 오해
없이 소비하도록, Gate G1 전에 TypeScript request·response 초안, 해석 조건
표시·수정 흐름, 검색 이유·미확인 조건·partial/unknown 표시 의미, URL query
state, 오류·빈 결과 UX, 승인 Mock·API 전환·Browser 검증 **계획**을
고정한다.

Frontend는 자연어 parser를 만들지 않는다. 지역·연령·신청 상태는 Backend
판정 `match|mismatch|unknown`을 그대로 표시하고, unknown을 전국·무제한으로
추정하지 않는다.

## 범위

### W3-F0 (현재 작업 — 계획·초안만)

- 본 Forest 계획서와 Slice별 atomic 작업 정의
- `frontend/src/types/draft/` W3-F0 TypeScript 소비 초안
- Backend 06 W3-B0 초안과 대조할 항목·G1 미확정 목록
- 기존 `/api/v1/policies` 목록·상세 소비 구조 분석 및 검색 API와의 경계
- Browser·반응형·접근성 **검증 계획** (실행은 G1 이후 Slice)

### G1 승인 후 본 구현 (별도 Slice — 이 문서에만 계획)

- `/search` 자연어 검색 페이지·SearchBar·URL sync
- 해석 조건 Chip·수정 UI
- 결과별 검색 이유·미확인 조건·partial/unknown 배지
- 승인 Mock(MSW) 데이터셋
- 검색 API Client·`VITE_USE_MOCK` 전환
- Browser·a11y·반응형 검증 실행

## 범위 밖

- Frontend 전용 자연어 parser·토큰화·규칙 엔진
- Backend 06 Repository·Service·API·테스트 구현
- Data DT3 수집·bootstrap·Schema·Fixture·Seed 변경
- MSW·API Client·프로덕션 UI component **G1 승인 전** 구현
- LLM·벡터 검색 UI
- 즐겨찾기·알림·캘린더·관리자 CollectionRun UI
- 미승인 endpoint path·query 이름을 production code에 hard-code

## 선행 조건

- [Gate G1 인수인계](../../weekly_plan/week_03_search_contract_handoff.md)의
  고정 계약·브랜치 기준 준수
- Frontend 01: `PolicyDto`, `/api/v1/policies`, pagination, numeric `id`,
  `include_partial` opt-in 구현·검증 완료
- Integration 03: Source 중립 검색 projection·`match|mismatch|unknown`
  primitive 완료
- Data 02 DT2: actual profile·Data 권고안·Schema 영향 판정 (Backend·Frontend
  초안 대기)
- 작업 브랜치 HEAD === 인수인계 문서 기준 커밋 SHA

## 공통 설계 원칙

### 고정 계약 (인수인계 — 임의 변경 금지)

- 검색 요청은 PostgreSQL만 사용; Frontend는 검색 중 외부 Source API를 호출하지
  않는다.
- Frontend는 자연어 원문을 `q`로 전달; **별도 NL parser 금지**.
- Backend가 결정적 한국어 규칙으로 구조화하는 **단일 기준**.
- 지역·연령·신청 상태: `match|mismatch|unknown` 구분; 근거 없으면 전국
  추정 금지.
- `invalid` 정책 비공개; 기존 목록·상세·`include_partial`은 새 검색 API
  승인 전까지 유지.
- `NormalizedProgram` 1.1.0, Fixture, Seed, DB enum, `null`·빈 배열 규칙은
  DT2 Data 권고에서 단독 변경 금지.

### 기존 목록 API와 검색 API 경계

| 구분 | 경로(현행) | 역할 |
| --- | --- | --- |
| 목록·exact filter | `GET /api/v1/policies` | pagination, category·region·status exact, `include_partial` |
| 상세 | `GET /api/v1/policies/{id}` | numeric DB id |
| 자연어 검색 (G1 pending) | `GET /api/v1/policies/search` (초안) | `q`, interpreted conditions, reasons, ranked results |

- `/programs` 화면: 현행 exact filter + **client-side** keyword filter
  (`SearchPage`, `policyFilters.ts`) — 검색 API **대체 아님**.
- `/search` 화면 (계획): NL 검색 전용; G1 승인 후 신규 route.

### 소비 타입 권위

1. Gate G1 승인된 OpenAPI·Backend W3-B0
2. `docs/api/policies.md` (목록·상세)
3. `frontend/src/types/draft/*` (승인 전 초안)

## Slice 계획

각 Slice는 **한 번에 커밋·검증 가능한 atomic 단위**다. W3-F0 Slice는
문서·draft 타입만; FE4-09 이후는 `G1_APPROVED` 후에만 착수한다.

---

### FE4-00 — Forest 계획 등록 (W3-F0)

| 항목 | 내용 |
| --- | --- |
| **목표** | Frontend 04 Forest 계획 확정 및 문서 색인 등록 |
| **변경 파일** | `docs/development/develop_plan/frontend/04_policy_search.md`, `docs/development/develop_plan/README.md`, `docs/index.md` |
| **세부 작업** | PLAN_HEADINGS 필수 섹션 작성; W3-F0/G1 이후 Slice 구분; 인계 보드 `R1-SEARCH-DATA-SEMANTICS` 링크 |
| **검증** | `python3 scripts/validate_docs.py`; 링크·Forest owner area |
| **완료 기준** | 문서 검증 통과; Team Leader가 W3-F0 리뷰 가능 |

---

### FE4-01 — 검색 request·response TypeScript 초안 (W3-F0)

| 항목 | 내용 |
| --- | --- |
| **목표** | Backend 06과 대조할 소비 타입 초안 |
| **변경 파일** | `frontend/src/types/draft/policySearch.contract.ts`, `frontend/src/types/draft/README.md` |
| **세부 작업** | `PolicySearchRequestDraft`, `PolicySearchResponseDraft`, `PolicyMatchVerdict`, `PolicySearchResultItemDraft`, `PolicySearchInterpretedConditionDraft`, `PolicySearchResultReasonDraft`; endpoint placeholder; **production import 금지** |
| **검증** | `npm run build` (draft가 컴pile만 되는지); Backend W3-B0 필드명 diff 표 (본 문서 Gate G1 표) |
| **완료 기준** | G1 검토용 타입 초안 커밋; endpoint·merge 규칙은 `미확정` 명시 |

**G1 미확정 (Backend와 동기화 필요)**

- HTTP method·path 최종값
- `q` 빈 문자열 허용 여부·422 vs 400
- structured 필드와 interpreted merge·override 규칙
- `exclude_confirmed_mismatch` 기본값
- `include_partial` 기본값 및 목록 API와의 UX 일관성
- `score` 노출 여부·정렬 tie-breaker

---

### FE4-02 — Match verdict·해석 조건 Chip 타입 (W3-F0)

| 항목 | 내용 |
| --- | --- |
| **목표** | Backend 해석 결과를 Chip UI로 표현하기 위한 데이터 모델 |
| **변경 파일** | `frontend/src/types/draft/policySearch.contract.ts` (interpreted_conditions), 계획서 § Chip UX |
| **세부 작업** | `dimension`·`label`·`value`·`verdict`·`user_modified`; Chip 편집 후 재요청 payload (structured override) 초안; **Chip React component 구현 금지** |
| **검증** | TypeScript compile; 샘플 JSON (온통청년 regional / 복지로 unknown) walkthrough 문서 |
| **완료 기준** | Chip 상태 머신(표시→편집→재검색)이 문서·타입으로 설명됨 |

**Chip UX 초안 (구현 전 설계)**

```text
[지역: 미확인 ×] [연령: 25세 ×] [상태: 접수 중 ×]  + 조건 추가
```

- `unknown` Chip: 경고 아이콘 + "정보 미확인" (전국 아님)
- `mismatch` Chip: 사용자가 명시적으로 포함하기 전 결과에서 제외 (G1)
- `user_modified=true` Chip: 강조 border

---

### FE4-03 — 검색 이유·미확인 조건 타입 (W3-F0)

| 항목 | 내용 |
| --- | --- |
| **목표** | 결과 행별 `reasons`·global `unconfirmed_dimensions` 소비 의미 고정 |
| **변경 파일** | `frontend/src/types/draft/policySearch.contract.ts`, `frontend/src/types/draft/policySearchDisplay.ts` |
| **세부 작업** | `PolicySearchResultReasonDraft.summary`·`codes`·`unknown_dimensions`; global banner copy; 복지로 10건 partial·unknown 표본 UX 시나리오 3종 문서화 |
| **검증** | Data 02 actual profile 표와 reason copy 대조 리뷰 체크리스트 |
| **완료 기준** | "왜 이 정책이 보이는가"·"무엇이 미확인인가" UI copy가 타입과 1:1 |

**표본 시나리오 (Data 02 DT2)**

1. 온통청년 valid + regional match → reason "지역 일치"
2. 복지로 partial + region unknown → partial 배지 + "지역 정보 미확인"
3. confirmed mismatch 제외 후 empty → `EMPTY_RESULTS` + Chip 유지

---

### FE4-04 — partial·unknown 표시 의미 (W3-F0)

| 항목 | 내용 |
| --- | --- |
| **목표** | `data_quality_status: partial`과 verdict `unknown` 혼동 방지 |
| **변경 파일** | `frontend/src/types/draft/policySearchDisplay.ts`, Frontend 01 `PartialBadge` **동작 참조만** (수정 G1 후) |
| **세부 작업** | `PARTIAL_QUALITY_BADGE_*`, `POLICY_MATCH_VERDICT_*`; variant 토큰; 목록·상세·검색 결과 동일 semantic |
| **검증** | Fixture/Seed 4건 + Data actual partial 10건 copy review |
| **완료 기준** | partial≠unknown 문구; 오해 방지 helper text |

| 상태 | 배지 | 의미 |
| --- | --- | --- |
| `partial` (quality) | 정보 일부 누락 | Schema-valid이나 검색 필드 일부 null |
| `unknown` (verdict) | 정보 미확인 | 해당 dimension 판정 불가 |
| `mismatch` | 조건 불일치 | 요청과 confirmed data 불일치 |

---

### FE4-05 — URL query state 모듈 초안 (W3-F0)

| 항목 | 내용 |
| --- | --- |
| **목표** | `/search?q=...&page=...` round-trip without NL parser |
| **변경 파일** | `frontend/src/types/draft/policySearchUrlState.ts` |
| **세부 작업** | `parsePolicySearchUrlState`, `buildPolicySearchSearchParams`, `toPolicySearchRequestDraft`, interpreted JSON serialize/deserialize; route constant `POLICY_SEARCH_ROUTE='/search'` |
| **검증** | unit test 계획만 기록 (G1 후 `policySearchUrlState.test.ts`); round-trip 예시 URL 5개 in plan |
| **완료 기준** | 공유 가능한 URL로 검색 상태 복원 가능 (설계 수준) |

**예시 URL (초안)**

```text
/search?q=서울+25세+주거+지원&page=1&include_partial=true
/search?q=복지+생활&region=서울특별시&age=30&exclude_confirmed_mismatch=false
```

---

### FE4-06 — Loading·Empty·Error·404·422·500 UX 매핑 (W3-F0)

| 항목 | 내용 |
| --- | --- |
| **목표** | 검색 API 오류를 Frontend 01 `LoadingState`/`EmptyState`/`ErrorState` 패턴에 매핑 |
| **변경 파일** | `frontend/src/types/draft/policySearchErrors.ts`, 계획서 § 오류 표 |
| **세부 작업** | `mapHttpStatusToSearchErrorDraft`, empty query/results; `preserve_interpreted_conditions` 플래그; 404=endpoint 미배포 vs policy not found 구분 (G1) |
| **검증** | Browser test plan (G1 후); MSW error fixture plan |
| **완료 기준** | HTTP status → title/message/retryable 표 완성 |

| HTTP/상황 | UI kind | retry | Chip 유지 |
| --- | --- | --- | --- |
| loading | (스피너) | — | — |
| empty query | empty_query | no | no |
| 200 total=0 | empty_results | no | yes |
| 422 | validation | no | yes |
| 404 | not_found | no | G1 |
| 5xx/network | server/network | yes | yes |

---

### FE4-07 — 승인 Mock 계약·API 전환 계획 (W3-F0, 문서만)

| 항목 | 내용 |
| --- | --- |
| **목표** | G1 승인 Mock 데이터셋·MSW·env gate 설계 (구현 금지) |
| **변경 파일** | 본 계획 § Mock; `frontend/src/types/draft/README.md` |
| **세부 작업** | Mock must mirror: interpreted_conditions, reasons, verdicts, pagination; Data 표본 기반 4+2 fixture 시나리오; `VITE_USE_POLICY_SEARCH_MOCK` (이름 G1); **MSW handler 구현 금지** |
| **검증** | Mock 시나리오 표 리뷰; Backend integration test parity checklist |
| **완료 기준** | G1 후 FE4-12에서 구현 가능한 Mock spec |

**Mock 시나리오 (승인 대기)**

| ID | q 입력 | 기대 interpreted | items | 비고 |
| --- | --- | --- | --- | --- |
| M1 | 서울 주거 | region match | 온통청년 valid | baseline |
| M2 | 전국 청년 | region unknown | mixed | unknown banner |
| M3 | 25세 일자리 | age match | employment | |
| M4 | 복지로 생활 | multi unknown | partial only | 복지로 표본 |
| M5 | (empty) | — | 422/empty | validation |
| M6 | mismatch heavy | exclude | empty | exclude flag |

---

### FE4-08 — Browser·반응형·접근성 검증 계획 (W3-F0)

| 항목 | 내용 |
| --- | --- |
| **목표** | G1 이후 실행할 manual·automated checklist |
| **변경 파일** | 본 계획 § 검증 계획 |
| **세부 작업** | viewport 390/1440; keyboard: SearchBar submit, Chip remove, pagination; screen reader: verdict·partial labels; reduced motion; **실행 기록 금지 (W3-F0)** |
| **검증** | checklist existence only |
| **완료 기준** | FE4-14 착수 시 복사 가능한 테스트 케이스 ≥15 |

---

### FE4-09 — `/search` route·SearchBar shell (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | NL SearchBar + URL sync wiring |
| **변경 파일** | `frontend/src/pages/user/PolicySearchPage.tsx` (신규), `frontend/src/App.tsx`, `frontend/src/components/search/SearchBar.tsx` |
| **선행** | `G1_APPROVED`; FE4-05 promoted types |
| **세부 작업** | React Router route; controlled `q`; submit → URL update → query hook; **parser 없음** |
| **검증** | `npm run build`; Browser: URL share reload |
| **완료 기준** | Mock 또는 staging API로 q round-trip |

---

### FE4-10 — Interpreted condition Chips·수정 UI (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | `interpreted_conditions` 렌더·편집·재검색 |
| **변경 파일** | `frontend/src/components/search/InterpretedConditionChips.tsx`, `ConditionEditorDrawer.tsx` |
| **세부 작업** | verdict별 variant; remove/edit; user_modified 플래그; structured override to request |
| **검증** | Browser: edit region unknown → user sets 서울 → re-fetch |
| **완료 기준** | Chip UX 초안(FE4-02)과 일치 |

---

### FE4-11 — 검색 결과 목록·reason·배지 (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | Ranked list with reasons, partial/unknown badges |
| **변경 파일** | `frontend/src/components/search/PolicySearchResultCard.tsx`, `SearchReasonList.tsx` |
| **세부 작업** | Reuse `PolicyCard` layout where possible; link to `/programs/{id}`; score display G1; global unconfirmed banner |
| **검증** | Browser M1–M4 mock scenarios |
| **완료 기준** | 복지로 partial unknown 시나리오 오해 없음 |

---

### FE4-12 — MSW 승인 Mock (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | FE4-07 Mock spec 구현 |
| **변경 파일** | `frontend/src/mocks/policySearchHandlers.ts`, fixtures JSON |
| **세부 작업** | MSW only in dev/test; no production bundle default |
| **검증** | Mock parity vs Backend contract test list |
| **완료 기준** | M1–M6 pass offline |

---

### FE4-13 — 검색 API Client·env switch (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | `getPolicySearch()` production client |
| **변경 파일** | `frontend/src/api/policySearch.ts`; promote draft types → `frontend/src/types/policySearch.ts` |
| **세부 작업** | axios; approved path only; mock gate; no duplicate list API |
| **검증** | integration against Backend staging; 422/500 cases |
| **완료 기준** | `VITE_USE_POLICY_SEARCH_MOCK=false` E2E smoke |

---

### FE4-14 — Browser·a11y·반응형 검증 실행 (G1 후)

| 항목 | 내용 |
| --- | --- |
| **목표** | FE4-08 checklist 실행·개발 기록 |
| **변경 파일** | `development_notes/frontend/policy_search.md` |
| **검증** | manual Browser + optional Playwright; document pass/fail only |
| **완료 기준** | Forest 완료 기준 충족 evidence |

---

## 검증 계획

### W3-F0 (이번 커밋)

```powershell
python3 scripts/validate_docs.py
cd frontend
npm run build
npm run lint
git diff --check
```

- Browser 테스트: **미실행** (계획만)
- MSW·API Client·UI component: **미구현**

### G1 이후 Forest 완료

- FE4-08 checklist 전항목
- Mock M1–M6 + Backend staging parity
- `include_partial`·unknown·mismatch 정책 Data 권고와 일치 확인
- 기존 `/programs` list API 회귀 없음

## Forest 완료 기준

- Gate G1 승인 및 `G1_APPROVED` 기록
- 승인된 request·response가 production types·API Client·UI에 반영
- `/search` NL 검색·Chip·reason·partial/unknown UX가 Data 표본 시나리오 통과
- Browser·a11y·반응형 검증 실행 결과가 개발 기록에 있음
- `docs/index.md` `R1-SEARCH-DATA-SEMANTICS` 후속 조치 반영
- CHANGELOG 1~2항목 (Forest 완료 시)

## 위험과 미확정 사항

| ID | 항목 | 영향 | 재개 조건 |
| --- | --- | --- | --- |
| G1-EP | endpoint·method | Client URL | Backend W3-B0 + G1 |
| G1-UNK | unknown 포함·감점 | 복지로 10건 노출 | Data 권고 + G1 |
| G1-PARTIAL | search default include_partial | partial 노출 | G1 |
| G1-MERGE | NL + structured merge | Chip edit | Backend 06 |
| G1-ROUTE | `/search` vs `/programs` 통합 | IA | Team Leader |
| FF-REBASE | Backend W3-B0 먼저 merge 시 Frontend rebase | branch | handoff § rebase |

## 관련 문서

- [3주차 Gate G1 인수인계](../../weekly_plan/week_03_search_contract_handoff.md)
- [3주차 Release 1](../../weekly_plan/week_03_release_1.md)
- [Data 02 Release Dataset Bootstrap](../data/02_release_dataset_bootstrap.md)
- [Data 02 개발 기록](../../development_notes/data/release_dataset_bootstrap.md)
- [Integration 03 Policy Search Data Foundation](../integration/03_policy_search_data_foundation.md)
- [Policy API 계약 (목록·상세)](../../../api/policies.md)
- [Policy Discovery Forest (Frontend 01)](01_policy_discovery.md)
- [Fixture·Seed 계약](../../../data/fixture_seed_contract.md)
- [ADR 0001 Policy Search Data Foundation](../../../architecture/decisions/0001-policy-search-data-foundation.md)
- W3-F0 draft types: `frontend/src/types/draft/`

## Gate G1 Frontend 체크리스트 (Team Leader용)

| # | Frontend 초안 | Backend W3-B0 | Data 권고 |
| --- | --- | --- | --- |
| 1 | `PolicySearchRequestDraft.q` | request `q` | NL 경계 |
| 2 | structured filters | pydantic fields | |
| 3 | `PolicyMatchVerdict` | evaluation enum | match/mismatch/unknown |
| 4 | `interpreted_conditions` | response block | |
| 5 | `unconfirmed_dimensions` | global unknowns | no national guess |
| 6 | `reasons[]` per item | reason DTO | |
| 7 | partial badge + include_partial | partial policy | 복지로 10건 |
| 8 | 422/404/500 UX | error contract | |
| 9 | URL state | — | shareable search |
| 10 | Mock M1–M6 | contract tests | actual profile |

## 기존 Frontend 구조 분석 (W3-F0)

| 경로 | 현재 역할 | Frontend 04 관계 |
| --- | --- | --- |
| `frontend/src/types/policy.ts` | `PolicyDto`, list query | 검색 결과 `policy` embed |
| `frontend/src/api/policies.ts` | list/detail client | 유지; 검색 API 별도 |
| `frontend/src/pages/user/SearchPage.tsx` | `/programs` exact+local filter | 검색 API **미사용** |
| `frontend/src/utils/policyFilters.ts` | client-side filter | `/search`와 **병행** |
| `frontend/src/components/policy/PolicyCard.tsx` | list card | FE4-11 reuse 참고 |
| `frontend/src/types/draft/*` | W3-F0 초안 | G1 전 production import 금지 |
