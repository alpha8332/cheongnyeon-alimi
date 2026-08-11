# Collector 실행

## 현재 지원 소스

```text
youthcenter-api
bokjiro-central-welfare-api
cheonan-youthcenter-web
regional-gyeongbuk-youth-platform
regional-busan-youth-platform
```

`regional-seoul-youth-platform`은 목록 링크 클릭 뒤 identity가 생기는 Browser
Source이므로 HTTP Collector 목록에는 없고, 검증된 Browser 캡처를 Runtime Raw로
가져온 뒤 재처리 CLI에서 지원한다.

현재 Collector는 명시적 CLI 실행만 지원한다. 단일 페이지 제한 수집과
호출 예산 안에서 전체 목록을 순회하는 릴리스 snapshot 수집을 구분한다.
저장된 Runtime Raw는 별도 재처리 CLI로 추가 외부 호출 없이 PostgreSQL에
적재할 수 있다. Scheduler와 자동 주기 적재는 구현하지 않았다.

## 실행 환경

다음 환경변수를 현재 프로세스에 안전하게 주입한다.

```text
YOUTHCENTER_API_KEY
BOKJIRO_API_KEY
HTTP_TIMEOUT_SECONDS
HTTP_MAX_RETRIES
HTTP_REQUEST_DELAY_SECONDS
```

HTTP 변수는 생략하면 각각 10초, 추가 재시도 3회, 요청 간격 1초를 사용한다.
`.env.example`은 변수명과 안전한 예시를 제공하지만 Collector가 `.env`
파일을 자동으로 읽지는 않는다. API 키를 shell history, 명령 인자, 로그나
문서에 입력하지 않고 현재 환경의 비밀 주입 수단을 사용한다.

키 존재 여부만 확인하려면 값을 출력하지 않는다.

```powershell
Test-Path Env:YOUTHCENTER_API_KEY
Test-Path Env:BOKJIRO_API_KEY
```

## Source와 옵션 확인

```powershell
python -m collectors --list-sources
python -m collectors --help
```

공통 옵션:

| 옵션 | 기본값 | 범위 | 의미 |
| --- | --- | --- | --- |
| `--page` | `1` | 1~1000 | 요청 페이지 |
| `--limit` | `10` | 1~500 | 목록 요청·저장 최대 항목 수 |
| `--detail-limit` | `3` | 0~5 | Source별 상세 수, 승인 예산은 최대 3~5건 |

온통청년은 `--detail-limit`을 사용하지 않는다.

## 제한 수집

온통청년 목록 10건:

```powershell
python -m collectors --source youthcenter-api --page 1 --limit 10 --detail-limit 0
```

복지로 목록 10건과 그중 상세 3건:

```powershell
python -m collectors --source bokjiro-central-welfare-api --page 1 --limit 10 --detail-limit 3
```

천안청년센터 승인 목록 1회와 공지 674번 상세 1건:

```powershell
python -m collectors --source cheonan-youthcenter-web --page 1 --limit 1 --detail-limit 1
```

이 Source는 `page=1`만 허용하고 `limit`과 `detail-limit`이 더 커도 승인 정책
1건·상세 1건을 넘기지 않는다. 요청 시작 간격은 최소 2초다.

경북 신청중 목록 3건과 상세 3건:

```powershell
python -m collectors --source regional-gyeongbuk-youth-platform `
  --page 1 --limit 3 --detail-limit 3
```

경북은 공식 `신청중` 필터를 사용하고 지역구분·시행기관·지원대상 evidence가
일치하는 후보를 상세 예산 안에서 우선한다. 실제 승인은 이후 지역·신청 상태
Gate가 결정한다.

부산 목록 3건과 상세 3건:

```powershell
python -m collectors --source regional-busan-youth-platform `
  --page 1 --limit 3 --detail-limit 3
```

두 지역 Source 모두 page 1, 목록 1회, 상세 최대 3건과 요청 간격 최소 2초를
강제한다. 부산의 이미지 원문을 재배포하지 않고 정책 식별·기관·기간·대상 등
최소 사실과 Raw provenance만 처리한다.

