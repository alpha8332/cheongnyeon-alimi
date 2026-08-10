# 데이터 소스

## 문서 상태

- 상태: 기준선
- 현재 구현 상태: 온통청년·복지로 Collector 구현 및 제한 실호출 확인

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
| 천안청년센터 이음 공지 | `cheonan-youthcenter-web` | 공개 웹 | W4-G0 승인, 공지 674번 preflight 확인 |

두 API 인증키는 확보된 상태지만 키 값은 문서나 Git에 기록하지 않는다.
현재 로컬 작업 트리의 인증키 파일과 인증키가 포함된 참고 문서는 비밀 포함
자료이므로 Fixture나 커밋 대상이 아니다. 웹 Source의 실제 원문 HTML·이미지도
Git에 넣지 않고 합성·최소 구조 Fixture만 사용한다.

현재 구현은 두 공식 API만 포함한다. 승인 웹 Source 구현은 Data 04 Forest에서
진행한다.
구체적인 수집 건수와 결정 게이트는
[Data Pipeline Forest 계획](../development/develop_plan/data/01_data_pipeline.md)을
따른다.
요청 파라미터, 실제 응답 필드와 호출 결과는
[API Source Profile](source_profiles.md)에서 관리한다.

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
CAPTCHA·첨부·이미지·이메일·전화번호·개인정보 페이지는 수집하지 않는다.
actual HTML은 `runtime/html/`에만 두고 Git Fixture는 원문을 복제하지 않은
합성·최소 구조로 만든다. Selector는 Data 04 구현 시 actual DOM을 다시 확인해
Source module에만 확정한다.

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
