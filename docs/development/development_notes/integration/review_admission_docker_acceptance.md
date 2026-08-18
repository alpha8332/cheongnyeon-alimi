# Integration 10 Review Admission and Deploy Handoff 개발 기록

## 작업 정보

- 상태: completed
- 기록 시작일: `2026-08-19`
- 담당 영역: Data·Backend·Frontend·Team Leader - Integration
- 브랜치: `feature/integration/week-05-acceptance`
- RA4 시작 Git SHA: `424514165b1e2c92f477d04005521d9d5e5d4bb2`
- 계획: [Integration 10 개발 계획](../../develop_plan/integration/10_review_admission_docker_acceptance.md)
- 선행 상태: Integration 07 `W5-G1_PASS`
- 현재 판정: `RA0_PASS`, `RA1_PASS`, `RA2_PASS`, `RA3_PASS`,
  `REVIEW_ADMISSION_PASS`, `W5-G1_REVALIDATED`

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
| RA1 | completed | review producer·사유·표본·taxonomy v2와 RA2 후보 6건, `RA1_PASS` |
| RA2 | completed | admission v1·taxonomy v2·RA3 현재성 보정 후 `RA2_PASS` |
| RA3 | completed | 실제 DB 3건 적재·동일 manifest 전건 unchanged, `RA3_PASS` |
| RA4 | completed | 확정 구현 SHA manifest·전체 회귀·actual API·Mock/actual Browser·추천·post-admission baseline 계약 통과, `REVIEW_ADMISSION_PASS`·`W5-G1_REVALIDATED` |

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

### RA1 review producer와 사유 inventory

`2026-08-19` 기준으로 기존 audit 두 개를 최신 Raw·checkpoint와 실제 DB에서
다시 실행했다. 외부 Source 재호출과 DB write는 수행하지 않았다.

| producer | 대상 | 현재 판정 |
| --- | ---: | --- |
| regional policy gate | review 1,140 | admission v1 감사 대상 |
| 최신 cross-source duplicate gate | `duplicate_review_required` 3 | 전건 `hold_review` |
| regional checkpoint | closed 3,033 | `exclude_closed`, 승격 금지 |
| regional checkpoint | failed 322 | `exclude_failed`, 승격 금지 |
| regional checkpoint | duplicate 2 | `exclude_duplicate`, 승격 금지 |

최신 duplicate review 3건은 각각 `canonical_url_matches_multiple_policies`,
`material_title_containment_requires_review`,
`same_title_with_incomplete_comparison_evidence`다. Source는
`kinfa-financial-product-web`, `kpass-transit-refund-web`,
`regional-jeonbuk-youth-platform`이며 RA2에서 자동 승격하지 않는다.

지역 review reason은 한 후보에 여러 개가 함께 존재한다.

| reason·route | 건수 |
| --- | ---: |
| `insufficient_regional_evidence` | 1,041 |
| application state route | 694 |
| `application_period_missing` | 646 |
| `youth_target_unconfirmed` | 430 |
| capture failure | 322 |

evidence coverage에서 `capture_contract_gap`은
`additional_benefit_text 947`, `source_region_text 889`,
`region_eligibility_text 826`, `application_channel_text 768`,
`implementing_organization_text 653`, `application_period_text 628`이다. 이는
Source 값이 없다는 뜻이 아니라 과거 캡처 계약으로 확인할 수 없다는 뜻이므로
null을 근거 있는 부재로 바꾸지 않는다.

audit schema를 `1.1.0`으로 올리고 Source×reason마다 `external_id`를 정렬해 최대
20개만 담는 `review_reason_samples`를 추가했다. Raw 본문·제목·자격 텍스트는
보고서에 복사하지 않는다. 새 보고서는 Source 13, discovered 4,606,
review 1,140, decision drift 0이며 SHA-256은
`97F8BE2E358128535023E8D6480AAEDABD04BCEA10D2AC60B989C3B2050FEB12`다.

