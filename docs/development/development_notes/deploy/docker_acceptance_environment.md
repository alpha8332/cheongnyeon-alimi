# Deploy 01 Docker Acceptance Environment 개발 기록

## 작업 정보

- 상태: in-progress
- 실행 판정: `DEP0_PASS`·`DEP1_PASS`·`DEP2_PASS`·`DEP3_PASS`·`DEP4_PASS`
  (`DOCKER_ACCEPTANCE_PENDING`)
- 기록 시작일: `2026-08-19`
- DEP1 preflight일: `2026-08-20`
- DEP1 완료일: `2026-08-20`
- DEP2 완료일: `2026-08-20`
- DEP3 시작일: `2026-08-20`
- DEP3 완료일: `2026-08-20`
- DEP4 시작일: `2026-08-20`
- DEP4 완료일: `2026-08-20`
- DEP5 시작일: `2026-08-20`
- 담당 영역: Team Leader - Integration·Deploy
- 현재 브랜치: `feature/deploy/docker-acceptance-environment`
- DEP0 기준 Git SHA: `9d6475d49275a06704ec82651bb9d1fcdcbfd478`
- DEP1 snapshot Git SHA: `75510a92d5f566e34c1ff92e7d97b65d88e8b178`
- 선행 Gate: Integration 10 `REVIEW_ADMISSION_PASS`
- 계획: [Deploy 01 Docker Acceptance Environment](../../develop_plan/deploy/01_docker_acceptance_environment.md)
- 후속 단계: Integration 07 DTL5-5 독립 사용성 리뷰·QA

## 목적

Integration 10이 확정한 동일 DB snapshot을 Backend·Frontend 담당자와
리뷰어·QA가 각자 격리된 Docker Volume으로 재현한 실제 구현·검증 결과를
누적한다. 계획된 명령이나 기대 결과를 실행 결과로 기록하지 않는다.

## Forest 범위

- DEP0 입력·환경·비밀 경계 고정
- DEP1 snapshot allowlist·dump·manifest·hash
- DEP2 Dockerfile·Compose 구현
- DEP3 restore·Migration·health·actual smoke
- DEP4 clean-room·Volume·복구·test DB 격리
- DEP5 BE·FE·리뷰어·QA 동일 환경 인계

## Slice 진행 현황

| Slice | 상태 | 실제 결과 |
| --- | --- | --- |
| DEP0 | completed | Git·Docker·dependency·Migration·secret·보관 경로·port 기준선 확인, `DEP0_PASS` |
| DEP1 | completed | allowlist·민감정보 scan·EFS custom dump·manifest·hash·TOC 검증 완료, `DEP1_PASS` |
| DEP2 | completed | 고정 image·Compose·fail-closed restore 도구·개발 override 구현, `DEP2_PASS` |
| DEP3 | completed | 실제 3,273건 restore·Migration·health·API·Browser·관리자 PIN·Volume 보존 통과, `DEP3_PASS` |
| DEP4 | completed | 별도 project clean-room·실패 복구·재시작·test DB/Volume 격리 통과, `DEP4_PASS` |
| DEP5 | in-progress | 이식 가능한 암호화 package 도구·receipt·역할별 결과·결함 양식 준비, 최종 commit package와 독립 인수 4건 대기 (`DEP5_PACKAGE_READY`) |

현재 판정은 `DEP0_PASS`·`DEP1_PASS`·`DEP2_PASS`·`DEP3_PASS`·`DEP4_PASS`,
`DOCKER_ACCEPTANCE_PENDING`이다.

## 구현 내용

DEP0에서 실제 저장소와 실행 환경을 확인하고 DEP1에서 snapshot 생성기와 실제
Acceptance dump를 완성했다. DEP2에서는 reviewer 고정 image·Compose와 개발
override, snapshot 검증·복원 도구를 구현하고 image build·구성·fail-closed
경계를 검증했다. DEP3에서는 실제 DB 복원과 Browser smoke를 수행했으며, 아래에는
실제로 관찰한 실패와 수정·재검증 결과만 기록한다. DEP4에서는 기존 환경을
유지한 채 별도 project·Volume으로 clean-room과 복구·test 격리를 검증했다.
DEP5에서는 EFS 원본을 다른 PC로 전달할 수 없는 경계를 확인하고 이식 가능한
암호화 package와 동일 환경 인수 계약을 구현했다. 실제 수신자 결과는 아직
수집하지 않았으므로 전체 Gate는 pending으로 유지한다.

### DEP0 기준선

- 작업 트리가 깨끗한 `9d6475d49275a06704ec82651bb9d1fcdcbfd478`에서 권장
  브랜치 `feature/deploy/docker-acceptance-environment`를 생성했다.
- Integration 10 확정 구현 `f3f67aa`는 현재 SHA의 ancestor다.
- Docker Client·Server는 `29.6.2`, Compose는 `5.3.1`, Buildx는
  `0.35.0-desktop.2`다.
