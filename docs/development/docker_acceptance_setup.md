# Docker Acceptance 환경 설정

## 목적

이 문서는 Backend·Frontend 담당자와 리뷰어·QA가 같은 Git 계보와 같은
PostgreSQL Acceptance snapshot을 각자의 격리 Volume에 복원하는 절차다. 실제
dump·manifest·비밀번호는 Git, Docker image, CI artifact에 포함하지 않는다.

현재 절차는 로컬 Docker Acceptance용이다. Nginx·TLS·도메인·운영 배포는
6주차 범위이며 이 문서의 결과를 운영 배포 완료로 해석하지 않는다.

> 현재 상태는 `DEP4_PASS`·`DEP5_PACKAGE_READY`이며 실제 snapshot
> restore·API·Browser·관리자 PIN·clean-room·복구·test 격리와 이식 가능한
> package 계약까지 검증했다. 담당자·리뷰어의 독립 실행 결과 수집은 남아 있다.
> `DOCKER_ACCEPTANCE_PASS` 전에는 이 문서를 대회 심사자용 최종 실행 보증으로
> 사용하지 않는다.

## 웹 UI 실행 방식 한눈에 보기

Docker image 하나를 Docker Desktop의 **Run** 버튼으로 개별 실행하는 구조가
아니다. 웹 UI는 다음 네 실행 단위를 Compose project 한 개로 함께 관리한다.

```text
Acceptance snapshot → PostgreSQL → FastAPI Backend → React Frontend
                                               ↓
                                  http://127.0.0.1:3000
```

처음 받은 PC에서는 한 번만 환경 파일과 snapshot을 준비하고 다음 명령을
실행한다.

```powershell
.\deployment\postgres\initialize_compose_env.ps1
.\deployment\postgres\restore.ps1 `
  -SnapshotDir 'C:\approved\acceptance-snapshot' `
  -StartServices
```

명령이 `DEP3_RESTORE_PASS`로 끝나고 두 health endpoint가 정상이라면 Browser에서
`http://127.0.0.1:3000`을 연다. 두 번째 실행부터는 DB를 다시 복원하지 않는다.

```powershell
docker compose --env-file .env.compose -f compose.yaml up -d --wait backend frontend
Start-Process http://127.0.0.1:3000
```

즉, BE·FE 담당자나 심사자는 최초 복원 뒤 Docker Desktop의 **Containers**에서
`cheongnyeon-alimi-acceptance` project 전체를 시작해도 된다. `database`,
`migrate`, `backend`, `frontend`를 서로 무관한 image처럼 따로 Run하지 않는다.

## 필요한 전달 패키지

다른 PC에서 같은 화면과 데이터를 재현하려면 다음 항목이 모두 같은 조합이어야
한다.

| 전달 항목 | 이유 |
| --- | --- |
| Git SHA 또는 해당 Release source | Dockerfile·Migration·API·UI 버전 고정 |
| `compose.yaml`과 Dockerfile | 전체 서비스 연결과 image 재현 |
| 외부 Acceptance dump·manifest | 동일한 3,273건 정책 데이터 복원 |
| snapshot version·SHA-256 | 전달 중 변경·잘못된 조합 차단 |
| `.env.compose.example` | 개인별 비추적 secret 작성 기준 |
| 시작·health·종료 명령 | 실행 결과와 Volume 보존 방식 통일 |

실제 `.env.compose`, DB password, 관리자 PIN, dump는 Git에 포함하지 않는다.
현재 로컬 snapshot은 Windows EFS로 암호화되어 다른 PC에서 그대로 복호화할 수
없다. DEP5의 [동일 환경 인계 패키지](handoff/docker_acceptance/README.md)에 따라
AES-256 archive와 receipt를 생성·검증하고 passphrase를 별도 채널로 전달한다.

## Docker Desktop 기준 사용자 흐름

1. Docker Desktop을 실행하고 Engine이 **Running**인지 확인한다.
2. 저장소와 승인된 snapshot package를 같은 Git SHA 조합으로 준비한다.
3. 저장소 루트 PowerShell에서 최초 restore 명령을 한 번 실행한다.
4. Docker Desktop의 **Containers**에서 project 안의 DB·Backend·Frontend가
   healthy인지 확인한다.
