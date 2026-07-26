# 데이터 수집 정책

## 문서 상태

- 상태: 기준선
- 현재 구현 상태: 공통 HTTP·실행 기반 구현, 소스 Collector 미구현

이 문서는 외부 정책 데이터를 안전하고 재현 가능하게 수집하기 위한 공통
원칙을 정의한다.

## 수집 범위 관리

수집 소스, 검증 건수, 자동화 수준과 제외 범위는 Forest 계획에서 정한다.
현재 Data Pipeline Forest의 실행 범위는
[개발 계획](../development/develop_plan/data/01_data_pipeline.md)을 따른다.
어떤 범위로 구현하더라도 이 문서의 HTTP, 보안, 원문 보존, 라이선스와 실패
처리 원칙은 동일하게 적용한다.

## 공통 HTTP 정책

API와 Web Collector는 공통 HTTP Client를 사용한다.

초기 기본값:

```text
timeout: 10 seconds
max retries: 3
request delay: 1.0 seconds
```

필수 기능:

- 명시적 Timeout
- 식별 가능한 User-Agent
- 상태 코드 검사
- 제한된 재시도와 재시도 가능 오류 구분
- 웹 요청 간 간격
- JSON과 XML 응답 처리
- 테스트 가능한 Session 또는 Client 주입
- 소스와 URL을 포함하되 비밀정보를 제외한 오류 메시지

공식 소스의 호출 제한이 확인되면 해당 제한을 기본값보다 우선한다.

현재 공통 `HttpClient`는 Timeout·전송 오류와 5xx만 최대 3회 재시도한다.
`max retries`는 최초 요청 이후의 추가 시도 횟수이므로 기본 총 시도 횟수는
최대 4회다. 401·403은 인증 오류, 429는 호출량 오류, 그 밖의 4xx는 요청
오류로 즉시 중단한다. 5xx 재시도에는 0.5초부터 시작하는 지수 backoff를
적용하고 모든 요청 시작 사이에는 최소 1초 간격을 둔다.

공통 Client는 redirect를 자동 추적하지 않는다. 특히 query 인증정보가 다른
origin이나 비표준 포트로 전달되는 일을 막고 3xx를 명시적 오류로 처리한다.
오류 URL에서는 인증 파라미터만 선별하지 않고 모든 query 값과 URL user
information을 `<redacted>`로 바꾼다. 응답 본문과 하위 전송 예외 메시지는
공통 예외에 포함하지 않는다.

HTML Collector는 현재 Forest 범위 밖이다. 이후 별도 Forest에서 승인되면
HTML 파서와 웹 수집 정책의 구현 범위를 다시 확정한다.

## 웹 수집 원칙

- robots 정책과 이용약관을 확인한다.
- 공개 목록과 필요한 상세 페이지만 제한적으로 요청한다.
- 정적 HTML을 우선한다.
- 공개 내부 API가 있으면 이용 조건을 확인하고 안정적인 방법을 선택한다.
- Selector는 소스별 모듈에서 관리한다.
- Playwright나 Selenium은 정적 HTML과 공개 요청으로 데이터를 얻을 수 없을
  때만 별도 검토한다.
- 로그인 우회, CAPTCHA 우회와 접근 통제 회피를 구현하지 않는다.

## 인증정보

다음 환경변수를 사용한다.

```text
YOUTHCENTER_API_KEY
BOKJIRO_API_KEY
HTTP_TIMEOUT_SECONDS
HTTP_MAX_RETRIES
HTTP_REQUEST_DELAY_SECONDS
```

- 실제 값은 로컬 `.env` 또는 안전한 비밀 관리 수단에 둔다.
- `.env`는 Git에 커밋하지 않는다.
- `.env.example`에는 변수명과 비밀이 아닌 예시만 기록한다.
- 인증키를 URL, 로그, 예외 메시지, Fixture와 문서에 포함하지 않는다.
- 키가 없으면 모호한 네트워크 오류 대신 명확한 설정 오류를 반환한다.
- 인증 파라미터 이름이 소스마다 달라도 `apiKeyNm`, `openApiVlak`,
  `serviceKey`와 같은 값은 공통 redaction 대상으로 처리한다.
