# cheongnyeon-alimi 문서 안내

이 문서는 프로젝트 문서의 진입점이다. 개발자와 AI Agent는 작업을
시작하기 전에 이 문서와 작업 영역에 해당하는 정책 문서를 확인한다.

## 현재 문서

- [문서화 정책](governance/documentation_policy.md): 문서의 역할, 갱신
  기준, 작성 및 검증 규칙
- [브랜치 전략](governance/branch_strategy.md): 브랜치 역할, 이름과 병합 흐름
- [커밋 작성 규칙](governance/commit_convention.md): Conventional Commits
  형식과 커밋 구성 기준
- [코드 리뷰 정책](governance/code_review.md): PR 작성, 리뷰와 병합 기준
- [역할과 책임](governance/role_assignment.md): Data·Backend·Frontend,
  Team Leader의 Integration·Deploy, 보고서·사용성 리뷰·QA 책임
- [시스템 아키텍처 개요](architecture/overview.md): 목표 구조와 계층별 책임
- [시스템 흐름](architecture/system_flow.md): 외부 소스부터 Web UI까지의
  데이터 흐름
- [컨테이너 구조](architecture/container_structure.md): 초기 실행 단위,
  영역별 산출물과 통합·배포 시점
- [Policy 데이터베이스 매핑](architecture/policy_database_mapping.md):
  NormalizedProgram 1.2.0의 37개 논리 필드, Eligibility Summary와 행정구역·검색 projection
  PostgreSQL·Importer·공개 API 경계
- [CollectionRun 데이터베이스 계약](architecture/collection_run_database.md):
  Seed·Runtime 실행 이력의 PostgreSQL 필드, 상태 전이와 보안 경계
- [아키텍처 결정 기록](architecture/decisions/README.md): ADR 작성 및 변경
  관리 규칙
- [데이터 소스](data/data_sources.md): 데이터 소스 등록 기준과 현재 확인 상태
- [Source Profile](data/source_profiles.md): 온통청년·복지로 API와 천안청년센터
  공개 공지의 요청 계약, 실제 응답·표본 구조와 호출 제약
- [데이터 Schema 기준선](data/data_schema.md): Raw, Extracted와 Normalized
  데이터 계약과 Source Adapter 원칙
- [RawPolicyDocument JSON Schema](../data/schema/raw_policy_document.schema.json):
  원본 byte와 수집 메타데이터의 실행 가능한 Raw 계약
- [NormalizedProgram JSON Schema](../data/schema/normalized_program.schema.json):
  정규화 필드, provenance와 품질 분류의 실행 가능한 계약
- [Eligibility Summary 공통 계약](data/eligibility_summary_contract.md):
  제외 조건·필요 서류·공개 시설 연락처와 Source evidence의 승인 의미
- [EligibilitySummary JSON Schema](../data/schema/eligibility_summary.schema.json):
  Data·Backend·Frontend가 공유하는 실행 가능한 nested 계약
- [Regional Youth Policy Source Inventory JSON Schema](../data/schema/regional_youth_policy_source_inventory.schema.json):
  지역 포털 후보·preflight·승인 경로와 행정구역 mapping 상태의 실행 계약
- [지역 청년정책 Source inventory](../data/reference/regional_youth_policy_sources.json):
  17개 지역 포털의 RYP1 action profile과 13개 승인·3개 차단·1개 제외 판정
- [Supplemental Official Policy Inventory JSON Schema](../data/schema/supplemental_official_policy_inventory.schema.json):
  Data 06 XLSX 후보 lineage·오류 격리와 공식 Source preflight 실행 계약
- [Supplemental Duplicate Audit JSON Schema](../data/schema/supplemental_official_policy_duplicate_audit.schema.json):
  온통청년·복지로 snapshot·PostgreSQL 선행 중복 감사 계약
- [Data 06 후보·Source inventory](../data/reference/supplemental_official_policy_inventory.json):
  URL 64행 정제 결과와 approved 5·blocked 1·rejected 9 Source 판정
- [Data 06 선행 중복 감사](../data/reference/supplemental_official_policy_duplicate_audit.json):
  exact duplicate 26·review 11·잠정 신규 19·비교 제외 4 판정
- [Review Admission 규칙](data/review_admission_rules.md):
  taxonomy v2와 versioned `promote_partial`·보류·hard exclusion 계약
- [Review Admission Audit JSON Schema](../data/schema/review_admission_audit.schema.json):
  identity·근거 code·provenance·fingerprint 기반 감사 manifest 계약
- [정규화 규칙](data/normalization_rules.md): 날짜, 검색 배열, 지역, 연령과
  카테고리 변환 기준
- [수집 정책](data/collection_policy.md): HTTP, Raw 보존, 보안과 라이선스
  원칙
- [공개 정책 bootstrap dataset 계약](data/public_policy_dataset.md):
  재배포 Source·field allowlist, versioned manifest·hash와 공개 Runtime 경계
- [공개 dataset 사용자 결과 동등성 계약](data/public_dataset_parity.md):
  작성자 DB와 공개 bootstrap 사이의 Source·안전성 차이 fail-closed 감사
- [정책 생명주기 계약](data/policy_lifecycle.md): 관측·검증·inactive 시각,
  마감 즉시 제외와 완전 수집에서만 허용하는 soft-deactivation 경계
- [행정구역 기준정보](data/administrative_regions.md): 공식 법정동 snapshot,
  versioned 지역·계층·별칭·유효기간 Seed와 exact code 해석 경계
- [Fixture와 Seed 계약](data/fixture_seed_contract.md): 합성 Raw부터
  canonical Seed까지의 재생성·소비자 검토 기준
- [Forest 개발 계획](development/develop_plan/README.md): Forest별 범위,
  Slice와 완료 기준
