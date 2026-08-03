# Policy Search Data Foundation Forest 개발 기록

## 작업 정보

- 시작일: 2026-08-03
- 상태: in-progress
- 영역: Data·Backend 공동 통합, Frontend 소비 검토, Team Leader Gate
- 브랜치: `feature/database/policy-search-foundation`
- 기반 브랜치: `feature/data/release-dataset-bootstrap`
- 관련 계획:
  [`03_policy_search_data_foundation.md`](../../develop_plan/integration/03_policy_search_data_foundation.md)
- 현재 Slice: PSF7 completed, PSF8 next

## 목적

실제 온통청년·복지로 응답의 검색 key가 현재 Extracted 이후 어디에서
유실되는지 확인하고, 장기 지역 Source를 수용할 공통 데이터·DB·검색 경계를
구현 전에 승인한다. 기존 Policy 목록·상세와 Frontend 소비를 깨뜨리지 않도록
새 검색 projection과 query별 판정 책임을 분리한다.

## Forest 범위

- Source 중립 검색 데이터 계약과 Source별 lineage
- versioned 행정구역 기준정보와 정책 적용 관계
- PostgreSQL Migration과 search projection
- Importer transaction·idempotency·rollback
- 지역·연령·상태의 `match|mismatch|unknown` 판정 primitive
- 기존 Policy API·Frontend 호환과 actual DT1 Raw 재생

Backend 자연어 parser·최종 관련도 가중치, Frontend 검색 UI, 실제 지자체
crawler와 Release snapshot bootstrap은 이 기록의 Forest 범위 밖이다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| PSF0 | completed | 현재 lineage·손실·partial 영향 감사, ADR 0001 승인, version·DB·API 경계 확정 |
| PSF1 | completed | Normalized 1.1.0 실행 계약·legacy adapter·지역 경계 Fixture·소비 전환 검증 |
| PSF2 | completed | 공식 법정동 snapshot, versioned 지역·별칭 Seed와 exact resolver |
| PSF3 | completed | 검색 컬럼·지역 관계·projection Migration, 제약과 지역 Seed 적재 |
| PSF4 | completed | 두 Source 검색 field mapping, exact 지역 증거 resolver와 actual Raw 재생 |
| PSF5 | completed | Policy·지역 규칙·versioned projection 원자적 적재와 Runtime warning lineage 보존 |
| PSF6 | completed | 지역·연령·신청 상태 3값 판정, alias 모호성·projection field별 근거 |
| PSF7 | completed | 기존 소비·Backend 실행 호환, 합성 query plan, actual Raw 재생·DB dry-run |
| PSF8 | pending | Forest Gate와 Data 02 인계 |

## 구현 내용

### PSF0 - 현재 계약 감사와 ADR Gate

- DT1 실제 표본 결과를 기준으로 온통청년 10건과 복지로 10건이 모두
  `partial`이고 기존 목록·상세 기본 응답에서 숨겨지는 영향을 확인했다.
- `collectors/extractors.py`, `ExtractedPolicy`, `NormalizedProgram`,
  Normalizer·Validator, Backend Importer·ORM·Repository·Pydantic DTO와
  Frontend `PolicyDto`·Mock filter를 정적으로 대조했다.
- 온통청년 `plcyExplnCn`, `mclsfNm`, `plcyKywdNm`과 복지로
  `wlfareInfoOutlCn`, `lifeArray`, `trgterIndvdlArray`가 Raw와
  `extra.source_fields`에는 남지만 현재 Normalized·DB·API에는 도달하지
  않는 것을 확인했다.
- 온통청년 `zipCd`는 현재 `region_text`로 전달되지만 승인된 code table이
  없어 `regions=[]`가 되고, 복지로는 지역 key 자체가 없어 두 경우를
  동일한 빈 배열만으로 구분할 수 없음을 확인했다.
- 기존 Backend `region` query와 Frontend Mock 지역 필터는 `regions` 문자열
  exact membership이고, Frontend는 문자열 `전국`을 특별 처리한다. 이
  호환 필터를 새 계층 판정으로 조용히 바꾸지 않기로 했다.
- [ADR 0001](../../../architecture/decisions/0001-policy-search-data-foundation.md)을
  `accepted`로 변경하고 Raw→Extracted→Normalized→DB→API lineage,
  1.1.0 필드, 지역 rule, 테이블 이름과 Migration 영향을 확정했다.

### PSF0 - 계약 결정

- `NormalizedProgram` 1.1.0은 기존 31개 필드에 `keywords`,
  `life_stages`, `target_groups`, `coverage_scope`, `region_rules`를 추가한다.
  배열은 항상 배열이며 누락 시 `[]`, coverage는 필수 enum이고 근거가 없으면
  `unknown`이다.
- `region_rules`는 include·exclude, canonical scheme·code, Source code·text와
  `matched|unmapped|ambiguous`를 함께 보존한다. 이름이나 code 앞자리로
  canonical region을 추정하지 않는다.
- 기존 1.0.0 입력은 PSF1 compatibility adapter가 새 배열 `[]`와
  `coverage_scope=unknown`만 보완한다. 기존 `regions`를 canonical rule이나
  전국 근거로 자동 승격하지 않는다.
