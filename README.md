# cheongnyeon-alimi

공공 청년정책 데이터를 수집·정제하고 사용자가 정책을 검색하고 추천받을 수
있도록 만드는 오픈소스 웹 플랫폼이다.

## 문서

프로젝트의 문서 구조, 개발 전후 확인 사항과 변경 유형별 문서 갱신 기준은
[docs/index.md](docs/index.md)에서 확인한다.

현재 온통청년·복지로의 제한 수집과 Raw 저장 기반이 구현되어 있다. 환경변수와
안전한 실행 범위는 [Collector 실행 문서](docs/operations/collector.md)를
따른다. 구현되지 않은 전체 수집, Scheduler와 서비스 기능은 완료된 것으로
안내하지 않는다.

Windows에서 Backend와 PostgreSQL 통합 테스트를 실행하는 절차는
[Backend Windows 로컬 환경](docs/development/backend_local_setup.md)을
따른다.