### RA1 청년 대상 taxonomy와 표본 판정

사용자 범위 결정에 따라 청년 대상 taxonomy를 v2로 확장했다. 기존 `청년`,
`청소년`, `대학생`과 신혼부부·청년 부모뿐 아니라 다음 원문 표지를 청년 대상
조건으로 인정한다.

- 가족·부모: `신혼부부`, `예비신혼부부`, `미혼모`, `미혼부`, `청소년부모`
- 돌봄·자립: `가족돌봄청년`, `가족돌봄청소년`, `영케어러`, `자립준비청년`,
  `보호종료아동`
- 취약·전환: 고립·은둔, 학교밖·가정밖·쉼터퇴소, 경계선지능, 장애·저소득·
  주거취약·다문화·탈북, 니트·구직단념·장기미취업, 전입·지역정착 청년 표지
- 취업·교육: `취업준비생`, `구직자`, `미취업자`, `졸업생`, `졸업예정자`,
  `대학원생`, `학자금`, `장학생`, `사회초년생`, `신입사원`
- 가구·사업: `1인가구`, `예비창업자`, `초기창업`, `스타트업`, `귀농`,
  `후계농`, 청년농업인·청년창업자
- 세대·병역: 정확한 `2030세대`, `ROTC`, `학군사관후보생`, `사관후보생`,
  `군복무`, `전역자`, `전역청년`

공백·가운뎃점·괄호는 비교 시 정규화하지만 단순 연도 `2030년`은 세대 표지로
인정하지 않는다. 일반 `한부모`, `부모`, `가구`, `학생`, `기업`, `농업인`처럼
목록에 없는 상위 표현만으로는 확정하지 않는다. 새 표지는 청년 대상 조건만
충족하며 공식성·identity·현재성·지역·duplicate 조건을 우회하지 않는다.
원문에 없는 나이·소득·세부 자격도 만들지 않는다.

checkpoint outcome이 실제 `review`이고 현재 판정에
`youth_target_unconfirmed`가 있는 430건만 최신 detail Raw와 다시 대조했다.
taxonomy v2 일치 고유 후보는 44건이다. 그룹별 일치는 기존 직접 표지 1,
가족·부모 2, 돌봄·자립 1, 취업·교육 23, 가구·사업 17, 세대·병역 2건이며
후보 하나가 여러 그룹에 속할 수 있다. 이 대조는 closed 등 다른 checkpoint
outcome 1,514건을 review 수치에 섞지 않는다.

이미 Policy DB에 있는 `partial` 1,802건도 같은 방향으로 읽기 전용 대조했다.
아래는 제목·대상·자격·지원 내용의 taxonomy 표지 일치 수이며 서로 겹칠 수
있다. 이미 적재된 row이므로 신규 admission 수가 아니라 검색·추천의 청년 분류와
미확정 자격 표시를 보강할 후보군이다.

| partial 후보군 | 일치 |
| --- | ---: |
| 대학원생·대학생·학자금·장학생 | 160 |
| 니트·구직단념·장기미취업 | 77 |
| 취업준비생·구직자·미취업자·졸업생 | 56 |
| 자립준비청년·보호종료아동 | 50 |
| 예비창업자·초기창업·스타트업 | 28 |
| 귀농·후계농·청년농업인 | 24 |
| 고립·은둔 | 24 |
| ROTC·군복무·전역 | 24 |
| 가족돌봄청년·가족돌봄청소년·영케어러 | 12 |
| 학교밖·가정밖·쉼터퇴소 청소년 | 12 |
| 1인가구 | 9 |
| 사회초년생·신입사원 | 8 |
| 저소득·주거취약 등 취약청년 | 7 |
| 전입·지역정착청년 | 7 |
| 경계선지능·느린학습 | 4 |
| 정확한 `2030세대` 계열 | 1 |

44건 중 지역·현재성 공통 조건을 사전 충족한 후보는 6건이다.

