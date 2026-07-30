# Backend Policy Runtime Safety Forest 개발 계획

## 계획 정보

- 번호: Backend 03
- 담당 영역: Backend
- 상태: draft
- 권장 브랜치: `fix/backend/policy-runtime-safety`
- 선행 Forest:
  [Backend Policy Persistence Hardening](02_policy_persistence_hardening.md),
  [Policy Data Database Integration](../integration/02_policy_data_database_integration.md)
- 대상 인계사항:
  `BE-POLICY-TIMESTAMP-ORDER`, `BE-SQL-ECHO-LOGGING`
- 개발 기록:
  구현을 시작해 `in-progress`로 전환할 때
  `docs/development/development_notes/backend/policy_runtime_safety.md`를
  생성한다.

## 목적

Policy 최초 적재와 갱신 시각의 순서 불변식을 확정하고, Backend DB engine의
개발 SQL logging이 정책 값·provenance·인증정보를 노출하지 않는 안전한
기본값을 갖도록 한다. SQLite 단위 환경과 실제 PostgreSQL 환경에서 같은
계약을 검증하고 두 Backend 인계사항을 종료한다.

## 범위

- Policy `created_at`·`updated_at` 생성 주체와 최초 insert 순서 계약
- unchanged·updated upsert의 `updated_at` 변경 규칙
- SQLite와 PostgreSQL의 timestamp 생성·반환 차이 검증
- Backend development engine의 SQL echo 활성화 조건
- 정책 본문·provenance·인증정보의 SQL parameter log 비노출
- Unicode 정책 값이 포함된 write에서 logging stream 오류 회귀 검증
- 관련 Backend·API·DB·개발 환경 문서와 인계 보드 동기화

## 범위 밖

- Normalized Schema, Fixture와 canonical Seed 변경
- Policy 공개 DTO의 필드 추가·삭제
- 일반 사용자 인증, 관리자 권한과 CollectionRun 관리자 API
- 운영 관측성 플랫폼, 중앙 로그 수집과 배포 설정 전반
- Collector·Normalizer와 Frontend 화면 변경

## 선행 조건

- 최신 `develop`의 Policy Migration·Importer·Repository 기준선을 사용한다.
- Windows `.venv`와 실제 PostgreSQL 테스트 DB 사용 방법을 먼저 확인한다.
- timestamp·logging 계약을 결정하기 전 임의의 default나 보정 시각을
  구현하지 않는다.
- 실제 PostgreSQL 검증이 불가능하면 SQLite 성공을 PostgreSQL 성공으로
  기록하지 않는다.

## 공통 설계 원칙

- 최초 insert 후 `updated_at < created_at`이 되지 않는 명시적 불변식을
  우선 검토한다.
- 시각 생성 주체는 DB 또는 application 중 하나의 일관된 경계를 선택하고,
  ORM·Migration·Importer·API 문서를 함께 맞춘다.
- unchanged upsert는 사용자 데이터와 `updated_at`을 불필요하게 변경하지
  않는다.
- 실제 update의 시각은 기존 값보다 감소하지 않아야 한다.
- SQL parameter와 비밀정보를 로그에 기록하지 않는 상태를 기본값으로 한다.
- 상세 SQL logging이 필요하면 명시적인 로컬 설정과 안전 경계를 요구한다.
- 로그 출력 자체의 encoding 오류가 DB transaction 결과를 왜곡하거나
  성공·실패 판정을 숨기지 않아야 한다.

## Slice 계획

### R0 - 현재 동작과 계약 확정

- 상태: draft
- 목적:
  timestamp와 SQL logging의 현재 생성·출력 경계를 실행 증거로 확정한다.
- 주요 작업:
  - Policy 모델, Migration과 Importer의 시각 생성 주체 대조
  - 최초 insert·unchanged·updated upsert 시각 재현
  - development·testing 환경별 engine echo 설정 대조
  - 정책 값·provenance와 Unicode 문자가 포함된 write log 재현
  - DB 소유 시각과 application 소유 시각 대안의 영향 비교
- 산출물:
  - 선택한 timestamp 불변식과 logging 기본값 결정
  - 재현 테스트 또는 검증 명령
- 선행 조건:
  - 실제 PostgreSQL 테스트 연결 가능
- 완료 기준:
  - SQLite·PostgreSQL의 현재 결과와 차이를 구분해 기록
  - `created_at`·`updated_at` 생성 주체와 허용 순서 합의
  - parameter logging 허용 범위와 기본값 합의

### R1 - Policy timestamp 순서 보장

- 상태: draft
- 목적:
  최초 insert와 후속 upsert에서 합의한 시각 불변식을 구현한다.
