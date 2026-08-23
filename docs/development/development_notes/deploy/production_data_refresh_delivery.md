# Deploy 02 Production Data Refresh and Delivery 개발 기록

## 작업 정보

- 상태: in-progress
- 작업일: `2026-08-23`
- 담당 영역: Data, Team Leader - Integration·Deploy
- 계획: [Deploy 02 계획](../../develop_plan/deploy/02_production_data_refresh_delivery.md)
- 주차 계획: [6주차 Final Release](../../weekly_plan/week_06_final_release.md)
- 시작 SHA: `f838d4191cb5cc33c324d3e946c7a12ed8a56b1b`
- 현재 Gate: `W6-P0_DATASET_CONTRACT_PASS`

## 목적

API key와 로컬 DB dump 없이 배포 가능한 공개 normalized bootstrap 경계를
확정하고, Source·field allowlist와 versioned manifest를 실행 가능한 계약으로
구현한다.

## Forest 범위

- W6-P0 공개 데이터·라이선스 계약과 Runtime proof artifact
- W6-P1 정책 생명주기
- W6-P2 Celery·Redis 중앙 수집
- W6-P3 clone/ZIP 최초 실행
- W6-P4 Production Compose·CI/CD
- W6-P5 clean-room과 Final Gate

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| W6-P0 | completed | default-deny 계약, 451건 actual artifact·hash 재검증, `W6-P0_DATASET_CONTRACT_PASS` |
| W6-P1 | pending | 정책 생명주기 |
| W6-P2 | pending | Celery·Redis 중앙 수집 |
| W6-P3 | pending | clone/ZIP 최초 실행 |
| W6-P4 | pending | Production Compose·CI/CD |
| W6-P5 | pending | clean-room·Final Gate |

## 구현 내용

### Source·field 계약

- 실제 DB 16개 Source를 기존 inventory와 `2026-08-23` 공식 페이지로 대조했다.
- 복지로 중앙부처복지서비스만 `이용허락범위 제한 없음` 근거로 include했다.
- 온통청년·지역·천안·KOSAF·고용24 등은 약관 제한 또는 명시적 공개
  라이선스 부재로 제외했다.
- `NormalizedProgram 1.2.0` 필드 37개를 허용하고 DB 내부 ID·timestamp,
  Raw·dump·비밀·연락처를 금지했다.

### 생성·검증 도구

- allowlist Source만 읽는 `build_public_bootstrap_dataset.py`를 추가했다.
- PostgreSQL row를 현재 1.2.0 공개 Schema로 projection하고 각 레코드를
  Schema·Python model로 검증한다.
- dataset·Schema·Source contract SHA-256, row·byte 수와 Source attribution을
  manifest에 기록한다.
- 검증 모드는 DB 없이 artifact 변조·계약 drift·비허용 Source·연락처·비밀
  pattern을 다시 확인한다.
- 생성은 partial file 뒤 원자적 rename을 사용하고 Runtime output은 Git에서
  제외한다.

### Actual proof artifact

- Acceptance DB의 복지로 후보 461건을 읽었다.
- 자유 텍스트의 개인 휴대전화 형식 때문에 10건을 레코드 단위로 제외했다.
- 공개 artifact 451건, 1,247,899 bytes를 생성했다.
- SHA-256은
  `28c36be54ee859b63a496e2cea295d58ab88eb438ef1ffcce0b647198cf8ccb3`다.
- 별도 검증 모드가 같은 version·451건·SHA-256을 재확인했다.

## 주요 변경 파일

- `data/schema/public_policy_dataset_sources.schema.json`
- `data/schema/public_policy_dataset_manifest.schema.json`
- `data/schema/public_policy_dataset_pointer.schema.json`
- `data/reference/public_policy_dataset_sources.json`
- `scripts/build_public_bootstrap_dataset.py`
- `tests/test_public_bootstrap_dataset.py`
- `docs/data/public_policy_dataset.md`
- `.gitignore`

## 설계 결정

- 수집 가능과 공개 재배포 가능을 분리하고 default-deny로 판정한다.
- 실제 데이터는 Git에 넣지 않고 P4의 versioned GitHub Release asset으로만
  발행한다.
- Redis·Celery 도입 전에도 dataset 계약은 PostgreSQL·Source license를
  기준으로 독립 검증할 수 있어야 한다.
- 기존 DB 복지로 행은 `schema_version=1.1.0`이지만 현재 DB column에는 1.2.0
  필드가 모두 있다. 공개 projection에서 Schema version만 1.2.0으로 올리고
  `data_quality_status=partial`과 기존 값은 그대로 보존한다.
- 이메일·개인 휴대전화·기관 연락처가 발견된 레코드는 자동 마스킹하지 않고
  전체 제외한다.
- immutable versioned asset을 먼저 검증한 뒤 작은 latest pointer만 갱신하며
  실패 시 직전 pointer를 유지한다.

## 검증 결과

### 첫 실패와 보정

1. 임시 Docker run의 시스템 Python에 SQLAlchemy가 없어 import 전에 중단됐다.
   image의 `/opt/venv/bin/python`으로 실행 경계를 수정했다.
2. `.env.compose`에는 조합된 `DATABASE_URL`이 없어 argument 검증이 중단됐다.
   컨테이너 내부 비추적 DB 변수로 URL을 조합하고 값은 출력하지 않았다.
3. 실제 복지로 행이 1.1.0이라 1.2.0 Schema 검증이 fail-closed했다. 현재 DB
   필드를 1.2.0 projection으로 검증하되 품질 상태는 보존했다.
4. 개인 휴대전화 형식 10건이 발견돼 발행이 중단됐다. 레코드 단위 제외와
   manifest 제외 집계를 추가한 뒤 다시 생성했다.

### 통과 결과

| 검증 | 결과 |
| --- | --- |
| 신규 단위 테스트 | `4 tests`, PASS |
| Source contract | default exclude, include 1 Source, 37 allowed fields |
| actual 후보 | 461건 |
| 개인정보 보수 경계 | 10건 제외, 발행 artifact match count 0 |
| actual artifact | 451건, 1,247,899 bytes |
| artifact 재검증 | version·row·SHA-256 일치 |

## 남은 작업

1. W6-P1에서 lifecycle Migration과 complete·partial·failed inactive 경계를
   구현한다.
2. W6-P2에서 실제 Celery worker가 성공한 완전 수집만 dataset 후보로 넘긴다.
3. W6-P3·P4에서 pointer, GitHub Release upload와 promotion·rollback을
   구현하고 새 Git SHA로 artifact를 재생성한다.
4. 공개 제외 10건은 제공기관 연락처와 개인 연락처를 구분하는 승인 규칙이
   생기기 전까지 제외 상태를 유지한다.
