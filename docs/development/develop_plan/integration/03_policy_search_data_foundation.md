# Policy Search Data Foundation Forest 개발 계획

## 계획 정보

- 번호: Integration 03
- 담당 영역: Data·Backend 공동 통합
- 상태: in-progress
- 대상 Release: `v0.1.0`
- 권장 브랜치: `feature/database/policy-search-foundation`
- 기반 브랜치: `feature/data/release-dataset-bootstrap`
- 현재 Slice: PSF1 completed, PSF2 next
- 선행 Slice: Data 02 DT1
- 후속 Forest: Data 02 DT2~DT4, Backend 06, Frontend 04,
  Integration 04 Release 1 Acceptance
- 제안 ADR:
  [ADR 0001 정책 검색 데이터 기반](../../../architecture/decisions/0001-policy-search-data-foundation.md)

이 Forest는 사용자가 명시한 stacked 작업 흐름을 따른다.

```text
feature/data/release-dataset-bootstrap
  └─ feature/database/policy-search-foundation
       → 완료·검증 후 feature/data/release-dataset-bootstrap에 병합
       → Data 02 완료 후 develop PR
```

일반적인 작업 브랜치는 최신 `develop`에서 시작하지만, 이 Forest는 DT1
실데이터 근거에 직접 의존하고 Data 02의 DT2~DT4를 차단하는 공통 기반이므로
기반 브랜치와 merge target을 명시한 stacked 예외로 관리한다. Slice마다
브랜치를 추가하지 않는다.

## 목적

온통청년·복지로의 실제 key를 손실 없이 공통 검색 필드로 변환하고, 향후
지자체 API·공식 웹사이트 crawler가 추가돼도 같은 정책·지역·검색 계약을
사용할 수 있는 데이터베이스 기반을 만든다.

현재 구현의 `regions` JSONB 문자열 배열 exact match와 Source별 제한된
Extractor 매핑을 그대로 확장하지 않는다. 다음 세 책임을 분리한다.

```text
Source Raw·출처
  → Source Adapter와 공통 정책 계약
  → 행정구역·정책 적용 관계
  → 검색 projection과 query 판정
```

검색 요청은 PostgreSQL만 조회한다. 외부 API와 지역 웹사이트 수집은
Collector 실행 경계에 남기며 사용자 검색 시점에 호출하지 않는다.

## 범위

- 현재 Source key → 공통 검색 필드의 손실 목록과 권위 매핑 확정
- `summary`, 검색 키워드, 생애주기, 대상자와 지역 적용 범위 계약
- 전국·지역·미확인과 포함·제외를 표현하는 지역 규칙
- 버전·계층·별칭·폐지 이력을 보존하는 대한민국 행정구역 기준정보
- 정책과 행정구역의 관계형 저장 모델
- Korean text 검색을 위한 Source 중립 search projection
- 기존 Policy identity·Raw provenance·공개 목록·상세의 호환 경계
- Migration upgrade·downgrade·backfill과 populated DB 검증
- Importer transaction·idempotency와 검색 projection 동기화
- 전국·상위 지역·정확 지역·다른 지역·미확인 판정 primitive
- 향후 지역 Source Adapter가 따를 Fixture·계약 테스트
- Data·Backend·Frontend 소비 검토와 Data 02 DT2 인계

## 범위 밖

- Backend 자연어 문장 해석과 최종 검색 endpoint
- 관련도 최종 가중치와 사용자별 추천
- Frontend 검색·결과 UI 구현
- 실제 지자체 웹사이트 crawler
- 지자체 사이트별 HTML selector와 이용약관 조사
- Source 간 정책을 제목만으로 자동 병합하는 canonical deduplication
- Scheduler·worker·Docker·배포 구성
- 전체 Release snapshot 수집과 Runtime DB 최종 bootstrap

Backend 자연어 해석·최종 정렬은 Backend 06, Frontend 표시는 Frontend 04,
실제 지자체 Source 추가는 별도 Collector/Data Forest가 담당한다.

## 선행 조건

- Data 02 DT1의 두 Source 실응답과 품질 분포가 기록됨
- 현재 `NormalizedProgram` 1.0.0, Policy DB 매핑과 공개 API 계약 확인
- 실제 API key와 Runtime Raw가 Git에서 제외됨
- Migration 검증용 `_test` PostgreSQL DB가 Runtime DB와 분리됨
- Data·Backend·Frontend가 Schema·`null`·빈 배열·enum 영향 검토에 참여함
- 기존 Data 02 DT1 변경이 기반 브랜치에 커밋돼 작업 트리가 clean임