5. Browser에서 `http://127.0.0.1:3000`을 열어 검색·상세·추천 화면을 확인한다.
6. 사용을 마치면 project의 **Stop** 또는 문서의 `docker compose stop`을 사용한다.
7. 다음 실행에서는 project 전체를 **Start**한다. Volume에 복원된 DB가 유지된다.

Docker Desktop의 delete, reset 또는 **Delete volumes**는 정상 종료 방법이
아니다. 심사·QA 중 Volume을 새로 만들 필요가 있으면 DEP4 복구 절차에 따라
project와 Volume 이름을 먼저 확인한다.

최초 설정부터 Browser 실행까지 감싸는 `run_docker.bat`은 DEP3~DEP5 실제 절차가
확정된 뒤 구현할 비차단 후속 항목이다. 현재는 이 문서의 명시적 명령을 사용하며,
BAT가 아직 없다는 이유로 Deploy 01 Gate를 통과 처리하거나 실패 처리하지 않는다.

## 구성

| 파일·서비스 | 역할 |
| --- | --- |
| `compose.yaml` | reviewer용 고정 image·Volume·health dependency |
| `compose.dev.yaml` | 개발자용 source bind mount·hot reload override |
| `database` | host port를 공개하지 않는 PostgreSQL 18.4 서비스 DB |
| `restore` | hash가 일치할 때 빈 DB에만 복원하는 one-shot profile |
| `migrate` | 복원 baseline을 확인한 뒤 Alembic head 적용 |
| `backend` | non-root FastAPI, 실제 DB, `/health` |
| `frontend` | non-root 정적 React build, `/health` |
| `database-test` | 이름이 `_test`로 끝나는 별도 test profile·Volume |

서비스 DB는 외부 통신이 차단된 내부 DB network에만 연결하고 Backend가 app
network와 DB network를 잇는다. Frontend와 Backend의 host 공개 port는
기본값도 `127.0.0.1`에만 bind한다.

Acceptance Frontend는 반드시 `VITE_USE_MOCK=false`로 build한다. 이 값이 빠지면
API에 실제 정책이 있어도 UI가 bundled Mock 데이터만 조회할 수 있으므로
`compose.yaml`이 기본값을 false로 전달하고 Dockerfile이 다른 값을 거부한다.

## 1. 환경 파일 준비

Windows에서는 저장소 루트의 PowerShell에서 다음 초기화기를 실행하는 방법을
권장한다. 관리자 PIN은 보안 프롬프트로만 입력하며 나머지 secret은 서로 다른
64자리 난수로 생성한다. 기존 파일은 덮어쓰지 않는다.

```powershell
.\deployment\postgres\initialize_compose_env.ps1
```

초기화기는 PIN 평문을 저장하지 않고 `.env.compose`에 SHA-256 hash만 기록한다.
생성 파일의 ACL은 현재 Windows 사용자만 접근하도록 상속을 제거하고 Git ignore
여부까지 확인한다.

직접 설정해야 할 때만 example을 복사한다.

```powershell
Copy-Item .env.compose.example .env.compose
```

`.env.compose`는 Git에서 제외된다. 모든 `CHANGE_ME`를 교체한다. Compose가 DB
URL을 조립하므로 DB password는 32자리 이상의 URL-safe 문자만 허용한다. 아래
64자리 hex 생성값을 사용하면 이 계약을 충족한다.

```powershell
[Convert]::ToHexString(
  [Security.Cryptography.RandomNumberGenerator]::GetBytes(32)
).ToLower()
```

위 명령을 각각 새로 실행해 서비스 DB password, test DB password,
`BACKEND_SECRET_KEY`, `ADMIN_TOKEN_SECRET`에 서로 다른 값을 넣는다. 4자리 관리자
PIN 자체를 저장하지 않고 SHA-256만 넣는다.

```powershell
$AdminPin = Read-Host '4자리 관리자 PIN'
if ($AdminPin -notmatch '^\d{4}$') { throw 'PIN은 숫자 4자리여야 합니다.' }
[Convert]::ToHexString(
  [Security.Cryptography.SHA256]::HashData(
    [Text.Encoding]::UTF8.GetBytes($AdminPin)
  )
).ToLower()
$AdminPin = $null
```

