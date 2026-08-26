# Production 배포와 공개 dataset 발행

## 적용 범위

운영자가 검증된 Backend·Frontend image와 공개 normalized dataset을 발행하고
`compose.production.yaml`로 배포하는 현재 절차다. 일반 사용자의 clone·ZIP
실행은 [Windows Docker 최초 실행](docker_first_run.md)을 따른다.

사용자 PC는 원본 API를 수집하지 않는다. 보호된 GitHub Environment의 일회성
job만 승인된 API key에 접근하며 새 PostgreSQL·Redis·Celery 환경에서 완전
수집과 promotion을 수행한다.

## 배포 단위

- `compose.production.yaml`: PostgreSQL·Redis·Migration·dataset bootstrap·
  Backend·worker·scheduler·Frontend·Nginx
- `.env.production`: Git에서 제외되는 image digest, host 경로와 secret
- `production-release.json`: Git SHA, image digest, Alembic head, Schema와
  dataset version·hash를 묶는 릴리스 영수증
- `dataset-<version>` Release: 불변 dataset artifact와 manifest
- `dataset-latest` Release: 검증된 불변 manifest를 가리키는 pointer

## Production Compose

1. `.env.production.example`을 Git에서 제외된 `.env.production`으로 복사한다.
2. Release 영수증의 digest-qualified Backend·Frontend image를 입력한다.
3. 검증된 dataset artifact와 manifest가 있는 절대 경로를 지정한다.
4. 모든 secret을 새 값으로 주입하고 구성을 검증한다.

```powershell
docker compose --env-file .env.production -f compose.production.yaml config --quiet
docker compose --env-file .env.production -f compose.production.yaml up -d --wait
```

