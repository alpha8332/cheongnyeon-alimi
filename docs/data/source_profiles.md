# Source Profile

## 문서 상태

- 상태: 기준선
- 마지막 공식 자료 확인: 2026-08-10
- 마지막 실호출 확인: 2026-08-10
- 범위: 온통청년·복지로 API, 천안청년센터 승인 공개 웹 공지

이 문서는 Source Preflight에서 확인한 요청 계약, 응답 구조, 필드와 호출
제약을 기록한다. 공식 자료의 명세, 실제 응답과 로컬 과거 샘플을 구분하며,
실호출로 확인하지 못한 사항을 현재 동작으로 표현하지 않는다.

## Source ID와 검증 상태

| Source ID | 표시 이름 | 공식 요청 계약 | 실응답 |
| --- | --- | --- | --- |
| `youthcenter-api` | 온통청년 청년정책 API | 로컬 제공 계약 채택 | JSON 전체 목록 2,698건 Raw 확인 |
| `bokjiro-central-welfare-api` | 복지로 중앙부처 복지서비스 API | 확인 | XML 전체 목록 461건·상세 5건 Raw 확인 |
| `cheonan-youthcenter-web` | 천안청년센터 이음 공지 | W4-G0 승인 | 공지 674 HTML Raw → PostgreSQL·API 확인 |

Source ID는 원문 제공기관의 ID와 구분되는 프로젝트 내부 식별자다.
Raw `external_id`는 온통청년의 `plcyNo`, 복지로의 `servId`로 확정했다.
목록 항목과 상세 응답은 같은 `source_id + external_id`로 연결하고 목록
항목은 부모 전체 응답의 `document_id`도 참조한다. Data 4에서 두
Extractor가 공통 `ExtractedPolicy`와 기여 Raw provenance를 사용하도록
확정했다.

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

Data 3 Collector도 같은 요청을 1회 수행해 목록 전체 1개와 `plcyNo` 기반
항목 10개의 Raw를 `runtime/raw/`에 저장하고 다시 로드했다.

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

### Data 4 Extractor와 runtime Raw 프로필

`YouthCenterExtractor`는 2026-07-26 Data 3의 목록 항목 Raw 10개를 외부 호출
없이 재처리했다. 60개 필드는 모두 존재율 100%이고 모두 string이었으며
null은 없었다. 빈 문자열 집계는 다음과 같다.

