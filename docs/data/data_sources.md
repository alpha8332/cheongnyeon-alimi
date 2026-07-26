# 데이터 소스

## 문서 상태

- 상태: 기준선
- 현재 구현 상태: Collector 미구현

이 문서는 프로젝트에서 사용할 데이터 소스의 등록 기준과 현재 확인 상태를
정의한다. 특정 Forest의 수집 건수와 구현 범위는
[Data Pipeline Forest 계획](../development/develop_plan/data/01_data_pipeline.md)에서
관리한다.
실제 엔드포인트, 응답 형식과 이용 조건은 Collector 구현 전에 공식 자료와
실제 응답으로 다시 확인한다.

## 현재 소스 후보

| 소스 | 계획 식별자 | 유형 | 상태 |
| --- | --- | --- | --- |
| 온통청년 청년정책 API | `youthcenter-api` | 공식 API | 인증키 확보, 현재 계약 재검증 필요 |
| 복지로 중앙부처 복지서비스 API | `bokjiro-central-welfare-api` | 공식 API | 인증키 확보, 연동 미검증 |
| 대표 HTTPS 정책 사이트 | `sample-web` | 공개 웹 | 후속 Forest 후보 |

두 API 인증키는 확보된 상태지만 키 값은 문서나 Git에 기록하지 않는다.
현재 로컬 작업 트리의 인증키 파일과 인증키가 포함된 참고 문서는 비밀 포함
자료이므로 Fixture나 커밋 대상이 아니다. `sample-web`은 공통 구조 검증을
위한 계획 식별자이며 실제 서비스 source ID로 확정된 이름이 아니다.

현재 Forest는 두 공식 API를 우선하고 Web Collector는 범위에서 제외한다.
구체적인 수집 건수와 결정 게이트는
[Data Pipeline Forest 계획](../development/develop_plan/data/01_data_pipeline.md)을
따른다.

## 온통청년 API

### 확정된 기준

- 인증키는 `YOUTHCENTER_API_KEY` 환경변수에서 읽는다.
- API 응답은 원본 형태로 보존한다.
- 응답 항목은 공통 `RawPolicyDocument`로 감싼다.
- Collector가 정규화된 정책을 직접 반환하지 않는다.

### 확인된 자료와 불일치

로컬 참고 자료에는 다음 계약이 기록되어 있다.

```text
endpoint: /go/ythip/getPlcy
authentication parameter: apiKeyNm
pagination: pageNum, pageSize
response selector: rtnType
```

반면 [현재 공식 제공목록](https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiDoc/47)의
요청 예시는 다음 계약을 사용한다.

```text
endpoint: /opi/youthPlcyList.do
authentication parameter: openApiVlak
pagination: pageIndex, display
```

공식 이용방법은 XML 전송을 설명하지만 로컬 참고 자료에는 `rtnType=json`과
10건의 JSON 샘플이 있다. 이 차이가 해결되기 전에는 어느 endpoint나 응답
형식도 구현 계약으로 확정하지 않는다.

### 구현 전 확인 사항

- 현재 유효한 base URL과 endpoint
- 현재 유효한 인증 파라미터 이름과 전달 방식
- 요청 파라미터, 페이지 크기와 제한
- 실제 응답 형식이 XML, JSON 또는 선택 가능한 형식인지 여부
- 정책 고유 ID와 상세 원문 URL의 위치
- 오류 응답, 호출 제한과 재시도 가능 상태 코드
- 이용약관, 공공데이터 이용 조건과 출처 표기 요구사항
- 응답에 개인정보 또는 저장을 제한해야 하는 필드가 있는지 여부

공식 문서와 실제 응답을 확인하기 전에는 예시 URL이나 필드명을 코드 계약으로
확정하지 않는다.

## 복지로 중앙부처 복지서비스 API

### 확인된 기준

- 인증키는 `BOKJIRO_API_KEY` 환경변수에서 읽는다.
- 제공 기관은 한국사회보장정보원이며 데이터는 복지로에서 제공한다.
- 데이터 형식은 XML이다.
- 목록과 상세 endpoint를 분리한다.
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

### 구현 전 확인 사항

- `serviceKey`의 encoding·decoding 형태와 전달 방식
- 목록과 상세의 현재 필수 파라미터
- 서비스 ID와 목록·상세 연결 규칙
- 현재 XML namespace, 문자 인코딩과 빈 element 표현
- 페이지 최대 크기, 오류 payload와 할당량 초과 상태
- 2025년 API 변경 공지 이후 추가·삭제된 응답 필드
- 생애주기, 가구유형, 관심주제 코드표의 현재 값
- 목록·상세 원문의 Fixture 재배포와 출처 표시 조건

[2025년 변경 공지](https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000004050)는
온라인 신청 가능 여부와 관심주제 추가, 일부 미사용 필드 제거를 안내한다.
따라서 이전 샘플만으로 Extractor 필드를 확정하지 않고 실제 응답과 현재
공식 명세를 함께 확인한다.

## 대표 HTTPS 웹 소스

### 확정된 기준

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

현재 대표 웹사이트와 Selector는 확정되지 않았다.

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

- 대표 HTTPS 웹사이트
- 온통청년 API의 현재 endpoint, 인증 파라미터와 응답 형식
- 복지로 목록·상세의 실제 XML 구조와 연결 ID
- 각 소스의 공식 호출 제한과 재배포 조건
- 실제 서비스에서 사용할 최종 source ID 목록

미확정 사항은 Source Preflight와 Collector 구현 Slice에서 공식 자료와 실제
샘플 응답을 확인한 뒤 확정한다.
