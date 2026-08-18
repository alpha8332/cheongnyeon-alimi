# Integration 10 Review Admission and Deploy Handoff Forest 개발 계획

## 계획 정보

- 번호: Integration 10
- 담당 영역: Data, Backend, Frontend, Team Leader - Integration·Deploy
- 상태: completed
- 계획일: `2026-08-18`
- 작업 브랜치: `feature/integration/week-05-acceptance`
- 대상 Release: `v0.5.0` Acceptance 기준선과 `v1.0.0` 배포 기반
- 선행 상태: Integration 07 `W5-G1_PASS`
- 후속 Gate: [Deploy 01 `DOCKER_ACCEPTANCE_PASS`](../deploy/01_docker_acceptance_environment.md)
- 후속 단계: 독립 사용성 리뷰·QA, Integration 07 `W5-G2`

## 계획 작성 환경과 사실 경계

이 계획은 실제 PostgreSQL과 최신 `runtime/`이 없는 회사 PC에서 작성했다.
따라서 저장소 문서에 기록된 과거 DB 건수, review 건수와 Source별 분포를
현재 값으로 사용하지 않는다. 계획 작성 중 실제 DB 조회, Runtime replay,
review 표본 판정과 외부 Source 재호출은 수행하지 않았다.

구현을 시작하는 DB 보유 PC에서 같은 시점의 Git, PostgreSQL, Runtime Raw,
checkpoint와 decision을 다시 확인한 결과만 이 Forest의 실제 입력으로 사용한다.
기존 `W5-G1_PASS` 수치는 당시 인수 기록으로 보존하되 새 데이터 기준선의
통과 근거로 재사용하지 않는다.

## 문제 정의

현재 지역 정책 Gate는 지역 근거와 신청 가능 상태를 모두 확정한 후보만
`accepted_policy`로 만들어 Importer에 전달한다. 불명확한 필드가 있는 후보는
review 결정과 Raw에 남지만 사용자 Policy DB에는 적재되지 않는다. 이 경계가
안전성은 높였으나, 불확실한 부가 조건과 게시 가능성까지 하나의 탈락 조건으로
묶으면 실제 서비스에 노출되는 정책이 지나치게 적어질 수 있다.

이번 Forest는 다음 두 질문을 분리한다.

1. 이 후보를 공식 정책으로 식별하고 사용자에게 출처와 함께 보여줄 수 있는가?
2. 지역, 신청기간, 나이, 소득 등 모든 신청 조건을 확정할 수 있는가?

첫 번째는 충족하지만 두 번째가 일부 미확정인 후보는 검증된 근거만 저장한
`partial` Policy로 승격할 수 있다. 공식성·identity·현재성·청년 대상 여부가
확인되지 않는 후보는 review에 남긴다.

## 목적

1. DB 보유 PC의 최신 DB와 Runtime을 읽기 전용으로 감사해 review 실제 분포와
   원인을 고정한다.
2. versioned admission 규칙으로 review를 `promote_partial`, `hold_review`,
   `exclude`로 결정적으로 분류한다.
3. 승인된 `promote_partial`만 기존 Normalizer·Importer transaction을 통해
   실제 PostgreSQL에 반영한다.
4. 동일 입력 재실행이 `unchanged`이며 closed·duplicate·invalid·failed 후보가
   승격되지 않음을 검증한다.
5. 재판정이 끝난 DB와 manifest를 Deploy 01 입력으로 동결한다.
6. Deploy 01이 같은 snapshot version을 각자의 격리된 Volume에서 재현할 수
   있게 인계 계약과 Gate 순서를 고정한다.

## 범위

- 최신 DB·Runtime의 읽기 전용 inventory와 변경 전 backup
- review 사유 감사, 표본 대조와 versioned admission 규칙
- 승인 partial의 기존 Importer 기반 PostgreSQL 적재와 재실행
- 새 데이터 기준 DB·API·Frontend actual 회귀
- post-admission snapshot manifest와 Deploy 01 입력 인계
- Deploy 01 `DOCKER_ACCEPTANCE_PASS` 뒤 DTL5-5 시작 여부 판정

