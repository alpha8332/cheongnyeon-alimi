# API Source Profile

## 문서 상태

- 상태: 기준선
- 마지막 공식 자료 확인: 2026-07-26
- 마지막 실호출 확인: 2026-07-26
- 범위: 온통청년 청년정책 API, 복지로 중앙부처 복지서비스 API

이 문서는 Source Preflight에서 확인한 요청 계약, 응답 구조, 필드와 호출
제약을 기록한다. 공식 자료의 명세, 실제 응답과 로컬 과거 샘플을 구분하며,
실호출로 확인하지 못한 사항을 현재 동작으로 표현하지 않는다.

## Source ID와 검증 상태

| Source ID | 표시 이름 | 공식 요청 계약 | 실응답 |
| --- | --- | --- | --- |
| `youthcenter-api` | 온통청년 청년정책 API | 로컬 제공 계약 채택 | JSON 10건 확인 |
| `bokjiro-central-welfare-api` | 복지로 중앙부처 복지서비스 API | 확인 | 목록 1건과 상세 1건 확인 |

Source ID는 원문 제공기관의 ID와 구분되는 프로젝트 내부 식별자다.
Raw `external_id`는 온통청년의 `plcyNo`, 복지로의 `servId`로 확정했다.
목록 항목과 상세 응답은 같은 `source_id + external_id`로 연결하고 목록
항목은 부모 전체 응답의 `document_id`도 참조한다. Extracted 계약은 후속
Slice에서 확정한다.

## 온통청년 청년정책 API

### 현재 검증 요청 계약

로컬 제공 자료의 요청 방법과 2026-07-26 실호출에서 다음 계약을 확인했다.

```text
method: GET
scheme: HTTPS
base: https://www.youthcenter.go.kr
path: /go/ythip/getPlcy
authentication query parameter: apiKeyNm
pagination: pageNum, pageSize
response selector: rtnType=json
response: JSON
```

인증키는 `YOUTHCENTER_API_KEY`에서 읽고 요청 직전에
`apiKeyNm`으로 전달한다. 요청 URI, query string과 인증 오류 원문을 로그나
Fixture에 남기지 않는다.

요청 예시와 동일한 `pageNum=1`, `pageSize=10`, `rtnType=json` 호출은
HTTP 200과 `application/json`을 반환했고 정책 10건을 포함했다. 홈페이지
로그인 세션이나 cookie는 사용하지 않았다.

### 공식 제공목록과의 차이

| 항목 | 검증된 계약 | 공식 제공목록의 다른 계약 | 판단 |
| --- | --- | --- | --- |
| path | `/go/ythip/getPlcy` | `/opi/youthPlcyList.do` | 검증된 path 채택 |
| 인증 파라미터 | `apiKeyNm` | `openApiVlak` | 검증된 이름 채택 |
| 페이지 | `pageNum`, `pageSize` | `pageIndex`, `display` | 검증된 이름 채택 |
| 형식 | `rtnType=json`, JSON | 이용방법은 XML, 제공목록은 JSON 보기 | JSON 채택 |

[온통청년 OPEN API 제공목록][youth-api-list]은
`/opi/youthPlcyList.do`와 `openApiVlak`를 안내하고
[공식 이용방법][youth-api-guide]은 XML 전송을 설명한다. 그러나 보유 키로
`/opi/youthPlcyList.do`를 호출하면 HTTP 302와
`http://www.youthcenter.go.kr:8080/` redirect를 반환했다. 자동 redirect를
따르면 접근할 수 없는 8080 포트 연결에서 `SocketException`이 발생한다.

반면 같은 키로 `/go/ythip/getPlcy`를 호출하면 HTTP 200 JSON을 반환했다.
따라서 이 저장소는 실동작을 우선해 `/go/ythip/getPlcy` 계약을 Collector
기준으로 사용한다. `/opi/youthPlcyList.do`는 새 키 발급 또는 제공기관의
gateway 수정 후 다시 검토할 대체 계약으로 남긴다.

