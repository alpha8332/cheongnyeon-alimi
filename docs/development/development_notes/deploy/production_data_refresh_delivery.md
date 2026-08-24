# Deploy 02 Production Data Refresh and Delivery 개발 기록

## 작업 정보

- 상태: in-progress
- 작업일: `2026-08-24`
- 담당 영역: Data, Team Leader - Integration·Deploy
- 계획: [Deploy 02 계획](../../develop_plan/deploy/02_production_data_refresh_delivery.md)
- 주차 계획: [6주차 Final Release](../../weekly_plan/week_06_final_release.md)
- 시작 SHA: `f838d4191cb5cc33c324d3e946c7a12ed8a56b1b`
- 현재 Gate: `W6-P4_PRODUCTION_PASS`

## 목적

API key와 로컬 DB dump 없이 배포 가능한 공개 normalized bootstrap 경계를
확정하고, Source·field allowlist·versioned manifest와 정책 생명주기를 실행
가능한 계약으로 구현한다.

## Forest 범위

- W6-P0 공개 데이터·라이선스 계약과 Runtime proof artifact
- W6-P1 정책 생명주기
- W6-P2 Celery·Redis 중앙 수집
- W6-P3 clone/ZIP 최초 실행
- W6-P4 Production Compose·CI/CD
- W6-P5 clean-room과 Final Gate

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| W6-P0 | completed | default-deny 계약, 451건 actual artifact·hash 재검증, `W6-P0_DATASET_CONTRACT_PASS` |
| W6-P1 | completed | 3 timestamp, soft-deactivation, 마감 기본 제외, `W6-P1_LIFECYCLE_PASS` |
| W6-P2 | completed | Redis AOF·Celery worker·단일 Beat·actual queue, `W6-P2_QUEUE_PASS` |
| W6-P3 | completed | actual 451건 clean Volume·offline 멱등 bootstrap, `W6-P3_BOOTSTRAP_PASS` |
| W6-P4 | completed | 중앙 dataset Release·GHCR digest·SLSA provenance·clean Production smoke, `W6-P4_PRODUCTION_PASS` |
| W6-P5 | pending | clean-room·Final Gate |

## 구현 내용

### Source·field 계약

- 실제 DB 16개 Source를 기존 inventory와 `2026-08-23` 공식 페이지로 대조했다.
- 복지로 중앙부처복지서비스만 `이용허락범위 제한 없음` 근거로 include했다.
- 온통청년·지역·천안·KOSAF·고용24 등은 약관 제한 또는 명시적 공개
  라이선스 부재로 제외했다.
- `NormalizedProgram 1.2.0` 필드 37개를 허용하고 DB 내부 ID·timestamp,
  Raw·dump·비밀·연락처를 금지했다.

### 생성·검증 도구

- allowlist Source만 읽는 `build_public_bootstrap_dataset.py`를 추가했다.
- PostgreSQL row를 현재 1.2.0 공개 Schema로 projection하고 각 레코드를
  Schema·Python model로 검증한다.
- dataset·Schema·Source contract SHA-256, row·byte 수와 Source attribution을
  manifest에 기록한다.
- 검증 모드는 DB 없이 artifact 변조·계약 drift·비허용 Source·연락처·비밀
  pattern을 다시 확인한다.
- 생성은 partial file 뒤 원자적 rename을 사용하고 Runtime output은 Git에서
  제외한다.

### Actual proof artifact

- Acceptance DB의 복지로 후보 461건을 읽었다.
- 자유 텍스트의 개인 휴대전화 형식 때문에 10건을 레코드 단위로 제외했다.
- 공개 artifact 451건, 1,247,899 bytes를 생성했다.
- SHA-256은
  `28c36be54ee859b63a496e2cea295d58ab88eb438ef1ffcce0b647198cf8ccb3`다.
- 별도 검증 모드가 같은 version·451건·SHA-256을 재확인했다.

### 정책 생명주기