- 주요 작업:
  - 최초 insert의 `created_at`·`updated_at` 역전 방지
  - unchanged upsert의 `updated_at` 보존
  - 실제 update의 nondecreasing `updated_at` 보장
  - ORM·Migration·Importer 동기화 여부 확인
  - API timestamp 의미와 Frontend 영향 확인
- 산출물:
  - timestamp 구현과 단위·통합 테스트
  - 필요 시 DB·API 기준 문서 갱신
- 선행 조건:
  - R0 timestamp 계약 확정
- 완료 기준:
  - 최초 insert에서 `updated_at >= created_at`
  - unchanged 재실행에서 두 시각의 불필요한 변경 없음
  - 실제 update에서 `updated_at` 감소 없음
  - SQLite와 실제 PostgreSQL 검증 결과 기록

### R2 - SQL parameter logging 안전화

- 상태: draft
- 목적:
  Backend SQL logging의 안전한 기본값과 명시적인 디버그 경계를 구현한다.
- 주요 작업:
  - development engine의 기본 SQL echo 비활성화
  - 상세 logging을 위한 명시적 설정과 안전한 예시 정의
  - 정책 본문·provenance·인증정보의 parameter 비노출 테스트
  - Unicode 정책 값 write의 logging stream 오류 회귀 테스트
  - write 결과와 logging 실패의 관계 확인
- 산출물:
  - 설정·engine 변경과 보안 회귀 테스트
  - Backend 로컬 환경·운영 문서 갱신
- 선행 조건:
  - R0 logging 계약 확정
- 완료 기준:
  - 기본 실행 로그의 정책 값·provenance·인증정보 노출 0건
  - Unicode 정책 값 write에서 logging encoding 오류 0건
  - 전체 DB URL과 비밀번호가 오류·로그에 노출되지 않음

### R3 - 통합 검증과 인계 종료

- 상태: draft
- 목적:
  timestamp·logging 변경의 전체 회귀와 문서 동기화를 완료한다.
- 주요 작업:
  - 관련 Backend 단위·API 테스트
  - 실제 PostgreSQL insert·upsert 통합 테스트
  - Backend 전체 회귀
  - 문서·Fixture 결정성 검증
  - 권위 문서와 개발 기록 갱신
  - 완료 증거 기록 후 두 인계사항을 `docs/index.md`에서 제거
- 산출물:
  - 최종 검증 기록과 완료된 Forest 개발 기록
- 선행 조건:
  - R1·R2 완료
- 완료 기준:
  - 관련 테스트와 전체 Backend 회귀 통과
  - `python scripts/validate_docs.py` 통과
  - 문서와 실제 timestamp·logging 동작 일치
  - `BE-POLICY-TIMESTAMP-ORDER`, `BE-SQL-ECHO-LOGGING` 종료

## 검증 계획

- Policy 모델·Importer·Repository 단위 테스트
- logging 설정과 parameter 비노출 회귀 테스트
- 실제 PostgreSQL Migration → insert → unchanged → update 검증
- 관련 Backend API 테스트와 Backend 전체 회귀
- `python scripts/build_data_fixtures.py --check`
- `python scripts/validate_docs.py`
- `git diff --check`

실제 명령과 결과는 개발 기록에 기록하며 실행하지 않은 검증을 통과로
표현하지 않는다.

## Forest 완료 기준

- Policy timestamp 불변식이 코드·DB·API 문서에서 일치
- 기본 SQL logging의 정책 값·provenance·인증정보 노출 0건
- SQLite와 실제 PostgreSQL 관련 회귀 통과
- Schema·Fixture·Seed와 Frontend 영향 검토 완료
- 권위 문서와 개발 기록 동기화
- 두 대상 인계사항 제거

## 위험과 미확정 사항

- DB server default와 application 시각을 혼용하면 DB별 precision과 transaction
  timestamp 의미가 달라질 수 있다.
- 시각 생성 주체를 바꾸면 기존 Migration과 API 소비자의 timestamp 해석에
  영향이 생길 수 있다.
- SQL 문장 자체와 parameter 값을 분리하지 못하는 logging 설정은 안전한
  디버그 경계를 제공하기 어렵다.
- 보안 기본값과 상세 debugging 편의 사이의 선택은 Backend·운영 문서에서
  명시해야 한다.

## 관련 문서

- [Policy 데이터베이스 매핑](../../../architecture/policy_database_mapping.md)
- [Policy API 계약](../../../api/policies.md)
- [Backend Windows 로컬 환경](../../backend_local_setup.md)
- [Integration 개발 기록](../../development_notes/integration/policy_data_database_integration.md)
- [공동 확인 및 인계 보드](../../../index.md#공동-확인-및-인계-보드)
