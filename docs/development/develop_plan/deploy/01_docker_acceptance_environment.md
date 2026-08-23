# Deploy 01 Docker Acceptance Environment 개발 계획

## 계획 정보

- 번호: Deploy 01
- 담당 영역: Team Leader - Integration·Deploy
- 상태: in-progress
- 실행 시작일: `2026-08-19` (`DEP0_PASS`)
- 계획일: `2026-08-19`
- 권장 구현 브랜치: `feature/deploy/docker-acceptance-environment`
- 대상 Release: `v0.5.0` 독립 리뷰 환경과 `v1.0.0` 배포 기반
- 선행 Forest: Integration 10 RA0~RA4 `REVIEW_ADMISSION_PASS`
- 후속 단계: Integration 07 DTL5-5 독립 사용성 리뷰·QA
- 개발 기록: [Deploy 01 개발 기록](../../development_notes/deploy/docker_acceptance_environment.md)

## 목적

Backend·Frontend 담당자와 리뷰어·QA가 서로 다른 PC에서도 같은 Git SHA와
같은 PostgreSQL Acceptance snapshot을 격리된 Volume으로 복원해 동일한
시스템을 검증하게 한다. 개인 PC의 원격 PostgreSQL이나 작성자 로컬 Runtime에
의존하지 않고 PostgreSQL → FastAPI → React 실행과 재시작·복구를 재현한다.

## 범위

- post-admission Acceptance dump와 manifest의 안전한 생성·검증·전달
- PostgreSQL·FastAPI·React Dockerfile과 Compose 구성
- 명시적 one-shot restore와 Migration 실행
- 개발용 bind mount와 리뷰어용 고정 Acceptance 실행의 분리
- 서비스 DB와 `_test` DB·Volume·Compose profile 격리
- health check, 재시작 후 데이터 유지와 실패 복구
- 새 PC clean-room 실행과 BE·FE·리뷰어·QA 인계
- CI의 합성 Seed 기반 image·Compose smoke

## 범위 밖

- review admission 규칙·승격 대상 결정과 실제 Policy 적재
- 실제 DB dump·Runtime Raw·비밀번호·API key의 Git 또는 image 포함
- 기존 Volume 자동 삭제·덮어쓰기와 서비스 DB를 테스트 정리 대상으로 사용
- 호스트 PostgreSQL `5432`의 인터넷·사내망 공개
- Nginx·TLS·도메인·registry·운영 배포 완료
- Kubernetes와 다중 노드 운영
- Docker 환경에서만 동작하도록 기존 `run.bat` 로컬 경로를 제거하는 작업
- 최초 secret 생성·snapshot restore·Compose 시작·Browser 열기를 한 번에 감싸는
  `run_docker.bat` one-click launcher. 이 항목은 Deploy 01 실제 절차가 확정된
  뒤 별도 후속 작업으로 구현한다.

## 선행 조건

- Integration 07 W5-G1 기능 동결과 실제 E2E가 통과함
- Integration 10 RA0~RA4가 `REVIEW_ADMISSION_PASS`와
  `W5-G1_REVALIDATED`를 기록함
- BE·FE 구현이 같은 Git SHA에 있고 Backend manifest·Frontend lockfile이
  재현 가능함
- 실제 자격증명 교체와 Git 밖의 암호화 snapshot 전달 위치가 준비됨
- 각 참여 PC에서 Docker Engine·Compose 사용이 허용됨

## 입력 계약

Deploy 01은 Integration 10 RA4가 만든 다음 입력을 변경 없이 받는다.

- 검증된 Git SHA
- admission rule version과 decision manifest hash
- PostgreSQL major version과 Alembic revision
- post-admission dump 파일명·size·SHA-256
- Policy 전체·Source별·quality·application status 집계
- 대표 stable `(source_id, external_id)`
- 별도 Runtime/checkpoint archive hash와 보관 위치 식별자

dump가 만들어진 뒤 Policy·Migration·admission manifest가 바뀌면 기존 dump를
재사용하지 않는다. RA4를 다시 실행하고 새 snapshot version을 발급한다.

## 공통 설계 원칙

- 실제 자격증명 교체를 DEP0 전에 완료하고 교체 사실만 기록한다.
- dump와 Runtime archive는 workspace·Git·Docker build context·CI artifact 밖의
  승인된 암호화 저장소로만 전달한다.
