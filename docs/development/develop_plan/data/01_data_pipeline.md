# Data Pipeline Forest 개발 계획

## 계획 정보

- 담당 영역: Data
- 상태: in-progress
- 대상 기간: 데이터 파이프라인 기반 구축 Forest
- 관련 브랜치: `feature/data/pipeline-foundation`
- 현재 Slice: Data 7 기술 검증 완료, Data 6 공동 검토 대기
- 개발 기록:
  [Data Pipeline Forest 개발 기록](../../development_notes/data/data_pipeline.md)

## 목적

온통청년과 복지로의 공식 API에서 제한된 샘플을 수집하고, Raw 원문 보존부터
소스별 추출, 공통 정규화·검증, Fixture와 Seed 생성까지 이어지는 데이터
파이프라인 기준선을 구현한다. Backend와 Frontend가 Collector의 외부 연동
상태와 무관하게 같은 샘플 데이터 계약으로 후속 개발을 시작할 수 있게 한다.

## 확인된 전제와 계획 변경

초기 계획은 온통청년 API와 대표 HTTPS 웹사이트 한 곳을 대상으로 했다. 현재는
온통청년과 복지로의 API 인증키가 모두 확보되어 있으므로 이 Forest에서는
임의의 웹사이트보다 두 공식 API를 우선한다.

| 소스 | 계획 식별자 | 기준 응답 | 기준 수집 단위 |
| --- | --- | --- | --- |
| 온통청년 청년정책 API | `youthcenter-api` | JSON | 정책 목록 항목 |
| 복지로 중앙부처 복지서비스 API | `bokjiro-central-welfare-api` | XML | 목록 항목과 선택한 상세 |

이 변경으로 Source Extractor가 서로 다른 두 공식 API의 필드와 목록·상세 구조를
공통 `ExtractedPolicy`로 변환하는지를 기준선에서 검증할 수 있다. HTML
Selector와 Web Collector 검증은 별도 Forest 후보로 이동한다.

### 자료 간 불일치

온통청년 로컬 참고 자료와 현재 공식 제공목록은 다음 항목이 다르다.

- 로컬 참고 자료: `/go/ythip/getPlcy`, `apiKeyNm`, `pageNum`, `pageSize`,
  `rtnType`
- 현재 공식 제공목록의 요청 예시: `/opi/youthPlcyList.do`,
  `openApiVlak`, `pageIndex`, `display`
- 공식 이용방법은 결과를 XML로 설명하지만 로컬 참고 자료에는 JSON 선택
  파라미터와 10건의 JSON 샘플이 있다.

보유 키로 두 계약을 각각 검증한 결과, 공식 제공목록 endpoint는 HTTP 302로
외부에서 접근할 수 없는 HTTP 8080 포트에 redirect했고 로컬 참고 자료의
`/go/ythip/getPlcy`는 HTTP 200 JSON을 반환했다. 따라서 현재 Collector는
실동작이 확인된 로컬 제공 계약을 사용하고 공식 제공목록 endpoint는 새 키
또는 gateway 수정이 확인될 때 다시 검토한다.

복지로는 현재 공식 자료에서 다음 사항을 확인했다.

- Base URL:
  `https://apis.data.go.kr/B554287/NationalWelfareInformationsV001`
- 목록: `/NationalWelfarelistV001`
- 상세: `/NationalWelfaredetailedV001`
- 응답 형식: XML
- 개발계정 호출량이 제한되므로 단위 테스트는 저장된 Fixture로 실행하고 실제
  호출은 명시적 통합 검증으로만 수행

공식 자료의 변경일과 실제 응답이 다를 수 있으므로 이 정보도 첫 연동 시 다시
검증한다.

## 범위

- 두 공식 API의 endpoint·인증·응답 형식을 확인하는 Source Preflight
- 온통청년 정책 목록의 제한된 Raw 수집
- 복지로 서비스 목록과 선택한 상세의 제한된 Raw 수집
- 공통 HTTP Client와 기본 오류·재시도·호출 간격 처리
- Raw 원문, 수집 메타데이터와 SHA-256 Hash 보존
- 소스별 Extractor와 공통 Normalizer 및 Validator 기반
- Raw와 Normalized JSON Schema
- 검토된 Fixture와 canonical JSON Seed 생성
- 필요성이 합의된 경우에만 canonical Seed에서 파생한 CSV 생성