- [Release와 Milestone 계획](development/develop_plan/release_roadmap.md):
  `v0.1.0`, `v0.5.0`, `v1.0.0` 목표와 릴리스 완료 조건
- [전체 Forest 로드맵](development/develop_plan/forest_roadmap.md):
  완료 기반과 릴리스별 후속 Forest·의존 순서
- [주차별 실행 계획](development/develop_plan/weekly_delivery_plan.md):
  1~6주차 인계 순서와 릴리스 검증 게이트
- [주차별 상세 실행 계획](development/weekly_plan/README.md): 주차별 선행
  관계, 병렬 작업, 역할과 검증 Gate
- [3주차 상세 실행 계획](development/weekly_plan/week_03_release_1.md):
  실데이터 정책 검색과 `v0.1.0` 실행 순서, Gate G4와 publication 완료 상태
- [3주차 Data·Team Leader 실행 계획](development/weekly_plan/week_03_data_team_leader.md):
  실데이터 수집·적재와 통합·릴리스 판정 Slice
- [3주차 검색 계약 Gate G1 인수인계](development/weekly_plan/week_03_search_contract_handoff.md):
  Backend 06·Frontend 04 공통 시작 커밋, 고정 계약, 역할별 초안과 공동 승인 기준
- [4주차 상세 실행 계획](development/weekly_plan/week_04_v0_5_0.md):
  공식 웹 Source·자격요건과 사용자·관리자 기본 기능 전체의 W4-G0 계약,
  병렬 실행과 Release 2 midpoint
- [4주차 Data·Team Leader 실행 계획](development/weekly_plan/week_04_data_team_leader.md):
  Data 03·04, 자격요건 evidence, 공동 계약과 W4-G0~G4 actual 통합·판정
- [5주차 상세 실행 계획](development/weekly_plan/week_05_release_2.md):
  Data·Backend·Frontend 안정화, 사용성 리뷰·QA와 Release 2 `v0.5.0` 판정
- [5주차 Data·Team Leader 실행 계획](development/weekly_plan/week_05_data_team_leader.md):
  Data 06 SOP0~SOP5, W5-G0~G2 actual 인수·독립 검증과 Release 2 판정
- [Review Admission Forest 계획](development/develop_plan/integration/10_review_admission_docker_acceptance.md):
  DB 보유 PC 최신 review 재판정·partial 적재와 새 데이터 기준선 인계
- [Docker Acceptance Environment 계획](development/develop_plan/deploy/01_docker_acceptance_environment.md):
  동일 Acceptance snapshot의 Docker·clean-room·BE·FE·리뷰어 환경 인수
- [Production Data Refresh and Delivery 계획](development/develop_plan/deploy/02_production_data_refresh_delivery.md):
  공개 normalized dataset·정책 생명주기·Celery/Redis 중앙 수집·Production
  Compose·CI/CD와 clean-room Final Gate
- [6주차 Final Release 실행 계획](development/weekly_plan/week_06_final_release.md):
  `W6-P0`~`W6-P5` Critical Path와 `W6-G0_FINAL_RELEASE_PASS`
- [오픈소스 개발대회 제출 준비 체크리스트](contest/open_source_submission_checklist.md):
  `v1.0.2` 공개 저장소·README·clone/ZIP·신규 Windows clean-room Gate
- [v1.0.2 공개 데이터·검색·추천 QA 개선 기록](troubleshooting/integration/v1_0_2_qa_improvements.md):
  작성자·심사자 활성 dataset 동등성, 지역 검색, 복수 분야·관심 분야, 정렬과
  홈 추천 통합의 실제 구현·Docker·API·Browser 검증
- [Production Data Refresh and Delivery 개발 기록](development/development_notes/deploy/production_data_refresh_delivery.md):
  W6-P0 공개 dataset 계약부터 W6-P5 clone·ZIP clean-room 457건 actual 결과
- [Production 배포와 데이터셋 발행](operations/production_delivery.md): GHCR
  digest image·Nginx Compose·CI와 dataset promotion·rollback 절차
- [Docs System Forest 계획](development/develop_plan/integration/01_docs_system.md)
- [Data Pipeline Forest 계획](development/develop_plan/data/01_data_pipeline.md)
- [Release Dataset Bootstrap Forest 계획](development/develop_plan/data/02_release_dataset_bootstrap.md):
  Release 1 실제 정책 수집·PostgreSQL 적재와 품질 기준선
- [Release 1 실데이터 품질 Profile](data/release_dataset_profile.md):
  실제 snapshot 품질·검색 분포와 Backend·Frontend 안전 인계
- [Policy Discovery Forest 계획](development/develop_plan/frontend/01_policy_discovery.md)
- [React Router Advisory Review Forest 계획](development/develop_plan/frontend/02_react_router_advisory.md):
  현재 client-only Frontend의 RSC advisory 영향과 호환 대응 검토
- [CollectionRun Admin UI Forest 계획](development/develop_plan/frontend/03_collection_run_admin_ui.md):
  관리자 PIN·실행 이력·수동 실행 UI (FE3-xx Slice)
- [Policy Search Forest 계획](development/develop_plan/frontend/04_policy_search.md):
  Gate G1 승인 `GET /api/v1/policies/search` flat query 소비, Filter Chip·Reason UI
- [User Service Features Forest 계획](development/develop_plan/frontend/05_user_service_features.md):
  브라우저 로컬 조건·즐겨찾기·D-Day·내부 알림·`.ics` (FE5-xx Slice)
- [Recommendation UI Forest 계획](development/develop_plan/frontend/06_recommendation_ui.md):
  결정적 추천 조건·결과·이유 UI (FE6-xx Slice)
- [Eligibility Summary UI Forest 계획](development/develop_plan/frontend/07_eligibility_summary_ui.md):
  정책 상세 핵심 신청 조건 카드 (FE7-xx Slice)