- 기존 DB row의 `schema_version`은 Migration만으로 바꾸지 않는다. 실제 Raw
  재처리 또는 승인된 1.1.0 입력이 있을 때만 1.1.0이 된다.
- 저장 이름은 `administrative_regions`, `administrative_region_aliases`,
  `policy_region_rules`, `policy_search_documents`와 정책의 네 검색 컬럼으로
  고정했다.
- 기존 `/api/v1/policies` 목록·상세 field set, exact region filter,
  provenance 비노출과 partial opt-in은 유지한다. Frontend는 전환 기간의
  `schema_version`만 1.0.0·1.1.0 union으로 소비해야 한다.
- 새 검색은 valid·partial을 후보로 사용한다. 명시적 `mismatch`는 제외하고
  `unknown`은 `unverified_conditions`로 반환한다. 따라서 Source 완전성
  `partial`을 사용자 검색 부적합으로 오용하지 않는다.
- 검색 점수·조건·이유는 query별 값이므로 기존 Policy DTO나 Policy 원본
  row에 저장하지 않는다. Backend 06 검색 응답과 Frontend 04가 별도로
  소비한다.

### PSF0 - 영역별 소비 검토

| 영역 | 확인한 현재 소비 | 결정 영향 |
| --- | --- | --- |
| Data | strict 1.0.0 field set, nullable 단일 값, 배열 `[]`, source field `extra` | PSF1에서 1.1.0 Schema·모델·legacy adapter와 Source 경계 Fixture 필요 |
| Backend | 31개 ORM·Importer mapping, JSONB exact region, 기본 valid 공개 | PSF3~PSF6에서 additive DB·transaction·3값 primitive; 기존 endpoint 회귀 유지 |
| Frontend | `schema_version: '1.0.0'`, 기존 PolicyDto와 client-side exact/전국 처리 | PSF1에서 version union 소비 검증, Frontend 04에서 별도 검색 응답으로 교체 |
| Team Leader | DT1 실제 표본과 Release 1 검색 요구, Data 02 DT2 차단 관계 | PSF0 Gate 승인, PSF8 전 기존 인계 항목 유지 |

현재 Schema, Fixture, Seed, DB, 공개 API와 Frontend 코드는 PSF0에서 변경하지
않았다. 승인된 설계를 실제 계약으로 구현하는 시점은 PSF1 이후이며, 각
Slice에서 관련 기준 문서와 소비 테스트를 함께 갱신한다.

### PSF1 - 검색 데이터 계약과 Fixture

- `NormalizedProgram`과 JSON Schema를 1.1.0·36개 필드로 갱신하고 검색용
  문자열 배열 3개, coverage enum과 근거 보존형 `RegionRule`을 구현했다.
- exact 1.0.0 field set만 compatibility adapter로 받아 새 배열 `[]`,
  `coverage_scope=unknown`, `region_rules=[]`를 보완한다. 기존 `regions`에서
  전국이나 canonical 지역을 추정하지 않는다.
- 전국·지역·미확인의 coverage 불변식, matched·unmapped·ambiguous의 canonical
  identity·Source evidence 규칙과 include/exclude 중복·충돌을 Validator와
  모델 양쪽에서 검사한다.
- 외부 원문이 없는 합성 계약 Fixture 7건으로 전국, 상위 지역, 정확 지역,
  제외 지역, 미확인, 동명이인, 폐지 code 경계를 고정했다.
- canonical Seed를 1.1.0으로 결정적 재생성했다. PSF4 Source 매핑 전이므로
  새 검색 필드는 안전한 기본값만 가진다.
- 현재 Backend ORM이 기존 31개 필드만 저장하므로 기본값이 아닌 검색 필드가
  들어오면 importer가 `search_storage_not_ready`로 거부한다. 이는 PSF3 전
  조용한 데이터 손실을 막는 전환 경계다.
- Frontend `PolicyDto`는 version을 1.0.0·1.1.0 union으로 넓혔지만 새 검색
  5개 필드는 기존 목록·상세 공개 DTO에서 제외함을 소비 테스트로 고정했다.

### PSF2 - 행정구역 기준정보

- 행정안전부 법정동코드 조회의 존재·폐지 전체 목록과 상세 다운로드를
  `2026-08-03`에 대조해 53,387건을 결정적 gzip CSV로 고정했다. manifest는
  source·license URL, 존재 20,560건, 폐지 32,827건과 정규화 CSV SHA-256을
  보존한다.
- 정책 지역 판정에는 시·도와 시·군·구 537건을 선택하고 대한민국 시스템
  루트 1건을 추가했다. `kr-bjd-20260803` scheme의 지역 538건과 공식
  전체명·최하지역명·승인 축약 1,080건을 별도 Seed로 생성한다.
- 공식 `parent_code`와 감사용 `source_parent_code`를 보존한다. 공식 parent가
  비자치구의 집계 시를 표현하지 않는 경우, 같은 광역 parent 아래 현재 유효
  전체 이름이 정확히 일치할 때만 `aggregate_parent_code`를 추가한다.