- `20260824_0007` Migration으로 `last_seen_at`, `last_verified_at`,
  `inactive_at`과 조회 index·무결성 constraint를 추가했다.
- 기존 3,273건은 `collected_at`, `updated_at`을 기준으로 전부 backfill했고
  기존 행을 임의 inactive 처리하지 않았다.
- 사용자 목록·상세·자연어 검색·추천·공개 dataset builder가 같은
  `inactive_at IS NULL`·KST 종료일 predicate를 사용한다.
- 기존 지역 projection의 물리 `DELETE`를 soft-deactivation으로 교체했다.
- 완전 snapshot 전체 재생, invalid 0건, DB commit 성공일 때만 미발견
  identity를 inactive 처리한다. 일부 limit·invalid·rejected·failed와 지역
  `FAILED` 결정은 기존 상태를 보존한다.
- 동일 identity 재등장 시 생명주기 시각을 단조 증가시키고 `inactive_at`을
  `null`로 복구한다.

### 중앙 Celery·Redis 수집 queue

- 관리자 `POST /api/v1/admin/collection-runs`는 PostgreSQL에 `queued` row를
  먼저 commit한 뒤 같은 `run_id`를 Celery task ID로 Redis에 발행한다.
- FastAPI `BackgroundTasks` 실행을 제거해 외부 HTTP·Raw·Importer 작업이 API
  process 자원과 생명주기를 점유하지 않는다.
- `collection-worker`는 prefetch 1, late ack, worker-lost 재전달, soft/hard
  timeout, bounded retry·jitter, 기본 `6/m` rate limit을 적용한다.
- PostgreSQL partial unique index가 Source별 active row를 하나로 제한하고,
  session advisory lock이 여러 worker의 실제 Source 겹침을 차단한다.
- Redis는 AOF Volume을 사용하지만 최종 상태 원본은 PostgreSQL이다. Celery
  result backend는 비활성화했다.
- Beat는 단일 service이며 schedule은 기본 비활성화했다. API key와 호출 주기를
  중앙 운영자가 승인한 뒤에만 활성화한다.
- Frontend CollectionRun type·필터·badge·Mock과 active-run 판정을 `queued`까지
  확장해 Backend `202` 응답을 실행 완료로 오해하지 않게 했다.
- `20260824_0008`은 `queued` enum·constraint를, `20260824_0009`는 active Source
  unique index와 기존 중복 active row의 명시적 failed 보정을 추가한다.

### clone/ZIP 최초 실행

- 저장소 루트 `run_docker.bat`과 `scripts/run_docker.ps1`을 추가했다.
- Docker engine·Compose v2·2 GiB disk·port와 `.env.compose` 없는 기존 기본
  Volume 충돌을 먼저 검사한다.
- HTTPS pointer, manifest SHA-256, dataset SHA-256·byte를 host에서 검증하고
  `%LOCALAPPDATA%` 아래 version별 immutable cache로 옮긴다.
- `public-dataset-bootstrap` Compose profile은 검증 cache를 read-only mount하고
  P0 검증기로 manifest·Schema·Source allowlist·내용 안전성을 다시 검사한 뒤에만
  PostgreSQL에 멱등 upsert한다.
- 전체 검증과 import가 성공한 뒤에만 offline `latest.pointer.json`을 갱신한다.
  network 장애만 직전 cache로 대체하고 hash 불일치는 그대로 중단한다.
- Migration과 bootstrap 뒤 여섯 상시 service health를 기다린 다음 Browser를
  열며, 두 번째 실행은 기존 cache·Volume을 재사용한다.
- 외부 GitHub Release pointer·asset 발행은 P4가 담당한다. P3에서는 같은 형식의
  actual P0 artifact를 로컬 검증 입력으로 사용해 소비 파이프라인을 확정했다.

### Production Compose·CI/CD

- `compose.production.yaml`은 source build 없이 Backend·Frontend release image를
  입력받고 PostgreSQL·Redis·Migration·dataset bootstrap·Backend·worker·단일
  Beat·Frontend·Nginx를 실행한다.