| Source / external_id | 원문 제목 | taxonomy 근거 |
| --- | --- | --- |
| `regional-daegu-youth-platform/8375` | 1인가구 커뮤니티 프로그램 | `1인가구` |
| `regional-daegu-youth-platform/8187` | 달성 창업 성공패키지 | `초기창업` 계열 |
| `regional-daegu-youth-platform/8357` | 여성1인가구지원사업 | `1인가구` |
| `regional-gangwon-youth-platform/A2026010600300200900600001` | 속초시 취업자격증 응시료 지원 | 취업·구직 계열 |
| `regional-gyeongbuk-youth-platform/1009` | 신혼부부 주택자금 대출이자 지원 | `신혼부부` |
| `regional-gyeongnam-youth-platform/2091` | 양산시 1인가구 프로그램 | `1인가구` |

이는 실제 승격 결과가 아니다. taxonomy v2를 기존 producer 상수에 즉시 넣으면
완료 checkpoint의 과거 판정과 replay가 달라지므로, RA2의 versioned admission
규칙·fixture에서 적용한다. duplicate와 scratch DB 검증 전에는 Policy DB에
반영하지 않는다.

전체 지역 review의 결정적 사전 분류는 다음과 같다.

| 분류 | 건수 | 의미 |
| --- | ---: | --- |
| RA2 `promote_partial` 후보 | 6 | taxonomy v2 포함 모든 공통 조건 사전 충족 |
| `hold_review` | 1,134 | 청년·지역·현재성·provenance 중 하나 이상 부족 |
| duplicate `hold_review` | 3 | 중복 충돌 또는 비교 근거 부족 |

RYP9 재판정 감사의 29건은 모두 `accepted→duplicate` 제안이라
`existing_accepted_preserved=false`, `transition_scope_valid=false`다. 기존
accepted를 조용히 제거하는 전환이므로 admission v1 입력에서 제외하고 원래
accepted 상태를 유지한다.

### RA2 최초 admission과 RA3 사전 검증에서 발견한 결함

기존 regional producer와 완료 checkpoint를 바꾸지 않는
`review-admission-v1`, taxonomy `2.0.0`을 구현했다. audit는 실제 PostgreSQL의
aggregator baseline과 저장된 Raw·checkpoint를 읽기 전용으로 다시 대조하고,
apply는 같은 입력으로 manifest를 재생성해 hash가 일치할 때만 기존
Normalizer·Importer에 승격 후보를 전달한다.

RA2 최초 manifest 결과는 다음과 같았으나 RA3에서 폐기했다.

| 항목 | 실제 값 |
| --- | ---: |
| regional review | 1,140 |
| `promote_partial` | 5 |
| `hold_review` | 1,135 |
| 승격 후보 hard exclusion | 0 |
| 외부 duplicate producer `hold_review` | 2 |
| manifest SHA-256 | `803e64cf5a774eb01323412491ea4b0b9a7e9b57995df89969ac69ea42e1ef74` |
| aggregator baseline ID | `2194e49e05089e56d27984a52f3f9fd6` |

최초 `promote_partial` identity는 다음 5건이었다.

- `regional-daegu-youth-platform/8187`
- `regional-daegu-youth-platform/8357`
- `regional-daegu-youth-platform/8375`
- `regional-gangwon-youth-platform/A2026010600300200900600001`
- `regional-gyeongnam-youth-platform/2091`

RA1 사전 후보였던 `regional-gyeongbuk-youth-platform/1009`는 실제 aggregator
비교에서 `same_title_with_incomplete_comparison_evidence`가 확인돼
`duplicate_review_required`로 보류했다. 외부 producer의
`kinfa-financial-product-web/hessalLoanYoos`,
`kpass-transit-refund-web/intro`도 기존 duplicate review를 유지한다.