## 범위 밖

- 회사 PC의 오래된 DB·Runtime 또는 문서 수치로 실제 admission 결과를 결정
- review 전체를 일괄 승인하거나 목표 row 수를 맞추기 위해 조건을 완화
- 수동 SQL `INSERT`·`UPDATE`로 Importer와 decision 이력을 우회
- 실제 DB dump, Runtime Raw, 비밀번호나 API key를 Git 또는 이미지에 포함
- 개인 PC의 PostgreSQL `5432`를 인터넷·사내망에 직접 공개
- Nginx, TLS, 도메인, registry와 운영 배포 완료
- blocked/rejected Source를 재승인 없이 다시 수집
- `closed`, 확정 duplicate, schema invalid와 failed 후보를 partial로 승격

## 선행 조건

- DB 보유 PC에서 현재 작업 브랜치와 최신 Runtime에 접근할 수 있어야 한다.
- 실제 DB 자격증명이 노출된 적이 있다면 먼저 교체해야 한다.
- PostgreSQL client의 `pg_dump`, `pg_restore`, `psql`과 repository `.venv`가
  실행 가능해야 한다.
- Raw·checkpoint·decision과 DB backup을 둘 Git 밖의 안전한 저장 공간이
  있어야 한다.
- Docker Desktop 또는 동등한 Docker Engine·Compose 사용이 해당 PC 정책상
  허용돼야 한다.
- Data, Backend, Frontend와 Integration의 변경 경계와 독립 QA 역할을 유지한다.

## Slice 계획

### 결과 구조

```text
DB 보유 PC의 최신 Git·DB·Runtime
  → RA0 읽기 전용 inventory와 변경 전 backup
  → RA1 review 사유·표본 감사와 규칙 입력 확정
  → RA2 versioned admission 구현·fixture·dry-run
  → RA3 승인된 partial만 transaction 적재·재실행
  → RA4 DB/API/Browser 회귀와 새 Acceptance 기준선
  → Deploy 01 DEP0~DEP5 snapshot·Docker·clean-room Acceptance
  → DOCKER_ACCEPTANCE_PASS
  → 독립 사용성 리뷰·QA
```

RA 단계 중 하나라도 실패하면 Deploy 01에 snapshot을 인계하지 않는다.
`DOCKER_ACCEPTANCE_PASS` 전에는 새 데이터 기준으로 독립 사용성 리뷰·QA를
시작하지 않는다.

## 공통 설계 원칙

### Admission v1 계약

### 공통 필수 조건

`promote_partial` 후보는 다음 조건을 모두 만족해야 한다.

- 실행 시점에 승인 상태인 공식 Source
- 비어 있지 않고 Source 범위에서 안정적인 `(source_id, external_id)`
- 비어 있지 않은 제목과 query credential이 제거된 공식 `source_url`
- 선택한 list/detail Raw와 연결되는 provenance
- Normalizer 결과가 `valid` 또는 `partial`; `invalid`가 아님
- 정책이 청년 대상임을 보여주는 item-level 원문 또는 승인된 청년 taxonomy와
  item-level 대상·시행기관 근거의 조합
- 명시적 마감·신청 종료·현재가 아닌 일정이 없음
- exact identity·canonical URL·승인 fingerprint 기준의 확정 duplicate가 아님
- Source별 완료 checkpoint와 replay identity가 일치함

### 현재성 조건

다음 중 하나를 만족해야 현재 게시 가능한 후보로 본다.

- 상세 원문에서 실행 기준일에 `open`임을 판정할 수 있음
- 승인된 공식 목록이 접수중·모집중만 반환하고, 같은 list Raw provenance와
  item identity가 있으며, 캡처가 실행 기준일로부터 7일 이내임
- Source 계약에 7일보다 짧은 freshness가 이미 있으면 더 짧은 값을 적용

