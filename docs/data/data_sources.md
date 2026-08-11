# 데이터 소스

## 문서 상태

- 상태: 기준선
- 현재 구현 상태: 온통청년·복지로 API와 천안청년센터 승인 웹 Collector,
  Runtime replay·PostgreSQL 적재와 제한 actual 검증 완료

이 문서는 프로젝트에서 사용할 데이터 소스의 등록 기준과 현재 확인 상태를
정의한다. 특정 Forest의 수집 건수와 구현 범위는
[Data Pipeline Forest 계획](../development/develop_plan/data/01_data_pipeline.md)에서
관리한다.
실제 엔드포인트, 응답 형식과 이용 조건은 Collector 변경이나 운영 확대 전에
공식 자료와 제한된 실제 응답으로 다시 확인한다.

## 현재 소스 후보

| 소스 | 계획 식별자 | 유형 | 상태 |
| --- | --- | --- | --- |
| 온통청년 청년정책 API | `youthcenter-api` | 공식 API | JSON 목록 10건 Raw 수집 확인 |
| 복지로 중앙부처 복지서비스 API | `bokjiro-central-welfare-api` | 공식 API | XML 목록 10건·상세 3건 Raw 수집 확인 |
| 천안청년센터 이음 공지 | `cheonan-youthcenter-web` | 공개 웹 | 공지 674번 actual Raw → PostgreSQL·API 확인 |

두 API 인증키는 확보된 상태지만 키 값은 문서나 Git에 기록하지 않는다.
현재 로컬 작업 트리의 인증키 파일과 인증키가 포함된 참고 문서는 비밀 포함
자료이므로 Fixture나 커밋 대상이 아니다. 웹 Source의 실제 원문 HTML·이미지도
Git에 넣지 않고 합성·최소 구조 Fixture만 사용한다.

현재 구현은 두 공식 API와 승인 웹 Source의 제한 Collector·Extractor·Runtime
replay·정규화·PostgreSQL 적재를 포함한다. 웹 Source의 Source 전용 section을
공통 조건 필드로 승격하는 작업은 Integration 08 DTL4-4에서 진행한다.
구체적인 수집 건수와 결정 게이트는
[Data Pipeline Forest 계획](../development/develop_plan/data/01_data_pipeline.md)을
따른다.
요청 파라미터, 실제 응답 필드와 호출 결과는
[API Source Profile](source_profiles.md)에서 관리한다.

## 지역 청년정책 Source inventory

Data 05는 사용자 제공 XLSX의 17개 지역 포털 URL을
[`regional_youth_policy_sources.json`](../../data/reference/regional_youth_policy_sources.json)으로
변환해 실행 기준으로 사용한다. 구조와 허용 상태는
[`regional_youth_policy_source_inventory.schema.json`](../../data/schema/regional_youth_policy_source_inventory.schema.json)이
검증한다.

RYP1은 17개 모두의 상세 identity를 재검증해 13개 승인, 3개 차단, 1개 제외로
확정했다. 승인 Source는 서버 HTML 8개, 공개 JSON 1개(경북), Browser 4개
(서울·강원·충북·제주)로 분리한다. 경북은 `/policy/list.json`과
`/policy/detail.modal`을 제한 호출하며, robots의 `/policy/list.tc/` 규칙은 실제
목록·JSON·modal 경로와 일치하지 않는다. 화면 discovery가 성공해도 robots 허용
경계가 없는 세종·경기·충남은 운영 collection을 승인하지 않는다.

Schema `1.1.0`은 `browser_access`, discovery 상태, collection mode, interaction
budget, 재현 action profile과 상세 표본 identity 또는 실패 이유를 검증한다.

홈 URL은 Source 발견의 필수 시작점이다. 최초 등록과 drift 복구 때 Browser가
메뉴·검색·select·tab·pagination을 제한 탐색해 action profile을 만들고, 운영
Collector는 profile을 재사용한다. 매 실행마다 홈이나 외부 인터넷을 무제한
재귀 순회하지 않는다.