로컬 역할에는 `CREATEDB`가 없어 서비스 DB 권한을 확대하지 않았다. 대신
로컬 `127.0.0.1:55432`에만 bind한 PostgreSQL 18 Docker scratch DB
`cheongnyeon_alimi_admission_test`에 RA0 dump를 복원했다. Migration
`20260810_0006`, Policy 3,270건에서 5건의 Policy·search projection write가
`inserted`로 계산됐고 transaction rollback 후 다시 3,270건이었다. 하지만
canonical region rule이 0건이었고, 통합 테스트가 Policy 수와 importer 멱등성만
검사해 이 결함을 놓쳤다.
별도 멱등성 검증에서는 첫 적용이 `inserted 5`, 동일 manifest 재적용이
`unchanged 5`였고 검증 identity를 정리한 뒤 다시 3,270건임을 확인했다. 서비스
DB와 checkpoint는 변경하지 않았다.

### RA3 현재성·지역 보정과 실제 적재

RA3 시작 시 RA2 커밋 `603a0bcd4c7e2b6ef6c0926f768adebfcdd5e51a`를
확인하고 manifest를 다시 만들었다. 최초 서비스 적용 5건 직후 region rule 0건을
발견해 Gate를 중단했다. 해당 시도로 생성된 Policy 5건과 정확히 연결된
CollectionRun 3건만 보상 rollback해 Policy 3,270·CollectionRun 40 기준선으로
되돌렸다. 다른 기존 row는 변경하지 않았고 RA0 dump로도 복구 가능하다.

원인은 두 가지였다.

1. review의 원본 `ExtractedPolicy`를 바로 정규화해 regional Gate가 확인한
   canonical region을 Policy·region rule로 물질화하지 않았다.
2. checkpoint의 과거 `open`을 실행 기준일에도 그대로 사용했다.

admission은 실행 기준일 `2026-08-19`로 기존 regional Gate를 다시 평가하고,
청년 대상 조건만 taxonomy v2로 대체하도록 수정했다. 대구 `8375`는 8월 14일,
`8187`은 8월 18일 마감이므로 `exclude_closed`로 바뀌었다. `valid`와 `partial`을
모두 허용한다는 공통 계약도 classifier에 반영했다.

최종 manifest 결과는 다음과 같다.

| 항목 | 최종 값 |
| --- | ---: |
| regional review | 1,140 |
| `promote_partial` | 3 |
| `hold_review` | 1,071 |
| `exclude_closed` | 66 |
| hard exclusion 오승격 | 0 |
| 외부 duplicate `hold_review` | 2 |
| manifest SHA-256 | `d6d781aaefa41e12a73d6f868fd5f291e83dc41e7930382441467795e9f4fdad` |

최종 적재 identity와 품질은 다음과 같다.

| Source / external_id | 품질 | canonical region |
| --- | --- | --- |
| `regional-daegu-youth-platform/8357` | `partial` | 대구광역시 `2700000000` |
| `regional-gangwon-youth-platform/A2026010600300200900600001` | `partial` | 강원특별자치도 `5100000000` |
| `regional-gyeongnam-youth-platform/2091` | `valid` | 경상남도 `4800000000` |

scratch CLI의 첫 실행 `inserted 3`, 두 번째 `unchanged 3`, canonical region
rule·search projection 각 3건과 cleanup 후 Policy 3,270건을 확인했다. 서비스
DB에는 corrected payload를 `inserted 3`으로 적용했다. 이후 checkpoint 원래
reason과 실행일 reason을 내부적으로 분리해 최종 manifest SHA가 바뀌었지만 정책
payload는 같았고, 최종 SHA를 두 번 실행해 모두 `unchanged 3`을 확인했다. 각
실행은 Source별 transaction과 `runtime_import` CollectionRun을 남겼다.

최종 서비스 DB는 Policy 3,273건, `valid 1,469`, `partial 1,804`, `open 821`,
CollectionRun 52건이다. 승인 3건의 matched region rule과 search projection은
각 3건이다. 기존 orphan `running` 1건은 이번 Slice에서 변경하지 않았다.

