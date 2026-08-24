# Production 배포와 데이터셋 발행

## 적용 범위

이 문서는 운영자가 검증된 Backend·Frontend image와 공개 normalized dataset을
하나의 Production release로 발행하고 배포하는 절차를 정의한다. 일반 사용자의
clone/ZIP 최초 실행은 [Windows Docker 최초 실행](docker_first_run.md)을 따른다.

Production은 사용자 PC마다 원본 API를 수집하지 않는다. 보호된
`production-data` Environment의 GitHub-hosted 일회성 job만 API key에 접근하며,
job마다 새 PostgreSQL·Redis·Celery worker에서 완전 수집과 promotion을 수행한다.
사용자 PC DB와 장기 Self-hosted Runner는 연결하지 않는다. 일반 배포는 GHCR
image와 공개 dataset GitHub Release만 소비한다.

## 배포 단위

- `compose.production.yaml`: PostgreSQL·Redis·Migration·dataset bootstrap·
  Backend·worker·단일 Beat·Frontend·Nginx
- `.env.production`: Git에서 제외되는 image digest, host 경로와 secret
- `production-release.json`: Git SHA·image digest·Alembic head·normalized Schema·
  dataset version/hash를 묶는 불변 릴리스 영수증
- `dataset-<version>` Release: 불변 dataset과 manifest
- `dataset-latest` Release: 검증된 불변 manifest를 가리키는 작은 mutable pointer

## Production Compose 실행

1. `.env.production.example`을 `.env.production`으로 복사한다.
2. `production-release.json`의 digest-qualified image 두 개를 입력한다. tag만
   입력하거나 `CHANGE_ME`를 남기지 않는다.
3. 검증된 dataset artifact와 `manifest.json`이 함께 있는 절대 host 경로를
   `PUBLIC_DATASET_DIR`에 입력한다.
4. 모든 secret을 새 값으로 교체하고 아래 명령을 실행한다.

```powershell
docker compose --env-file .env.production -f compose.production.yaml config --quiet
docker compose --env-file .env.production -f compose.production.yaml up -d --wait
```