- 이 규칙으로 `천안시 동남구 → 천안시 → 충청남도 → 대한민국` ancestor를
  제공한다. 이름이나 code prefix를 실행 시점에 일반 추정하지 않으며 폐지
  code의 후계 지역도 만들지 않는다.
- 별칭 resolver는 Unicode NFKC와 공백만 정규화하고 여러 지역의 `중구`를
  `ambiguous`로 반환한다. 5자리 crosswalk도 Seed에 명시된 exact 값만
  `matched`로 처리하고 없는 값은 `unmapped`로 반환한다.
- PSF1 검색 계약 Fixture의 합성 지역 identity를 실제 scheme과 충남·천안·
  아산·폐지 천안군 code로 교체했다. Source 응답과 정책 내용은 계속 합성이며
  온통청년 `zipCd`의 의미 확정은 PSF4에 남겼다.

### PSF3 - PostgreSQL Migration과 ORM

- Alembic head `20260803_0004`를 추가해 Policy에 `keywords`, `life_stages`,
  `target_groups` JSONB와 `coverage_scope` enum을 저장한다. 기존 row에는
  `[]`·`unknown`을 backfill하지만 실제 `schema_version`은 변경하지 않는다.
- `administrative_regions`, `administrative_region_aliases`,
  `policy_region_rules`, `policy_search_documents` ORM과 테이블을 구현했다.
  공식 parent와 aggregate parent, 유효기간, 다중 별칭, Source 근거와
  matched·unmapped·ambiguous를 관계형으로 보존한다.
- 지역 parent는 composite FK와 deferred cycle trigger로 검사한다. 정책
  coverage는 transaction 최종 상태에서 nationwide rule 금지, regional
  matched include 필수, unknown matched rule 금지를 검사한다.
- 같은 정책·canonical 지역의 중복과 include·exclude 충돌을 unique
  constraint로 차단하고 unresolved rule은 canonical FK를 금지하면서 Source
  근거를 요구한다.
- `policy_search_documents.search_text`에 `pg_trgm`의 `gin_trgm_ops` GIN
  index를 추가했다. 이 Migration이 설치한 것인지 구분할 수 없는 공용
  extension은 downgrade에서 제거하지 않는다.
- 지역 Seed importer와 `python -m app.cli.import_regions`를 추가했다. 같은
  versioned scheme을 반복 적재하면 unchanged이고, DB 값이 Seed와 다르거나
  예상 밖 code·alias가 있으면 덮어쓰지 않고 transaction을 실패시킨다.
- 기존 Policy importer는 검색 배열·coverage를 저장하도록 확장했다.
  `region_rules` 관계·projection의 원자적 교체는 PSF5 책임이므로 비어 있지
  않은 rules는 `search_relation_storage_not_ready`로 명시적으로 거부한다.
- 기존 Policy 목록·상세 API와 Frontend DTO 필드 집합은 변경하지 않았다.

### PSF4 - Source Adapter와 정규화

- `ExtractedPolicy`에 `summary`, `keywords`, `life_stages`, `target_groups`,
  `coverage_scope_hint`와 `SourceRegionEvidence`를 추가했다. 향후 HTML Source도
  같은 code·text·include·exclude 경계를 사용하므로 공통 Normalizer가 Source
  key나 selector를 직접 알 필요가 없다.
- 온통청년 `plcyExplnCn`을 summary, `mclsfNm`과 `plcyKywdNm`을 keywords로
  옮긴다. `zipCd`가 쉼표 구분 5자리 목록일 때만 `kr-bjd-prefix5` Source
  evidence를 만들며 그 밖의 문자열이나 누락은 지역으로 추정하지 않는다.
- 복지로 summary는 상세 `wlfareInfoOutlCn` 우선·목록 `servDgst` fallback,
  keywords는 `intrsThemaArray`, life stages는 `lifeArray`, target groups는
  `trgterIndvdlArray`를 사용한다. 상세 값이 없을 때만 목록 값으로 fallback하며
  쉼표 문자열과 반복 XML leaf를 모두 순서 보존 배열로 처리한다.
- 공통 Normalizer는 versioned 지역 Seed를 캐시해 Adapter가 명시한 code는
  exact external-code resolver, text는 alias resolver로 처리한다. matched는
  canonical code와 표시 `regions`, unmapped·ambiguous는 Source 증거만 가진
  rule로 만든다. 폐지 code도 `active_only=False` exact identity로 보존하고
  후계 지역으로 치환하지 않는다.
- 실제 DT1 Raw 대조에서 온통청년 `zipCd`는 총 373개·고유 260개였고 모두
  exact crosswalk에 유일하게 일치했다. 개편 전 인천 code 3개가 발견되어
  현행 code로 자동 치환하지 않는 경계를 고정했다.
- 실제 Raw 오프라인 재생 결과 온통청년은 10건 중 valid 8·partial 2,
  summary·keywords 10건, regional 10건, matched rule 373개였다. 복지로는
  partial 10건, summary 10·keywords 9·life stages 8·target groups 5건이며
  지역 근거가 없어 모두 unknown·rule 0건이었다.