초기 검증 목표:

- 온통청년 정책 10건 이상 Raw 수집
- 복지로 목록 10건 이상과 그중 상세 3~5건 Raw 수집
- 두 소스가 모두 공통 `ExtractedPolicy`와 `NormalizedProgram` 흐름을 통과
- 외부 호출 없이 저장된 Fixture만으로 전체 단위 테스트 재실행

실제 호출 건수는 각 서비스의 현재 할당량과 이용 조건을 확인한 뒤 더 낮게
조정할 수 있다. 검증 목표를 채우기 위해 반복 호출하지 않고 한 번 받은
응답을 안전한 Fixture 후보로 검토한다.

## 범위 밖

- 온통청년 또는 복지로 전체 데이터 수집
- 임의 HTTPS 웹사이트와 HTML Selector 기반 Collector
- 정기 Scheduler와 운영 수집
- 수정·삭제 자동 감지와 완전한 변경 이력
- 소스 간 동일 정책의 자동 병합
- 정교한 중복 판정
- LLM 기반 자격 조건 추출
- 운영 DB 직접 적재 자동화와 DB Migration

Web Collector는 API 파이프라인 기준선이 완료된 뒤 독립적인 수집 대상,
robots·이용 조건, Selector 완료 기준을 가진 별도 Forest로 검토한다.

## 선행 조건

- 온통청년의 현재 endpoint, 인증 파라미터와 XML·JSON 지원 여부 확인
- 복지로 목록·상세 endpoint와 개발계정 호출 제한 확인
- 인증키 파일과 인증키가 포함된 참고 문서를 Git 추적 대상에서 제외
- 비밀값을 제외한 환경변수 이름과 로컬 실행 방법 합의
- 두 API 샘플의 필드 존재율, 빈 문자열, 코드값과 날짜 형식 프로파일링
- `application_status`, category와 소스 간 중복 표현 공동 검토

계획 환경변수 이름:

```text
YOUTHCENTER_API_KEY
BOKJIRO_API_KEY
HTTP_TIMEOUT_SECONDS
HTTP_MAX_RETRIES
HTTP_REQUEST_DELAY_SECONDS
```

실제 키 값, 인증 파라미터가 포함된 URL과 전체 query string은 코드, 문서,
Fixture, 로그와 예외 메시지에 남기지 않는다.

## 공통 설계 원칙

- Collector는 정규화하지 않는다.
- Raw 원문은 손실 없이 보존한다.
- 소스별 필드명과 목록·상세 결합은 Extractor가 담당한다.
- 공통 형식 변환은 Normalizer가 담당한다.
- Validator는 Schema 위반을 정상 데이터와 분리한다.
- 같은 `external_id`라도 `source_id`가 다르면 동일 레코드로 간주하지 않는다.
- 소스 간 중복 후보는 원본을 병합하지 않고 provenance를 유지한다.
- 실제 운영 Raw와 비밀정보는 Git에 포함하지 않는다.
- 공통 기준은 `docs/data/` 문서를 따르고 이 계획에는 Forest 실행 범위와
  미확정 계약의 결정 게이트를 둔다.

## 데이터 표현과 Schema 설계 기준

### Raw 계층

목록 응답 전체와 항목별 문서, 복지로 상세 응답을 구분할 수 있어야 한다.
기존 `RawPolicyDocument`만으로 이 관계를 표현할 수 있는지 첫 Schema
Slice에서 검토한다.

검토할 최소 메타데이터:

- `source_id`
- source-scoped `external_id`
- 목록·상세·항목을 구분하는 문서 역할
- 목록 항목과 상세 응답의 연결 ID
- 실제 요청 URL에서 인증정보를 제거한 안전한 `source_url`
- 수집 시각, HTTP 상태, content type과 raw format
- 원문 hash와 Collector 버전

문서 역할과 연결 ID의 최종 필드명, required 여부와 enum은 실제 두 API
샘플을 확인한 뒤 Backend·Frontend 영향 검토와 함께 확정한다.

### Extracted 계층

두 API의 코드와 원문 필드를 `ExtractedPolicy`로 매핑하되 다음을 보존한다.

