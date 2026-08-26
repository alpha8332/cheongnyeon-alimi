# Windows actual Runtime·DB 연결 환경 복구

## 문제 정보

- 발생·해결일: 2026-08-14
- 환경: Windows, PostgreSQL 18, FastAPI, React/Vite
- 영역: Team Leader 통합 실행·actual E2E·Runtime 비추적
- 관련 구현 커밋:
  `d8952a4b058e640b01e3448db4880010e2aef319`,
  `a378948`
- 관련 Gate: `W4-G3_APPROVED`, `W4-G4_MIDPOINT_PASS`

## 문제 상황

Backend·Frontend·Data 구현은 각각 테스트를 통과했지만 사용자의 기본 Windows
환경에서 실제 PostgreSQL→FastAPI→React 흐름을 안정적으로 실행할 수 없었다.
통합 과정에서 다음 문제가 확인됐다.

- 기본 애플리케이션 역할이 기존 `cheongnyeon_alimi` 테이블을 읽지 못해 검색과
  관리자 CollectionRun API가 HTTP 500을 반환
- `run_local.ps1`가 DB 이름을 고정해 권한이 있는 격리 DB를 선택할 수 없음
- 기본 DB Migration이 `20260803_0004`에 머물러 저장소 head
  `20260810_0006`과 불일치
- 사용자 PowerShell PATH에 `node.exe`가 없어 `run.bat` 시작 실패
- 실행 중 변경되는 `backend/logs/app.log`가 Git에 추적돼 worktree를 오염

각 영역의 단위 테스트 성공만으로는 이 환경 차이를 발견할 수 없었다.

## 조사와 실제 원인

### DB 존재·포트 수신과 애플리케이션 사용 가능성을 동일하게 봄

PostgreSQL 서비스와 DB가 존재해도 실행 역할의 schema·table·sequence 권한,
Migration revision, pgpass의 host·DB·role 일치는 별도 조건이다. 기존 실행기는
DB 이름을 고정해 검증된 다른 DB로 전환할 방법도 없었다.

### Node 실행 파일 탐색 범위가 PATH뿐이었음

Frontend 의존성은 존재했지만 실행기는 `Get-Command node.exe`만 사용했다.
Codex 데스크톱 번들 Node.js가 있어도 사용자 PATH에 없으면 시작 단계에서
실패했다.

### Runtime 산출물과 소스 파일의 경계가 섞임

활성 `app.log`가 Git 추적 상태여서 서버 실행만으로 작업 트리가 변경됐다.
실행 프로세스가 파일 handle을 가진 동안 branch 전환과 파일 교체도 영향을 받을
수 있는 구조였다.

## 해결 과정

### 1. 검증된 DB 선택과 pgpass 역할 확인

`run_local.ps1`에 검증된 `DatabaseName` 인자를 추가하고 기본값은 기존
`cheongnyeon_alimi`로 유지했다. pgpass에서 host `127.0.0.1|localhost|*`, port
`5432|*`, 선택 DB 이름과 일치하는 role만 사용해 비밀번호 없는 DATABASE_URL을
구성했다.

격리 actual E2E에서는 Alembic `20260810_0006`, 행정구역 538건·alias 1,080건,
canonical Seed와 저장 Runtime Raw를 적용했다. 외부 API를 다시 호출하지 않았다.

### 2. 기본 실제 DB 권한·Migration 정렬

DB 소유자 권한으로 애플리케이션 역할에 필요한 최소 schema usage, table DML,
sequence 권한을 부여하고 Migration `0005`·`0006`을 적용했다. 기존 중앙 정책
3,159건은 보존했다.

Runtime Raw·checkpoint를 먼저 dry-run한 뒤 천안 1건과 지역 정책 109건을 실제
적재했다. 동일 Raw 재실행은 모두 `unchanged`, 실패·prune 0이었다.

### 3. Node 실행 경로 보강

Node 실행 파일은 다음 순서로 찾도록 수정했다.

1. 명시한 `-NodeExecutable`
2. 사용자 PATH의 `node.exe`
3. Codex 데스크톱 번들 Node.js

어느 경로에도 없으면 설치 또는 명시 인자를 안내하며 fail-closed 처리한다.

### 4. Runtime log 비추적

추적 중인 `backend/logs/app.log`의 actual 변경은 시작 HEAD로 복원한 뒤 Git에서
제거하고 `backend/logs/`를 `.gitignore`에 추가했다. 디렉터리와 활성 파일은
Backend 시작 시 다시 생성되며 소스 이력에 포함하지 않는다.

### 5. 실제 종단 검증

`run.bat -NoBrowser -ExitAfterReady`로 Backend health 200, Frontend
`127.0.0.1:3000` 준비와 두 서비스 정상 종료를 확인했다. 이후 기본 실제 DB에서
지역 정책 검색·상세까지 Browser로 대조했다.

## 확인 결과

| 검증 | 결과 |
| --- | --- |
| DTL4-7 기존 Real API golden | 7 passed |
| DTL4-7 actual Critical Path | 3 passed |
| Frontend unit·lint·build | 162 passed·통과·통과 |
| 관련 Backend 단위·API | 65 passed |
| DTL4-8 Data 전체 | 282 passed |
| DTL4-8 Backend PostgreSQL 포함 | 187 passed |
| DTL4-8 Data PostgreSQL integration | 8 passed |
| DTL4-8 Browser | Mock 79 passed·actual 조건 14 skipped |
| Migration | 단일 head `20260810_0006` |
| Git 금지 경로·Runtime 파일 | 추적 0건 |

최종 기본 DB는 3,269건이며 중앙 정책 3,159건, 천안 1건, 지역 정책 109건을
포함했다. actual Browser에서 서울 청년 정책 검색과 공식 상세 연결을 확인했다.
Mock 실행의 actual-only 14 skip은 성공으로 세지 않고 별도 Real API 8건과 actual
Critical Path 3건으로 검증했다.

## 예방 방법

- PostgreSQL 포트·DB 존재·역할 인증·권한·Migration을 각각 확인한다.
- 실행기가 DB 이름을 고정하지 않도록 검증된 명시 인자를 제공한다.
- URL에 비밀번호를 넣지 않고 pgpass의 host·DB·role 일치를 확인한다.
- Node 등 외부 실행 파일은 PATH와 승인된 번들·명시 경로를 순서대로 탐색한다.
- 서버 실행으로 바뀌는 로그·Raw·decision 파일을 Git에서 추적하지 않는다.
- Mock Browser skip을 actual E2E 성공으로 간주하지 않는다.
- 실제 DB 적재 전 dry-run, 적재 후 동일 Raw `unchanged`를 확인한다.
- 서비스 종료와 listener 정리까지 실행기 완료 조건에 포함한다.

## 관련 근거

- [현재 컨테이너 구조](../../architecture/container_structure.md)
- `run.bat`
- `scripts/run_local.ps1`
- `.gitignore`
- `frontend/e2e/dtl4-7-actual.spec.ts`