기간이 없다는 이유만으로 신청 상태를 생성하지 않는다. 접수중 목록 근거가
있으면 `application_status=open`과 근거 code를 저장할 수 있지만 시작·종료일은
원문에 없으면 `null`로 둔다. 접수중 근거도 없으면 `hold_review`다.

### 청년 대상 taxonomy v2

정책 단위 제목·대상·자격 원문에 다음 값이 명시되면 청년 대상 조건을 충족한
것으로 본다.

- 기존 직접 표지: `청년`, `청소년`, `대학생`
- 가족·생애단계 표지: `신혼부부`, `예비신혼부부`
- 청년 부모 표지: `미혼모`, `미혼부`, `청소년부모`
- 돌봄·자립 표지: `가족돌봄청년`, `가족돌봄청소년`, `영케어러`,
  `자립준비청년`, `보호종료아동`
- 취약·전환 표지: `고립청년`, `은둔청년`, `학교밖청소년`,
  `가정밖청소년`, `쉼터퇴소청소년`, `경계선지능청년`, `장애청년`,
  `저소득청년`, `주거취약청년`, `다문화청년`, `탈북청년`, `니트청년`,
  `구직단념청년`, `장기미취업청년`, `전입청년`, `지역정착청년`
- 취업·교육 표지: `취업준비생`, `구직자`, `미취업자`, `졸업생`,
  `졸업예정자`, `대학원생`, `학자금`, `장학생`, `사회초년생`, `신입사원`
- 가구·창업·농업 표지: `1인가구`, `예비창업자`, `초기창업`, `스타트업`,
  `귀농`, `후계농`, `청년농업인`, `청년창업자`
- 세대·병역 표지: `2030세대`, `ROTC`, `학군사관후보생`, `사관후보생`,
  `군복무`, `전역자`, `전역청년`

이 taxonomy는 청년 대상 조건 한 가지만 충족한다. 공식 Source·identity,
현재성, 지역 근거와 duplicate 조건은 별도로 통과해야 한다. `신혼`, `미혼모`
등이 있어도 나이·소득·세부 자격을 생성하지 않고 원문에 없으면 `partial`의
미확정 조건으로 남긴다.

공백·가운뎃점·괄호 차이는 정규화하되 다른 단어로 추론하지 않는다. 특히
`2030세대`와 공백 변형만 세대 표지로 인정하고 단순 연도 `2030년`은 인정하지
않는다. `가구`, `부모`, 일반 `한부모`, `학생`, `기업`, `농업인`처럼 위
taxonomy에 없는 상위 표현만으로는 청년 대상을 확정하지 않는다. 포털 이름이나
Source scope만으로 정책 단위 청년 대상을 대신하지 않는다.

taxonomy v2는 완료 checkpoint를 만든 기존 regional producer의 판정을 소급해
바꾸지 않는다. RA2의 versioned admission 규칙과 fixture에서 적용하고, 기존
checkpoint outcome·Raw replay를 입력으로 보존한다.

### 지역 조건

지역 Source 후보는 다음 중 하나를 충족해야 한다.

- 정책 단위 지역·거주·활동 조건이 canonical 관할과 일치
- 정책 단위 시행기관이 canonical 관할과 일치하고 대상 원문에도 같은 관할의
  거주·활동 근거가 있음
- 승인된 Source 관할·운영 scope와 정책 단위 대상 또는 시행기관 근거가 함께
  있고 두 provenance가 같은 후보에 연결됨

포털 이름이나 접속 위치만으로 지역을 추론하지 않는다. 동명 시군구처럼
상위 지역이 불명확하거나 서로 다른 지역 근거가 충돌하면 `hold_review`다.

### partial 허용 필드

공통 필수·현재성·지역 조건을 통과한 뒤 다음 필드가 미확정인 것은 전체 정책을
제외하지 않는다.

- 정확한 신청 시작일·종료일
- 세부 나이 범위
- 소득·취업·교육 조건
- 우대·제외 조건
- 필요 서류
- 지원 규모의 구조화 값

