# Data Pipeline Forest 개발 기록

## 작업 정보

- 기간: 2026-07-26
- 담당 영역: Data
- 상태: in-progress
- 브랜치: `feature/data/pipeline-foundation`
- 관련 계획:
  [Data Pipeline Forest 개발 계획](../../develop_plan/data/01_data_pipeline.md)
- 현재 Slice: Data 7 기술 검증 완료, Data 6 공동 검토 대기

## 목적

온통청년과 복지로 공식 API의 현재 요청 계약과 실제 응답 구조를 확인하고,
두 공식 API의 source Collector와 공유 실행·HTTP·Raw 저장 기반을 구축하고,
저장된 Raw를 공통 `ExtractedPolicy`와 `NormalizedProgram`으로 재처리하고
품질을 분류하며 합성 Fixture와 canonical Seed로 재현한다. 인증키와 운영
Raw가 Git, 로그, 예외, URL 기록과 Fixture에 남지 않도록 저장소 기준선을
유지하면서 제한된 실제 수집부터 Schema·Seed 검증까지 확인한다.

## Forest 범위

이 기록은 Data Pipeline Forest 전체의 실제 구현과 검증 결과를 Slice별로
누적한다. Data 0부터 Data 7의 기술 범위를 수행했다. 공통 실행·HTTP·Raw
기반, 두 source Collector·Extractor, 공통 Normalizer·Validator와 합성
Fixture·Seed를 구현하고 최종 회귀를 통과했다. Data 6의 Backend·Frontend
공동 승인은 대기 중이다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| Data 0 | completed | 두 API 실응답과 비밀정보 경계 확인 |
| Data 1 | completed | 공통 Collector·Registry·CLI와 HTTP Client 구현 |
| Data 2 | completed | 원본 byte 기반 Raw 계약·Schema·안전 저장 구현 |
| Data 3 | completed | 두 공식 API 제한 수집과 Raw 변환 검증 |
| Data 4 | completed | 공통 Extracted 계약과 두 Source Extractor 구현 |
| Data 5 | completed | Normalized Schema·Normalizer·품질 분류 구현 |
| Data 6 | in-progress | 합성 Fixture·Seed 완료, 소비자 공동 승인 대기 |
| Data 7 | completed | 전체 파이프라인·회귀·문서 최종 검증 완료 |

## 구현 내용

### Data 0 - 공식 자료와 로컬 자료 대조

2026-07-26 기준 공식 자료를 다시 확인했다.

- 온통청년 공식 제공목록은 `/opi/youthPlcyList.do`, `openApiVlak`,
  `pageIndex`, `display`를 안내한다.
- 온통청년 공식 이용방법은 XML 전송을 설명하지만 제공목록은 JSON 결과 보기를
  제공한다.
- 로컬 제공 자료는 `/go/ythip/getPlcy`, `apiKeyNm`, `pageNum`,
  `pageSize`, `rtnType=json`을 사용하며 실제 호출에 성공했다.
- 복지로 공식 명세는
  `/NationalWelfarelistV001`와 `/NationalWelfaredetailedV001`,
  `serviceKey`, 목록 `callTp=L`, 상세 `callTp=D`를 사용한다.
- 복지로 2025년 변경 공지는 온라인 신청 가능 여부와 관심주제 추가,
  미사용 필드 제거를 안내한다.

요청 계약, 필드, 코드와 자료 차이는
[API Source Profile](../../../data/source_profiles.md)에 기록했다.

### Data 0 - 참고 자료와 실응답 프로파일

비밀값을 출력하지 않고 참고 자료의 구조만 추출했다.

- 온통청년 JSON 실응답: 10건, 정책 항목 60개 필드
- 정책 항목 값: 모두 JSON string, null 없음, 16개 필드에서 빈 문자열 관찰
- 온통청년 코드 정의서: 제공기관, 제공방법, 승인상태, 신청·사업기간,
  결혼·소득·전공·취업·학력·특화 조건 코드 확인
- 복지로 v2.2 가이드: 목록·상세 요청과 응답 필드, 코드표와 오류 코드 확인

DOCX와 XLSX 참고 자료는 읽기 전용으로 유지했다. 비밀이 포함된 DOCX의
내용이나 키 값을 Markdown, Fixture와 테스트 출력에 복사하지 않았다.

### Data 0 - 실제 API 호출

Source Preflight 응답은 파일로 저장하지 않고 메모리에서 구조만 집계했다.
요청 URI와 query string은 출력하지 않았고 예외 메시지도 기록하지 않았다.

| 시각(Asia/Seoul) | Source ID | operation | 결과 |
| --- | --- | --- | --- |
| 2026-07-26 12:58:56 | `youthcenter-api` | 공식 제공목록 endpoint | 302 자동 추적 후 8080 연결 실패 |
| 2026-07-26 12:59:35 | `youthcenter-api` | 공식 제공목록 endpoint 재확인 | 302 자동 추적 후 8080 연결 실패 |
| 2026-07-26 13:00:06 | `bokjiro-central-welfare-api` | 복지 목록 1건 | HTTP 200, XML UTF-8 |
| 2026-07-26 13:00:15 | `bokjiro-central-welfare-api` | 선택 상세 1건 | HTTP 200, XML UTF-8 |
| 2026-07-26 후속 진단 | `youthcenter-api` | 공식 제공목록 endpoint, redirect 중지 | HTTP 302, HTTP 8080 root로 이동 |
| 2026-07-26 후속 진단 | `youthcenter-api` | `/go/ythip/getPlcy`, 1건 | HTTP 200, JSON |
| 2026-07-26 13:32:30 | `youthcenter-api` | `/go/ythip/getPlcy`, 10건 | HTTP 200, JSON 10건 |