- [Admin Observability UI Forest 계획](development/develop_plan/frontend/08_admin_observability_ui.md):
  관리자 정책 데이터 표·로그 콘솔 UI (FE8-xx Slice)
- [Integration Fix and Regression Forest 계획](development/develop_plan/frontend/09_integration_and_regression.md):
  W4-F9 통합 수정·W4-F10 전체 회귀 (FE9-xx Slice)
- [Backend Baseline Forest 계획](development/develop_plan/backend/01_policy_baseline.md)
- [Backend Policy Persistence Hardening Forest 계획](development/develop_plan/backend/02_policy_persistence_hardening.md):
  기존 Policy ORM·Importer·API를 실제 Migration·PostgreSQL·transaction
  기준으로 완성하는 Backend 후속 계획
- [Backend Policy Runtime Safety Forest 계획](development/develop_plan/backend/03_policy_runtime_safety.md):
  Policy timestamp 순서와 SQL parameter logging 안전화 계획
- [Backend Admin Access Control Forest 계획](development/develop_plan/backend/04_admin_access_control.md):
  관리자 API 공통 인증·권한 기준선 계획
- [Backend CollectionRun Admin API Forest 계획](development/develop_plan/backend/05_collection_run_admin_api.md):
  실행 이력 조회·수동 실행의 관리자 API 계획
- [Backend Policy Search Forest 계획](development/develop_plan/backend/06_policy_search.md):
  Gate G1 승인 PostgreSQL 기반 정책 검색 API·파서 및 W3-B0 계약
- [v0.5.0 Backend Stabilization Forest 계획](development/develop_plan/backend/07_v0_5_0_backend_stabilization.md):
  5주차 Release 2 (v0.5.0) 백엔드 전체 회귀 검증, Data 06 적재 연동 대조, QA/리뷰 결함 수정 및 인수 게이트 계획
- [Policy Data Database Integration Forest 계획](development/develop_plan/integration/02_policy_data_database_integration.md):
  Backend의 검증된 저장 경계를 사용해 Data 파이프라인의 Seed·Runtime
  결과를 PostgreSQL과 Policy API까지 연결하는 데이터 담당 2주차 공동 계획
- [Policy Search Data Foundation Forest 계획](development/develop_plan/integration/03_policy_search_data_foundation.md):
  Source 중립 검색 필드, 행정구역 계층·적용 관계, search projection과
  Migration의 Release 1 공통 기반
- [Release 1 Acceptance Forest 계획](development/develop_plan/integration/04_release_1_acceptance.md):
  실제 snapshot DB → 검색 API → Frontend Browser 인수와 Release 1 판정
- [v0.5.0 Contract Baseline Forest 계획](development/develop_plan/integration/05_v0_5_0_contract_baseline.md):
  사용자 저장·관리자 인증·추천·수동 실행·품질 노출의 W4-G0 공동 계약
- [Recommendation Vertical Slice Forest 계획](development/develop_plan/integration/06_recommendation_vertical_slice.md):
  결정적 추천 API와 이유·미확정 조건 UI의 실제 세로 연결
  (Frontend UI Slice: [FE6-xx](development/develop_plan/frontend/06_recommendation_ui.md))
- [Release 2 Feature Acceptance Forest 계획](development/develop_plan/integration/07_release_2_feature_acceptance.md):
  4주차 midpoint와 5주차 리뷰·QA·Release 2 Gate
- [Recurrent Collection and Quality Operations Forest 계획](development/develop_plan/data/03_recurrent_collection_quality_operations.md):
  반복 수집의 수정·중복·실패 격리와 안전한 품질 통계
- [Public HTTPS Policy Ingestion Forest 계획](development/develop_plan/data/04_public_https_policy_ingestion.md):
  승인 공식 웹 Source 한 곳의 목록·상세·자격요건 근거 수집과 PostgreSQL 적재
- [Regional Youth Policy Ingestion Forest 계획](development/develop_plan/data/05_regional_youth_policy_ingestion.md):
  `v0.5.0` 지역 공식 포털 탐색, 지역 고유 정책 판정과 온통청년·복지로 중복 제외
- [Supplemental Official Policy Ingestion Forest 계획](development/develop_plan/data/06_supplemental_official_policy_ingestion.md):
  온통청년·복지로 누락 가능 중앙·공공기관 Source의 중복 감사와 실제 적재
- [Eligibility Evidence and Summary Forest 계획](development/develop_plan/integration/08_eligibility_evidence_summary.md):
  정책 상세의 핵심 신청 조건·제외·서류·확인 필요와 Source evidence 세로 연결
  (Frontend UI Slice: [FE7-xx](development/develop_plan/frontend/07_eligibility_summary_ui.md))
- [Admin Data and Log Console Forest 계획](development/develop_plan/integration/09_admin_data_log_console.md):
  관리자 읽기 전용 정책 데이터 표와 구조화 파일 로그·조회·archive 삭제·감사
  (Frontend UI Slice: [FE8-xx](development/develop_plan/frontend/08_admin_observability_ui.md))
- [Review Admission Forest 계획](development/develop_plan/integration/10_review_admission_docker_acceptance.md):
  최신 DB·Runtime 기반 review admission, partial 적재와 Deploy 입력 확정
- [Review Admission Forest 개발 기록](development/development_notes/integration/review_admission_docker_acceptance.md):
  RA0 실제 기준선·변경 전 보호와 RA1~RA4 실행 근거
- [Docker Acceptance Environment 계획](development/develop_plan/deploy/01_docker_acceptance_environment.md):
  snapshot hash·Docker Compose·Volume·clean-room과 동일 환경 인계