미확정 필드는 임의 값으로 채우지 않고 `null`, 빈 배열과
`eligibility_summary.unknowns`에 원문 근거 code로 보존한다. 하나라도 미확정이면
`data_quality_status=partial`이며 API와 UI가 확정 자격으로 표현하지 않아야 한다.

### 보류와 제외

| 판정 | 조건 | DB Policy 영향 |
| --- | --- | --- |
| `promote_partial` | 공통 필수·현재성·지역 조건 통과, 부가 조건 일부 미확정 | 기존 Importer로 insert/update |
| `hold_review` | 청년 대상·현재성·지역 중 하나가 불확실하거나 duplicate 후보 충돌 | Policy 변경 없음 |
| `exclude_closed` | 명시적 종료 또는 실행 기준일보다 지난 마감 | Policy 변경 없음 |
| `exclude_duplicate` | identity·URL·fingerprint로 확정된 중복 | Policy 변경 없음 |
| `exclude_invalid` | Schema invalid, provenance·identity·URL 필수값 누락 | Policy 변경 없음 |
| `exclude_failed` | 수집·추출·DB admission 실패 | Policy 변경 없음 |

`예산 소진 시까지`만 있고 현재 접수중 근거가 없는 후보, 청년 대상 여부가
확인되지 않는 후보와 상위 지역이 불명확한 후보는 `hold_review`다.

## RA0 - DB 보유 PC 기준선과 변경 전 보호

### 사전 확인

저장소 루트에서 다음을 실행하고 결과를 개발 기록에 남긴다.

```powershell
git status --short --branch
git rev-parse HEAD
git rev-parse origin/feature/integration/week-05-acceptance
.\.venv\Scripts\python.exe --version
docker version
docker compose version
```

다음을 실제 값으로 기록하되 계획 문서의 과거 수치와 일치하도록 만들지 않는다.

- Git SHA와 dirty/untracked 상태
- PostgreSQL server version
- repository Alembic head와 actual `alembic_version`
- `policies` 전체·Source별·`data_quality_status`·`application_status` 집계
- 최신 `collection_runs` Source별 terminal 상태와 집계
- Runtime Raw, 완료 manifest, regional checkpoint와 decision 파일 수·최신 시각
- review audit 대상 Source와 현재 replay 가능 여부
- DB dump와 Runtime archive를 둘 디스크 여유 공간

DB URL에는 비밀번호를 넣지 않고 기존 `PGPASSFILE` 또는 동등한 로컬 비밀
주입을 사용한다. 실제 자격증명이 과거에 노출됐다면 inventory 전에 교체하고
교체 사실만 기록한다.

### 변경 전 backup

실제 적재 전에 custom-format dump를 workspace 밖의 명시적 backup 디렉터리에
생성한다.

```powershell
pg_dump --format=custom --no-owner --no-acl `
  --file <absolute-backup-dir>\pre-review-admission.dump `
  --dbname <credential-free-database-url>
Get-FileHash -Algorithm SHA256 `
  <absolute-backup-dir>\pre-review-admission.dump
```

Runtime은 `runtime/raw`, 완료 snapshot manifest, `runtime/decisions`와
checkpoint만 승인된 암호화 저장소에 별도 보존한다. API key, `.env`, pgpass,
Browser profile, 로그와 임시 캡처는 archive에서 제외한다.

### RA0 Gate

- actual DB와 repository Migration 불일치가 없음
- 완료 checkpoint가 참조하는 Raw가 모두 존재함
- 변경 전 dump의 SHA-256과 restore 대상 PostgreSQL major version이 기록됨
- 원본 DB를 삭제·덮어쓰지 않는 복구 경로가 있음
- 하나라도 불명확하면 `RA0_BLOCKED`; replay와 적재를 시작하지 않음

## RA1 - 최신 review inventory와 승인 표본

### 읽기 전용 감사

실행 날짜를 실제 `YYYY-MM-DD`로 지정한다.

```powershell
.\.venv\Scripts\python.exe scripts\audit_regional_reviews.py `
  --as-of <YYYY-MM-DD> `
  --raw-root runtime/raw `
  --checkpoint-root runtime/decisions/regional-checkpoints `
  --output runtime/decisions/regional-review-audit.json

