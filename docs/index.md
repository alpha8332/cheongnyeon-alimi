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
- [역할과 책임](governance/role_assignment.md): 영역별 책임과 공동 통합 지점
- [시스템 아키텍처 개요](architecture/overview.md): 목표 구조와 계층별 책임
- [시스템 흐름](architecture/system_flow.md): 외부 소스부터 Web UI까지의
  데이터 흐름
- [컨테이너 구조](architecture/container_structure.md): 초기 실행 단위와
  향후 분리 기준
- [아키텍처 결정 기록](architecture/decisions/README.md): ADR 작성 및 변경
  관리 규칙
- [데이터 소스](data/data_sources.md): 데이터 소스 등록 기준과 현재 확인 상태
- [데이터 Schema 기준선](data/data_schema.md): Raw, Extracted와 Normalized
  데이터 계약 원칙
- [정규화 규칙](data/normalization_rules.md): 날짜, 지역, 연령과 카테고리
  변환 기준
- [수집 정책](data/collection_policy.md): HTTP, Raw 보존, 보안과 라이선스
  원칙
- [Forest 개발 계획](development/develop_plan/README.md): Forest별 범위,
  Slice와 완료 기준
- [Docs System Forest 계획](development/develop_plan/integration/01_docs_system.md)
- [Data Pipeline Forest 계획](development/develop_plan/data/01_data_pipeline.md)
- [Forest 개발 기록](development/development_notes/README.md): Forest별
  실제 구현과 검증 결과
- [Docs System Forest 개발 기록](development/development_notes/integration/docs_system.md)
- [문서 품질 검증](development/documentation_validation.md): 로컬 검증 명령,
  검사 범위와 CI 연동 기준
- [변경 이력](../CHANGELOG.md): 사용자와 팀에 의미 있는 변경 사항

아직 생성하지 않은 문서는 색인에 미리 등록하지 않는다. 문서를 추가하거나
이동할 때 이 목록과 관련 문서의 링크를 함께 갱신한다.

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
