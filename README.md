# cheongnyeon-alimi

공공 청년정책 데이터를 수집·정제하고 사용자가 정책을 검색하고 추천받을 수
있도록 만드는 오픈소스 웹 플랫폼이다.

## 문서

프로젝트의 문서 구조, 개발 전후 확인 사항과 변경 유형별 문서 갱신 기준은
[docs/index.md](docs/index.md)에서 확인한다.

현재 온통청년·복지로의 제한 수집과 Raw 저장, 저장된 Runtime Raw의
PostgreSQL 재처리, Seed·Runtime 최소 실행 이력 기반이 구현되어 있다.
환경변수와 안전한 실행 범위는
[Collector 실행 문서](docs/operations/collector.md)를 따른다. 구현되지 않은
전체 수집, Scheduler와 자동 주기 적재는 완료된 것으로 안내하지 않는다.

Windows에서 Backend와 PostgreSQL 통합 테스트를 실행하는 절차는
[Backend Windows 로컬 환경](docs/development/backend_local_setup.md)을
따른다.

Windows에서 실제 PostgreSQL을 사용하는 전체 시스템을 실행하려면 저장소
루트의 `run.bat`를 실행한다. Backend와 Frontend가 같은 터미널에서 실행되고
홈 화면이 열리며, 종료할 때는 해당 터미널에서 `Ctrl+C`를 누른다. 별도
pgpass 경로가 필요하면 첫 번째 인자로 전달할 수 있다. Release 1 역할별 확인
항목은
[Release 1 독립 검증 증거 안내](docs/contest/release_1_evidence_guide.md)를
따른다.

기본 DB가 아닌 명시적으로 준비한 격리 DB를 사용하려면 PowerShell에서
`run.bat -PgpassFile <path> -DatabaseName <database>`로 실행한다. DB 이름은
영문자·숫자·밑줄·하이픈만 허용하며 pgpass에도 해당 DB 또는 `*` 항목이 있어야
한다.
