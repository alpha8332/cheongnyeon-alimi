# Windows PostgreSQL 테스트 환경 복구

## 문제 정보

- 발생일: 2026-07-29~2026-07-30
- 환경: Windows, Python 3.11.9, PostgreSQL 18
- 영역: Backend 로컬 개발·PostgreSQL 통합 테스트

## 증상

다른 데스크톱에서 작업하던 저장소를 Windows 환경에서 이어받았을 때 Backend와
PostgreSQL 통합 테스트를 바로 실행할 수 없었다.

1. 저장소의 기존 `venv`에는 `bin/`만 있고
   `venv\Scripts\python.exe`가 없어 Windows에서 실행할 수 없었다.
2. 전역 Python은 실행됐지만 `pytest`, SQLAlchemy와 Backend 의존성이 없었다.
3. `127.0.0.1:5432`는 열려 있었지만 `TEST_DATABASE_URL`과 로컬 `.env`가
   없었고, `.env.example`의 예시 계정으로는 인증되지 않았다.
4. 새로 준비한 PostgreSQL 역할도 처음에는 password authentication에
   실패했다.
5. 역할 확인용 `SELECT`를 PowerShell 프롬프트에 직접 입력하자 PowerShell
   parser 오류가 발생했다. 이는 PostgreSQL 오류가 아니라 SQL을 잘못된
   실행기에서 실행한 결과였다.
6. `TEST_DATABASE_URL`이 없을 때 Backend 테스트는 PostgreSQL 테스트 5건을
   skip하므로, 일반 테스트 성공만으로 실제 DB 검증을 완료했다고 볼 수
   없었다.

## 실제 원인

### Python 가상환경은 데스크톱과 운영체제 사이에서 이식되지 않는다

기존 `venv`는 Unix 디렉터리 구조였다. 가상환경에는 Python 실행 파일 경로와
플랫폼별 바이너리가 들어가므로 저장소를 다른 PC로 옮긴 뒤 그대로 재사용할 수
없다. Windows용 `.venv`를 현재 Python으로 다시 만들어야 했다.

### 포트 수신과 테스트 DB 사용 가능 여부는 다른 상태다

`5432` 포트가 열려 있고 PostgreSQL 서비스가 실행 중이어도 다음 항목은 별도로
확인해야 한다.

- 접속할 PostgreSQL 역할이 존재하고 `LOGIN` 가능한가
- 입력한 비밀번호가 그 역할의 현재 비밀번호와 일치하는가
- 역할에 테스트 DB를 만들 `CREATEDB` 권한이 있는가
- `_test`로 끝나는 전용 DB가 존재하는가
- 테스트 프로세스에 `TEST_DATABASE_URL`이 명시됐는가

이번 환경은 PostgreSQL 18 서비스는 실행 중이었지만 테스트 역할의 인증 상태와
전용 DB가 준비되지 않았다. `.env.example`의 계정과 비밀번호는 안전한 예시일
뿐 로컬 설치의 실제 자격증명이 아니다.

### SQL과 PowerShell 명령의 실행 경계가 혼동됐다

`SELECT ... FROM pg_roles`는 SQL이므로 `psql` 세션 또는 pgAdmin Query Tool에서
실행해야 한다. PowerShell은 이를 PostgreSQL에 전달하지 않고 자체 문법으로
해석한다.

## 해결 방법

정상 구축 절차 전체는
[Backend Windows 로컬 환경](../../development/backend_local_setup.md)을
따른다. 이번 문제는 다음 순서로 해결했다.

### 1. Windows 가상환경 재생성

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --disable-pip-version-check `
  -r backend\requirements.txt
```

PostgreSQL 설정 전 Backend 전체 테스트를 실행해 Python 환경과 SQLite 단위
경계를 먼저 확인했다.

```powershell
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q
```

이 단계에서는 46건이 통과하고 `TEST_DATABASE_URL`이 필요한 5건이 skip됐다.

### 2. PostgreSQL 역할을 서버 안에서 확인

PostgreSQL 관리자 역할로 `psql`에 접속한 뒤 SQL을 실행했다.

```powershell
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' `
  -h 127.0.0.1 -p 5432 -U postgres -d postgres -W