```text
addAplyQlfcCndCn 3
aplyUrlAddr 3
aplyYmd 8
bizPrdBgngYmd 6
bizPrdEndYmd 6
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

Source Preflight의 앞선 10건과 비교하면 `bizPrdBgngYmd`와 `bizPrdEndYmd`의
빈 값은 각각 8건에서 6건으로 달랐다. 필드나 타입 변경은 아니며 두 시점의
page 1 응답 내용이 달라진 것으로 관찰했다. 고정된 빈 값 비율을 소스 계약으로
간주하지 않는다.

공통 매핑은 `plcyNm`, 운영기관명, 대분류, 신청기간 원문, 지역 코드 원문,
연령 제한 필드, 참여·추가 자격, 지원 내용과 신청 방법을 사용한다.
`aplyYmd`가 비어 있으면 `aplyPrdSeCd`의 검증된 특정기간·상시·마감 의미를
전달하고, 연령 최소·최대는 의미를 추가 추정하지 않는 표시 text로 만든다.
대·중분류, 키워드, 자격 코드와 매핑 여부와 관계없이 전체 60개 필드를
`extra.source_fields.list_item`에 보존한다.

### 호출 제한과 오류

- 공식 공개 페이지에서 계정별 숫자 호출 한도를 확인하지 못했다.
- 이용약관은 대량 이용을 별도 계약 대상으로 두며 과도한 트래픽이 서비스
  이용을 방해할 경우 접근을 제한할 수 있다고 명시한다.
- `/go/ythip/getPlcy`의 JSON 정상 응답은 확인했다.
- 잘못된 키나 파라미터를 사용하는 오류 호출은 실행하지 않아 오류 payload와
  인증 실패 상태는 아직 미확인이다.
- `/opi/youthPlcyList.do`의 302 redirect는 현재 Collector에서 따라가지
  않는다.

### 2026-07-31 Release 1 DT1 표본

재시도 없이 `pageNum=1`, `pageSize=10` 목록 1회를 호출해 Raw 11개와
정책 10건을 재처리했다. 응답의 `total_count`는 2,696이었다.

- 10건 모두 `partial`, invalid는 0건
- `zipCd` 원문은 10건 모두 존재하지만 정규화 `regions`는 모두 빈 배열
- 최소·최대 연령은 9건, 연령 원문은 10건에 존재
- 신청 상태는 open 6건, closed 3건, scheduled 1건
- 신청기간 형태는 fixed 5건, always 2건, 미상 3건
- 카테고리 원문은 10건 모두 존재하고 2건은 미매핑 경고 포함
- 표본 제목·지원·자격 text에서 주거·월세 직접 표현은 탐지되지 않음

보유 `온통청년 API코드정보.xlsx`에는 정책·자격·분류 코드가 있지만
`zipCd` 행정구역 code-to-name 표는 없다. PSF4는 DT1 Raw의 `zipCd` 373개,
고유 260개를 별도 공식 법정동 기준정보의 `kr-bjd-prefix5` exact crosswalk와
대조했고 260개가 모두 유일하게 일치했다. 이 증거를 바탕으로 Adapter는
쉼표 구분 5자리 code만 exact resolver에 전달한다. 앞자리·기관명이나 code
개수로 지역·전국을 추정하지 않는다.

표본에는 인천광역시 개편 전 code `28110`, `28140`, `28260`과 현행 code가
함께 존재한다. 폐지 code는 후계 code로 자동 치환하지 않고 당시 canonical
identity와 Source code를 보존한다. 새로운 code가 crosswalk에 없으면
`unmapped`, 여러 후보면 `ambiguous`로 남긴다. 집계·과거 code와 현재 세부
code는 [행정구역 기준정보](administrative_regions.md)의 원천 parent·aggregate
parent·폐지 보존 규칙을 따른다.

DT1 당시 2,696건을 전체 수집하려면 page size와 종료 조건 확인이 필요했다.
공개 자료에서 `/go/ythip/getPlcy`의 최대 `pageSize`와 숫자 호출 한도를
확인하지 못했으므로 DT3에서 `pageSize=500`을 실제 응답으로 검증했다.

### 2026-08-03 PSF4 오프라인 재생

DT1의 같은 Raw 11개를 네트워크 없이 새 Adapter로 재생했다.

- 정책 10건 중 valid 8건, partial 2건, invalid 0건
- `plcyExplnCn` summary와 `mclsfNm`·`plcyKywdNm` keywords 10건 모두 채움
- 10건 모두 `regional`, region rule 373개 모두 exact `matched`
- `zipCd` 원문과 전체 Source field·Raw provenance 유지
- Source에 명시되지 않은 life stage·target group은 모두 빈 배열 유지

### 2026-08-04 Release 1 전체 목록 snapshot

`pageSize=500`을 실제로 수용함을 확인하고 6개 page를 재시도 없이 순회했다.
첫 응답부터 마지막 응답까지 `total_count=2698`이 유지됐고, 고유 `plcyNo`
2,698개가 보고 건수와 일치했다. Raw는 목록 응답 6개와 목록 항목 2,698개,
합계 2,704개다.

- 실제 성공 호출 6회, 상세 호출 없음
- snapshot ID: `4580234be1df46cbbe4a700fc4e02630`
- DT4 연령 placeholder 보정 후 오프라인 재생:
  valid 1,462·partial 1,236·invalid 0, accepted 2,698
- `0세 ~ 0세` 631건은 실제 0세 한정으로 확정하지 않고 원문 보존,
  구조화 연령 null과 `placeholder_age_range` 경고로 처리함
- Source URL 후보 3건에 literal 공백이 있었으며, URL 계약에 맞지 않는 후보를
  사용하지 않고 query 없는 공식 Raw source endpoint로 fallback함
- Source 원문 URL 값은 `extra.source_fields`와 Raw에 그대로 보존함

전체 품질·검색 분포와 소비 경계는
[Release 1 실데이터 품질 Profile](release_dataset_profile.md)을 따른다.

Source가 cursor나 시점 고정 token을 제공하지 않으므로 이 snapshot은 6회
응답 사이 변경 가능성을 완전히 제거하지 못한다. manifest의 시작·완료 시각,
각 응답 Raw ID와 고정 total을 재현 경계로 사용한다.

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

Source Preflight에서는 목록 1건과 그 목록의 `servId`를 사용한 상세 1건을
호출했다. Data 3에서는 목록 10건 1회와 그중 첫 상세 3건을 호출했다. 응답은
HTTP 200, `application/xml`, UTF-8이었고 namespace 없는 `wantedList`와
`wantedDtl` 구조를 사용했다. 응답에 rate limit 관련 HTTP header는 없었다.

Data 3 Collector는 목록 전체 1개, 항목 10개와 상세 3개의 Raw를
`runtime/raw/`에 저장하고 다시 로드했다. 목록 항목과 상세의 `servId`
연결 오류는 없었다.

목록 응답 메타데이터 leaf:

```text
numOfRows, pageNo, totalCount, resultCode, resultMessage
```

목록 항목 leaf:

```text
inqNum, intrsThemaArray, jurMnofNm, jurOrgNm, lifeArray,
onapPsbltYn, rprsCtadr, servDgst, servDtlLink, servId, servNm,
sprtCycNm, srvPvsnNm, svcfrstRegTs, trgterIndvdlArray
```

상세 leaf element:

```text
alwServCn, crtrYr, intrsThemaArray, jurMnofNm, lifeArray,
resultCode, resultMessage, rprsCtadr, servId, servNm,
servSeCode, servSeDetailLink, servSeDetailNm, slctCritCn,
sprtCycNm, srvPvsnNm, tgtrDtlCn, trgterIndvdlArray,
wlfareInfoOutlCn
```

상세 한 건에서 `servSeCode`와 `servSeDetailNm`은 각각 9회,
`servSeDetailLink`는 8회 반복됐다. XML Raw 단계의 leaf 값은 모두 string으로
관찰했고 빈 element는 없었다. 한 건의 결과이므로 선택 필드가 항상
존재한다고 일반화하지 않는다. 숫자·날짜처럼 보이는 값도 Extractor와
Normalizer가 명시적으로 변환하기 전에는 Raw string으로 보존한다.

### Data 4 Extractor와 runtime Raw 프로필

`BokjiroExtractor`는 목록 항목 10개와 상세 3개를 재처리해 정책 10개를
만들었다. 상세 3개는 같은 `servId`의 목록과 결합했고 나머지 7개는 목록
값만 유지했다.

| 역할 | 문서 수 | 필드 수 | 존재율 예외 | 빈 값 | 반복 배열 |
| --- | ---: | ---: | --- | --- | --- |
| `list_item` | 10 | 15 | `intrsThemaArray` 90%, `lifeArray` 80%, `trgterIndvdlArray` 50% | 없음 | 없음 |
| `detail_response` | 3 | 19 | 없음, 모두 100% | 없음 | `servSeCode`, `servSeDetailLink`, `servSeDetailNm` |

상세가 있으면 제목·주관부처·대상·선정기준·급여 내용을 상세에서 우선하고,
상세 값이 없으면 목록의 제목·부처·요약을 유지한다. 관심주제는 목록 원문을
`category_text`로 전달한다. 목록과 상세의 전체 leaf 값은 역할별
`extra.source_fields`에 보존해 `lifeArray`, `trgterIndvdlArray`,
`servSeCode`를 포함한 코드·표시 문자열과 반복 순서를 유지한다.

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

### 2026-07-31 Release 1 DT1 표본

재시도 없이 `pageNo=1`, `numOfRows=10` 목록 1회와 첫 3건의 상세를 호출해
Raw 14개와 정책 10건을 재처리했다. 응답의 `total_count`는 461이었다.

- 10건 모두 `partial`, invalid는 0건
- 지역, 최소·최대 연령, 연령 원문과 신청기간·상태는 10건 모두 없음
- 카테고리 원문은 9건, 지원 내용은 10건에 존재
- 상세가 결합된 3건에서 자격 text가 보강됨
- 표본 제목·지원·자격 text에서 주거·월세 직접 표현은 탐지되지 않음

현재 목록·상세 응답 계약만으로는 지역·연령·신청기간을 정규화할 수 없다.
상세 호출도 이 세 누락을 해소하지 않았으므로 값을 추정하지 않는다.
명세상 목록 최대 500건으로 현재 461건 전체 목록은 한 요청 후보지만,
개발계정 트래픽 100의 기간 단위가 불명확해 461건 전체 상세 호출은
승인 범위가 아니다. 상세 대상은 검색 가치와 실제 보강 효과를 기준으로
결정론적으로 제한하고 호출 상한을 실행 전에 기록해야 한다.

### 2026-08-03 PSF4 오프라인 재생

DT1의 같은 Raw 14개를 네트워크 없이 새 Adapter로 재생했다.

- 정책 10건 모두 partial, invalid 0건
- summary 10건, interests 기반 keywords 9건
- life stages 8건, target groups 5건
- 지역 근거가 없어 10건 모두 `coverage_scope=unknown`, region rule 0건
- 상세 3건은 상세 값을 우선하고 목록 값은 fallback으로 유지했으며 양쪽
  Source field와 Raw provenance를 모두 보존

### 2026-08-04 Release 1 전체 목록 snapshot

명세상 최대 `numOfRows=500`으로 목록 1회를 호출해 `total_count=461`과 고유
`servId` 461개가 일치함을 확인했다. 승인된 상세 상한 5건만 같은 회차에서
추가 호출했다. Raw는 목록 응답 1개, 목록 항목 461개와 상세 5개, 합계
467개다.

- 실제 성공 호출 6회: 목록 1회·상세 5회
- snapshot ID: `2e0b8100348544b3b023b27017025218`
- 오프라인 재생: valid 0·partial 461·invalid 0, accepted 461
- 전체 상세 461건은 호출 상한 밖이며 수행하지 않음

### 2026-08-06 DT7C 신청기간 Source mapping 재감사

현재 Release 1 snapshot `ffa74ef47e6048109f11bf40d1ac5e15`의 복지로
461건을 외부 호출 없이 재생했다. 목록·상세 leaf 계약에는 신청기간 전용 필드가
없으며 Extractor도 `application_period_text`를 만들지 않는다.

- 461건 모두 신청기간 원문·시작일·종료일·일정·상태가 null
- Source 근거 없는 구조화 승격 0건, 기간·상태 불일치 0건
- `청년내일저축계좌`, `청년월세 지원사업` 2건의 일반 본문에서 날짜 표기 관찰
- 두 정책 모두 원문을 summary·support content에 보존하고 신청기간으로는
  승격하지 않음

온통청년은 같은 감사에서 `aplyYmd`와 검증된 `aplyPrdSeCd`만 신청기간 근거로
사용했다. 일반 본문 날짜 탐지는 Source mapping을 대체하지 않으며 관찰 건수만
profile에 남긴다.

## 천안청년센터 이음 공개 공지

### W4-G0 승인 요청 계약

| 항목 | 확인·승인 값 |
| --- | --- |
| Source ID | `cheonan-youthcenter-web` |
| 운영 근거 | 천안시 청년지원기관 천안청년센터 이음 공개 공지 |
| 목록 | `https://www.ch2030youth.kr/bbs/board.php?bo_table=notice` |
| 상세 | `/bbs/board.php?bo_table=notice&wr_id={positive_integer}` |
| identity | `notice:{wr_id}` |
| 표본 | `notice:674` |
| 요청 예산 | 동시 1개, 시작 간격 최소 2초, 목록 1회·표본 상세 1건 |
| 보존 | actual HTML은 Runtime 전용, Git은 합성·최소 구조 Fixture만 허용 |

