# cheongnyeon-alimi

공공 청년정책 데이터를 수집·정제하고 사용자가 정책을 검색하고 추천받을 수
있도록 만드는 오픈소스 웹 플랫폼이다.

## 문서

프로젝트의 문서 구조, 개발 전후 확인 사항과 변경 유형별 문서 갱신 기준은
[docs/index.md](docs/index.md)에서 확인한다.

현재 온통청년·복지로의 제한 수집과 Raw 저장, 저장된 Runtime Raw의
PostgreSQL 재처리, Seed·Runtime 최소 실행 이력 기반이 구현되어 있다.
환경변수와 안전한 실행 범위는
[Collector 실행 문서](docs/operations/collector.md)를 따른다. Source 전체 수집과
공개 dataset의 GitHub Release·GHCR 자동 발행 Workflow가 구현됐고 `v1.0.0`
원격 Production과 공개 dataset 457건 발행을 완료했다.

## 데이터 수집과 최신성

GitHub에서 저장소를 clone하거나 ZIP으로 내려받고 Docker를 실행하는 것만으로
최신 청년정책이 자동 수집되지는 않는다. 온통청년·복지로 실제 수집에는 각각
`YOUTHCENTER_API_KEY`, `BOKJIRO_API_KEY`가 필요하며 실제 키는 저장소, Docker
image와 배포 package에 포함하지 않는다. API 키가 없는 사용자는 Collector를
직접 실행할 수 없다.

현재 Collector는 명시적 CLI 실행, 저장된 Runtime Raw의 PostgreSQL 재처리와
관리자 화면에서 요청하는 단일 Source 수동 수집·적재를 지원한다. Docker 환경은
공개 웹 Source를 키 없이 수동 실행할 수 있고, 온통청년·복지로는 Git에서 무시되는
`.env.compose`에 각 API key를 넣어야 한다. Acceptance Compose에는 Redis broker,
Celery worker와 단일 Beat가 구현돼 있지만 정기 수집은 안전하게
`COLLECTION_SCHEDULE_ENABLED=false`가 기본값이다. 따라서 API key와 승인된
Source 주기를 설정하지 않고 웹 UI만 켠 상태에서는 신규 정책이 자동 추가되지
않는다. 종료일이 지난 정책은 현재 KST 기준 공개 검색·추천에서 즉시 제외된다.
공개 dataset 발행용 완전 수집은 중앙 환경에서만
`COLLECTION_SCHEDULE_COMPLETE_SNAPSHOT=true`로 별도 승인하며, 관리자 화면의
일반 제한 수집 성공은 공개 latest를 갱신하지 않는다.

최종 공개 배포는 각 사용자 PC가 동일 Source를 직접 반복 수집하는 방식이 아니라,
승인된 중앙 수집 환경이 API 키와 호출량을 관리하고 재배포가 허용된 정규화
dataset을 버전화하여 사용자가 최초 실행·갱신 때 검증 후 로컬 PostgreSQL에
적재한다. Windows 실행기, hash·Schema 검증, immutable cache, Migration과
멱등 bootstrap과 Production Compose·CI promotion/rollback은 구현됐다. 실제
공개 Release는 보호된 `production-data` Environment의 GitHub-hosted 일회성
PostgreSQL·Redis·Celery 수집과 완전성 검증 뒤에만 갱신한다. 사용자 PC의 DB
접속 정보나 장기 Self-hosted Runner는 사용하지 않는다.
실제 정책 Raw와 DB dump는 Git에 커밋하지 않는다.

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

전체 웹 UI는 Frontend image 하나를 Docker Desktop에서 개별 실행하는 방식이
아니라, 저장소 루트의 `run_docker.bat`이 PostgreSQL·Redis·Migration·공개
dataset bootstrap·Backend·worker·Beat·Frontend를 함께 시작한다. API key는
공개 최초 실행에 필요하지 않으며 첫 실행 때 관리자 4자리 PIN만 입력한다.

```powershell
.\run_docker.bat
```

기본 GitHub Release dataset pointer가 활성화되어 공개 dataset 457건을 자동으로
검증·적재한다. 요구 환경, cache, offline 재실행과 실패 복구는
[Windows Docker 최초 실행](docs/operations/docker_first_run.md)을 따른다.

운영 image·Nginx Compose, GHCR release와 dataset 승격·롤백은
[Production 배포와 데이터셋 발행](docs/operations/production_delivery.md)을
따른다.

Acceptance snapshot을 다른 PC에 동일하게 인계하는 별도 절차는
[Docker Acceptance 환경 설정](docs/development/docker_acceptance_setup.md)과
[동일 환경 인계 패키지](docs/development/handoff/docker_acceptance/README.md)에
정의되어 있다.

## 라이선스

프로젝트 코드는 [MIT License](LICENSE)로 배포한다. 정책 데이터의 재배포 범위와
출처 표시는 코드 라이선스와 별개이며
[공개 정책 dataset 계약](docs/data/public_policy_dataset.md)을 따른다.
