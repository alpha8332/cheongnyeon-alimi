# 데이터 수집 정책

## 적용 범위

이 문서는 공식 API, 공개 파일과 웹 Source를 안전하고 재현 가능하게 수집하는
현재 공통 원칙을 정의한다. 실제 실행 명령과 Source별 옵션은
[Collector 운영](../operations/collector.md)을 따른다.

## HTTP 경계

공통 HTTP client의 기본값은 timeout 10초, 최대 재시도 3회, 요청 시작 간
최소 간격 1초다. Source의 더 엄격한 공식 제한이 있으면 그 값을 우선한다.

- timeout·전송 오류와 5xx만 제한적으로 재시도한다.
- 401·403은 인증, 429는 호출량, 그 밖의 4xx는 요청 오류로 즉시 중단한다.
- 5xx는 지수 backoff를 적용한다.
- redirect를 자동 추적하지 않아 인증 query가 다른 origin으로 전달되지 않게
  한다.
- User-Agent, content type과 응답 형식을 검증한다.
- 오류에는 Source와 안전한 오류 유형만 남기고 response body·query 값과 하위
  예외 메시지를 포함하지 않는다.

## 인증정보

API key는 `YOUTHCENTER_API_KEY`, `BOKJIRO_API_KEY` 환경변수로만 주입한다.
실제 값은 GitHub Environment secret 또는 Git에서 제외된 로컬 환경에 둔다.

- Frontend bundle, Fixture, 문서, CollectionRun과 구조화 로그에 저장하지 않는다.
- URL을 기록할 때 user information과 query 값을 전부 redaction한다.
- key가 없으면 명확한 설정 오류를 반환한다.
- 사용자 PC의 공개 dataset 설치·검색은 API key 유무와 독립적이다.

## Raw 보존

`RawPolicyDocument`는 source ID, 외부 identity, 문서 역할, source URL, 수집
시각, content type·format, 원본 byte, byte 수와 SHA-256을 함께 보존한다.

- 원문을 정규화 값으로 덮어쓰지 않는다.
- hash·byte 수가 payload와 다르면 저장·로드하지 않는다.
- 실제 Raw는 Runtime Volume에만 두고 Git과 공개 dataset에서 제외한다.
- 목록 item과 상세는 부모·identity 관계를 검증한다.
- source URL은 credential query가 없는 안전한 형태만 보존한다.

## 웹 수집

- 공개 목록과 필요한 상세만 allowlist로 요청한다.
- 동시성과 요청 간격을 Source별로 제한한다.
- 로그인·회원·신청·CAPTCHA·접근 통제를 우회하지 않는다.
- 첨부, 이미지와 개인 연락처를 수집 대상에서 제외한다.
- selector·locator는 Source 모듈에 격리하고 drift를 빈 값으로 가장하지 않는다.
- Browser capture는 정적 HTML과 공개 요청으로 필요한 필드를 얻을 수 없을 때만
  제한적으로 사용한다.

명시적 재배포 허가가 없는 웹 Source의 Raw와 normalized 원문은 중앙 Runtime과
관리자 검토 범위에만 두고 공개 artifact에서 제외한다.

## 추출·정규화·검증

Extractor는 저장된 Raw를 외부 재호출 없이 처리한다. Normalizer는 날짜·지역·
연령·분야를 공통 형식으로 바꾸고, Validator는 `valid`, `partial`, `invalid`를
판정한다.

- 선택 필드 누락으로 전체 수집을 중단하지 않는다.
- 필드 누락과 빈 문자열·빈 element를 가능한 범위에서 구분한다.
- 근거 없는 지역·연령·상태를 만들지 않는다.
- invalid는 정상 정책과 분리하고 DB batch admission을 fail-closed한다.
- 동일 `(source_id, external_id)`는 멱등 upsert한다.

## CollectionRun과 queue

관리자 수동 실행과 scheduler는 PostgreSQL에 `queued` CollectionRun을 만든 뒤
Redis queue에 publish한다. Celery worker가 수집·정규화·import를 수행한다.

- Source별 active run unique 조건과 DB lock으로 중복 실행을 막는다.
- publish 실패, worker 실패와 stale 상태를 구분한다.
- raw payload나 secret 대신 삽입·갱신·실패 집계와 안전한 오류 유형만 남긴다.
- scheduler는 기본 비활성화이며 중앙 운영자가 승인한 Source만 실행한다.

## 생명주기

미발견 정책의 `inactive_at` 전이는 완전 snapshot, 검증과 DB commit이 모두
성공한 실행에서만 허용한다. 일부 limit, invalid·rejected·failed와 미완료
checkpoint에서는 기존 정책 상태를 유지한다. 재등장한 identity는 inactive를
해제한다.

자세한 규칙은 [정책 생명주기](policy_lifecycle.md)를 따른다.

## 공개 dataset 분리

수집 성공은 사용자 공개를 의미하지 않는다. 공개 후보는 별도의 Source
allowlist, 필드 allowlist, 개인정보·비밀 pattern, lifecycle, row·hash와 격리
DB projection Gate를 통과해야 한다.

수동·정기 수집 결과는 중앙 promotion 전까지 공개 membership에 포함하지 않는다.
새 dataset 발행이 실패하면 이전 `dataset-latest`를 유지한다.

## Git 포함 경계

| 데이터 | Git |
| --- | --- |
| JSON Schema·합성 Fixture·합성 Seed | 포함 |
| 공식 기준정보를 변환한 행정구역 Seed | 포함 |
| 실제 API·HTML Raw, rejected, checkpoint | 제외 |
| PostgreSQL dump·Volume | 제외 |
| 공개 normalized artifact | Git이 아닌 versioned GitHub Release |

## 검증

- 단위 테스트는 외부 요청 대신 합성 JSON·XML·HTML Fixture를 사용한다.
- 실제 API 호출은 명시적 중앙 통합 실행으로 분리한다.
- 인증 누락, 빈 응답, 4xx·5xx, timeout, 중복 identity와 drift를 검증한다.
- 공개 후보는 manifest 검증과 격리 DB 설치·검색 smoke를 추가로 수행한다.

Source·저장 범위·개인정보·이용 조건이 바뀌면 이 문서,
[데이터 소스](data_sources.md), Collector 테스트, 운영 문서와 공개 Source
contract를 함께 갱신한다.