출력된 hash를 `ADMIN_PIN_HASH`에 넣는다. 실제 snapshot 경로와 dump hash는
`restore.ps1`이 검증 후 현재 process에만 주입하므로 example의 해당 placeholder를
실제 값으로 Git에 기록하지 않는다.

관리자 수동 수집에서 온통청년 또는 복지로 API Source를 사용할 때만 이 비추적
파일의 `YOUTHCENTER_API_KEY` 또는 `BOKJIRO_API_KEY`를 채운다. 키가 없으면 공개
웹 Source만 선택한다. API key를 저장소·image·receipt에 넣지 않으며, 키가 필요한
Source의 실패도 CollectionRun `failed`로 종결된다.

## 2. Compose 계약 확인

```powershell
docker compose --env-file .env.compose -f compose.yaml config --quiet
docker compose --env-file .env.compose -f compose.yaml config --profiles
docker compose --env-file .env.compose -f compose.yaml -f compose.dev.yaml config --quiet
```

정상 profile 출력은 `restore`, `test` 두 개다. 환경변수가 비었으면 `config`가
실패한다. `restore.ps1`은 `CHANGE_ME`, `_test` suffix 누락, 서비스·test DB의 같은
password도 추가로 차단한다.

## 3. 최초 snapshot 검증·복원·기동

승인된 암호화 채널에서 받은 snapshot 디렉터리는 workspace 밖에 둔다. 디렉터리
안에는 다음 두 파일이 있어야 한다.

```text
acceptance-post-admission.dump
acceptance-snapshot.manifest.json
```

검증만 할 때는 다음을 실행한다.

```powershell
.\.venv\Scripts\python.exe deployment\postgres\verify_snapshot.py `
  --snapshot-dir 'C:\approved\acceptance-snapshot' `
  --repository-root .
```

검증기는 canonical manifest hash, dump size·hash, allowlist 7개 table, blocker
scan, Policy 3,273건, CollectionRun 61건, stable identity 3건과 snapshot Git SHA의
현재 checkout ancestor 여부를 확인한다.

최초 실행은 build → DB health → 빈 DB restore → 복원 baseline 확인 → Migration →
Backend health → Frontend health 순서로 진행한다.

```powershell
.\deployment\postgres\restore.ps1 `
  -SnapshotDir 'C:\approved\acceptance-snapshot' `
  -StartServices
```

이미 같은 Dockerfile과 build argument로 image를 검증한 경우에만 `-SkipBuild`를
사용한다. restore가 hash 불일치 또는 비어 있지 않은 DB를 만나면 실패하며 기존
Volume을 drop·reset하지 않는다.

## 4. 일상 실행·확인·종료

최초 복원 뒤 reviewer 환경을 다시 시작한다.

```powershell
docker compose --env-file .env.compose -f compose.yaml up -d --wait backend frontend
```

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:3000/health
docker compose --env-file .env.compose -f compose.yaml ps
```

기본 Browser URL은 `http://127.0.0.1:3000`이다. 로그 확인 시 환경변수 전체를
출력하는 명령은 사용하지 않는다.

```powershell
docker compose --env-file .env.compose -f compose.yaml logs --tail 100 backend frontend
```

Volume을 유지한 정상 종료는 다음 명령이다.

```powershell
docker compose --env-file .env.compose -f compose.yaml stop
```

`docker compose down -v`는 서비스 DB와 test DB Volume을 삭제하므로 일반 종료
명령으로 사용하지 않는다. reset이나 복구는 DEP4에서 실제 project·Volume 이름을
먼저 확인한 뒤 별도 승인 절차로 수행한다.

## 5. 개발 override

hot reload가 필요할 때만 두 Compose 파일을 함께 사용한다.

```powershell
docker compose --env-file .env.compose `
  -f compose.yaml -f compose.dev.yaml `
  up -d --wait backend frontend
```

이 override는 Backend·Frontend source와 공개 데이터 reference·schema·seed만
bind mount한다. reviewer 결과는 source 변경이 섞이지 않는 `compose.yaml`만으로
재현한다. 개발 override에서만 PostgreSQL이 기본
`127.0.0.1:55432`로 임시 공개된다.

## 6. Test DB profile

test DB는 서비스 DB와 다른 이름·password·Volume·network를 사용한다.

