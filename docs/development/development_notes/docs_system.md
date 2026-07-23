# Docs System Forest 개발 기록

## 작업 정보

- 시작일: 2026-07-23
- 상태: completed
- 영역: documentation
- 관련 계획: [`01_docs_system.md`](../develop_plan/01_docs_system.md)
- 관련 Slice: D0~D6
- 브랜치:
  - `docs/governance/documentation-system`: D0~D1
  - `docs/governance/collaboration-policy`: D2~D6

## 목적

계획, 실제 구현 결과, 변경 이력과 문제 해결 기록의 역할을 분리하고,
GitHub에서 프로젝트 문서를 바로 탐색할 수 있는 기준과 검증 가능한 문서
시스템을 구축한다.

## Forest 범위

- 문서 역할과 갱신 규칙
- docs 디렉터리 구조와 진입점
- 협업·거버넌스 정책
- 시스템 아키텍처 기준선
- 데이터 문서 기준선
- Forest 기반 개발 계획과 개발 기록
- 문서 품질 자동 검증

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| D0 | completed | 문서 역할, 갱신 규칙과 체크리스트 확정 |
| D1 | completed | docs 기본 구조와 탐색 진입점 구축 |
| D2 | completed | 협업·거버넌스 정책 이관 |
| D3 | completed | 시스템 아키텍처 기준선 수립 |
| D4 | completed | 데이터 문서 기준선 수립 |
| D5 | completed | Forest 계획·기록 구조와 Docs Forest 문서 연결 |
| D6 | completed | 문서 검증기, 단위 테스트와 실행 가이드 구축 |

## 구현 내용

### D0 - 문서 시스템 규칙 확정

- 문서 탐색 진입점과 변경 유형별 갱신 안내를 추가했다.
- 문서별 책임, 작성 기준과 AI Agent 작업 규칙을 정의했다.
- `[Unreleased]` 기반 변경 이력을 추가했다.
- 계획, 개발 기록, 변경 이력과 troubleshooting의 역할을 분리했다.
- 작업 전후 체크리스트에 검증, 비밀정보와 임시 파일 확인을 포함했다.

### D1 - 문서 디렉터리 골격 및 진입점

- 루트 `README.md`에 프로젝트 설명과 문서 진입 링크를 추가했다.
- `docs/index.md`에 문서 영역과 책임을 정리했다.
- 각 영역에 최소 `README.md`를 추가했다.
- 예정된 세부 문서는 실제 내용이 생길 때 생성하도록 했다.
- 빈 디렉터리용 `.gitkeep` 대신 역할을 설명하는 문서를 사용했다.

### D2 - 협업 및 거버넌스 정책 이관

- `main`, `develop`과 작업 브랜치의 역할 및 병합 흐름을 정의했다.
- 작업 브랜치 이름을 `<type>/<domain>/<task>`로 통일했다.
- Conventional Commits의 type, scope와 description 규칙을 정리했다.
- PR 작성자·리뷰어 책임과 최소 병합 기준을 연결했다.
- 데이터, 백엔드, 프론트엔드와 팀장·공통 책임을 정의했다.
- 실제 저장소 상태와 계획이 다를 때 임의로 구조를 바꾸지 않는 원칙을
  추가했다.

### D3 - 시스템 아키텍처 기준선 수립

- `External Sources → Collector → RawPolicyDocument → Source Extractor →
  ExtractedPolicy → Normalizer → NormalizedProgram → Validator →
  Fixture/Seed 또는 PostgreSQL → FastAPI → React` 흐름을 문서화했다.
- Collector, Extractor, Normalizer와 Validator의 책임을 분리했다.
- JSON Schema를 팀 간 논리적 데이터 계약으로 정의했다.
- 운영 Raw와 개발용 최소 Fixture의 저장 정책을 구분했다.
- 초기 `frontend`, `backend`, `database` 3개 컨테이너와 향후 분리 조건을
  정리했다.
- 아키텍처 변경을 기록할 ADR 형식과 상태를 정의했다.

### D4 - 데이터 문서 기준선 수립

- 온통청년 API와 대표 HTTPS 웹 소스의 범위 및 등록 기준을 정리했다.
- `RawPolicyDocument`, `ExtractedPolicy`, `NormalizedProgram`의 역할과
  논리 필드를 정의했다.
