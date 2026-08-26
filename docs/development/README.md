# 개발 문서

이 디렉터리는 현재 저장소를 실행하고 검증하려는 기여자를 위한 실무 문서만
관리한다. 완료된 주차별 계획, 작업 Slice와 구현 일지는 현재 계약 문서에
반영된 뒤 제출본에서 제거한다.

## 문서

- [문서 품질 검증](documentation_validation.md): 링크, 경로, 비밀정보와 문서
  구조를 검사하는 방법
- [Backend Windows 로컬 환경](backend_local_setup.md): Python 가상환경과
  PostgreSQL 기반 Backend 테스트 방법
- [Frontend 실제 API 수동 테스트](frontend_real_api_manual_testing_guide.md):
  Mock이 아닌 Docker Backend와 UI를 함께 검증하는 방법

## 기록 원칙

- 현재 시스템 계약은 `docs/architecture/`, `docs/api/`, `docs/data/`와
  `docs/operations/`에 기록한다.
- 사용자 기능 설명은 `docs/product/`에 기록한다.
- 실제로 발생했고 재사용 가능한 해결법이 확인된 문제는
  `docs/troubleshooting/`에 기록한다.
- 예정 작업과 논의는 GitHub Issue·Pull Request에서 관리한다.
- 사용자에게 의미 있는 완료 변경은 루트 `CHANGELOG.md`에 요약한다.

실행하지 않은 명령이나 테스트를 성공했다고 기록하지 않으며, 실제 API key,
PIN, access token, DB 비밀번호와 Raw 원문은 문서에 남기지 않는다.