inventory의 관할 라벨은 제공 자료의 광주·전남 분리 17개를 보존한다. 현재
행정구역 기준 `kr-bjd-20260803`은 광주 `2900000000`과 전남 `4600000000`을
퇴역으로, `전남광주통합특별시(1200000000)`를 활성으로 관리한다. Source
RYP1에서 기존 광주 센터가 연결하는 현행 공식 통합 플랫폼을 확인해 광주
Source를 활성 통합 코드 `1200000000`으로 연결했다. 전남 구 포털은 robots가
홈만 허용하고 현행 통합 플랫폼으로 대체되어 `rejected`로 두며 퇴역 코드
lineage를 유지한다. 실제 Policy region rule은 공식 원문의 시행·대상 관할을
확인한 뒤 기존 행정구역 계약에 따라 생성한다.

승인 여부는 원문·이미지 재배포 허가를 뜻하지 않는다. 명시적 개방 라이선스가
없는 Source는 최소 정책 사실과 provenance만 Runtime에서 처리하며 실제 HTML,
이미지와 첨부파일을 Git에 저장하지 않는다.

## 온통청년 API

### 현재 검증 요청 기준

- 인증키는 `YOUTHCENTER_API_KEY` 환경변수에서 읽는다.
- HTTPS `GET /go/ythip/getPlcy`를 사용한다.
- 인증 파라미터는 `apiKeyNm`, 페이지 파라미터는 `pageNum`과
  `pageSize`다.
- JSON 응답은 `rtnType=json`으로 요청한다.
- API 응답은 원본 형태로 보존한다.
- 응답 항목은 공통 `RawPolicyDocument`로 감싼다.
- Collector가 정규화된 정책을 직접 반환하지 않는다.

### 공식 자료와의 차이

로컬 참고 자료와 2026-07-26 실호출에서 다음 계약을 확인했다.

```text
endpoint: /go/ythip/getPlcy
authentication parameter: apiKeyNm
pagination: pageNum, pageSize
response selector: rtnType
```

반면 [공식 제공목록](https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiDoc/47)의
요청 예시는 다음 계약을 사용한다.

```text
endpoint: /opi/youthPlcyList.do
authentication parameter: openApiVlak
pagination: pageIndex, display
```

공식 이용방법은 XML 전송을 설명하지만 공식 제공목록은 JSON 결과 보기를
제공한다. 보유 키를 `openApiVlak`로 전달한 공식 제공목록 endpoint는
HTTP 302로 외부에서 접근할 수 없는 HTTP 8080 포트에 redirect했다.

같은 키를 `apiKeyNm`으로 전달한 `/go/ythip/getPlcy`는 HTTP 200,
`application/json`과 정책 10건을 반환했다. 따라서 현재 Collector 계약은
실제 동작이 확인된 `/go/ythip/getPlcy`를 사용하고 공식 제공목록의 다른
endpoint는 새 키 또는 gateway 수정이 확인될 때 다시 검토한다.

### 이용·재배포 검토

2026-07-26 기준
[공식 OPEN API 이용방법][youth-api-guide]은 회원가입, 인증키 신청과 담당자
승인을 요구한다. [현행 이용약관][youth-terms]은 대량 이용을 별도 계약
대상으로 두고 서비스에서 얻은 게시 자료의 무단 상업적 가공·판매를
제한한다.

API 정책 원문의 Git 재배포 범위가 별도로 명확하지 않으므로 운영 Raw와 실제
정책 내용을 Fixture·Seed에 포함하지 않는다. 테스트 자료는 source 필드
구조와 경계만 재현한 합성 데이터다.

### 남은 확인 사항

- 정책 상세 원문 URL의 안정성과 접근 조건
- 오류 응답, 호출 제한과 재시도 가능 상태 코드
- API 응답 원문의 비상업적 재배포와 출처 표기 조건
- 응답에 개인정보 또는 저장을 제한해야 하는 필드가 있는지 여부

현재 숫자 호출 한도는 공식 공개 페이지에서 확인하지 못했다. 대량 이용과
과도한 트래픽 제한은 공식 이용약관을 따르며 단위 테스트에서 실제 API를
호출하지 않는다.