- 온통청년의 정책 대·중분류, 키워드와 자격 코드 원문
- 복지로의 생애주기, 가구유형, 관심주제와 목록·상세 원문
- 신청 기간, 연령, 지역과 자격 조건의 원문 text
- 공통 필드로 매핑하지 않은 소스 필드는 `extra`
- 소스 표시 이름과 source-scoped 외부 ID

Extractor는 빈 문자열과 실제 값 없음, 코드 미해석을 구분해 Normalizer에
전달한다.

### Normalized 계층

현재 `NormalizedProgram`의 null·빈 배열 규칙은 유지한다.

- 선택 단일 값 없음: `null`
- 복수 값 없음: `[]`
- 필수 값 없음 또는 Schema 위반: `invalid`
- 원문에 없는 값은 추정하지 않음

다음 항목은 실제 두 소스 프로파일을 근거로 공동 검토하기 전까지 enum이나
필드 구조를 확정하지 않는다.

- 상시 신청 여부와 현재 신청 가능 상태의 분리 여부
- 온통청년 대분류와 복지로 관심주제를 단일 `category`로 축약할지 여부
- `category`를 단일 값으로 유지할지 배열로 전환할지 여부
- 학력·취업·특화 조건의 code와 표시 문자열 보존 방식
- 복지로의 생애주기·가구유형을 기존 조건 배열에 매핑할지 별도 필드로 둘지
- 동일 서비스의 여러 출처를 표시하는 provenance 구조

이 계약을 변경할 경우 `docs/data/data_schema.md`,
`docs/data/normalization_rules.md`, JSON Schema, Fixture와 Seed를 같은
Slice에서 동기화하고 Backend 응답 Schema·검색 필터와 Frontend 타입·표시의
영향을 공동 확인한다.

### Fixture와 Seed

JSON을 타입 보존이 가능한 canonical 표현으로 사용한다. 배열, `null`,
provenance와 원문 text를 손실시키는 수작업 CSV를 기준 계약으로 삼지 않는다.

계획 산출물:

```text
data/fixtures/raw/<source_id>/...
data/fixtures/extracted/...
data/fixtures/normalized/programs.json
data/fixtures/rejected/...
data/seeds/initial_programs.json
```

CSV가 Backend 초기 적재에 필요하다고 공동 합의한 경우에만 canonical JSON에서
결정적으로 생성한다. 이때 배열의 직렬화, `null`과 빈 문자열 구분, enum과
날짜 형식을 명시하고 JSON과 CSV의 일관성을 자동 검증한다.

Seed 구성은 소스별 건수만 채우는 방식이 아니라 다음 대표 사례를 포함한다.

- 온통청년과 복지로 각각의 정상 사례
- 목록 정보만 있는 사례와 상세가 결합된 사례
- 지역 제한 있음·없음
- 연령 범위 있음·없음
- 특정 기간·상시·마감 또는 기간 미상
- 선택 단일 값 누락과 빈 배열
- 여러 원문 분류·관심주제가 있는 사례
- invalid로 분리되는 필수 필드 누락 사례

## Slice 계획

### Data 0 - Source Preflight와 비밀정보 경계

- 상태: completed
- 목적: 두 API의 현재 계약과 안전한 실행 조건을 확인한다.
- 작업:
  - 로컬 참고 자료와 현재 공식 자료의 차이 기록
  - 인증키를 출력하지 않는 최소 호출로 endpoint·파라미터·응답 형식 확인
  - 소스별 호출 제한과 오류 응답 확인
  - API 응답 필드·타입·빈 값·코드의 Source Profile 작성
  - 비밀 포함 파일, `.env`, runtime Raw의 Git 제외 검증
- 완료 기준:
  - 두 source ID와 현재 호출 계약이 문서화됨
  - 인증키가 URL, 로그, 예외와 Fixture에 남지 않음
  - 실제 호출 횟수와 결과가 개발 기록에 남음
- 진행 결과:
  - `youthcenter-api`와 `bokjiro-central-welfare-api`를 현재 source ID로
    문서화함
  - 온통청년 `/go/ythip/getPlcy`의 HTTP 200 JSON 10건 응답과 60개 정책
    필드를 확인함
  - 복지로 목록·상세의 HTTPS XML 계약을 최소 실호출로 확인함
  - `/opi/youthPlcyList.do`는 보유 키로 HTTP 8080 redirect가 발생해 현재
    계약에서 제외함
  - 비밀 포함 파일, `.env`와 runtime Raw의 Git 재유입 방지 규칙을 추가함