`2026-08-10` 익명 공개 상세에서 제목·게시일·대상·지원 내용·제출서류와
유의사항을 확인했다. 회원가입·로그인이 필요한 신청 단계는 수집 범위가 아니다.
첨부·이미지·개인정보 페이지는 따라가지 않는다. 공개 시설 대표전화와 공식
카카오채널은 기관 문의 정보로 Runtime Raw와 `institutional_contact`에 보존하고,
개인 휴대전화·개인 이메일·성명은 구조화 추출하지 않는다.

DTL4-4A에서 세 Source의 자격요건 승격 규칙을
[Eligibility Summary 공통 계약](eligibility_summary_contract.md)으로 고정했다.
온통청년 `ptcpPrpTrgtCn`과 복지로 `slctCritCn`은 실제 원문 의미가 필수·제외·
우대로 단일하지 않아 자동 분류하지 않고 `unknowns`로 보존한다. 천안 웹은
승인 section과 `#bo_v_con` evidence를 사용하며 대표전화·공식 채널만
`institutional_contacts`로 승격한다.

표본 게시일은 `2026-07-24`, 본문 신청기간은
`2026-04-22`~`2026-05-06 23:00`인데 제목에는 “곧 마감”이 있어 서로
충돌한다. Extractor는 신청 상태를 보정하지 않고 `data_quality_status=partial`,
신청 상태 `unknown`과 확인 필요 evidence를 만든다.