인증키를 사용한 API 요청 합계는 온통청년 5회, 복지로 2회다. 원인 분리를
위한 온통청년 무인증 HEAD와 GET 연결 점검도 각각 1회 수행했다.
복지로 목록 응답의
`servId`를 상세 요청에 재사용했다. 두 복지로 응답에는 rate limit 관련
HTTP header가 없었다. 할당량을 보호하기 위해 잘못된 키나 파라미터를 이용한
오류 호출은 수행하지 않았다.

온통청년 최초 실패는 네트워크나 로그인 문제가 아니라 `HttpClient`가 공식
제공목록 endpoint의 302를 자동 추적해 외부에서 접근할 수 없는 8080 포트로
연결한 결과였다. 같은 키로 로컬 제공 계약을 사용하면 정상 JSON을 받았다.

### Data 0 - Git 비밀정보 경계

초기 점검에서 다음 문제를 확인했다.

- 루트 `.gitignore`가 없었다.
- `APIkey.txt`가 Git 추적 중이었고 1개 커밋 이력이 있었다.
- 실제 키가 포함된 로컬 참고 DOCX도 Git 추적 중이었고 1개 커밋 이력이
  있었다.

다음 재유입 방지 규칙을 추가했다.

```text
.env
.env.*
!.env.example
APIkey.txt
비밀 포함 로컬 참고 DOCX의 정확한 경로
runtime/raw/
data/runtime/raw/
```

두 비밀 파일은 로컬 원본을 삭제하거나 수정하지 않고 Git 인덱스에서만
제외했다. 이 조치는 과거 커밋의 비밀을 삭제하지 않으므로 두 API 키를
폐기·재발급해야 한다. 과거 이력 정리는 키 회전 후 저장소 관리자와 별도로
결정해야 하며 이 Slice에서 이력 재작성은 수행하지 않았다.

문서 비밀값 검사는 `BOKJIRO_API_KEY` 할당도 탐지하도록 확장했다. 별도
단위 테스트는 비밀 파일, `.env` 계열과 runtime Raw 후보가 ignore되고
`.env.example`은 예외로 남는지 확인한다.

### Data 1 - 공통 Collector 실행 구조

`collectors` 패키지에 source ID와 `collect()`를 요구하는 `Collector`
프로토콜을 추가했다. `CollectorRegistry`는 안정적인 kebab-case source ID와
0-argument factory를 연결하고, 중복·미등록·factory 결과의 ID 불일치를 설정
오류로 처리한다.

`python -m collectors --source SOURCE_ID`는 Registry에서 선택한 Collector를
실행한다. `--list-sources`도 제공한다. Data 1 완료 시점에는 실제 API
Collector를 등록하지 않아 기본 Registry가 비어 있었고 Mock Registry로
선택과 실행을 검증했다. Data 3에서 `youthcenter-api`와
`bokjiro-central-welfare-api`를 등록했다.

### Data 1 - 공통 HTTP Client

표준 라이브러리 기반 `HttpClient`와 주입 가능한 `HttpTransport`를 구현했다.
기본값은 Timeout 10초, 추가 재시도 최대 3회, 0.5초 지수 backoff, 요청 시작
간 최소 1초와 `cheongnyeon-alimi-collector` User-Agent다.

- Timeout·전송 오류와 5xx만 제한적으로 재시도
- 401·403, 429, 일반 4xx, 소진된 5xx, 예상 밖 상태를 별도 예외로 분류
- bytes 응답과 JSON·XML 파싱 제공
- 429는 호출량 보호를 위해 재시도하지 않음
- 자동 redirect를 차단해 query 인증정보가 다른 목적지로 전달되지 않게 함
- 모든 query 값과 URL user information을 `<redacted>`로 치환
- 오류 응답 본문과 하위 전송·파싱 예외 원문을 공통 예외에 포함하지 않음
- 주입한 sleep·monotonic clock으로 실제 대기 없이 간격과 backoff 검증

Data 1에서는 복지로 XML의 애플리케이션 결과 코드와 source 환경변수 로딩을
후속 source Collector 범위로 남겼다. 두 항목은 Data 3에서 구현했다. Data 1
자체에서는 외부 API를 추가 호출하지 않았다.

### Data 2 - Raw 모델과 실행 가능한 Schema

`RawPolicyDocument` Schema version `1.0.0`을 Python 모델과 Draft 2020-12
JSON Schema로 함께 구현했다. JSON 객체를 다시 직렬화하거나 XML tree를
문자열로 바꾸면 원문 byte가 달라질 수 있으므로 `raw_payload_base64`에는
HTTP body 원본 byte를 Base64로 저장한다. `content_hash`는 Base64 문자열이나
envelope가 아닌 디코딩한 원본 byte의 SHA-256이다.

Python 모델은 생성과 로드 시 다음을 함께 검증한다.

- Schema version, source ID, UUID hex document ID와 모든 required 필드
- Base64 payload, `byte_length`와 `sha256:<64 lowercase hex>` 일치
- timezone이 있는 `collected_at`과 200~299 `http_status`
- query·fragment·user information이 없는 HTTPS `source_url`
- 역할별 `external_id`와 `parent_document_id` 조건
- 추가 필드가 없는 JSON envelope

실패 응답은 정상 Raw 문서로 만들지 않는다. 응답 오류와 실행 실패 기록은
후속 Collector 실행 기록 범위로 분리한다.

### Data 2 - 전체·항목·상세 보존 경계

| 역할 | 보존 경계 | 연결 |
| --- | --- | --- |
| `list_response` | 목록 HTTP body 전체 | 관계 ID 없음 |
| `list_item` | 목록에서 분리한 한 항목 | 부모 `list_response.document_id` |
| `detail_response` | 상세 HTTP body 전체 | source-scoped `external_id` |