RA3 실행 시 Git HEAD는 RA2 커밋 `603a0bcd4c7e2b6ef6c0926f768adebfcdd5e51a`이고
RA3 수정분은 아직 미커밋이므로 manifest의 `git_sha`도 이 기준 SHA를 가리킨다.
RA3 커밋 뒤 RA4 시작 시 새 HEAD로 manifest를 다시 생성하고, 정책 payload와
판정 수가 같으며 서비스 적용이 `unchanged 3`인지 확인해야 한다.

## RA4 실제 결과

RA3 변경을 커밋한 `424514165b1e2c92f477d04005521d9d5e5d4bb2`에서
manifest를 다시 만들었다. 판정은 `review 1,140`, `promote_partial 3`,
`hold_review 1,071`, `exclude_closed 66`, hard exclusion 오승격 0,
외부 duplicate hold 2로 RA3와 같았다. 새 manifest SHA-256은
`e466ed4e751077fa363974aaa795492f011e3ea33d2f1ccc174efef8a85d936f`이고
서비스 DB 재적용은 `inserted 0`, `updated 0`, `unchanged 3`이었다.

이 manifest는 RA4에서 추천 결함을 수정하기 전 HEAD를 가리킨다. 따라서 정확한
판정·멱등성 증거로는 유효하지만 Deploy 01 최종 handoff manifest로 사용하지
않는다. 아래 코드·문서 변경을 사용자가 커밋한 뒤 그 commit SHA로 다시 생성해
동일 판정·`unchanged 3`을 확인해야 한다.

추천 수정 commit `874c0f808c4a3cd9ef73135b7dbd3a11cedb27aa`에서 다시
audit했을 때 post-admission 전체 Policy 3,273건을 manifest baseline으로 기록해,
apply가 요구하는 승격 전 baseline 3,270건과 충돌하는 계약 결함을 발견했다.
audit가 이미 존재하는 `promote_partial` identity 3건을 현재 Policy 수에서 제외해
승격 전 기준선 3,270건을 기록하도록 수정하고 단위 회귀를 추가했다. 수정 후
검증 manifest는 판정 수가 같고 서비스 재적용도 `inserted 0`, `updated 0`,
`unchanged 3`이었다. 이 실행 뒤 CollectionRun은 58건이며 기존 orphan
`running` 1건은 그대로다.

이 검증 manifest의 SHA-256은
`65f375e542e221512bdee144bddb3ca30123ebbdf64bd6440ae61b48f5025769`지만,
baseline 수정이 아직 미커밋인 상태에서 생성돼 내장 `git_sha`가 `874c0f8`을
가리킨다. 따라서 결함 수정 검증에만 사용하고 Deploy 01 인계본으로 사용하지
않는다.

baseline 계약 수정을 커밋한 확정 구현 SHA
`f3f67aac242b29e0494dd1a3f667fcaa7d9ca9d0`에서 최종 manifest를 다시 만들었다.
계약 SHA-256은
`789f8e3b61c144843e93bc762d60f114179c6bfb8e5effd260138c73484e1203`,
file SHA-256은
`03b6d91952e53148e709d2a66838faaf26f63432a49050d48f7b2ab40186ebda`다.
baseline 3,270, review 1,140, promote 3, hold 1,071, closed 66,
external duplicate hold 2, hard exclusion 0으로 판정이 유지됐다. 서비스 DB
최종 재적용은 `inserted 0`, `updated 0`, `unchanged 3`, Policy 3,273건
유지였고 세 Source run은 모두 `succeeded`였다.

### 실제 DB·API 기준선

| 항목 | RA4 값 |
| --- | ---: |
| PostgreSQL / Alembic | `18.4` / `20260810_0006` |
| Policy | 3,273 |
| `valid` / `partial` | 1,469 / 1,804 |
| `open` | 821 |
| CollectionRun | 61 |
| orphan `running` | 1, 변경하지 않음 |