## 복지로 중앙부처 복지서비스 API

### 확인된 기준

- 인증키는 `BOKJIRO_API_KEY` 환경변수에서 읽는다.
- 제공 기관은 한국사회보장정보원이며 데이터는 복지로에서 제공한다.
- 데이터 형식은 XML이다.
- 목록과 상세 endpoint를 분리한다.
- HTTPS를 사용한다.
- 목록에서 선택한 최소 사례에 대해서만 상세를 호출한다.
- 목록과 상세 Raw를 각각 보존하고 source-scoped 서비스 ID로 연결한다.
- 개발계정 호출량을 고려해 실제 호출을 단위 테스트와 분리한다.

2026-07-26에 [공공데이터포털 공식 자료](https://www.data.go.kr/data/15090532/openapi.do)에서
확인한 endpoint:

```text
base: https://apis.data.go.kr/B554287/NationalWelfareInformationsV001
list: /NationalWelfarelistV001
detail: /NationalWelfaredetailedV001
```

공식 자료에는 개발계정 신청 가능 트래픽이 100으로 표시되어 있다. 실제
계정의 현재 할당량과 응답 헤더를 연동 전에 다시 확인하고, 테스트마다
호출하지 않는다.

같은 공식 자료는 2026-07-26 기준 이용허락범위를 `제한 없음`으로 표시한다.
다만 Fixture의 최소성, 두 소스 간 일관된 경계와 시점 의존성 제거를 위해
복지로도 실제 정책 원문이 아닌 합성 Raw를 사용한다.

2026-07-26 Source Preflight의 목록 1건·상세 1건과 Data 3의 목록 10건·상세
3건을 호출해 다음을 확인했다.

- 두 응답 모두 HTTP 200, `application/xml`, UTF-8
- root element는 각각 `wantedList`, `wantedDtl`
- 목록의 `servId`로 상세를 연결할 수 있음
- 응답에 rate limit 관련 HTTP header 없음

필드와 반복 element 프로필은
[API Source Profile](source_profiles.md)에 기록한다.

### 남은 확인 사항

- 선택 필드가 비어 있거나 element 자체가 없는 실제 경계 응답
- 오류 payload와 할당량 초과의 실제 HTTP 상태
- 2025년 API 변경 공지 이후 추가·삭제된 응답 필드
- 생애주기, 가구유형, 관심주제 코드표의 현재 값

[2025년 변경 공지](https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000004050)는
온라인 신청 가능 여부와 관심주제 추가, 일부 미사용 필드 제거를 안내한다.
따라서 이전 샘플만으로 Extractor 필드를 확정하지 않고 실제 응답과 현재
공식 명세를 함께 확인한다.

## 대표 HTTPS 웹 소스

### 확정된 기준

- Source ID는 `cheonan-youthcenter-web`이다.
- 목록 allowlist는 `/bbs/board.php?bo_table=notice` 한 페이지다.
- 상세 allowlist는
  `/bbs/board.php?bo_table=notice&wr_id={positive_integer}`이며 첫 승인 표본은
  [공지 674번](https://www.ch2030youth.kr/bbs/board.php?bo_table=notice&wr_id=674)이다.
- external identity는 `notice:{wr_id}`이며 표본은 `notice:674`다.
- 동시 요청은 1개, 요청 시작 간격은 최소 2초로 하고 목록 1회·승인 상세 1건
  외 pagination·대량 순회를 하지 않는다.
- 목록 페이지와 상세 페이지 파서를 분리한다.
- 정적 HTML과 공개 내부 API를 우선 검토한다.
- CSS Selector는 소스별 설정에 모으고 공통 코드에 흩어놓지 않는다.
- 특정 선택 필드가 없어도 전체 수집을 중단하지 않는다.

### 대상 선정 기준

- HTTPS로 공개 접근 가능
- 로그인이나 사용자 조작 없이 정책 원문 확인 가능
- 목록에서 상세 페이지를 안정적으로 식별 가능
- robots 정책, 이용약관과 라이선스상 수집·보존 가능
- 정책명, 기관, 신청 기간, 지원 내용과 대상 조건 중 핵심 필드 확인 가능
- 구조와 예외를 검증할 수 있는 대표 상세 사례 확보 가능
- 개인정보가 포함된 게시물이나 첨부파일을 수집하지 않아도 됨

### 동적 페이지 처리

페이지 소스에 필요한 데이터가 없을 때만 동적 처리를 검토한다.

1. 개발자 도구의 Network 요청에서 공개 JSON API가 있는지 확인한다.
2. 공개 요청을 직접 재현할 수 있으면 해당 응답을 사용한다.
3. 두 방법으로 데이터를 얻을 수 없을 때만 Playwright 같은 브라우저 자동화를
   별도 결정으로 검토한다.

### 2026-08-10 표본과 보존 경계

공지 674번에서 공개 제목·게시일·지원 대상·지원 내용·제출서류·유의사항을
확인했다. 게시일은 `2026-07-24`인데 본문 신청기간은
`2026-04-22`~`2026-05-06 23:00`이고 제목은 “곧 마감”으로 표시돼 충돌한다.
신청 상태는 추정하지 않고 `unknown`, 데이터 품질은 `partial`로 기록한다.

`/robots.txt`는 directive 대신 404 페이지를 반환했고 별도 사이트 이용약관은
찾지 못했으며 footer에는 `all rights reserved`가 표시된다. 로그인·회원·신청·
CAPTCHA·첨부·이미지·개인정보 페이지는 따라가지 않는다. 공개 시설 대표전화와
공식 문의 채널은 기관 정보로 구분해 Runtime Raw와 Source 전용 필드에 보존하고,
개인 휴대전화·개인 이메일·성명은 구조화 추출하지 않는다. actual HTML Raw는
`runtime/raw/`에만 두고 Git Fixture는 원문을 복제하지 않은 합성·최소 구조로
만든다.

DTL4-3A actual 확인에서 목록은 `#bo_list`, 상세는 `#bo_v`·`#bo_v_title`·
`#bo_v_info`·`#bo_v_con`을 사용했다. Source HTML의 비표준 `</img>` 종료 태그는
void element로 처리하며 selector 누락은 정상 빈 값이 아닌 drift로 분류한다.

DTL4-3B는 저장된 actual Raw 3건을 외부 재호출 없이 replay해 `partial` 정책
1건과 provenance 3건을 PostgreSQL에 적재했다. 동일 Raw 재실행은 `unchanged`
1건이었고 중복 row를 만들지 않았다. 신청기간 한글 표기는 현재 공통 파서가
추정하지 않아 신청 상태를 `unknown`으로 유지한다. Source 전용 제외조건·서류와
기관 연락처는 공통 Schema 계약 전이므로 Raw·Extractor 근거에만 남기고 DB/API
공통 필드로 자동 승격하지 않는다.

## 소스 등록 시 기록할 정보

- `source_id`와 표시 이름
- source type
- 운영 기관
- 목록, 상세와 API endpoint
- 인증 필요 여부
- 응답 형식과 문자 인코딩
- 정책 ID 결정 방식
- 호출 제한과 권장 요청 간격
- robots 정책과 이용약관 확인 결과
- 데이터 라이선스와 출처 표시 방법
- 개인정보 및 저장 제외 필드
- 마지막 구조 검증일
- 담당 Collector와 Extractor

소스 추가나 이용 조건 변경은 [수집 정책](collection_policy.md)과 관련
Collector 문서를 함께 갱신한다.

## 현재 미확정 사항

- 온통청년 API의 오류 payload
- 복지로 선택 필드의 누락·빈 element 경계 사례
- 온통청년 API 원문의 명시적인 비상업적 재배포·출처 표시 조건
- 온통청년의 숫자 호출 한도와 복지로 트래픽 기간 단위

미확정 사항은 후속 Source Profile 확인 또는 명시적 실제 호출에서 공식
자료와 실제 샘플을 근거로 확정한다.

[youth-api-guide]: https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiGuide
[youth-terms]: https://www.youthcenter.go.kr/cmnFooter/termsInfo
