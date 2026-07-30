# Frontend React Router Advisory Review Forest 개발 계획

## 계획 정보

- 번호: Frontend 02
- 담당 영역: Frontend
- 상태: in-progress
- 작업 브랜치: `fix/backend/week2-hardening`
- 공유 Forest:
  [Backend Policy Runtime Safety](../backend/03_policy_runtime_safety.md)
- 선행 Forest:
  [Frontend Policy Discovery](01_policy_discovery.md)
- 대상 사항: `npm audit`의 React Router RSC 관련 high 2건

## 목적

현재 client-only Vite Frontend에서 보고된 React Router RSC advisory의
실제 도달 가능성과 호환 가능한 수정 버전을 확인한다. 안전한 버전 변경이
가능하면 의존성을 갱신하고, 불가능하면 위험 수용 범위와 재검토 조건을
명시적으로 기록한다.

## 범위

- 현재 lockfile 기준 `npm audit` 결과 재현
- advisory의 영향 package·버전·실행 경로 확인
- 현재 앱의 RSC action 또는 관련 server 기능 사용 여부 확인
- 호환 가능한 안전 버전과 breaking change 검토
- 필요 시 `package.json`과 lockfile 동기화
- 소비 테스트·lint·build와 브라우저 기본 회귀
- 수정 또는 위험 수용 결정 문서화

## 범위 밖

- Router 구조 전면 재작성
- 일반적인 Frontend 의존성 일괄 upgrade
- Policy API·DTO·Mock 계약 변경
- Backend 인증·API와 배포 아키텍처 변경

## 선행 조건

- 공식 advisory와 package metadata를 실행 시점에 다시 확인한다.
- `npm audit fix --force`를 검토 없이 실행하지 않는다.
- 현재 Node·npm 버전과 저장소 lockfile을 기준으로 재현한다.

## 공통 설계 원칙

- audit severity만으로 사용하지 않는 실행 경로를 사용 중이라고 단정하지
  않는다.
- 호환 가능한 안전 버전이 있으면 직접 의존성과 lockfile을 함께 갱신한다.
- 강제 downgrade·major 변경이 필요하면 기능·타입·라우팅 영향을 먼저
  검증한다.
- 안전 버전이 없으면 영향 범위, 임시 보호 조건과 재검토 trigger를 기록한다.
- 실행하지 않은 test·lint·build를 성공으로 기록하지 않는다.

## Slice 계획

### F0 - Advisory 재현과 도달 가능성 검토

- 상태: completed
- 목적:
  현재 의존성 트리와 앱 실행 경로에서 advisory의 실제 영향을 확정한다.
- 산출물:
  - `npm audit` 재현 결과
  - 영향 package 경로와 RSC 기능 사용 여부 기록
- 선행 조건:
  - 공식 advisory와 package metadata 접근 가능
- 완료 기준:
  - 취약 package·버전과 현재 앱의 도달 가능성을 구분해 기록

2026-07-30 현재 lockfile과 공식 advisory를 다시 확인했다. npm은
`react-router-dom@7.18.1`에서 전이되는 `react-router@7.18.1` 때문에 high
2건을 보고하며, 두 항목은 하나의 RSC CSRF advisory
`GHSA-qwww-vcr4-c8h2`에서 파생된다. 공식 영향 조건은 unstable RSC API
사용이다. 현재 앱은 Vite client-only `createBrowserRouter` 구성이고
RSC·server action API를 사용하지 않아 현재 실행 경로에서는 도달할 수
없다. 재현 명령과 상세 근거는
[개발 기록](../../development_notes/frontend/react_router_advisory.md)에
남겼다.

### F1 - 호환 버전 결정

- 상태: draft
- 목적:
  기능 회귀 없이 적용 가능한 dependency 대응 방법을 결정한다.
- 산출물:
  - upgrade·downgrade·위험 수용 중 선택한 대응과 이유
- 선행 조건:
  - F0 완료
- 완료 기준:
  - 강제 변경 여부와 Router API 호환성 검토 완료

### F2 - 의존성 또는 보호 조치 반영

- 상태: draft
- 목적:
  F1 결정에 따라 manifest·lockfile 또는 위험 수용 기록을 반영한다.
- 산출물:
  - 필요 시 갱신된 `package.json`과 lockfile
  - 수정하지 않을 경우 적용 범위와 재검토 trigger
- 선행 조건:
  - F1 완료
- 완료 기준:
  - 설치 의존성과 결정 문서가 일치
  - 임의의 `--force` 변경 없음

### F3 - Frontend 회귀와 문서 동기화

- 상태: draft
- 목적:
  의존성 결정이 기존 Policy Discovery 동작을 깨뜨리지 않았음을 확인한다.
- 산출물:
  - 실제 실행한 소비 테스트·lint·build·브라우저 결과
  - Frontend 개발 기록과 필요한 인계사항 갱신
- 선행 조건:
  - F2 완료
  - Codex CLI·VS Code Codex에서는 브라우저 제어를 지원하지 않으므로,
    자동 검증과 빌드가 끝난 뒤 ChatGPT 데스크톱 앱의 Browser에서
    `http://localhost:3000`을 확인할 수 있는 환경 준비
- 완료 기준:
  - `npm ci`, `npm test`, `npm run lint`, `npm run build` 통과
  - ChatGPT 데스크톱 앱의 Browser에서 주요 라우팅 기본 회귀 확인
  - `python scripts/validate_docs.py` 통과

## 검증 계획

- `npm ci`
- `npm audit`
- `npm test`
- `npm run lint`
- `npm run build`
- ChatGPT 데스크톱 앱의 Browser에서 홈·목록·숫자 ID 상세·partial opt-in
  route 확인
- `python scripts/validate_docs.py`
- `git diff --check`

## Forest 완료 기준

- advisory의 현재 앱 도달 가능성 확인
- 호환 가능한 수정 적용 또는 근거 있는 위험 수용 결정
- manifest·lockfile·문서 일치
- Frontend 자동·브라우저 회귀 통과
- 후속 재검토 조건이 필요하면 인계 보드에 명시

## 위험과 미확정 사항

- 실행 시점의 공식 advisory와 안전 버전 상태가 바뀔 수 있다.
- 자동 수정이 Router major·minor 호환성 변경이나 downgrade를 요구할 수 있다.
- 현재 client-only 앱이 RSC 기능을 사용하지 않더라도 향후 구조 변경 시
  도달 가능성이 달라질 수 있다.

## 관련 문서

- [Frontend Policy Discovery 계획](01_policy_discovery.md)
- [Frontend Policy Discovery 개발 기록](../../development_notes/frontend/policy_discovery.md)
- [Policy API 계약](../../../api/policies.md)
- [공동 확인 및 인계 보드](../../../index.md#공동-확인-및-인계-보드)