- 합성 Raw·Extracted·Normalized·검색 계약 Fixture와 canonical Seed를
  결정적으로 재생성했다. Seed는 실제 Source 검색 값을 포함하지만 지역 관계
  rule은 PSF5 전환 동안 비워 기존 PostgreSQL·API 회귀 경계를 유지한다.
- 공개 Policy API와 Frontend DTO 필드 집합은 변경하지 않았다. Runtime
  온통청년 결과의 비어 있지 않은 rule은 PSF5 전까지 importer가
  `search_relation_storage_not_ready`로 거부하므로 손실 적재하지 않는다.

### PSF5 - Import transaction과 projection 동기화

- `PolicySearchRepository`는 관계 rule을 순서 없는 집합으로 비교하고 값이
  달라질 때만 정책별 행을 전체 교체한다. matched FK와 unresolved Source
  evidence는 Normalized 1.1.0의 여섯 필드를 그대로 저장한다.
- projection service는 title·keyword·summary·eligibility·support field군을
  NFKC·공백 정규화하고 `search_text`로 합성한다. 현재 version은 `1.0.0`이며
  값과 version이 같으면 projection 행과 timestamp를 바꾸지 않는다.
- Policy upsert 뒤 관계와 projection을 같은 importer transaction에서
  동기화한다. Policy 컬럼이 같아도 rule 또는 projection이 달라지면 updated,
  세 저장 대상이 모두 같을 때만 unchanged다. source identity와 created_at은
  유지하고 updated_at은 감소하지 않는다.
- projection 재생성 service는 commit을 소유하지 않아 호출자가 transaction과
  대상 policy ID를 결정한다. importer 중간 관계 상태는 외부에 노출되지 않는다.
- PostgreSQL projection trigger로 두 번째 policy write를 강제 실패시켜 앞선
  Policy·rule·projection까지 batch 전체가 rollback되는 것을 확인했다.
- 첫 실제 온통청년 dry-run에서 `unmapped_category` warning으로 정한 partial
  2건이 canonical 객체 재검증만으로는 valid로 재분류되어
  `quality_status_mismatch`가 발생하는 기존 Runtime 경계를 발견했다. Validator를
  느슨하게 만들지 않고 `RuntimeReplayResult`가 accepted program과 Normalizer
  issue를 같은 순서로 전달하도록 수정했다. 이후 같은 Raw 10건과 복지로
  partial 10건이 DB admission을 통과했다.
- 실제 API는 재호출하지 않았다. Runtime DB에서 두 Source를 `--dry-run`해 실제
  FK·constraint·projection write까지 수행한 뒤 rollback했으며 Policy·rule·
  projection·CollectionRun은 모두 0건으로 유지됐다.

### PSF6 - 지역·조건 판정 primitive

- `PolicySearchEvaluationService`와 순수 판정 함수를 추가해 Backend 06이 DB
  조회와 판정 의미를 재구현하지 않고 조합할 수 있게 했다. 모든 조건 결과는
  `match|mismatch|unknown`과 기계 판독 가능한 reason을 가진다.
- query 지역 alias는 NFKC·공백 정규화 뒤 현재 scheme의 active 후보를 exact
  조회한다. 후보 없음·한 건·여러 건을 `unmapped|matched|ambiguous`로 분리하고
  모호한 경우 canonical 후보 목록을 버리지 않는다.
- regional policy는 query 지역에서 `aggregate_parent_code`를 우선해 상위
  경로를 만든다. 정확 지역과 상위 include를 구분하고, 같은 경로의 exclude는
  include보다 먼저 mismatch로 판정한다. 다른 active include는 mismatch,
  unresolved·retired rule 또는 coverage unknown은 unknown이다.
- 나이는 확인된 최소·최대 범위와 명시적 `연령 제한 없음`만 match로 처리한다.
  신청 상태는 `open|closed|scheduled` exact 비교이며 저장 상태 null은
  unknown이다. 입력 범위를 벗어난 나이와 지원하지 않는 요청 상태는 오류로
  거부한다.
- projection은 미리 해석된 검색어를 title·keyword·summary·eligibility·
  support 각 필드에 대조해 일치어와 미일치어를 근거로 반환한다. 이 단계는
  동의어를 만들거나 점수를 계산하지 않아 자연어 parser·가중치 책임을
  Backend 06에 남긴다.
- 기존 Policy 목록·상세 Repository와 API, DB Schema·Migration, Fixture·Seed,
  Frontend 타입과 UI는 변경하지 않았다.

### PSF7 - 소비 호환·성능·실데이터 재생

- 기존 Backend mapping 테스트와 Frontend `PolicyDto`를 다시 대조해 공개
  `PolicyRead` 33개 필드와 1.0.0·1.1.0 version union을 유지했다. keywords·
  life stages·target groups·coverage·region rules와 projection은 기존 목록·
  상세 OpenAPI에 노출하지 않는다.
- Frontend 계약 테스트가 welfare 2건을 기대했지만 PSF4 canonical Seed의 실제
  welfare는 `SYN-YOUTH-002` 1건임을 확인했다. Mock 필터나 Seed를 바꾸지 않고
  테스트를 1건과 정확한 identity 검증으로 동기화했다.