- [Docker Acceptance Environment 개발 기록](development/development_notes/deploy/docker_acceptance_environment.md):
  DEP0~DEP5 실제 구현·검증과 `DOCKER_ACCEPTANCE_PASS` 근거
- [Docker Acceptance 웹 UI 실행 방법](development/docker_acceptance_setup.md):
  Docker Desktop 최초 복원·Compose 실행·웹 UI 접속·재시작·종료 방법과 현재 검증 상태
- [Docker Acceptance 동일 환경 인계 패키지](development/handoff/docker_acceptance/README.md):
  AES-256 snapshot 전달, receipt 대조와 BE·FE·사용성 리뷰어·QA 독립 결과 계약
- [ADR 0001 정책 검색 데이터 기반](architecture/decisions/0001-policy-search-data-foundation.md):
  장기 지역 Source 확장을 위한 데이터·DB 구조 제안과 검증 기준
- [Forest 개발 기록](development/development_notes/README.md): Forest별
  실제 구현과 검증 결과
- [프론트엔드 개발 히스토리 (1~5주차)](development/frontend_development_history_w1_w5.md):
  1~5주차 Frontend UI/기능·UX·구현 설계 종합 (백엔드·데이터 제외)
- [Docs System Forest 개발 기록](development/development_notes/integration/docs_system.md)
- [Data Pipeline Forest 개발 기록](development/development_notes/data/data_pipeline.md)
- [Release Dataset Bootstrap Forest 개발 기록](development/development_notes/data/release_dataset_bootstrap.md):
  DT0 실행 환경과 실데이터 수집·적재 검증 결과
- [Recurrent Collection and Quality Operations Forest 개발 기록](development/development_notes/data/recurrent_collection_quality_operations.md):
  DTL4-2A~2B 반복·수정·중복·실패 판정, CollectionRun 영속과 PostgreSQL 검증
- [Public HTTPS Policy Ingestion Forest 개발 기록](development/development_notes/data/public_https_policy_ingestion.md):
  DTL4-3A 승인 공식 웹 Source의 제한 호출·HTML 추출과 actual 검증
- [Regional Youth Policy Ingestion Forest 개발 기록](development/development_notes/data/regional_youth_policy_ingestion.md):
  RYP0 inventory부터 RYP2 경북 Adapter, RYP3 지역·신청 상태와 RYP4 교차 Source
  제외 Gate 검증 결과
- [Supplemental Official Policy Ingestion Forest 개발 기록](development/development_notes/data/supplemental_official_policy_ingestion.md):
  SOP0 후보 정제·SOP1 실제 DB 중복 감사·SOP2 공식 Source allowlist 판정
- [Eligibility Evidence and Summary Forest 개발 기록](development/development_notes/integration/eligibility_evidence_summary.md):
  DTL4-4 조건·서류·시설 연락처 계약부터 실제 PostgreSQL·API·Browser 인수까지
- [Policy Discovery Forest 개발 기록](development/development_notes/frontend/policy_discovery.md)
- [Policy Search Forest 개발 기록](development/development_notes/frontend/policy_search.md):
  Gate G1 search contract TypeScript types promote (FE4-11)
- [Recommendation UI Forest 개발 기록](development/development_notes/frontend/recommendation_ui.md):
  FE6-00~04 DTO·조건 form·결과·error·region collapse·FE6-05 Playwright E2E
- [User Service Features Forest 개발 기록](development/development_notes/frontend/user_service_features.md):
  FE5-00~06,08 localStorage·즐겨찾기·조건·D-Day·cross-route identity·FE5-07 Playwright E2E
- [CollectionRun Admin UI Forest 개발 기록](development/development_notes/frontend/collection_run_admin_ui.md):
  FE3-00~06 PIN session·실행 기록·수동 실행·ApiErrorToast·Playwright E2E
- [Eligibility Summary UI Forest 개발 기록](development/development_notes/frontend/eligibility_summary_ui.md):
  Integration 08 승인 DTO·핵심 신청 조건·evidence 원문·a11y·Playwright E2E와 DTL4-6 회귀 정리
- [Admin Observability UI Forest 개발 기록](development/development_notes/frontend/admin_observability_ui.md):
  FE8-00~06 admin policy·log DTO·표·drawer·maintenance·Toast·a11y·Playwright E2E
- [Integration Fix and Regression Forest 개발 기록](development/development_notes/frontend/integration_and_regression.md):
  FE9-01 W4-F9 Frontend-only 통합 수정·blocker triage; FE9-02 W4-F10 Mock-first 회귀
- [Frontend Real API 수동 테스트 가이드](development/frontend_real_api_manual_testing_guide.md):
  `VITE_USE_MOCK=false` + localhost:8000 Browser 수동 검증 절차 (Real API E2E skip 대응)
- [React Router Advisory Review Forest 개발 기록](development/development_notes/frontend/react_router_advisory.md):
  advisory 재현과 현재 client-only 앱의 RSC 도달 가능성
- [Backend Baseline Forest 개발 기록](development/development_notes/backend/policy_baseline.md)
- [Backend Policy Persistence Hardening Forest 개발 기록](development/development_notes/backend/policy_persistence_hardening.md)
- [Backend Policy Runtime Safety Forest 개발 기록](development/development_notes/backend/policy_runtime_safety.md):
  Policy timestamp·SQL logging 현재 동작, 결정과 검증 결과
- [Backend Policy Search Forest 개발 기록](development/development_notes/backend/policy_search.md):
  PostgreSQL 기반 정책 검색 API·파서 및 DTO 구현 결과
- [Backend Admin Access Control Forest 개발 기록](development/development_notes/backend/admin_access_control.md):
  관리자 4자리 PIN 세션 인증, fail-closed 및 401/403/429/422 상태코드 검증 결과