- host port `3000`·`8000`은 DEP0 확인 시 listen process가 없었다.
- C drive 여유 공간은 585.45 GB였다.
- snapshot 보관 위치는 workspace 밖
  `%LOCALAPPDATA%\cheongnyeon-alimi\acceptance\acceptance-20260819-9d6475d`로
  확정하고 디렉터리 존재를 확인했다.
- Runtime archive는 기존 workspace 밖 백업을 사용하며 34,043,724 byte,
  SHA-256
  `A440EFE30144678C2EF07BAE0CC824E92DCF168C3AFF9C032DA46A468AF0C358`로
  Integration 10 인계값과 일치했다.

실제 DB는 PostgreSQL `18.4`, repository와 actual Alembic은 모두
`20260810_0006`이다. Policy 3,273건, CollectionRun 61건과 대표 stable
identity 3/3을 읽기 전용 SQL로 확인했다.

admission manifest의 내장 계약 hash는
`789f8e3b61c144843e93bc762d60f114179c6bfb8e5effd260138c73484e1203`,
실제 file hash는
`03b6d91952e53148e709d2a66838faaf26f63432a49050d48f7b2ab40186ebda`로
Integration 10 기록과 각각 일치했다. 두 값은 `manifest_sha256` field를
제외한 canonical 계약 hash와 field를 포함한 파일 전체 hash여서 서로 다른 것이
정상이다.

pgpass는 workspace 밖 `%LOCALAPPDATA%\Temp`에 있고 현재 사용자 R/W ACL만
있다. 비밀번호를 출력하지 않은 연결로 기본 `postgres`가 아닌 login role이며
superuser가 아님을 확인했다. 실제 credential 값과 role 이름은 문서에 기록하지
않았다.

### Backend dependency 재현성 보정

기존 `backend/requirements.txt`의 12개 직접 의존성은 모두 최소 버전 범위여서
서로 다른 시점의 image build가 같은 transitive version을 보장하지 않았다.
또한 현재 Windows `.venv`에는 manifest가 요구하는 `httpx2`가 빠져 Backend
회귀에서 Starlette deprecation warning이 발생했다. PyPI에서 `httpx2` 2.0.0
이상 배포를 확인하고 현재 최신 검증 버전 `2.12.0`을 `.venv`와 Acceptance
constraints에 반영한 뒤, 전체 package를 Linux Python 3.14용 hash lock으로
고정했다.

- Backend 요구사항 SHA-256:
  `9889EB22FF3E449645F23DD9E2E2FEBABA93A06FC6B8B91053203028B53823EA`
- Backend Acceptance constraints SHA-256:
  `C6866B4343972A60AF3A1E430BFD30FB0E89F9D3C3EAA5ECF6D74D79A8A90E0C`
- Backend hash lock SHA-256:
  `AF60066EDECA601210ECFC2B8C59C609ACF6FA13E508FDCC7DBCBAA8F01C162D`
- Frontend npm lockfile v3 SHA-256:
  `2C651CBE11B4ADC2BDCD65D97CE31598A637776BD9C48B36688ED5B7F51F667E`

`python:3.14.5-slim-bookworm` 일회성 Linux container에서
`pip install --dry-run --require-hashes -r requirements.lock`를 실행해 전체
package가 hash 검증을 통과하고 설치 가능한 것을 확인했다. Base image digest는
`sha256:a9bee15510a364124aa24692899d269835683b883de42f7ebec8c293cf679ccb`다.

### DEP1 allowlist·민감정보 preflight

실제 PostgreSQL을 read-only session으로 inventory한 결과 public table은 다음
7개뿐이며 Integration 10 예비 allowlist와 정확히 일치했다.

| table | row |
| --- | ---: |
| `administrative_region_aliases` | 1,080 |
| `administrative_regions` | 538 |
| `alembic_version` | 1 |
| `collection_runs` | 61 |
| `policies` | 3,273 |
| `policy_region_rules` | 123,884 |
| `policy_search_documents` | 3,273 |

허용 table의 전체 column inventory를 확인하고 다음 값 수준 scan을 수행했다.

| scan | 결과 |
| --- | ---: |
| 금지 column | 0 |
| 제공된 API key 후보 | 2 |
| DB 안의 API key 일치 | 0 |
| 고위험 credential query | 0 |
| 불안전 `token` query | 0 |
| 공개 `.go.kr` 숫자 navigation token | 2 |
| provenance 로컬 절대 경로 | 0 |
| CollectionRun error 민감 문자열 | 0 |
| 비허용 contact kind | 0 |
| email contact | 0 |
| 공개 기관 연락처 | 101 |

최초 보수 regex는 양산·안성 공식 `.go.kr` 게시판 URL의 13자리 숫자 `token`
2건도 credential 후보로 잡았다. 두 값은 서로 다르고 제공된 API key와 일치하지
않으며, 공개 게시판 navigation parameter 조건을 충족했다. 이 값은 실제
credential과 합치지 않고 별도 비차단 집계로 남겼다. 구조화 contact 101건은
데이터 계약이 허용한 `phone`·`official_channel`뿐이고 email·비허용 kind는
0건이다.

`deployment/postgres/create_snapshot.py`는 다음 조건을 fail-closed로 검사한다.

