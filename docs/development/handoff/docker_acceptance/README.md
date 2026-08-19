# Docker Acceptance 동일 환경 인계 패키지

## 목적과 현재 Gate

이 문서는 Backend·Frontend 담당자와 사용성 리뷰어·QA가 동일 Git SHA와 동일
PostgreSQL snapshot을 각자 격리된 Docker Volume에 복원하고 결과를 같은 형식으로
회신하기 위한 DEP5 인계 계약이다.

인계 문서와 암호화 도구가 준비됐다는 사실만으로 `DEP5_PASS` 또는
`DOCKER_ACCEPTANCE_PASS`가 되지 않는다. 최종 handoff commit 뒤 생성한 receipt와
각 역할의 독립 실행 기록에서 Git SHA·snapshot version·dump hash가 모두 일치해야
Gate를 닫는다.

## 고정 데이터 계약

| 항목 | 승인 값 |
| --- | --- |
| snapshot version | `acceptance-20260819-75510a9` |
| snapshot Git SHA | `75510a92d5f566e34c1ff92e7d97b65d88e8b178` |
| dump SHA-256 | `46810a6ac6082680d2fae17ab98721597ec4b5e23ec667b3d086b5a4e9739a8b` |
| manifest 계약 SHA-256 | `551136bab08bf8db45935a07a7fb8a2056acf6b1b6bc01ba117eea6331513122` |
| manifest file SHA-256 | `42394556feba9b4d0058bde495f28a808fbcb302660abc30838ec11dde455299` |
| Alembic revision | `20260810_0006` |
| Policy / CollectionRun | `3273` / `61` |

최종 Git SHA는 이 문서를 포함한 DEP5 commit 뒤 receipt에서 확정한다. 위 snapshot
Git SHA는 데이터 생성 lineage이며 실행 checkout SHA를 대신하지 않는다.

## 전달물

다음 항목을 한 release 단위로 전달한다.

1. receipt의 정확한 Git SHA를 checkout할 수 있는 저장소 접근 경로
2. AES-256·header encryption을 적용한 `.7z` snapshot package
3. archive hash와 Git·snapshot 계약을 담은 `.receipt.json`
4. [Docker Acceptance 환경 설정](../../docker_acceptance_setup.md)
5. [역할별 실행 결과 양식](acceptance_result_template.md)
6. [결함·재검증 양식](defect_report_template.md)

`.7z`와 receipt는 승인된 파일 전달 채널로 보내고 passphrase는 별도 채널로
전달한다. 저장소, Issue, PR, 팀 채팅, receipt에 passphrase·PIN·DB password를
기록하지 않는다. 각 참여자는 `.env.compose`와 관리자 PIN을 자기 PC에서 새로
생성하며 서로 공유하지 않는다.

## Integration·Deploy 패키지 생성

7-Zip 26.x console과 깨끗한 최종 handoff checkout에서 실행한다. 시스템 설치가
어려운 PC는 공식 `7zr.exe`를
`%LOCALAPPDATA%\cheongnyeon-alimi\tools\7zip-portable\7zr.exe`에 둘 수 있다.
출력 경로는 workspace 밖이어야 한다. 7-Zip이 archive 생성 시 passphrase를 한
번 요청하고, archive 검증 시 같은 passphrase를 다시 요청한다.
PowerShell script는 passphrase를 읽거나 저장하지 않는다.

```powershell
.\deployment\postgres\create_acceptance_transfer_package.ps1 `
  -SnapshotDir 'C:\approved\acceptance-snapshot' `
  -OutputDir 'C:\approved\handoff-output'
```

정상 결과는 `DEP5_TRANSFER_PACKAGE_CREATED`다. 생성된 archive와 receipt의
`archive_sha256`을 대조한 뒤에만 전달한다. EFS 원본 snapshot은 이 package를
대체해 다른 PC로 직접 복사하지 않는다.

## 수신자 공통 실행 순서

1. receipt의 `git_sha`를 checkout하고 `git status --short`가 비었는지 확인한다.
2. `.7z`의 SHA-256을 receipt와 대조한다.
3. 7-Zip에서 `-p`를 붙이지 않고 workspace 밖 새 디렉터리에 압축을 해제한다.
   encrypted header를 읽을 때 나타나는 대화형 prompt에 passphrase를 입력한다.