## 공통 설계 원칙

### 현재 계약과 미래 계약 구분

- `NormalizedProgram` 1.1.0 Schema·모델·Fixture는 PSF1의 현재 실행
  계약이고, DB·기존 API는 PSF3 전환 전까지 기존 31개 저장 필드를 유지한다.
- accepted ADR과 PSF1 완료는 데이터 계약을 확정한 것이며 PSF2 이후의
  지역 기준정보·DB·검색 구현 완료를 뜻하지 않는다.
- 새 계약은 additive Migration과 명시적 version 변경을 우선하며, 기존
  실데이터를 추정값으로 채우지 않는다.

### Source 중립성

- Backend 검색은 `plcyNm`, `servNm` 같은 Source key를 직접 참조하지 않는다.
- Source Adapter가 Raw key를 공통 필드로 변환하고 Raw와 provenance를
  재추적 가능하게 보존한다.
- `summary`는 이미 존재하는 공통 필드에 Source 설명을 채운다.
- 검색 전용 필드와 사용자 표시 필드를 섞어 표시 text를 오염시키지 않는다.

### 지역 불변식

정책의 지역 적용 범위는 다음 enum을 사용한다.

```text
nationwide
regional
unknown
```

- 누락된 지역은 자동으로 `nationwide`가 되지 않는다.
- `nationwide`는 Source 계약이나 정책 원문 근거가 있을 때만 사용한다.
- `regional`은 하나 이상의 승인된 포함 지역을 가져야 한다.
- 포함·제외 지역은 같은 정책에서 중복될 수 없다.
- 원본 `region_text`·Source code와 정규화 지역 code를 함께 보존한다.
- 지역 이름은 code 기준정보에서 파생하며 identity로 사용하지 않는다.
- 행정구역 개편은 기존 code를 덮어쓰지 않고 유효기간과 연결 관계로
  추적한다.

### 검색 판정

지역·연령·신청 상태는 이분법이 아니라 다음 3값을 사용한다.

```text
match
mismatch
unknown
```

- 명시적 `mismatch`는 기본 결과에서 제외한다.
- `unknown`은 결과를 조작해 match로 만들지 않고 감점·미확인 조건으로
  전달할 수 있다.
- `matched_conditions`와 `unverified_conditions`는 query별 결과이므로
  정책 원본 컬럼에 고정 저장하지 않는다.

### 호환성과 복구

- `(source_id, external_id)` source-scoped identity와 provenance를 유지한다.
- Source 간 canonical 병합은 근거 있는 별도 Forest 전까지 수행하지 않는다.
- 기존 `regions` 표시 배열은 호환 경계로 유지하되 관계형 지역 규칙에서
  파생 가능한 값으로 다룬다.
- Migration은 upgrade·downgrade와 populated DB backfill을 제공한다.
- 기존 row의 지역 근거가 없으면 `coverage_scope=unknown`으로 backfill한다.
- 정책, 지역 관계와 search projection은 한 Import transaction에서
  일관되게 갱신한다.

## PSF0 승인 목표 계약

### 공통 정책 필드

현재 계약의 `summary`를 실제로 채우고, 다음 검색 의미를
`NormalizedProgram` 1.1.0의 필수 필드로 구현한다.

| 필드 | 타입 | 누락 | 목적 |
| --- | --- | --- | --- |
| `keywords` | string 배열 | `[]` | Source 공식 키워드·중분류 검색 |
| `life_stages` | string 배열 | `[]` | 청년 등 생애주기 |
| `target_groups` | string 배열 | `[]` | 대상자 특성 |
| `coverage_scope` | enum | 필수 `unknown` | 전국·지역·미확인 구분 |
| `region_rules` | object 배열 | `[]` | 포함·제외 canonical 지역과 Source 근거·해석 상태 |

필드 이름과 1.1.0 version은 PSF0에서 승인했다. `region_rules` 원소의
`relation`, `resolution_status`, canonical scheme·code와 Source code·text
불변식은 ADR 0001을 따른다. PSF1은 이 결정을 실행 가능한 Schema·모델과
Fixture로 구현한다.
Frontend 표시가 필요 없는 내부 검색 필드는 공개 Policy DTO에 무조건
추가하지 않고 Backend 06 검색 응답 계약과 분리한다.

