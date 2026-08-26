# 데이터 소스

## 현재 범위

Backend 관리자 수집기 catalog와 worker registry에는 11개 Source가 등록돼 있다.
이 수는 공개 dataset Source 수와 다르다. 수집 가능 여부, 로컬 DB 보존과
정규화 결과 재배포 허용 여부를 각각 판정한다.

| Source ID | 표시명 | 유형 | 인증정보 | 공개 dataset |
| --- | --- | --- | --- | --- |
| `bokjiro-central-welfare-api` | 복지로 중앙부처 복지서비스 | API | 필요 | 포함 |
| `youthcenter-api` | 온통청년 청년정책 API | API | 필요 | 포함 |
| `data-go-kr-incheon-youth-programs` | 인천 청년공간 유유기지 프로그램 | 파일 | 불필요 | 포함 |
| `cheonan-youthcenter-web` | 천안청년센터이음 공지 | 웹 | 불필요 | 제외 |
| `regional-busan-youth-platform` | 부산청년플랫폼 | 웹 | 불필요 | 제외 |
| `regional-gyeongbuk-youth-platform` | 경북청년포털 청년e끌림 | 웹 | 불필요 | 제외 |
| `kinfa-financial-product-web` | 서민금융진흥원 금융상품 | 웹 | 불필요 | 제외 |
| `kosaf-scholarship-web` | 한국장학재단 장학금 | 웹 | 불필요 | 제외 |
| `kpass-transit-refund-web` | 모두의카드 교통비 환급 | 웹 | 불필요 | 제외 |
| `lh-housing-announcement-web` | LH청약플러스 임대주택 공고 | 웹 | 불필요 | 제외 |
| `work24-policy-web` | 고용24 정책 | 웹 | 불필요 | 제외 |

권위 목록은 `backend/app/services/collector_catalog.py`, 실제 worker factory는
`collectors.default_registry`, 관리자 수동 실행 allowlist는
`backend/app/services/manual_collection_contract.py`다. 세 목록이 달라지면
관리자 화면과 worker 실행 가능 상태가 어긋나므로 같은 변경에서 대조한다.

## 공개 Source

### 복지로

- Source ID: `bokjiro-central-welfare-api`
- 공식 제공기관: 한국사회보장정보원
- 형식: XML 목록·상세 API
- 인증: `BOKJIRO_API_KEY`
- identity: Source의 서비스 ID
- 공개 근거: 공공데이터포털 이용허락범위 `제한 없음`
- 공식 문서: [중앙부처복지서비스 API](https://www.data.go.kr/data/15090532/openapi.do)

목록과 상세 Raw를 별도로 보존하고 같은 Source identity로 결합한다. 단위
테스트는 합성 XML을 사용하며 실제 호출은 중앙 수집 환경에서만 수행한다.

### 온통청년

- Source ID: `youthcenter-api`
- 공식 제공기관: 한국고용정보원
- 형식: JSON API
- 인증: `YOUTHCENTER_API_KEY`
- identity: 정책 ID
- 공개 근거: 공공데이터포털 이용허락범위 `제한 없음`과 프로젝트 API 이용 승인
- 공식 문서: [온통청년 청년정책 API](https://www.data.go.kr/data/15143273/openapi.do)

전국·시도·시군구 정책을 함께 공급하므로 사용자 지역 검색의 주된 지역 정책
Source다. 지역 근거가 없거나 해석되지 않은 row를 전국 정책으로 승격하지 않는다.

### 인천 공개 파일

- Source ID: `data-go-kr-incheon-youth-programs`
- 제공기관: 인천광역시
- 형식: 공공데이터포털 공개 파일
- 인증: 불필요
- 공개 근거: 이용허락범위 `제한 없음`
- 공식 문서: [청년공간 유유기지 프로그램](https://www.data.go.kr/data/15038491/fileData.do?recommendDataYn=Y)

## 웹 Source

웹 Source는 공개 페이지에서 최소 정책 사실과 provenance를 수집할 수 있지만,
명시적 개방 라이선스나 항목별 공공누리 근거가 확인되지 않은 normalized 결과를
공개 artifact에 넣지 않는다.

- 로그인, 신청, CAPTCHA, 첨부·이미지와 개인정보 페이지를 따라가지 않는다.
- robots, 이용약관, 저작권 정책과 요청 간격을 Source별로 확인한다.
- 정적 HTML이나 공개 내부 API를 우선하고 Browser capture는 필요한 범위로
  제한한다.
- 원문 HTML과 이미지는 GitHub Release에 재배포하지 않는다.
- 수동 수집 결과는 로컬 DB·Runtime에 남아도 공개 membership에 자동 포함되지
  않는다.

지역 후보 inventory는 `data/reference/regional_youth_policy_sources.json`에
보존한다. inventory 등록이나 수집 성공은 사용자 공개 승격을 의미하지 않는다.

## 인증정보와 로그

- 실제 key는 로컬 `.env` 또는 GitHub Environment secret에서만 주입한다.
- key 값, 길이, 일부 문자열과 query 전체를 화면·로그·문서에 노출하지 않는다.
- 관리자 수집기 화면은 `설정됨/미설정` boolean만 표시한다.
- 사용자 `run_docker.bat`은 key를 요구하지 않고 공개 dataset을 설치한다.

## Source 추가 기준

1. 제공기관, 공식 URL, identity와 응답 형식을 확인한다.
2. 호출 제한, robots, 이용약관과 개인정보 제외 범위를 기록한다.
3. 합성 Fixture로 정상·빈 값·오류·drift를 검증한다.
4. 완전 snapshot과 lifecycle 판정 방법을 정의한다.
5. normalized 결과 재배포 근거를 별도로 확인한다.
6. 공개할 경우 Source contract, manifest Gate와 attribution을 갱신한다.

세부 HTTP·Raw·실패 처리는 [데이터 수집 정책](collection_policy.md), 공개 여부는
[공개 정책 dataset](public_policy_dataset.md)을 따른다.