`list_response`와 `detail_response`가 권위 있는 HTTP 원문이다. `list_item`은
Extractor가 항목 단위로 처리하기 위한 파생 Raw이므로 부모 전체 응답을
반드시 참조한다. 목록 항목과 상세 응답은 같은 `source_id + external_id`로
연결하며 현재 온통청년은 `plcyNo`, 복지로는 `servId`를 사용한다.

### Data 2 - Runtime Raw 저장

최종 운영 Raw root를 `runtime/raw/`로 확정했다.

```text
runtime/raw/<source_id>/<document_role>/<UTC YYYY>/<MM>/<DD>/<document_id>.json
```

`RawDocumentStore`는 설정 root 아래에서만 저장·로드한다. 완성된 임시 파일을
같은 filesystem에서 hard link해 부분 envelope 노출을 방지하고 기존
`document_id` 파일은 덮어쓰지 않는다. 로드할 때 실제 resolve 경로가 root
밖이면 symlink를 포함해 거부한다. `data/runtime/raw/`는 사용하지 않지만
오입력된 Raw의 재유입 방지를 위해 기존 ignore를 유지한다.

Data 2 테스트는 관찰된 구조를 축소한 JSON 목록 전체·항목과 XML 상세 byte를
사용했다. 검토된 배포 Fixture는 Data 6 범위이므로 만들지 않았고 외부 API도
추가 호출하지 않았다.

### Data 3 - Source Collector와 설정

기본 Registry에 `youthcenter-api`와 `bokjiro-central-welfare-api` factory를
등록했다. factory는 실제 키 파일을 읽지 않고 각각
`YOUTHCENTER_API_KEY`, `BOKJIRO_API_KEY` 환경변수에서 인증키를 읽는다.
Timeout, 재시도와 요청 간격도 기존 계획 환경변수를 적용한다.

공통 `CollectionOptions`는 page 1~1000, 목록 limit 1~500, 상세 limit 0~5를
검증한다. CLI 기본값은 page 1, 목록 10건과 상세 3건이다. 성공 출력은
source ID, 요청·항목·상세·Raw 문서 수만 제공한다.

`.env.example`에는 안전한 placeholder와 HTTP 기본값을 추가했다. 별도
라이브러리를 추가하지 않았으므로 `.env` 파일을 자동 로드하지 않고 현재
프로세스 환경 또는 비밀 관리 수단으로만 값을 주입한다.

### Data 3 - 온통청년 Collector

검증된 `/go/ythip/getPlcy` 계약에 `apiKeyNm`, `pageNum`, `pageSize`,
`rtnType=json`을 전달한다. `resultCode=200`과 JSON 구조를 확인하고 목록이
비었거나 항목 `plcyNo`가 유효하지 않으면 Raw 저장 전에 실패한다.

목록 HTTP body 전체는 `list_response`, 최대 limit까지의 각 정책 객체는
결정적 JSON byte의 `list_item`으로 저장한다. 모든 항목은 부모 목록
`document_id`와 source-scoped `plcyNo`를 보존한다.

### Data 3 - 복지로 Collector

목록은 `callTp=L`, `pageNo`, `numOfRows`, `srchKeyCode=003`을 사용하고 상세는
`callTp=D`, `servId`를 사용한다. Encoding key가 주입돼도 한 번 decode한 뒤
공통 HTTP Client가 query를 한 번 encoding하도록 처리한다.

XML `resultCode=0`을 성공으로 보고 `30`·`31`은 인증, `22`는 할당량,
그 밖의 코드는 application 요청 오류로 분류한다. 목록의 직접 `servId`
항목을 최대 limit까지 Raw로 만들고, 중복을 제거한 첫 ID 중 detail limit만
상세 호출한다. 상세 응답 `servId`가 요청 ID와 다르면 저장하지 않는다.

두 Collector 모두 HTTP 상태 분류와 별도로 source payload 결과 코드를
확인한다. 응답 byte에서 요청 인증키의 원본·URL encoding·decoding 표현이
발견되면 Raw 저장 전에 파싱 오류로 중단한다.

### Data 3 - 실제 제한 수집

로컬 키 파일은 구현 의존성으로 사용하지 않고 이번 검증 PowerShell
프로세스에서 각 줄의 마지막 토큰만 해당 환경변수에 주입했다. 값은 출력하지
않았고 프로세스 실행 직후 환경변수를 제거했다.

| 시각(Asia/Seoul) | Source ID | 실제 요청 | 결과 |
| --- | --- | --- | --- |
| 2026-07-26 15:37:20 | `youthcenter-api` | 목록 1회, page 1, limit 10 | 항목 10건, Raw 11개 |
| 2026-07-26 15:37:31 | `bokjiro-central-welfare-api` | 목록 1회, 상세 3회 | 목록 10건, 상세 3건, Raw 14개 |

Data 3 실호출은 온통청년 1회와 복지로 4회다. Data 0부터 누적한 인증 API
요청은 온통청년 6회, 복지로 6회다. 이번 실행은 추가 retry 없이 모두 첫
시도에 성공했다.

저장된 25개 envelope를 `RawDocumentStore`로 다시 로드해 payload Hash와 길이를
검증했다. 역할별 결과는 온통청년 목록 전체 1·항목 10, 복지로 목록 전체
1·항목 10·상세 3이다. 부모 문서와 `external_id` 연결 오류, query·fragment·
user information이 있는 `source_url`, 실제 두 인증키와 일치하는 envelope·
payload는 모두 0건이었다. 두 source runtime 경로도 Git ignore임을 확인했다.

첫 일회성 관계 집계는 상세 문서를 항목 문서보다 먼저 순회하면서 아직 만들지
않은 항목 ID 집합과 비교해 오류 3건으로 잘못 표시했다. 전체 항목 ID 집합을
먼저 구성한 재검증에서는 관계 오류 0건이었다. 저장 문서나 Collector 관계
계약의 오류는 아니며 해당 임시 집계 코드는 저장하지 않았다.