성공 출력에는 source ID, 실제 요청 수, 항목·상세·Raw 문서 수만 포함된다.
요청 URL, query, 인증키, payload와 저장 파일명은 출력하지 않는다.

## 릴리스 snapshot 수집

전체 목록 수집은 `scripts/collect_release_snapshot.py`를 사용한다. 각 page의
Raw가 모두 저장되고 Source가 보고한 `total_count`만큼 고유 external ID를
확인한 경우에만 완료 manifest를 원자적으로 생성한다. 호출 예산 부족,
중복 ID, 수집 중 total 변경, 조기 빈 page 또는 Raw metadata 불일치가 있으면
완료 manifest를 만들지 않고 실패한다.

온통청년 전체 목록, 최대 6회 요청:

```powershell
.\.venv\Scripts\python.exe -B scripts\collect_release_snapshot.py `
  --source youthcenter-api `
  --raw-root runtime/raw `
  --page-size 500 `
  --detail-limit 0 `
  --request-budget 6
```

복지로 전체 목록과 첫 page의 상세 최대 5건, 최대 6회 요청:

```powershell
.\.venv\Scripts\python.exe -B scripts\collect_release_snapshot.py `
  --source bokjiro-central-welfare-api `
  --raw-root runtime/raw `
  --page-size 500 `
  --detail-limit 5 `
  --request-budget 6
```

| 옵션 | 기본값 | 범위 | 의미 |
| --- | --- | --- | --- |
| `--source` | 필수 | 지원 Source ID | 수집할 Source |
| `--raw-root` | `runtime/raw` | 경로 | Git 제외 Raw root |
| `--page-size` | `500` | 1~500 | page당 목록 수 |
| `--detail-limit` | `0` | 0~5 | 첫 page 복지로 상세 수 |
| `--request-budget` | `12` | 1~100 | 목록과 상세를 합한 최대 요청 수 |

완료 manifest는 다음 Git 제외 경로에 저장된다.

```text
runtime/raw/_snapshots/<source_id>/<snapshot_id>.json
```

manifest에는 인증 query나 payload를 넣지 않고 snapshot ID, 시작·완료 시각,
page size, 호출 예산·실제 호출 수, total·item 수와 기여 Raw document ID만
기록한다. 수집 중간에 저장된 Raw는 원문 보존을 위해 남을 수 있지만 완료
manifest가 없으므로 릴리스 snapshot으로 선택되지 않는다.

## Raw 결과

Raw는 다음 Git 제외 경로에 저장된다.

```text
runtime/raw/<source_id>/<document_role>/<UTC YYYY>/<MM>/<DD>/<document_id>.json
```

- `list_response`: 목록 HTTP body 전체
- `list_item`: 목록에서 분리한 항목
- `detail_response`: 상세 HTTP body 전체

실제 Raw는 검토 없이 Fixture나 커밋 대상으로 복사하지 않는다. 실패 시
Collector는 비밀값을 제외한 오류 분류만 출력하고 종료 코드 1을 반환한다.
429 또는 복지로 결과 코드 `22`는 재시도하지 않는다.

## 저장된 Runtime Raw 재처리

재처리는 Collector를 호출하지 않고 저장된 envelope만 다음 경계로 통과시킨다.

```text
runtime/raw
→ RawPolicyDocument load
→ source Extractor
→ Normalizer·Validator
→ valid·partial batch
→ Backend Import Service
→ PostgreSQL
```

전제 조건:

- Backend 의존성을 설치한 저장소 `.venv`를 사용한다.
- `DATABASE_URL` 대상 DB에 `alembic upgrade head`를 먼저 적용한다.
- URL이나 문서에 비밀번호를 넣지 않고 PostgreSQL pgpass 등 로컬 비밀 주입
  수단을 사용한다.
- 저장소 루트에서 명령을 실행한다.
- 실제 적재는 `collection_runs` Migration과 실행 이력을 사용하므로 반드시
  최신 Alembic head를 적용한다.