- 선택 단일 값은 null, 복수 값은 빈 배열을 사용하는 기준을 확정했다.
- 날짜, 지역, 연령, 카테고리의 1주차 정규화 원칙을 정리했다.
- 출처 URL, 수집 시각, SHA-256 Hash와 원문 보존 기준을 정의했다.
- Fixture·Seed와 실제 runtime 데이터의 Git 포함 정책을 구분했다.
- 인증키, 개인정보와 데이터 라이선스 확인 기준을 정의했다.
- JSON Schema와 설명 문서의 동기화 규칙을 추가했다.

### D5 - Forest 기반 develop plan 구축

- 단일 누적 파일 방식과 Slice별 문서 분할 방식을 제거했다.
- `development_notes/`에 Forest별 개발 기록 하나를 두도록 변경했다.
- D0~D4 기록을 이 `docs_system.md`에 통합했다.
- `develop_plan/`을 `docs/development/` 아래로 이동했다.
- `01_docs_system.md`에 D0~D6의 목적, 진행 상태와 완료 기준을 작성했다.
- 첫 Data Forest 계획은 Data Forest를 시작할 때 작성하도록 범위를 분리했다.

### D6 - 문서 품질 검증 장치

- Python 표준 라이브러리만 사용하는 `scripts/validate_docs.py`를 추가했다.
- 필수 문서, Markdown 링크, 이전 저장소명과 비밀값 패턴을 검사한다.
- 빈 문서·디렉터리와 Forest 계획·개발 기록의 대응 및 상태를 검사한다.
- 완료된 Forest에 미완료 Slice가 남아 있으면 실패하도록 했다.
- 임시 디렉터리를 사용하는 단위 테스트를 추가했다.
- 로컬 실행, 검사 범위, 규칙 변경과 CI 연동 방법을 문서화했다.

## 주요 변경 파일

- `README.md`
- `CHANGELOG.md`
- `docs/index.md`
- `docs/governance/*.md`
- `docs/architecture/*.md`
- `docs/data/*.md`
- `docs/development/README.md`
- `docs/development/develop_plan/`
- `docs/development/development_notes/`
- `docs/development/documentation_validation.md`
- `scripts/validate_docs.py`
- `tests/test_validate_docs.py`

## 설계 결정

- 빈 문서와 빈 디렉터리를 미리 만들지 않는다.
- 미래 작업은 `docs/development/develop_plan/`, 실제 결과는
  `docs/development/development_notes/`에서 관리한다.
- 개발 계획과 개발 기록은 Forest당 각각 하나의 문서로 관리한다.
- Forest 내부 Slice는 문서 내부의 진행 표와 섹션으로 구분한다.
- 사용자와 팀에 의미 있는 변경만 `CHANGELOG.md`에 기록한다.
- troubleshooting 문서는 실제 발생하고 원인이 확인된 문제에 한해 작성한다.
- 현재 릴리스 흐름은 `develop → main`으로 유지한다.
- Collector는 독립 모듈로 유지하되 초기부터 별도 컨테이너로 분리하지 않는다.
- 실제 수집 Raw와 runtime 처리 결과는 Git에서 제외한다.
- `application_status` enum은 계획 예시가 충돌하므로 확정하지 않는다.

## 검증 결과

- Markdown 상대 링크와 대상 파일을 확인했다.
- 필수 문서 영역과 각 영역의 안내 문서가 존재하는지 확인했다.
- 프로젝트명이 `cheongnyeon-alimi`로 통일됐는지 확인했다.
- 빈 문서와 작업 중 생성한 임시 파일이 없는지 확인했다.
- D0~D4의 구현 내용과 결정이 이 Forest 기록에 통합됐는지 대조했다.
- 아키텍처와 데이터 기준선에서 확정·미확정 상태가 구분됐는지 확인했다.
- 문서 검증기 단위 테스트를 실행했다.
- 실제 저장소를 대상으로 문서 검증기를 실행했다.
- 테스트가 만든 임시 디렉터리가 자동으로 제거되는지 확인했다.

## 남은 작업

- `application_status`의 의미와 enum을 Data Schema 구현 전에 공동 검토한다.
- 온통청년 API의 공식 endpoint, 호출 제한과 이용 조건을 Collector 구현 전에
  확인한다.
- 첫 Data Forest를 시작할 때 대응하는 계획과 개발 기록 문서를 생성한다.
- 문서 검증 CI Workflow는 배포·CI 설정 작업에서 추가한다.
