# 변경 이력

이 파일은 `cheongnyeon-alimi`의 사용자와 팀에 의미 있는 변경 사항을
기록한다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
프로젝트는 [Semantic Versioning](https://semver.org/lang/ko/)을 사용한다.

## [Unreleased]

### Added

- 정책 상세 API에 Source 근거가 있는 신청 조건·제외 조건·필요 서류·공개 시설
  문의처 요약을 추가하고 NormalizedProgram 1.2·PostgreSQL JSONB로 연결
  ([계약](docs/data/eligibility_summary_contract.md))
- 승인한 천안청년센터 공개 공지를 제한 수집하고 Runtime Raw → 정규화 →
  PostgreSQL → partial 정책 상세 API까지 재처리하는 첫 공식 웹 Source 기반 추가
  ([개발 기록](docs/development/development_notes/data/public_https_policy_ingestion.md))
- 반복 수집에서 metadata-only 재실행·business 변경·실행 내 중복·실패
  rollback을 구분하고 품질 집계를 CollectionRun에 영속하는 Data 03 기반 추가
  ([개발 기록](docs/development/development_notes/data/recurrent_collection_quality_operations.md))
- 천안청년센터 공개 공지 표본과 최소 수집·비재배포 경계를 포함한 v0.5.0
  `W4-G0` 계약 기준선 승인
  ([개발 기록](docs/development/development_notes/integration/v0_5_0_contract_baseline.md))

## [0.1.0] - 2026-08-06

### Added

- Windows에서 실제 PostgreSQL·Backend·Frontend를 한 터미널에 실행하고 홈
  화면을 여는 범용 `run.bat` 추가. 같은 터미널의 `Ctrl+C`로 함께 종료
  ([실행 안내](README.md))
- 정책 검색·상세에 실제 자격 충족을 확정하지 않는다는 공통 안내를 추가하고,
  새 golden query의 actual API 첫 결과·근거·출처·수집 시각을 Browser·E2E로 검증
  ([개발 기록](docs/development/development_notes/integration/release_1_acceptance.md))
- Release snapshot의 신청기간을 Source 전용 필드 근거로만 구조화하고 본문 날짜
  미승격·기간 상태 일치·golden 정책 근거를 검증하는 오프라인 안전성 감사 추가
  ([데이터 Profile](docs/data/release_dataset_profile.md))

- 신청 가능한 `청년단기숙소 지원사업`을 Release 1 golden으로 고정하고 snapshot·정책 identity·순위·unknown·응답시간을 검증하는 HTTP acceptance 계약과 감사 도구 추가

- 정책 상세에서 기존 공개 DTO의 데이터 출처와 수집 시각을 KST로 확인할 수
  있게 표시
  ([개발 기록](docs/development/development_notes/integration/release_1_acceptance.md))
- 실제 정책 3,156건 snapshot을 PostgreSQL 검색 API와 Frontend 실제 API
  모드로 연결하고 검색·pagination·상세·상태 E2E 10건을 검증
  ([개발 기록](docs/development/development_notes/integration/release_1_acceptance.md))
- `GET /api/v1/policies/search` 자연어 정책 검색 API 엔드포인트 및 규칙 기반 파서, PostgreSQL Query Builder, Golden Query 통합 테스트 구현
  ([개발 계획](docs/development/develop_plan/backend/06_policy_search.md))

### Fixed

- 실제 Release snapshot 검색의 빈 결과 화면이 합성 canonical Seed 기반이라고
  잘못 안내하던 문구를 실제 snapshot·수집 범위·수집 시점 경계와 일치하도록
  수정
  ([개발 기록](docs/development/development_notes/integration/release_1_acceptance.md))
- 자연어 정책 검색에서 대화형·일반 term의 OR 일치가 결과를 과도하게
  넓히던 문제를 구체 term anchor로 수정해 Release 1 golden을 1위·2초
  이내로 안정화
  ([개발 기록](docs/development/development_notes/integration/release_1_acceptance.md))

- Backend를 문서화된 `backend` 작업 디렉터리에서 실행할 때 검색 판정
  서비스가 저장소 루트 Data 패키지를 요구하던 import 회귀를 제거하고,
  Frontend Mock의 welfare 기대값을 현재 canonical Seed와 동기화
  ([개발 기록](docs/development/development_notes/integration/policy_search_data_foundation.md))
- React Router RSC advisory high 2건에 대응해 client-only Frontend를
  `react-router@8.3.0`으로 전환하고 자동·HTTP·Browser 라우팅 회귀로
  기존 Policy Discovery 동작을 확인
  ([개발 기록](docs/development/development_notes/frontend/react_router_advisory.md))
- Policy 최초 적재 시 `updated_at < created_at`이 될 수 있던 순서를 단일
  UTC write instant와 DB constraint로 바로잡고, 기존 역전 행 보정 및
  update 시각 비감소를 보장
  ([개발 기록](docs/development/development_notes/backend/policy_runtime_safety.md))
- Backend SQL logging을 명시적 opt-in·parameter 비노출 방식으로 안전화하고
  미처리 예외의 DB URL·비밀번호 상세 노출 가능성과 Unicode logging 오류를
  제거
  ([개발 기록](docs/development/development_notes/backend/policy_runtime_safety.md))

### Added

- Policy Search 결과 카드에서 `/programs/{id}` 상세 이동 및 partial opt-in query 전달 추가 ([개발 기록](docs/development/development_notes/frontend/policy_search.md))
- 홈 hero 검색·추천 검색어 칩에서 `/search?q=` golden flow 진입 추가 ([개발 기록](docs/development/development_notes/frontend/policy_search.md))
- Policy Search 우측 사이드바 Reason·미해석 키워드 UX 추가 ([개발 기록](docs/development/development_notes/frontend/policy_search.md))
- Policy Search partial/unknown 배지 분리 및 unconfirmed_conditions tooltip 추가 ([개발 기록](docs/development/development_notes/frontend/policy_search.md))
- Policy Search 해석 조건 칩 remove/edit/add 및 URL flat param 동기화 추가 ([개발 기록](docs/development/development_notes/frontend/policy_search.md))
- Policy Search pagination UI 및 URL `page` sync, stale response guard 추가 ([개발 기록](docs/development/development_notes/frontend/policy_search.md))
- Policy Search Loading/Empty/Error shell 및 SearchBar 입력 수정·지우기 버튼 추가 ([개발 기록](docs/development/development_notes/frontend/policy_search.md))
- Policy Search `/search` 페이지, SearchBar·URL flat param 동기화, Mock 기반 React Query fetch 추가 ([개발 기록](docs/development/development_notes/frontend/policy_search.md))
- Gate G1 Policy Search TypeScript contract types를 production 타입 경로로 승격 ([개발 기록](docs/development/development_notes/frontend/policy_search.md))
- 호출 예산·완전성 manifest를 사용하는 온통청년·복지로 다중 page 릴리스
  snapshot 수집과 고정 snapshot 재처리를 추가하고, 실제 정책 3,159건의
  PostgreSQL bootstrap·멱등 재실행 및 실제 검색 품질 Profile을 검증
  ([개발 기록](docs/development/development_notes/data/release_dataset_bootstrap.md))
- `NormalizedProgram` 1.1.0 검색 데이터 계약, 1.0.0 compatibility adapter,
  공식 법정동 기반 versioned 지역·계층·별칭 Seed, 지역 적용 관계 경계
  Fixture, PostgreSQL 지역 관계·검색 projection Migration, 온통청년·복지로
  Source 검색 필드·exact 지역 Adapter와 Policy·지역 규칙·versioned projection
  원자적·멱등 importer, 지역·연령·신청 상태 3값 판정 primitive 추가
  ([개발 기록](docs/development/development_notes/integration/policy_search_data_foundation.md))
- Frontend Policy Discovery Slice: 공개 `PolicyDto`, canonical Seed Mock
  adapter, `/api/v1/policies` 목록·상세 Client와 partial opt-in 정책
  목록·상세·필터 UI 기반 추가
  ([개발 기록](docs/development/development_notes/frontend/policy_discovery.md))
- 저장된 Runtime Raw의 무네트워크 PostgreSQL 재처리와 idempotent 적재,
  향후 관리자 기능을 위한 안전한 Seed·Runtime `CollectionRun` 실행 이력 기반
  추가
  ([개발 기록](docs/development/development_notes/integration/policy_data_database_integration.md))
- PostgreSQL Migration, 검증 우선·원자적 Seed importer, 정확한 JSONB 배열
  필터와 품질 일관성을 갖춘 Policy Repository·API 종단 기반 완성
  ([개발 기록](docs/development/development_notes/backend/policy_persistence_hardening.md))
- `NormalizedProgram` 1.0.0 기반 PostgreSQL/SQLite ORM Policy 모델, Seed Upsert Importer CLI(`python -m app.cli.import_seed`) 및 정책 목록·상세 조회 API 추가 ([개발 기록](docs/development/development_notes/backend/policy_baseline.md))
- 온통청년·복지로 source Collector·Extractor, 비밀정보 안전한 공통 HTTP·CLI,
  Raw 보존부터 provenance 기반 정규화·Schema 검증·품질 분류와 결정적
  Fixture·canonical Seed까지의 데이터 파이프라인 기반 추가
  ([개발 기록](docs/development/development_notes/data/data_pipeline.md))
- 문서 탐색·라우팅, 협업·의존성·통합 배포 책임, Architecture·Data 기준선과
  Forest별 계획·개발 기록을 연결하는 Docs System 구축
  ([개발 기록](docs/development/development_notes/integration/docs_system.md))
- 문서 링크, 필수 파일, 비밀값 패턴, Forest 담당 영역·대응과 색인 등록을
  확인하는 로컬 문서 검증 기반 추가
  ([개발 기록](docs/development/development_notes/integration/docs_system.md))