### 승인 Source 매핑

| Source | Raw key | 공통 의미 |
| --- | --- | --- |
| 온통청년 | `plcyExplnCn` | `summary` |
| 온통청년 | `mclsfNm`, `plcyKywdNm` | `keywords` |
| 온통청년 | `zipCd` | 지역 code 후보와 `region_text` |
| 온통청년 | `sprtTrgtMinAge`, `sprtTrgtMaxAge` | 연령 범위 |
| 복지로 | `servDgst`, `wlfareInfoOutlCn` | `summary` |
| 복지로 | `intrsThemaArray` | categories·keywords |
| 복지로 | `lifeArray` | `life_stages` |
| 복지로 | `trgterIndvdlArray` | `target_groups` |
| 복지로 | `tgtrDtlCn`, `slctCritCn` | `eligibility_text` |
| 복지로 | 지역 필드 없음 | `coverage_scope=unknown` |

`plcyAprvSttsCd`는 사용자 신청 가능 상태로 사용하지 않는다. 신청 상태는
신청기간 원문·구분과 수집 시점을 기준으로 별도 판정한다.

### 행정구역 기준정보

승인 테이블:

```text
administrative_regions
administrative_region_aliases
policy_region_rules
```

`administrative_regions`는 scheme, code, 이름, level, parent, 유효기간을
보존한다. 별칭은 광주처럼 문맥에 따라 모호할 수 있으므로 전역 unique
문자열로 단정하지 않는다. `policy_region_rules`는 include·exclude, 원본
code와 근거 text를 보존한다.

### 검색 projection

검색용 projection은 공개 Policy DTO와 분리한다.

```text
policy_search_documents
  policy_id
  title_text
  keyword_text
  summary_text
  eligibility_text
  support_text
  search_text
  projection_version
  updated_at
```

Korean text는 정규화된 문자열과 PostgreSQL `pg_trgm` 후보를 검토한다.
최종 점수와 자연어 parser는 Backend 06에서 확정하지만, 이 Forest는
Source별 핵심 text가 projection에서 유실되지 않고 transaction 안에서
동기화되는 것까지 보장한다.

## Slice 계획

### PSF0 - 현재 계약 감사와 ADR Gate

- 상태: completed (`2026-08-03`)
- 목적: 구현 전에 현재 손실·호환성·책임 경계를 확정한다.
- 선행 조건: Data 02 DT1 완료
- 수행:
  - Raw key → Extracted → Normalized → DB → API 필드 lineage 작성
  - 현재 `regions` JSONB exact match와 partial 비노출 영향 확인
  - Normalized version, 공개 DTO와 내부 projection 경계 결정
  - ADR의 Data·Backend·Frontend 소비 계약 검토
- 산출물: 승인 ADR, 필드 lineage, 호환성·Migration 영향표
- 완료 기준:
  - 추정값 금지와 `nationwide|regional|unknown` 의미 승인
  - 새 필드·테이블·공개 API 영향 분류
  - 구현을 막는 미확정 항목 0건

감사 결과와 확정 lineage·호환성·Migration 영향은
[ADR 0001](../../../architecture/decisions/0001-policy-search-data-foundation.md)과
[개발 기록](../../development_notes/integration/policy_search_data_foundation.md)에
기록한다. PSF0는 기존 계약을 구현 변경하지 않고 다음을 확정했다.

- `NormalizedProgram` 1.1.0의 새 필드는 `keywords`, `life_stages`,
  `target_groups`, `coverage_scope`, `region_rules`다.
- 1.0.0은 명시적 compatibility adapter로 안전한 빈 값·`unknown`만 보완하며
  기존 DB row의 version을 Migration만으로 바꾸지 않는다.
- 기존 목록·상세 DTO의 필드 집합과 partial opt-in은 유지하고 새 검색
  projection·3값 판정·검색 이유는 별도 내부 및 검색 응답 계약으로 둔다.
- `partial`은 검색 부적합과 동의어가 아니다. 새 검색은 valid·partial을
  후보로 삼고 `mismatch`와 `unknown`을 구분한다.