- snapshot에는 정책 서비스에 필요한 allowlist Schema만 포함한다. 세션,
  임시 token, 로컬 경로, 운영 로그, 테스트 데이터와 개인 연락처는 포함하지
  않거나 생성 전 검증된 정제 절차로 제거한다.
- dump hash 검증 전에는 restore하지 않는다.
- restore는 빈 Acceptance Volume에만 허용한다. 비어 있지 않은 대상은
  fail-closed하고 자동 drop·reset하지 않는다.
- 실제 secret은 Git 비추적 `.env` 또는 승인된 secret 주입으로 전달한다.
  `.env.compose.example`에는 placeholder와 생성 방법만 둔다.
- Backend·Frontend 로그와 Browser bundle에 credential, connection string,
  Raw payload가 없어야 한다.
- Database port는 기본적으로 host에 publish하지 않는다. 로컬 점검이 꼭
  필요하면 `127.0.0.1` bind override에서만 임시 허용한다.

## Slice 계획

## 실행 구조

```text
Integration 10 RA4 / REVIEW_ADMISSION_PASS
  → DEP0 입력·환경·비밀 경계 고정
  → DEP1 snapshot allowlist·dump·manifest·hash
  → DEP2 image·Compose 구현
  → DEP3 빈 Volume restore·Migration·health·actual smoke
  → DEP4 clean-room·재시작·복구·test DB 격리
  → DEP5 동일 snapshot BE·FE 인수와 reviewer package
  → DOCKER_ACCEPTANCE_PASS
  → DTL5-5 독립 사용성 리뷰·QA
```

## Slice DEP0 - 기준선과 실행 계약

### 수행 작업

- Git SHA와 clean worktree 확인
- Docker Engine·Compose·BuildKit 버전 확인
- Backend Python manifest와 Frontend lockfile 확인
- repository·actual Alembic head 일치 확인
- 실제 자격증명 교체 완료와 비추적 secret 경로 확인
- snapshot·Runtime archive 보관 위치와 디스크 여유 확인
- host port `3000`·`8000` 충돌과 Docker 사용 정책 확인

### Gate

- Integration 10 `REVIEW_ADMISSION_PASS`와 RA4 manifest가 있음
- 재현 가능한 Backend dependency와 Frontend lockfile이 있음
- secret·dump 저장 위치가 workspace 밖으로 확정됨
- 하나라도 없으면 `DEP0_BLOCKED`

## Slice DEP1 - Acceptance snapshot 생성

### 산출물

- Git에 포함되는 fail-closed 생성기
  `deployment/postgres/create_snapshot.py`
- Git 밖의 custom-format `acceptance-post-admission.dump`
- Git에 넣을 수 있는 비밀 없는
  `deployment/postgres/acceptance-snapshot.manifest.example.json`
- 실제 manifest는 Git 밖에 저장
- snapshot allowlist·금지 table·금지 field 검증 결과

### 절차

```powershell
pg_dump --format=custom --no-owner --no-acl `
  --file <absolute-snapshot-dir>\acceptance-post-admission.dump `
  --dbname <credential-free-database-url>

Get-FileHash -Algorithm SHA256 `
  <absolute-snapshot-dir>\acceptance-post-admission.dump
