# Integration 10 Review Admission and Deploy Handoff 개발 기록

## 작업 정보

- 상태: in-progress
- 기록 시작일: `2026-08-19`
- 담당 영역: Data·Backend·Frontend·Team Leader - Integration
- 브랜치: `feature/integration/week-05-acceptance`
- 기준 Git SHA: `9583f3e4a5c2ac68309d4312c703b8c0785f681e`
- 계획: [Integration 10 개발 계획](../../develop_plan/integration/10_review_admission_docker_acceptance.md)
- 선행 상태: Integration 07 `W5-G1_PASS`
- 현재 판정: `RA0_PASS`, RA1 대기

## 목적

DB 보유 PC의 최신 Git·PostgreSQL·Runtime을 실제 값으로 다시 고정하고, review
재판정이나 적재 전에 원본 DB와 Runtime을 복구 가능한 형태로 보호한다. 이후
RA1~RA4의 review admission 결과가 과거 문서 수치나 다른 PC의 DB에 의존하지
않게 한다.

## Forest 범위

- RA0 최신 Git·DB·Runtime inventory와 변경 전 보호
- RA1 review producer·사유·표본 감사
- RA2 versioned admission·fixture·scratch DB dry-run
- RA3 승인된 `promote_partial`만 transaction 적재·재실행
- RA4 DB·API·Browser 회귀, `W5-G1_REVALIDATED`와 Deploy 입력 인계

## Slice 진행 현황

| Slice | 상태 | 실제 결과 |
| --- | --- | --- |
| RA0 | completed | 실제 DB·Migration·Runtime 기준선과 암호화 변경 전 backup, `RA0_PASS` |
| RA1 | pending | evidence gap·review 사유·표본 감사 대기 |
| RA2 | pending | admission v1 구현·fixture·scratch DB dry-run 대기 |
| RA3 | pending | 실제 DB transaction 적재·멱등 재실행 대기 |
| RA4 | pending | DB·API·Browser 회귀와 Deploy 인계 대기 |

## 구현 내용

### RA0 Git·도구 기준선

- local·origin SHA 모두 `9583f3e4a5c2ac68309d4312c703b8c0785f681e`
- 작업트리는 배포 계획·문서 체계 변경이 아직 커밋되지 않아 dirty 상태
- Python `3.14.5`
- PostgreSQL client·server `18.4`
- Docker Client·Server `29.6.2`, Compose `5.3.1`
- Backend·Frontend listener `8000`, `3000`은 모두 중지 상태
- C 드라이브 여유 공간 `583.75 GiB`

Docker CLI는 설치돼 있었지만 Engine이 꺼져 있어 RA0에서 Docker Desktop을
기동하고 Server version까지 확인했다. PostgreSQL client는 PATH에는 없었지만
`C:\Program Files\PostgreSQL\18\bin`의 설치본을 사용했다.

### RA0 PostgreSQL 기준선

- Database: `cheongnyeon_alimi`
- repository Alembic head: `20260810_0006`
- actual `alembic_version`: `20260810_0006`
- Policy 전체: `3,270`

| Source | Policy |
| --- | ---: |
| `youthcenter-api` | 2,698 |
| `bokjiro-central-welfare-api` | 461 |
| `regional-daegu-youth-platform` | 33 |
| `regional-busan-youth-platform` | 16 |
| `regional-jeonbuk-youth-platform` | 16 |
| `regional-incheon-youth-platform` | 15 |
| `regional-gwangju-integrated-youth-platform` | 10 |
| `regional-gyeongnam-youth-platform` | 7 |
| `regional-ulsan-youth-platform` | 5 |
| `regional-gangwon-youth-platform` | 2 |
| `regional-gyeongbuk-youth-platform` | 2 |
| `cheonan-youthcenter-web` | 1 |
| `kosaf-scholarship-web` | 1 |
| `regional-daejeon-youth-platform` | 1 |
| `regional-jeju-youth-platform` | 1 |
| `regional-seoul-youth-platform` | 1 |

| 분포 | 값 |
| --- | --- |
| 품질 | `valid 1,468`, `partial 1,802` |
| 신청 상태 | `open 818`, `closed 1,972`, `scheduled 17`, `null 463` |
| CollectionRun | `succeeded 39`, `running 1`, terminal Source 18개 |

`youthcenter` run `515ed43d-2d28-4667-82f3-f21d6ceea685`는
`2026-08-17 17:11:08+09:00`부터 `running`이며 RA0 확인 시점에 1일 이상
경과했다. Backend listener와 별도 DB activity는 없으므로 진행 중 작업으로
간주하지 않고 orphan/stale 후보로 RA1 이후 수정 전 triage한다. RA0에서는
상태를 변경하지 않았다.

### RA0 Runtime 기준선

| 항목 | 실제 값 |
| --- | ---: |
| `runtime/raw` JSON | 19,013 |
| `runtime/decisions` JSON | 169 |
| regional checkpoint | 13 |
| 최신 Raw·decision 시각 | `2026-08-17` |

현재 Raw와 checkpoint의 읽기 전용 재생은 13개 Source, discovered 4,606,
captured 4,284, accepted 109, review 1,140, closed 3,033, duplicate 2,
failed 322로 끝났고 `checkpoint_decision_drift=0`이다. 완료 checkpoint가
참조하는 Raw 누락으로 인한 replay 실패는 없었다.