- 요청 URL을 기록해야 하면 query string 전체를 제거하거나 허용된
  비인증 파라미터만 다시 구성한다.

현재 로컬 참고 자료 일부에는 실제 인증키가 포함되어 있다. 해당 파일은
읽기 전용 비밀 자료로 취급하고 Git, Fixture, 테스트 snapshot과 개발 기록에
복사하지 않는다.

과거 Git 이력에 인증키 파일과 비밀 포함 참고 문서가 들어간 사실이 확인되면
ignore와 인덱스 제외만으로 해결된 것으로 간주하지 않는다. 해당 키를
폐기·재발급하고, 저장소 이력 정리는 협업 영향과 원격 상태를 확인한 뒤
별도로 결정한다.

## 공식 API 호출 예산

실제 외부 API 호출은 단위 테스트와 분리된 명시적 통합 검증으로만 실행한다.

- 기본 테스트는 검토된 JSON·XML Fixture를 사용한다.
- Source Preflight는 현재 endpoint, 인증과 응답 형식을 확인하는 최소 호출만
  수행한다.
- 복지로 목록은 한 페이지를 재사용하고 상세는 대표 3~5건만 호출한다.
- 호출 전에 현재 계정의 할당량과 공식 제한을 확인한다.
- 429 또는 제공기관의 할당량 오류는 제한적으로 재시도하지 않고 실행을
  중단해 남은 호출량을 보호한다.
- 실제 호출 결과에는 키 값과 전체 query string을 제외한 소스, 실행 시각,
  호출 건수, HTTP 결과와 응답 구조 확인 결과만 기록한다.

## Raw 보존

Raw는 받은 내용을 재현 가능한 형태로 보존한다.

- 목록·상세 HTTP 응답 전체 byte를 Base64로 보존
- 목록 항목별 파생 Raw는 부모 목록 응답을 참조
- 출처 URL과 timezone을 포함한 수집 시각 기록
- content type과 raw format 기록
- 원본 byte의 SHA-256 content hash와 byte 길이 기록
- Collector 버전 기록
- 원문을 정규화된 필드로 덮어쓰지 않음

Hash는 다음을 위한 기반이다.

- 동일 원문 재수집 감지
- 변경 여부 확인
- 중복 저장 방지

현재 `RawPolicyDocument`는 Base64를 디코딩한 원본 byte로
`sha256:<64 lowercase hex>`를 계산한다. Hash와 byte 길이가 payload와
일치하지 않으면 저장·로드하지 않는다. 변경 이력과 소스 간 중복 판정은
후속 Forest 범위다.

## Git과 Runtime 데이터

| 구분 | 예 | Git 포함 |
| --- | --- | --- |
| Schema | `data/schema/*.schema.json` | 포함 |
| 테스트 Raw Fixture | 축소·검토한 XML, JSON, HTML | 조건부 포함 |
| 개발 Fixture | `data/fixtures/normalized/programs.json` | 포함 |
| canonical 개발 Seed | `data/seeds/initial_programs.json` | 포함 |
| 파생 CSV Seed | canonical JSON에서 생성한 CSV | 합의·검증 시 포함 |
| 실제 수집 Raw | 전체 API 응답, 운영 HTML | 제외 |
| 처리 결과 | runtime normalized, rejected | 제외 |
| DB 데이터 | PostgreSQL Volume | 제외 |

Git에 포함할 Fixture는 다음 조건을 모두 만족해야 한다.

- 테스트에 필요한 최소 범위
- 개인정보와 비밀정보 제거
- 이용 조건상 재배포 가능
- 출처와 생성 또는 수집 방법 기록
- 원본 구조를 검증하는 데 필요한 특성 유지

