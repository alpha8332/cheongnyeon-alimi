# 운영 문서

이 디렉터리는 현재 시스템의 설치, 수집, Production 발행과 복구 절차를
관리한다.

- [Windows Docker 최초 실행](docker_first_run.md): clone·ZIP 사용자의 API key
  없는 공개 dataset 설치와 Web UI 실행
- [Collector 실행](collector.md): 중앙 수집기, queue, scheduler와 Runtime 처리
- [Production 배포와 dataset 발행](production_delivery.md): image·manifest·
  promotion과 공급망 검증

구조적 책임은 `docs/architecture/`, 데이터 판정은 `docs/data/`, API 계약은
`docs/api/`, 실제 장애의 원인과 해결은 `docs/troubleshooting/`를 따른다.

삭제·초기화 명령은 정확한 Compose project와 Volume을 확인한 뒤 실행한다.
실제 API key, 관리자 PIN, token, DB 비밀번호와 Raw payload를 명령 기록·로그·
문서에 남기지 않는다.