```

```sql
SELECT rolname, rolcanlogin, rolcreatedb
FROM pg_roles
WHERE rolname = '<test-role>';
```

필요한 역할 속성을 설정하고 `psql`의 `\password <test-role>`로 비밀번호를
다시 지정했다. 비밀번호를 SQL literal이나 shell history에 넣지 않았다.

```sql
ALTER ROLE "<test-role>" WITH LOGIN CREATEDB;
\password <test-role>
```

관리자 세션을 닫은 뒤 테스트 역할로 직접 인증되는지 확인했다.

```powershell
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' `
  -h 127.0.0.1 -p 5432 -U <test-role> -d postgres -W `
  -c 'SELECT current_user;'
```

### 3. 전용 테스트 DB와 안전한 인증 경계 준비

테스트 DB는 애플리케이션 DB와 분리하고 이름을 `_test`로 끝냈다. Backend
PostgreSQL 테스트도 이 접미사를 강제한다.

```powershell
& 'C:\Program Files\PostgreSQL\18\bin\createdb.exe' `
  -h 127.0.0.1 -p 5432 -U <test-role> `
  -T template0 -E UTF8 cheongnyeon_alimi_test -W
```

자동 테스트에는 URL에 비밀번호를 넣지 않고 임시 `pgpass`와 비밀번호 없는
`TEST_DATABASE_URL`을 사용했다. `pgpass`를 만들 때 `:`와 `\`를 escape하고
UTF-8 BOM 없이 저장했으며 현재 Windows 사용자만 읽고 쓸 수 있게 했다.

### 4. PostgreSQL 전체 테스트 실행

```powershell
$env:PGPASSFILE = '<temporary-pgpass-path>'
$env:TEST_DATABASE_URL = `
  'postgresql+psycopg2://<test-role>@127.0.0.1:5432/cheongnyeon_alimi_test'

try {
  .\.venv\Scripts\python.exe -B -m pytest backend/tests -q
} finally {
  Remove-Item Env:TEST_DATABASE_URL -ErrorAction SilentlyContinue
  Remove-Item Env:PGPASSFILE -ErrorAction SilentlyContinue
}
```

검증 후 임시 credential과 `pgpass` 파일을 삭제했다.

## 확인 결과

- Windows `.venv`에서 Backend 의존성 import 성공
- PostgreSQL 미설정 Backend 회귀: 46건 통과, 5건 skip
- 테스트 역할의 직접 `psql` 인증 성공
- `cheongnyeon_alimi_test` 생성 성공
- 실제 PostgreSQL Backend 전체 회귀: 51건 통과
- Alembic upgrade·downgrade 성공
- JSONB·enum·timezone 왕복, upsert, transaction rollback 성공
- canonical Seed → PostgreSQL → Repository → Policy API 종단 검증 성공
- 테스트 종료 후 Policy 테이블과 enum 제거 확인
- 빈 `alembic_version` 테이블만 남아 다음 Migration에 재사용 가능
- 임시 credential·`pgpass` 파일 삭제 확인

## 예방 방법

- `venv`나 `.venv`를 다른 PC 또는 운영체제에서 복사해 재사용하지 않는다.
- 새 환경에서는 저장소 manifest인 `backend/requirements.txt`로 가상환경을
  다시 만든다.
- `pg_isready` 또는 열린 포트만으로 DB 준비 완료를 판단하지 않는다.
- `psql` 직접 인증, 역할 속성, 테스트 DB와 `TEST_DATABASE_URL`을 각각
  확인한다.
- `.env.example`의 예시 비밀번호를 실제 로컬 비밀번호로 가정하지 않는다.
- SQL은 `psql` 또는 Query Tool에서 실행하고 PowerShell에 직접 입력하지
  않는다.
- PostgreSQL 테스트 skip을 성공으로 기록하지 않는다.
- 테스트 DB 이름은 `_test`로 끝내고 운영·개발 DB를 대상으로 실행하지
  않는다.
- 비밀번호를 코드, 문서, shell history와 출력에 남기지 않는다.
- 임시 인증 파일은 테스트 성공·실패와 관계없이 제거한다.