- `backend` 디렉터리에서 Uvicorn을 실행하면 PSF6 판정 service의
  `collectors.regions` import 때문에 시작하지 못하는 회귀를 발견했다. alias
  정규화를 이미 Backend projection이 제공하는 동일한 NFKC·공백 함수로
  연결해 저장소 루트가 `PYTHONPATH`에 없어도 실행되게 했고 subprocess import
  회귀 테스트를 추가했다.
- Backend 06에는 지역 해석 후보, 지역·연령·신청 상태의 state·reason·evidence,
  projection field별 일치·미일치어를 내부 입력으로 인계한다. 공개 검색 응답
  이름, parser·동의어·점수와 pagination은 여기서 확정하지 않았다.
- 전용 PostgreSQL에 합성 policy·projection 20,000건을 만들고 200건 일치
  `EXPLAIN (ANALYZE, BUFFERS)`를 실행했다. 기본 `ILIKE`는 Sequential Scan
  19.258ms, 기본 `LIKE`는 Sequential Scan 2.597ms, 강제 trigram GIN
  `ILIKE`는 Bitmap Scan 2.030ms였다. index는 정상 사용 가능하지만 기본
  planner가 선택하지 않는 위험을 Backend 06 실제 query plan으로 인계했다.
- 저장된 DT1 Raw를 API 재호출 없이 다시 재생했다. 온통청년은 10건 accepted,
  valid 8·partial 2, regional 10, matched rule 373, 연령 범위 9·미상 1,
  open 6·closed 3·scheduled 1이었다. projection 5개 field군의 빈 값은 없었다.
- 복지로는 10건 accepted·partial 10, coverage·연령·신청 상태 unknown 10이었다.
  지역 rule은 0건이고 eligibility projection 2건·keyword projection 1건이
  비어 있다. Source 근거가 없는 값을 전국·특정 지역·연령·open으로 만들지
  않았음을 확인했다.
- Runtime DB에서 두 Source 각 10건을 실제 FK·constraint·projection write까지
  dry-run한 뒤 rollback했다. 전후 Policy·rule·projection·CollectionRun은
  모두 0건이고 지역 538건·별칭 1,080건은 유지됐다.
- 1280×720 인앱 Browser에서 홈·검색·기본 목록·partial 포함·복지 필터·자산
  검색·partial 상세·빈 결과·직접 진입과 새로고침 기능은 모두 통과했다.
  console error·warning, React 오류 화면과 관찰된 네트워크 실패도 없었다.
- `/programs`에서 partial 포함 시 두 partial 카드의 `정보 일부 누락`
  배지가 `PolicyCard` 제목과 같은 `overflow: hidden; white-space: nowrap`
  영역에 놓여 `정보...`처럼 잘리는 임시 Mock UI 결함도 확인했다. 데이터·API·
  소비 계약 회귀는 아니므로 PSF7 차단사항으로 보지 않고 Frontend 최종 디자인과
  Integration 04 Browser 검증에 인계한다.

## 주요 변경 파일

- `collectors/normalized.py`
- `collectors/normalizer.py`
- `collectors/validation.py`
- `data/schema/normalized_program.schema.json`
- `data/fixtures/contracts/policy_search_region_cases.json`
- `data/fixtures/normalized/programs.json`
- `data/fixtures/rejected/programs.json`
- `data/seeds/initial_programs.json`
- `scripts/build_data_fixtures.py`
- `backend/app/services/seed_importer.py`
- `backend/app/services/runtime_importer.py`
- `backend/app/services/policy_search_projection.py`
- `backend/app/services/policy_search_evaluation.py`
- `backend/app/repositories/policy_search.py`
- `collectors/runtime.py`
- `frontend/src/types/policy.ts`
- `frontend/src/mocks/policyContract.ts`
- `docs/data/data_schema.md`
- `docs/data/normalization_rules.md`
- `docs/data/fixture_seed_contract.md`
- `docs/architecture/policy_database_mapping.md`
- `docs/api/policies.md`
- `docs/architecture/decisions/0001-policy-search-data-foundation.md`
- `docs/architecture/decisions/README.md`
- `docs/development/develop_plan/integration/03_policy_search_data_foundation.md`
- `docs/development/develop_plan/README.md`
- `docs/development/develop_plan/forest_roadmap.md`
- `docs/development/development_notes/integration/policy_search_data_foundation.md`
- `docs/development/development_notes/README.md`
- `docs/index.md`
- `collectors/regions.py`
- `data/reference/administrative_regions/`
- `data/seeds/administrative_regions.json`
- `data/seeds/administrative_region_aliases.json`
- `scripts/fetch_administrative_regions.py`
- `scripts/build_administrative_regions.py`
- `tests/test_administrative_regions.py`
- `docs/data/administrative_regions.md`
- `backend/alembic/versions/20260803_0004_policy_search_storage.py`
- `backend/app/models/administrative_region.py`
- `backend/tests/test_policy_search_projection.py`
- `backend/tests/test_postgresql_policy_search_import.py`
- `backend/tests/test_policy_search_evaluation.py`
- `backend/tests/test_postgresql_policy_search_evaluation.py`
- `backend/tests/test_postgresql_policy_search_performance.py`
- `backend/tests/test_app_import_boundary.py`
- `backend/app/models/policy_search.py`
- `backend/app/models/policy.py`
- `backend/app/services/region_reference_importer.py`
- `backend/app/services/seed_importer.py`
- `backend/app/cli/import_regions.py`
- `backend/tests/test_policy_search_models.py`
- `backend/tests/test_region_reference_importer.py`
- `backend/tests/test_postgresql_policy_search_migration.py`
- `collectors/extracted.py`
- `collectors/extractors.py`
- `collectors/normalizer.py`
- `tests/test_extractors.py`
- `tests/test_normalization.py`
- `tests/test_data_fixtures.py`
- `docs/data/source_profiles.md`
- `docs/operations/collector.md`
- `frontend/tests/policy-contract.test.ts`

