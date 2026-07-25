# 아키텍처 문서

이 디렉터리는 `cheongnyeon-alimi` 전체 시스템의 구조와 구성 요소 사이의
경계를 설명한다.

## 포함하는 내용

- 시스템 개요와 주요 구성 요소
- 데이터 수집부터 사용자 화면까지의 전체 흐름
- 컨테이너와 배포 단위의 구조
- 여러 영역에 영향을 주는 아키텍처 결정과 근거

## 현재 문서

- [시스템 아키텍처 개요](overview.md)
- [시스템 흐름](system_flow.md)
- [컨테이너 구조](container_structure.md)
- [아키텍처 결정 기록](decisions/README.md)

## 문서 분류 기준

Architecture 문서는 담당자의 작업 기록이 아니라 현재 시스템의 구조, 경계와
영역 간 관계를 설명한다.

- `overview.md`, `system_flow.md`, `container_structure.md`는 Data, Backend,
  Frontend가 함께 참조하는 공통 문서로 유지한다.
- 특정 영역의 구조 설명이 공통 문서에서 분리할 만큼 커졌을 때만 `data/`,
  `backend/`, `frontend/` 하위 디렉터리와 문서를 생성한다.
- 둘 이상의 영역에 영향을 주거나 되돌리기 어려운 구조 결정은
  [`decisions/`](decisions/README.md)에 ADR로 기록한다.
- 여러 영역의 현재 구조를 함께 설명해야 하지만 별도 ADR이 필요하지 않으면
  이 디렉터리의 공통 문서에 반영한다.
- 기능 구현 과정, 변경 파일과 테스트 결과는 Architecture가 아니라 담당
  영역의 `docs/development/development_notes/`에 기록한다.
- 미래 구조 제안과 아직 구현하지 않은 설계는 Architecture의 현재 상태처럼
  작성하지 않고 관련 `docs/development/develop_plan/`에서 관리한다.

문서를 작성한 담당자가 아니라 설명하는 구조의 범위로 위치를 결정한다. 실제
내용이 없는 역할별 디렉터리는 미리 만들지 않는다.

## 포함하지 않는 내용

- 아직 합의되지 않은 미래 설계: `docs/development/develop_plan/`
- 개별 API의 요청·응답 계약: `docs/api/`
- 데이터 필드와 정규화 규칙: `docs/data/`
- 서비스 실행과 장애 대응 절차: `docs/operations/`

시스템 경계나 구성 요소의 책임이 실제로 확정되거나 변경될 때 문서를
추가한다. 구현되지 않은 구조는 현재 아키텍처로 표현하지 않는다.
