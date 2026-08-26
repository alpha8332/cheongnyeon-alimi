# 변경 이력

이 파일은 `cheongnyeon-alimi`의 사용자와 팀에 의미 있는 변경 사항을
기록한다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
프로젝트는 [Semantic Versioning](https://semver.org/lang/ko/)을 사용한다.

## [Unreleased]

## [1.1.1] - 2026-08-26

### Fixed

- 전국·다지역 정책의 수백 개 행정구역이 검색·목록 카드와 상세 핵심 조건에
  한꺼번에 펼쳐지던 문제를 수정했다. 카드는 앞 2개 지역과 나머지 개수로
  축약하고, 상세에서는 같은 요약 상태에서 전체 지역을 펼쳐 확인할 수 있다.

## [1.1.0] - 2026-08-26

### Added

- placeholder였던 관리자 수집기 화면을 등록 source 11개, 중앙 queue·worker·
  scheduler, 활성 공개 dataset source별 정책 수, 최근 CollectionRun과 source별
  수동 실행을 확인하는 비밀 비노출 운영 화면으로 교체했다
  ([관리자 수집기 상태 API](docs/api/admin_collectors.md))
- 관리자 보안 화면에서 현재 PIN을 새 PIN으로 변경하고, 서버 PC의
  `reset_admin_pin.bat`으로 정책 DB와 CollectionRun을 보존한 채 분실 PIN을
  복구할 수 있게 했다. PIN 변경·복구 시 기존 관리자 세션을 모두 무효화하며,
  새 PIN verifier는 salted PBKDF2로 저장한다
  ([관리자 인증 API 계약](docs/api/admin_access.md),
  [Docker 운영 절차](docs/operations/docker_first_run.md#관리자-pin-변경과-분실-복구))

### Fixed

- Windows PowerShell 5.1이 `reset_admin_pin.bat`의 Docker 표준입력 시작에
  UTF-8 BOM을 붙여 정상적인 4자리 PIN을 5글자로 거부하던 문제를 수정했다.
  복구 CLI는 첫 입력의 BOM 하나만 제거하며 기존 길이·숫자·확인 검증은 유지한다.

## [1.0.2] - 2026-08-25

### Added

- 재배포가 허용된 온통청년 1,587건과 인천 청년 프로그램 4건을 복지로 461건과
  함께 공개해, API key 없이 실행하는 사용자가 전국·지역 청년정책 2,052건을
  동일하게 검색할 수 있게 했다. 활성 dataset 설치·membership·결과 parity와
  지역 coverage Gate로 작성자 DB의 로컬 정책이 사용자 결과에 섞이지 않게 했다
  ([QA 개선 기록](docs/troubleshooting/integration/v1_0_2_qa_improvements.md))

### Changed

- 홈에 시·도→시·군·구·분야 검색 조건과 프로필 관련도 보정을 통합하고,
  복수 관심 분야·복수 정책 분야 표시, 실제 결과가 있는 예시·관련 검색어,
  관련도·가나다·마감·수집일 결정적 정렬을 추가했다
  ([QA 개선 기록](docs/troubleshooting/integration/v1_0_2_qa_improvements.md))
- 대회 제출과 일반 사용자의 최초 실행을 기준으로 README를 Quick Start·기능·
  데이터 최신성·문제 해결 중심으로 재구성하고, 기여 가이드와 제출 clean-room
  Gate를 추가했다
- 플랫폼 종속 `venv/` 605개 파일과 `.DS_Store`의 Git 추적을 해제하고 OS·IDE·
  Python·Frontend·테스트·로그·임시 package의 ignore 경계를 보강했다
- 코드와 CSS에서 사용하지 않는 Vite·React starter image와 social icon sprite를
  공개 tree에서 제거했다

### Fixed

- `양산` 같은 접미사 없는 복합 지역 검색, 하위 시·군·구와 상위 관할·전국 정책
  포함, 지역 미확정 안내와 지역 정책 우선순위를 보정하고, 예시 검색 무결과·
  프로필 단일 관심 분야·주거 필터에서 복지 배지만 보이던 문제를 수정했다
  ([QA 개선 기록](docs/troubleshooting/integration/v1_0_2_qa_improvements.md))
- 깨끗한 심사자 DB와 작성자 DB가 서로 다른 공개 정책 집합을 반환하던 문제를
  활성 dataset projection으로 수정했다. 새 dataset 설치 실패 시 이전 version을
  유지하고 수동 수집 결과는 별도 승격 전까지 공개하지 않는다
  ([공개 dataset 동등성 계약](docs/data/public_dataset_parity.md))

## [1.0.1] - 2026-08-24

### Added

- 프로젝트 코드를 `cheongnyeon-alimi contributors` 명의의 MIT License로
  배포하고, 정책 dataset의 Source별 재배포 계약과 코드 라이선스 경계를 README에
  명시했다

### Fixed

- Final Gate SHA `ea6d3fa`를 MIT `LICENSE`가 포함된 annotated `v1.0.1` tag와
  GitHub Release로 다시 발행하고, GHCR image·Production Compose smoke·공개
  dataset을 새 `production-release.json`으로 대조했다
  ([운영 문서](docs/operations/production_delivery.md#v101-mit-라이선스-패치-발행-증거))

## [1.0.0] - 2026-08-24

### Changed

- Git `f5883bb`를 `v1.0.0`으로 발행하고 중앙 완전 수집 461건 중 개인정보
  경계를 통과한 457건의 versioned dataset, GHCR Backend·Frontend digest,
  SLSA provenance 2건과 clean Production Compose smoke를 하나의
  `production-release.json`으로 고정해 `W6-P4_PRODUCTION_PASS`를 확정했다
  ([운영 문서](docs/operations/production_delivery.md#v100-실제-발행-증거))
- 최종 Docker Acceptance commit과 AES-256 package receipt를 고정하고 BE·FE·
  사용성·QA를 역할별 project·secret·Volume으로 분리해 4건 모두 같은 Git SHA·
  snapshot·dump·archive hash로 통과시켜 `DOCKER_ACCEPTANCE_PASS`를 확정했다
  (개발 기록)
- review admission v1으로 실행일 현재성·청년 taxonomy·canonical region을 모두
  통과한 지역 정책 3건을 실제 DB에 적재하고 동일 manifest 재실행의 전건
  `unchanged`와 Source별 CollectionRun을 검증했다. post-admission DB에서
  manifest를 다시 만들 때 이미 승격된 identity를 baseline에서 제외해 같은
  manifest를 결정적으로 재적용할 수 있도록 audit/apply 계약을 보강했다
  (개발 기록)
- 홈·맞춤 추천·검색·북마크 UX: 홈 안내 문구 갱신, `/recommendations` 상단·결과 카드 `추가 확인 필요` 박스 제거, 검색 결과 자격 확인 뱃지 제거, 정책 카드 D-Day(`D-nn`) 표시, 북마크 페이지 전체 데이터 삭제 버튼 제거.
  (개발 기록)
- 관리자 대시보드(`/admin`): 최신 CollectionRun 집계 요약·수집 시각·품질 metric card. 데이터 품질(`/admin/quality`): 최근 회차별 failed·invalid·duplicate 집계 비교·drill-down.
  (개발 기록)
- 홈 추천 정책: 프로필 저장 조건(region·age·category) 있을 때 Recommendation API 연동·안내 캡션; 없을 때 open·상시 폴백(안내 문구 미노출).
  (개발 기록)
- 북마크 폴더: `···` 메뉴 바깥 클릭·ESC 닫기, 사용자 폴더 삭제 확인 modal(기본 폴더 보호).
  (개발 기록)
- 정책 상세 헤더: 제목 행 우측 북마크, 주관기관 아래 공식 신청·ICS 액션 바, ○ 요약 줄바꿈·`YYYYMMDD` 기간 정규화.
  (개발 기록)
- 홈 첫 화면 featured 정책: 마감·예정·지난 마감일 제외, 상태·분야 뱃지 semantic 컬러(상시 민트·모집중 블루·마감 레드).
  (개발 기록)
- 정책 목록·상세: 카드 신청기간 `YYYY.MM.DD` 정규화, 카테고리·상태 뱃지를 달력 테마와 일치, 상세 메타 줄바꿈·본문 ordered/bullet 리스트.
  (개발 기록)
- 정책 상세(`/programs/:id`): Summary Header(상태·D-Day·4대 메타)·섹션 카드·하단 Sticky CTA(북마크·공식 신청·ICS). `EligibilitySummary`·API schema 유지.
  (개발 기록)
- 북마크(`/favorites`): 탭 리스트 → 폴더 그리드 탐색기(브레드크럼, 정렬, 그리드/리스트 뷰, 폴더 진입). localStorage v2 schema 유지.
  (개발 기록)
- 홈 NL 검색: 결과·필터 칩·sidebar를 `/` URL state(`/?q=…`)에서 렌더; legacy `/search`는 query preserve redirect. 메인 컨텐츠 max-width 중앙 정렬. 프로필 저장 조건을 검색 API flat filter 기본값으로 merge.
  (개발 기록)
- 마감 달력(`/calendar`): ISO 날짜 정규화·정책명 폴백·칩 button 중첩 제거로 일정 칩 미노출 버그 수정.
  (개발 기록)
- 마감 달력(`/calendar`): 일정 칩 텍스트를 정책명(`title`)으로 표시(날짜 칸·all-day·주/일 뷰). 카테고리 색상 유지·말줄임 compact 스타일.
  (개발 기록)
- 마감 달력(`/calendar`): macOS/Apple Calendar 스타일 2패널 UI(분야 필터·미니 달력, Day/Week/Month/Year, all-day 카테고리 칩·일정 상세 modal). KST `application_start`·`application_end` 매핑·`.monthly-calendar__grid` E2E 호환 유지.
  (개발 기록)
- 북마크: localStorage schema v2(폴더·`bookmarks` entry), 기본 `기본 폴더`, 북마크 페이지 폴더 탭·`+ 새 폴더 만들기`, 저장 시 폴더 선택 모달. v1 flat `favorites[]`는 read 시 migrate.
  (개발 기록)
- 사용자 앱 sidebar: 메뉴 순서·라벨 정리(달력·관리자·사용자 프로필), sidebar 검색 링크 제거. `내 조건 저장`은 `/profile`에서만 편집 (홈 카드 제거). localStorage 조건은 맞춤 추천 등 기존과 동일 공유.
  (개발 기록)

- 4주차 실제 로컬 DB를 Migration `20260810_0006`과 정책 3,269건으로 정렬하고,
  지역 청년정책 109건의 멱등 적재와 서울·대구·부산 검색·상세 노출을 검증했다
  (개발 기록)
- DTL4-7에서 실제 PostgreSQL·Runtime·FastAPI·React를 연결해 관리자 데이터·
  CollectionRun·로그 정리, 공식 Source 자격요건, 추천·북마크·달력·알림·`.ics`
  세 Critical Path와 Release 1 검색·상세 회귀를 검증했다
  (개발 기록)
- DTL4-5에서 관리자 Policy·로그 Backend OpenAPI와 Frontend TypeScript·Mock을
  동일 DTO·pagination·오류 계약으로 정렬하고, 현재 로그 rotate 정리·감사와
  request/run/source correlation을 연결했다
  (개발 기록)
- 관리자 기본 PIN `0000`을 local client의 development/local/test로 제한하고,
  production token 서명은 전용 `ADMIN_TOKEN_SECRET` 없이는 fail-closed 처리했다
  (개발 기록)

### Fixed

- Windows clone·GitHub ZIP clean-room에서 공개 dataset 457건이 모두 partial이라
  정책 목록이 0건으로 보이고 첫 100건 뒤에 접근할 수 없던 문제를 수정했다.
  사용자 UI는 partial을 명시적으로 포함하고 5페이지 전체를 탐색하며, 추천 API의
  비표준 `기타`·`unknown` 값을 안전하게 정규화해 결과 렌더 crash를 제거했다
  ([문제 해결 기록](docs/troubleshooting/integration/windows_clone_zip_clean_room_recovery.md))
- Windows PowerShell clean-room에서 명시 project의 Volume 대신 기본 project를
  검사하던 문제, 없는 Volume의 native error, `Get-FileHash`·ACL module 자동 로드,
  `.git` 없는 ZIP의 env 보호 검사를 수정해 clone과 ZIP 양쪽 최초 실행·offline
  재실행을 통과시켰다
  ([문제 해결 기록](docs/troubleshooting/integration/windows_clone_zip_clean_room_recovery.md))
- Frontend 개발 dependency high 취약점 4건을 lockfile 갱신으로 0건으로 줄이고
  CI에 `npm audit --audit-level=high`를 추가했다

- 중앙 공개 dataset 발행이 worker destination hostname·Celery remote-control
  readiness와 불충분한 오류 정보 때문에 원인을 드러내지 못하던 문제를 PID·ready
  log 기반 검증과 안전한 오류 유형·worker log 진단으로 수정했다. GitHub Secret의
  라벨·줄바꿈 혼입을 key 값 한 줄로 바로잡아 다섯 번째 실행에서 발행을 완료했고
  readiness를 79초에서 4초로 94.9% 줄였다
  ([문제 해결 기록](docs/troubleshooting/integration/public_dataset_release_activation.md))
- Docker 관리자 수동 수집이 `running` 행만 만들고 실행되지 않던 문제를 실제
  Collector·Raw replay·DB 반영·terminal 상태로 연결하고, snapshot 고정 count를
  모든 재시작에 강제해 운영 데이터가 바뀌면 기동이 막히던 restore 검증을
  restore 직후 one-shot 단계로 분리했다
  ([문제 해결 기록](docs/troubleshooting/backend/docker_manual_collection_restart_recovery.md))
- Docker Acceptance 격리 사용성·QA에서 다른 province의 retired 지역 rule이
  천안 검색에 인천 정책을 포함하던 문제, `0세~0세` sentinel과 연령 제한 없음
  설명 충돌, unknown 자격의 `제한 없음 해당없음` 결측 표식 노출, 저장 분야가
  자연어 분야를 덮던 문제, Mock-first spec의 actual 경계 누락을 실제 UI·API
  재현으로 수정했다
  ([문제 해결 기록](docs/troubleshooting/integration/docker_acceptance_usability_consistency.md))

- 맞춤 추천이 사용자 지역·연령·분야의 확정 불일치와 마감 정책을 점수만 낮춰
  계속 반환하고 첫 200개 Policy만 평가하던 문제를 수정했다. 검색과 같은 3값
  판정으로 명시적 지역을 fail-closed 처리하고, 전체 승인 snapshot의 지역 rule을
  bulk 평가해 실제 3,273건 응답을 약 14.8초에서 약 1.4초로 개선했다
  ([문제 해결 기록](docs/troubleshooting/backend/recommendation_full_inventory_performance.md),
  개발 기록)
- review admission이 checkpoint의 과거 `open`을 재사용하고 canonical region
  rule을 만들지 않던 문제를 수정해, 실행 기준일 재판정과 region/search
  projection을 fail-closed 검증하도록 했다
  (개발 기록)
- `run.bat`가 Node.js를 시스템 PATH에서만 찾아 Codex 데스크톱 환경에서 시작하지
  못하던 문제를 수정하고, 번들 Node.js 자동 탐색과 명시적 실행 파일 인자를 추가
- Windows actual 실행기가 DB 이름을 `cheongnyeon_alimi`로 고정해 격리 검증 DB를
  선택할 수 없던 문제를 수정하고, 검증된 `DatabaseName` 인자로 pgpass 대상 DB를
  명시할 수 있게 했다
  (검증 안내)
- Runtime 로그 `backend/logs/app.log`가 Git에 추적되던 경계를 정리하고 Backend
  로그 디렉터리 전체를 비추적 대상으로 고정했다
- DTL4-6에서 Integration 08 승인 Eligibility DTO와 충돌하던 과거 fixture id,
  개인 조건 비교·summary 새로고침 E2E/API hook·미사용 CSS를 제거하고 현재
  seed·evidence 원문 계약으로 Browser 회귀와 수동 검증 문서를 정렬
  (개발 기록)
- Frontend `/` white screen after FE9-01: harden localStorage recovery notice reads,
  module-init storage sync, layout error boundaries, and route error fallback
  (개발 기록)
- Frontend W4-F9 cross-Forest integration (FE9-01): shared admin 401 redirect hook,
  localStorage corrupt recovery banner, AdminLoginPage cooldown lint
  (개발 기록)
- Admin policy data table row detail drawer did not appear when clicking
  상세보기: replaced grid sidebar with fixed overlay slide-in drawer and
  `isDrawerOpen` state on `/admin/policies`
  (개발 기록)
- Frontend `/`·`/favorites` 접속 시 404 UI가 뜨던 문제: `useFavorites` snapshot
  참조 불안정으로 layout error boundary가 트리거되던 것을 수정
  (개발 기록)
- 충북의 과거 상시모집 공고에서 종료된 운영기간을 우선 판정해 만료 정책이 현재
  신청 가능한 정책으로 노출되지 않도록 보정

- 명시적 지역 자연어 검색을 match-only로 격리하고 광주·인천·울산·제주 정책 상세의
  공식 지역·대상·시행 기관 근거와 대구·서울의 정책 단위 지역 표기를 보강해 실제
  신청 가능한 지역 정책 68건을 검색 DB에 추가
  (개발 기록)

- Browser navigation timeout 뒤 요청 URL과 준비 DOM을 검증하고 locator 신호
  대신 페이지 DOM selector를 polling해, 정상 로드된 충북·울산 페이지의 false
  timeout으로 인한 중단을 방지
  (개발 기록)

- 울산 목록 상태 badge와 상세 제목·본문 렌더 race를 구분하고 identity별 tab
  격리로 597건의 신청기간 관찰 상태를 전건 보강
  (개발 기록)

- 충북 공식 상세의 한글 순번 `제출기한`을 `훈련기간`과 구분해 신청 마감으로
  추출하고, 단일 신청 마감일을 open·ended 상태로 판정하도록 보강
  (개발 기록)

- 강원 상세 실패 325건을 목록 page 컨텍스트가 유실된 동일 유형으로 분류해
  대표 3건만 복구하고, 제주 비정형 상세 2건은 공식 제목 기한·등록일 근거로
  종료 판정을 복구하면서 failed 자동 승격을 제한
  (개발 기록)

- 충북·울산·대전·강원 공식 상세의 신청기간 selector와 서울 compact 날짜 해석을
  보강하고, 원문 빈 값·목록 total/identity drift는 checkpoint·DB 판정을 바꾸지
  않은 채 review 근거로 보존
  (개발 기록)

- 대전 current-only identity를 판정에 편입하지 않는 명시적 교집합 재캡처 경계와
  강원 기존 상세 12건 제한 보강으로 두 Source의 legacy 필드 상태를 해소
  (개발 기록)

- 서울시·자치구 정책 110건을 공식 목록과 재대조하고 review 97건의 구조화 상세를
  제한 재캡처해 빈 신청기간과 실제 라벨 부재를 구분
  (개발 기록)

- 대구 현재목록의 identity 교체 drift를 checkpoint 고정 상세 URL·제목 계약으로
  격리하고, 기존 197건만 제한 재캡처해 legacy 필드 상태를 전건 해소
  (개발 기록)

- 광주 접수중 목록의 추가 4·누락 1 identity 교체 drift를 checkpoint 고정
  `policyId` 상세 계약으로 격리하고, 기존 31건만 제한 재캡처해 legacy 필드
  상태를 전건 해소
  (개발 기록)

- 인천 접수중 목록에서 빠진 마감 전환 정책을 checkpoint 고정 `poly_seq` 상세
  계약으로 격리하고, 기존 28건의 상세 필드 관찰 상태를 전건 보강
  (개발 기록)

- 전북 checkpoint 89건, 경북 review 58건, 경남 review 28건의 공식 상세 근거를
  재대조하고 HTML entity와 공식 경남 JSON endpoint를 반영해 legacy 필드 상태를
  전건 해소
  (개발 기록)

- 제주 review 207건의 공식 상세를 checkpoint 고정 `wr_id` 계약으로 보강해 지역
  Source 전체 legacy 필드 상태를 0으로 해소하고 RYP8 완료 감사를 통과
  (개발 기록)

### Added

- 강원 잔여 상세 실패를 초기·중기·후기 page 순환 canary로 읽기 전용 감시하고,
  경남·제주 종료 이력·필드 null 상태·실패 원인·checkpoint outcome을 함께
  대조하는 RYP8 완료 감사를 추가
  (개발 기록)

- 지역 Source review 1,903건을 사유·필드 coverage로 감사하고, 공식 목록 scope와
  정책별 지역·청년 근거를 함께 요구하는 안전한 승격 계약 및 Browser 필드 관찰
  상태를 추가
  (개발 기록)

- 13개 승인 지역 Source에서 4,606개 정책 identity를 checkpoint 기반으로 전체
  순회해 수집 인프라 기준 신청 가능성·지역 고유성·온통청년/복지로 중복을
  누락 없이 분류하고,
  accepted 부산 16건·경북 2건만 PostgreSQL에 동기화
  (개발 기록)

- 정책 상세에 Source 근거가 있는 신청 조건·제외 조건·필요 서류·공개 시설
  문의처 요약을 추가하고 NormalizedProgram 1.2·PostgreSQL JSONB·반응형 UI와
  실제 세로 인수로 연결
  (개발 기록)
- 승인한 천안청년센터 공개 공지를 제한 수집하고 Runtime Raw → 정규화 →
  PostgreSQL → partial 정책 상세 API까지 재처리하는 첫 공식 웹 Source 기반 추가
  (개발 기록)
- 반복 수집에서 metadata-only 재실행·business 변경·실행 내 중복·실패
  rollback을 구분하고 품질 집계를 CollectionRun에 영속하는 Data 03 기반 추가
  (개발 기록)
- 천안청년센터 공개 공지 표본과 최소 수집·비재배포 경계를 포함한 v0.5.0
  `W4-G0` 계약 기준선 승인
  (개발 기록)
- Frontend W4-F10 week4 regression matrix E2E (FE9-02): `week4-regression.spec.ts`
  covering admin·eligibility·user·Release 1 golden·mobile cross checks
  (개발 기록)
- Frontend CollectionRun Admin DTO·Mock·route shell (FE3-00): admin session·
  collection run types, Mock-first API client, nested `/admin` layout
  (개발 기록)
- Frontend CollectionRun Admin PIN session·run list·manual trigger (FE3-01~04):
  protected `/admin` routes, filters·detail·confirm dialog
  (개발 기록)
- Frontend CollectionRun Admin Browser E2E (FE3-05): Playwright admin PIN·run
  list·detail·manual trigger Mock-first flow
  (개발 기록)
- Frontend CollectionRun Admin Toast·a11y (FE3-06): shared ApiErrorToast·401/429/5xx
  admin wiring·keyboard PIN·confirm Escape·Browser E2E
  (개발 기록)
- Frontend admin API clients aligned to Backend 04·05 Real OpenAPI (FE3-00):
  `size`/`pages` list envelope, dual error parsing, Bearer header option
  (개발 기록)
- Frontend 홈 저장 조건 UI(FE5-02): region·age·category 브라우저 localStorage
  저장·복원·조건-only 초기화(북마크 유지)
  (개발 기록)
- Frontend KST D-Day·마감 달력·in-app 알림·`.ics`·전체 데이터 삭제 (FE5-03~05,
  FE5-08): `/calendar`, `/notifications`, detail `.ics` download
  (개발 기록)
- Frontend eligibility summary DTO·Mock detail fixtures (FE7-00): complete·
  partial·unknown 표본 envelope와 contract tests
  (개발 기록)
- Frontend eligibility summary card UI (FE7-01~04): policy detail 핵심 신청 조건
  sections, local condition badges, evidence links (Mock-first)
  (개발 기록)
- Frontend Eligibility Summary Browser E2E (FE7-05): Playwright complete·partial·
  unknown mock detail fixtures, comparison badges, search golden regression
  (개발 기록)
- Frontend Eligibility Detail Toast·a11y (FE7-06): policy detail summary refetch
  5xx Toast·422 inline·section nav·long text expand Browser E2E
  (개발 기록)
- Frontend admin observability DTO·Mock handlers (FE8-00): read-only policy
  projection list/detail·log file/event pagination·safe error contract
  (개발 기록)
- Frontend admin observability UI (FE8-01~04): `/admin/policies` table·row detail,
  `/admin/logs` event filter·refresh, archive delete·rotate confirm (Mock-first)
  (개발 기록)
- Frontend Admin Observability Browser E2E (FE8-05): Playwright PIN session·policy
  table·log view·maintenance confirm·admin nav regression
  (개발 기록)
- Frontend Admin Observability Toast·a11y (FE8-06): policy·log ApiErrorToast·409
  delete conflict·table keyboard·column toggle Escape·Browser E2E
  (개발 기록)
- Frontend recommendation UI (FE6-01~04): `/recommendations` 조건 form·FE5
  localStorage 연동·결과·reason·error/retry·region collapse
  (개발 기록)
- Frontend Recommendation Browser E2E (FE6-05): Playwright structured
  recommendation·empty·cross-route·search golden Mock-first flow
  (개발 기록)
- Frontend cross-route policy identity (FE5-06): shared detail path·추천 결과
  favorite toggle·sidebar `/recommendations`·`/calendar` nav
  (개발 기록)
- Frontend User Service Browser E2E (FE5-07): Playwright favorites·conditions·
  calendar·notifications·reset·cross-route Mock-first flow
  (개발 기록)

## [0.1.0] - 2026-08-06

### Added

- Windows에서 실제 PostgreSQL·Backend·Frontend를 한 터미널에 실행하고 홈
  화면을 여는 범용 `run.bat` 추가. 같은 터미널의 `Ctrl+C`로 함께 종료
  ([실행 안내](README.md))
- 정책 검색·상세에 실제 자격 충족을 확정하지 않는다는 공통 안내를 추가하고,
  새 golden query의 actual API 첫 결과·근거·출처·수집 시각을 Browser·E2E로 검증
  (개발 기록)
- Release snapshot의 신청기간을 Source 전용 필드 근거로만 구조화하고 본문 날짜
  미승격·기간 상태 일치·golden 정책 근거를 검증하는 오프라인 안전성 감사 추가
  (데이터 Profile)

- 신청 가능한 `청년단기숙소 지원사업`을 Release 1 golden으로 고정하고 snapshot·정책 identity·순위·unknown·응답시간을 검증하는 HTTP acceptance 계약과 감사 도구 추가

- 정책 상세에서 기존 공개 DTO의 데이터 출처와 수집 시각을 KST로 확인할 수
  있게 표시
  (개발 기록)
- 실제 정책 3,156건 snapshot을 PostgreSQL 검색 API와 Frontend 실제 API
  모드로 연결하고 검색·pagination·상세·상태 E2E 10건을 검증
  (개발 기록)
- `GET /api/v1/policies/search` 자연어 정책 검색 API 엔드포인트 및 규칙 기반 파서, PostgreSQL Query Builder, Golden Query 통합 테스트 구현
  (개발 계획)

### Fixed

- 실제 Release snapshot 검색의 빈 결과 화면이 합성 canonical Seed 기반이라고
  잘못 안내하던 문구를 실제 snapshot·수집 범위·수집 시점 경계와 일치하도록
  수정
  (개발 기록)
- 자연어 정책 검색에서 대화형·일반 term의 OR 일치가 결과를 과도하게
  넓히던 문제를 구체 term anchor로 수정해 Release 1 golden을 1위·2초
  이내로 안정화
  (개발 기록)

- Backend를 문서화된 `backend` 작업 디렉터리에서 실행할 때 검색 판정
  서비스가 저장소 루트 Data 패키지를 요구하던 import 회귀를 제거하고,
  Frontend Mock의 welfare 기대값을 현재 canonical Seed와 동기화
  (개발 기록)
- React Router RSC advisory high 2건에 대응해 client-only Frontend를
  `react-router@8.3.0`으로 전환하고 자동·HTTP·Browser 라우팅 회귀로
  기존 Policy Discovery 동작을 확인
  (개발 기록)
- Policy 최초 적재 시 `updated_at < created_at`이 될 수 있던 순서를 단일
  UTC write instant와 DB constraint로 바로잡고, 기존 역전 행 보정 및
  update 시각 비감소를 보장
  (개발 기록)
- Backend SQL logging을 명시적 opt-in·parameter 비노출 방식으로 안전화하고
  미처리 예외의 DB URL·비밀번호 상세 노출 가능성과 Unicode logging 오류를
  제거
  (개발 기록)

### Added

- Policy Search 결과 카드에서 `/programs/{id}` 상세 이동 및 partial opt-in query 전달 추가 (개발 기록)
- 홈 hero 검색·추천 검색어 칩에서 `/search?q=` golden flow 진입 추가 (개발 기록)
- Policy Search 우측 사이드바 Reason·미해석 키워드 UX 추가 (개발 기록)
- Policy Search partial/unknown 배지 분리 및 unconfirmed_conditions tooltip 추가 (개발 기록)
- Policy Search 해석 조건 칩 remove/edit/add 및 URL flat param 동기화 추가 (개발 기록)
- Policy Search pagination UI 및 URL `page` sync, stale response guard 추가 (개발 기록)
- Policy Search Loading/Empty/Error shell 및 SearchBar 입력 수정·지우기 버튼 추가 (개발 기록)
- Policy Search `/search` 페이지, SearchBar·URL flat param 동기화, Mock 기반 React Query fetch 추가 (개발 기록)
- Gate G1 Policy Search TypeScript contract types를 production 타입 경로로 승격 (개발 기록)
- 호출 예산·완전성 manifest를 사용하는 온통청년·복지로 다중 page 릴리스
  snapshot 수집과 고정 snapshot 재처리를 추가하고, 실제 정책 3,159건의
  PostgreSQL bootstrap·멱등 재실행 및 실제 검색 품질 Profile을 검증
  (개발 기록)
- `NormalizedProgram` 1.1.0 검색 데이터 계약, 1.0.0 compatibility adapter,
  공식 법정동 기반 versioned 지역·계층·별칭 Seed, 지역 적용 관계 경계
  Fixture, PostgreSQL 지역 관계·검색 projection Migration, 온통청년·복지로
  Source 검색 필드·exact 지역 Adapter와 Policy·지역 규칙·versioned projection
  원자적·멱등 importer, 지역·연령·신청 상태 3값 판정 primitive 추가
  (개발 기록)
- Frontend Policy Discovery Slice: 공개 `PolicyDto`, canonical Seed Mock
  adapter, `/api/v1/policies` 목록·상세 Client와 partial opt-in 정책
  목록·상세·필터 UI 기반 추가
  (개발 기록)
- 저장된 Runtime Raw의 무네트워크 PostgreSQL 재처리와 idempotent 적재,
  향후 관리자 기능을 위한 안전한 Seed·Runtime `CollectionRun` 실행 이력 기반
  추가
  (개발 기록)
- PostgreSQL Migration, 검증 우선·원자적 Seed importer, 정확한 JSONB 배열
  필터와 품질 일관성을 갖춘 Policy Repository·API 종단 기반 완성
  (개발 기록)
- `NormalizedProgram` 1.0.0 기반 PostgreSQL/SQLite ORM Policy 모델, Seed Upsert Importer CLI(`python -m app.cli.import_seed`) 및 정책 목록·상세 조회 API 추가 (개발 기록)
- 온통청년·복지로 source Collector·Extractor, 비밀정보 안전한 공통 HTTP·CLI,
  Raw 보존부터 provenance 기반 정규화·Schema 검증·품질 분류와 결정적
  Fixture·canonical Seed까지의 데이터 파이프라인 기반 추가
  (개발 기록)
- 문서 탐색·라우팅, 협업·의존성·통합 배포 책임, Architecture·Data 기준선과
  Forest별 계획·개발 기록을 연결하는 Docs System 구축
  (개발 기록)
- 문서 링크, 필수 파일, 비밀값 패턴, Forest 담당 영역·대응과 색인 등록을
  확인하는 로컬 문서 검증 기반 추가
  (개발 기록)
