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

W4-G0에서 승인한 천안청년센터 이음 공지 Source 한 곳을 기존 Raw 계약에
연결한다. DTL4-3A에서는 호출 범위와 속도를 코드로 제한하고, 합성 HTML로
목록·상세 구조와 실패 경계를 검증한 뒤 실제 승인 표본을 Raw와 Source 전용
추출 결과까지 확인한다.

## Forest 범위

- Source ID `cheonan-youthcenter-web`, 외부 identity `notice:674`
- 승인 목록 1회와 승인 상세 1건만 허용하는 동기 Collector
- 최소 요청 시작 간격 2초와 pagination·외부 URL 차단
- 합성 목록·상세·선택 필드 누락·selector drift Fixture
- Runtime HTML Raw와 Source 전용 Extractor
- 공개 시설 대표전화·공식 문의 채널 보존
- 개인 휴대전화·개인 이메일·성명 구조화 추출 제외

정규화, 공통 Policy 필드 승격, Runtime replay, PostgreSQL 적재와 API 노출은
DTL4-3B 이후 범위다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| DTL4-3A | 완료 | 제한 호출, 합성 HTML, Collector·Extractor와 승인 표본 actual 검증 |
| DTL4-3B | 대기 | 정규화·검증·PostgreSQL 적재와 lineage 종단 검증 |

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

## 주요 변경 파일

- `collectors/cheonan_youthcenter.py`
- `collectors/__init__.py`
- `data/fixtures/html/cheonan-youthcenter-web/*.html`
- `tests/test_cheonan_youthcenter_web.py`
- `docs/data/data_sources.md`
- `docs/data/collection_policy.md`
- `docs/data/source_profiles.md`
- `docs/development/develop_plan/data/04_public_https_policy_ingestion.md`

## 설계 결정

- 범용 crawler를 만들지 않고 승인 Source·identity를 코드 allowlist로 고정한다.
- 실제 HTML은 ignored Runtime Raw에만 두고 Git에는 검토한 합성 Fixture만 둔다.
- 선택 필드 누락은 `null` 또는 빈 목록으로 보존하지만 필수 selector drift는
  정상 데이터로 처리하지 않는다.
- 시설 대표 연락처와 개인 연락처를 구분한다. 기관 정보는 Source evidence로
  보존하고 개인 연락처는 승격하지 않는다.
- 다중 process 간 전역 pacing lock은 기존 Collector 실행 모델에 없으므로
  이번 Slice에서 별도 scheduler·lock 구조를 추가하지 않는다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| Source 전용 단위·통합 테스트 | 통과: 11 tests |
| actual 제한 Collector | 통과: 요청 2회, Raw 3건 |
| actual Source Extractor | 통과: identity·section·기관 연락처·provenance 확인 |
| 전체 Data 회귀 | 통과: 150 tests |
| Backend 영향 회귀 | 통과: 110 passed, 15 skipped, 기존 deprecation warnings 2건 |
| Fixture 재현성 | 통과: managed files 14개 일치 |
| 문서 검증 | 통과: `python scripts/validate_docs.py` |
| diff 공백 검사 | 통과: `git diff --check` |

## 남은 작업

- DTL4-3B에서 Runtime Raw replay를 공통 정규화·검증·품질 판정에 연결한다.
- 동일 입력 재실행의 created·unchanged·updated 판정과 PostgreSQL 적재를
  actual로 검증한다.
- 시설 대표 연락처를 사용자 화면에 노출하려면 DTL4-4 또는 Backend 소비
  계약에서 공통 Policy/API 필드와 표시 기준을 별도로 승인해야 한다.
- 여러 Collector process를 동시에 실행할 운영 요구가 생기면 process-local
  pacing만으로는 요청 간격을 보장하지 못하므로 scheduler 직렬화나 공유 lock을
  별도 결정해야 한다.