```powershell
docker compose --env-file .env.compose -f compose.yaml `
  --profile test up -d --wait database-test
```

`TEST_POSTGRES_DB`가 `_test`로 끝나지 않으면 container가 fail-closed한다. DEP4
test 종료 전후에는 서비스 DB Policy 수와 서비스 Volume이 바뀌지 않았는지 다시
확인한다.

## 7. 별도 project clean-room·복구 확인

같은 PC에서 기존 reviewer 환경을 유지한 채 clean-room을 재현할 때는 project,
image tag, Backend·Frontend host port를 모두 분리한다. Frontend build에는 새
Backend host port가 들어가므로 image tag를 공유하면 안 된다.

```powershell
$env:COMPOSE_PROJECT_NAME = 'cheongnyeon-alimi-cleanroom'
$env:ACCEPTANCE_IMAGE_TAG = "cleanroom-$(git rev-parse --short HEAD)"
$env:BACKEND_HOST_PORT = '18000'
$env:FRONTEND_HOST_PORT = '13000'
$env:VITE_API_BASE_URL = 'http://127.0.0.1:18000'
$env:CORS_ORIGINS = '["http://127.0.0.1:13000","http://localhost:13000"]'

.\deployment\postgres\restore.ps1 `
  -SnapshotDir 'C:\approved\acceptance-snapshot' `
  -StartServices
```

복원 뒤 `http://127.0.0.1:18000/health`와
`http://127.0.0.1:13000`을 확인한다. 전체 재시작 전후에는 Policy·CollectionRun
count와 stable identity를 대조한다.

DB 중단 복구는 clean-room project에서만 연습한다. 정상 reviewer project나
서비스 Volume에는 실패를 주입하지 않는다.

```powershell
docker compose --env-file .env.compose -f compose.yaml stop database
curl.exe --max-time 15 http://127.0.0.1:18000/health
docker compose --env-file .env.compose -f compose.yaml `
  up -d --wait database backend frontend
```

중단 중 health는 성공하면 안 되며, 복구 뒤 `status=ok`와 기존 count가 돌아와야
한다. hash 실패 restore도 기존 Volume을 자동 삭제하거나 재복원하지 않고 count
불변을 먼저 확인한다.

test profile을 검증한 뒤에는 container만 stop하고 두 DB Volume 이름이 다른지
기록한다.

```powershell
docker compose --env-file .env.compose -f compose.yaml `
  --profile test up -d --wait database-test
docker compose --env-file .env.compose -f compose.yaml `
  --profile test stop database-test
docker volume ls --format '{{.Name}}'
```

clean-room 종료도 Volume을 보존하는 `stop`을 사용한다. Volume 삭제가 필요한
경우 project와 `acceptance-db`·`acceptance-test-db`의 정확한 이름을 먼저 출력하고
별도 확인을 받은 뒤 수행한다. 이 문서에서는 자동 삭제 명령을 제공하지 않는다.

## 문제 해결

- `snapshot Git SHA is not an ancestor`: 다른 branch 또는 승인되지 않은
  snapshot 조합이다. 임의로 우회하지 말고 Git SHA와 전달 package를 다시 맞춘다.
- `target database is not empty`: 자동 재복원하지 않는다. 기존 project·Volume을
  보존하고 새 Compose project 또는 DEP4 복구 절차를 사용한다.
- `Policy baseline count mismatch`: dump와 manifest 조합 또는 복원 대상이 다르다.
- Frontend에서 API 연결 실패: `VITE_API_BASE_URL`은 Browser가 접근할 수 있는
  `127.0.0.1` URL이어야 하며 Compose service명 `backend`를 넣지 않는다.
- port 충돌: `.env.compose`의 host port만 바꾸고 `VITE_API_BASE_URL`과
  `CORS_ORIGINS`도 같은 값으로 맞춘 뒤 Frontend image를 다시 build한다.

## 금지 사항

- dump·manifest·Runtime archive·`.env.compose`를 Git에 추가하거나 image에 복사
- DB port를 `0.0.0.0` 또는 외부 interface에 공개
- hash 검사 우회, 기존 Volume 자동 삭제, 비어 있지 않은 DB에 restore
- service DB를 Backend test의 정리 대상으로 사용
- container inspect·환경변수 전체 출력 결과를 팀 채널에 공유
