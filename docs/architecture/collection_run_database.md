# CollectionRun 데이터베이스 계약

## 목적과 범위

`collection_runs`는 향후 관리자 기능이 Seed 적재와 Runtime 재처리 결과를
조회할 수 있도록 실행 단위의 안전한 요약을 저장한다. 정책 데이터와 Raw
payload, 상세 실패 목록, URL과 인증정보는 저장하지 않는다.

CLI의 `seed_import`·`runtime_import`와 Celery worker의 `collection` 이력을 같은
원본에 기록한다. 관리자와 단일 Beat가 만든 실행은 Redis보다 먼저 PostgreSQL에
저장되며, Redis result backend는 운영 상태 원본으로 사용하지 않는다.

## 테이블 계약

| 필드 | PostgreSQL 타입 | null | 의미 |
| --- | --- | --- | --- |
| `run_id` | `UUID` | 불가 | 실행 식별자, primary key |
| `source_id` | `TEXT` | 가능 | source 단위 실행의 source ID. 여러 source가 섞인 Seed는 `null` |
| `run_type` | `collection_run_type` | 불가 | `seed_import`, `runtime_import`, `collection` |
| `trigger_type` | `collection_run_trigger_type` | 불가 | `cli`, `scheduler`, `admin` |
| `started_at` | `TIMESTAMPTZ` | 불가 | API·scheduler 접수 UTC 시각 |
| `finished_at` | `TIMESTAMPTZ` | 가능 | 종료 시각. `queued`·`running`에서만 `null` |
| `status` | `collection_run_status` | 불가 | `queued`, `running`, `succeeded`, `partial_failure`, `failed` |
| `is_complete_snapshot` | `BOOLEAN` | 불가 | Source 권위 범위를 완전히 순회하고 lifecycle complete 판정을 통과했는지. 기본 `false` |
| `requested_count` | `INTEGER` | 불가 | CLI가 요청한 최대 처리 수 또는 Seed 입력 수 |
| `raw_document_count` | `INTEGER` | 불가 | 선택한 Raw 문서 수 |
| `extracted_count` | `INTEGER` | 불가 | Extractor가 만든 항목 수 |
| `accepted_count` | `INTEGER` | 불가 | 검증과 identity admission을 통과한 수 |
| `partial_count` | `INTEGER` | 불가 | accepted 중 품질 상태가 `partial`인 수 |
| `invalid_count` | `INTEGER` | 불가 | 품질·Schema 검증에서 제외된 입력 수 |
| `duplicate_count` | `INTEGER` | 불가 | 실행 내 같은 source-scoped identity로 제외된 후속 후보 수 |
| `rejected_count` | `INTEGER` | 불가 | 검증 또는 identity admission에서 저장 대상에서 제외된 입력 수 |
| `inserted_count` | `INTEGER` | 불가 | 신규 정책 수 |
| `updated_count` | `INTEGER` | 불가 | 값이 바뀐 기존 정책 수 |
| `unchanged_count` | `INTEGER` | 불가 | 같은 값으로 재실행된 기존 정책 수 |
| `skipped_count` | `INTEGER` | 불가 | 기존 호환용 건너뜀 수. 현재 importer는 identity 거부에 사용하지 않음 |
| `failed_count` | `INTEGER` | 불가 | DB write 또는 실행 실패 수 |
| `error_type` | `VARCHAR(255)` | 가능 | 안전한 예외 class 이름. 오류 메시지는 저장하지 않음 |

모든 count는 0 이상이어야 한다. `finished_at`은 `started_at`보다 빠를 수 없고,
terminal 상태에는 종료 시각이 반드시 있어야 한다. `source_id`가 있다면 빈
문자열일 수 없다. 관리자 목록 조회를 고려해 `source_id`, `started_at`,
`status`에 index를 둔다. `source_id`별 `queued|running` row는 partial unique
index로 하나만 허용한다.

## 상태 판정

```text
enqueue
  → queued
  → running
      ├─ 전체 실행 성공 ─────────────→ succeeded
      ├─ 일부 invalid 제외 후 적재 ─→ partial_failure
      └─ 검증·DB·실행 실패 ─────────→ failed
```

