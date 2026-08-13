# Collector 실행

## 현재 지원 소스

```text
youthcenter-api
bokjiro-central-welfare-api
cheonan-youthcenter-web
regional-gyeongbuk-youth-platform
regional-busan-youth-platform
```

서울과 RYP6의 Browser 구현 지역은 HTTP Collector 목록에는 없고, 검증된 실제
Browser 캡처를 Runtime Raw로 가져온 뒤 재처리 CLI에서 지원한다.

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

RYP6 공통 Browser capture는 단일 객체 또는 Source별 객체 배열을 받을 수 있다.
각 객체는 승인 목록 URL, `page`, `total_count` 또는 `null`, `has_next`, 한 page에서
관찰한 전체 `discovered_ids`, 최대 30개 action trace와 상세 최대 3건을 포함한다.
`discovered_ids`와 상세 batch를 분리해 아직 상세를 처리하지 않은 identity도
체크포인트의 pending 대상으로 보존한다. 호환 입력에서 `discovered_ids`가 없으면
상세 batch의 identity만 사용하므로 전체 pagination 실행에는 생략할 수 없다.
상세 identity와 제목이 다르거나 승인 URL 범위를 벗어나면 Raw를 저장하지 않는다.

전체 Browser 순회는 loopback capture endpoint의 `/discover`로 page 전체 identity를
먼저 저장하고 응답의 `pending_ids`만 상세 처리한다. 성공 상세은 `/capture`, 공식
상세 오류는 `/failure`로 기록한다. checkpoint `1.2.0`은 failed identity를 실제
상세 캡처로 간주하지 않지만 pending detail에서는 제외하므로 중단 뒤 같은 실패
요청을 반복하지 않는다. 서버는 `127.0.0.1`에만 bind하고 실행별 bearer token을
요구한다.

```powershell
.\.venv\Scripts\python.exe -B scripts\import_regional_browser_capture.py `
  <regional-browser-capture.json> `
  --raw-root runtime/raw `
  --checkpoint-root runtime/decisions/regional-checkpoints

.\.venv\Scripts\python.exe -B scripts\import_runtime_data.py `
  --source regional-incheon-youth-platform `
  --raw-root runtime/raw `
  --limit 3 `
  --decision-root runtime/decisions `
  --checkpoint-root runtime/decisions/regional-checkpoints
```

캡처 CLI는 Raw 저장과 함께 page·total·종료 상태와 전체 발견 identity를
Git 제외 체크포인트에 원자적으로 기록한다. 모든 page를 발견하는 동안 상세는
최대 3건씩 처리할 수 있지만 Forest 완료 전에는 모든 identity가
`accepted/duplicate/review/closed/failed` 중 하나로 판정돼야 한다. 알려진 목록
total보다 적은 발견·판정으로 종료하거나 이미 발견·판정한 identity를 다시
추가하면 실패한다. 저장이나 체크포인트 갱신이 실패하면 해당 호출이 새로 만든
Raw를 제거하며 기존 체크포인트는 유지한다.

RYP7 이후 공통 Browser 상세 캡처는 구조화 필드 값과 함께 라벨 관찰 상태를
기록한다. `value_extracted`는 라벨과 값이 모두 확인됨,
`label_present_value_empty`는 라벨은 있으나 원문 값이 비어 있음,
`label_not_found`는 현재 capture contract가 라벨을 찾지 못했음을 뜻한다. 마지막
상태를 원문 값 부재로 간주하지 않는다. 관찰 필드가 없는 과거 Raw는 계속
재생할 수 있지만 review 감사에서 `null_unverifiable`로 분류한다.

DB를 변경하지 않고 완료 checkpoint와 현재 regional replay의 review 사유·필드
coverage를 대조하려면 다음 명령을 사용한다.

```powershell
.\.venv\Scripts\python.exe scripts\audit_regional_reviews.py `
  --as-of 2026-08-13 `
  --raw-root runtime/raw `
  --checkpoint-root runtime/decisions/regional-checkpoints `
  --output runtime/decisions/regional-review-audit.json
```

checkpoint가 미완료이거나 replay identity가 다르면 실패한다. accepted·review·
closed outcome이 현재 regional Gate와 충돌해 DB projection에 영향을 줄 수
있어도 실패한다. 이미 미적재인 duplicate가 새 Gate에서 review로 바뀐 경우는
숨기지 않고 `checkpoint_decision_drift`로 집계한다. 보고서는 Git 제외 Runtime
경계에 원자적으로 작성되며 Raw payload를 포함하지 않는다.

RYP8 부산 replay는 목록 HTML의 `meta[name=author]`, `<title>`,
`select[name=endstat] option[selected]`을 Source scope locator로 보존하고 상세
`dtif_atc`·`dtif_cont` pair를 field observation으로 변환한다. Source scope는
RYP9 전까지 판정에 적용하지 않으므로 기존 checkpoint outcome과 DB는 유지된다.
limited actual은 다음처럼 목록·상세 각 1건만 요청할 수 있다.