다만 `capture_evidence_gap_sources=10`이며 RYP9 재판정 사전 감사는 transition
29건, `ready_for_redecision=false`다. blocker는
`existing_accepted_preserved`, `transition_scope_valid`이다. 이 값은 RA0
실패가 아니라 RA1에서 규칙·표본·전환 범위를 다시 확인할 입력이며, 통과로
간주하거나 기존 RYP9 결과로 덮어쓰지 않는다.

### RA0 변경 전 보호

backup 위치는 workspace 밖의 다음 사용자 전용 EFS 암호화 디렉터리다.

```text
%LOCALAPPDATA%\cheongnyeon-alimi\backups\2026-08-19-ra0-9583f3e
```

| 산출물 | 크기 | SHA-256 | 검증 |
| --- | ---: | --- | --- |
| `pre-review-admission.dump` | 3,026,807 bytes | `6B6DEA8FBE2CB53E13F67601F792253BA779BFFCBDE55FC17BCA60D79888D17E` | EFS, `pg_restore --list` 93행 |
| `pre-review-admission-runtime.zip` | 34,043,724 bytes | `A440EFE30144678C2EF07BAE0CC824E92DCF168C3AFF9C032DA46A468AF0C358` | EFS, entry 19,551개, 허용 경로 밖 entry 0 |
| `ra0-regional-replayability-audit.json` | 44,665 bytes | `8086023886010EC71390869143321392342CE925E4007A076F7F661009628105` | EFS, read-only replay |
| `ra0-regional-ryp9-replayability-audit.json` | 21,135 bytes | `630FC185D6AA5E54DF77E270701FD3642AFA735DD1CB75C122BA6A75F014F072` | EFS, DB session rollback |

dump에는 owner·ACL을 고정하지 않았다. 복구는 원본 DB를 drop·overwrite하지
않고 PostgreSQL 18의 새 빈 DB에 `pg_restore`하는 경로로 제한한다. 이번
Slice에서는 TOC 가독성만 확인했고 실제 restore rehearsal은 Deploy 01의 별도
Volume에서 수행한다.

pgpass는 Git 밖 `%LOCALAPPDATA%\Temp`에 있고 현재 사용자 R/W ACL만 확인했다.
Git 추적 대상에는 example 환경 파일만 있으며 pgpass, 실제 dump,
`runtime/raw`와 `runtime/decisions`는 없다. 비밀번호·API key 값은 기록하거나
출력하지 않았다.

## 주요 변경 파일

- `docs/development/develop_plan/integration/10_review_admission_docker_acceptance.md`
- `docs/development/development_notes/integration/review_admission_docker_acceptance.md`
- `docs/development/develop_plan/README.md`
- `docs/development/development_notes/README.md`
- `docs/development/develop_plan/forest_roadmap.md`
- `docs/index.md`

DB·Runtime 원본은 변경하지 않았다. backup과 read-only audit 결과는 Git 밖의
암호화 디렉터리에만 생성했다.

## 설계 결정

1. 과거 문서의 3,269건 대신 실행 시점 실제 DB 3,270건을 RA0 기준선으로 쓴다.
2. dirty worktree는 배포 계획 문서 변경분으로 식별해 숨기지 않고, RA1 코드
   구현 전 별도 커밋으로 고정한다.
3. Raw 본문과 실제 자격증명은 개발 기록에 넣지 않고 count·hash·판정만 남긴다.
4. orphan `running` run은 RA0에서 수동 SQL로 수정하지 않는다. 운영 계약에
   맞는 stale 처리 경로를 확인한 뒤 별도 증거와 함께 정리한다.
5. capture evidence gap과 RYP9 blocker는 RA1 입력으로 유지한다. 목표 row 수를
   맞추기 위해 partial 승격 규칙을 완화하지 않는다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| local/origin Git SHA | 통과, 동일 `9583f3e` |
| repository/actual Migration | 통과, 모두 `20260810_0006` |
| PostgreSQL inventory | 통과, Policy 3,270건과 CollectionRun 분포 기록 |
| Runtime inventory | 통과, Raw 19,013·decision 169·checkpoint 13 |
| checkpoint Raw replay | 통과, Source 13·decision drift 0 |
| 변경 전 DB dump | 통과, EFS·SHA-256·TOC 93행 |
| Runtime archive | 통과, EFS·SHA-256·entry 19,551·허용 밖 0 |
| Docker 사전 확인 | 통과, Engine `29.6.2`·Compose `5.3.1` |
| 원본 DB·Runtime 변경 금지 | 통과, read-only SQL·rollback audit만 수행 |

따라서 RA0 Gate는 `RA0_PASS`다. evidence gap, RYP9 blocker와 stale run은
RA1~RA3의 명시적 입력이며 아직 해결되거나 승인된 것으로 보지 않는다.

## 남은 작업

1. 현재 문서 변경을 커밋해 RA1 코드 작업의 clean Git 기준선을 만든다.
2. RA1에서 review producer·reason 교집합과 Source별 결정적 표본을 만든다.
3. capture evidence gap 10개 Source의 capture-contract gap과
   legacy-unverifiable null을 분리한다.
4. RYP9 blocker `existing_accepted_preserved`, `transition_scope_valid`의 실제
   transition을 대조하고 admission v1 규칙 입력을 확정한다.
5. orphan `youthcenter` CollectionRun을 승인된 stale 처리 경로로 정리하되,
   RA0 DB dump와 변경 전 수치는 그대로 보존한다.
6. RA1 Gate 전에는 replay 결과를 실제 DB에 적재하지 않는다.
