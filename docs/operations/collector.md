# Collector 실행

## 현재 지원 소스

```text
youthcenter-api
bokjiro-central-welfare-api
```

현재 Collector는 명시적 CLI 실행만 지원한다. Scheduler, 전체 수집과 운영 DB
적재는 구현하지 않았다.

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

## 테스트와 실제 호출 분리

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

위 테스트는 Mock HTTP Client와 임시 Raw root를 사용하며 외부 API를 호출하지
않는다. 실제 호출은 환경변수가 준비된 상태에서 `--source`를 지정한 CLI
명령을 별도로 실행할 때만 발생한다.
