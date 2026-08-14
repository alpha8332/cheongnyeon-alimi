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

## SQL statement 진단

Backend SQL logging은 환경 이름과 분리돼 있으며 기본적으로 꺼져 있다.
`ENVIRONMENT=development`만으로 SQL statement가 출력되지 않는다.

일시적으로 statement를 확인해야 할 때만 로컬 `.env` 또는 현재 process에
다음을 명시한다.

```powershell
$env:SQL_ECHO = 'true'
```

`SQL_ECHO=true`여도 SQLAlchemy bound parameter는 항상 숨긴다. 정책 본문,
provenance, API key, DB password와 URL credential은 로그에 출력하지 않는다.
미처리 Backend 예외도 상세 문자열이나 traceback 대신 예외 타입만 기록한다.
설정은 process 시작 시 읽으므로 실행 중인 Backend·Seed·Runtime importer를
재시작해야 반영된다. 진단 후에는 변수를 제거한다.

```powershell
Remove-Item Env:SQL_ECHO -ErrorAction SilentlyContinue
```

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

## 관리자 PIN 설정 및 해시 생성 (Backend 04)

`development`, `local`, `test` 환경에서는 별도 설정이 없고 실제 요청 client가
loopback일 경우에만 기본 PIN `0000`을 사용한다.
프로덕션 배포 또는 커스텀 PIN을 사용하려면 4자리 숫자 PIN의 SHA-256 해시를 생성하여 `.env`에 설정한다.

1. **PowerShell에서 4자리 PIN 해시 생성**:
   ```powershell
   .\.venv\Scripts\python.exe -c "import hashlib; print(hashlib.sha256(b'1234').hexdigest())"
   ```
2. **`.env` 파일 설정 및 교체**:
   ```env
   ADMIN_PIN_HASH=03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4
   ADMIN_TOKEN_SECRET=your-production-admin-token-secret
   ADMIN_SESSION_EXPIRE_MINUTES=60
   ```
3. **전체 서명 토큰 일괄 폐기**:
   - production은 `ADMIN_TOKEN_SECRET`이 필수이며 `SECRET_KEY`로 fallback하지 않는다.
   - 사용 중인 `ADMIN_TOKEN_SECRET`을 교체하면 기존 관리자 세션 토큰이 즉시
     서버 검증에서 무효화된다.

## 안전 수칙

- 실제 비밀번호를 `.env.example`, 문서, 명령 예시와 Git 추적 파일에 넣지
  않는다.
- `DATABASE_URL`과 `TEST_DATABASE_URL`의 대상 DB를 혼동하지 않는다.
- `_test`로 끝나지 않는 URL에서 PostgreSQL 통합 테스트를 실행하지 않는다.
- 연결 실패를 SQLite 성공으로 대체하지 않는다.
- 테스트 종료 후 session 환경변수와 임시 `pgpass`를 제거한다.