- [Backend CollectionRun Admin API Forest 개발 기록](development/development_notes/backend/collection_run_admin_api.md):
  CollectionRun 실행 이력 목록·상세, 수동 실행 202 및 Stale 판정 계약 결과
- [v0.5.0 Backend Stabilization Forest 개발 기록](development/development_notes/backend/v0_5_0_backend_stabilization.md):
  5주차 Release 2 (v0.5.0) 백엔드 회귀 검증, Data 06 연동 대조 및 QA 결함 수정 개발 기록
- [Recommendation Vertical Slice Forest 개발 기록](development/development_notes/integration/recommendation_vertical_slice.md):
  사용자 조건 기반 결정적 맞춤 추천 API, 부합도 점수, 사유 Code 및 비단정 계약 결과
- [Eligibility Evidence and Summary Forest 개발 기록](development/development_notes/integration/eligibility_evidence_summary.md):
  정책 상세 자격요건 구조화 응답 DTO 및 Evidence 출처 보증 검증 결과
- [Admin Data and Log Console Forest 개발 기록](development/development_notes/integration/admin_data_log_console.md):
  관리자 읽기 전용 정책 데이터 표 목록·상세 API 및 페이징/Allowlist 검증 결과
- [Policy Data Database Integration Forest 개발 기록](development/development_notes/integration/policy_data_database_integration.md):
  Backend 저장·조회 증거를 바탕으로 한 데이터 계약 승인과 Frontend 인계 결과
- [Policy Search Data Foundation Forest 개발 기록](development/development_notes/integration/policy_search_data_foundation.md):
  검색 데이터 lineage·ADR Gate와 Schema·지역·DB·Source Adapter 검증 결과
- [Release 1 Acceptance Forest 개발 기록](development/development_notes/integration/release_1_acceptance.md):
  DT5 실제 snapshot 복구·PostgreSQL·HTTP·Browser 통합과 결함 수정 결과
- [v0.5.0 Contract Baseline Forest 개발 기록](development/development_notes/integration/v0_5_0_contract_baseline.md):
  DTL4-0 시작 SHA·환경·Forest 소유 경계와 W4-G0 진행 근거
- [Release 2 Feature Acceptance 개발 기록](development/development_notes/integration/release_2_feature_acceptance.md):
  DTL5-0 W5-G0 기준선, Data 06 포함 actual E2E·독립 검증과 Release 2 판정 근거
- [Policy API 계약](api/policies.md): 정책 목록·상세·자연어 검색, pagination,
  category·region·status 필터, 복수 프로필 선호도·정렬과 partial 노출 규칙
- [관리자 인증 API 계약](api/admin_access.md): 관리자 PIN 로그인·변경, 세션 무효화와 상태코드 계약
- [CollectionRun 관리자 API 계약](api/admin_collection_runs.md): CollectionRun 실행 이력 목록·상세, 수동 실행 및 stale 판정 계약
- [관리자 정책 데이터 표 API 계약](api/admin_policies.md): 관리자 읽기 전용 정책 데이터 표 목록·상세, 페이징 및 Allowlist 정렬 계약
- [관리자 로그 및 감사 API 계약](api/admin_logs.md): 관리자 서버 로그 파일/이벤트 조회, 회전 archive 삭제 및 Audit 감사 기록 계약
- [맞춤 정책 추천 API 계약](api/recommendation.md): 복수 관심 분야·지역·연령 기반 결정적 추천, 부합도 점수, 추천 사유 및 비단정 계약
- [문서 품질 검증](development/documentation_validation.md): 로컬 검증 명령,
  검사 범위와 CI 연동 기준
- [Backend Windows 로컬 환경](development/backend_local_setup.md):
  Windows `.venv`, PostgreSQL 테스트 DB와 Backend 전체 테스트 절차
- [Collector 실행](operations/collector.md): 온통청년·복지로 제한 수집,
  환경변수, Runtime Raw 경계와 저장 Raw의 PostgreSQL 재처리
- [실측 기반 문제 해결·개선율 보고서](troubleshooting/integration/measured_improvement_report.md):
  응답시간 90.7% 감소, 식별 오류 100% 제거와 지역정책 판정 개선을 실제 전후
  수치로 종합한 보고서
- [Windows PostgreSQL 테스트 환경 복구](troubleshooting/backend/windows_postgresql_test_environment.md):
  다른 PC 환경에서 발생한 가상환경·DB 역할 인증·테스트 DB 문제의 해결 기록
- [Docker 수동 수집·재시작 복구](troubleshooting/backend/docker_manual_collection_restart_recovery.md):
  관리자 수동 실행의 `running` 고착과 가변 DB 재시작 차단을 실제 Docker에서
  재현하고 terminal 상태·데이터 보존으로 수정한 기록
- [추천 전체 정책 판정의 N+1과 오추천 해결](troubleshooting/backend/recommendation_full_inventory_performance.md):
  추천 정확성 보완 중 드러난 N+1을 제거해 실제 3,273건 응답을 약 14.8초에서
  약 1.4초로 개선한 문제 해결 기록
- [연령 `0세~0세` placeholder 오판 보정](troubleshooting/data/release_age_placeholder_normalization.md):
  실제 631건의 근거 없는 연령 bound를 미확정으로 복구하고 멱등 재적재한 기록
- [지역 Browser 수집 실패·drift 안전 복구](troubleshooting/data/regional_browser_capture_recovery.md):
  page-context·timeout·identity drift를 제한 복구하고 미해결 실패를 격리한 기록
- [Review admission 현재성·지역 projection 오적재 복구](troubleshooting/data/review_admission_currentness_recovery.md):
  잘못된 5건 승격을 rollback하고 현재성·region rule·manifest baseline을 보정한 기록
- [Windows actual Runtime·DB 연결 환경 복구](troubleshooting/integration/windows_actual_runtime_acceptance.md):
  DB 권한·Migration·Node·Runtime log를 정렬해 실제 종단 실행을 복구한 기록
