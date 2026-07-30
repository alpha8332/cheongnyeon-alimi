# Backend Policy Runtime Safety Forest 개발 기록

## 작업 정보

- 기간: 2026-07-30
- 담당 영역: Backend
- 상태: in-progress
- 브랜치: `fix/backend/week2-hardening`
- 관련 계획:
  [Backend Policy Runtime Safety Forest 개발 계획](../../develop_plan/backend/03_policy_runtime_safety.md)
- 현재 Slice: R1 completed, R2 대기

## 목적

Policy 최초 insert와 후속 upsert의 `created_at`·`updated_at` 순서 불변식을
구현하고, Backend development SQL logging의 statement·parameter 출력
경계를 안전화한다.

## Forest 범위

- Policy 최초 insert·unchanged·update timestamp 생성 순서
- SQLite와 실제 PostgreSQL의 현재 write 동작
- development SQL echo의 statement·parameter 출력
- CP949 strict stream의 Unicode logging 오류
- R1 timestamp와 R2 logging 구현 계약
- 관련 계획·DB 매핑·인계 문서 동기화

Schema·Fixture·Seed·공개 DTO와 Frontend 화면은 범위 밖이다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| R0 | completed | SQLite·PostgreSQL timestamp와 development logging 경계 확정 |
| R1 | completed | timestamp 순서 구현과 SQLite·PostgreSQL 검증 완료 |
| R2 | draft | SQL parameter logging 안전화 |
| R3 | draft | 통합 검증과 인계 종료 |

## 구현 내용

### R0 확인 당시 timestamp 생성 주체

- Policy ORM의 `created_at`과 `updated_at`에는 Python `utc_now` default와
  DB `CURRENT_TIMESTAMP` server default가 모두 있다.
- 최초 Migration도 두 컬럼에 `CURRENT_TIMESTAMP` server default를 둔다.
- Seed·Runtime 공통 Importer는 write마다 Python
  `datetime.now(timezone.utc)`를 `updated_at`에만 넣고 `created_at`은
  전달하지 않는다.
- PostgreSQL upsert insert는 application `updated_at`을 먼저 만들고,
  SQLAlchemy가 statement 실행 직전에 ORM Python `created_at` default를
  별도로 평가한다. SQL log의 INSERT parameter에도 `created_at`이
  포함되므로 Migration의 DB server default는 이 경로에서 사용되지 않는다.
- portable SQLite insert도 application `updated_at` 생성 후 ORM
  `created_at` default를 실행한다.
- unchanged upsert는 두 시각을 보존한다.
- 실제 update는 `created_at`을 보존하고 새 application `updated_at`을
  저장하지만 시스템 시각 역행에 대한 별도 nondecreasing 보호는 없다.

### R1 timestamp 순서 구현

- Importer가 Policy write마다 `utc_now()`를 한 번만 호출하고 최초 insert의
  `created_at`·`updated_at`에 같은 UTC aware instant를 전달한다.
- unchanged upsert는 기존 두 시각을 그대로 보존한다.
- PostgreSQL upsert는 기존 값과 incoming 값의 `GREATEST`를 저장하고,
  portable SQLite 경계는 UTC로 정규화한 두 값 중 늦은 값을 저장한다.
- Importer의 명시적인 write instant를 ORM `onupdate`가 덮어쓰지 않도록
  `updated_at`의 암묵적 Python `onupdate`를 제거했다. 현재 Policy 변경
  writer는 Importer 하나이며 향후 writer도 `updated_at`을 명시해야 한다.
- ORM과 새 Migration에 `updated_at >= created_at` constraint를 추가했다.
- Migration은 constraint 추가 전에 기존 역전 행의 `updated_at`을
  `created_at`으로 보정한다. downgrade는 constraint만 제거하며 이미 보정된
  과거 시각을 원래 역전 값으로 복구하지 않는다.

### SQL logging 경계

- non-SQLite engine은 `environment == "development"`이면 SQLAlchemy
  `echo=True`로 생성된다.
- 기본 설정과 `.env.example`의 `ENVIRONMENT`는 `development`이므로
  기본 Web API engine과 Seed CLI의 global engine은 echo 대상이다.