- clean worktree와 현재 Git SHA
- workspace 밖 pgpass·snapshot·Runtime archive 경로
- 7개 table allowlist와 금지 column
- 알려진 secret 후보, credential query, 로컬 경로와 contact kind
- RA4 Policy 3,273·CollectionRun 61·Migration·stable identity
- admission 계약/file hash
- 기존 dump·manifest overwrite 금지
- `pg_dump --no-owner --no-acl`과 dump TOC·schema owner/ACL 재검사

생성기 단위 테스트 11개가 통과했다. 미커밋 상태에서 실행한 첫 검증은
`DEP1_BLOCKED: repository worktree must be clean`으로 종료했고 외부 snapshot
산출물을 만들지 않아 fail-closed 경계를 확인했다.

### DEP1 실제 snapshot 생성

생성기를 커밋한 clean SHA `4ae19b3`에서 첫 실제 생성을 실행했다. custom archive
자체는 만들어졌지만 PostgreSQL 18 `pg_restore --schema-only`가 SQL 출력 대상
`--file` 또는 restore 대상 `--dbname`을 요구해 검증 단계에서 중단됐다. 생성기는
`.partial`을 제거했고 최종 dump·manifest는 남기지 않았다.

원인은 archive나 DB가 아니라 schema-only 출력 명령의 누락이었다.
`--file=-`를 추가한 수정 커밋 `75510a9`에서 다시 실행해 다음 snapshot을
확정했다. `snapshot_version` 날짜는 manifest 생성 시각의 UTC 기준이다.

| 항목 | 실제 결과 |
| --- | --- |
| snapshot version | `acceptance-20260819-75510a9` |
| repository Git SHA | `75510a92d5f566e34c1ff92e7d97b65d88e8b178` |
| PostgreSQL / Alembic | `18.4` / `20260810_0006` |
| dump filename | `acceptance-post-admission.dump` |
| dump size | 3,020,687 byte |
| dump SHA-256 | `46810a6ac6082680d2fae17ab98721597ec4b5e23ec667b3d086b5a4e9739a8b` |
| manifest 계약 SHA-256 | `551136bab08bf8db45935a07a7fb8a2056acf6b1b6bc01ba117eea6331513122` |
| manifest file SHA-256 | `42394556feba9b4d0058bde495f28a808fbcb302660abc30838ec11dde455299` |
| TOC | 75행·ACL 0 |
| schema owner·ACL statement | 0 |
| table / blocker scan | 7 / 0 |
| Policy / CollectionRun | 3,273 / 61 |
| 대표 stable identity | 3/3 |

dump와 실제 manifest는 Git·workspace 밖
`%LOCALAPPDATA%\cheongnyeon-alimi\acceptance\acceptance-20260820-75510a9`에
있다. 두 파일 모두 현재 사용자만 복호화할 수 있는 Windows EFS AES-256으로
암호화했다. EFS recovery certificate는 없으므로 이 디렉터리를 유일한 복구본으로
간주하지 않고, DEP5 전달 때 별도 승인된 암호화 전달 package를 만들어야 한다.

파일 암호화 뒤 dump size·SHA-256, manifest 계약·file SHA-256을 독립 재계산해
내장값과 일치함을 확인했다. 원본 서비스 DB는 전체 과정에서 read-only inventory와
`pg_dump`만 사용해 변경하지 않았다. 이 결과로 DEP1 Gate는 `DEP1_PASS`다.

### DEP2 image·Compose 구현

Backend는 실행 시 저장소 루트의 `collectors`와 `data/reference`·`data/schema`·
`data/seeds`를 사용하고 Frontend build도 `data/seeds` alias를 사용한다. 따라서
두 image의 build context는 저장소 루트로 두고 Dockerfile별 ignore allowlist로
필요한 경로만 전송했다. root fallback `.dockerignore`도 `.env`, dump, Runtime,
로그, 가상환경과 `node_modules`를 제외한다.

Base image는 mutable tag만 사용하지 않고 다음 digest로 고정했다.

| image | base·실행 user | 실제 build 결과 |
| --- | --- | --- |
| Backend | Python 3.14.5 slim digest `a9bee155...`, UID/GID `10001:10001` | 80,337,475 byte, image ID `b42d5a09...` |
| Frontend | Node 22.22.0 slim digest `dd9d2197...`, `node` UID 1000 | 79,630,173 byte, image ID `20a48a1b...` |
| PostgreSQL | 18.4 bookworm digest `882236b8...` | official entrypoint·DB process 사용 |

Frontend는 build stage의 Node package를 runtime image에 복사하지 않고 정적
`dist`와 Node 표준 라이브러리 server만 포함한다. `npm ci`의 전체 build tree는
dev dependency advisory 4건을 표시했지만 runtime 대상
`npm audit --omit=dev --audit-level=high`는 취약점 0건으로 통과했다. Vite build는
통과했고 600.70 kB JS chunk 경고는 기능 실패가 아니며 후속 성능 개선 후보로
남겼다.

Compose는 다음 경계를 구현했다.

- `database`는 host port가 없고 internal `database` network·전용 named Volume만
  사용한다.