```powershell
.\.venv\Scripts\python.exe -m collectors `
  --source regional-busan-youth-platform `
  --page 1 --limit 1 --detail-limit 1
```

RYP8 Browser 제한 재캡처는 loopback 서버의 `/recapture`를 사용한다. 이 경계는
새 identity를 발견하거나 checkpoint outcome을 바꾸지 않으며, 완료 checkpoint의
기존 `page`·identity·total과 일치할 때만 새 Raw를 저장한다. `recaptureIds`를
지정하면 현재 공식 목록에서 확인되는 선택 identity만 상세를 다시 관찰한다.
대구는 `.view_txt` 문단, 광주는 목록의 `policyView(policyId)` 클릭 상세를
사용한다. source scope는 Raw list response에 staging되지만 RYP9 전에는 Gate의
승격 근거로 소비하지 않는다.

현재 목록에 신규 identity만 추가되고 checkpoint identity의 누락이 없는 경우는
Source별 승인을 받은 뒤에만 `recaptureExcludedIds`로 current-only identity를
명시할 수 있다. 값은 비어 있지 않은 고유 문자열 목록이어야 하며 checkpoint
identity와 선택 `recaptureIds`에 겹치면 안 된다. 서버는 현재 total이
`checkpoint total + 제외 identity 수`와 정확히 같고, 재캡처 identity가 기존
captured 범위의 부분집합일 때만 저장한다. 이 예외는 신규 identity를 checkpoint에
추가하거나 outcome을 만들지 않으며, total 차이가 없거나 감소·교체 drift인
Source에는 사용할 수 없다. 대전은 current-only `CT_000000000042` 한 건을 이
방식으로 기록하고 기존 12건만 재캡처했다.

Browser navigation timeout은 실패 응답으로 단정하기 전에 요청한 URL의
origin·path·query와 Source별 준비 DOM이 이미 로드됐는지 확인한다. 둘 다
일치할 때만 현재 DOM으로 계속한다. 준비 selector는 locator wait 신호에
의존하지 않고 페이지 DOM을 최대 20초 polling하며, 어느 하나라도 다르면
timeout을 발생시킨다. 이 fallback은 전송 완료 신호만 보완하며 목록 total·
identity drift를 우회하지 않는다.

울산 화면의 total 596은 모든 page에 반복되는 고정 공지 `57904`를 제외한
일반 게시물 수다. 재캡처 경계의 effective total은 dedupe한 unique identity
597이며 완료 checkpoint와 순서까지 일치해야 한다. closed identity `37439`도
현재 목록에 있으므로 recapture scope에서 제외하지 않는다.

울산 상세는 카드 상태 badge `마감`, `접수전`, `접수일정 없음`을 실제 제목에서
분리한다. `.title_here`와 `#board_normal_view`가 요청 identity의 제목으로 두 번
연속 일치한 뒤에만 추출한다. 제목 mismatch·title timeout만 목록 context에서
한 번 재관찰하며 삭제·권한·다른 DOM 오류는 재시도하지 않는다. 이 PC처럼 연속
상세 navigation의 렌더 상태가 호출 사이에 남으면 identity마다 새 Browser tab을
열고 처리 직후 닫아 격리한다.

인천은 `지원내용` heading을 `지원규모`보다 우선하고 `지원대상·지원조건`을
결합한다. 전북은 `공고상세보기URL`을 공식 신청 channel로 관찰한다. 서울은
서울시 정책 89건의 `ctList.do` 18 page를 논리 page 1~18, 자치구 정책 21건의
`guList.do` 5 page를 논리 page 19~23으로 연결한다. 두 목록의 total·identity·
순서가 완료 checkpoint 110건과 모두 일치할 때만 review identity를 재캡처하며
closed identity는 기존 outcome 보존을 위해 제외한다. 상세는
`.policy-detail strong.title`과 `.policy-detail .form-table`이 준비된 뒤 구조화
`th`·`td`를 읽는다. 공식 `사업신청기간` 라벨의 빈 값은
`label_present_value_empty`, 원문에 없는 Source 지역 라벨은 `label_not_found`로
보존한다.

완료 checkpoint와 현재 공식 목록 identity가 교체된 Source는 상세 URL이 여전히
열리더라도 일반 `/recapture`로 저장하지 않는다. fixture·실제 DOM 대조까지만
수행하고 Source별 별도 재수집 승인을 받는다. 서울의 과거 교체 drift는
`2026-08-14` 전건 대조에서 추가·누락·순서 차이 0으로 해소된 것을 확인한 뒤
기존 checkpoint로 재개했다.