## 설계 결정

- Source 누락값과 미매핑 code를 전국·특정 지역으로 보정하지 않는다.
- `regions` 문자열 배열은 기존 표시·exact filter 호환용이고 새 지역 identity는
  versioned scheme·code와 관계형 rule이 담당한다.
- `NormalizedProgram`은 1.1.0으로 확장하지만 populated DB의 1.0.0 row는
  사실과 다르게 일괄 version 변경하지 않는다.
- 공개 목록·상세와 새 자연어 검색의 후보·응답 의미를 분리한다.
- `partial`과 조건 `unknown`을 분리해 실제 정책이 데이터 완전성만으로 검색
  후보에서 모두 사라지는 회귀를 막는다.
- `region_rules`는 매핑된 canonical 관계뿐 아니라 unmapped·ambiguous Source
  evidence도 보존해 향후 기준정보 갱신 뒤 재처리할 수 있게 한다.
- 지역 query가 모호하거나 미매핑이면 regional policy를 임의 일치시키지
  않고 unknown으로 남긴다. nationwide는 지역 query 상태와 무관하게 match다.
- active canonical include가 다른 지역만 가리킬 때만 mismatch이며 unresolved
  rule이 있으면 오탐 방지를 위해 unknown을 우선한다. 일치 exclude는 가장
  가까운 include보다도 우선한다.
- projection primitive는 field evidence만 제공한다. 검색어 추출·동의어와
  최종 순위 규칙은 Backend 06 계약 없이 이 Forest에서 고정하지 않는다.
- Backend 실행 계층은 저장소 루트 `collectors` 패키지 경로에 의존하지 않는다.
  공통 저장 계약은 공유하되 Uvicorn의 문서화된 작업 디렉터리에서 독립적으로
  import 가능해야 한다.
- 합성 plan에서 GIN이 강제 사용 가능하다는 사실만으로 운영 기본 plan을
  보장하지 않는다. 최종 query 형태와 실제 분포 없이 DB 비용 설정이나 index를
  변경하지 않는다.

## 검증 결과

PSF0는 계약 감사 Slice이므로 외부 API 호출, Runtime Raw 변경, DB Migration과
코드 변경을 수행하지 않았다.

| 검증 | 결과 |
| --- | --- |
| Data·Backend 계약 단위 테스트 | Extractor·Normalizer·Fixture·mapping·Policy API 40건 통과 |
| Frontend 소비 테스트 | Node 24.18.0, 7건 통과 |
| Frontend lint | 통과 |
| Frontend production build | Vite 8.1.5, 210 modules build 통과 |
| PostgreSQL Policy API 통합 테스트 | `TEST_DATABASE_URL`·`PGPASSFILE` 미설정으로 1건 skip, 성공으로 간주하지 않음 |
| 문서 검증기 단위 테스트 | 10건 통과 |
| `scripts/validate_docs.py` | 통과 |
| `git diff --check` | 통과 |

PowerShell의 `npm.ps1`은 로컬 ExecutionPolicy에 차단됐지만 Node·npm 부재가
아니었다. 저장소 설정을 바꾸지 않고 `npm.cmd`로 같은 test·lint·build를
실행해 통과했다. 테스트가 생성한 `frontend/.test-dist`와 `frontend/dist`는
검증 후 제거했다.

Python 계약 테스트와 PostgreSQL skip에서 기존 Starlette `httpx` 사용
deprecation warning 1건이 발생했다. 이는 DT1에서 이미 확인한 범위 밖
의존성 경고이며 PSF0에서 패키지를 변경하지 않았다.

### PSF1 검증 (`2026-08-03`)

| 검증 | 결과 |
| --- | --- |
| Fixture·Seed 결정적 재생성 검사 | 13개 파일 일치 |
| Data·Backend 단위·통합 테스트 | PostgreSQL 전용 항목 포함 174건 통과, 25 subtests 통과 |
| PostgreSQL 대상 테스트 | 전용 `_test` DB에서 Migration·Seed·Runtime·Repository·API 24건 통과 |
| Frontend 소비 테스트 | 7건 통과 |
| Frontend lint | 통과 |
| Frontend production build | Vite 8.1.5, 210 modules build 통과 |
| Browser UI 회귀 | Vite `localhost:3000` 실행 확인, 현재 앱의 Browser 연결 목록이 비어 있어 직접 화면 검증 미실행 |
| `scripts/validate_docs.py` | 통과 |
| `git diff --check` | 통과, line-ending 안내만 발생 |