- 외부 host port는 Nginx `8080` 하나뿐이다. Database·queue network는 internal,
  collector egress는 worker에만 부여하고 로그·Runtime·DB·Redis를 분리된 named
  Volume에 둔다.
- Nginx는 `/api/`를 Backend로, 나머지를 Frontend로 reverse proxy하고 자체
  `/health`를 제공한다. Frontend image는 same-origin `VITE_API_BASE_URL=/`로
  빌드한다.
- dataset promotion은 공개 allowlist Source마다 최신 CollectionRun 한 건을
  요구한다. `collection`·`succeeded`·`is_complete_snapshot=true`·finished 및
  invalid/rejected/failed 0건이 아니거나 더 최신 실행이 있으면 artifact 작성
  전에 중단한다. 따라서 제한 수집 성공은 latest를 갱신할 수 없다.
- 불변 dataset Release를 업로드한 뒤 다시 다운로드해 검증하고 마지막에만
  `dataset-latest` pointer를 갱신한다. rollback도 기존 불변 asset을 재검증한
  뒤 pointer만 이동한다.
- 공통 CI는 Backend/Data pytest·PostgreSQL, Frontend unit·lint·build와 image
  contract를 실행한다. Production release는 GHCR digest image, SBOM·provenance·
  attestation, clean Compose smoke를 통과한 뒤 Git·Migration·Schema·dataset
  version을 `production-release.json`에 묶는다.
- `20260824_0010`은 완전 snapshot 증거를 CollectionRun에 영속한다. 일반 관리자
  제한 수집은 항상 false이고, 중앙 scheduler의 명시적 complete mode가 bounded
  multi-page manifest와 동일 snapshot 전체 import를 통과한 경우에만 true다.

## 주요 변경 파일

- `data/schema/public_policy_dataset_sources.schema.json`
- `data/schema/public_policy_dataset_manifest.schema.json`
- `data/schema/public_policy_dataset_pointer.schema.json`
- `data/reference/public_policy_dataset_sources.json`
- `scripts/build_public_bootstrap_dataset.py`
- `tests/test_public_bootstrap_dataset.py`
- `docs/data/public_policy_dataset.md`
- `.gitignore`
- `backend/alembic/versions/20260824_0007_policy_lifecycle.py`
- `backend/app/repositories/policy_lifecycle.py`
- `backend/app/models/policy.py`
- `backend/app/services/runtime_importer.py`
- `docs/data/policy_lifecycle.md`
- `backend/alembic/versions/20260824_0008_collection_queue.py`
- `backend/alembic/versions/20260824_0009_active_source_run.py`
- `backend/alembic/versions/20260824_0010_collection_run_completeness.py`
- `backend/app/worker/celery_app.py`
- `backend/app/worker/tasks.py`
- `backend/app/services/collection_queue.py`
- `backend/app/services/source_collection_lock.py`
- `backend/app/cli/import_public_dataset.py`
- `scripts/run_docker.ps1`
- `run_docker.bat`
- `docs/operations/docker_first_run.md`
- `compose.yaml`
- `compose.production.yaml`
- `.env.production.example`
- `deployment/nginx/nginx.conf`
- `.github/workflows/ci.yml`
- `.github/workflows/production-release.yml`
- `.github/workflows/public-dataset-release.yml`
- `.github/workflows/public-dataset-rollback.yml`
- `scripts/promote_public_dataset.py`
- `scripts/build_public_dataset_pointer.py`
- `scripts/download_public_dataset.py`
- `scripts/build_production_release_manifest.py`
- `data/schema/production_release_manifest.schema.json`
- `tests/test_production_delivery.py`
- `docs/operations/production_delivery.md`

## 설계 결정

- 수집 가능과 공개 재배포 가능을 분리하고 default-deny로 판정한다.
- 실제 데이터는 Git에 넣지 않고 P4의 versioned GitHub Release asset으로만
  발행한다.