### Data 4 - 공통 Extracted 계약

`ExtractedPolicy` Python 모델은 두 Extractor가 같은 텍스트 경계를 사용하도록
다음 값을 공통으로 제공한다.

- source ID와 표시 이름, source-scoped external ID
- 제목, 기관, 분류, 신청기간, 지역, 연령, 자격, 지원 내용과 신청 방법 원문
- 안전하게 선별한 공개 source URL과 최신 수집 시각
- 기여 Raw별 document ID, 역할, content hash, 수집 시각과 안전 endpoint
- 역할별 source 전체 필드를 담은 `extra.source_fields`

공통 선택 필드의 source 값이 없거나 빈 문자열이면 null을 사용하지만
`extra`에는 필드 부재와 빈 문자열을 원래 상태로 유지한다. 복지로 XML leaf는
한 번 나타나면 string, 반복되면 원문 순서의 string 배열로 보존한다. 이
계약은 Normalizer 입력용 내부 경계이며 Normalized Schema, Fixture, Seed,
Backend API와 Frontend 타입은 변경하지 않았다.

### Data 4 - 온통청년 Extractor

`YouthCenterExtractor`는 부모 목록 전체와 JSON 목록 항목을 검증한 뒤
`plcyNo`와 Raw external ID가 같은 항목만 추출한다. 제목·운영기관·대분류·
신청기간·지역 코드·연령·자격·지원 내용·신청 방법을 공통 필드로 전달한다.
운영기관이 비면 등록기관을 유지하고 `aplyYmd`가 비면 검증된
`aplyPrdSeCd`의 특정기간·상시·마감 의미를 전달한다.

목록 항목의 전체 60개 필드는 매핑 여부와 관계없이 `extra`에 보존한다.
따라서 대·중분류, 키워드, 제공방법·승인상태·신청기간과 자격 코드, 빈
문자열을 후속 단계에서 확인할 수 있다.

### Data 4 - 복지로 Extractor와 목록·상세 결합

`BokjiroExtractor`는 `source_id + servId`가 같은 목록과 상세만 결합한다.
상세가 있으면 상세 제목·주관부처·대상·선정기준·급여 내용을 우선하며 비거나
상세가 없으면 목록 제목·부처·요약을 유지한다. 중복 ID, 부모 목록이 없는
항목, 목록에 없는 상세와 payload·Raw metadata의 ID 불일치는 추출 오류다.

목록과 상세의 전체 leaf 값을 각각 보존한다. Data 3 Raw에서는 상세 3건의
`servSeCode`, `servSeDetailLink`, `servSeDetailNm`이 반복 배열이었고 목록
항목의 `intrsThemaArray`, `lifeArray`, `trgterIndvdlArray`에는 선택 누락이
있었다.

### Data 4 - 실제 Raw 재처리와 Source Profile

Data 3에서 저장한 runtime Raw 25개를 다시 로드해 외부 호출 없이
재처리했다.

| Source ID | 입력 | Extracted | 상세 결합 |
| --- | --- | ---: | ---: |
| `youthcenter-api` | 목록 전체 1·항목 10 | 10 | 해당 없음 |
| `bokjiro-central-welfare-api` | 목록 전체 1·항목 10·상세 3 | 10 | 3 |

온통청년은 10건 모두 60개 string 필드가 있었고 16개 필드에서 빈 문자열이
관찰됐다. 복지로 목록은 15개 필드 중 `intrsThemaArray` 1건,
`lifeArray` 2건, `trgterIndvdlArray` 5건이 누락됐다. 상세 3건은 19개 필드가
모두 존재하고 빈 값이 없었으며 3개 반복 leaf를 배열로 집계했다.

모든 정책에서 `extra`의 목록·상세 필드와 해당 Raw를 독립적으로 다시 파싱한
결과가 같았고 source field 보존 오류는 0건이었다. provenance ID·hash·source
연결 오류, 실제 인증키 일치와 불안전한 Extracted source URL도 모두 0건이었다.
추출 결과 20건은 JSON 직렬화 가능했고 runtime Raw 25개는 계속 Git ignore
상태였다.

Source Preflight와 Data 3 Raw의 온통청년 빈 값 수를 비교하면
`bizPrdBgngYmd`와 `bizPrdEndYmd`가 각각 8건에서 6건으로 달랐다. 필드·타입
변경은 아니므로 시점별 page 1 데이터 변화로 기록하고 빈 값 비율을 고정
계약으로 사용하지 않는다.

### Data 5 - NormalizedProgram 1.0.0

`NormalizedProgram` Python 모델과 Draft 2020-12 JSON Schema는 31개 필드와
Schema version `1.0.0`을 공유한다. 객체의 모든 key는 required이고 선택 단일
값 없음은 null, 복수 값 없음은 빈 배열이다. source ID, 표시 이름, external
ID와 기여 Raw provenance를 유지해 같은 external ID의 다른 소스와 원문을
추적할 수 있게 했다.

실제 복지로 관심주제가 여러 값을 가지므로 단일 `category` 후보를
`categories` 배열로 바꿨다. 또한 `always`와 `open`의 의미 충돌을 해소하기
위해 일정 유형 `application_schedule`과 수집 기준 상태
`application_status`를 분리했다.

### Data 5 - 공통 Normalizer

Normalizer는 API 필드명과 XML 태그를 알지 않고 Extracted 공통 필드만
사용한다.

- HTML tag·Entity, 앞뒤·연속 공백과 줄바꿈을 정리하되 문장 의미를 재작성하지
  않음