### Data 1 - 공통 모델과 HTTP 기반

- 상태: completed
- 목적: Collector가 공유할 실행 구조와 HTTP 동작을 구현한다.
- 작업:
  - Collector 인터페이스, Registry와 CLI
  - Timeout, 제한된 재시도·backoff와 요청 간격
  - JSON·XML 처리와 테스트 가능한 Client 주입
  - 인증 실패, 429, 재시도 가능한 5xx와 파싱 오류 구분
  - 인증 파라미터와 query string 마스킹
- 완료 기준:
  - `--source`로 Collector를 선택할 수 있음
  - Mock으로 정상, Timeout, 429, 4xx와 5xx 동작을 검증함
  - 비밀값이 로그와 예외에 노출되지 않음
- 진행 결과:
  - `Collector` 프로토콜, source ID 기반 `CollectorRegistry`와
    `python -m collectors --source SOURCE_ID` CLI를 구현함
  - 총 시도 횟수를 제한하는 Timeout·전송·5xx 재시도, 지수 backoff와
    요청 시작 간 최소 간격을 구현함
  - 401·403 인증 실패, 429, 일반 4xx, 소진된 5xx, Timeout·전송·JSON·XML
    파싱 오류를 서로 다른 예외로 분류함
  - 자동 redirect를 차단하고 오류 URL의 모든 query 값과 user information을
    `<redacted>`로 대체하며 응답 본문과 원본 예외 메시지를 노출하지 않음
  - 주입한 Transport와 가상 clock으로 정상·실패·재시도·호출 간격을 검증함
  - 실제 소스 Collector 등록과 환경변수 로딩은 Data 3·4 범위로, Raw 결과
    모델과 저장은 Data 2 범위로 유지함

### Data 2 - Raw 계약과 저장

- 상태: completed
- 목적: 두 API의 목록·항목·상세 원문을 손실 없이 보존한다.
- 작업:
  - Raw Python 모델과 JSON Schema
  - 문서 역할과 목록·상세 연결 방식 확정
  - SHA-256 hash와 안전한 파일 저장
  - 전체 응답과 항목별 Raw의 보존 경계 확정
- 완료 기준:
  - JSON과 XML 기반 Raw 사례가 Schema를 통과함
  - 동일한 원문은 동일한 hash를 생성함
  - 경로 이탈과 운영 Raw의 Git 포함을 방지함
- 진행 결과:
  - Raw Schema `1.0.0`, Python `RawPolicyDocument`와 JSON Schema를 구현함
  - 목록 전체 `list_response`, 파생 `list_item`, 상세 `detail_response` 역할과
    `parent_document_id`, source-scoped `external_id` 연결 규칙을 확정함
  - HTTP body 원본 byte를 Base64로 보존하고 디코딩한 byte에
    `sha256:<64 lowercase hex>`와 `byte_length`를 검증함
  - query·fragment·user information이 없는 HTTPS `source_url`만 허용함
  - 운영 저장 위치를 `runtime/raw/`로 확정하고 UTC 날짜·source·역할별
    불변 JSON envelope 저장과 로드를 구현함
  - 중복 덮어쓰기, 설정 root 밖 경로와 symlink 경로 이탈을 거부함
  - JSON 목록·항목과 XML 상세 사례의 Schema 통과, byte 왕복, hash 결정성과
    Git ignore 경계를 외부 API 호출 없이 검증함
  - Raw는 내부 provenance 계약이므로 Normalized Schema, Fixture, Seed,
    Backend API와 Frontend 타입은 변경하지 않음

### Data 3 - 온통청년과 복지로 Collector

- 상태: completed
- 목적: 두 공식 API에서 제한된 데이터를 Raw 문서로 변환한다.
- 작업:
  - 온통청년 목록 Collector
  - 복지로 목록과 상세 Collector
  - 페이지·limit 처리와 응답 건수 기록
  - 빈 응답, 인증 실패, 할당량 제한과 형식 오류 처리
