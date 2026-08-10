# Public HTTPS Policy Ingestion Forest 개발 기록

## 작업 정보

- 기간: `2026-08-10`~
- 담당 영역: Data & Team Leader
- 상태: in-progress
- 브랜치: `feature/data/public-web-policy-source`
- 병합 대상: `develop`
- 시작 기준: `7294802` (`feat(data): persist recurrent quality counts`)
- 계획: [Data 04 Public HTTPS Policy Ingestion Forest](../../develop_plan/data/04_public_https_policy_ingestion.md)

## 목적

W4-G0에서 승인한 천안청년센터 이음 공지 Source 한 곳을 기존 Raw 계약과
Runtime replay·PostgreSQL에 연결한다. DTL4-3A에서는 호출 안전과 Extractor를,
DTL4-3B에서는 정규화·품질·반복 판정과 정책 상세 API까지 검증한다.

## Forest 범위

- Source ID `cheonan-youthcenter-web`, 외부 identity `notice:674`
- 승인 목록 1회와 승인 상세 1건만 허용하는 동기 Collector
- 최소 요청 시작 간격 2초와 pagination·외부 URL 차단
- 합성 목록·상세·선택 필드 누락·selector drift Fixture
- Runtime HTML Raw와 Source 전용 Extractor
- 공개 시설 대표전화·공식 문의 채널 보존
- 개인 휴대전화·개인 이메일·성명 구조화 추출 제외

Source 전용 제외조건·필요서류·기관 연락처의 공통 Policy/API 필드 승격은
Integration 08 DTL4-4 이후 범위다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| DTL4-3A | 완료 | 제한 호출, 합성 HTML, Collector·Extractor와 승인 표본 actual 검증 |
| DTL4-3B | 완료 | Runtime replay·정규화·PostgreSQL 반복 판정과 partial 정책 API actual 검증 |

## 구현 내용

### 승인 Source Adapter

- 공통 `HttpClient`를 사용하되 Source 설정의 요청 간격을 최소 2초로
  올리고, 한 실행에서 목록 1회와 상세 최대 1회만 순차 호출한다.
- 고정된 board 경로와 `bo_table=notice`, 승인 `wr_id=674`만 허용한다.
  page 확대, 추가 query, 외부 링크, 신청·로그인·첨부·이미지 URL은 따라가지
  않는다.
- 목록과 상세 DOM을 모두 파싱한 뒤 Raw를 저장한다. 필수 selector가 바뀌면
  일부 Raw를 남기지 않고 selector drift 오류로 종료한다.
- Raw `source_url`은 기존 계약에 따라 query가 없는 board URL로 저장하고,
  Source 전용 canonical URL은 승인 identity에서 다시 구성한다.

### HTML Extractor와 연락처 경계

- Python 표준 `HTMLParser`로 `#bo_list`, `#bo_v`, `#bo_v_title`,
  `#bo_v_info`, `#bo_v_con`을 읽고 title, summary, 신청기간, 대상, 지원 내용,
  신청 방법과 Source 전용 section evidence를 만든다.
- 공개 시설 대표전화와 공식 문의 채널은 사용자가 실제 문의에 필요한 기관
  정보로 판단해 Source 전용 `institutional_contact`에 보존한다.
- `010` 등 개인 휴대전화와 개인 이메일·성명은 구조화 추출하지 않는다.
  공통 Policy/API 연락처 계약은 아직 없으므로 이번 Slice에서 새 필드를
  임의로 만들지 않았다.
- 실제 상세 HTML에 void element인 `img`의 명시적 `</img>`가 있어 최초 actual
  파싱은 selector drift로 안전하게 실패했고 Raw는 저장되지 않았다. void
  element 종료 태그가 본문 컨테이너를 닫지 않도록 파서를 수정한 뒤 회귀
  Fixture를 추가했다.

### 실제 승인 표본 확인

`2026-08-10` 차수 시점에 목록과 공지 674번은 익명 HTTPS `200` 응답과 UTF-8
HTML을 반환했다. `/robots.txt`는 directive가 없는 `404` HTML을 반환했다.
최종 Collector 실행은 요청 2회, 선택 항목 1건, 상세 1건, Runtime Raw 3건을
생성했다. Extractor는 외부 identity 1건, section 7개, 시설 대표전화 1개,
공식 문의 채널 1개와 provenance 3개를 만들었다. 실제 연락처 값과 원문 HTML은
문서·테스트 출력·Git에 기록하지 않았다.

preflight와 parser 원인 진단 중 승인 목록·상세에 제한한 추가 GET이 있었다.
pagination·bulk·로그인·신청·첨부·이미지는 요청하지 않았지만, 별도 진단
process끼리는 공통 `HttpClient`의 process-local 2초 pacing 상태를 공유하지
않았다. 이후 실제 요청은 DTL4-3B 종단 검증 전까지 중단한다.

### DTL4-3B Runtime replay와 정규화

- `collectors.runtime`의 지원 Source와 Extractor registry에
  `cheonan-youthcenter-web`을 추가해 저장 HTML Raw를 외부 요청 없이 재생한다.
- 실제 Raw 3건은 정책 1건, `partial` 1건, invalid 0건으로 정규화됐다. 정책명,
  기관, 지원 내용, 신청 방법, 대상과 provenance 3건을 기존 공통 계약으로
  유지했다.