### 2026-07-26 실응답 프로필

| 위치 | 관찰 타입 | 관찰 결과 |
| --- | --- | --- |
| `resultCode` | integer | 존재 |
| `resultMessage` | string | 존재 |
| `result.pagging.totCount` | integer | 존재 |
| `result.pagging.pageNum` | integer | 존재 |
| `result.pagging.pageSize` | integer | 존재 |
| `result.youthPolicyList` | array | `pageSize=10` 요청에서 10건 |
| 정책 항목의 60개 필드 | string | null 없음, 빈 문자열 있음 |

응답은 약 41KB였으며 파일로 저장하지 않고 메모리에서 구조만 집계했다.
빈 문자열이 관찰된 필드와 10건 중 빈 값의 수:

```text
addAplyQlfcCndCn 3
aplyUrlAddr 3
aplyYmd 8
bizPrdBgngYmd 8
bizPrdEndYmd 8
bizPrdEtcCn 1
earnEtcCn 7
etcMttrCn 2
operInstPicNm 1
plcyAplyMthdCn 2
ptcpPrpTrgtCn 3
refUrlAddr1 1
refUrlAddr2 10
sbmsnDcmntCn 3
sprvsnInstPicNm 1
srngMthdCn 9
```

관찰된 전체 항목 필드:

```text
addAplyQlfcCndCn, aplyPrdSeCd, aplyUrlAddr, aplyYmd,
bizPrdBgngYmd, bizPrdEndYmd, bizPrdEtcCn, bizPrdSeCd,
bscPlanAsmtNo, bscPlanCycl, bscPlanFcsAsmtNo, bscPlanPlcyWayNo,
earnCndSeCd, earnEtcCn, earnMaxAmt, earnMinAmt, etcMttrCn,
frstRegDt, inqCnt, jobCd, lastMdfcnDt, lclsfNm, mclsfNm,
mrgSttsCd, operInstCd, operInstCdNm, operInstPicNm, plcyAplyMthdCn,
plcyAprvSttsCd, plcyExplnCn, plcyKywdNm, plcyMajorCd, plcyNm,
plcyNo, plcyPvsnMthdCd, plcySprtCn, ptcpPrpTrgtCn,
pvsnInstGroupCd, refUrlAddr1, refUrlAddr2, rgtrHghrkInstCd,
rgtrHghrkInstCdNm, rgtrInstCd, rgtrInstCdNm, rgtrUpInstCd,
rgtrUpInstCdNm, sbizCd, sbmsnDcmntCn, schoolCd, sprtArvlSeqYn,
sprtSclCnt, sprtSclLmtYn, sprtTrgtAgeLmtYn, sprtTrgtMaxAge,
sprtTrgtMinAge, sprvsnInstCd, sprvsnInstCdNm, sprvsnInstPicNm,
srngMthdCn, zipCd
```

실응답 필드명은 로컬 `온통청년json.txt`의 10건 샘플과 일치했다. 로컬 코드
정의서에서 다음 코드군을 확인했다.

| 필드 | 의미 | 코드 범위 또는 값 |
| --- | --- | --- |
| `pvsnInstGroupCd` | 제공기관 그룹 | 중앙부처, 지자체 |
| `plcyPvsnMthdCd` | 정책 제공 방법 | 인프라, 프로그램, 대출, 보조금 등 13개 |
| `plcyAprvSttsCd` | 정책 승인 상태 | 신청, 승인, 반려, 임시저장 |
| `aplyPrdSeCd` | 신청 기간 구분 | 특정기간, 상시, 마감 |
| `bizPrdSeCd` | 사업 기간 구분 | 특정기간, 기타 |
| `mrgSttsCd` | 결혼 상태 | 기혼, 미혼, 제한없음 |
| `earnCndSeCd` | 소득 조건 | 무관, 연소득, 기타 |
| `plcyMajorCd` | 전공 요건 | 9개 값 |
| `jobCd` | 취업 요건 | 10개 값 |
| `schoolCd` | 학력 요건 | 10개 값 |
| `sbizCd` | 특화 요건 | 10개 값 |

