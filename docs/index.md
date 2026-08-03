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
  NormalizedProgram 1.1.0의 36개 논리 필드, 행정구역·검색 projection
  PostgreSQL·Importer·공개 API 경계
- [CollectionRun 데이터베이스 계약](architecture/collection_run_database.md):
  Seed·Runtime 실행 이력의 PostgreSQL 필드, 상태 전이와 보안 경계
- [아키텍처 결정 기록](architecture/decisions/README.md): ADR 작성 및 변경
  관리 규칙
- [데이터 소스](data/data_sources.md): 데이터 소스 등록 기준과 현재 확인 상태
- [API Source Profile](data/source_profiles.md): 온통청년·복지로 요청 계약,
  실제 응답 구조·검색 필드 mapping과 호출 제약
- [데이터 Schema 기준선](data/data_schema.md): Raw, Extracted와 Normalized
  데이터 계약과 Source Adapter 원칙
- [RawPolicyDocument JSON Schema](../data/schema/raw_policy_document.schema.json):
  원본 byte와 수집 메타데이터의 실행 가능한 Raw 계약
- [NormalizedProgram JSON Schema](../data/schema/normalized_program.schema.json):
  정규화 필드, provenance와 품질 분류의 실행 가능한 계약
- [정규화 규칙](data/normalization_rules.md): 날짜, 검색 배열, 지역, 연령과
  카테고리 변환 기준
- [수집 정책](data/collection_policy.md): HTTP, Raw 보존, 보안과 라이선스
  원칙
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
  실데이터 정책 검색과 `v0.1.0` 실행 순서
- [3주차 Data·Team Leader 실행 계획](development/weekly_plan/week_03_data_team_leader.md):
  실데이터 수집·적재와 통합·릴리스 판정 Slice
- [3주차 검색 계약 Gate G1 인수인계](development/weekly_plan/week_03_search_contract_handoff.md):
  Backend 06·Frontend 04 공통 시작 커밋, 고정 계약, 역할별 초안과 공동 승인 기준
- [Docs System Forest 계획](development/develop_plan/integration/01_docs_system.md)
- [Data Pipeline Forest 계획](development/develop_plan/data/01_data_pipeline.md)
- [Release Dataset Bootstrap Forest 계획](development/develop_plan/data/02_release_dataset_bootstrap.md):
  Release 1 실제 정책 수집·PostgreSQL 적재와 품질 기준선
- [Policy Discovery Forest 계획](development/develop_plan/frontend/01_policy_discovery.md)
- [React Router Advisory Review Forest 계획](development/develop_plan/frontend/02_react_router_advisory.md):
  현재 client-only Frontend의 RSC advisory 영향과 호환 대응 검토
- [CollectionRun Admin UI Forest 계획](development/develop_plan/frontend/03_collection_run_admin_ui.md):
  관리자 실행 이력·수동 실행의 Frontend 소비 계획
- [Policy Search Forest 계획](development/develop_plan/frontend/04_policy_search.md):
  `GET /api/v1/policies/search` flat query 소비, Filter Chip·Reason UI (Gate G1 통합안 draft)
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
- [Policy Data Database Integration Forest 계획](development/develop_plan/integration/02_policy_data_database_integration.md):
  Backend의 검증된 저장 경계를 사용해 Data 파이프라인의 Seed·Runtime
  결과를 PostgreSQL과 Policy API까지 연결하는 데이터 담당 2주차 공동 계획
- [Policy Search Data Foundation Forest 계획](development/develop_plan/integration/03_policy_search_data_foundation.md):
  Source 중립 검색 필드, 행정구역 계층·적용 관계, search projection과
  Migration의 Release 1 공통 기반
- [ADR 0001 정책 검색 데이터 기반](architecture/decisions/0001-policy-search-data-foundation.md):
  장기 지역 Source 확장을 위한 데이터·DB 구조 제안과 검증 기준
- [Forest 개발 기록](development/development_notes/README.md): Forest별
  실제 구현과 검증 결과