현재 Slice는 DB Schema를 바꾸지 않는다. SQLite·계약 테스트와 전용 `_test`
PostgreSQL 종단 테스트로 1.1.0 기본값 저장 호환, 의미 있는 검색 필드의
명시적 거부, Migration upgrade·downgrade와 기존 API 회귀를 검증했다.
Frontend test·build가 생성한 `.test-dist`와 `dist`는 검증 후 제거했다.

### PSF2 검증 (`2026-08-03`)

| 검증 | 결과 |
| --- | --- |
| 공식 전체·상세 자료 수집 대조 | 53,387건 일치, 존재 20,560건·폐지 32,827건 |
| 지역 Seed 결정적 재생성 `--check` | 지역 538건·별칭 1,080건 일치 |
| Data 단위 테스트 | 100건 통과 |
| Backend·Integration pytest | 69건 통과, PostgreSQL 전용 12건 skip |
| PSF2 지역 경계 테스트 | 7건 통과 |

PSF2는 DB Schema나 공개 API·Frontend UI를 변경하지 않는다. PostgreSQL 전용
12건은 현재 shell에 `TEST_DATABASE_URL`·`PGPASSFILE`이 없어 skip됐으며
성공으로 간주하지 않았다. 이 Slice의 지역 기준정보는 파일 모델과 Seed
경계이므로 DB 적재·Migration 통합 검증은 PSF3 완료 기준에서 수행한다.
기존 Starlette `httpx` deprecation warning 1건은 그대로 발생했으며 PSF2
범위에서 의존성을 바꾸지 않았다.

### PSF3 검증 (`2026-08-03`)

| 검증 | 결과 |
| --- | --- |
| Data 단위 테스트 | 100건 통과 |
| Backend·Integration 전체 pytest | PostgreSQL 포함 91건 통과 |
| 신규 PostgreSQL Migration 종단 | 빈·populated upgrade, downgrade→upgrade와 constraint 통과 |
| 지역 Seed PostgreSQL 적재 | 지역 538건·별칭 1,080건, 반복 적재 unchanged |
| Runtime DB Migration | `20260730_0003` → `20260803_0004` 적용 |
| Runtime DB 상태 | Policy·CollectionRun·rule·projection 0건 유지, 지역 538건·별칭 1,080건 |
| `pg_trgm` | Runtime·`_test` DB 설치 및 trgm GIN index 확인 |

전용 `_test` DB에서 기존 1.0.0 row를 먼저 만든 뒤 head로 upgrade해 version을
그대로 유지하면서 새 기본값만 채우는 것을 확인했다. 지역 parent·aggregate
parent, matched·unmapped rule, coverage 불변식, canonical 충돌, cycle,
projection timezone 왕복을 검사했다. downgrade 후 기존 Policy row·31개
계약이 남고 재-upgrade되는 것도 확인했다.

Runtime DB는 적용 전 Policy·CollectionRun이 모두 0건이었다. head 적용과 지역
기준정보 적재 뒤에도 두 테이블은 0건이고 검색 rule·projection도 0건이다.
기존 Starlette `httpx` deprecation warning 1건은 유지하며 PSF3 범위에서
의존성을 변경하지 않았다. Frontend/API 계약 변경이 없어 Browser UI 검증은
수행하지 않았다.

### PSF4 검증 (`2026-08-03`)

| 검증 | 결과 |
| --- | --- |
| Source Adapter·Normalizer 집중 테스트 | 34건 통과 |
| Data 전체 단위 테스트 | 102건 통과 |
| Fixture·Seed 결정적 재생성 검사 | 13개 파일 일치 |
| Backend·Integration 전체 pytest | PostgreSQL 포함 91건 통과, 기존 warning 1건 |
| DT1 온통청년 Raw 오프라인 재생 | 10건 accepted, valid 8·partial 2, matched rule 373개 |
| DT1 복지로 Raw 오프라인 재생 | 10건 accepted, partial 10, coverage unknown 10건 |

실제 API를 다시 호출하지 않고 Git 제외 Runtime Raw와 provenance를 재생했다.
PSF4는 DB Schema·공개 API·Frontend UI를 변경하지 않으므로 Migration 추가와
Browser UI 검증은 수행하지 않았다.

### PSF5 검증 (`2026-08-03`)

| 검증 | 결과 |
| --- | --- |
| Projection·Importer 집중 단위 테스트 | 정책·rule·projection 동시 적재, version 복구, partial warning lineage 통과 |
| Data 전체 단위 테스트 | 102건 통과 |
| Backend·Integration 전체 pytest | PostgreSQL 포함 96건 통과, 기존 warning 1건 |
| PostgreSQL 원자성 | 동일 입력 unchanged·중복 0건, projection 강제 실패 batch 전체 rollback |
| Fixture·Seed 결정적 재생성 검사 | 13개 파일 일치 |
| 행정구역 Seed 결정적 검사 | 지역 538건·별칭 1,080건 일치 |
| 온통청년 actual Raw DB dry-run | 10건 accepted·insert 후보 10, rollback 후 DB 0건 |
| 복지로 actual Raw DB dry-run | 10건 accepted·insert 후보 10, rollback 후 DB 0건 |

