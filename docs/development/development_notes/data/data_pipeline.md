# Data Pipeline Forest 개발 기록

## 작업 정보

- 기간: 2026-07-26
- 담당 영역: Data
- 상태: in-progress
- 브랜치: `feature/data/pipeline-foundation`
- 관련 계획:
  [Data Pipeline Forest 개발 계획](../../develop_plan/data/01_data_pipeline.md)
- 현재 Slice: Data 1 완료

## 목적

온통청년과 복지로 공식 API의 현재 요청 계약과 실제 응답 구조를 확인하고,
두 소스 Collector가 공유할 안전한 실행·HTTP 기반을 구축한다. 인증키와 운영
Raw가 Git, 로그, 예외, URL 기록과 Fixture에 남지 않도록 저장소 기준선을
유지한다.

## Forest 범위

이 기록은 Data Pipeline Forest 전체의 실제 구현과 검증 결과를 Slice별로
누적한다. 현재는 Data 0과 Data 1을 수행했다. 공통 Collector 실행 계약과
HTTP 기반까지만 구현했으며 실제 소스 Collector, Raw 모델, Extractor,
Normalizer, Schema, Fixture와 Seed는 시작하지 않았다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| Data 0 | completed | 두 API 실응답과 비밀정보 경계 확인 |
| Data 1 | completed | 공통 Collector·Registry·CLI와 HTTP Client 구현 |
| Data 2 | pending | 미착수 |
| Data 3 | pending | 미착수 |
| Data 4 | pending | 미착수 |
| Data 5 | pending | 미착수 |
| Data 6 | pending | 미착수 |
| Data 7 | pending | 미착수 |

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
실행한다. `--list-sources`도 제공한다. 이 Slice에는 실제 API Collector를
등록하지 않았으므로 기본 Registry는 비어 있다. Mock Registry를 주입한 CLI
테스트로 source 선택과 실행을 검증했으며 실제 `youthcenter-api`와
`bokjiro-central-welfare-api` 등록은 Data 3·4에서 수행한다.

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

복지로 XML의 애플리케이션 결과 코드는 공통 HTTP 상태가 아니므로 Data 4
소스 Collector에서 분류한다. 환경변수 로딩도 각 소스 Collector가 실제
인증 파라미터를 구성하는 Data 3·4 범위로 남겼다. 이 Slice에서는 외부 API를
추가 호출하지 않았다.

## 주요 변경 파일

- `.gitignore`
- `collectors/__init__.py`
- `collectors/__main__.py`
- `collectors/base.py`
- `collectors/cli.py`
- `collectors/errors.py`
- `collectors/http.py`
- `collectors/registry.py`
- `scripts/validate_docs.py`
- `tests/test_collectors_cli.py`
- `tests/test_collectors_http.py`
- `tests/test_validate_docs.py`
- `tests/test_secret_boundaries.py`
- `docs/data/source_profiles.md`
- `docs/data/data_sources.md`
- `docs/data/collection_policy.md`
- `docs/data/README.md`
- `docs/development/develop_plan/data/01_data_pipeline.md`
- `docs/development/develop_plan/README.md`
- `docs/development/development_notes/README.md`
- `docs/index.md`

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

## 검증 결과

- 복지로 최소 실호출: 목록 1회, 상세 1회 성공
- 온통청년 실호출: `/go/ythip/getPlcy`에서 JSON 1건과 10건 요청 성공
- Python: 로컬 `uv`가 관리하는 CPython 3.14.5 사용, 새 설치 없음
- 단위·CLI 통합 테스트:
  `python -m unittest discover -s tests -p "test_*.py" -v`
  Data 0·1 전체 30건 통과
- 문서 검증: `python scripts/validate_docs.py` 통과
- diff 공백 오류 검사: `git diff --check` 통과
- Git 상태: 두 비밀 파일 모두 추적 대상 아님, 두 경로 모두 ignore 확인
- 비밀값 검색: ignore 대상 비밀 파일을 제외한 Git 포함 후보 54개를 실제 두
  키 값과 대조했고 일치 파일 0개
- 임시 산출물: Source Preflight 임시 스크립트와 테스트가 생성한 Python 3.14
  bytecode 제거

## 남은 작업

- 온통청년 오류 payload 확인
- 온통청년 계정별 공식 호출 한도 확인
- 두 API 키 폐기·재발급
- 필요하면 저장소 관리자와 과거 Git 이력 정리 방식 결정
- Raw 저장 Slice에서 최종 runtime Raw 경로 확정
- Data 2에서 Raw 계약과 저장 구현
- Data 3·4에서 실제 source Collector 등록과 환경변수 로딩 구현