`/robots.txt`는 directive가 아닌 404 페이지였고 별도 이용약관은 찾지 못했다.
footer의 `all rights reserved`를 고려해 공개 사실의 최소 추출만 승인하며,
pagination·대량 순회·원문 HTML 또는 이미지의 Git 재배포는 승인하지 않는다.
actual DOM은 목록 `#bo_list`, 상세 `#bo_v`·`#bo_v_title`·`#bo_v_info`·
`#bo_v_con`으로 확인했다. `</img>` 비표준 종료 태그를 허용하되 필수 selector
누락은 drift로 실패한다.

### 2026-08-10 DTL4-3B actual replay

DTL4-3A의 actual Raw 3건을 외부 요청 없이 replay했다. Extractor·Normalizer는
정책 1건을 `partial`, 신청 상태 `unknown`으로 분류하고 provenance 3건을
유지했다. 전용 PostgreSQL 최초 적재는 `inserted=1`, 동일 Raw 재실행은
`unchanged=1`이었으며 CollectionRun 2건과 정책 row 1건이 일치했다. 공개 정책
상세 API는 기본 partial 비노출 `404`, `include_partial=true`에서 `200`을
반환했고 Raw provenance는 공개 DTO에 포함하지 않았다.

합성 HTML PostgreSQL 통합 테스트에서는 최초 `inserted`, 동일 `unchanged`,
지원 내용 변경 `updated`와 후속 selector drift 실패 뒤 기존 row 보존을
확인했다. Source 전용 section의 제외조건·필요서류와 기관 연락처는 DTL4-4의
공통 조건·소비 계약 전까지 자동 승격하지 않는다.

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

## Collector 실행 계약

- 기본 Registry source ID:
  `youthcenter-api`, `bokjiro-central-welfare-api`,
  `cheonan-youthcenter-web`
- 공통 옵션: `page` 1~1000, `limit` 1~500, `detail_limit` 0~5
- CLI 기본값: page 1, limit 10, 복지로 상세 3건
- 온통청년 요청 수: 목록 1회
- 복지로 요청 수: 목록 1회와 선택한 상세 수
- 천안청년센터 요청 수: page 1의 승인 목록 1회와 `notice:674` 상세 최대 1회,
  같은 실행의 요청 시작 간격 최소 2초
- 테스트는 주입한 HTTP Client와 임시 Raw root를 사용하며 외부 호출하지 않음
- 실제 호출은 환경변수를 주입한 명시적 CLI 실행으로만 수행
- 응답 payload에서 요청 인증키가 발견되면 Raw 저장 전에 파싱 오류로 중단

[youth-api-list]: https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiDoc/47
[youth-api-guide]: https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiGuide
[bokjiro-api]: https://www.data.go.kr/data/15090532/openapi.do
[bokjiro-change]: https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000004050
