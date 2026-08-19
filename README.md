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
한다. Node.js는 PATH를 우선 사용하고 Codex 데스크톱의 번들 Node.js가 있으면
자동으로 대체 사용한다. 다른 Node.js 실행 파일을 지정하려면
`-NodeExecutable <path>`를 함께 전달한다.

## Docker로 웹 UI 실행

다른 PC에서 같은 PostgreSQL snapshot·Backend·Frontend를 실행하는 Docker
Acceptance 경로를 구축하고 있다. 전체 웹 UI는 Frontend image 하나를 Docker
Desktop에서 개별 실행하는 방식이 아니라, `compose.yaml`로 PostgreSQL →
Migration → Backend → Frontend를 함께 시작한다.

현재 `DEP2_PASS`까지 완료했으며 image·Compose build와 안전 경계는 검증됐다.
실제 snapshot 복원·Browser 검증과 다른 PC 인계가 끝나는
`DOCKER_ACCEPTANCE_PASS` 전까지는 대회 심사자용 최종 실행 패키지로 안내하지
않는다. 최초 실행, Docker Desktop 재실행과 웹 UI 접속 방법은
[Docker Acceptance 환경 설정](docs/development/docker_acceptance_setup.md)을
따른다. 다른 PC 인계용 암호화 package·receipt와 역할별 결과 양식은
[Docker Acceptance 동일 환경 인계 패키지](docs/development/handoff/docker_acceptance/README.md)에
정의되어 있다.
