# Collector 실행

## 현재 지원 소스

```text
youthcenter-api
bokjiro-central-welfare-api
```

현재 Collector는 명시적 CLI 실행만 지원한다. 저장된 Runtime Raw는 별도
재처리 CLI로 추가 외부 호출 없이 PostgreSQL에 적재할 수 있다. Scheduler,
전체 수집과 자동 주기 적재는 구현하지 않았다.

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
| `--detail-limit` | `3` | 0~5 | 복지로 상세 요청 최대 수 |

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

성공 출력에는 source ID, 실제 요청 수, 항목·상세·Raw 문서 수만 포함된다.
요청 URL, query, 인증키, payload와 저장 파일명은 출력하지 않는다.

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

온통청년 최신 Raw 회차를 검증만 하고 rollback:

```powershell
.\.venv\Scripts\python.exe -B scripts\import_runtime_data.py `
  --source youthcenter-api `
  --raw-root runtime/raw `
  --limit 100 `
  --dry-run
```

실제 적재는 같은 명령에서 `--dry-run`만 제거한다. 복지로는 source를
`bokjiro-central-welfare-api`로 지정한다.

| 옵션 | 기본값 | 규칙 |
| --- | --- | --- |
| `--source` | 필수 | 현재 지원하는 두 source ID 중 하나 |
| `--raw-root` | `runtime/raw` | Git 제외 Runtime Raw root |
| `--limit` | `100` | 최신 회차에서 처리할 list item 수, 1~500 |
| `--dry-run` | 꺼짐 | 실제 transaction을 수행한 뒤 rollback |

### 회차와 품질 처리

- source별 가장 최신 `list_response` 한 건을 회차 경계로 사용한다.
- 해당 response를 `parent_document_id`로 참조하는 `list_item`만 처리한다.
- detail은 선택된 item과 external ID가 같고 목록 수집 시각 이후인 문서 중
  최신 한 건만 결합한다.
- `--limit`은 item에 적용하며 부모 response와 연결된 detail은 제한 수에
  포함하지 않는다.
- 최신 response에 item이 없으면 과거 회차로 후퇴하지 않고 실패한다.
- valid·partial은 같은 source batch transaction으로 importer에 전달하고
  invalid는 DB transaction 전에 분리한다.
- DB write 하나가 실패하면 해당 accepted batch 전체를 rollback한다.
- 같은 Raw를 재실행하면 같은 `(source_id, external_id)`를 사용해
  `unchanged` 또는 명시적인 `updated`로 집계하며 중복 row를 만들지 않는다.

성공 요약은 source, Raw·추출·valid·partial·invalid·accepted 수와
inserted·updated·unchanged·skipped·rejected·failed 수만 출력한다. 실패
항목은 source ID, external ID, 안전한 오류 코드·경로·오류 타입과 기여 Raw
document ID만 출력하며 Raw payload, source URL query와 인증키를 출력하지
않는다.

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

Runtime 재처리 자동 테스트는 `data/fixtures/raw`의 합성 Raw를 사용하고 외부
API를 호출하지 않는다. 운영 `runtime/raw`는 Git에 포함하지 않으며, 경로가
없는 환경의 smoke 결과를 성공적인 Runtime 적재로 기록하지 않는다.