대분류 5개, 중분류 17개와 키워드 17개도 로컬 정의서에 있다. 코드표 자체의
변경 주기와 최신성은 Collector 이후 Extractor 구현 시 계속 검증한다.

### 호출 제한과 오류

- 공식 공개 페이지에서 계정별 숫자 호출 한도를 확인하지 못했다.
- 이용약관은 대량 이용을 별도 계약 대상으로 두며 과도한 트래픽이 서비스
  이용을 방해할 경우 접근을 제한할 수 있다고 명시한다.
- `/go/ythip/getPlcy`의 JSON 정상 응답은 확인했다.
- 잘못된 키나 파라미터를 사용하는 오류 호출은 실행하지 않아 오류 payload와
  인증 실패 상태는 아직 미확인이다.
- `/opi/youthPlcyList.do`의 302 redirect는 현재 Collector에서 따라가지
  않는다.

## 복지로 중앙부처 복지서비스 API

### 현재 공식 요청 계약

[공공데이터포털 공식 명세][bokjiro-api]와 2026-07-26 실응답에서 다음
계약을 확인했다.

```text
method: GET
scheme: HTTPS
base: https://apis.data.go.kr/B554287/NationalWelfareInformationsV001
list path: /NationalWelfarelistV001
detail path: /NationalWelfaredetailedV001
authentication query parameter: serviceKey
response: XML, UTF-8
```

목록 필수 파라미터:

| 이름 | 값 또는 규칙 |
| --- | --- |
| `serviceKey` | `BOKJIRO_API_KEY`를 요청 직전에 전달 |
| `callTp` | `L` |
| `pageNo` | 기본 1, 공식 설명상 최대 시작 위치 1000 |
| `numOfRows` | 기본 10, 최대 500 |
| `srchKeyCode` | `001` 제목, `002` 내용, `003` 제목+내용 |

목록 선택 파라미터는 `searchWrd`, `lifeArray`, `trgterIndvdlArray`,
`intrsThemaArray`, `age`, `onapPsbltYn`, `orderBy`다.

상세 필수 파라미터:

| 이름 | 값 또는 규칙 |
| --- | --- |
| `serviceKey` | `BOKJIRO_API_KEY`를 요청 직전에 전달 |
| `callTp` | `D` |
| `servId` | 목록의 `servId` |

`servId`를 source-scoped 외부 ID와 목록·상세 연결 키 후보로 사용한다.

### 2026-07-26 실응답 프로필

목록 1건과 그 목록의 `servId`를 사용한 상세 1건을 호출했다. 두 응답 모두
HTTP 200, `application/xml`, UTF-8이었고 namespace 없는 `wantedList`와
`wantedDtl` root를 사용했다. 응답에 rate limit 관련 HTTP header는 없었다.

목록 leaf element:

```text
numOfRows, pageNo, totalCount, resultCode, resultMessage,
inqNum, intrsThemaArray, jurMnofNm, jurOrgNm, onapPsbltYn,
rprsCtadr, servDgst, servDtlLink, servId, servNm, sprtCycNm,
srvPvsnNm, svcfrstRegTs
```

상세 leaf element:

```text
servId, servNm, jurMnofNm, wlfareInfoOutlCn, crtrYr,
rprsCtadr, tgtrDtlCn, slctCritCn, alwServCn,
servSeCode, servSeDetailNm, servSeDetailLink,
resultCode, resultMessage
```

상세 한 건에서 `servSeCode`와 `servSeDetailNm`은 각각 9회,
`servSeDetailLink`는 8회 반복됐다. XML Raw 단계의 leaf 값은 모두 string으로
관찰했고 빈 element는 없었다. 한 건의 결과이므로 선택 필드가 항상
존재한다고 일반화하지 않는다. 숫자·날짜처럼 보이는 값도 Extractor와
Normalizer가 명시적으로 변환하기 전에는 Raw string으로 보존한다.