.\.venv\Scripts\python.exe scripts\audit_regional_ryp9.py `
  --raw-root runtime/raw `
  --checkpoint-root runtime/decisions/regional-checkpoints `
  --output runtime/decisions/regional-ryp9-audit.json
```

regional audit schema `1.1.0`은 Source×reason code별 최대 20개의 정렬된
`external_id` 표본을 제공한다. cross-source duplicate producer는 최신 manifest의
`duplicate_review_required`를 별도로 합쳐 전체 review inventory를 만든다. RA2의
`audit_review_admission.py`는 이 두 입력과 admission v1 dry-run을 하나의
결정적 manifest로 통합한다. 보고서에는 Raw 본문 대신 identity, Source,
reason code, field observation, provenance ID와 현재 checkpoint outcome만 넣는다.

### 표본 선정

- Source × 주 reason code별 최대 20건을 결정적 정렬로 선택
- 후보가 20건 이하면 전건 확인
- duplicate 충돌, 지역 충돌, 청년 대상 미확인은 전건 또는 별도 high-risk 표본
- 공식 페이지 재확인은 robots·이용 조건과 기존 요청 예산 안에서만 수행
- 현재 페이지 drift를 과거 checkpoint에 조용히 편입하지 않음

표본 판정은 `promote_partial`, `hold_review`, `exclude`와 근거를 기록한다.
표본 통과율을 전체 건수로 단순 외삽하지 않고 규칙이 전체 Raw replay에 적용된
dry-run 결과를 RA2에서 따로 계산한다.

### RA1 Gate

- 모든 review producer와 reason code가 inventory에 나타남
- checkpoint drift, Raw 누락과 재수집 필요 항목이 분리됨
- Admission v1 Boolean 조건으로 판정할 수 없는 새 사유는 규칙을 먼저 보완
- 목표 row 수가 아니라 근거 충족 여부로 표본 승인

## RA2 - 결정적 admission 구현과 dry-run

상태: completed·RA3 재검증 (`RA2_PASS`, 2026-08-19). `review-admission-v1`과
taxonomy `2.0.0`을 기존 producer와 분리해 구현했다. RA3 사전 검증에서
checkpoint의 과거 `open`을 그대로 사용하고 canonical region을 물질화하지 않은
결함을 찾아 실행 기준일의 regional Gate를 다시 적용했다. 최종 review 1,140건은
`promote_partial` 3·`hold_review` 1,071·`exclude_closed` 66건이며, 변경 전 dump를
복원한 PostgreSQL 18 scratch DB에서 3건의 insert·재실행 unchanged·rollback을
검증했다.

### 계획된 변경 파일

```text
collectors/review_admission.py
scripts/audit_review_admission.py
scripts/apply_review_admission.py
data/schema/review_admission_audit.schema.json
data/fixtures/contracts/review_admission_cases.json
tests/test_review_admission.py
tests/integration/test_review_admission_to_database.py
docs/data/review_admission_rules.md
docs/operations/collector.md
```

실제 구현 중 기존 구조로 충분한 파일은 새로 만들지 않고 기존 regional Gate와
Runtime importer를 확장할 수 있다. 다만 audit와 apply는 별도 명령으로 유지해
읽기 전용 판정과 DB 변경을 혼동하지 않는다.

### audit 출력 계약

- `rule_version`, Git SHA, 실행 기준일
- DB Migration revision과 입력 checkpoint hash
- Source별 review·승격·보류·제외 수
- reason code 원본과 최종 admission reason
- 승격 identity 목록과 residual unknown code
- blocker, drift와 Raw 누락
- Raw payload·credential·개인 연락처 없음

### dry-run