- 한글 표기의 신청기간은 현재 공통 날짜 파서가 구조화하지 않으며
  `unparsed_application_period` warning과 신청 상태 `unknown`을 유지한다.
  제목·게시일·본문 기간 충돌을 근거 없이 `closed`로 보정하지 않았다.
- Source 전용 section의 제외조건·필요서류와 `institutional_contact`는
  `ExtractedPolicy.extra`와 Raw에 존재하지만 현재 `NormalizedProgram`이
  `extra`를 저장하지 않는다. DTL4-4 공동 Schema 승인 전에는 공통
  `required_conditions`·`excluded_conditions` 또는 API 연락처로 승격하지
  않는다.

### PostgreSQL 반복·실패·API 검증

전용 `cheongnyeon_alimi_test`에 Alembic head를 적용하고 actual Raw를 두 번
적재했다.

- 첫 실행: Raw 3, extracted 1, partial 1, inserted 1, run ID
  `3c3400f9-74ad-41f7-8933-e0c807fdc1f3`
- 동일 Raw 재실행: Raw 3, extracted 1, partial 1, unchanged 1, run ID
  `f2777803-87ce-4d15-a912-3a572cec52dc`
- DB 결과: 정책 row 1, CollectionRun 2, provenance 3, 중복·실패 0
- 정책 상세 API: 기본 partial 비노출 `404`, `include_partial=true`에서 `200`,
  공개 DTO provenance 비노출

실제 공개 페이지를 변경할 수 없으므로 `updated`와 selector drift 실패는 합성
HTML PostgreSQL 통합 테스트로 검증했다. 지원 내용 변경은 `updated=1`이었고,
그 뒤 최신 batch의 selector drift가 Runtime replay를 실패시켜도 기존 정책
row와 변경 provenance는 유지됐다. 검증 뒤 테스트 DB는 Alembic `base`로
정리했다.

## 주요 변경 파일

- `collectors/cheonan_youthcenter.py`
- `collectors/runtime.py`
- `collectors/__init__.py`
- `data/fixtures/html/cheonan-youthcenter-web/*.html`
- `tests/test_cheonan_youthcenter_web.py`
- `tests/test_runtime_replay.py`
- `tests/integration/test_cheonan_web_runtime_to_database.py`
- `docs/data/data_sources.md`
- `docs/data/collection_policy.md`
- `docs/data/source_profiles.md`
- `docs/development/develop_plan/data/04_public_https_policy_ingestion.md`
- `docs/operations/collector.md`

## 설계 결정

- 범용 crawler를 만들지 않고 승인 Source·identity를 코드 allowlist로 고정한다.
- 실제 HTML은 ignored Runtime Raw에만 두고 Git에는 검토한 합성 Fixture만 둔다.
- 선택 필드 누락은 `null` 또는 빈 목록으로 보존하지만 필수 selector drift는
  정상 데이터로 처리하지 않는다.
- 시설 대표 연락처와 개인 연락처를 구분한다. 기관 정보는 Source evidence로
  보존하고 개인 연락처는 승격하지 않는다.
- 다중 process 간 전역 pacing lock은 기존 Collector 실행 모델에 없으므로
  이번 Slice에서 별도 scheduler·lock 구조를 추가하지 않는다.
- business 필드가 같고 수집 시각·provenance만 달라진 재실행은 기존 importer
  계약에 따라 `unchanged`다. business 값이 달라질 때만 `updated`로 판정하고
  최신 수집 metadata를 함께 저장한다.
- partial 정책은 기존 공개 API 계약에 따라 기본 목록·상세에서 숨기고
  명시적인 `include_partial=true`에서만 제공한다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| Source 전용 단위·통합 테스트 | 통과: 11 tests |
| actual 제한 Collector | 통과: 요청 2회, Raw 3건 |
| actual Source Extractor | 통과: identity·section·기관 연락처·provenance 확인 |
| DTL4-3B 단위 회귀 | 통과: 23 tests |
| 웹 Source PostgreSQL 통합 | 통과: inserted·unchanged·updated·drift 보존 1 test |
| actual PostgreSQL·CollectionRun | 통과: inserted 1, unchanged 1, 정책 1, run 2 |
| actual 정책 상세 API | 통과: 기본 404, partial 명시 조회 200 |
| 전체 Data 회귀 | 통과: 152 tests |
| Backend PostgreSQL 전체 회귀 | 통과: 125 tests, 기존 deprecation warnings 2건 |
| 저장소 PostgreSQL 통합 전체 | 통과: 6 tests, 기존 warning 1건 |
| Fixture 재현성 | 통과: managed files 14개 일치 |
| 문서 검증 | 통과: `python scripts/validate_docs.py` |
| diff 공백 검사 | 통과: `git diff --check` |

## 남은 작업

- Source 전용 제외조건·필요서류와 시설 대표 연락처를 사용자 화면에 노출하려면
  DTL4-4 또는 Backend 소비
  계약에서 공통 Policy/API 필드와 표시 기준을 별도로 승인해야 한다.
- 여러 Collector process를 동시에 실행할 운영 요구가 생기면 process-local
  pacing만으로는 요청 간격을 보장하지 못하므로 scheduler 직렬화나 공유 lock을
  별도 결정해야 한다.