- 점·slash·8자리 날짜와 날짜 범위를 `YYYY-MM-DD`로 변환
- `상시`, `마감`, `예산 소진 시`의 일정·상태 의미를 분리
- 수집 시각의 Asia/Seoul 날짜로 기간의 open·closed·scheduled 판정
- 숫자가 명확한 연령 범위와 한쪽 경계만 0~150 안에서 구조화
- 시·도 축약과 승인된 예시만 표준 지역명으로 변환
- 다중 관심주제를 category enum 배열로 변환하고 중복 제거

행정구역 5자리 코드는 승인된 code-to-name 기준표가 없어 추정하지 않는다.
`region_text`는 유지하고 `regions=[]`과 `unmapped_region_code` 경고를 남긴다.
매핑되지 않은 명시적 category는 원문을 보존하면서 `other`와 경고를 사용하고
분류 자체가 없으면 빈 배열로 둔다.

### Data 5 - Schema Validator와 품질 분류

새 의존성을 추가하지 않고 표준 라이브러리 Validator로 현재 Schema가 사용하는
required·additionalProperties·type·enum·pattern·format·배열·local `$ref`
keyword를 검사한다. 날짜·연령 범위 순서와 선언한 품질 상태가 실제 판정과
일치하는지도 확인한다.

각 issue는 `$.title`, `$.regions`, `$.provenance[0]` 형태의 위치, 안정적인
code, 안전한 message와 warning·error severity를 가진다.

- `valid`: Schema와 주요 검색 필드가 모두 충족됨
- `partial`: Schema-valid지만 category·지역·연령·신청기간 누락 또는 선택
  파싱 경고가 있음
- `invalid`: Schema·핵심 필드·범위 관계·품질 상태 계약 위반

valid·partial은 `NormalizedProgram`을 유지하고 invalid는 candidate와 issue만
남겨 정상 결과와 분리한다.

개인정보·외부 원문이 없는 합성 valid·partial·invalid JSON Fixture 3개를
`tests/fixtures/normalized/`에 두고 Schema와 품질 분기를 검증했다. 실제
API 원문을 재배포하는 Data 6 Fixture와는 역할을 분리한다.

### Data 5 - 실제 Raw 재처리

외부 API를 추가 호출하지 않고 runtime Raw 25개를 다시 로드해
Raw → Extracted → Normalized → Validated 흐름을 실행했다.

| Source ID | Extracted | valid | partial | invalid |
| --- | ---: | ---: | ---: | ---: |
| `youthcenter-api` | 10 | 0 | 10 | 0 |
| `bokjiro-central-welfare-api` | 10 | 0 | 10 | 0 |

20건이 모두 partial인 주된 이유는 표준 지역명이 없기 때문이다. 온통청년
10건은 지역 코드만 제공하고 복지로 10건은 공통 지역 정보가 없었다. 복지로는
연령과 신청기간도 10건 모두 없었고 category 1건이 누락됐다. 온통청년의
명시 상태는 closed 6건·open 4건으로 변환됐다.

20건의 Python 모델과 JSON Schema 오류, Raw provenance ID·hash 연결 오류는
모두 0건이었고 전체 결과는 JSON 직렬화 가능했다. partial을 valid로 가장하지
않았으며 실제 수집 호출은 0회다.

### Data 5 - Backend·Frontend 영향

현재 저장소에는 Normalized를 소비하는 Backend 응답 모델·DB Schema와
Frontend 타입·Mock이 없어 직접 변경할 파일은 없다. 다만 단일 category 대신
배열, 신청 일정·상태 분리, 모든 key required, null·빈 배열과 provenance는
향후 소비자 계약에 영향을 준다. Data 6의 Fixture·Seed를 소비 계약으로
승인하기 전에 Backend·Frontend 담당과 공동 검토해야 한다. 승인 전
Normalized 1.0.0은 Data 파이프라인 내부 기준안이다.

### Data 6 - 재배포 경계

2026-07-26 기준 복지로 공공데이터포털은 중앙부처 복지서비스 API의
이용허락범위를 `제한 없음`으로 표시한다. 온통청년은 공식 이용방법에서
회원가입·인증키 신청·담당자 승인을 요구하고, 현행 이용약관은 대량 이용을
별도 계약으로 두며 서비스에서 얻은 게시 자료의 무단 상업적 가공·판매를
제한한다.

온통청년 API 원문의 Git 재배포 범위는 명시적으로 확인되지 않았다. 두
소스의 테스트 경계를 일관되게 유지하고 개인정보·시점 의존성도 배제하기
위해 실제 runtime Raw와 정책 내용은 Fixture에 복사하지 않았다. 대신 실제
응답에서 관찰한 JSON·XML 역할과 필드 이름만 재현한 합성 Raw를 사용한다.
모든 ID는 `SYN-`, URL은 `fixture.invalid`, 내용은 합성 문구다.

### Data 6 - Fixture와 canonical Seed

고정 문서 ID·수집 시각·payload를 가진 합성 Raw 8개에서 같은 파이프라인으로
Extracted 5건을 만들었다. Normalized 결과는 valid 2건·partial 2건·invalid
1건이다.

| 계층 | 경로 | 결과 |
| --- | --- | ---: |
| Raw | `data/fixtures/raw/` | 온통청년 4·복지로 4 |
| Extracted | `data/fixtures/extracted/policies.json` | 5 |
| Normalized | `data/fixtures/normalized/programs.json` | 4 |
| rejected | `data/fixtures/rejected/programs.json` | 1 |
| Seed | `data/seeds/initial_programs.json` | 4 |

Normalized Fixture와 Seed는 byte가 같은 JSON 배열이다. Seed는 Schema-valid
valid·partial만 포함하고 필수 제목이 없는 invalid는 `$.title`,
`schema_type`, `error` 사유와 candidate를 rejected에 보존한다.

대표 사례는 source 2종, 목록 전용·상세 결합, 지역·연령 있음과 없음,
특정기간·상시, open·closed, 다중 category, null·빈 배열과 Raw provenance를
포함한다. CSV importer 요구나 소비 코드가 없어 파생 CSV는 만들지 않았다.

