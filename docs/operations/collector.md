# Collector 운영

## 운영 경계

일반 사용자는 Collector를 실행하지 않는다. `run_docker.bat`이 검증된 공개
dataset을 설치하므로 API key 없이 검색·추천을 사용할 수 있다. 실제 Source
수집, scheduler와 dataset promotion은 중앙 운영자 범위다.

## 등록 Source

현재 worker registry와 관리자 수동 실행 계약에는 11개 Source가 있다.

```text
bokjiro-central-welfare-api
cheonan-youthcenter-web
data-go-kr-incheon-youth-programs
kinfa-financial-product-web
kosaf-scholarship-web
kpass-transit-refund-web
lh-housing-announcement-web
regional-busan-youth-platform
regional-gyeongbuk-youth-platform
work24-policy-web
youthcenter-api
```

등록 Source와 공개 dataset Source는 다르다. 현재 공개 artifact는 복지로,
온통청년과 인천 공공데이터 3개 Source만 포함한다. 나머지는 재배포 근거 확인
전까지 로컬 Runtime·DB와 관리자 검토 범위에만 둔다.

## 관리자 수집기 화면

`/admin/collectors`에서 다음 정보를 비밀정보 없이 확인한다.

- 등록 Source ID·표시명·API·file·web 유형
- Redis broker와 Celery worker 연결
- worker registry 등록 여부
- API credential의 설정됨·미설정 boolean
- 수동 실행 가능 여부
- scheduler 활성 상태·대상 Source·KST cron
- 활성 공개 dataset의 Source별 정책 수
- active run과 최근 CollectionRun

화면은 API key 값·길이·일부 문자열, worker hostname과 broker credential을
반환하지 않는다.

## 직접 제한 수집

개발 환경에서 registry와 Source 응답을 확인할 때만 사용한다.

```powershell
python -m collectors --list-sources
python -m collectors --source youthcenter-api --page 1 --limit 10 --detail-limit 0
```

`--detail-limit`은 0~5 범위다. 실제 API key가 없는 Source는 명확한 설정 오류로
중단한다. 이 명령은 사용자 공개 dataset을 갱신하지 않는다.

## 관리자 수동 실행

인증된 관리자가 수집기 화면이나 CollectionRun API에서 Source와 요청 수를
확인하면 Backend가 다음 순서로 처리한다.

1. 같은 Source의 non-stale queued·running 실행 확인
2. PostgreSQL에 durable `queued` CollectionRun 생성
3. Redis `collection` queue에 task publish
4. worker가 Source별 DB lock 획득
5. 제한 수집 → Runtime Raw 저장 → replay·정규화·검증 → DB import
6. terminal 상태와 안전한 count 기록

중복 active run은 `409 Conflict`로 거부한다. queue publish가 실패하면 생성한
run을 `failed`로 마감한다. 일반 수동 실행은 `is_complete_snapshot=false`이므로
성공해도 public dataset promotion 근거가 아니다.

## 정기 실행

Celery beat는 `COLLECTION_SCHEDULE_ENABLED=true`일 때만 하나의 Source를 KST
cron으로 enqueue한다. 기본값은 비활성화다.

주요 설정:

- `COLLECTION_SCHEDULE_SOURCE_ID`
- `COLLECTION_SCHEDULE_REQUESTED_COUNT`
- `COLLECTION_SCHEDULE_COMPLETE_SNAPSHOT`
- `COLLECTION_SCHEDULE_CRON_HOUR`
- `COLLECTION_SCHEDULE_CRON_MINUTE`

같은 Source에 active run이 있으면 새 schedule run을 만들지 않는다. scheduler
instance는 하나만 운영한다.

## worker 전달·재시도

worker는 prefetch 1, late acknowledgement와 worker-lost 재전달을 사용한다.
Source lock이 busy이면 bounded retry와 jitter backoff를 적용하고 한도를 넘으면
run을 failed로 마감한다. task에는 soft·hard timeout과 rate limit이 적용된다.

Redis는 broker일 뿐 Policy·CollectionRun의 권위 저장소가 아니다. Redis AOF가
있어도 DB 실행 상태와 멱등 importer를 함께 사용한다.