- PostgreSQL 테스트는 `environment="test"`, Runtime import 전용 engine은
  `environment="runtime-import"`를 사용해 echo가 꺼진다.
- SQLite engine은 environment와 무관하게 echo option을 전달하지 않는다.
- `echo=True` 경계를 고정한 기존 단위 테스트는 있지만 parameter 비노출과
  Unicode logging stream 회귀 테스트는 없다.

## 검증 결과

### SQLite timestamp 재현

canonical Seed 첫 항목을 인메모리 SQLite에 insert → unchanged → title update
순서로 실행했다.

```text
first: inserted=1
updated_at - created_at = -0.007107 seconds
unchanged: created_at preserved=true, updated_at preserved=true
changed: updated=1, created_at preserved=true
changed updated_at - previous updated_at = 0.011870 seconds
changed updated_at >= created_at=true
```

SQLite는 `DateTime(timezone=True)` 조회값의 `tzinfo`를 보존하지 않았지만 기존
Importer 비교 함수가 naive 값을 UTC로 정규화한다. 최초 insert 역전은
timezone 표현 문제가 아니라 두 시각을 서로 다른 시점과 주체가 생성한
결과다.

### 관련 단위 테스트

다음 실제 파일을 대상으로 38건이 통과했다.

```text
backend/tests/test_database.py
backend/tests/test_policy_mapping_contract.py
backend/tests/test_policy_model.py
backend/tests/test_import_seed_cli.py
backend/tests/test_policies.py
```

Starlette TestClient의 `httpx` 사용 방식 deprecation 경고 1건은 R0 범위 밖
기존 경고다. 최초 진단 명령은 저장소 root `PYTHONPATH` 누락과 존재하지 않는
`test_seed_importer.py` 경로 지정으로 각각 중단됐고, 경계를 수정한 위 명령만
성공 결과로 기록한다.

### R1 timestamp 회귀

SQLite timestamp·constraint, Importer 매핑, Migration SQL을 포함한 R1 관련
테스트 33건이 통과했다. 전체 Backend 테스트에서는 PostgreSQL URL 없이
59건이 통과했고 PostgreSQL 전용 7건은 skip됐다.

PostgreSQL 18.4의 격리 DB에서 Migration 보정·constraint
upgrade/downgrade, PostgreSQL atomic upsert, Policy API 종단과 canonical
Seed 통합 테스트 7건이 통과했다. 다음 경계를 실제 DB에서 확인했다.

- 기존 `updated_at < created_at` 행을 `updated_at = created_at`으로 보정
- constraint 적용 후 역전 update 거부
- 최초 Importer insert의 `created_at == updated_at`
- 시스템 시각 역행 중 변경 update의 기존 `updated_at` 보존
- 시각 정상화 뒤 변경 update의 `updated_at` 증가
- Migration downgrade에서 constraint 제거

격리 DB는 테스트 후 삭제하고 존재하지 않음을 확인했다. Starlette
TestClient deprecation 경고 1건은 기존 범위 밖 경고다.

### PostgreSQL 관련 통합 테스트

별도 `cheongnyeon_alimi_r0_pytest_20260730_test` DB에서 다음 PostgreSQL
테스트 3건이 통과했다.

```text
backend/tests/test_postgresql_upsert.py
backend/tests/test_postgresql_end_to_end.py
```

Starlette TestClient deprecation 경고 1건만 남았다. 테스트 종료 후 격리 DB를
삭제하고 존재하지 않음을 확인했다.

### PostgreSQL 재현

기존 테스트 DB와 분리한 `cheongnyeon_alimi_r0_20260730_test`를 생성하고
PostgreSQL 18.4에서 Migration head를 적용한 뒤 canonical Seed 합성 항목을
insert → unchanged → title update 순서로 실행했다.

```text
first: inserted=1
updated_at - created_at = -0.049344 seconds
updated_at >= created_at=false
unchanged: created_at preserved=true, updated_at preserved=true
changed: updated=1, created_at preserved=true
changed updated_at >= previous updated_at=true
changed updated_at >= created_at=true
```

