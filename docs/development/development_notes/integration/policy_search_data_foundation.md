# Policy Search Data Foundation Forest 개발 기록

## 작업 정보

- 시작일: 2026-08-03
- 상태: in-progress
- 영역: Data·Backend 공동 통합, Frontend 소비 검토, Team Leader Gate
- 브랜치: `feature/database/policy-search-foundation`
- 기반 브랜치: `feature/data/release-dataset-bootstrap`
- 관련 계획:
  [`03_policy_search_data_foundation.md`](../../develop_plan/integration/03_policy_search_data_foundation.md)
- 현재 Slice: PSF0 completed, PSF1 next

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
| PSF1 | pending | Normalized 1.1.0 실행 계약·legacy adapter·Fixture |
| PSF2 | pending | 행정구역 기준정보 |
| PSF3 | pending | PostgreSQL Migration·ORM |
| PSF4 | pending | Source Adapter·정규화 |
| PSF5 | pending | Import transaction·projection 동기화 |
| PSF6 | pending | 지역·조건 판정 primitive |
| PSF7 | pending | 소비 호환·성능·actual Raw 재생 |
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

## 주요 변경 파일

- `docs/architecture/decisions/0001-policy-search-data-foundation.md`
- `docs/architecture/decisions/README.md`
- `docs/development/develop_plan/integration/03_policy_search_data_foundation.md`
- `docs/development/develop_plan/README.md`
- `docs/development/develop_plan/forest_roadmap.md`
- `docs/development/development_notes/integration/policy_search_data_foundation.md`
- `docs/development/development_notes/README.md`
- `docs/index.md`

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

## 남은 작업

- PSF1에서 승인된 1.1.0 Schema·Python 모델·legacy adapter와 경계 Fixture를
  구현하고 Data·Backend·Frontend 소비 테스트를 갱신한다.
- PSF2에서 온통청년 `zipCd`를 해석할 권위 있는 행정구역 scheme·version과
  라이선스를 확보해야 한다. 확보 전에는 code를 매핑하지 않는다.
- PSF3에서 `pg_trgm` 사용 가능 여부와 cross-row 지역 불변식의 PostgreSQL
  구현 방식을 실제 `_test` DB에서 검증한다.
- 기존 `R1-SEARCH-DATA-SEMANTICS` 인계 항목은 PSF0만으로 종료하지 않는다.
  PSF8 전체 Gate와 Data 02 DT2 소비 승인이 완료되어야 제거할 수 있다.
- Source 간 canonical deduplication, Backend 최종 가중치와 지역 crawler는
  Forest 범위 밖이며 변경하지 않는다.