기본 Host 노출은 `127.0.0.1:8080` Nginx 하나다. `/api/`는 Backend, 나머지는
Frontend로 전달된다. PostgreSQL과 Redis는 internal network에 있고 실제 Source
HTTPS가 필요한 worker만 egress network를 사용한다.

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
Invoke-RestMethod 'http://127.0.0.1:8080/api/v1/policies?limit=1&include_partial=true'
docker compose --env-file .env.production -f compose.production.yaml ps
```

`down`은 Volume을 보존한다. `down -v`는 Production DB·Redis·로그·Runtime을
삭제하므로 백업과 정확한 Compose project 확인 없이 사용하지 않는다.

## 애플리케이션 Release Workflow

`.github/workflows/ci.yml`은 Backend·Data pytest와 PostgreSQL, Frontend
unit·lint·build, image와 Production 계약을 검증한다.

`v*` tag 또는 수동 실행으로 `production-release.yml`을 시작하면 CI 성공 뒤에만
다음을 수행한다.

1. Backend·Frontend image를 GHCR에 Git SHA·tag로 push
2. SBOM·provenance와 artifact attestation 생성
3. `dataset-latest` 다운로드와 hash·Schema 재검증
4. digest image로 clean Production Migration·bootstrap·smoke
5. `production-release.json` 생성과 GitHub Release 업로드

## 현재 공개 Release 증거

`2026-08-25`에 `main` Git
`c3d3935a196a024037168e9afb5a94dfef4542e3`을 annotated `v1.0.2`로 발행하고
[Production workflow](https://github.com/alpha8332/cheongnyeon-alimi/actions/runs/32840085712)를
통과했다.

| 항목 | 고정 값 |
| --- | --- |
| Release | [`v1.0.2`](https://github.com/alpha8332/cheongnyeon-alimi/releases/tag/v1.0.2) |
| Git SHA | `c3d3935a196a024037168e9afb5a94dfef4542e3` |
| Alembic head | `20260824_0011` |
| Normalized Schema | `1.2.0`, SHA-256 `e9169e69869ffd77cdc6f5d26c04fbc660c018859cea886949d98219be3a7b49` |
| 공개 dataset | `public-bootstrap-20260824-897152e7a18c15`, 2,052건 |
| dataset manifest | SHA-256 `8658ae447eae7cc5e005d90e41e3c2007658fc38e9110cc369dd902323d1d1a9` |
| Backend image | `ghcr.io/alpha8332/cheongnyeon-alimi-backend@sha256:60b8cb9f960f2d61130778ad36f0fb7b917293ed6d3721c46dd9007b33bebfe7` |
| Frontend image | `ghcr.io/alpha8332/cheongnyeon-alimi-frontend@sha256:940967f5d9328277f7ed4e9b3909055e2159c3ddf56ea2541041074a1a71b98a` |
| Release 영수증 | SHA-256 `440bc6b40f47b8f91d1d2ee4c73c8ec8ab67c77fa2abcc55f9bd62eb658057d2` |
| 공급망 증거 | [SLSA provenance](https://github.com/alpha8332/cheongnyeon-alimi/attestations) |

현재 dataset의 Source 구성은 복지로 461건, 온통청년 1,587건, 인천 공공데이터
4건이며 활성 identity SHA-256은
`9f65f2b1dae66b7f07b61310f5f3d07c024e0ab9e86eee843387f06d04afd0e5`다.

이 값은 `v1.0.2`의 불변 증거다. `dataset-latest`가 이후 승격되면 사용자
실행의 현재 수치는 새 manifest를 따른다.

## 공개 dataset Workflow

`public-dataset-release.yml`은 보호된 `production-data` Environment와
GitHub-hosted 일회성 runner에서 실행한다. Source API key는 Environment secret으로
주입하고 저장소·artifact·로그에 기록하지 않는다. DB와 Redis는 job 종료 시
폐기된다.

수동 실행과 schedule은 같은 concurrency group을 사용한다. Workflow는 행정구역
기준을 적재하고 worker를 시작한 뒤 공개 allowlist Source를 완전 수집한다.
promotion 입력 CollectionRun은 다음을 모두 만족해야 한다.

- Source의 최신 `run_type=collection`
- terminal `status=succeeded`와 `finished_at`
- `is_complete_snapshot=true`
- invalid·rejected·failed count가 모두 0

통과한 후보만 artifact로 만들고 같은 격리 DB에 다시 설치·활성화한다. 현재
Validator로 품질을 재분류하고 active membership 기준 목록·검색·추천·상세와
identity hash를 검사한다.

지역 coverage Gate는 활성 최상위 관할과 관할별 단독 대상 정책이 존재하는지
확인한다. 서울만 있거나 전국형 한 row에 모든 지역 이름만 붙인 artifact는
발행할 수 없다. 공개 Source 3개도 각각 1건 이상 있어야 한다.

불변 Release 업로드 뒤 파일을 다시 내려받아 hash를 확인한 경우에만
`dataset-latest` pointer를 갱신한다. 실패·불완전 수집·더 최신 실행 발견에서는
기존 pointer를 유지한다.

## Rollback

`public-dataset-rollback.yml`에 기존 dataset version을 입력한다. Workflow는
불변 Release의 manifest·artifact와 Schema를 다시 검증하고 `dataset-latest`
pointer만 이전 version으로 이동한다. artifact를 덮어쓰거나 DB dump를 배포하지
않는다.

## 금지 경계

- `.env.production`, API key, PIN, token과 DB 비밀번호를 Git·image·CI artifact에
  포함하지 않는다.
- Raw payload, HTML, PostgreSQL dump, Runtime log를 공개 Release에 넣지 않는다.
- 공개 저장소 PR 코드가 장기 secret·DB에 접근하지 않도록 self-hosted runner를
  연결하지 않는다.
- image digest·Git SHA·Migration·Schema·dataset version이 영수증과 일치할 때만
  Production Release를 승인한다.

최종 제출 상태는 [제출 체크리스트](../contest/open_source_submission_checklist.md),
기능·데이터 QA는
[v1.0.2 개선 기록](../troubleshooting/integration/v1_0_2_qa_improvements.md)을
따른다.
