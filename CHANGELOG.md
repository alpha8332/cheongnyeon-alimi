# 변경 이력

이 파일은 `cheongnyeon-alimi`의 사용자와 팀에 의미 있는 변경 사항을
기록한다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
프로젝트는 [Semantic Versioning](https://semver.org/lang/ko/)을 사용한다.

## [Unreleased]

### Fixed

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

- `NormalizedProgram` 1.1.0 검색 데이터 계약, 1.0.0 compatibility adapter,
  공식 법정동 기반 versioned 지역·계층·별칭 Seed, 지역 적용 관계 경계
  Fixture와 PSF3 전 검색 필드 손실 방지 경계 추가
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