- [변경 이력](../CHANGELOG.md): 사용자와 팀에 의미 있는 변경 사항
- [Release 1 검증 증거 안내](contest/release_1_evidence_guide.md):
  DT7E actual snapshot·contract hash 기반 경량 QA·사용성 검증 절차
- [Release 1 기술 증거](contest/release_1_technical_evidence.json):
  실제 PostgreSQL golden·control acceptance의 안전한 실행 결과
- [Release 1 경량 리뷰 근거](contest/release_1_review_summary.md):
  제공된 Word 리뷰의 QA·사용성 관찰과 Release 2 후속사항
- [Release 1 수동 증거](contest/release_1_evidence.json):
  G4 경량 QA·사용성 판정의 contract 고정 JSON
- [Release 1 Gate 결정](contest/release_1_gate_decision.json):
  Team Leader G4 `pass`, 비차단 후속과 릴리스 publication 상태

아직 생성하지 않은 문서는 색인에 미리 등록하지 않는다. 문서를 추가하거나
이동할 때 이 목록과 관련 문서의 링크를 함께 갱신한다.

## 공동 확인 및 인계 보드

기존 Normalized 1.0.0의 Data·Backend·Frontend 소비 검토는 2주차
Integration 02에서 완료됐다. PSF1은 1.1.0 검색 데이터 계약과 전환 경계를
추가했으며 검토 증거와 현재 규칙은
[Fixture와 Seed 계약](data/fixture_seed_contract.md),
[Policy DB 매핑](architecture/policy_database_mapping.md)과
[Policy API 계약](api/policies.md)을 따른다.

앞으로 Schema, Fixture, Seed, 필수·선택 여부, `null`, 빈 배열 또는 enum을
변경하면 Data 담당이 단독으로 확정하지 않고 Backend·Frontend 영향과 소비
테스트를 같은 Forest에서 다시 확인한다.

2주차 완료 시점에는 활성 인계사항이 없었다. 3주차 Data 02 DT1 실데이터
preflight에서 확인한 `R1-SEARCH-DATA-SEMANTICS`는 DT2A~DT2D 공동 검토와
Gate G1 승인으로 `2026-08-04`에 종료했다. Release 1 구현과 근거는
`2026-08-06` 커밋 `4629a61`로 `develop`에 병합됐으며 현재 활성 영역 간
인계사항은 없다.

`R1-RELEASE-EVIDENCE`는 `2026-08-06` 경량 QA·사용성 리뷰와 새 contract hash
기술 재검증을 통과해 종료했다. 보고서와 API 오류 UX는 Release 1을 완료한
것처럼 기록하지 않고 `v0.5.0` 계획에서 다시 다룬다.

Release 1은 PR #15의 `main` 커밋 `2b33ed7`과 `v0.1.0` tag로 발행됐고,
`develop`도 같은 커밋으로 fast-forward됐다. publication은 완료됐으며 현재
활성 영역 간 인계사항은 없다.

기존 `R1-ACTUAL-DATA-BOUNDARIES`는 신청 가능한 단기숙소 정책을 현 Source에서
confirmed 1건으로 승인해 종료했다. DT6 월세 결과는 역사적 unknown 회귀
근거로 보존하며 현재 Source 추가 차단사항으로 사용하지 않는다.
`R1-SEARCH-RELEVANCE`도 DT7B에서 자연어·control 모두 1건 중 1위와 응답시간
예산을 통과해 종료했다.
`R1-POLICY-PERIOD-EXTRACTION`은 DT7C에서 Source mapping을 재감사해 종료했다.
복지로 계약에는 신청기간 전용 필드가 없으므로 본문 날짜 2건은 원문만 보존하고
기간·상태를 null로 유지한다. Source 근거 없는 승격과 상태 불일치는 0건이며
golden 정책은 온통청년의 명시적 `상시` 근거로 안전성 감사를 통과했다.

4주차 DTL4-1에서 다음 실제 소비 검토·계약 차이를 확인했다. 상세 근거와
검토안은 [v0.5.0 Contract Baseline 개발 기록](development/development_notes/integration/v0_5_0_contract_baseline.md)과
[계획](development/develop_plan/integration/05_v0_5_0_contract_baseline.md)에 둔다.

| ID | 상태 | 다음 담당 | 완료·재개 조건 |
| --- | --- | --- | --- |
| `W4-G1-BE-AUTH` | completed (`2026-08-14`) | Team Leader 검토 | local client+local/test 기본 `0000`, production 전용 token secret fail-closed 테스트 통과 |
| `W4-G1-FE-CONSUMER` | completed (`2026-08-14`) | Team Leader 검토 | 관리자·자격요건·추천·localStorage·날짜 TypeScript·Mock 소비 대조와 Frontend 162건 통과 |
| `W4-G2-PG-READINESS` | completed (`2026-08-14`) | DTL4-7 actual E2E | PostgreSQL 포함 Python 487건·95 subtests, Migration 단일 head와 격리 test DB 확인 |
| `W4-G2-FE-READINESS` | completed (`2026-08-14`) | DTL4-7 actual E2E | unit·lint·build 통과, Mock Browser 79건 통과·Real API 조건부 11건 실행 조건 명시 |
| `W4-G3-ACTUAL-E2E` | completed (`2026-08-14`) | DTL4-8 전체 회귀 | 실제 PostgreSQL·Runtime·FastAPI·React 관리자·웹 Source·사용자 E2E와 Release 1 검색·상세 회귀 통과 |
| `W4-G4-MIDPOINT` | completed (`2026-08-14`) | 5주차 승인 작업·독립 검증 | 전체 회귀·계약·문서·비추적 대조, Migration `20260810_0006`, 실제 DB 3,269건·지역정책 109건 검색 인수 통과; Release 2 최종 Gate는 아님 |
| `W5-G0` | completed (`2026-08-17`) | Data 06·영역별 안정화 | 5주차 시작 SHA·Migration·DB·Runtime·actual API mode와 검증 환경 고정 |
| `W5-G1` | completed (`2026-08-18`) | Deploy 01 | Backend·Frontend·Data 06 통합 PostgreSQL·API·Browser 전체 회귀 통과. `2026-08-19` review admission 뒤 `W5-G1_REVALIDATED` 완료 |

