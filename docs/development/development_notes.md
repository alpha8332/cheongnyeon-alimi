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