- 완료 기준:
  - 온통청년 10건 이상 Raw 수집
  - 복지로 목록 10건 이상과 상세 3~5건 Raw 수집
  - 실제 호출과 Mock 테스트가 분리됨
- 진행 결과:
  - 환경변수 기반 factory와 기본 Registry에 `youthcenter-api`,
    `bokjiro-central-welfare-api`를 등록함
  - 공통 CLI에 `--page`, `--limit`, `--detail-limit`과 요청·항목·상세·Raw
    문서 수의 안전한 실행 요약을 추가함
  - 온통청년 `pageNum`·`pageSize` JSON 목록과 `plcyNo` 항목 Raw 변환을
    구현함
  - 복지로 `pageNo`·`numOfRows` XML 목록, `servId` 항목과 최대 5건 상세
    Raw 변환을 구현함
  - 빈 목록, 형식 오류, external ID 불일치, HTTP와 소스 payload의
    인증·할당량·일반 오류를 분류함
  - 응답이 요청 인증키를 반사하면 Raw 저장 전에 중단하고 `source_url`에는
    query를 포함하지 않음
  - Mock 단위 테스트와 수동 opt-in 실제 호출을 분리함
  - 2026-07-26 실제 호출에서 온통청년 목록 10건, 복지로 목록 10건과
    상세 3건을 각각 Raw 11개와 14개로 저장·재로드함
  - Data 3 실호출은 온통청년 1회, 복지로 목록 1회·상세 3회였으며 저장된
    25개 Raw에서 인증키 일치, 불안전 URL과 관계 오류가 모두 0건이었음

### Data 4 - 소스별 Extractor와 Source Profile

- 상태: completed
- 목적: 두 API의 Raw를 공통 의미 단위로 추출한다.
- 작업:
  - `YouthCenterExtractor`
  - `BokjiroExtractor`
  - 복지로 목록·상세 결합
  - 코드값과 미매핑 필드의 `extra` 보존
  - 필드 존재율과 빈 값 보고서
- 완료 기준:
  - 두 소스가 같은 `ExtractedPolicy` 경계를 사용함
  - 선택 필드 누락 시에도 확인 가능한 값이 유지됨
  - 원문 값과 source provenance가 손실되지 않음
- 진행 결과:
  - `source_name`, 최신 `collected_at`과 기여 Raw별 ID·역할·hash·시각·안전
    URL을 포함한 공통 `ExtractedPolicy` Python 모델을 구현함
  - `YouthCenterExtractor`가 목록 JSON 필드와 신청기간 코드·연령 경계를
    공통 text로 전달하고 전체 60개 source 필드를 `extra`에 보존함
  - `BokjiroExtractor`가 같은 `servId`의 목록·상세를 결합하고 상세가 없는
    7건은 목록의 확인 가능한 값을 유지함
  - 복지로 반복 XML leaf는 배열로, 누락 필드는 부재로, 빈 element와 JSON
    빈 문자열은 빈 값으로 서로 구분함
  - 실제 runtime Raw를 추가 API 호출 없이 재처리해 소스별 10건씩 총 20건을
    추출하고 상세 3건 결합, source field 보존·provenance 오류 0건을 확인함
  - 온통청년 10건·60필드와 복지로 목록 10건·15필드, 상세 3건·19필드의
    존재·누락·빈 값·반복 타입 프로필을 기준 문서에 반영함

### Data 5 - 정규화, Schema와 Validator

- 상태: completed
- 목적: 공통 `NormalizedProgram` 변환과 품질 분류를 구현한다.
- 작업:
  - 텍스트, 날짜, 연령, 지역과 카테고리 정규화
  - 실제 샘플 기반 미확정 계약 공동 검토
  - Normalized JSON Schema와 Validator
  - valid·partial·invalid 분리와 오류 위치 출력
- 완료 기준:
  - 정상·경계·실패 Fixture를 검증함
  - 문서, Python 모델과 JSON Schema가 일치함
  - Schema 변경의 Backend·Frontend 영향을 기록함