Team Leader는 천안청년센터 공지 674번의 최소 수집·비재배포 경계를 포함해
`W4-G0_APPROVED`로 판정했다. 위 후속 항목은 W4-G1 구현 적합성
확인이며 Data 03·04의 기반 구현과 완료된 Integration 08을 막지 않는다.
DTL4-5는 위 두 항목과 관리자 Policy·로그 DTO, Eligibility 중복 proposal,
Data 05 재사용·중복 경계를 함께 대조해 `W4-G1_APPROVED`로 판정했다. 상세 근거는
[v0.5.0 Contract Baseline 개발 기록](development/development_notes/integration/v0_5_0_contract_baseline.md)에 둔다.
DTL4-6은 실제 PostgreSQL과 전 영역 자체 검증을 통과하고 Eligibility 과거 proposal
잔재를 정리해 `W4-G2_APPROVED`로 판정했다. DTL4-7은 실제 PostgreSQL·Runtime·
FastAPI·React에서 관리자·웹 Source·사용자 세 Critical Path와 Release 1 검색·
상세 회귀를 통과해 `W4-G3_APPROVED`로 판정했다. 이어 DTL4-8 전 영역 회귀·
문서 대조와 비추적 감사를 완료해
`W4-G4_MIDPOINT_PASS`로 판정했다. 5주차에는 Data 06·승인 추가 기능·결함 수정·
UI/UX 최적화와 독립 QA·사용성 리뷰·보고서 대조를 수행한다.
`W4-ES2-BE-CONSUMER`는 NormalizedProgram 1.2.0, Migration `20260810_0006`,
상세 DTO와 PostgreSQL actual 대조를 통과해 `2026-08-10` 완료 처리했다.
`W4-ES3-FE-CONSUMER`는 상세 TypeScript·Mock·UI와 승인 문구, 시설 전화 링크,
키보드·모바일 Browser 검증을 통과해 같은 날 완료 처리했다. 현재 상세에는 개인
조건 비교 기능이 없어 `조건상 일치`·`조건상 불일치`를 임의 표시하지 않는다.
`W4-ES4-ACTUAL`은 승인 천안 fixture의 실제 PostgreSQL → 상세 API → Browser
대조와 Release 1 snapshot 3,156건의 HTTP·Browser golden 회귀를 통과했다.

미래 계획 자체나 아직 발생하지 않은 위험은 인계사항으로 등록하지 않는다.

### 인계사항 발생 시 기록 방법

각 담당자 또는 담당 AI Agent는 다음 Forest 작업 중 다른 영역의 확인이
필요한 계약, 소비 테스트, 차단 의존성이나 후속 조치를 실제로 발견하면 이
절에 표를 추가한다.

- `ID`, 현재 상태, 다음 담당, 완료 또는 재개 조건과 권위 문서 링크를
  반드시 기록한다.
- `review-pending`은 소비자 검토 증거 대기,
  `action-needed`는 담당 영역의 조치 필요,
  `trigger-based`는 명시된 조건이 생길 때만 재개하는 항목에 사용한다.
- 상세 구현 계획과 결과는 담당 Forest 계획·개발 기록·Issue에 남기고 이
  표에는 요약과 링크만 둔다.
- 확인이나 구현 증거 없이 다른 영역의 승인을 대신 기록하지 않는다.
- 완료한 항목은 관련 기준 문서와 개발 기록을 먼저 갱신한 뒤 현재 보드에서
  제거하거나 후속 항목으로 교체한다.

## 문서 영역

| 영역 | 책임 |
| --- | --- |
| [architecture](architecture/README.md) | 공통 시스템 구조, 경계, 흐름과 영역 간 아키텍처 결정 |
| [api](api/README.md) | 외부에 제공하는 API 계약, 오류와 사용 예시 |
| [data](data/README.md) | 데이터 출처, Schema, 정규화와 수집 정책 |
| [governance](governance/README.md) | 브랜치, 커밋, 리뷰, 기여와 문서화 규칙 |
| [development](development/README.md) | 개발 환경, Forest 계획과 실제 개발 기록 |
| [troubleshooting](troubleshooting/README.md) | 실제 발생하고 원인이 확인된 문제의 해결 기록 |
| [operations](operations/README.md) | Collector, Scheduler, 백업과 운영 절차 |
| [contest](contest/README.md) | 대회 보고서, 시연, 제출과 SBOM 자료 |

각 영역의 `README.md`는 해당 영역의 책임과 문서 추가 기준을 설명한다. 세부
문서는 실제로 작성할 내용이 있을 때만 생성한다.

## 변경 유형별 문서 갱신