PSF3 이후 지역 code를 사용하는 Source를 적재하기 전에는 versioned 지역
기준정보도 같은 DB에 준비한다.

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -B -m app.cli.import_regions
Set-Location ..
```

반복 실행은 같은 값이면 unchanged이며, 같은 scheme의 DB 값이 잠긴 Seed와
다르면 덮어쓰지 않고 실패한다. PSF4부터 온통청년 5자리 `zipCd`는 승인된
exact crosswalk만 사용해 region rule을 생성한다. 미매핑·모호한 값과 폐지
code를 현행 지역으로 추정하거나 자동 치환하지 않는다.

PSF5부터 비어 있지 않은 region rule, 정책과 versioned search projection을
같은 transaction에 저장한다. 관계 또는 projection write 하나가 실패하면
accepted batch 전체를 rollback한다. Runtime replay는 Normalizer warning을
program과 함께 importer에 전달해 Source 변환 warning으로 분류한 partial을
재검증에서도 유지한다. 아래 `--dry-run`은 실제 FK·constraint·projection
write까지 수행한 뒤 rollback하므로 운영 DB에 Policy·rule·projection·실행
이력을 남기지 않는다.

온통청년 최신 Raw 회차를 검증만 하고 rollback:

```powershell
.\.venv\Scripts\python.exe -B scripts\import_runtime_data.py `
  --source youthcenter-api `
  --raw-root runtime/raw `
  --limit 5000 `
  --dry-run
```

실제 적재는 같은 명령에서 `--dry-run`만 제거한다. 복지로는 source를
`bokjiro-central-welfare-api`로 지정한다. 재현할 snapshot을 고정하려면
완료 출력의 ID를 `--snapshot-id`에 전달한다.

천안청년센터 저장 Raw도 같은 경로로 재처리한다. 이 명령은 외부 사이트를
다시 호출하지 않는다.

```powershell
.\.venv\Scripts\python.exe -B scripts\import_runtime_data.py `
  --source cheonan-youthcenter-web `
  --raw-root runtime/raw `
  --limit 1
```

경북 Runtime은 RYP3에서 지역·open을 통과한 후보가 있을 때 최신 온통청년·
복지로 snapshot manifest와 현재 PostgreSQL row를 읽기 전용 기준선으로 묶어
RYP4 교차 Source 판정을 수행한다.

```powershell
.\.venv\Scripts\python.exe -B scripts\import_runtime_data.py `
  --source regional-gyeongbuk-youth-platform `
  --raw-root runtime/raw `
  --limit 3 `
  --decision-root runtime/decisions
```

기준선 Source 하나라도 최신 완료 manifest나 유효 DB row가 없으면 open 지역
후보를 적재하지 않고 실패한다. 확정 중복과 review는 Importer에 전달하지 않고
비밀 없는 identity·match field·fingerprint를 Git 제외 decision manifest에
보존한다. 현재 closed인 후보만 있으면 RYP3에서 먼저 격리하므로 기준선을
불필요하게 요구하지 않는다.

부산도 같은 교차 Source Gate와 Runtime 명령을 사용한다.

```powershell
.\.venv\Scripts\python.exe -B scripts\import_runtime_data.py `
  --source regional-busan-youth-platform `
  --raw-root runtime/raw `
  --limit 3 `
  --decision-root runtime/decisions
```

서울은 승인된 in-app Browser action profile로 관찰한 JSON 파일만 다음 경계에서
가져온다. Importer는 Source ID, 목록·상세 allowlist, `plcyBizId`, 제목 일치,
최대 3건을 검증하고 원본 캡처 파일은 정식 Runtime Raw 저장 뒤 제거한다.

```powershell
.\.venv\Scripts\python.exe -B scripts\import_seoul_browser_capture.py `
  <browser-capture.json> --raw-root runtime/raw

.\.venv\Scripts\python.exe -B scripts\import_runtime_data.py `
  --source regional-seoul-youth-platform `
  --raw-root runtime/raw `
  --limit 3 `
  --decision-root runtime/decisions