### 코드와 오류 계약

로컬 v2.2 가이드에서 확인한 검색 코드:

- `lifeArray`: `000` 구분없음, `001` 영유아, `002` 아동, `003` 청소년,
  `004` 청년, `005` 중장년, `006` 노년, `007` 임신·출산
- `trgterIndvdlArray`: `010` 다문화·탈북민, `020` 다자녀,
  `030` 보훈대상자, `040` 장애인, `050` 저소득, `060` 한부모·조손
- `intrsThemaArray`: `010`부터 `160`까지 신체건강, 정신건강, 생활지원,
  주거, 일자리, 문화·여가, 안전·위기, 임신·출산, 보육, 교육, 입양·위탁,
  보호·돌봄, 서민금융, 법률, 관계개선, 에너지
- `servSeCode`: `010` 문의, `020` 사이트, `030` 근거법령,
  `040` 서식·자료, `050` FAQ, `060` 인포그래픽,
  `070` 복지사업 전달체계

가이드의 결과 코드:

| 코드 | 의미 |
| --- | --- |
| `0` | 성공 |
| `04` | HTTP 오류 |
| `10` | 잘못된 요청 파라미터 |
| `12` | 서비스 없음 또는 폐기 |
| `20` | 서비스 접근 거부 |
| `22` | 요청 제한 횟수 초과 |
| `30` | 등록되지 않은 서비스키 |
| `31` | 활용기간 만료 |
| `99` | 기타 오류 |

할당량 보호를 위해 잘못된 키나 파라미터를 사용한 오류 호출은 실행하지 않았다.
오류 결과는 HTTP 상태만으로 판단하지 않고 XML의 `resultCode`와
`resultMessage`도 함께 분류해야 한다.

### 호출 제한과 자료 차이

- 현재 한국어 공공데이터포털은 개발계정 신청 가능 트래픽을 100으로
  표시한다. 기간 단위는 공개 페이지에서 명확히 확인되지 않았다.
- 로컬 v2.2 가이드는 평균 응답 시간 500ms와 최대 30 TPS를 기재한다.
- 현재 명세는 목록 `numOfRows` 최대 500을 안내한다.
- 로컬 가이드는 HTTP와 전송 레벨 암호화 없음으로 작성됐지만 2026-07-26
  HTTPS 목록·상세 호출이 모두 성공했다. 구현은 HTTPS를 사용한다.
- [2025년 변경 공지][bokjiro-change]는 온라인 신청 가능 여부와 관심주제를
  추가하고 장애 유형·정도, 법령 링크 등 미사용 필드를 제거했다고 안내한다.

## 공통 비밀정보 경계

- 인증키 값은 환경변수에서만 읽고 코드, 문서, Fixture와 테스트 snapshot에
  복사하지 않는다.
- `apiKeyNm`, `openApiVlak`, `serviceKey`는 모두 redaction 대상이다.
- 오류 로그에는 source ID, operation, 실행 시각, HTTP 상태와 오류 분류만
  남기며 URI와 query string을 남기지 않는다.
- API 응답은 Source Preflight 중 메모리에서 구조만 집계하고 저장하지 않았다.
- 실제 Raw 저장은 Git에서 제외된 `runtime/raw/`를 사용한다.
- `data/runtime/raw/`는 사용하지 않는 과거 후보지만 재유입 방지를 위해
  ignore를 유지한다.
- 비밀이 포함된 로컬 키 파일과 참고 DOCX는 Git 추적에서 제외한다.
- 과거 Git 이력에 비밀 파일이 존재하므로 현재 키는 노출된 것으로 간주하고
  폐기·재발급해야 한다. 인덱스 제외는 과거 이력을 제거하지 않는다.

[youth-api-list]: https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiDoc/47
[youth-api-guide]: https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiGuide
[bokjiro-api]: https://www.data.go.kr/data/15090532/openapi.do
[bokjiro-change]: https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000004050