### Data 6 - 결정적 재생성과 오프라인 검증

`scripts/build_data_fixtures.py --write`는 합성 정의에서 Raw부터 Seed까지
12개 JSON 파일을 다시 만들고 `--check`는 committed byte와 예상 파일 집합을
검사한다. 외부 API, 인증키와 `runtime/raw/`를 읽지 않는다.

Data 6 테스트 9건은 다음을 확인한다.

- 12개 산출물의 결정적 byte 일치와 추가·누락 파일 탐지
- Raw 역할·관계·Hash와 합성 host·비밀정보 경계
- Raw → Extracted 5건 재현
- Seed 4건의 Normalized Schema와 valid 2·partial 2 분류
- source·null·빈 배열·enum·날짜·다중 category·상세 provenance 보존
- invalid의 정확한 오류 위치와 정상 Seed 제외
- 외부 네트워크 호출 없음, CSV 미생성과 인증 파라미터·개인 식별자 부재

### Data 6 - Backend·Frontend 공동 검토 상태

[Fixture와 Seed 계약](../../../data/fixture_seed_contract.md)에 Backend와
Frontend가 확인할 적재·Mock·nullable·배열·품질·provenance 항목을
기록했다.

Data 기술 검토와 자동 검증은 완료했다. 그러나 현재 저장소에는 Backend
모델·Importer, Frontend TypeScript 타입·Mock, 담당 Issue·PR이나 두 영역의
승인 기록이 없다. Data 담당이 공동 승인을 대신 기록하지 않으며 실제 승인
또는 소비 테스트가 생길 때까지 Data 6 상태를 `in-progress`로 유지한다.

### Data 7 - 커밋된 Fixture 종단 간 재생

Data 7에서는 생성 함수의 중간 결과가 아니라 Git에 저장된 합성 Raw
envelope 8개를 직접 로드하는 통합 테스트를 추가했다.

```text
Committed Raw 8
→ Extracted 5
→ Normalized·Validated: valid 2, partial 2, invalid 1
→ canonical Seed 4 + rejected 1
```

accepted 결과의 전체 객체 배열이 `initial_programs.json`과 같고 invalid
candidate·issue 배열이 `rejected/programs.json`과 같은지 확인한다. 이
검증으로 Raw 관계·Hash, source mapping, Normalizer, Validator, 품질 분리와
Seed 직렬화가 하나의 오프라인 흐름에서 연결됨을 확인했다.

운영 Raw 25개도 외부 호출 없이 다시 처리했다. Extracted 20건과 partial
20건을 만들었고 invalid와 error severity issue는 0건이었다. Data 7에서
실제 API 요청은 추가하지 않았으므로 누적 호출 횟수는 기존 기록과 같다.

### Data 7 - Forest 완료 감사

Fixture 결정성 12개 파일, 전체 회귀 81건, 문서 검증, diff 공백 검사,
Git ignore와 비밀값 대조를 통과했다. Data 기준 문서, 실행 가능한 Schema,
Fixture·Seed와 개발 기록의 필드·품질·재배포 경계도 일치한다.

Data 7의 기술 완료 기준은 모두 충족했다. canonical Fixture·Seed까지
제공하는 결과는 팀에 의미가 있으므로 기존 `CHANGELOG.md` Data 항목을
확장했다.

Forest 전체는 완료 처리하지 않는다. Data 6의 Backend·Frontend 공동 승인과
그에 따른 importer·Mock 또는 명시적 승인 기록이 아직 없기 때문이다.
Data 7 이후 남은 첫 완료 게이트는
[Fixture와 Seed 계약](../../../data/fixture_seed_contract.md)의 두 pending
행을 실제 검토 결과로 갱신하는 것이다.

## 주요 변경 파일

- `.gitignore`
- `.env.example`
- `collectors/__init__.py`
- `collectors/__main__.py`
- `collectors/base.py`
- `collectors/bokjiro.py`
- `collectors/cli.py`
- `collectors/config.py`
- `collectors/errors.py`
- `collectors/extracted.py`
- `collectors/extractors.py`
- `collectors/http.py`
- `collectors/normalized.py`
- `collectors/normalizer.py`
- `collectors/profile.py`
- `collectors/raw.py`
- `collectors/registry.py`
- `collectors/storage.py`
- `collectors/source_common.py`
- `collectors/youthcenter.py`
- `collectors/validation.py`
- `data/fixtures/raw/`
- `data/fixtures/extracted/policies.json`
- `data/fixtures/normalized/programs.json`
- `data/fixtures/rejected/programs.json`
- `data/seeds/initial_programs.json`
- `data/schema/normalized_program.schema.json`
- `data/schema/raw_policy_document.schema.json`
- `scripts/build_data_fixtures.py`
- `scripts/validate_docs.py`
- `tests/test_collectors_cli.py`
- `tests/test_collectors_http.py`
- `tests/test_extractors.py`
- `tests/test_data_fixtures.py`
- `tests/test_normalization.py`
- `tests/fixtures/normalized/valid.json`
- `tests/fixtures/normalized/partial.json`
- `tests/fixtures/normalized/invalid.json`
- `tests/test_raw_storage.py`
- `tests/test_source_collectors.py`
- `tests/test_validate_docs.py`
- `tests/test_secret_boundaries.py`
- `docs/data/source_profiles.md`
- `docs/data/data_sources.md`
- `docs/data/collection_policy.md`
- `docs/data/data_schema.md`
- `docs/data/fixture_seed_contract.md`
- `docs/data/README.md`
- `docs/development/develop_plan/data/01_data_pipeline.md`
- `docs/development/develop_plan/README.md`
- `docs/development/development_notes/README.md`
- `docs/index.md`
- `docs/operations/collector.md`
- `docs/operations/README.md`
- `README.md`

