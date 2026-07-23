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