외부에는 기본 `127.0.0.1:8080` Nginx만 공개된다. `/api/`는 Backend로, 나머지
경로는 Frontend로 전달된다. PostgreSQL과 Redis는 internal network이며 collector
worker만 별도 egress network를 가진다.

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
Invoke-RestMethod 'http://127.0.0.1:8080/api/v1/policies?limit=1&include_partial=true'
docker compose --env-file .env.production -f compose.production.yaml ps
docker compose --env-file .env.production -f compose.production.yaml logs --tail 100 nginx backend collection-worker
```

정상 종료는 `docker compose ... down`을 사용한다. `--volumes`는 운영 DB·Redis·
로그·Runtime을 삭제하므로 백업과 정확한 대상 확인 없이 사용하지 않는다.

## CI와 image release

`.github/workflows/ci.yml`은 Backend/Data 전체 pytest와 PostgreSQL, Frontend
unit·lint·build, Backend·Frontend image build와 Production 계약 회귀를 수행한다.

`v*` tag 또는 수동 실행으로 `production-release.yml`을 시작하면 CI 성공 뒤에만
다음 순서로 진행한다.

1. Backend·Frontend image를 GHCR에 Git SHA·release tag로 push
2. SBOM·provenance 생성과 artifact attestation
3. 현재 `dataset-latest`를 내려받아 hash·Schema 재검증
4. digest image로 clean Production Compose Migration·bootstrap·smoke
5. `production-release.json` 생성과 해당 GitHub Release 업로드

실제 Workflow가 완료되기 전에는 로컬 image digest를 GHCR 발행 증거로 사용하지
않으며 `W6-P4_PRODUCTION_PASS`를 부여하지 않는다.

## v1.0.0 실제 발행 증거

`2026-08-24`에 Git `f5883bbbc5a830f18114cb6677251389505e9ecc`를
annotated `v1.0.0` tag로 발행하고
[Production workflow](https://github.com/alpha8332/cheongnyeon-alimi/actions/runs/32688600713)를
끝까지 통과했다. Release 영수증은
[production-release.json](https://github.com/alpha8332/cheongnyeon-alimi/releases/download/v1.0.0/production-release.json)이며
asset SHA-256은
`2ce4eada7e50c653ac52804bab1df41f7987a5cdbbbe43385a12bfa64be6da69`다.

| 항목 | 고정 값 |
| --- | --- |
| Release | [`v1.0.0`](https://github.com/alpha8332/cheongnyeon-alimi/releases/tag/v1.0.0) |
| Alembic head | `20260824_0010` |
| normalized Schema | `1.2.0`, SHA-256 `e9169e69869ffd77cdc6f5d26c04fbc660c018859cea886949d98219be3a7b49` |
| 공개 dataset | `public-bootstrap-20260824-f5883bb79c594f`, 457건 |
| dataset manifest | SHA-256 `03bc9ce4d396c727a1277c1525d1a10a2fff7eb6d23cc08a2d31ac6113930487` |
| latest pointer | SHA-256 `35b7d11ea440c6bc2cca0cfff20879113acfc66864f68ec6f0683b0f61820c5a` |
| Backend image | `ghcr.io/alpha8332/cheongnyeon-alimi-backend@sha256:96d4eb098dbac89570b691b8836dbe8d4134823f73aab527e8bf7f4ef9852898` |
| Frontend image | `ghcr.io/alpha8332/cheongnyeon-alimi-frontend@sha256:ea721d7b0990d5a5da43d33e461d3d69bd2744b415b45785d4be4bd51b3f353b` |
| 공급망 증거 | [SLSA provenance 2건](https://github.com/alpha8332/cheongnyeon-alimi/attestations) |

Workflow는 공개 dataset을 다시 내려받아 hash·Schema를 검증하고, 위 digest
image로 clean Migration·bootstrap·Nginx smoke를 통과한 뒤에만 Release 영수증을
올렸다. 이 실제 원격 증거를 기준으로 `W6-P4_PRODUCTION_PASS`를 판정했다.

## v1.0.1 MIT 라이선스 패치 발행 증거

`2026-08-24`에 Final Gate Git
`ea6d3fac8d012c4f4216bbb472a1446508c46049`를 annotated `v1.0.1` tag로
발행하고
[Production workflow](https://github.com/alpha8332/cheongnyeon-alimi/actions/runs/32693225940)를
끝까지 통과했다. 이 패치 릴리스는 `v1.0.0`의 공개 dataset 계약을 유지하면서
GitHub source archive에 표준 MIT `LICENSE`를 포함한다. Release 영수증은
[production-release.json](https://github.com/alpha8332/cheongnyeon-alimi/releases/download/v1.0.1/production-release.json)이며
asset SHA-256은
`e89ed2f62b412c65472713506c64117f1447fbaef96a2fcf49e99af2e6683a6f`다.

| 항목 | 고정 값 |
| --- | --- |
| Release | [`v1.0.1`](https://github.com/alpha8332/cheongnyeon-alimi/releases/tag/v1.0.1) |
| Git SHA | `ea6d3fac8d012c4f4216bbb472a1446508c46049` |
| Alembic head | `20260824_0010` |
| normalized Schema | `1.2.0`, SHA-256 `e9169e69869ffd77cdc6f5d26c04fbc660c018859cea886949d98219be3a7b49` |
| 공개 dataset | `public-bootstrap-20260824-f5883bb79c594f`, 457건 |
| dataset manifest | SHA-256 `03bc9ce4d396c727a1277c1525d1a10a2fff7eb6d23cc08a2d31ac6113930487` |
| latest pointer | SHA-256 `35b7d11ea440c6bc2cca0cfff20879113acfc66864f68ec6f0683b0f61820c5a` |
| Backend image | `ghcr.io/alpha8332/cheongnyeon-alimi-backend@sha256:b5e54f0a568020f24a81570d9c750f7883678e72fee62cccd1e177a95a483878` |
| Frontend image | `ghcr.io/alpha8332/cheongnyeon-alimi-frontend@sha256:d3aaf747127e62f2a5de933cd4955dd6e003dbed6f7abc1ca7bccd50712148fd` |
| 공급망 증거 | [SLSA provenance 2건](https://github.com/alpha8332/cheongnyeon-alimi/attestations) |

검증 시 GitHub tag source ZIP을 새 디렉터리에 내려받아 루트 `LICENSE`의
`MIT License` 표제와 `Copyright (c) 2026 cheongnyeon-alimi contributors`를
확인했다. 자동 생성 source archive의 hash는 배포 계약으로 사용하지 않고,
불변 배포 식별은 위 tag Git SHA와 Release 영수증 SHA-256으로 판정한다.

## Dataset promotion Gate

`public-dataset-release.yml`은 보호된 `production-data` Environment와
GitHub-hosted `ubuntu-latest`에서 실행한다. Environment secret은 공개 재배포가
허용된 API Source의 `BOKJIRO_API_KEY`, `YOUTHCENTER_API_KEY`이며 DB URL·password는
저장하지 않는다.
Workflow 내부 PostgreSQL과 Redis는 매 실행 종료 시 폐기된다. 수동 실행과 매일
03:17 KST schedule은 같은 `concurrency` 그룹을 사용해 중복 실행하지 않는다.

Workflow는 Migration 뒤 격리 Celery worker를 시작하고
`scripts/run_complete_collection.py`로 공개 allowlist Source를 queue에 넣는다.
그 실행에서 생성된 CollectionRun은 다음을 모두 만족해야 한다.

- 해당 Source의 최신 `run_type=collection`
- terminal `status=succeeded`
- `is_complete_snapshot=true`
- `finished_at` 존재
- `invalid_count`·`rejected_count`·`failed_count`가 모두 0

조건이 맞지 않으면 artifact 작성 전 중단한다. 통과하면 불변 Release를 먼저
업로드하고, 업로드된 파일을 다시 내려받아 검증한 뒤에만 `dataset-latest`
pointer를 갱신한다. 실패·`partial_failure`·더 최신 실행 존재 시 기존 latest는
그대로 남는다.

공개 dataset 수집 Source는 `bokjiro-central-welfare-api`, `youthcenter-api`,
`data-go-kr-incheon-youth-programs`다. Worker는 bounded multi-page snapshot
manifest를 만든 뒤 그 snapshot ID만 재생해 완전성 증거를 CollectionRun에
기록한다. 일반 관리자 제한 수집은 성공해도
`is_complete_snapshot=false`이며 promotion 입력으로 사용할 수 없다. 신규 Source는
라이선스 allowlist와 해당 API secret, 완전 수집 회귀를 함께 추가해야 한다.

공개 저장소에 장기 Self-hosted Runner를 연결하지 않는다. PR 코드가 runner와
secret을 탈취할 수 있는 공격 표면을 피하고, GitHub-hosted job의 폐기 가능한 DB와
queue만 사용한다.

## Rollback

`public-dataset-rollback.yml`에 기존 `dataset_version`을 입력한다. Workflow는
불변 Release의 manifest·artifact hash와 Schema를 다시 검증하고 새 pointer를
만든 뒤 `dataset-latest`만 이전 version으로 이동한다. dataset asset을 덮어쓰거나
운영 DB dump를 배포하지 않는다.

Rollback 후 Production 재배포에서는 이동된 pointer로 dataset을 다시 내려받아
검증하고 bootstrap한다. 기존 정책 identity upsert는 멱등이며 정책 DB와 Volume
복구는 별도의 백업 절차로 다룬다.

## Secret·artifact 금지 경계

- `.env.production`, API key, PIN 평문, DB password를 Git·image·CI artifact에
  포함하지 않는다.
- Raw payload, HTML, PostgreSQL dump, Runtime log를 공개 Release에 넣지 않는다.
- GHCR에는 Dockerfile의 allowlist context만 포함하고 dataset은 별도 Release로
  유지한다.
- Production release는 image digest·Git SHA·Migration·Schema·dataset version이
  하나의 manifest에서 일치할 때만 승인한다.