- 진행 결과:
  - 텍스트의 HTML·Entity·공백 정리와 날짜·연령·지역·category 정규화를
    구현하고 원문 text를 병행 보존함
  - 실제 다중 관심주제를 근거로 단일 `category` 후보를 `categories` 배열로
    바꾸고 일정 유형과 수집 기준 상태를 `application_schedule`과
    `application_status`로 분리함
  - `NormalizedProgram` Python 모델과 Draft 2020-12 JSON Schema 1.0.0의
    31개 필드, null·빈 배열·enum·provenance 계약을 일치시킴
  - 표준 라이브러리 Validator가 Schema, 날짜·연령 순서와 품질 상태 일치를
    검사하고 JSON path issue로 valid·partial·invalid를 분리하도록 구현함
  - 개인정보·외부 원문이 없는 합성 정상·경계·실패 JSON Fixture 3개와
    Normalizer·Validator 사례 13건, Data 0~5 전체 회귀 71건을 통과함
  - 실제 Raw 25개를 추가 외부 호출 없이 정책 20건으로 재처리해 partial
    20건, invalid 0건과 Schema·provenance 오류 0건을 확인함
  - 현재 Backend·Frontend 소비 구현은 없으며 Data 6 Fixture·Seed 승인 전에
    배열 category, 신청 일정·상태, required key와 provenance를 공동 검토해야
    함을 기준 문서에 기록함

### Data 6 - Fixture와 Seed 계약

- 상태: in-progress
- 목적: Backend와 Frontend가 사용할 재현 가능한 샘플 데이터를 제공한다.
- 작업:
  - 검토된 Raw·Extracted·Normalized Fixture
  - canonical JSON Seed와 재생성 명령
  - 필요 시에만 파생 CSV 생성
  - rejected 사례와 실패 사유
  - 출처·개인정보·비밀정보·재배포 조건 검토
- 완료 기준:
  - 정상 Seed가 Normalized Schema를 통과함
  - 소스·null·빈 배열·enum·날짜 표현이 보존됨
  - 외부 네트워크 없이 Fixture 기반 테스트가 가능함
  - Backend·Frontend가 사용할 계약이 공동 검토됨
- 진행 결과:
  - 실제 API 원문 대신 두 소스의 관찰된 JSON·XML 구조만 재현한 합성 Raw
    8개와 Extracted 5건을 구현함
  - valid 2건·partial 2건의 Normalized Fixture와 byte가 같은 canonical
    JSON Seed 4건을 생성하고 invalid 1건과 `$.title` 실패 사유를 분리함
  - 고정 ID·시각·payload를 사용하는 재생성 명령과 committed byte 비교
    명령을 구현하고 외부 네트워크·runtime Raw 의존이 없음을 검증함
  - null·빈 배열·다중 category·날짜, fixed·always, open·closed,
    목록 전용·상세 결합과 provenance 대표 사례를 포함함
  - CSV 소비 요구가 없어 파생 CSV는 생성하지 않음
  - 복지로는 공식 이용허락범위 `제한 없음`, 온통청년은 승인형 API와
    상업적 가공 제한을 확인해 실제 원문을 Git에 포함하지 않음
  - Data 기술 검토는 완료했으나 저장소에 Backend·Frontend 구현과 승인
    증거가 없어 공동 검토 완료 기준은 아직 충족하지 못함

### Data 7 - 최종 검증과 Forest 기록

- 상태: completed
- 목적: 전체 흐름과 문서 동기화를 최종 확인한다.
- 완료 기준:
  - Raw → Extracted → Normalized → Validated → Seed 흐름 통과
  - 관련 단위·통합 테스트 통과
  - `python scripts/validate_docs.py` 통과
  - Data 개발 기록에 실제 호출·테스트·제약 기록
  - 완료 결과가 의미 있을 때만 `CHANGELOG.md` 갱신
- 진행 결과:
  - 커밋된 합성 Raw 8개를 직접 다시 로드해 Extracted 5건,
    valid 2·partial 2·invalid 1로 변환하고 accepted 4건이 canonical
    Seed와, invalid 1건이 rejected와 정확히 일치함을 통합 테스트로 검증함
  - 운영 Raw 25개도 추가 API 호출 없이 Extracted 20건·partial 20건으로
    재처리했고 검증 오류 0건을 확인함
  - Fixture 결정성 12개 파일, Data 전체 회귀 81건, 문서 검증과 diff 공백
    검사를 통과함
  - 실제 API를 추가 호출하지 않았으며 기존 호출 횟수·제약·재배포 경계를
    개발 기록에서 재확인함
  - canonical Fixture·Seed까지 제공하는 의미 있는 Forest 결과를 기존
    `CHANGELOG.md` Data 항목에 합쳐 기록함
  - Data 7 기술 검증은 완료했지만 Data 6의 Backend·Frontend 공동 승인
    기준이 남아 Forest 전체 상태는 `in-progress`로 유지함