- `restore`는 외부 snapshot을 read-only mount하고 dump SHA-256을 container
  안에서 다시 계산한 뒤 public table·sequence가 모두 0일 때만 single
  transaction restore를 수행한다.
- `migrate`는 restore된 7개 table, Policy 3,273건, CollectionRun 61건,
  Alembic `20260810_0006`, stable identity 3건을 먼저 확인한다. 빈 DB에서
  Migration만 선행하는 흐름은 차단한다.
- Backend·Frontend는 read-only root filesystem, 최소 tmpfs·named write Volume,
  `no-new-privileges`와 health check를 사용한다.
- Browser bundle에는 내부 `database:5432`, `CHANGE_ME`, dump·`.env`·로그가
  없음을 container 내부 scan으로 확인했다.
- `database-test`는 `test` profile, `_test` suffix, 별도 password·Volume·internal
  network 계약을 사용한다.
- `compose.dev.yaml`에만 source bind mount·hot reload와
  `127.0.0.1:55432` DB port를 둔다.

`docker compose config`는 example을 사용한 reviewer·restore·test·dev 구성이
모두 통과했고 환경변수를 제공하지 않으면 exit 1로 실패했다. 정의 profile은
`restore`, `test` 두 개로 확인했다. Compose CLI 자체는 존재하지 않는 profile
이름도 오류 없이 빈 선택으로 처리하므로, 인계 문서에는 정의 profile 확인
명령과 허용 이름만 기록했다.

실제 외부 snapshot에 `verify_snapshot.py`를 실행해 snapshot version
`acceptance-20260819-75510a9`, dump SHA-256, manifest 계약·file hash,
Policy·CollectionRun·stable identity와 현재 checkout의 Git ancestor 관계가 모두
일치했다. 이 단계는 dump를 읽고 hash를 계산했을 뿐 DB restore는 실행하지
않았다.

별도 임시 Compose project의 빈 Volume에서 `migrate`를 직접 실행한 결과
`DEP2_BLOCKED: public table allowlist mismatch`, exit 1로 차단됐다. 잘못된 test
DB명은 `DEP2_BLOCKED: test database name must end with _test`, exit 64로
차단됐다. 두 검증에서 만든 container·network·Volume은 project 이름을 확인한 뒤
제거했으며 서비스 Volume에는 접근하지 않았다.

이 결과로 image build, build context, non-root, network·Volume, dependency,
placeholder와 fail-closed 경계에 대한 DEP2 Gate는 `DEP2_PASS`다. 실제 빈
Acceptance Volume restore·Migration·Backend·Frontend·Browser 결과는 DEP3에서
검증한다.

BE·FE 담당자와 대회 심사자가 image 하나를 개별 실행하는 것으로 오해하지 않도록
웹 UI 실행 방법을 보강했다. README와 문서 index에서 Docker 실행 문서로 바로
이동할 수 있고, 문서에는 최초 restore, 이후 Docker Desktop project 재시작,
Browser 접속, Volume 보존 종료와 전달 package 구성을 구분했다. DEP3~DEP5가
남았다는 상태도 함께 표시해 아직 실행하지 않은 clean-room 결과를 보증하지
않는다.

### DEP3 actual preflight

DEP3는 Git `eff9491`에서 시작했다. Docker Engine·Compose는 각각 `29.6.2`·
`5.3.1`이고 host port `3000`·`8000`의 listen process는 없었다. 기존 Compose
project와 `cheongnyeon-alimi` 이름의 Docker Volume도 0개여서 기존 Docker
데이터와 충돌하지 않는 새 Acceptance project를 만들 수 있는 상태다.

외부 snapshot을 다시 검증해 dump 3,020,687 byte와 SHA-256
`46810a6ac6082680d2fae17ab98721597ec4b5e23ec667b3d086b5a4e9739a8b`, manifest
계약·file hash, Policy 3,273건, CollectionRun 61건과 Git ancestor 관계가 모두
일치했다. reviewer·restore·test Compose config와 Backend·Frontend image build도
다시 통과했다.

실제 secret 파일 `.env.compose`는 존재하지 않았고 Backend `.env`나 root `.env`도
없어 기존 credential을 재사용하지 않았다. PIN을 터미널·채팅에 평문으로 남기지
않기 위해 `initialize_compose_env.ps1`을 추가했다. 이 도구는 로컬 보안
프롬프트에서 4자리 PIN을 받고 평문을 저장하지 않으며, 나머지 secret을 각각
32-byte 난수로 생성하고 현재 Windows 사용자 전용 ACL·Git ignore를 확인한다.
사용자가 초기화기를 실행해 `DEP3_COMPOSE_ENV_CREATED`를 확인했다. 생성 파일은
Git에서 제외되고 현재 Windows 사용자 전용 ACL 1개만 유지됐으며 PIN 평문은
저장되지 않았다.

### DEP3 restore 실패와 해결

첫 restore는 `administrative_region_alias_kind` enum type 부재로 실패했다. DEP1
dump가 허용 table만 선택해 만든 data snapshot이어서 table data와 sequence는
있지만 Alembic이 생성한 의존 enum type은 포함하지 않았기 때문이다. 복원은 단일
transaction에서 rollback되어 public table·type 0개 상태를 확인했고 일부 데이터가
남지 않았다.