- [Docs System Forest 개발 기록](development/development_notes/integration/docs_system.md)
- [Data Pipeline Forest 개발 기록](development/development_notes/data/data_pipeline.md)
- [Release Dataset Bootstrap Forest 개발 기록](development/development_notes/data/release_dataset_bootstrap.md):
  DT0 실행 환경과 실데이터 수집·적재 검증 결과
- [Policy Discovery Forest 개발 기록](development/development_notes/frontend/policy_discovery.md)
- [React Router Advisory Review Forest 개발 기록](development/development_notes/frontend/react_router_advisory.md):
  advisory 재현과 현재 client-only 앱의 RSC 도달 가능성
- [Backend Baseline Forest 개발 기록](development/development_notes/backend/policy_baseline.md)
- [Backend Policy Persistence Hardening Forest 개발 기록](development/development_notes/backend/policy_persistence_hardening.md)
- [Backend Policy Runtime Safety Forest 개발 기록](development/development_notes/backend/policy_runtime_safety.md):
  Policy timestamp·SQL logging 현재 동작, 결정과 검증 결과
- [Policy Data Database Integration Forest 개발 기록](development/development_notes/integration/policy_data_database_integration.md):
  Backend 저장·조회 증거를 바탕으로 한 데이터 계약 승인과 Frontend 인계 결과
- [Policy Search Data Foundation Forest 개발 기록](development/development_notes/integration/policy_search_data_foundation.md):
  검색 데이터 lineage·ADR Gate와 Schema·지역·DB·Source Adapter 검증 결과
- [Policy API 계약](api/policies.md): 정책 목록·상세, pagination,
  category·region·status 필터와 partial 노출 규칙
- [문서 품질 검증](development/documentation_validation.md): 로컬 검증 명령,
  검사 범위와 CI 연동 기준
- [Backend Windows 로컬 환경](development/backend_local_setup.md):
  Windows `.venv`, PostgreSQL 테스트 DB와 Backend 전체 테스트 절차
- [Collector 실행](operations/collector.md): 온통청년·복지로 제한 수집,
  환경변수, Runtime Raw 경계와 저장 Raw의 PostgreSQL 재처리
- [Windows PostgreSQL 테스트 환경 복구](troubleshooting/backend/windows_postgresql_test_environment.md):
  다른 PC 환경에서 발생한 가상환경·DB 역할 인증·테스트 DB 문제의 해결 기록
- [변경 이력](../CHANGELOG.md): 사용자와 팀에 의미 있는 변경 사항

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
preflight에서 다음 공동 검토 항목이 실제로 확인됐다.

| ID | 상태 | 다음 담당 | 완료 또는 재개 조건 | 권위 문서 |
| --- | --- | --- | --- | --- |
| `R1-SEARCH-DATA-SEMANTICS` | action-needed | Backend·Frontend·Data | Integration 03 병합과 DT2 actual profile·Data 권고안·Schema 영향 판정 완료. Backend 06·Frontend 04 초안으로 unknown·partial·상태·정렬·검색 이유 소비 의미를 검토하고 Gate G1 승인 | [Gate G1 인수인계](development/weekly_plan/week_03_search_contract_handoff.md), [검색 데이터 기반 개발 기록](development/development_notes/integration/policy_search_data_foundation.md), [Data 02 개발 기록](development/development_notes/data/release_dataset_bootstrap.md) |

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
| 현재 데이터 계약 | `docs/data/` |
| Frontend ↔ Backend API 계약 | `docs/api/` |
| 실제 해결한 Backend 장애 | `docs/troubleshooting/backend/` |

- 미래 범위와 완료 기준은 `develop_plan/`에 기록한다.
- 실제 구현과 검증 결과는 `development_notes/`에 기록한다.
- 현재 유효한 계약은 `data/`, `api/`, `architecture/`, `operations/` 등 관련
  기준 문서에 반영한다.
- 둘 이상의 영역이 함께 책임지는 계획·결과·문제는 `integration/`에 둔다.
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