## 완전 snapshot

Release용 완전 수집은 일반 수동 실행과 분리한다.

```powershell
python scripts/run_complete_collection.py `
  --source-id youthcenter-api `
  --page-size 500 `
  --timeout-seconds 1200
```

실제 명령은 중앙 Workflow의 폐기 가능한 DB·queue 환경에서 실행한다. 완전
snapshot은 manifest item count 전체를 고정 snapshot ID로 재생하고 다음을
증명해야 한다.

- terminal `succeeded`
- `is_complete_snapshot=true`
- invalid·rejected·failed count 0
- 해당 Source의 최신 CollectionRun

조건을 만족하지 않으면 공개 artifact 후보로 사용할 수 없다.

## Runtime Raw 재처리

`scripts/import_runtime_data.py`는 저장된 Raw를 외부 재호출 없이 Extractor·
Normalizer·Validator와 importer에 다시 통과시킨다. source, snapshot·limit,
dry-run과 Runtime root를 명시할 수 있다.

- `(source_id, external_id)`로 멱등 upsert한다.
- invalid가 있으면 정상 batch와 분리하거나 계약에 따라 rollback한다.
- 완전성이 증명되지 않은 재처리는 미발견 정책을 inactive로 만들지 않는다.
- replay 결과는 공개 membership을 자동 변경하지 않는다.

실제 Raw와 decision·checkpoint는 `backend-runtime` 또는 Production Runtime
Volume에 두며 Git에 commit하지 않는다.

## 상태와 count

| 상태 | 의미 |
| --- | --- |
| `queued` | DB 생성 후 worker 대기 |
| `running` | worker가 실행권을 얻음 |
| `succeeded` | 실행과 DB 처리가 성공 |
| `partial_failure` | 일부 정규화·검증 문제 |
| `failed` | 실행 또는 persist 실패 |

CollectionRun은 requested, Raw, extracted, accepted, partial, invalid, duplicate,
rejected, inserted, updated, unchanged, skipped와 failed count를 저장한다.
정책 본문, Raw URL, API key와 전체 exception message는 저장하지 않는다.

queued·running이 기준 시간을 넘으면 관리자 화면에서 stale로 표시한다.
stale 표시는 감사·복구 신호이며 기존 행을 자동 삭제하지 않는다.

## 공개 dataset promotion

완전 CollectionRun 3개를 검증한 뒤 `promote_public_dataset.py`가 Source contract,
content safety, artifact·manifest와 격리 DB 설치를 검증한다. 사용자 projection,
identity hash와 지역 coverage가 모두 통과한 뒤에만 GitHub Release와
`dataset-latest`를 갱신한다.

수동 수집이나 웹 Source row가 로컬 DB에 추가돼도 active public membership에는
자동 포함되지 않는다.

## 장애 확인 순서

1. `/admin/collectors`에서 broker·worker·registry·credential 상태 확인
2. `/admin/runs`에서 active·stale·terminal 상태와 count 확인
3. `/admin/runs/{id}`에서 단계별 집계 확인
4. `/admin/logs`에서 run ID·Source·안전한 error type 조회
5. worker·Redis health와 Runtime Volume 소유권 확인

재시작 복구는
[Docker 수동 수집·재시작 문제](../troubleshooting/backend/docker_manual_collection_restart_recovery.md)를
참고한다. worker 재시작 때문에 공개 dataset이나 PostgreSQL Volume을 초기화하지
않는다.

## 테스트

- 단위 테스트는 합성 JSON·XML·HTML과 주입 가능한 client를 사용한다.
- 실제 Source 호출은 중앙 통합 실행으로 분리한다.
- 관리자 acceptance probe는 외부 Source 없이 Redis → worker → PostgreSQL을
  확인하며 acceptance·test 환경에서만 허용한다.
- API key, Raw payload와 DB credential을 테스트 출력에 남기지 않는다.

데이터 수집 원칙은 [수집 정책](../data/collection_policy.md), 공개 승격은
[공개 dataset](../data/public_policy_dataset.md), 실행 DB 계약은
[CollectionRun](../architecture/collection_run_database.md)을 따른다.