## 설계 결정

### 공식 선언보다 검증된 실동작을 우선한다

온통청년 공식 제공목록의 다른 endpoint는 보유 키로 정상 응답하지 않았고
로컬 제공 계약은 같은 키로 정상 JSON을 반환했다. Collector 기준은
`live-verified`인 `/go/ythip/getPlcy`로 확정하고
`/opi/youthPlcyList.do`는 재검토 대상으로 기록했다.

### 오류 확인을 위해 할당량을 소비하지 않는다

복지로 공식 가이드에 결과 코드가 있고 개발계정 트래픽이 제한되어 있으므로
의도적인 잘못된 인증이나 파라미터 호출은 하지 않았다. 실제 Collector는
HTTP 상태와 XML 결과 코드를 함께 분류해야 한다.

### Raw string을 조기에 타입 변환하지 않는다

복지로 XML leaf 값과 온통청년 과거 JSON 정책 필드는 Raw 단계에서 string으로
관찰됐다. 숫자·날짜처럼 보이는 값도 Extractor와 Normalizer 계약이 정해질
때까지 원문 string으로 보존한다.

### 인덱스 제외와 키 회전을 별도 조치로 본다

`git rm --cached`와 `.gitignore`는 재유입을 막지만 과거 이력의 키를
무효화하지 않는다. 현재 키는 노출된 것으로 간주하고 재발급해야 한다.
저장소 이력 재작성과 협업자 동기화는 사용자의 별도 승인 없이 수행하지 않는다.

### 공통 Client는 redirect와 오류 payload를 자동 해석하지 않는다

Data 0에서 확인한 온통청년 302처럼 redirect 목적지가 안전하거나 유효하다고
가정할 수 없으므로 공통 Client는 3xx를 자동 추적하지 않는다. 또한 HTTP
Client는 응답 본문을 예외에 넣지 않는다. 소스별 결과 코드와 안전하게
선별한 진단 정보는 실제 Collector가 해당 소스 계약에 따라 처리한다.

### 원문 byte와 파생 항목을 같은 증거 수준으로 취급하지 않는다

JSON/XML 파싱 결과는 원문 의미를 보존해도 byte 표현을 보존하지 못한다.
따라서 목록·상세 HTTP body 전체는 Base64로 원본 byte를 저장하고 Hash의
기준으로 삼는다. 항목별 Raw는 부모 전체 응답을 추적할 수 있는 파생 문서로
명시해 원본 HTTP body처럼 가장하지 않는다.

### Raw Schema는 서비스 소비자 계약과 분리한다

이번 required·null·enum 규칙은 Collector 재처리를 위한 Raw 내부 계약이다.
`NormalizedProgram`, Fixture, Seed, Backend API와 Frontend 타입은 변경하지
않았다. 향후 Backend가 Raw를 적재하거나 Frontend 관리자 기능이 Raw를
소비하면 영향받는 계약을 공동 검토한다.

### 실제 키 파일과 Collector 설정을 결합하지 않는다

`APIkey.txt`는 현재 로컬 검증 자료일 뿐 배포 계약이 아니다. Collector
factory는 합의된 환경변수만 사용하고 `.env` 자동 로딩이나 로컬 파일 parsing을
구현하지 않는다. 이 경계로 키 파일 형식, 경로와 배포 환경을 분리한다.

### HTTP 성공과 source payload 성공을 모두 요구한다

두 API는 HTTP 200 안에서도 application 결과 코드를 제공한다. 공통
`HttpClient`의 HTTP 오류 분류만으로 성공을 판단하지 않고 source Collector가
온통청년 `resultCode`와 복지로 XML `resultCode`를 확인한 뒤에만 Raw를 만든다.

### 공통 필드 null과 source 원문의 빈 상태를 분리한다

Normalizer가 소스 필드명을 알지 않도록 공통 선택 필드는 값 없음과 빈 문자열을
null로 전달한다. 동시에 `extra.source_fields`에는 필드 부재, 빈 string과
반복 배열을 그대로 남겨 source 구조와 원문 상태를 잃지 않는다. 매핑된 필드도
전체 source 필드 집합에 포함해 추출 규칙 변경 시 다시 확인할 수 있게 한다.

### Extracted provenance는 결과 하나에 기여한 모든 Raw를 가리킨다

목록 항목만 가리키면 HTTP 원문인 부모 목록 전체를 놓치고, 복지로 상세만
가리키면 목록에서만 제공되는 값을 놓친다. 따라서 목록 전체·항목과 선택적인
상세의 ID·역할·hash·시각·endpoint를 모두 보존하고 Extracted 수집 시각은
그중 가장 최근 시각으로 정한다.

### 다중 category를 단일 enum으로 축약하지 않는다

복지로 실제 목록은 쉼표로 구분된 여러 관심주제를 제공하고 온통청년도
금융·복지·문화가 결합된 분류를 가진다. 한 값만 고르는 우선순위는 검색 의미를
잃으므로 `categories` 배열로 보존하고 미매핑 원문은 `other`와 warning으로
표시한다.

### 신청 일정 유형과 현재 상태를 분리한다

`always`는 기간의 형태이고 `open`은 특정 기준일의 상태다. 두 의미를 한 enum에
섞지 않고 schedule과 status로 나눈다. 상태 비교가 필요하면 실행 시각이 아닌
입력의 `collected_at`을 Asia/Seoul 날짜로 바꿔 결정해 재실행 결과를
결정적으로 유지한다.

### 선택 필드 파싱 실패는 partial로 보존한다

지역 코드표 부재나 유효하지 않은 선택 날짜 하나 때문에 정책 전체를
invalid로 버리지 않는다. 원문 text와 위치가 있는 warning을 보존하고 null·빈
배열로 표시한다. 제목·출처·provenance 또는 Schema 위반만 정상 결과에서
완전히 분리한다.