### PSF1 - 검색 데이터 계약과 Fixture

- 상태: completed (`2026-08-03`)
- 목적: Source와 DB가 공유할 실행 가능한 계약을 고정한다.
- 선행 조건: PSF0 Gate
- 수행:
  - Normalized Schema version과 Python 모델 갱신
  - summary·keywords·life stages·target groups·coverage·region code 규칙
  - `null`, 빈 배열, enum과 포함·제외 불변식 구현
  - 전국·지역·미확인·상위·제외·폐지 code Fixture 작성
  - canonical Seed와 Data·Backend·Frontend 소비 테스트 갱신
- 산출물: JSON Schema, 모델, Fixture·Seed와 계약 문서
- 완료 기준:
  - Schema·모델·Fixture 필드 집합과 품질 판정 일치
  - Backend 저장 후보와 Frontend 소비 영향 공동 확인
  - 기존 1.0.0 입력 호환 또는 명시적 migration 경계 검증

PSF1은 1.1.0의 36개 필드 Schema·Python 모델과 exact 1.0.0 compatibility
adapter를 구현했다. 전국·지역·미확인·상위·정확·제외·동명이인·폐지 code
경계를 합성 Fixture로 고정하고 canonical Seed를 1.1.0으로 재생성했다.
PSF3 Migration 전에는 새 검색 값이 모두 안전한 기본값인 입력만 기존 31개
ORM에 저장하며, 의미 있는 검색 값은 `search_storage_not_ready`로 거부한다.
Frontend는 기존 목록·상세 DTO의 필드 집합을 유지하고 version union만
소비한다.

### PSF2 - 행정구역 기준정보

- 목적: 이름 추정이 아닌 versioned code와 계층으로 지역을 판정한다.
- 선행 조건: PSF1 계약
- 수행:
  - 공식 행정구역 자료의 출처·버전·라이선스 확인
  - region·alias·parent·validity seed 생성 절차
  - 천안시→충청남도→대한민국 ancestor 탐색
  - 동명이인, 축약어, 폐지·분할·집계 code 처리
  - Source code 미매핑을 warning과 `unknown`으로 유지
- 산출물: 재현 가능한 지역 기준정보와 생성·검증 절차
- 완료 기준:
  - 코드 수·계층·고아 parent·중복·순환 검증
  - 천안·충남·전국과 모호한 별칭 Fixture 통과
  - 권위 없는 앞자리 추정 없음

### PSF3 - PostgreSQL Migration과 ORM

- 목적: 공통 정책, 지역 관계와 search projection을 손실 없이 저장한다.
- 선행 조건: PSF1·PSF2
- 수행:
  - coverage enum·정책 검색 필드·지역 테이블·관계 테이블 추가
  - search projection과 `pg_trgm` extension·index 후보 구현
  - FK, unique, include/exclude 충돌과 coverage 불변식 제약
  - 기존 row `unknown` backfill
  - upgrade·downgrade와 ORM·Schema field set 갱신
- 산출물: Alembic revision, ORM과 DB 매핑 문서
- 완료 기준:
  - 빈 DB와 기존 데이터 DB에서 upgrade 성공
  - downgrade 후 기존 계약 복구
  - PostgreSQL constraint·JSON/관계·timezone 왕복 통과
  - Runtime DB와 `_test` DB 경계 유지

### PSF4 - Source Adapter와 정규화

- 목적: 실제 Source key를 공통 검색 필드로 손실 없이 옮긴다.
- 선행 조건: PSF1
- 수행:
  - 온통청년 summary·중분류·키워드·지역 code 매핑
  - 복지로 summary·개요·생애주기·대상자 매핑
  - 명시 근거 없는 복지로 지역은 `unknown` 유지
  - 향후 지역 HTML Source가 따를 Adapter contract와 합성 Fixture
  - Raw source field·provenance 보존 회귀
- 산출물: Extractor·Normalizer와 Source별 매핑 테스트
- 완료 기준:
  - 검색 대상 key의 Raw→공통 필드 lineage 100% 설명
  - Source key 누락·빈 값·다중 값 회귀 통과
  - 사용자 표시 text에 검색용 합성 문자열을 섞지 않음

### PSF5 - Import transaction과 projection 동기화