재현 후 격리 DB를 삭제하고 존재하지 않음을 확인했다. 실제 PostgreSQL에서도
최초 역전 원인은 DB server clock이 아니라 서로 다른 시점에 실행되는 두
Python timestamp 생성이다.

### PostgreSQL development logging 재현

같은 격리 DB에서 `environment="development"` engine으로 synthetic 정책을
적재했다. 실제 정책·운영 Raw·credential은 사용하지 않았다.

```text
development engine echo=true
synthetic policy title 노출=true
synthetic provenance raw_document_id 노출=true
parameter hidden marker=false
CP949 unencodable write=1
stderr UnicodeEncodeError=true
ASCII synthetic insert=1
Unicode synthetic insert=1
```

SQLAlchemy logging stream 오류와 DB transaction은 분리되어 Unicode log
오류가 발생해도 insert는 성공했다. 따라서 현재 logging은 민감 parameter
노출뿐 아니라 콘솔 오류가 실제 DB 결과를 오인하게 만드는 운영 위험이 있다.

## 설계 결정

### timestamp

R1은 Importer가 최초 insert에 사용할 하나의 UTC aware write instant를
생성해 `created_at`과 `updated_at`에 같이 전달하고, DB는
`updated_at >= created_at`을 검증하는 방식이다.

- 최초 insert: 두 시각은 같은 logical write instant
- unchanged: 두 시각 모두 보존
- update: `created_at` 보존, `updated_at`은 기존 값보다 감소하지 않음
- DB constraint: `updated_at >= created_at`을 ORM과 Migration에서 보호
- DB server default: Importer 밖의 누락 insert를 위한 방어적 fallback
- 기존 역전 row: constraint 적용 전에 `updated_at = created_at`으로
  안전하게 정규화하고 Migration upgrade·downgrade를 검증

DB가 두 시각을 전부 생성하는 대안은 PostgreSQL upsert와 portable SQLite
update의 시각 반환·precision 계약이 달라지고, 현재 Importer가 결과 집계와
업데이트 값을 application에서 구성하는 구조와 맞추기 위해 더 넓은 변경이
필요하다.

### SQL logging

R2는 `ENVIRONMENT=development`가 SQL echo를 자동 활성화하지 않게 하고,
별도의 명시적인 boolean 설정만 상세 SQL logging을 켜도록 하는 방식이다.
상세 logging을 허용해도 engine에는 parameter를 숨기는 설정을 항상 적용한다.

- 기본값: SQL echo off
- 명시적 debug: statement만 허용, bound parameter는 숨김
- 정책 본문·provenance·credential: 모든 환경에서 비노출
- Unicode 정책 값: parameter를 출력하지 않아 logging stream encoding과
  분리

## 계약 영향

- Normalized Schema, Fixture, Seed, null·빈 배열·enum 규칙은 변경하지 않는다.
- 공개 Policy DTO의 필드 집합과 타입은 변경하지 않는다.
- R1은 공개 필드의 타입·shape를 바꾸지 않고 timestamp 의미만 엄격하게
  만든다. Frontend는 기존 timezone-aware string을 그대로 소비할 수 있다.
- Migration은 기존 역전 행의 `updated_at`을 `created_at`으로 보정하므로
  해당 행의 공개 `updated_at` 값은 한 번 변경될 수 있다.
- R2 logging 변경은 API 응답과 Frontend 소비 계약에 영향이 없다.

## 주요 변경 파일

- `docs/development/develop_plan/README.md`
- `docs/development/develop_plan/backend/03_policy_runtime_safety.md`
- `docs/development/development_notes/README.md`
- `docs/development/development_notes/backend/policy_runtime_safety.md`
- `docs/architecture/policy_database_mapping.md`
- `docs/api/policies.md`
- `docs/index.md`
- `backend/app/models/policy.py`
- `backend/app/services/seed_importer.py`
- `backend/alembic/versions/20260730_0003_enforce_policy_timestamp_order.py`
- 관련 Backend 단위·PostgreSQL 테스트

## 남은 작업

- R2에서 명시적인 SQL echo 설정과 parameter 비노출 구현
- R3에서 전체 Backend·PostgreSQL 회귀와 두 인계사항 종료