신규 stable identity는 다음 실제 Policy ID로 조회됐다. 숫자 ID는 이 snapshot의
관측값이며 Deploy·후속 검증 assertion은 stable identity를 사용한다.

| stable identity | actual ID | 품질 | 지역 |
| --- | ---: | --- | --- |
| `regional-daegu-youth-platform/8357` | 15102 | `partial` | 대구광역시 |
| `regional-gangwon-youth-platform/A2026010600300200900600001` | 15103 | `partial` | 강원특별자치도 |
| `regional-gyeongnam-youth-platform/2091` | 15104 | `valid` | 경상남도 |

세 표본은 공개 상세 opt-in, 공식 HTTP(S) 원문과 eligibility `partial` coverage를
유지했다. partial ID 15102는 기본 상세에서 404, `include_partial=true`에서
200이었고 valid ID 15104는 기본 상세에서도 200이었다. 명시적 올바른 지역
검색은 각 표본 1건과 `region=match`만 반환했고 서울특별시로 바꾼 동일 keyword
검색에는 세 표본이 모두 0건이었다.

### RA4에서 발견하고 수정한 추천 결함

actual Browser에서 대구광역시·25세를 입력했을 때 마감 정책과 제주·인천 등
확정 불일치 지역 정책이 추천되는 high 결함을 발견했다. 원인은 추천 서비스가
검색의 3값 판정을 재사용하지 않고 일치 조건에 점수만 더했으며, 첫 200개
Policy만 평가한 데 있었다.

- 지역·연령·분야·상태 확정 mismatch를 후보에서 제외
- 명시적 지역의 `unknown`도 검색 API와 동일하게 fail-closed 제외
- status 미지정 기본 추천에서 `closed` 제외
- 계약의 `upcoming`을 DB `scheduled`로 매핑하고 명시 상태 `unknown`은 제외,
  invalid status는 422
- 연령 bounds 누락을 match로 추정하지 않고 확인 필요로 유지
- 고정 200건 제한을 제거해 전체 승인 snapshot 평가
- Policy region rule과 지역 catalog를 bulk query해 N+1 제거

실제 3,273건에서 대구·25세·partial 포함 응답은 수정 전 약 `14,845 ms`에서
bulk 판정 후 약 `1,386 ms`로 줄었고, 34건 모두 지역 match, closed 0건,
신규 ID 15102 포함이었다. valid-only 경상남도·25세 actual Browser는 7건,
타 시도 혼입 0, closed 0, 신규 ID 15104 노출, 비단정 문구와 7개 확인 필요
표시를 확인했다. 증상·원인·단계별 해결과 예방 기준은
[추천 전체 정책 판정의 N+1과 오추천 해결](../../../troubleshooting/backend/recommendation_full_inventory_performance.md)에
별도로 기록했다.

### RA4 회귀 결과

| 검증 | 최종 결과 |
| --- | --- |
| Data·Backend 포함 전체 pytest | 508 passed, 27 skipped, subtest 241 passed |
| Backend 전용 PostgreSQL | 191 passed |
| 별도 PostgreSQL integration | 8 passed |
| Frontend unit | 216 passed |
| Frontend lint / build | 통과 / 통과 |
| Playwright Mock Browser | 80 passed, actual-only 14 skipped |
| actual API·in-app Browser | 검색·상세·추천·관리자 Policy·CollectionRun 통과 |
| 추천 결정성·지역·마감·미확정 | 동일 순서, match-only, closed 0, 비단정·확인 필요 유지 |

skip은 PostgreSQL 전용 또는 actual 전용 조건을 충족하지 않은 실행에서만
발생했고, PostgreSQL·actual Browser는 별도 실행했다. pytest의
Starlette/httpx deprecation, Vite native config와 500 kB chunk 경고는 기존
비차단 경고로 남는다.

