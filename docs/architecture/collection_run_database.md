# CollectionRun 데이터베이스 계약

## 목적과 범위

`collection_runs`는 향후 관리자 기능이 Seed 적재와 Runtime 재처리 결과를
조회할 수 있도록 실행 단위의 안전한 요약을 저장한다. 정책 데이터와 Raw
payload, 상세 실패 목록, URL과 인증정보는 저장하지 않는다.

현재 구현은 CLI가 생성하는 `seed_import`와 `runtime_import` 이력을 기록한다.
`collection`, `scheduler`, `admin` enum은 후속 Collector·Scheduler·관리자
기능이 같은 계약을 사용할 수 있도록 예약돼 있다. 관리자 실행 API, 인증,
목록·상세 API와 대시보드는 현재 구현 범위가 아니다.

## 테이블 계약

| 필드 | PostgreSQL 타입 | null | 의미 |
| --- | --- | --- | --- |
| `run_id` | `UUID` | 불가 | 실행 식별자, primary key |
| `source_id` | `TEXT` | 가능 | source 단위 실행의 source ID. 여러 source가 섞인 Seed는 `null` |
| `run_type` | `collection_run_type` | 불가 | `seed_import`, `runtime_import`, `collection` |
| `trigger_type` | `collection_run_trigger_type` | 불가 | `cli`, `scheduler`, `admin` |
| `started_at` | `TIMESTAMPTZ` | 불가 | 실행 시작 UTC 시각 |
| `finished_at` | `TIMESTAMPTZ` | 가능 | 종료 시각. `running`에서만 `null` |
| `status` | `collection_run_status` | 불가 | `running`, `succeeded`, `partial_failure`, `failed` |
| `requested_count` | `INTEGER` | 불가 | CLI가 요청한 최대 처리 수 또는 Seed 입력 수 |
| `raw_document_count` | `INTEGER` | 불가 | 선택한 Raw 문서 수 |
| `extracted_count` | `INTEGER` | 불가 | Extractor가 만든 항목 수 |
| `accepted_count` | `INTEGER` | 불가 | 검증과 identity admission을 통과한 수 |
| `partial_count` | `INTEGER` | 불가 | accepted 중 품질 상태가 `partial`인 수 |
| `invalid_count` | `INTEGER` | 불가 | 품질·Schema 검증에서 제외된 입력 수 |
| `inserted_count` | `INTEGER` | 불가 | 신규 정책 수 |
| `updated_count` | `INTEGER` | 불가 | 값이 바뀐 기존 정책 수 |
| `unchanged_count` | `INTEGER` | 불가 | 같은 값으로 재실행된 기존 정책 수 |
| `skipped_count` | `INTEGER` | 불가 | DB admission에서 건너뛴 입력 수 |
| `failed_count` | `INTEGER` | 불가 | DB write 또는 실행 실패 수 |
| `error_type` | `VARCHAR(255)` | 가능 | 안전한 예외 class 이름. 오류 메시지는 저장하지 않음 |

모든 count는 0 이상이어야 한다. `finished_at`은 `started_at`보다 빠를 수 없고,
terminal 상태에는 종료 시각이 반드시 있어야 한다. `source_id`가 있다면 빈
문자열일 수 없다. 관리자 목록 조회를 고려해 `source_id`, `started_at`,
`status`에 index를 둔다.

## 상태 판정

```text
start
  → running
      ├─ 전체 실행 성공 ─────────────→ succeeded
      ├─ 일부 invalid 제외 후 적재 ─→ partial_failure
      └─ 검증·DB·실행 실패 ─────────→ failed
```

- 품질이 `partial`인 정책은 허용된 데이터이므로 그 자체로 실행 실패가 아니다.
- Runtime에서 invalid 일부를 제외하고 accepted batch를 정상 적재하면
  `partial_failure`다.
- DB admission 거부, transaction 실패 또는 실행 예외는 `failed`다.
- terminal 상태를 다시 완료 처리할 수 없다.
- 프로세스 중단이나 이력 종료 write 실패로 `running`이 남을 수 있다. 후속
  관리자 기능은 이를 진행 중 또는 중단 확인 필요 상태로 구분해야 하며
  임의로 성공 처리하면 안 된다.

### DTL4-2A importer 판정과 DTL4-2B 저장 경계

Importer 결과는 `inserted`, `updated`, `unchanged`, `duplicate`, `rejected`,
`failed`를 구분한다. `collected_at`·provenance만 달라진 입력은 business 변경이
아니므로 `unchanged`이며, 실행 내 같은 source-scoped identity는 첫 후보만
처리하고 이후 후보를 `duplicate`로 센다. 안전한 오류 단계는 `validate` 또는
`persist`와 exception class만 제공한다.

현재 `collection_runs` 물리 테이블에는 `duplicate_count`와 `rejected_count`가
없어 두 집계를 아직 영속하지 않는다. 기존 `skipped_count`나 `invalid_count`로
의미를 바꿔 저장하지 않으며, 두 컬럼과 Migration·관리자 DTO 연결은 DTL4-2B
완료 조건이다.

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

- Alembic revision: `20260730_0002`
- ORM: `app.models.collection_run.CollectionRun`
- write 경계: `app.services.collection_runs.CollectionRunWriter`

향후 Backend 관리자 API는 이 테이블을 직접 외부 DTO로 노출하지 않고 인증된
Repository·Service 경계와 별도 응답 계약을 정의해야 한다. Frontend는 그
API 계약이 확정되기 전에 ORM enum이나 내부 필드를 독자 타입으로 고정하지
않는다.
