# Production 배포와 데이터셋 발행

## 적용 범위

이 문서는 운영자가 검증된 Backend·Frontend image와 공개 normalized dataset을
하나의 Production release로 발행하고 배포하는 절차를 정의한다. 일반 사용자의
clone/ZIP 최초 실행은 [Windows Docker 최초 실행](docker_first_run.md)을 따른다.

Production은 사용자 PC마다 원본 API를 수집하지 않는다. 승인된 중앙
`production-data` runner만 API key와 운영 DB에 접근하며, 일반 배포는 GHCR image와
공개 dataset GitHub Release만 소비한다.

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

## Dataset promotion Gate

`public-dataset-release.yml`은 보호된 `production-data` environment와
`[self-hosted, linux, x64, production-data]` runner에서만 수동 실행한다. secret
`PRODUCTION_DATASET_DATABASE_URL`은 이 runner에만 제공한다.

입력한 CollectionRun은 공개 allowlist Source마다 정확히 하나여야 하며 다음을
모두 만족해야 한다.

- 해당 Source의 최신 `run_type=collection`
- terminal `status=succeeded`
- `is_complete_snapshot=true`
- `finished_at` 존재
- `invalid_count`·`rejected_count`·`failed_count`가 모두 0

조건이 맞지 않으면 artifact 작성 전 중단한다. 통과하면 불변 Release를 먼저
업로드하고, 업로드된 파일을 다시 내려받아 검증한 뒤에만 `dataset-latest`
pointer를 갱신한다. 실패·`partial_failure`·더 최신 실행 존재 시 기존 latest는
그대로 남는다.

완전 Source 실행은 중앙 scheduler에서만 명시적으로 활성화한다. 공개 dataset의
현재 Source를 기준으로 `COLLECTION_SCHEDULE_SOURCE_ID=bokjiro-central-welfare-api`,
`COLLECTION_SCHEDULE_COMPLETE_SNAPSHOT=true`, 적절한 page size와
`COLLECTION_SNAPSHOT_REQUEST_BUDGET`을 설정하고 API key를 secret으로 주입한다.
worker는 bounded multi-page snapshot manifest를 만든 뒤 그 snapshot ID만 재생해
완전성 증거를 CollectionRun에 기록한다. 관리자 UI의 일반 제한 수집은 성공해도
`is_complete_snapshot=false`이며 promotion 입력으로 사용할 수 없다.

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