- Redis·Celery 도입 전에도 dataset 계약은 PostgreSQL·Source license를
  기준으로 독립 검증할 수 있어야 한다.
- 기존 DB 복지로 행은 `schema_version=1.1.0`이지만 현재 DB column에는 1.2.0
  필드가 모두 있다. 공개 projection에서 Schema version만 1.2.0으로 올리고
  `data_quality_status=partial`과 기존 값은 그대로 보존한다.
- 이메일·개인 휴대전화·기관 연락처가 발견된 레코드는 자동 마스킹하지 않고
  전체 제외한다.
- immutable versioned asset을 먼저 검증한 뒤 작은 latest pointer만 갱신하며
  실패 시 직전 pointer를 유지한다.
- 다운로드 완료가 아니라 컨테이너 전체 계약 검증과 DB import 성공을 cache
  latest 승격의 transaction 경계로 사용한다.
- 실행기는 사용자가 소유한 기존 Volume을 자동 삭제·초기화하지 않는다.

## 검증 결과

### 첫 실패와 보정

1. 임시 Docker run의 시스템 Python에 SQLAlchemy가 없어 import 전에 중단됐다.
   image의 `/opt/venv/bin/python`으로 실행 경계를 수정했다.
2. `.env.compose`에는 조합된 `DATABASE_URL`이 없어 argument 검증이 중단됐다.
   컨테이너 내부 비추적 DB 변수로 URL을 조합하고 값은 출력하지 않았다.
3. 실제 복지로 행이 1.1.0이라 1.2.0 Schema 검증이 fail-closed했다. 현재 DB
   필드를 1.2.0 projection으로 검증하되 품질 상태는 보존했다.
4. 개인 휴대전화 형식 10건이 발견돼 발행이 중단됐다. 레코드 단위 제외와
   manifest 제외 집계를 추가한 뒤 다시 생성했다.
5. 첫 Beat 기동은 root 소유 named Volume에 schedule DB를 만들지 못해
   `PermissionError`로 재시작했다. schedule은 상태 원본이 아니므로 non-root가
   쓸 수 있는 `/tmp`로 옮기고 Redis AOF·PostgreSQL만 영속화했다.
6. 실제 공개 웹 Source 2개 queue 실행이 `TransportError`로 종료됐다. worker가
   internal DB·queue network에만 연결돼 외부 HTTP route가 없음을 확인해 worker
   전용 `collector-egress` network를 추가했다. 같은 천안 Source를 다시 실행해
   Raw 3·추출 1·accepted 1·unchanged 1, `succeeded`를 확인했다.
7. 첫 P3 image build는 Backend Docker context allowlist가 `scripts/`를 제외해
   공개 dataset 검증기 `COPY`에서 실패했다. 검증기 한 파일만 context에
   명시적으로 포함해 image 비밀·Runtime 제외 경계는 유지했다.
8. 독립 clean project 첫 시도는 이전 DEP4·DEP5 검증에서 남은 빈 Docker network
   25개 때문에 `all predefined address pools have been fully subnetted`로
   중단됐다. 연결 컨테이너가 0인 프로젝트 network만 확인·정리하고 같은 실행을
   재개해 새 Volume bootstrap을 통과했다.
9. 첫 Production Compose smoke는 inline `tmpfs` 문자열의 쉼표가 별도 mount로
   해석돼 `mode=1777` 경로 오류로 중단됐다. mount option 전체를 명시적 YAML
   문자열로 고정하고 clean project를 재생성했다.
10. worker healthcheck의 destination을 single quote로 감싸 `$HOSTNAME`이 확장되지
    않아 실제 worker가 ready인데도 `No nodes replied`가 발생했다. Compose escape만
    남기고 shell quote를 제거한 뒤 worker·Beat·전체 wait가 healthy로 통과했다.

### 통과 결과