- 품질이 `partial`인 정책은 허용된 데이터이므로 그 자체로 실행 실패가 아니다.
- `succeeded`는 제한 수집에도 가능하다. 공개 dataset promotion과 미발견 inactive는
  별도 `is_complete_snapshot=true` 증거까지 요구한다.
- 일반 관리자 수동 실행은 bounded preview이므로 항상 `false`다. 중앙 scheduler가
  complete mode로 새 snapshot manifest를 만들고 같은 snapshot ID 전체를 오류 없이
  import한 경우에만 `true`를 기록한다.
- Runtime에서 invalid 일부를 제외하고 accepted batch를 정상 적재하면
  `partial_failure`다.
- DB admission 거부, transaction 실패 또는 실행 예외는 `failed`다.
- terminal 상태를 다시 완료 처리할 수 없다.
- Celery task ID는 `run_id`와 같고 terminal task 재전달은 no-op이다.
- API race는 active Source partial unique index, 실제 worker 겹침은 PostgreSQL
  session advisory lock으로 차단한다.
- 프로세스 중단이나 이력 종료 write 실패로 `running`이 남을 수 있다. 후속
  관리자 기능은 이를 진행 중 또는 중단 확인 필요 상태로 구분해야 하며
  임의로 성공 처리하면 안 된다.

### 반복 품질 판정과 저장 경계

Importer 결과는 `inserted`, `updated`, `unchanged`, `duplicate`, `rejected`,
`failed`를 구분한다. `collected_at`·provenance만 달라진 입력은 business 변경이
아니므로 `unchanged`이며, 실행 내 같은 source-scoped identity는 첫 후보만
처리하고 이후 후보를 `duplicate`로 센다. 안전한 오류 단계는 `validate` 또는
`persist`와 exception class만 제공한다.

`invalid_count`는 Schema·품질 검증 실패만 세고, `rejected_count`는 invalid와
identity admission 거부를 포함해 저장 대상에서 제외된 전체 입력을 센다.
따라서 invalid는 rejected의 부분집합이며 두 수는 서로 더하지 않는다.
`duplicate_count`는 오류가 아닌 실행 내 중복 후보 수다. `skipped_count`는 기존
호환을 위해 유지하지만 현재 importer의 identity admission 거부에는 사용하지
않는다. Seed·Runtime CLI는 이 의미를 그대로 `collection_runs`에 영속한다.

## Transaction과 보안 경계

실행 이력의 시작·종료 write는 Policy import와 별도 session/transaction을
사용한다. 따라서 Policy batch가 rollback돼도 시작 또는 실패 이력은 남는다.
반대로 Policy commit 후 이력 종료 write가 실패할 수 있으므로 CLI는 이를
성공으로 숨기지 않고 실패 종료하며, 남은 `running` row가 운영 확인 지점이
된다.

`--dry-run`은 D4의 DB 변경 없음 계약을 유지하기 위해 실행 이력을 생성하지
않는다. 실제 실행만 `run_id`를 출력한다.

다음 값은 `collection_runs`에 저장하지 않는다.

- Raw payload와 원문 필드
- API key, 비밀번호와 credential
- source URL과 query
- DB 예외 메시지
- 항목별 오류 path와 상세 실패 목록

## Migration과 소비 경계

- CollectionRun 생성 revision: `20260730_0002`
- 반복 품질 count revision: `20260810_0005`
- queue 상태 revision: `20260824_0008`
- Source active singleton revision: `20260824_0009`
- 완전 snapshot 증거 revision: `20260824_0010`
- ORM: `app.models.collection_run.CollectionRun`
- write 경계: `app.services.collection_runs.CollectionRunWriter`

Backend 관리자 API는 인증된 Repository·Service와 별도 DTO를 통해서만 이
테이블을 조회한다. Frontend는 `202`를 성공 완료로 해석하지 않고 상세 조회의
terminal 상태를 기준으로 표시한다.