대구의 `checkpoint_detail_url` 모드는 추가 11·누락 8의 교체 drift에 대해 별도
승인된 예외다. 현재 목록을 checkpoint로 가장하지 않고, 기존 Raw list item의
상세 URL·제목으로 완료 checkpoint identity만 직접 재관찰한다. Browser runtime은
대구 공식 origin·detail path·`ap_seq`와 현재 `h4.v_tit` 제목을 검증하고, 서버는
대구 Source, page 1, 기존 total, `has_next=false`, 선택 `discovered_ids`와 detail
identity의 완전 일치, 기존 captured 부분집합을 모두 확인한다. 한 batch는 승인
예산과 같은 최대 3건이며 current-only identity, exclusion 목록, 다른 Source에는
사용할 수 없다. 분류 접두어는 기존 Raw 제목이 시작될 때까지만 제거해 제목 자체의
대괄호를 보존한다.

강원·제주의 기존 `failed` identity를 유형별 대표 표본으로 복구할 때만
`/recover`를 사용한다. 완료 checkpoint의 기존 total·page·identity와 일치하고
해당 outcome이 `failed`인 경우에만 Raw를 저장한다. 저장한 Raw를 같은 checkpoint
범위로 즉시 replay해 `review` 또는 `closed`가 확인되면 failed 결정을 교체한다.
replay가 identity를 누락하거나 `accepted`를 만들면 Raw와 checkpoint를 함께
되돌려 중복 기준선 없는 자동 승격을 막는다. 이 경계는 새 identity discovery,
다른 Source, enum·DB 변경에 사용할 수 없다.

강원 잔여 failed의 예지보전은 전체 재요청이 아니라 3구간 순환 canary로 한다.
`buildGangwonCanaryPlan(checkpoint, cycle)`이 2~10, 11~20, 21~29 page에서 실패
identity를 각 1건 고르고, `probeGangwonDetailCanary`가 공식 목록과 상세를 읽기
전용으로 확인한다. 호출 사이 최소 2초 간격을 지키며 canary 단계에서는 Raw,
checkpoint, DB를 쓰지 않는다. 세 건이 모두 `healthy`면 다음 회차에서 page와
identity를 순환한다. 하나라도 비정상이면 분류된 유형과 page 구간만 `/recover`
후보로 검토하고 자동 복구하지 않는다.

RYP8 데이터 완료 조건은 종료 이력·필드 상태·실패 원인·고정 outcome을 한 번에
감사한다. PowerShell의 native argument quote 제거를 피하려면 JSON 안의 큰따옴표를
백슬래시로 보존한다.

```powershell
$expectedOutcomes = '{\"accepted\":18,\"duplicate\":1,\"review\":1905,\"closed\":2360,\"failed\":322}'
& .\.venv\Scripts\python.exe scripts\audit_regional_ryp8.py `
  --raw-root runtime/raw `
  --checkpoint-root runtime/decisions/regional-checkpoints `
  --review-audit runtime/decisions/regional-review-audit.json `
  --expected-outcomes $expectedOutcomes `
  --output runtime/decisions/regional-ryp8-audit.json
```

`--max-legacy-null-slots`는 계획에서 승인된 수치가 있을 때만 지정한다. 생략하면
감사기는 임의 기준을 만들지 않고 `legacy_null_within_target=null`과
`data_ready=false`를 기록한다. 이 명령은 Raw·checkpoint·DB를 변경하지 않고
Git 제외 감사 보고서만 원자적으로 교체한다.

신청기간 필드에서 날짜가 하나만 추출되면 그 날짜를 신청 마감일로 판정한다.
as-of가 마감일을 지났으면 `application_period_ended`, 같거나 이전이면
`application_period_open`이다. 이는 `제출기한` 같은 명시적 신청기간 계열
라벨에서 추출된 값에 적용하며, `훈련기간`·행사일처럼 다른 의미의 날짜를
신청기간으로 mapping하는 근거는 아니다.

| 옵션 | 기본값 | 규칙 |
| --- | --- | --- |
| `--source` | 필수 | Runtime이 지원하는 16개 source ID 중 하나 |
| `--raw-root` | `runtime/raw` | Git 제외 Runtime Raw root |
| `--limit` | `5000` | snapshot에서 처리할 list item 수, 1~5000 |
| `--snapshot-id` | 최신 완료 manifest | 특정 완료 snapshot ID |
| `--dry-run` | 꺼짐 | 실제 transaction을 수행한 뒤 rollback |
| `--decision-root` | `runtime/decisions` | 교차 Source 판정 manifest의 Git 제외 root |
| `--checkpoint-root` | 없음 | 완료된 지역 checkpoint를 대조하고 accepted DB projection을 동기화 |

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
- 완료된 지역 checkpoint를 지정하면 accepted 결정 밖의 해당 Source 과거 row를
  같은 source identity 범위에서 제거한다. 미완료 checkpoint·다른 Source row는
  변경하지 않으며 요약의 `pruned`로 제거 수를 출력한다.

성공 요약은 source, Raw·추출·valid·partial·invalid·accepted·지역 제외·교차
Source 제외 수와
inserted·updated·unchanged·pruned·duplicate·skipped·rejected·failed 수만 출력한다. 실패
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