### 실제 원문 대신 source-shaped 합성 Raw를 배포한다

복지로 이용허락이 제한 없음이어도 실제 응답은 시점에 따라 바뀌고,
온통청년은 API 원문 재배포 범위가 명확하지 않다. 한 소스만 실제 원문으로
두면 테스트 증거 수준도 달라진다. 따라서 field·문서 역할·목록 상세 연결은
관찰 계약을 재현하되 정책 내용·ID·URL·시각은 합성·고정한다.

### partial은 rejected가 아니라 소비 가능한 품질 상태다

복지로처럼 지역·연령·신청기간이 없는 정책도 Schema를 통과하고 확인 가능한
내용이 있다. canonical Seed는 valid와 partial을 포함하고 invalid만
rejected로 분리한다. Backend·Frontend는 partial 처리 방식을 검토해야 하며
누락을 기본값으로 숨기지 않는다.

### 합의되지 않은 CSV를 만들지 않는다

JSON은 null·배열·enum·날짜·provenance를 그대로 보존한다. 현재 CSV importer
요구가 없으므로 중복 표현을 추가하지 않고 normalized Fixture와 Seed가 같은
canonical JSON 계약을 사용한다.

## 검증 결과

- 복지로 최소 실호출: 목록 1회, 상세 1회 성공
- 온통청년 실호출: `/go/ythip/getPlcy`에서 JSON 1건과 10건 요청 성공
- Python: 로컬 `uv`가 관리하는 CPython 3.14.5 사용, 새 설치 없음
- 단위·CLI 통합 테스트:
  `python -m unittest discover -s tests -p "test_*.py" -v`
  Data 0~7 전체 81건 통과
- Raw 계약 테스트: JSON·XML Schema 사례, Python·Schema 필드 일치, byte
  왕복, Hash 결정성·변조 탐지, 역할 연결, URL·저장 경로·덮어쓰기 경계 11건
  통과
- Raw 검증은 새 패키지 없이 표준 라이브러리와 Schema에서 사용하는
  Draft 2020-12 keyword 계약 assertion으로 수행
- Source Collector Mock 테스트: 환경변수, page·limit, JSON·XML 정상,
  빈 목록, 인증·할당량·application 오류, 형식 오류, 키 반사, 상세 ID 불일치,
  복지로 key encoding과 상세 limit 11건 통과
- Extractor Mock 테스트: 공통 필드 매핑, 선택 필드 fallback, 신청기간 코드·
  연령 text, 복지로 목록·상세 결합, 반복 XML 배열, 누락·빈 값 프로필,
  external ID 불일치와 전체 source field·provenance 보존 6건 통과
- Normalizer·Validator 테스트: HTML·Entity·공백, 실제 8자리 날짜, 일정·상태,
  연령 경계, 지역 alias·미매핑 코드, 다중 category, null·빈 배열, Python·
  Schema 왕복, 합성 JSON Fixture와 오류 위치, valid·partial·invalid 분리
  13건 통과
- Fixture·Seed 테스트: 합성 Raw·Extracted·Normalized 재생, committed byte와
  커밋된 Raw부터 Seed·rejected까지의 종단 간 일치,
  Schema, source·null·배열·enum·날짜·provenance, rejected 분리, 네트워크
  독립성, CSV 미생성과 비밀·개인 식별자 부재 10건 통과
- 결정적 산출물 검사:
  `python scripts/build_data_fixtures.py --check` 12개 파일 통과
- 실제 호출 통합 검증: 온통청년 1회와 복지로 4회 성공, Raw 25개 재로드와
  관계·비밀·안전 URL·Git ignore 검증 통과
- 실제 Raw 재처리: 추가 외부 호출 없이 두 소스 각 10건, 총 20건 추출,
  복지로 상세 3건 결합, source field·provenance 보존과 JSON 직렬화 검증 통과
- 실제 전체 흐름: Raw 25개에서 Normalized 20건 생성, valid 0·partial 20·
  invalid 0, Schema·provenance 오류 0건
- 문서 검증: `python scripts/validate_docs.py` 통과
- diff 공백 오류 검사: `git diff --check` 통과
- Git 상태: 두 비밀 파일 모두 추적 대상 아님, 두 경로 모두 ignore 확인
- 비밀값 검색: ignore 대상 비밀 파일을 제외한 Git 포함 후보 101개를 실제 두
  키 값과 대조했고 일치 파일 0개
- 임시 산출물: Source Preflight 임시 스크립트와 테스트가 생성한 Python 3.14
  bytecode 제거

## 남은 작업

- 온통청년 오류 payload 확인
- 온통청년 계정별 공식 호출 한도 확인
- 두 API 키 폐기·재발급
- 필요하면 저장소 관리자와 과거 Git 이력 정리 방식 결정
- 합성 Fixture·Seed의 category 배열, application schedule·status, required
  key·null·빈 배열·provenance를 Backend·Frontend가 실제 소비 관점에서 승인
- 온통청년 지역 코드를 표준 이름으로 바꿀 공식·버전 고정 code table 결정
- 현재 NTFS runtime 경로의 hard link 저장은 실호출 25개에서 성공함. 다른
  운영 filesystem이 hard link를 지원하지 않으면 부분 저장 대신 안전하게
  실패하므로 배포 환경에서 재검증 필요
- 합의된 Python 의존성 manifest가 생기면 표준 Draft 2020-12 validator를
  추가해 현재 표준 라이브러리 keyword assertion과 교차 검증
- 온통청년 계정별 숫자 호출 한도와 실제 오류 payload는 여전히 미확인
- 복지로 실제 오류·빈 element 경계는 할당량 보호를 위해 Mock으로만 검증