해결은 dump에 임의 DDL을 덧붙이는 대신 manifest의 Alembic revision
`20260810_0006`까지 빈 DB schema를 Migration으로 먼저 만든 뒤, 검증된 dump의
table data·sequence만 FK parent 순서로 복원하는 방식이다. `alembic_version` data는
제외하고 schema inventory와 모든 대상 table이 비어 있는지 다시 확인한다.

두 번째 restore는 commit 시 constraint trigger가 빈 session `search_path`에서
`enforce_administrative_region_acyclic` helper를 찾지 못해 rollback됐다. PostgreSQL
data-only restore의 공식 옵션인 `--disable-triggers`를 단일 transaction 안에서만
사용하고, 복원 직후 count·stable identity·4개 orphan query·Alembic revision을
전부 검증하도록 수정했다. 세 번째 실행은 `DEP3_SCHEMA_STATE=ready`,
`DEP3_RESTORE_BASELINE_VERIFIED`, `DEP3_RESTORE_COMPLETED`,
`DEP3_RESTORE_PASS`로 끝났다.

### DEP3 actual DB·API·Browser

복원 DB는 Policy 3,273, CollectionRun 61, 행정구역 538, alias 1,080,
지역 rule 123,884, 검색 document 3,273건이며 Alembic은 `20260810_0006`이다.
대표 stable identity 3/3과 orphan 0을 복원 검증기가 확인했다. PostgreSQL은 host
port를 공개하지 않고 Backend·Frontend만 각각 `127.0.0.1:8000`·`:3000`에
bind됐다.

API smoke에서 `/api/v1/health`는 `ok`, `서울 청년 주거` 검색은 37건 중 5건을
반환했고 검색 응답은 605ms였다. 실제 상세 id 6197은 HTTPS 원문과 eligibility
coverage를 반환했다. 추천은 조건 없는 요청 1,301건, `age=27` 1,269건,
`category=housing` 223건, `region=서울특별시` 1건을 반환했으며, 이유와 비단정
문구가 포함됐다. `서울특별시+housing` 0건은 조건별 분해 결과 실제 데이터 교집합
없음으로 확인했다. 무토큰 `/api/v1/admin/me`는 401, 공백 검색은 422였다.

첫 Browser actual에서는 API에 존재하는 id 6197이 UI에서 “찾을 수 없음”으로
표시됐다. 원인은 Frontend Docker build가 `VITE_API_BASE_URL`만 받고
`VITE_USE_MOCK`을 지정하지 않아 코드 기본값인 Mock 모드로 빌드된 것이었다.
Compose build arg와 Dockerfile에 `VITE_USE_MOCK=false`를 고정하고 재빌드했다.
이후 상세 화면에서 `청년월세 지원사업`, 공식 원문, 자격 정보 미확인 안내가
actual API 데이터로 렌더링됐다. 경상남도·25세 추천은 실제 정책 7건과 추천 이유,
미확정 조건, D-Day를 표시했다. actual 관리자 로그인 화면에서는 Mock 전용 PIN
안내도 숨겼다.

전체 서비스를 stop 후 다시 `up --wait`한 결과 Policy count는 3,273 → 3,273으로
유지됐고 세 서비스가 다시 healthy가 됐다. container log에서 5개 secret 값과
Raw payload marker를 검사해 노출 0건을 확인했다.

사용자가 초기화 시 입력한 PIN으로 직접 로그인한 뒤 Browser DOM을 다시 확인했다.
로그인 전 `/api/v1/admin/me` 401 경계와 달리 로그인 후 `/admin` 보호 route에서
로그아웃 버튼, 최신 CollectionRun과 관리자 navigation이 렌더링됐다. 이어 actual
`/admin/policies`에서 10개 row와 `1 / 328 페이지`, 정책 id 3160~3169를 확인했다.
PIN·access token 값은 읽거나 문서·로그에 기록하지 않았다. 이로써 DEP3의 마지막
수동 인증 경계까지 통과해 `DEP3_PASS`다.

### DEP4 clean-room·복구·test 격리

DEP4는 clean Git `32bc4a344316c5f9f5d1f53700fbbf51dcb4add5`에서 시작했다.
기존 project를 건드리지 않기 위해 `cheongnyeon-alimi-dep4-cleanroom`, image tag
`dep4-32bc4a3`, Backend host port 18000, Frontend host port 13000을 사용했다.
실행 전 같은 label의 container, 예정 named Volume과 두 port 사용은 모두 0이었다.
같은 PC의 별도 project 검증이므로 기존 비추적 env 계약을 사용했지만 image tag와
Volume·network·port는 모두 분리했다. 다른 PC 인계에서는 각 담당자가 초기화기로
자기 secret을 새로 생성한다.