```

Browser 캡처는 사람이 임의 작성하는 Seed가 아니며 실제 공개 목록·상세 DOM
관찰과 action trace를 담아야 한다. 계약 drift는 저장 전에 실패한다.

| 옵션 | 기본값 | 규칙 |
| --- | --- | --- |
| `--source` | 필수 | Runtime이 지원하는 여섯 source ID 중 하나 |
| `--raw-root` | `runtime/raw` | Git 제외 Runtime Raw root |
| `--limit` | `5000` | snapshot에서 처리할 list item 수, 1~5000 |
| `--snapshot-id` | 최신 완료 manifest | 특정 완료 snapshot ID |
| `--dry-run` | 꺼짐 | 실제 transaction을 수행한 뒤 rollback |
| `--decision-root` | `runtime/decisions` | 교차 Source 판정 manifest의 Git 제외 root |

### 회차와 품질 처리

- 완료 manifest가 있으면 기본적으로 source별 최신 manifest가 가리키는 모든
  `list_response`와 연결된 `list_item`을 하나의 회차로 처리한다.
- `--snapshot-id`를 지정하면 해당 manifest만 선택하고, 참조 Raw가 없거나
  item 수가 manifest와 다르거나 external ID가 중복이면 실패한다.
- detail은 manifest가 명시한 문서 중 선택된 item과 external ID가 같은
  문서만 결합한다.
- `--limit`은 item에 적용하며 부모 response와 detail은 제한 수에 포함하지
  않는다.
- 완료 manifest가 없는 기존 Fixture·과거 Raw는 호환을 위해 최신
  `list_response` 한 건과 그 자식 item·최신 detail 경계를 사용한다.
- 선택된 회차에 item이 없으면 과거 회차로 후퇴하지 않고 실패한다.
- valid·partial은 같은 source batch transaction으로 importer에 전달하고
  invalid는 DB transaction 전에 분리한다.
- DB write 하나가 실패하면 해당 accepted batch 전체를 rollback한다.
- 같은 Raw를 재실행하면 같은 `(source_id, external_id)`를 사용해
  `unchanged` 또는 명시적인 `updated`로 집계하며 중복 row를 만들지 않는다.

성공 요약은 source, Raw·추출·valid·partial·invalid·accepted·지역 제외·교차
Source 제외 수와
inserted·updated·unchanged·duplicate·skipped·rejected·failed 수만 출력한다. 실패
항목은 source ID, external ID, 안전한 오류 코드·경로·오류 타입과 기여 Raw
document ID만 출력하며 Raw payload, source URL query와 인증키를 출력하지
않는다.

지역·교차 Source 제외와 review는 CollectionRun `skipped_count`에 포함한다.
`duplicate_count`는 같은 Source의 `(source_id, external_id)` 반복만 의미한다.
교차 Source 정책 관계는 기존 aggregator row에 합성하거나 덮어쓰지 않는다.

실제 실행은 별도 `collection_runs` transaction에 `run_id`, source, 시작·종료
시각, 상태와 위 집계를 기록하고 CLI 요약에 `run_id`를 출력한다. 일부 invalid를
제외하고 accepted batch를 적재한 실행은 `partial_failure`, DB·검증·실행
실패는 `failed`다. 오류에는 예외 class 이름만 저장한다. `--dry-run`은 Policy와
실행 이력을 포함해 DB row를 남기지 않으며 요약의 `run_id`는 `None`이다.
필드 계약은
[CollectionRun 데이터베이스 계약](../architecture/collection_run_database.md)을
따른다.

`runtime/raw`가 없거나 선택한 source에 Raw가 없으면 DB를 변경하지 않고
명확한 오류와 종료 코드 1을 반환한다. `--dry-run`도 실제 DB upsert 결과를
계산하므로 연결 가능한 Migration 적용 DB가 필요하다.

## 테스트와 실제 호출 분리

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

위 테스트는 Mock HTTP Client와 임시 Raw root를 사용하며 외부 API를 호출하지
않는다. 실제 호출은 환경변수가 준비된 상태에서 `--source`를 지정한 CLI
명령을 별도로 실행할 때만 발생한다.

Runtime 재처리 자동 테스트는 `data/fixtures/raw`의 합성 API Raw와 검토된 합성
HTML을 사용하고 외부 Source를 호출하지 않는다. 운영 `runtime/raw`는 Git에
포함하지 않으며, 경로가 없는 환경의 smoke 결과를 성공적인 Runtime 적재로
기록하지 않는다.