Seed는 JSON을 canonical 표현으로 사용해 배열, `null`, enum과 provenance의
타입을 보존한다. CSV는 Backend 초기 적재에 필요하다고 합의한 경우에만
canonical JSON에서 결정적으로 생성하며, 배열 직렬화와 `null` 표현을
문서화하고 두 표현의 일관성을 자동 검증한다.

실제 runtime 저장 경로는 `runtime/raw/`다. 저장 envelope도 운영 Raw이므로
Git에 포함하지 않는다.

현재 재유입 방지 경계는 다음과 같다.

```text
.env
.env.*
APIkey.txt
runtime/raw/
data/runtime/raw/
```

`.env.example`은 실제 값 없이 변수명과 안전한 예시만 포함하는 경우 Git에
포함할 수 있다. 비밀이 포함된 로컬 참고 문서는 정확한 경로를 `.gitignore`에
등록한다. `data/runtime/raw/`는 현재 저장기가 사용하지 않는 과거 후보지만
잘못된 경로의 Raw가 Git에 재유입되지 않도록 ignore를 유지한다.

저장 경로는 다음과 같다.

```text
runtime/raw/<source_id>/<document_role>/<UTC YYYY>/<MM>/<DD>/<document_id>.json
```

저장기는 설정 root 밖 경로, query나 user information이 포함된 `source_url`,
형식에 맞지 않는 source ID·document ID와 기존 문서 덮어쓰기를 거부한다.

## 개인정보와 민감정보

- 정책 정보 수집에 필요하지 않은 이름, 연락처와 식별정보는 저장하지 않는다.
- 개인정보가 포함된 게시물, 첨부파일 또는 응답 필드는 수집 대상에서
  제외하거나 저장 전에 안전한 처리 기준을 별도로 확정한다.
- 운영 원문을 Fixture로 복사하기 전에 민감정보를 검토한다.
- 로그에는 인증키, 전체 query string과 개인정보를 남기지 않는다.
- 개인정보 처리 필요성이 생기면 구현 전에 보존 기간, 접근권한과 삭제 절차를
  문서화한다.

## 라이선스와 출처

소스를 구현하기 전에 다음을 확인하고 [데이터 소스](data_sources.md)에
기록한다.

- 제공 기관과 원문 URL
- 공공데이터 또는 웹사이트 이용약관
- 수집·저장·변환·재배포 허용 범위
- 출처 표시 문구와 링크 요구사항
- 호출 제한과 robots 정책
- 상업적 이용 또는 2차 저작물 제한

조건을 확인할 수 없거나 저장·재배포가 허용되는지 불명확하면 해당 원문을
Git Fixture에 포함하지 않는다.

## 실패 처리

- 인증키 누락, Timeout, HTTP 오류, 파싱 오류를 구분한다.
- 소스, 실행 시각, 오류 유형과 재시도 횟수를 기록한다.
- 인증키와 전체 응답의 민감정보는 오류 기록에서 제외한다.
- 특정 정책의 선택 필드 누락으로 전체 수집을 중단하지 않는다.
- 실패한 응답을 정상 `RawPolicyDocument`나 정상화 데이터로 가장하지 않는다.
- invalid 정규화 결과는 정상 출력과 분리한다.

## 테스트 원칙

- 외부 API를 매 테스트마다 호출하지 않는다.
- 검토된 XML, JSON과 HTML Fixture로 대부분의 테스트를 수행한다.
- 인증 누락, 정상 응답, 빈 응답, HTTP 오류와 선택 필드 누락을 검증한다.
- 실제 API 호출 검증은 별도 통합 절차로 구분하고 실행 조건을 명시한다.

## 정책 변경

수집 대상, 저장 범위, 개인정보 처리 또는 이용 조건이 바뀌면 다음을 함께
갱신한다.

- 이 문서와 `data_sources.md`
- Collector와 Extractor
- Fixture와 테스트
- 환경변수 및 운영 문서
- 의미 있는 변경인 경우 `CHANGELOG.md`