```powershell
.\.venv\Scripts\python.exe scripts\audit_review_admission.py `
  --as-of <YYYY-MM-DD> `
  --raw-root runtime/raw `
  --checkpoint-root runtime/decisions/regional-checkpoints `
  --decision-root runtime/decisions `
  --output runtime/decisions/review-admission-v1.json

.\.venv\Scripts\python.exe scripts\apply_review_admission.py `
  --manifest runtime/decisions/review-admission-v1.json `
  --dry-run
```

`--dry-run`은 서비스 DB가 아니라 변경 전 dump에서 만든 전용
`cheongnyeon_alimi_admission_test` 또는 동등한 scratch DB에서 실행한다. 실제 DB
constraint, region rule과 search projection write를 수행한 뒤 transaction 전체를
rollback해야 한다. scratch DB 이름·연결 대상이 허용값이 아니면 fail-closed하고,
audit hash와 apply 입력 hash가 다르면 실패한다.

### 필수 fixture

- 신청기간만 없고 현재 접수중 list scope가 있는 청년 지역 정책 → partial 승격
- 신청기간과 현재성 근거가 모두 없음 → review 유지
- 청년 대상 부가 조건만 미확정 → partial 승격·unknown 보존
- 청년 대상 여부 자체가 미확정 → review 유지
- 동명 시군구 상위 지역 불명 → review 유지
- 명시적 마감 → closed 제외
- 예산 소진 여부 불명 → review 유지
- exact·URL·fingerprint 확정 중복 → duplicate 제외
- Source scope만 있고 item-level 근거 없음 → review 유지
- invalid·provenance 누락·identity 누락 → 실패 또는 제외
- 같은 manifest 두 번 적용 → 두 번째 unchanged

### RA2 Gate

- fixture와 전체 단위 테스트 통과
- dry-run 승격 후보의 hard exclusion 0건
- 승격 후보 전건에 identity·URL·provenance·현재성·청년 근거 존재
- dry-run이 서비스 DB·Runtime decision·checkpoint를 변경하지 않음
- actual 수치와 표본 근거를 사람이 대조한 뒤에만 apply 승인

## RA3 - 실제 적재와 재실행

상태: completed (`RA3_PASS`, 2026-08-19). 최종 manifest
`d6d781aaefa41e12a73d6f868fd5f291e83dc41e7930382441467795e9f4fdad`의 3건만
Source별 transaction으로 적재했다. 첫 실행은 `inserted 3`, 두 번째 동일
manifest 실행은 `unchanged 3`이며 Policy는 3,270건에서 3,273건이 됐다.

### 적용 원칙

- 확정한 동일 manifest를 사용하고 중간에 최신 데이터를 다시 섞지 않음
- 직접 SQL이 아니라 기존 Normalizer·Importer·region/search projection transaction 사용
- Source 단위 transaction과 CollectionRun 집계를 남김
- 한 Source 실패 시 해당 Source 승격 batch 전체 rollback
- 기존 review·closed·duplicate decision history를 삭제하지 않음

```powershell
.\.venv\Scripts\python.exe scripts\apply_review_admission.py `
  --manifest runtime/decisions/review-admission-v1.json `
  --apply

.\.venv\Scripts\python.exe scripts\apply_review_admission.py `
  --manifest runtime/decisions/review-admission-v1.json `
  --apply