## 검증 계획

- Collector Registry와 CLI 단위 테스트
- HTTP Client의 정상, Timeout, 429, 인증 실패, 4xx와 5xx 테스트
- 온통청년 JSON·XML 후보와 복지로 XML Fixture 기반 Extractor 테스트
- 목록·상세 연결과 외부 ID 안정성 테스트
- Normalizer 정상·경계·실패 테스트
- Raw와 Normalized JSON Schema 검증 테스트
- canonical JSON Seed의 null·빈 배열·enum·날짜 검증
- 파생 CSV가 있으면 JSON과 논리적 값 일관성 검증
- 비밀정보, 개인정보와 운영 Raw의 Git 포함 방지 검증
- `python scripts/validate_docs.py`

실제 외부 API 호출은 명시적 opt-in 통합 검증으로 구분한다. 호출 전에 환경
변수 존재만 확인하고 키 값은 출력하지 않으며, 실행 시각·소스·호출 건수·HTTP
결과와 구조 확인 결과만 개발 기록에 남긴다.

## Forest 완료 기준

- 두 공식 API의 Raw → Extracted → Normalized → Validated 흐름이 대표
  샘플로 검증됨
- Backend와 Frontend가 사용할 canonical JSON Fixture 또는 Seed가 제공됨
- Schema와 `docs/data/` 기준 문서가 실제 구현과 일치함
- null·빈 배열·enum·날짜·provenance 계약이 공동 검토됨
- 실행한 테스트, 실제 API 호출 횟수와 알려진 제약이 Data 개발 기록에 기록됨
- 의미 있는 완료 결과가 `CHANGELOG.md`에 요약됨

## 위험과 미확정 사항

- 온통청년의 로컬 참고 자료와 현재 공식 제공목록 간 endpoint·파라미터 차이
- 온통청년의 XML·JSON 지원 범위와 응답 필드 변경 가능성
- 복지로 개발계정 호출량과 목록·상세 결합 비용
- 두 API 코드표의 변경과 빈 문자열 표현
- 목록과 상세 Raw의 연결 필드 및 required 규칙
- 소스 간 같은 정책 또는 유사 서비스의 중복 판정
- Normalized 1.0.0의 category 배열, 신청 일정·상태와 provenance에 대한
  Backend·Frontend 소비 계약 승인
- canonical JSON을 DB Seed로 직접 사용할지 별도 importer를 둘지 여부
- 실제 runtime Raw 저장 경로와 변경 감지 도입 시점

미확정 사항은 공식 자료와 실제 샘플을 확인하기 전까지 현재 동작으로 표현하지
않는다. Schema, Fixture와 Seed 계약은 Data 담당이 단독 확정하지 않고
Backend·Frontend와 공동 검토한다.

## 후속 Forest 후보

HTML 기반 수집은 API 기준선과 독립적인 목표와 완료 기준을 가진다.

- 추천 브랜치: `feature/data/web-collector-foundation`
- 분리 이유: 대상 사이트 선정, robots·이용 조건, Selector, 정적·동적 처리와
  HTML 회귀 Fixture가 두 공식 API의 완료 기준과 독립적이기 때문

DB 적재와 Migration도 현재 Forest 범위 밖이다. Backend의 최소 DB 모델과
적재 경계가 공동 확정된 뒤 별도 Forest로 계획한다.

## 관련 문서

- [개발 계획 안내](../README.md)
- [데이터 문서 안내](../../../data/README.md)
- [데이터 소스](../../../data/data_sources.md)
- [데이터 Schema 기준선](../../../data/data_schema.md)
- [데이터 정규화 규칙](../../../data/normalization_rules.md)
- [데이터 수집 정책](../../../data/collection_policy.md)
- [온통청년 OPEN API 제공목록](https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiDoc/47)
- [복지로 중앙부처 복지서비스 API](https://www.data.go.kr/data/15090532/openapi.do)
