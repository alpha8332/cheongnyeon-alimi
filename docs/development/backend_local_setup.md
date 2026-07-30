# Backend Windows 로컬 환경

## 목적

Windows에서 Backend 단위 테스트와 PostgreSQL 통합 테스트를 재현하는 현재
절차를 정의한다. 실제 장애 원인과 복구 과정은
[Windows PostgreSQL 테스트 환경 복구](../troubleshooting/backend/windows_postgresql_test_environment.md)에서
확인한다.

## 전제 조건

- 저장소 루트에서 명령을 실행한다.
- Windows에서 실행 가능한 Python이 있다.
- PostgreSQL 서버와 client 도구 `psql`, `createdb`, `pg_isready`가 있다.
- PostgreSQL 테스트 역할은 `LOGIN`과 `CREATEDB` 권한을 가진다.
- 애플리케이션 DB와 분리된 `_test` 접미사 DB만 통합 테스트에 사용한다.

PostgreSQL 설치 버전이나 경로가 다르면 아래 `$pgBin`만 실제 경로로 바꾼다.

```powershell
$pgBin = 'C:\Program Files\PostgreSQL\18\bin'
```

## Python 환경 구축

기존 `venv`가 다른 PC나 Unix에서 만들어졌다면 재사용하지 않는다. 저장소
루트에 Git ignore 대상인 Windows `.venv`를 만든다.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --disable-pip-version-check `
  -r backend\requirements.txt
```

의존성 파일을 바꾸지 않고 로컬에만 추가 설치하지 않는다.

## PostgreSQL 없이 Backend 확인

```powershell
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q
```

`TEST_DATABASE_URL`이 없으면 PostgreSQL 테스트는 skip된다. 이 결과는 SQLite
단위·API 경계의 성공이며 실제 PostgreSQL 성공을 의미하지 않는다.

## PostgreSQL 상태와 역할 확인

```powershell
& "$pgBin\pg_isready.exe" -h 127.0.0.1 -p 5432

& "$pgBin\psql.exe" `
  -h 127.0.0.1 -p 5432 -U <test-role> -d postgres -W `
  -c 'SELECT current_user;'
```

포트가 열려 있어도 두 번째 직접 인증이 실패하면 역할·비밀번호를 관리자
`psql` 또는 pgAdmin에서 먼저 수정한다. `.env.example`의 계정과 비밀번호는
실제 로컬 자격증명이 아니다.

## 테스트 DB 생성

`TEST_DATABASE_URL`은 `_test`로 끝나는 DB만 허용한다.

```powershell
& "$pgBin\createdb.exe" `
  -h 127.0.0.1 -p 5432 -U <test-role> `
  -T template0 -E UTF8 cheongnyeon_alimi_test -W
```

이미 존재한다는 오류가 나오면 새로 삭제하거나 덮어쓰지 말고 해당 DB가 이
저장소 전용 테스트 DB인지 확인한다.

## 비밀번호를 URL에 넣지 않고 전체 테스트 실행

PowerShell session 안에서만 임시 `pgpass`를 만들고 현재 사용자 ACL을
적용한다. `<test-role>`은 실제 PostgreSQL 역할명으로 바꾼다.

```powershell
$credential = Get-Credential -UserName '<test-role>' `
  -Message 'PostgreSQL test password'
$credentialValue = $credential.GetNetworkCredential().Password
$credentialValue = `
  $credentialValue.Replace('\', '\\').Replace(':', '\:')

$pgpassPath = Join-Path $env:TEMP 'cheongnyeon-alimi-pgpass.conf'
$pgpassLine = `
  "127.0.0.1:5432:*:$($credential.UserName):$credentialValue"
[IO.File]::WriteAllText(
  $pgpassPath,
  $pgpassLine + [Environment]::NewLine,
  [Text.UTF8Encoding]::new($false)
)
icacls $pgpassPath /inheritance:r /grant:r "${env:USERNAME}:(R,W)"

$env:PGPASSFILE = $pgpassPath
$env:TEST_DATABASE_URL = `
  "postgresql+psycopg2://$($credential.UserName)@127.0.0.1:5432/cheongnyeon_alimi_test"

try {
  .\.venv\Scripts\python.exe -B -m pytest backend/tests -q
} finally {
  Remove-Item Env:TEST_DATABASE_URL -ErrorAction SilentlyContinue
  Remove-Item Env:PGPASSFILE -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $pgpassPath -Force -ErrorAction SilentlyContinue
  $credential = $null
  $credentialValue = $null
}
```

테스트는 실제 Alembic Migration을 적용하고 종료 시 `base`로 downgrade한다.
빈 `alembic_version` 테이블은 남을 수 있다.

## 안전 수칙

- 실제 비밀번호를 `.env.example`, 문서, 명령 예시와 Git 추적 파일에 넣지
  않는다.
- `DATABASE_URL`과 `TEST_DATABASE_URL`의 대상 DB를 혼동하지 않는다.
- `_test`로 끝나지 않는 URL에서 PostgreSQL 통합 테스트를 실행하지 않는다.
- 연결 실패를 SQLite 성공으로 대체하지 않는다.
- 테스트 종료 후 session 환경변수와 임시 `pgpass`를 제거한다.