### Deploy 01 확정 입력

- rule / taxonomy: `review-admission-v1` / `2.0.0`
- 검증 구현 Git SHA: `f3f67aac242b29e0494dd1a3f667fcaa7d9ca9d0`
- admission manifest SHA-256:
  `789f8e3b61c144843e93bc762d60f114179c6bfb8e5effd260138c73484e1203`
- DB: PostgreSQL `18.4`, Alembic `20260810_0006`, 위 Policy·CollectionRun 집계
- stable identity: 위 3건
- 예비 table allowlist: `alembic_version`, `policies`,
  `administrative_regions`, `administrative_region_aliases`,
  `policy_region_rules`, `policy_search_documents`, `collection_runs`
- 제외: test DB, 관리자 token·PIN·pgpass, `backend/logs`, Runtime Raw·checkpoint·
  decision 원문, 임시 manifest, 개인 연락처·credential·운영 감사 원문
- 별도 보관 Runtime archive:
  `%LOCALAPPDATA%\cheongnyeon-alimi\backups\2026-08-19-ra0-9583f3e\pre-review-admission-runtime.zip`,
  SHA-256 `A440EFE30144678C2EF07BAE0CC824E92DCF168C3AFF9C032DA46A468AF0C358`

table allowlist·금지 field scan과 실제 post-admission dump/hash는 Deploy 01 DEP1
책임이다. Integration 10 입력은 위 SHA와 hash로 고정했고
`REVIEW_ADMISSION_PASS`와 `W5-G1_REVALIDATED`를 선언한다.

## 주요 변경 파일

- `docs/development/develop_plan/integration/10_review_admission_docker_acceptance.md`
- `docs/development/development_notes/integration/review_admission_docker_acceptance.md`
- `docs/development/develop_plan/README.md`
- `docs/development/development_notes/README.md`
- `docs/development/develop_plan/forest_roadmap.md`
- `docs/index.md`
- `collectors/regional_review_audit.py`
- `collectors/regional_expansion.py`
- `collectors/regional_pilot.py`
- `collectors/gyeongbuk_youth.py`
- `collectors/review_admission.py`
- `scripts/audit_review_admission.py`
- `scripts/apply_review_admission.py`
- `data/schema/review_admission_audit.schema.json`
- `data/fixtures/contracts/review_admission_cases.json`
- `tests/test_review_admission.py`
- `tests/test_review_admission_audit.py`
- `tests/integration/test_review_admission_to_database.py`
- `docs/data/review_admission_rules.md`
- `tests/test_regional_review_audit.py`
- `backend/app/repositories/policy_search.py`
- `backend/app/api/v1/endpoints/recommendation.py`
- `backend/app/schemas/recommendation.py`
- `backend/app/services/policy_search_evaluation.py`
- `backend/app/services/recommendation.py`
- `backend/tests/test_recommendation_api.py`

RA3에서 서비스 DB Policy 3건과 Source별 CollectionRun 6건을 추가했다. Runtime
Raw·checkpoint는 변경하지 않았고 manifest와 backup은 Git 밖에 유지했다.

## 설계 결정

1. 과거 문서의 3,269건 대신 실행 시점 실제 DB 3,270건을 RA0 기준선으로 쓴다.
2. dirty worktree는 배포 계획 문서 변경분으로 식별해 숨기지 않고, RA1 코드
   구현 전 별도 커밋으로 고정한다.
3. Raw 본문과 실제 자격증명은 개발 기록에 넣지 않고 count·hash·판정만 남긴다.
4. orphan `running` run은 RA0에서 수동 SQL로 수정하지 않는다. 운영 계약에
   맞는 stale 처리 경로를 확인한 뒤 별도 증거와 함께 정리한다.
5. capture evidence gap과 RYP9 blocker는 RA1 입력으로 유지한다. 목표 row 수를
   맞추기 위해 partial 승격 규칙을 완화하지 않는다.