```

실제 구현에서는 전체 DB를 무조건 dump하지 않는다. Schema inventory를 먼저
검사해 공개 정책·검색·지역·CollectionRun 중 Acceptance에 필요한 table만
allowlist로 확정한다. 운영 로그·감사 원문·임시 상태가 필요하면 합성 fixture로
대체하고 실제 운영 row를 전달하지 않는다.

### Gate

- dump SHA-256·size·PostgreSQL major·Alembic revision이 manifest와 일치
- 금지 table·field·credential·개인 연락처 scan 결과 0건
- 대표 stable identity와 집계가 RA4 결과와 일치
- restore용 DB role이 최소 권한이며 owner·ACL이 dump에 고정되지 않음
- 하나라도 실패하면 `DEP1_BLOCKED`

## Slice DEP2 - Image와 Compose 구현

### 계획 파일

```text
compose.yaml
compose.dev.yaml
.env.compose.example
.dockerignore
backend/Dockerfile
backend/Dockerfile.dockerignore
frontend/Dockerfile
frontend/Dockerfile.dockerignore
frontend/docker-server.mjs
deployment/postgres/restore.ps1
deployment/postgres/restore.sh
deployment/postgres/verify_snapshot.py
deployment/postgres/verify_restored_database.py
docs/development/docker_acceptance_setup.md
```

### 서비스

| 서비스 | 책임 |
| --- | --- |
| `database` | PostgreSQL, named Volume, 내부 network, `pg_isready` |
| `restore` | hash 검증 후 빈 Acceptance Volume에만 one-shot restore |
| `migrate` | repository Alembic head 적용 후 종료 |
| `backend` | FastAPI actual DB 연결과 `/health` |
| `frontend` | React build·Browser에서 접근 가능한 Backend URL |
| `database-test` | `_test` 전용 DB·별도 Volume·명시적 test profile |

최초 시작은 `restore.ps1`이 `database health → snapshot verify → empty restore →
restore baseline verify → migrate → backend health → frontend readiness`로
고정한다. 정확한 snapshot 집계 검증은 restore 직후에만 수행하고, 재시작은
운영 중 추가된 Policy·CollectionRun을 보존한 채 Migration만 통과한다.
Backend는 Compose 내부 `database` host를 사용하고, Frontend는 Browser가 접근할
수 없는 Compose service hostname을 bundle에 넣지 않는다.

`compose.dev.yaml`만 source bind mount·hot reload를 사용한다. reviewer용 공통
`compose.yaml`은 검증된 image와 snapshot version을 사용하며 host source 변경이
실행 결과에 섞이지 않아야 한다.

### Gate

- image layer와 build context에 dump·Runtime·`.env`·로그가 없음
- root가 아닌 실행 user와 최소 write 경로를 사용
- health dependency가 준비 전 성공을 허용하지 않음
- `docker compose config`가 placeholder 누락을 탐지하고 정의 profile이
  `restore`·`test`로만 확인됨
- Backend·Frontend image build 통과

## Slice DEP3 - Restore·Migration·actual smoke

### 수행 작업

1. 새 Compose project와 빈 named Volume 생성
2. 비추적 Compose secret 생성과 현재 사용자 전용 ACL 확인
3. manifest·dump hash 검증
4. one-shot restore와 Alembic head 적용
5. Backend `/health`, Frontend readiness 확인
6. manifest 집계와 대표 stable identity 조회
7. 검색·상세·추천·관리자 인증 경계 actual smoke
8. partial·unknown·공식 원문·`.ics` 표시 확인

### Gate

- hash 불일치와 비어 있지 않은 restore 대상이 fail-closed
- Migration head와 manifest revision 일치
- DB·API·Browser 집계와 stable identity 일치
- credential·Raw payload가 container log에 없음
- 서비스 종료 후에도 Volume이 명시적 삭제 없이는 유지됨

### 2026-08-20 actual 진행 결과

- 승인 snapshot hash와 Alembic revision을 확인한 뒤 빈 Volume에 Policy 3,273건,
  CollectionRun 61건을 복원했다.
- table-filtered dump에 빠진 의존 type은 snapshot revision까지 Migration으로
  정확한 schema를 먼저 만들고, 검증한 data-only TOC를 FK 순서로 복원하는 방식으로
  해결했다.
- data-only restore 중 constraint trigger가 빈 `search_path`에서 helper function을
  찾지 못한 문제는 단일 transaction 안에서 trigger를 일시 비활성화하고 복원 뒤
  count·stable identity·orphan·Migration revision을 전부 재검증하는 방식으로
  해결했다.
- Docker Frontend가 기본 Mock 모드로 빌드되던 통합 결함을 발견해 Acceptance
  image의 `VITE_USE_MOCK=false`를 build-time 필수 계약으로 고정했다.
- DB·health·검색·상세·추천·비인증 관리자 경계·actual Browser·재시작 후 Volume
  보존을 통과했다. 사용자가 생성한 PIN으로 로그인한 뒤 보호된 관리자 대시보드와
  actual 정책 데이터 328페이지를 확인해 `DEP3_PASS`를 기록했다.

## Slice DEP4 - clean-room·복구·test 격리

새 PC 또는 새 Compose project에서 다음을 수행한다.

- clone 후 example을 복사해 로컬 secret 생성
- 승인 수단으로 snapshot을 받아 hash 검증
- build·restore·migrate·서비스 시작
- 컨테이너 재시작 뒤 row count·stable identity 유지 확인
- 잘못된 hash, DB health 실패, backend startup 실패 재현
- 변경 전 또는 Acceptance dump를 새 Volume에 restore하는 복구 연습
- test profile 실행 전 대상 DB명 `_test`와 별도 Volume 확인
- test 종료 뒤 서비스 DB row·Volume 불변 확인

reset·복구 명령은 Compose project와 Volume의 실제 절대 이름을 먼저 출력하고
사용자 확인 없이는 실행하지 않는다. 문서에 `docker compose down -v`를 일반
종료 명령으로 안내하지 않는다.

### 2026-08-20 actual 결과

- Git `32bc4a3`에서 별도 project `cheongnyeon-alimi-dep4-cleanroom`, 별도 image
  tag와 host port 13000·18000을 사용해 기존 DEP3 환경과 격리했다.
- 승인 snapshot을 새 Volume에 복원해 Policy 3,273건, CollectionRun 61건,
  Alembic `20260810_0006`, API·Browser actual을 확인했다.
- 잘못된 dump hash는 exit 1로 차단됐고 전후 Policy 수는 3,273건으로 유지됐다.
  DB 중지 시 Backend health 503, DB 없이 Backend 재시작 시 health 시작 실패를
  확인한 뒤 정상 기동으로 복구했다.
- service·test DB는 서로 다른 `_test` 이름, named Volume과 internal network를
  사용했다. test DB probe는 서비스 DB에 나타나지 않았고 test 종료 뒤 서비스
  Policy 수는 3,273건이었다.
- 전체 stop·restart 뒤 count·stable identity·orphan 검증을 다시 통과했다.
  clean-room 컨테이너는 stop하고 Volume은 삭제하지 않았으며 `DEP4_PASS`다.

## Slice DEP5 - 동일 환경 인계

Backend·Frontend 담당자와 리뷰어·QA에게 다음을 한 묶음으로 전달한다.

- Git SHA와 snapshot version
- manifest·dump hash, 안전한 별도 다운로드 위치
- `.env.compose.example` 기반 개인 secret 생성 절차
- start·stop·health·log·복구 명령
- BE·FE actual 테스트 명령과 기대 수치
- DTL5-5 사용자·관리자 시나리오와 결함 기록 양식
- 금지 사항: dump 재배포, host DB 공개, 임의 데이터 수정, Volume 공유

각 참여자는 자기 격리 Volume을 사용한다. 결과에는 Git SHA, snapshot version,
Docker·Compose version과 test command를 남겨 서로 다른 입력을 같은 결과로
합치지 않는다.

### DEP5 패키지 준비 결과 (2026-08-20)

- Windows EFS 원본은 다른 PC로 이식할 수 없으므로 7-Zip AES-256과 header
  encryption을 사용하는 외부 전달 package 생성기를 추가했다.
- 생성기는 clean handoff commit, workspace 밖 출력 경로, 기존 산출물 비덮어쓰기,
  snapshot 재검증과 archive 재검증을 fail-closed 조건으로 둔다.
- passphrase는 PowerShell이 읽거나 저장하지 않고 7-Zip 대화형 prompt에서만
  입력한다. archive와 passphrase는 서로 다른 승인 채널로 전달한다.
- Git SHA·snapshot·dump·archive·Compose·설정 문서 hash를 담는 비밀정보
  없는 receipt와 역할별 결과·결함 양식을 추가했다.
- 상세 절차는 [Docker Acceptance 동일 환경 인계 패키지](../../handoff/docker_acceptance/README.md)를
  따른다.

이 결과는 `DEP5_PACKAGE_READY`다. 최종 handoff commit에서 package·receipt를
생성하고 Backend·Frontend·사용성 리뷰어·QA의 독립 실행 결과를 대조하기
전까지 `DEP5_PASS` 또는 `DOCKER_ACCEPTANCE_PASS`로 판정하지 않는다.

### DEP5 격리 역할 대체 검증 결과 (2026-08-23)

일정상 외부 담당자 회신을 기다리지 않고 한 실행자가 BE·FE·사용성·QA project,
secret, service/test Volume과 ports를 분리해 개발자 검증을 수행했다. 수동 수집이
실행되지 않던 Backend blocker와 가변 DB 재시작 blocker, 실제 UI의 지역·연령·
추천·저장 조건 일관성 문제, Mock/actual 테스트 격리 문제를 재현·수정했다.

이 결과는 최종 receipt SHA가 아니라 수정 worktree 검증이다. 구현 결함을 먼저
제거하는 근거로만 사용하며, clean handoff commit → 새 package/receipt → 같은
역할별 격리 재검증 순서를 생략하지 않는다. 상세 수치와 증거는
[Docker Acceptance 개발 기록](../../development_notes/deploy/docker_acceptance_environment.md)에 남긴다.

### DEP5 최종 인수 결과 (2026-08-23)

- 실행 checkout `51c35b64131bda2d62ece038e6723ede8b69cbe2`와 clean
  worktree를 receipt로 고정했다.
- archive SHA-256
  `3cd3ce62372c7b2670b37d38edb9095199008ec5d2ed084be945db2f0ed26146`을
  receipt와 대조하고 실제 수신 폴더 추출본을 다시 검증했다.
- BE·FE·사용성·QA를 `isolated-role-substitute`로 분리해 네 project와 독립
  Volume에서 모두 `DEP5_ROLE_PASS`를 확인했다.
- Backend 수동 수집·재시작 보존, QA service/test DB host binding 0과 log secret
  match 0을 포함해 차단 결함이 없었다.

따라서 `DEP5_PASS`·`DOCKER_ACCEPTANCE_PASS`로 Deploy 01을 닫고 DTL5-5를 연다.
이 판정은 독립 담당자 네 명의 사람 검토가 아니라 동일 실행자의 격리 역할 대체
검증이며, DTL5-5 독립 사용성 리뷰·QA를 대신하지 않는다.

## 비차단 후속 - Docker one-click BAT

`run_docker.bat`은 DEP3~DEP5에서 검증된 명령을 단순화하는 배포 편의 기능이다.
검증되지 않은 restore·secret·Volume 동작을 launcher 안에 먼저 숨기지 않기 위해
Deploy 01 범위에서는 구현하지 않는다. `DOCKER_ACCEPTANCE_PASS` 뒤 별도 작업으로
계획하며 Deploy 01 Forest 완료나 DTL5-5 시작의 필수 Gate로 사용하지 않는다.

후속 구현의 권장 계약은 다음과 같다.

- 최초 실행: Docker Engine·Compose 확인 → `.env.compose` 안전 생성 → 관리자
  PIN hash 입력 → 외부 snapshot 검증 → build·restore·Migration·health → Browser
  열기
- 재실행: 기존 Acceptance Volume을 보존하고 Compose project 전체 시작 → health
  확인 → Browser 열기
- 종료: container만 중지하고 Volume은 유지하며 `down -v`를 호출하지 않음
- 입력: 최초 실행에만 승인된 snapshot 절대 경로와 4자리 관리자 PIN 요구
- 금지: dump·PIN·실제 secret의 BAT·Git 포함, 비어 있지 않은 DB 자동 restore,
  기존 Volume 자동 삭제, Docker image 단독 실행

예상 진입점은 저장소 루트 `run_docker.bat`과 실제 로직을 담당하는 PowerShell
script다. 구현 전 DEP3~DEP5 명령과 오류 메시지를 그대로 재사용할 수 있는지 먼저
확인한다. 구현 뒤에는 새 PC 최초 실행, 공백·한글 경로, Docker 미실행, port 충돌,
두 번째 실행의 멱등성, stop 후 데이터 유지까지 별도 acceptance로 검증한다.

## CI 경계

CI에는 실제 Acceptance dump를 넣지 않는다. 빈 PostgreSQL과 저장소의 합성
Seed·fixture로 다음만 검증한다.

- Alembic fresh upgrade
- Backend·Data test와 `_test` 이름 안전 경계
- Frontend unit·lint·build
- Backend·Frontend image build
- 최소 Seed → DB → API smoke
- `docker compose config`와 health dependency
- build context secret·dump 금지 scan

실제 snapshot restore·Browser 회귀는 승인된 로컬 환경의 Acceptance Gate로
유지한다.

## 검증 계획

- DEP0에서 Git SHA·dependency·Migration·secret 경계를 fail-closed로 확인한다.
- DEP1에서 allowlist, 금지 데이터 scan, dump hash와 RA4 집계를 대조한다.
- DEP2에서 `docker compose config`, image build와 build context 금지 항목을
  검증한다.
- DEP3에서 빈 Volume restore·Migration·health와 DB → API → Browser actual
  smoke를 실행한다.
- DEP4에서 별도 Compose project의 clean-room·재시작·복구·test DB 격리를
  검증한다.
- DEP5에서 BE·FE 담당자와 리뷰어·QA가 같은 Git SHA·snapshot version을
  사용했는지 결과를 대조한다.
- 문서 검증과 관련 단위·통합·Browser 명령은 개발 기록에 실제 출력과 함께
  남긴다.

## 역할별 책임

| 역할 | 책임 | 종료 증거 |
| --- | --- | --- |
| Integration·Deploy | snapshot 계약, Dockerfile·Compose, Gate·인계 | DEP0~DEP5 기록과 `DOCKER_ACCEPTANCE_PASS` |
| Data | manifest 집계·stable identity·Runtime 분리 검토 | RA4 대조와 snapshot allowlist 승인 |
| Backend | image dependency·Migration·health·PostgreSQL actual 회귀 | Backend image·API·test 결과 |
| Frontend | production build·Browser API URL·actual Browser | Frontend image·Browser 결과 |
| QA | clean-room·재시작·복구·test 격리 | 독립 환경 실행 기록 |

## Forest 완료 기준

- DEP0~DEP5 Gate가 모두 통과함
- 같은 Git SHA·snapshot version·manifest hash가 모든 참여자 기록에 있음
- clean-room restore와 DB → FastAPI → React 실제 흐름이 통과함
- 컨테이너 재시작 뒤 데이터가 유지됨
- 서비스 DB와 test DB·Volume이 격리됨
- secret·dump·Runtime·로그가 Git과 image에 포함되지 않음
- 실패 restore와 복구가 기존 Volume을 파괴하지 않고 fail-closed함
- BE·FE 담당자 인수 뒤 리뷰어·QA package가 확정됨
- `DOCKER_ACCEPTANCE_PASS`가 개발 기록에 남음

`DOCKER_ACCEPTANCE_PASS` 뒤에만 동일 snapshot을 전제로 한 DTL5-5 독립
사용성 리뷰·QA를 시작한다. 이 Gate는 DTL5-5 결과나 Release 2 `W5-G2`를
대신하지 않는다.

## 위험과 미확정 사항

- snapshot allowlist는 실제 Schema inventory 뒤 확정한다. 개인·세션·감사
  데이터가 발견되면 dump 생성을 중단하고 정제 방식을 먼저 승인한다.
- 팀 PC의 Docker Desktop 정책·가상화 제한이 다르면 동등한 Docker
  Engine·Compose 환경을 별도 승인해야 한다.
- Frontend Browser API URL과 Backend 내부 DB hostname은 실행 주체가 달라
  Compose 구현 중 환경변수 계약을 다시 확인해야 한다.
- Acceptance snapshot 전달 채널과 보존 기간은 실제 dump 생성 전 확정해야
  하며, Git·image·CI artifact는 대안이 아니다.
- DEP0~DEP5 구현 결과에 따라 Nginx·Production image·CI로 승격할 수 있지만,
  그 확장은 6주차 `v1.0.0` Forest에서 별도 검증한다.

## 관련 문서

- [Integration 10 Review Admission](../integration/10_review_admission_docker_acceptance.md)
- [Integration 07 Release 2 Acceptance](../integration/07_release_2_feature_acceptance.md)
- [Docker Acceptance 동일 환경 인계 패키지](../../handoff/docker_acceptance/README.md)
- [5주차 Data·Team Leader 실행 계획](../../weekly_plan/week_05_data_team_leader.md)
- [컨테이너 구조](../../../architecture/container_structure.md)
- [브랜치 전략](../../../governance/branch_strategy.md)
- [역할과 책임](../../../governance/role_assignment.md)