actual Raw 검증은 저장된 Runtime Raw만 사용했고 외부 API를 호출하지 않았다.
DB Migration과 공개 Policy API·Frontend DTO는 바꾸지 않았으므로 새 Migration과
Browser UI 검증은 수행하지 않았다.

### PSF6 검증 (`2026-08-03`)

| 검증 | 결과 |
| --- | --- |
| PSF6 SQLite 판정 집중 테스트 | 3건 통과 |
| PSF6 PostgreSQL 종단 테스트 | 1건 통과, 공식 지역 538건·별칭 1,080건 적재 후 downgrade |
| Data 전체 단위 테스트 | 102건 통과 |
| 관련 검색 저장·projection 회귀 | 13건 통과, 기존 warning 1건 |
| Backend·Integration 전체 pytest | 99건 통과, 기존 CollectionRun 순서 테스트 1건 실패 |
| 실패 항목 단독 재실행 | 1건 통과 |
| Python compileall | 통과 |
| Ruff | 저장소 환경에 모듈이 없어 미실행, 성공으로 간주하지 않음 |
| `scripts/validate_docs.py` | 통과 |
| `git diff --check` | 통과, line-ending 안내만 발생 |
| PostgreSQL 테스트 DB 정리 | downgrade 후 `policies` 테이블 없음 확인 |

전체 pytest의 실패는 세 CollectionRun을 매우 빠르게 만들 때 같은
`started_at` 값이 생기면 `run_id` 정렬이 호출 순서를 보장하지 않는데 테스트가
그 순서를 기대하는 기존 비결정성이다. 같은 테스트 단독 실행은 통과했지만
전체 회귀를 통과로 기록하지 않는다. PSF6는 해당 코드와 테스트를 수정하지
않았으며 별도 담당 범위에서 안정적인 정렬 기준 또는 assertion을 결정해야
한다. 공개 API·Frontend UI 변경이 없어 Browser 검증은 수행하지 않았다.

### PSF7 검증 (`2026-08-03`)

| 검증 | 결과 |
| --- | --- |
| Data 전체 단위 테스트 | 102건 통과 |
| Backend·Integration 전체 pytest | PostgreSQL·신규 성능 테스트 포함 102건 통과, 기존 warning 1건 |
| Backend 실행 경계 집중 테스트 | subprocess import·판정 4건 통과 |
| 실제 FastAPI HTTP | 임시 8001번에서 health·목록 200, `PolicyRead` 33 fields·검색 내부 field 0 |
| Frontend 계약 테스트 | 최초 6/7, stale welfare 기대 수정 후 7/7 통과 |
| Frontend lint·production build | 통과, Vite 8.1.5·210 modules |
| Vite HTTP | 임시 `127.0.0.1:3000` root·`/programs` 200 |
| Browser UI | 기능 흐름·console·network 통과, Mock partial 배지 표시 문제는 Frontend·Integration 04에 인계 |
| 합성 PostgreSQL plan | 20,000건·200 matches, 기본 ILIKE 19.258ms·LIKE 2.597ms·강제 GIN 2.030ms |
| actual Raw 오프라인 재생 | 온통청년 10·복지로 10 accepted, 추정 지역·조건 생성 없음 |
| actual Raw Runtime DB dry-run | 각 10건 insert 후보, rollback 후 검색·실행 row 0 |
| Source key 직접 참조 검사 | Backend 판정·projection·repository 0건 |

PostgreSQL plan은 18.4, `Korean_Korea.949`, `random_page_cost=4`,
`seq_page_cost=1`, `effective_cache_size=4GB`인 현재 로컬 전용 테스트 DB의 단일
측정이다. 응답 시간 보장이나 운영 index 사용 증거로 일반화하지 않는다.
기존 Starlette `httpx` deprecation warning 1건은 유지하며 PSF7 범위에서
패키지를 변경하지 않았다.

## 남은 작업

- 온통청년이 공개 `zipCd` code-to-name 표를 제공하지 않는 권위 공백은 남아
  있다. 전체 pagination에서 새 code가 나오면 exact crosswalk 외 값은
  `unmapped`로 보존하고 Source 문서가 확보되기 전 추정하지 않는다.
- PSF8에서 전체 Forest Gate, Git·비밀·Runtime 경계와 Data 02 DT2 인계를
  최종 검토해야 한다.
- Frontend 최종 디자인 또는 Integration 04에서 partial 배지를 제목 overflow
  밖에 배치하고 1280×720 목록·상세 Browser 시나리오를 다시 확인해야 한다.
- Backend 06은 실제 snapshot과 최종 filter·정렬·pagination을 포함한 plan에서
  기본 `ILIKE` Sequential Scan과 trigram GIN 미선택 위험을 다시 평가해야 한다.
- 기존 `R1-SEARCH-DATA-SEMANTICS` 인계 항목은 PSF0만으로 종료하지 않는다.
  PSF8 전체 Gate와 Data 02 DT2 소비 승인이 완료되어야 제거할 수 있다.
- Source 간 canonical deduplication, Backend 최종 가중치와 지역 crawler는
  Forest 범위 밖이며 변경하지 않는다.