6. taxonomy v2 표지는 청년 대상 조건에만 사용하고 다른 Gate를 우회하지
   않는다. 기존 producer·checkpoint는 소급 변경하지 않고 RA2 admission에서
   버전을 고정한다.
7. audit 표본에는 identity·reason만 기록하고 Raw 본문을 복제하지 않는다.
8. checkpoint의 과거 `open`은 admission 실행일의 현재성을 대신하지 않는다.
   regional Gate를 다시 적용해 현재성과 canonical region을 함께 물질화한다.
9. RA3 최초 실패 시도분은 정확한 identity·run ID를 확인한 뒤에만 보상
   rollback하고, 삭제 전후 수치와 복구 가능한 RA0 dump를 유지한다.

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
| RA0~RA2 원본 DB·Runtime 변경 금지 | 통과, read-only SQL·scratch rollback만 수행 |
| RA1 regional audit | 통과, schema `1.1.0`·Source 13·review 1,140·drift 0 |
| 사유별 결정적 표본 | 통과, Source×reason 최대 20 identity·Raw 본문 0 |
| RA1 taxonomy 대조 | 통과, review 430건 중 v2 일치 44·RA2 후보 6·hold 1,134 |
| regional audit 단위 테스트 | 5개 통과 |
| RA2 admission fixture | 통과, 14 cases·taxonomy 전체 표지·2030 연도 오탐 방지 |
| 최종 admission audit | 통과, review 1,140·promote 3·hold 1,071·closed 66 |
| 최종 manifest Schema·hash | 통과, schema issue 0·SHA-256 `d6d781aa…` |
| PostgreSQL scratch CLI | 통과, inserted 3·unchanged 3·region/search 각 3·cleanup 3,270 |
| PostgreSQL admission 통합 테스트 | 2개 통과, rollback·CLI 멱등·Source별 run·지역 rule |
| 전체 Data·Integration 회귀 | 333개 통과·10개 환경 조건 skip·subtest 241개 통과 |
| RA3 서비스 1차 적용 | 통과, inserted 3·Policy 3,270→3,273 |
| RA3 서비스 재실행 | 통과, inserted 0·updated 0·unchanged 3 |
| RA3 최종 DB | 통과, Policy 3,273·valid 1,469·partial 1,804·open 821 |
| RA4 post-admission audit baseline | 통과, 전체 3,273에서 기존 승격 3건 제외·기준선 3,270 |
| RA4 baseline 계약 단위 회귀 | 6개 통과·subtest 69개 통과 |
| RA4 검증 manifest 재적용 | 통과, inserted 0·updated 0·unchanged 3·CollectionRun 58 |
| RA4 확정 SHA manifest | 통과, Git `f3f67aa`·SHA-256 `789f8e3b…`·기준선 3,270 |
| RA4 최종 서비스 재적용 | 통과, inserted 0·updated 0·unchanged 3·Policy 3,273·CollectionRun 61 |

따라서 RA0 Gate는 `RA0_PASS`, RA1 Gate는 `RA1_PASS`, 보정된 RA2 Gate는
`RA2_PASS`, 실제 적재 Gate는 `RA3_PASS`, RA4 Gate는
`REVIEW_ADMISSION_PASS`와 `W5-G1_REVALIDATED`다. evidence gap은 확인 불가
근거로 분리됐고 RYP9 blocker와 stale run은 계속 미해결이다. 이 항목들은
해결되거나 승격 승인된 것으로 보지 않는다.

## 남은 작업

1. 위 확정 SHA·manifest hash를 Deploy 01 DEP0~DEP1에 인계한다.
2. RYP9 `accepted→duplicate` 29건은 기존 accepted를 계속 보존한다.
3. orphan `youthcenter` CollectionRun을 승인된 stale 처리 경로로 정리하되,
   RA0 DB dump와 변경 전 수치는 그대로 보존한다.