승인 snapshot `acceptance-20260819-75510a9`를 새 Volume에 복원한 결과
`DEP3_RESTORE_PASS`, Policy 3,273, CollectionRun 61, Alembic
`20260810_0006`을 확인했다. clean-room API health는 `ok`, `경상남도 청년 취업`
검색은 24건이었다. 포트 13000 actual Browser에서 id 15005 `밀양 청년 취업 역량
강화 교육 과정`의 신청 기간·연령·지역·원문·D-Day·`.ics`를 확인했고 Browser
warning·error는 0건이었다. 기존 DEP3 서비스 DB도 Policy 3,273건을 유지했다.

실패·복구 검증은 clean-room Volume에만 수행했다.

- dump hash를 64자리 불일치 값으로 주입한 restore는 exit 1과
  `mounted dump SHA-256 does not match`로 차단됐고 Policy 수는
  3,273 → 3,273이었다.
- database container를 중지하자 실행 중 Backend `/health`는 503을 반환했다.
  DB가 없는 상태에서 Backend를 재시작하면 container health는 `starting`, HTTP는
  empty response로 실패했다. DB를 다시 기동하고 Compose dependency를 적용하자
  세 서비스가 healthy로 복구됐고 Policy는 3,273건이었다.
- 전체 project를 `stop`한 동안 service·test DB와 Backend write Volume 4개가
  유지됐다. 다시 `up --wait`한 뒤 Policy·Run은 3,273·61로 동일했고 복원
  verifier가 stable identity 3/3·orphan 0을 다시 확인했다.

test profile은 `cheongnyeon_alimi_acceptance_test` DB와 별도
`acceptance-test-db` Volume, 별도 internal `database-test` network에서 기동했다.
test DB에 `dep4_isolation_probe` 1건을 생성했지만 서비스 DB의 같은 table 수는
0이었고 Policy는 3,273건이었다. `_test` suffix가 없는 one-shot 실행은 exit 64로
차단됐다. test container를 stop한 뒤에도 서비스 DB 3,273건과 service Volume은
변하지 않았다.

clean-room log에서 5개 secret 값과 Raw payload marker 노출은 각각 0건이고 DB
host publish는 없었다. 검증을 마친 뒤 clean-room container는 전부 stop했으며
다음 named Volume을 명시적으로 보존했다.

- `cheongnyeon-alimi-dep4-cleanroom_acceptance-db`
- `cheongnyeon-alimi-dep4-cleanroom_acceptance-test-db`
- `cheongnyeon-alimi-dep4-cleanroom_backend-logs`
- `cheongnyeon-alimi-dep4-cleanroom_backend-runtime`

Volume 삭제는 수행하지 않았다. 기존 `cheongnyeon-alimi-acceptance`의 DB·Backend·
Frontend는 계속 healthy다. 이로써 `DEP4_PASS`다.

### DEP5 이식 가능한 package·인수 계약

DEP1 snapshot은 현재 PC의 Windows EFS로 보호되어 있으므로 파일을 그대로 복사해
다른 PC에서 사용하는 전달물이 될 수 없다. DEP5에서는 다음 경계를 갖는
`create_acceptance_transfer_package.ps1`을 추가했다.

- 이 문서와 인수 계약이 포함된 clean Git commit에서만 생성
- workspace 밖 출력과 기존 archive·receipt 비덮어쓰기
- 승인 snapshot을 기존 verifier로 다시 검증한 뒤 dump·manifest만 package에 포함
- 7-Zip AES-256·header encryption과 대화형 passphrase 사용
- 생성 archive를 같은 passphrase로 다시 test한 뒤에만 최종 파일명으로 이동
- archive hash, 실행 Git SHA, snapshot·dump·manifest, Migration·집계,
  Compose·설정 문서 hash를 비밀정보 없는 receipt로 기록

Backend·Frontend·사용성 리뷰어·QA는 각자 격리된 Compose project·Volume에서
restore하고 [역할별 실행 결과 양식](../../handoff/docker_acceptance/acceptance_result_template.md)과
[결함·재검증 양식](../../handoff/docker_acceptance/defect_report_template.md)으로
회신한다. 네 결과의 Git SHA·snapshot version·dump hash와 archive receipt가
일치하기 전에는 `DEP5_PASS`가 아니다.

현재 상태는 생성기·인수 문서·양식의 구현과 정적 계약 검증을 마친
`DEP5_PACKAGE_READY`다. 현재 변경을 commit하기 전에는 최종 실행 Git SHA가
확정되지 않으므로 실제 archive·receipt를 의도적으로 생성하지 않았다.

시스템 MSI 설치는 Windows 관리자 승인 단계에서 완료되지 않아 공식 7-Zip
26.02 `7zr.exe` portable console을 workspace 밖에 준비했다. 다운로드 파일
SHA-256 `56b8cc9f4971cef253644fafe54063ed7fdca551d4dee0f8c6baa81b855acd72`는
공식 GitHub release asset digest와 일치했다. 실제 대화형 probe에서 AES-256·
encrypted header archive 생성과 두 번째 암호 입력을 통한 archive test가
통과했다. 이때 기존 archive의 test·extract 명령에 값 없는 `-p`를 붙이면 빈
암호로 처리되어 실패함을 확인하고, test·수신자 extract 명령에서는 `-p`를
제거해 암호 prompt가 열리도록 보정했다.