| 변경 유형 | 필수 확인 문서 | 조건부 확인 문서 |
| --- | --- | --- |
| 완료된 주요 기능 | `CHANGELOG.md`, 개발 기록 | 관련 API, 데이터, 아키텍처, 운영 문서 |
| 영향이 큰 버그 수정 | `CHANGELOG.md` | 실제 해결된 경우 관련 troubleshooting 문서 |
| 데이터 스키마 변경 | `CHANGELOG.md`, 개발 기록, 데이터 문서 | JSON Schema, API 예시, DB 문서 |
| API 계약 변경 | `CHANGELOG.md`, API 문서 | 개발 기록, 프론트엔드 연동 문서 |
| DB 구조 변경 | `CHANGELOG.md`, 개발 기록, DB 문서 | 마이그레이션 및 운영 문서 |
| 환경변수·실행 방법 변경 | `.env.example`, 설정 문서 | 루트 `README.md`, 운영 문서 |
| 라이브러리·의존성 변경 | 담당 앱 manifest와 lockfile, 개발 기록 | 실행 방법, 통합·배포 영향 |
| 배포 구조 변경 | `CHANGELOG.md`, 아키텍처 문서 | 설정 및 운영 문서 |
| 계획 수립·변경 | 관련 `docs/development/develop_plan/` 문서 | 결정이 확정된 경우 관련 기준 문서 |
| 오탈자·서식 수정 | 해당 문서 | 일반적으로 변경 이력과 개발 기록은 불필요 |

문서가 아직 존재하지 않는 영역의 작업은 해당 문서를 같은 작업에서 만들거나,
개발 계획에 후속 작업과 완료 기준을 기록한다.

## 문서 라우팅

먼저 문서의 역할을 정하고, 계획·개발 기록·문제 해결 문서인 경우에만 담당
영역을 선택한다.

| 변경 내용 | 기록 위치 |
| --- | --- |
| Data Forest 계획 | `docs/development/develop_plan/data/` |
| Backend 즐겨찾기 계획 | `docs/development/develop_plan/backend/` |
| Frontend 캘린더 구현 결과 | `docs/development/development_notes/frontend/` |
| Seed → API → 화면 통합 | `docs/development/develop_plan/integration/` 및 대응하는 `development_notes/integration/` |
| Docker·Compose·동일 환경 인계 | `docs/development/develop_plan/deploy/` 및 대응하는 `development_notes/deploy/` |
| 현재 데이터 계약 | `docs/data/` |
| Frontend ↔ Backend API 계약 | `docs/api/` |
| 실제 해결한 Backend 장애 | `docs/troubleshooting/backend/` |

- 미래 범위와 완료 기준은 `develop_plan/`에 기록한다.
- 실제 구현과 검증 결과는 `development_notes/`에 기록한다.
- 현재 유효한 계약은 `data/`, `api/`, `architecture/`, `operations/` 등 관련
  기준 문서에 반영한다.
- 둘 이상의 애플리케이션 영역이 함께 책임지는 계획·결과·문제는
  `integration/`에 두고, 배포 구성·재현 환경·운영 인계가 독립 완료 기준이면
  `deploy/`에 둔다.
- 실제 문서가 없으면 담당 영역 디렉터리를 미리 만들지 않는다.

### AI Agent 최소 필독 문서

모든 AI Agent는 작업 전에 최소한 다음 문서를 확인한다.

1. `docs/index.md`
2. [문서화 정책](governance/documentation_policy.md)
3. [역할과 책임](governance/role_assignment.md)
4. 담당 영역의 Forest 계획

브랜치 생성·커밋·리뷰가 포함되면
[브랜치 전략](governance/branch_strategy.md),
[커밋 작성 규칙](governance/commit_convention.md),
[코드 리뷰 정책](governance/code_review.md)도 확인한다.

AI Agent에는 다음처럼 요청할 수 있다.

> `docs/index.md`와 `docs/governance/`의 관련 규칙을 읽고 작업하라. 작업 전
> 계획과 작업 후 구현 결과를 담당 영역의 문서에 기록하고, 변경된 공통 계약
> 문서와 문서 색인을 갱신하라. 의미 있는 완료 결과만 CHANGELOG에 요약하고
> 문서 검증을 실행하라.

세부 의무와 예외는
[문서화 정책](governance/documentation_policy.md)을 따른다.

## 문서 역할

- `docs/development/develop_plan/`은 Forest의 미래 작업 범위와 Slice 수행
  방법을 기록한다.
- `docs/development/development_notes/`는 Forest에서 실제로 구현하고 검증한
  결과를 상세 문서 하나로 기록한다.
- `CHANGELOG.md`는 완료된 Forest, 주요 기능·버그와 호환성 변경을 Forest당
  1~2개 항목으로 요약하고 상세 개발 기록을 연결한다.
- `docs/troubleshooting/`은 실제로 발생했고 원인과 해결 방법이 확인된 문제만
  기록한다.

계획, 구현 결과, 변경 이력, 문제 해결 기록을 서로 대신하여 사용하지 않는다.
내부 리팩터링, 동작을 바꾸지 않는 테스트 추가와 단순 문서 수정은 일반적으로
CHANGELOG에 기록하지 않는다.

## 작업 전 체크리스트

- 현재 브랜치와 작업 범위가 일치하는가?
- 관련 개발 계획과 문서화 정책을 확인했는가?
- 기존 변경사항과 충돌하거나 덮어쓸 파일이 없는가?
- 변경할 계약, API, Schema, DB 또는 환경변수를 식별했는가?
- 필요한 테스트와 완료 기준을 정했는가?

## 작업 후 체크리스트

- 실제 변경과 관련된 문서만 갱신했는가?
- 의미 있는 변경을 `CHANGELOG.md`의 `[Unreleased]`에 기록했는가?
- 완료한 기능 또는 주요 구조 변경을 개발 기록에 남겼는가?
- 계획 문서의 상태와 실제 결과가 일치하는가?
- 실행한 검증만 기록하고 실패 또는 미실행 항목을 숨기지 않았는가?
- 새 문서와 변경된 링크가 올바른가?
- 비밀키, 비밀번호, 개인정보 또는 비공개 원문이 포함되지 않았는가?
- 임시 파일과 빈 디렉터리를 제거했는가?

세부 규칙과 예외는
[문서화 정책](governance/documentation_policy.md)을 따른다.