4. `initialize_compose_env.ps1`로 개인 secret과 PIN hash를 생성한다.
5. `restore.ps1 -StartServices`를 실행하고 `DEP3_RESTORE_PASS`를 확인한다.
6. DB 3,273·61, Migration revision, Backend·Frontend health를 확인한다.
7. 역할별 시나리오를 수행하고 실행 결과 양식을 회신한다.
8. 정상 종료는 `docker compose stop`을 사용하고 Volume을 보존한다.

```powershell
git checkout <receipt.git_sha>
git status --short
Get-FileHash 'C:\received\package.7z' -Algorithm SHA256
7z.exe x -o'C:\received\acceptance-snapshot' 'C:\received\package.7z'
.\deployment\postgres\initialize_compose_env.ps1
.\deployment\postgres\restore.ps1 `
  -SnapshotDir 'C:\received\acceptance-snapshot' `
  -StartServices
```

기존 `.env.compose`나 동일 project Volume이 있으면 자동 덮어쓰기·복원을 하지
않는다. 각 수신자는 서로 다른 Compose project와 Volume을 사용한다.

## 역할별 확인 범위

### Backend

- Migration baseline·head와 restart 뒤 Policy 3,273·Run 61 유지
- health, 검색·상세·추천 actual API
- PIN session 200, 무토큰 401, 권한·rate limit 경계
- CollectionRun 목록·상세·수동 실행·stale
- 읽기 전용 관리자 Policy와 구조화 log 조회·삭제 감사 경계
- 실행한 Backend unit·PostgreSQL·보안·성능 명령의 pass·skip·fail 분리

서비스 DB는 테스트 정리 대상으로 사용하지 않는다. PostgreSQL 회귀는 `_test`
전용 DB와 별도 Volume에서만 수행한다.

### Frontend

- `VITE_USE_MOCK=false` actual 검색·상세·추천
- 핵심 신청 조건·공식 원문·partial·unknown 표시
- 즐겨찾기·D-Day·알림·`.ics`
- PIN 로그인·만료·로그아웃·보호 route
- 관리자 Policy·CollectionRun·log UI
- unit·lint·build·Mock·actual Browser·접근성·모바일 결과 분리

### 사용성 리뷰어

- 자연어 검색과 결과 조건 이해 가능성
- 추천 이유·미확정·빈 결과·비단정 안내
- 상세 원문 이동, 즐겨찾기·달력·알림 흐름
- 관리자 화면에서 오해하기 쉬운 용어와 오류 복구

### QA

- 기능·통합·회귀·경계·권한·실패 흐름
- partial·null·지역·연령·마감 데이터
- Browser 접근성·반응형과 주요 지원 환경
- clean-room 설치·재시작·Volume·test DB 격리·복구

## DTL5-5 시작 승인 기준

다음 네 역할 receipt가 모두 같은 Git SHA·snapshot version·dump hash를 가져야
한다.

- Backend 담당자: environment identity와 actual API 결과
- Frontend 담당자: environment identity와 actual Browser 결과
- 사용성 리뷰어: 독립 시나리오 관찰 기록
- QA 담당자: clean-room·회귀·결함 기록

불일치·미실행·skip은 통과로 합치지 않는다. blocker나 승인되지 않은 high 결함,
secret 노출, 데이터 손실, Migration·restore 실패가 있으면
`DOCKER_ACCEPTANCE_BLOCKED`다. 모든 receipt와 package hash가 일치하고 DEP0~DEP4
근거가 유지될 때만 Integration·Deploy가 `DEP5_PASS`와
`DOCKER_ACCEPTANCE_PASS`를 기록하고 DTL5-5를 연다.

## 금지 사항

- dump·manifest·archive·receipt의 passphrase를 Git·image·CI artifact에 포함
- archive와 passphrase를 같은 채널로 전송
- EFS 원본을 이식 가능한 package로 간주
- host PostgreSQL 공개, service DB 대상 테스트·임의 수정
- 다른 참여자의 `.env.compose`, PIN, Volume 공유
- `down -v`, Docker Desktop volume delete를 일반 종료로 사용
- 미실행·skip·Mock 결과를 actual 통과로 기록