후속 Slice에서도 다음 값을 실제 실행 결과로 계속 기록한다.

- Git SHA와 worktree 상태
- Docker Engine·Compose·BuildKit version
- snapshot version·size·SHA-256·PostgreSQL major·Alembic revision
- allowlist와 금지 table·field scan 결과
- image digest와 Compose project·Volume 이름
- restore·Migration·health 결과와 소요 시간
- DB 집계와 대표 stable identity
- Backend·Frontend·Browser test command와 pass·skip·fail
- clean-room PC 환경과 재시작·복구·test 격리 결과
- 첫 실패, 원인, 수정 SHA와 재검증

## 주요 변경 파일

DEP0~DEP5 package 준비에서 변경하거나 생성한 주요 파일은 다음과 같다.

- `docs/development/develop_plan/deploy/01_docker_acceptance_environment.md`
- `docs/development/development_notes/deploy/docker_acceptance_environment.md`
- `backend/requirements.acceptance.constraints.txt`
- `backend/requirements.lock`
- `deployment/postgres/create_snapshot.py`
- `deployment/postgres/acceptance-snapshot.manifest.example.json`
- `tests/test_create_acceptance_snapshot.py`
- `README.md`
- `docs/index.md`
- `.gitattributes`
- `.dockerignore`
- `.env.compose.example`
- `compose.yaml`
- `compose.dev.yaml`
- `backend/Dockerfile`
- `backend/Dockerfile.dockerignore`
- `frontend/Dockerfile`
- `frontend/Dockerfile.dockerignore`
- `frontend/docker-server.mjs`
- `deployment/postgres/restore.ps1`
- `deployment/postgres/restore.sh`
- `deployment/postgres/initialize_compose_env.ps1`
- `deployment/postgres/prepare_acceptance_schema.py`
- `deployment/postgres/verify_snapshot.py`
- `deployment/postgres/verify_restored_database.py`
- `frontend/src/pages/admin/AdminLoginPage.tsx`
- `tests/test_docker_acceptance_contract.py`
- `tests/test_verify_acceptance_snapshot.py`
- `docs/development/docker_acceptance_setup.md`
- `deployment/postgres/create_acceptance_transfer_package.ps1`
- `docs/development/handoff/docker_acceptance/README.md`
- `docs/development/handoff/docker_acceptance/acceptance_result_template.md`
- `docs/development/handoff/docker_acceptance/defect_report_template.md`
- `tests/test_docker_acceptance_handoff_contract.py`

DEP2~DEP4 실제 구현·검증 파일은 위 목록과 개발 계획의 해당 절에 반영했다.

## 설계 결정

1. review admission과 deployment 구현을 분리한다. Integration 10은 어떤
   데이터를 승격할지 결정하고, Deploy 01은 확정된 snapshot을 변경 없이
   재현한다.
2. DTL5-5 전에 `DOCKER_ACCEPTANCE_PASS`를 요구한다. 이는 BE·FE 담당자와
   리뷰어·QA가 서로 다른 DB를 보고 같은 결함으로 합치는 문제를 막기 위한
   환경 Gate다.
3. 실제 dump와 Runtime archive는 Git·image·CI에 포함하지 않고 승인된 암호화
   전달 수단을 사용한다.
4. restore는 빈 Volume에만 허용하며 자동 reset·drop·`down -v`를 정상 흐름에
   두지 않는다.
5. CI는 합성 Seed로 image·Compose를 검증하고 실제 snapshot Acceptance는
   승인된 로컬 clean-room Gate로 유지한다.
6. `run_docker.bat` one-click launcher는 DEP3~DEP5의 실제 절차가 고정된 뒤 만드는
   비차단 후속 작업으로 둔다. Deploy 01 안에서는 launcher 편의를 위해 미검증
   restore·secret·Volume 동작을 추가하지 않는다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| Git·branch·worktree | 통과, DEP0 `9d6475d`·DEP1 snapshot `75510a9` clean SHA |