| 검증 | 결과 |
| --- | --- |
| 신규 단위 테스트 | `4 tests`, PASS |
| Source contract | default exclude, include 1 Source, 37 allowed fields |
| actual 후보 | 461건 |
| 개인정보 보수 경계 | 10건 제외, 발행 artifact match count 0 |
| actual artifact | 451건, 1,247,899 bytes |
| artifact 재검증 | version·row·SHA-256 일치 |
| 전체 pytest | 548 passed, 27 skipped, 241 subtests passed |
| 실제 PostgreSQL 전용 | 18 passed, upgrade·backfill·downgrade·upsert 포함 |
| Acceptance Migration | `20260810_0006 → 20260824_0007`, 3,273건 보존 |
| lifecycle backfill | `last_seen_at`·`last_verified_at` 누락 0건 |
| 마감 기본 제외 | 1,093건 제외, 공개 후보·actual API 2,180건 |
| 마감 상세 actual | 공개 상세 `404`, DB 행 보존 |
| queue 단위 경계 | 32 passed |
| Acceptance Compose | PostgreSQL·Redis·Backend·worker·Beat·Frontend healthy |
| queue Migration | `20260824_0007 → 0008 → 0009`, active Source unique index 1개 |
| actual 성공 task | probe `335a7e79-…` `queued → running → succeeded` |
| egress 실패 주입 | 수정 전 2건 `TransportError`, terminal failed·policy write 0 |
| actual live Source | 천안 `098557da-…`, Raw 3·accepted 1·unchanged 1·`succeeded` |
| broker restart | worker 중지 적재 `ce1d07c7-…`, Redis restart 후 `succeeded` |
| PostgreSQL Source lock | 첫 획득 `true`, 동시 두 번째 획득 `false`, 해제 후 재획득 |
| 컨테이너 PostgreSQL 전체 | 212 passed (Migration upgrade·downgrade 포함) |
| 저장소 전체 pytest | 566 passed, 28 skipped, 241 subtests passed |
| Runtime unittest | 327 passed |
| Frontend unit | 222 passed |
| Frontend lint·build | PASS (`queued` 계약 포함) |
| 문서·Compose 검증 | PASS |
| P3 계약 단위 | 18 passed |
| actual 기존 Volume 첫 P3 import | 451 updated, 검증·health PASS |
| offline 재실행 | 451 unchanged, 기존 cache·Volume 재사용 PASS |
| API key 없는 clean Volume | Migration `0001 → 0009`, 451 inserted |
| clean Compose health | PostgreSQL·Redis·Backend·worker·Beat·Frontend healthy |
| hash 불일치 주입 | DB·latest 변경 없이 fail-closed PASS |
| P4 신규 계약 회귀 | 8 passed, 제한 성공 promotion 차단 포함 |
| P4 image build | Backend·same-origin Frontend local image PASS |
| Production Migration | clean Volume `0001 → 20260824_0010 (head)` |
| Production dataset | `public-bootstrap-20260823-f838d41`, 451 inserted·재실행 451 unchanged |
| Production health | PostgreSQL·Redis·Backend·worker·Beat·Frontend·Nginx healthy |
| Nginx actual | `/health` 200, `/api` 451건 조회, SPA `/` 200 |
| Production network | host 공개 Nginx 1개, DB·Redis host port 0개 |
| 중앙 공개 수집·Release | run `32687869888`, 후보·accepted 461건, 제외 4건, 발행 457건 |
| 원격 GHCR·Production Release | run `32688600713`, digest image 2개·SLSA provenance 2건·clean smoke·`v1.0.0` PASS |
| P4 기본 로컬 pytest | 576 passed, 28 skipped, 241 subtests passed |
| P4 Linux·PostgreSQL CI 동등 환경 | 602 passed, 2 skipped, 241 subtests passed |
| P4 Frontend | 222 passed, lint·same-origin production build PASS |
| Workflow lint | actionlint 1.7.12, 4 Workflow 0건 |
| 공개 수집 실행 구조 | GitHub-hosted ephemeral PostgreSQL·Redis·Celery, Self-hosted 제거 |

### P4 원격 CI 첫 실행 회귀

