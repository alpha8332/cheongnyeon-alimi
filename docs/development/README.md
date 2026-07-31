# 개발 문서

이 디렉터리는 개발 환경, 구현 지침과 완료된 개발 작업의 사실 기반 기록을
관리한다.

## 포함하는 내용

- 로컬 개발 환경과 설정 방법
- 프로젝트 공통 코딩 지침
- 구현된 기능과 주요 구조 변경의 개발 기록
- 아직 완료하지 않은 Forest의 개발 계획
- 실제로 실행한 테스트와 검증 결과

개발 문서는 Forest를 기준으로 계획과 실제 결과를 대응시킨다.

- [개발 계획](develop_plan/README.md): 아직 완료하지 않은 Forest의 범위,
  Slice와 완료 기준, 여러 Forest의 Release·주차별 조정 로드맵
- [주차별 상세 실행 계획](weekly_plan/README.md): 해당 주차의 선행 관계,
  병렬 작업, 역할별 책임과 통합 Gate
- [개발 기록](development_notes/README.md): Forest에서 실제로 구현하고
  검증한 상세 결과
- [문서 품질 검증](documentation_validation.md): 문서 검증 명령과 검사 규칙
- [Backend Windows 로컬 환경](backend_local_setup.md): Windows `.venv`,
  PostgreSQL 테스트 역할·DB와 전체 Backend 테스트 절차

계획과 개발 기록은 담당 영역이 명확할 때 `data/`, `backend/`, `frontend/`,
`integration/`으로 구분한다. 둘 이상의 영역에 걸친 공통 기반과 연결 작업은
`integration/`에서 관리한다. 폴더는 실제 Forest 문서가 생길 때 생성하며,
담당자 이름이 아니라 작업 책임을 기준으로 분류한다.

## 포함하지 않는 내용

- Forest·Release 구현 범위와 직접 관련 없는 조직 일정
- 사용자와 팀을 위한 변경 요약: 루트 `CHANGELOG.md`
- 재사용 가능한 장애 해결 절차: `docs/troubleshooting/`
- 운영 환경의 정기 작업과 복구 절차: `docs/operations/`

실행하지 않은 명령이나 테스트를 성공한 결과로 기록하지 않는다. 환경이나
기능이 실제로 추가될 때 관련 문서를 생성한다.