| Docker Engine·Compose·Buildx | 통과, `29.6.2`·`5.3.1`·`0.35.0-desktop.2` |
| Backend dependency hash lock | 통과, 38 package·Linux dry-run hash 설치 가능 |
| Frontend lockfile | 통과, npm lockfile v3 |
| repository·actual Migration | 통과, 모두 `20260810_0006` |
| RA4 DB·manifest 입력 | 통과, Policy 3,273·Run 61·stable identity 3/3·계약/file hash 일치 |
| secret·외부 보관·port | 통과, 비추적 pgpass ACL·외부 snapshot 경로·3000/8000 free |
| DEP1 snapshot 생성기 단위 테스트 | 11개 통과 |
| DEP1 Python 정적 검사 | Ruff 통과 |
| allowlist·민감정보 preflight | 통과, table 7·금지 scan blocker 0 |
| dirty worktree fail-closed | 통과, exit 1·외부 산출물 0 |
| 첫 snapshot 생성 | 예상 차단, `pg_restore --schema-only` 출력 대상 누락·최종 산출물 0 |
| 최종 snapshot 생성·dump hash | 통과, 3,020,687 byte·SHA-256 일치·EFS AES-256 |
| manifest·TOC·owner·ACL | 통과, 계약/file hash 일치·TOC 75·ACL/owner statement 0 |
| Compose reviewer·profile·dev config | 통과, placeholder 미제공 exit 1·profile `restore`/`test` |
| Backend·Frontend image build | 통과, non-root·digest 고정·80,337,475/79,630,173 byte |
| image 금지 artifact scan | 통과, dump·backup·`.env`·로그·내부 DB URL·placeholder 0 |
| Frontend production dependency audit | 통과, `--omit=dev` 취약점 0 |
| DEP2 snapshot verifier actual | 통과, DEP1 snapshot hash·집계·Git ancestor 일치 |
| 빈 DB Migration guard | 통과, 예상 차단 exit 1·임시 Volume 제거 |
| 잘못된 test DB명 guard | 통과, 예상 차단 exit 64·임시 Volume 제거 |
| DEP1·DEP2 도구/계약 단위 테스트 | 22개 통과 |
| DEP3 project·port preflight | 통과, 기존 project·matching Volume 0·3000/8000 free |
| DEP3 snapshot·config·image preflight | 통과, hash·집계·Git ancestor 일치·두 image build 성공 |
| DEP3 Compose secret | 통과, 보안 프롬프트 생성·PIN hash만 저장·현재 사용자 ACL·Git ignore 확인 |
| restore·Migration·health | 통과, `DEP3_RESTORE_PASS`·revision `20260810_0006`·세 서비스 healthy |
| actual DB·API | 통과, Policy 3,273·Run 61·stable identity 3/3·orphan 0·검색/상세/추천/401/422 |
| actual Browser | 통과, actual 상세·추천·원문·미확정·D-Day·PIN 로그인·관리자 정책 1/328페이지 확인 |
| Frontend Mock→actual 통합 결함 | 수정·재검증, `VITE_USE_MOCK=false` build 계약·Mock PIN 안내 비노출 |
| Frontend unit·lint·actual build | 통과, unit 216개·lint·`VITE_USE_MOCK=false` build |
| DEP1~DEP3 도구/계약 단위 테스트 | 25개 통과 |
| credential·Raw payload log scan | 통과, secret value 0·raw marker 0 |
| 서비스 재시작·Volume 보존 | 통과, Policy 3,273 → 3,273·세 서비스 healthy |
| DEP4 clean-room restore·actual | 통과, 별도 project/image/port·Policy 3,273·Run 61·검색 24·Browser actual |
| 잘못된 hash 복구 안전성 | 통과, exit 1·Policy 3,273 → 3,273 |
| DB health·Backend startup 복구 | 통과, DB down health 503·Backend starting 실패·재기동 후 세 서비스 healthy |
| clean-room 재시작·Volume 보존 | 통과, Policy/Run 3,273/61 불변·stable identity 3/3·orphan 0·Volume 4개 유지 |
| test DB·Volume·network 격리 | 통과, `_test` DB·별도 Volume/network·probe 미전파·잘못된 이름 exit 64 |
| DEP4 secret·Raw log·DB port | 통과, secret/raw marker 0·PostgreSQL host publish 없음 |
| DEP5 PowerShell package 생성기 구문 | 통과, parser error 0 |
| DEP5 package·인수 계약 단위 테스트 | 3개 통과 |
| DEP5 package dirty worktree guard | 예상 차단 통과, `DEP5_BLOCKED`·archive/receipt 미생성 |
| DEP5 portable 7-Zip·암호화 probe | 통과, 26.02 official digest 일치·7zAES·encrypted header test |
| 문서 검증 | `Documentation validation passed.` |
| 문서 검증기 단위 테스트 | 11개 통과 |

미실행 항목은 통과로 계산하지 않는다.

## 남은 작업

1. 현재 DEP5 변경을 commit하여 최종 실행 Git SHA를 고정한다.
2. clean checkout에서 이식 가능한 암호화 package·receipt를 생성하고 archive
   hash를 재확인한다.
3. package를 BE·FE 담당자와 사용성 리뷰어·QA에게 인계하되 passphrase는 별도
   승인 채널로 전달한다.
4. 네 역할의 독립 결과를 대조하고 모든 근거가 일치할 때만
   `DOCKER_ACCEPTANCE_PASS`를 기록하여 DTL5-5를 연다.

`run_docker.bat`은 `DOCKER_ACCEPTANCE_PASS` 이후 별도 backlog에서 구현한다.
Deploy 01 완료와 DTL5-5 시작을 막는 항목은 아니다.

## 관련 문서

- [Integration 10 Review Admission](../../develop_plan/integration/10_review_admission_docker_acceptance.md)
- [Integration 07 Release 2 개발 기록](../integration/release_2_feature_acceptance.md)
- [5주차 Data·Team Leader 실행 계획](../../weekly_plan/week_05_data_team_leader.md)
- [컨테이너 구조](../../../architecture/container_structure.md)
- [Docker Acceptance 동일 환경 인계 패키지](../../handoff/docker_acceptance/README.md)