- 문제 상황: PR #20의 첫 CI에서 Frontend는 통과했지만 `backend-data`와
  `image-contract`가 실패했다.
- 원인: 정책 생명주기 도입 후 마감 정책이 공개 조회에서 제외되는데 기존
  PostgreSQL 통합 테스트 2건이 과거 공개 건수를 기대했고, DB round-trip
  테스트는 새 lifecycle timestamp 3개를 normalized 원문 필드처럼 비교했다.
  별도로 `image-contract` job은 Python 의존성을 설치하지 않고 pytest를
  실행했다.
- 해결: DB 보존 4건과 공개 노출 3건을 분리해 검증하고 마감 상세 `404`를
  명시했다. lifecycle timestamp는 시스템 관리 필드로 분리한 뒤 값의 의미를
  별도 assertion으로 검증했으며, image contract job에 Python 3.14와 lockfile
  설치 단계를 추가했다.
- 결과: GitHub Runner와 같은 Linux·Python 3.14·PostgreSQL 18.4 환경에서
  `602 passed, 2 skipped, 241 subtests passed`, P4 계약 8건과 actionlint가
  모두 통과했다.

### P4 중앙 dataset·Production Release 실제 발행

- `public-dataset-release.yml`의 완전 수집은 후보 461건을 전부 처리하고
  `invalid=0`, `rejected=0`, `failed=0`, complete snapshot을 기록했다.
- 공개 연락처 경계에서 개인 휴대전화 패턴 4건을 제외해 457건을 발행했다.
  발행 artifact의 비밀·이메일·개인 휴대전화 match count는 모두 0이다.
- dataset version은 `public-bootstrap-20260824-f5883bb79c594f`, artifact
  SHA-256은
  `6457a37f109381384eb238bb84fd43dd5b60f0d37bc3a262d2c4e483a27ed1f9`다.
- `dataset-latest`를 실제 공개 URL에서 다시 내려받아 version·457건·artifact
  hash를 재검증했다.
- `v1.0.0` Production workflow는 Backend·Frontend digest image를 GHCR에
  발행하고 SLSA provenance 2건을 생성했다. 이어 공개 dataset 다운로드·검증과
  clean Migration `0001 → 20260824_0010`, Production Compose smoke를 통과한 뒤
  `production-release.json`을 Release에 올렸다.
- 실제 원격 실행과 불변 값은
  [Production 배포 문서](../../../operations/production_delivery.md#v100-실제-발행-증거)에
  고정했다.

### P4 공개 dataset activation 트러블슈팅

최초 네 번의 중앙 수집 시도는 발행 전에 fail-closed로 중단됐고 불변 Release와
`dataset-latest`를 변경하지 않았다. worker readiness의 hostname 의존과 Celery
remote-control 응답 의존을 제거하고, 안전한 오류 유형·worker log 진단을
보강한 뒤 GitHub Secret에는 라벨이나 줄바꿈이 아닌 복지로 key 값 한 줄만
등록했다. 다섯 번째 실행은 57초에 완료됐고 readiness는 79초에서 4초로
94.9% 감소했다. 전체 원인·수정·측정 근거는
[공개 dataset 중앙 발행 activation 복구](../../../troubleshooting/integration/public_dataset_release_activation.md)에
분리해 기록했다.

## 남은 작업

1. `W6-P5`에서 새 clone과 GitHub ZIP을 각각 독립 Volume에 올려 README만으로
   최초 실행·재실행·복구·Browser actual을 검증한다.
2. 공개 제외 4건은 제공기관 연락처와 개인 연락처를 구분하는 승인 규칙이
   생기기 전까지 제외 상태를 유지한다.
3. Production에서는 `collector-egress`를 worker에만 허용하고 제공기관 장애와
   인증·TLS 오류를 Source별 운영 지표로 계속 구분한다.
4. clean-room blocker/high 0건과 제출 문서·SBOM·CHANGELOG 대조가 끝난 뒤에만
   `W6-G0_FINAL_RELEASE_PASS`를 판정한다.