- 목적: Policy·지역 규칙·검색 문서를 하나의 원자적 적재 단위로 만든다.
- 선행 조건: PSF3·PSF4
- 수행:
  - 신규 insert·update·unchanged와 projection version 처리
  - 지역 관계 교체 중 중간 상태 비노출
  - 실패 rollback과 CollectionRun 집계
  - 같은 입력 재실행 idempotency
  - projection 재생성 명령 또는 서비스 경계
- 산출물: Importer·Repository 구현과 통합 테스트
- 완료 기준:
  - 동일 입력 재실행 시 중복 row·관계·projection 없음
  - 부분 실패 시 Policy·지역·projection 전부 rollback
  - source identity·created_at·updated_at 기존 불변식 유지

### PSF6 - 지역·조건 판정 primitive

- 목적: Backend 06이 사용할 결정적이고 테스트 가능한 판정 기반을 제공한다.
- 선행 조건: PSF2·PSF3·PSF5
- 수행:
  - exact·ancestor·nationwide·unknown·exclude 지역 판정
  - 연령·상태의 `match|mismatch|unknown` 공통 결과
  - 지역 alias 해석과 모호성 반환
  - 검색 projection field별 match 근거
  - 최종 관련도 가중치는 Backend 06으로 인계
- 산출물: Repository/service primitive와 경계 테스트
- 완료 기준:
  - 천안 query에 천안·충남·전국 match
  - 아산 regional policy mismatch
  - 지역 미상 중앙정부 policy unknown
  - 명시적 exclude가 ancestor include보다 우선

### PSF7 - 소비 호환·성능·실데이터 재생

- 목적: 새 기반이 기존 API와 실제 Runtime 흐름을 깨뜨리지 않는지 검증한다.
- 선행 조건: PSF1~PSF6
- 수행:
  - 기존 목록·상세 DTO와 Frontend 타입 호환 확인
  - Backend 06 검색 응답에 필요한 내부 필드 인계
  - 합성 대량 데이터 `EXPLAIN (ANALYZE, BUFFERS)`와 index 검토
  - DT1 Runtime Raw 오프라인 재처리
  - actual partial·unknown 분포와 누락 사유 재집계
- 산출물: 소비 검토, query plan, 실제 재생 결과
- 완료 기준:
  - 기존 목록·상세 회귀 통과
  - 새 검색 primitive가 Source key를 직접 참조하지 않음
  - 성능 결과와 남은 index 위험 기록
  - actual Raw 재생에서 추정값 생성 없음

### PSF8 - Gate와 Data 02 인계

- 목적: 새 기반을 현재 Data Forest에 병합 가능한 상태로 만든다.
- 선행 조건: PSF0~PSF7
- 수행:
  - 전체 Data·Backend·PostgreSQL·문서 검증
  - Schema·Fixture·Seed·DB·API 영향 문서 동기화
  - Runtime Raw·DB·비밀 Git 비추적 확인
  - Data·Backend·Frontend 검토 증거와 남은 위험 정리
  - 기반 브랜치 merge 전 staged diff·커밋·PR 범위 검토
- 산출물: 완료 개발 기록과 Data 02 DT2 인계
- 완료 기준:
  - Forest 완료 기준 전부 충족
  - `R1-SEARCH-DATA-SEMANTICS` 공동 확인 종료 가능
  - `feature/data/release-dataset-bootstrap` 병합 후 DT2 재개 가능

## Gate와 의존 순서

```text
PSF0 ADR·계약 경계
  → PSF1 실행 계약 ─┬→ PSF2 지역 기준정보 ─┐
                    └→ PSF4 Source 매핑 ───┤
PSF2 + PSF1 → PSF3 DB·Migration ──────────┤
PSF3 + PSF4 → PSF5 transaction·projection ┤
PSF2 + PSF5 → PSF6 판정 primitive ────────┤
                                     → PSF7 소비·성능·실데이터
                                     → PSF8 인계·병합
                                     → Data 02 DT2
```

병렬 가능한 작업:

- PSF2 지역 기준정보 조사와 PSF4 Source mapping 테스트
- PSF3 DB 모델 초안과 PSF4 Extractor 구현은 PSF1 승인 후 병렬
- Backend 06 테스트 골격과 Frontend 04 UI prototype은 계약 확정 전까지 병렬

기다려야 하는 작업:

