# 개발 기록

이 문서는 완료한 기능과 주요 구조 변경의 실제 구현 및 검증 결과를 기록한다.
예정된 작업은 `docs/develop_plan/`에서 관리한다.

## 2026-07-23 - 문서 시스템 규칙 확정

### 작업 정보

- 영역: documentation
- 브랜치: `docs/governance/documentation-system`
- 관련 계획: Slice D0 - 문서 시스템의 규칙 확정

### 목적

개발을 시작하기 전에 계획, 실제 구현 결과, 변경 이력과 문제 해결 기록의
역할을 분리하고, 코드 변경 후 어떤 문서를 갱신해야 하는지 판단할 기준을
마련한다.

### 구현 내용

- 문서 탐색 진입점과 변경 유형별 갱신 안내를 추가했다.
- 문서별 책임, 작성 기준과 AI Agent 작업 규칙을 정의했다.
- `[Unreleased]` 기반 변경 이력을 추가했다.
- 개발 완료 기록과 미래 개발 계획의 관리 위치를 분리했다.
- 작업 전후 점검 항목에 검증, 비밀정보, 임시 파일과 빈 디렉터리 확인을
  포함했다.

### 주요 변경 파일

- `docs/index.md`
- `docs/governance/documentation_policy.md`
- `CHANGELOG.md`
- `docs/development/development_notes.md`
- `docs/develop_plan/README.md`

### 설계 결정

- 문서가 생성되기 전에 전체 디렉터리와 빈 파일을 만들지 않는다.
- 미래 작업은 `develop_plan/`, 완료 결과는 이 문서에서 관리한다.
- 사용자와 팀에 의미 있는 변경만 `CHANGELOG.md`에 기록한다.
- troubleshooting 문서는 실제 발생하고 원인이 확인된 문제에 한해 작성한다.

### 검증

- Markdown 파일 간 상대 링크와 대상 파일의 존재 여부를 확인했다.
- Git diff로 Slice D0 외 파일이 변경되지 않았는지 확인했다.
- 임시 파일과 빈 디렉터리가 생성되지 않았는지 확인했다.

### 남은 작업

- Slice D1에서 전체 docs 디렉터리 골격과 루트 `README.md` 진입 링크를
  구축한다.

## 2026-07-23 - 문서 디렉터리 골격 및 진입점 구축

### 작업 정보

- 영역: documentation
- 브랜치: `docs/governance/documentation-system`
- 관련 계획: Slice D1 - docs 디렉터리 골격 및 진입점

### 목적

GitHub에서 프로젝트 문서 영역을 바로 탐색할 수 있게 하고, 영역 간 책임이
겹치거나 구현되지 않은 빈 문서가 대량으로 생성되는 것을 방지한다.

### 구현 내용

- 루트 `README.md`에 프로젝트 설명과 문서 진입 링크를 추가했다.
- `docs/index.md`에 아홉 개 문서 영역과 책임을 정리했다.
- 아키텍처, API, 데이터, 거버넌스, 개발, 문제 해결, 운영과 대회 영역에
  최소 `README.md`를 추가했다.
- 각 영역에 포함할 내용, 제외할 내용과 세부 문서 생성 기준을 명시했다.
- 예정된 세부 문서는 실제 내용이 생길 때 생성하도록 유지했다.

### 주요 변경 파일

- `README.md`
- `docs/index.md`
- `docs/*/README.md`
- `CHANGELOG.md`
- `docs/development/development_notes.md`

### 설계 결정

- Git이 빈 디렉터리를 추적하지 못하는 문제는 `.gitkeep` 대신 역할을
  설명하는 `README.md`로 해결했다.
- 영역별 README는 기준 문서를 대신하지 않고 책임과 문서 추가 기준만
  설명한다.
- 구현되지 않은 기능의 문서와 실행 예시는 미리 생성하지 않는다.

### 검증

- Markdown 파일의 로컬 상대 링크와 대상 파일 존재 여부를 확인했다.
- 모든 필수 문서 영역이 존재하는지 확인했다.
- 문서와 루트 안내에서 프로젝트명이 `cheongnyeon-alimi`로 통일됐는지
  확인했다.
- Git diff 공백 오류와 빈 파일·빈 디렉터리 여부를 확인했다.
- `opensource_plan/`에 변경이 없는지 확인했다.

### 남은 작업

- Slice D2에서 기존 계획 문서의 협업 규칙을 현재 정책과 충돌 없이
  Markdown 기준 문서로 이관한다.

## 2026-07-23 - 협업 및 거버넌스 정책 이관

### 작업 정보

- 영역: governance
- 브랜치: `docs/governance/collaboration-policy`
- 관련 계획: Slice D2 - 협업·거버넌스 문서 이관

### 목적

여러 Word 계획 문서에 나뉜 브랜치, 커밋, 리뷰와 역할 규칙을 실제 개발에서
사용할 하나의 Markdown 정책 체계로 통합한다.

### 구현 내용

- `main`, `develop`과 작업 브랜치의 역할 및 병합 흐름을 정의했다.
- 작업 브랜치 이름을 `<type>/<domain>/<task>`로 통일했다.
- Conventional Commits의 type, scope와 description 규칙을 정리했다.
- PR 작성자·리뷰어 책임과 최소 병합 기준을 연결했다.
- 데이터, 백엔드, 프론트엔드와 팀장·공통 책임 및 공동 계약 항목을 정의했다.
- 문서화 정책에서 다른 거버넌스 문서와 실제 저장소 우선 원칙을 연결했다.

### 주요 변경 파일

- `docs/governance/branch_strategy.md`
- `docs/governance/commit_convention.md`
- `docs/governance/code_review.md`
- `docs/governance/documentation_policy.md`
- `docs/governance/role_assignment.md`
- `docs/governance/README.md`
- `docs/index.md`
- `CHANGELOG.md`

### 설계 결정

- 짧은 하이픈형 브랜치 예시는 사용하지 않고 세 구간 이름 규칙으로 통일했다.
- 현재 릴리스 흐름은 `develop → main`으로 유지하고 별도 release 브랜치는
  정책 정의 전까지 도입하지 않는다.
- 역할 문서는 담당자 이름 대신 영역별 책임과 공동 검토 지점을 정의한다.
- 계획과 실제 상태가 다르면 저장소 상태를 확인하되 임의로 설정을 변경하지
  않는다.

### 검증

- Markdown 파일의 로컬 상대 링크와 대상 파일 존재 여부를 확인했다.
- 거버넌스 문서 사이의 브랜치 이름, PR 방향과 승인 기준을 대조했다.
- 프로젝트명과 금지된 짧은 브랜치 예시가 남아 있지 않은지 확인했다.
- Git diff 공백 오류와 빈 파일·빈 디렉터리 여부를 확인했다.
- `opensource_plan/`에 변경이 없는지 확인했다.

### 남은 작업

- GitHub 브랜치 보호, CODEOWNERS와 PR 템플릿은 실제 설정 작업 Slice에서
  정책과 일치하도록 구성한다.
- Slice D3에서 현재 시스템 아키텍처 기준선을 문서화한다.