```

첫 실행은 manifest 예상 `inserted`, `updated`, `unchanged`와 일치해야 한다.
두 번째 실행은 승격 대상 전부 `unchanged`, `inserted=0`, `updated=0`,
`pruned=0`, `failed=0`이어야 한다.

### RA3 Gate

- DB 증감이 manifest 승격·update와 정확히 일치
- closed·duplicate·invalid·failed Policy 신규 row 0건
- 승격 `valid`·`partial`의 확정·미확정 필드가 각각 계약대로 보존됨
- DB와 checkpoint/decision identity 불일치 0건
- 실패 시 원본 DB를 파괴하지 않고 pre-admission dump를 새 DB에 restore해 비교 가능

## RA4 - 새 데이터 기준선 인수

상태: completed (`2026-08-19`, `REVIEW_ADMISSION_PASS`,
`W5-G1_REVALIDATED`). 전체 회귀와 실제 API·Browser에서 추천의 지역·마감 혼입을
발견해 3값 판정 재사용과 bulk 평가로 수정했다. 검증 상세와 Deploy 확정 입력은
[개발 기록](../../development_notes/integration/review_admission_docker_acceptance.md)에
있다. 추천 수정 commit 뒤 post-admission DB에서 manifest를 재생성하며 audit의
baseline 수와 apply의 기준이 달랐던 계약 결함도 발견해 보정했다. 수정 전 HEAD와
미커밋 검증 manifest는 폐기했다. 확정 구현 SHA `f3f67aac242b29e0494dd1a3f667fcaa7d9ca9d0`에서
manifest를 재생성하고 동일 판정과 `unchanged 3`을 확인해 Gate를 통과했다.

다음 검증을 새 DB 수치와 stable `(source_id, external_id)` 표본으로 다시 실행한다.

- Data·Backend 전체 단위 및 PostgreSQL 통합 테스트
- Migration single head와 실제 DB revision
- 정책 목록·검색·상세 API
- 명시적 지역 검색의 mismatch·unknown 혼입 방지
- 추천의 unknown·비단정 문구
- partial 상세의 공식 원문, 신청기간 확인 필요와 eligibility unknown 표시
- 관리자 Policy·CollectionRun 품질 수치
- Frontend unit·lint·build, Mock Browser와 actual Browser 분리 실행
- Release 1 golden과 5주차 actual acceptance 회귀

`W5-G1_PASS`의 과거 고정 숫자 ID와 row count를 assertion으로 재사용하지 않는다.
새 표본은 조건과 stable Source identity로 선택한다.

### RA4 Gate

판정: `REVIEW_ADMISSION_PASS`, `W5-G1_REVALIDATED` (`2026-08-19`).

- 새 실제 수치, rule version, manifest hash와 테스트 결과가 개발 기록에 있음
- 승격된 partial을 확정 자격·확정 신청기간으로 오표시한 사례 0건
- 담당자 전체 회귀가 통과해야 `REVIEW_ADMISSION_PASS`와
  `W5-G1_REVALIDATED`를 함께 기록
- 기존 `W5-G1_PASS`는 변경 전 snapshot의 역사 근거로만 유지하고 새 row 수나
  새 Acceptance 환경의 통과 근거로 재사용하지 않음
- 실패하면 Deploy 01 snapshot 생성·인계와 독립 QA를 중단

## Deploy 01 인계 계약

RA4에서 `REVIEW_ADMISSION_PASS`와 `W5-G1_REVALIDATED`를 기록한 뒤에만
[Deploy 01 Docker Acceptance Environment](../deploy/01_docker_acceptance_environment.md)로
다음 입력을 인계한다.

- 검증된 Git SHA와 admission rule version
- decision manifest hash와 새 DB 집계
- PostgreSQL major version·Alembic revision
- 대표 stable `(source_id, external_id)`
- snapshot에 포함할 table allowlist와 제외해야 할 운영·민감 데이터 범주
- Raw/checkpoint archive의 별도 hash와 보관 위치 식별자

실제 dump 생성, 민감정보 scan, Dockerfile·Compose, restore·Migration, Volume,
clean-room, CI와 BE·FE·리뷰어 package는 Deploy 01에서 구현·검증한다. Integration
10은 dump나 컨테이너 구현 결과를 미리 통과로 기록하지 않는다.

Deploy 01의 `DOCKER_ACCEPTANCE_PASS` 뒤에만 같은 snapshot version을 전제로
DTL5-5 독립 사용성 리뷰·QA를 시작한다.

## 역할별 구현 인계

| 역할 | 구현 책임 | 종료 증거 |
| --- | --- | --- |
| Data | review inventory, admission rule·fixture, Raw replay·manifest | RA1~RA2 audit와 표본 근거 |
| Backend | Importer transaction, partial DB·search·추천 계약 | RA3 DB 집계와 PostgreSQL 회귀 |
| Frontend | partial·unknown·공식 원문 표시, 오단정 방지 | RA4 unit·actual Browser |
| Integration | RA Gate, 새 기준선과 Deploy 입력 인계 | `REVIEW_ADMISSION_PASS`·`W5-G1_REVALIDATED`·handoff manifest |
| Deploy | snapshot·Compose·clean-room·동일 환경 인계 | Deploy 01 `DOCKER_ACCEPTANCE_PASS` |
| 리뷰어·QA | Deploy가 고정한 snapshot에서 독립 시나리오 | 결함·재검증 근거; 구현 승인 대체 금지 |

## 검증 계획

- RA0은 Git·Migration·DB·Runtime 일치와 복구 가능성을 검증한다.
- RA1은 실제 reason code 전체성과 공식 원문 표본을 검증한다.
- RA2는 fixture, read-only audit와 transaction rollback dry-run을 검증한다.
- RA3은 실제 반영 수치와 두 번째 실행의 완전한 idempotency를 검증한다.
- RA4는 Data·Backend·Frontend actual 회귀와 partial 비단정 표현을 검증한다.
- Deploy 검증은 Deploy 01 계획과 개발 기록에서 snapshot hash, clean-room
  restore, health, Volume 유지와 test DB 격리를 확인한다.
- RA Slice의 실행 명령과 실제 결과는 구현 착수 뒤 새 Integration 10 개발
  기록에 남기고, Deploy 결과를 복제하지 않고 링크한다.

## 위험과 미확정 사항

현재 PC에서는 최신 review producer, reason 분포와 승격 예상 수를 확인하지
않았다. RA0·RA1 결과에서 새 reason이나 Source 계약이
발견되면 코드를 먼저 작성하지 말고 Admission v1 fixture와 규칙을 보완한다.
실제 dump의 allowlist, 사내 전달 수단과 보관 기간은 Deploy 01에서 조직 정책과
함께 확정한다.

### 전체 중단 조건

- DB 보유 PC의 최신 Runtime이나 checkpoint가 누락됨
- actual DB와 repository Migration이 다름
- review 사유가 Admission v1로 설명되지 않음
- 승격 후보에 공식성·현재성·청년 대상·지역 근거 중 필수 근거가 없음
- duplicate baseline 또는 checkpoint identity drift가 해소되지 않음
- dry-run이 DB나 decision을 변경함
- 실제 적용 두 번째 실행이 unchanged가 아님
- Deploy 입력 manifest와 새 DB 집계가 일치하지 않음

## Forest 완료 기준

- `REVIEW_ADMISSION_PASS`·`W5-G1_REVALIDATED`와 새 실제 데이터 기준선이 기록됨
- versioned audit/apply와 fixture·통합 테스트가 존재함
- 승인 partial만 DB에 반영되고 재실행이 unchanged임
- 새 snapshot으로 담당자 actual 회귀가 통과함
- Deploy 01이 필요한 allowlist·manifest·stable identity 입력을 인수함
- 구현 결과는 Integration 10 development note에 기록되고 관련 기준 문서와
  `CHANGELOG.md`는 실제 변경이 완료된 뒤 갱신됨

## 관련 문서

- [Integration 07 Release 2 Feature Acceptance](07_release_2_feature_acceptance.md)
- [Deploy 01 Docker Acceptance Environment](../deploy/01_docker_acceptance_environment.md)
- [5주차 Data·Team Leader 실행 계획](../../weekly_plan/week_05_data_team_leader.md)
- [5주차 Release 2 실행 계획](../../weekly_plan/week_05_release_2.md)
- [Regional Youth Policy Ingestion](../data/05_regional_youth_policy_ingestion.md)
- [컨테이너 구조](../../../architecture/container_structure.md)
- [Collector 운영](../../../operations/collector.md)
- [Backend Windows 로컬 환경](../../backend_local_setup.md)