- Migration 확정은 PSF1·PSF2 계약 뒤
- Importer transaction은 PSF3·PSF4 뒤
- 지역 판정은 versioned region table과 policy relation 뒤
- Backend 06 최종 query·정렬은 PSF6 인계 뒤
- Data 02 실제 bootstrap은 PSF5·PSF7 뒤

## 검증 계획

### Data

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
```

### Backend·PostgreSQL

```powershell
.\.venv\Scripts\python.exe -B -m pytest backend/tests tests/integration -q
```

PostgreSQL 통합 테스트는 `_test`로 끝나는 전용 DB에서만 실행한다.
Runtime DB에는 Migration과 승인된 실데이터 절차만 적용한다.

### Migration

- 빈 PostgreSQL DB upgrade → downgrade → upgrade
- 현재 revision과 기존 Policy row가 있는 DB upgrade
- 신규 constraint·FK·enum·index 확인
- downgrade 후 기존 Policy 조회·API 회귀

### 검색 기반

- 전국·상위·정확·다른 지역·미확인·exclude
- 27세의 범위 match·mismatch·unknown
- open·closed·scheduled·unknown
- 한국어 공백·축약·동의어 search projection
- actual DT1 Raw의 오프라인 재생
- 합성 규모 query plan과 buffer·실행 시간 기록

### 문서·Git

```powershell
python scripts/validate_docs.py
git diff --check
git status --short
```

실행하지 않은 테스트와 skip은 성공으로 기록하지 않는다.

## Forest 완료 기준

- 실제 Source 검색 key가 공통 필드와 search projection에 손실 없이 연결됨
- `nationwide|regional|unknown`과 include·exclude 불변식이 실행 가능함
- versioned 행정구역 code·계층·별칭과 정책 관계가 PostgreSQL에 존재함
- 천안 query가 천안·충남·전국·미상·타 지역을 구분할 수 있음
- 기존 Policy identity·provenance·목록·상세 호환 경계가 검증됨
- 빈 DB와 populated DB Migration·downgrade가 검증됨
- Importer transaction·idempotency·rollback이 Policy·지역·projection 전체에
  적용됨
- actual DT1 Raw 재생과 합성 경계 Fixture가 통과함
- Schema·Fixture·Seed·DB·API·Frontend 영향 문서가 동기화됨
- 비밀키, Runtime Raw와 DB 파일이 Git에 포함되지 않음
- Data·Backend·Frontend 공동 소비 검토 증거가 있음

## 위험과 미확정 사항

- 온통청년 `zipCd`의 권위 있는 최신 행정구역 code table은 아직 확보하지
  않았다.
- 지역 code의 집계·폐지·분할 관계를 잘못 일반화하면 검색 오탐이 생긴다.
- PostgreSQL `pg_trgm` extension 사용 가능 여부를 로컬·배포 환경에서
  확인해야 한다.
- 기존 공개 DTO의 필드 집합은 유지한다. 전환 기간의 `schema_version`은
  1.0.0·1.1.0을 모두 허용하고 새 검색 전용 필드는 Backend 06 응답과
  Frontend 04 소비 계약으로 분리하기로 PSF0에서 결정했다.
- Source 간 같은 정책의 canonical 병합은 이 Forest에서 해결하지 않는다.
- “완벽한 미래 예측”보다 검증된 Source 근거·version·Migration 가능성을
  우선한다. 알 수 없는 값은 `unknown`으로 보존한다.
- 이 stacked 브랜치가 장기화되면 `develop`과 충돌할 수 있으므로 PSF8 전에
  기반 브랜치와 `develop` 차이를 검토한다.

## 관련 문서

- [Data 02 Release Dataset Bootstrap](../data/02_release_dataset_bootstrap.md)
- [전체 Forest 로드맵](../forest_roadmap.md)
- [Release와 Milestone 계획](../release_roadmap.md)
- [3주차 상세 실행 계획](../../weekly_plan/week_03_release_1.md)
- [3주차 Data·Team Leader 계획](../../weekly_plan/week_03_data_team_leader.md)
- [데이터 Schema](../../../data/data_schema.md)
- [정규화 규칙](../../../data/normalization_rules.md)
- [Source Profile](../../../data/source_profiles.md)
- [Policy DB 매핑](../../../architecture/policy_database_mapping.md)
- [Policy API](../../../api/policies.md)
- [브랜치 전략](../../../governance/branch_strategy.md)
