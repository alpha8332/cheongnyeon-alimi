# 전체 Forest 로드맵

## 문서 정보

- 상태: approved
- 기준일: 2026-08-07
- 역할: 완료 Forest와 릴리스별 후속 Forest의 순서·의존성 조정

이 문서는 포트폴리오 수준의 순서를 정한다. `draft`, `approved`,
`in-progress`, `completed`, `superseded` 상태는 개별 Forest 계획 문서에서만
확정한다. 아래에서 `계획 필요`로 표시한 항목은 구현 전에 담당 영역에 독립
Forest 계획을 만들고 [`README.md`](README.md) 색인에 등록해야 한다.

## 완료된 기반

| Forest | 상태 | 제공 기준선 |
| --- | --- | --- |
| Integration 01 Docs System | completed | 문서·거버넌스·검증 체계 |
| Data 01 Data Pipeline | completed | 두 Source 제한 수집, Schema·Fixture·Seed |
| Backend 01 Policy Baseline | completed | FastAPI와 기본 Policy 계약 |
| Frontend 01 Policy Discovery | completed | 사용자 목록·상세·필터 UI |
| Backend 02 Policy Persistence Hardening | completed | Migration·PostgreSQL·Importer·API |
| Integration 02 Policy Data Database Integration | completed | Seed·Runtime 적재 경계와 실제 API 연결 |
| Backend 03 Policy Runtime Safety | completed | timestamp와 SQL logging 안전화 |
| Frontend 02 React Router Advisory Review | completed | Router v8 전환과 Browser 회귀 |

완료는 각 Forest가 정의한 합성 Seed, 제한 수집 또는 안전성 범위의 완료를
뜻한다. 실데이터 릴리스 snapshot, 서버 keyword·age 검색과 자동 Scheduler가
완료됐다는 의미는 아니다.

## `v0.1.0` Forest

| 순서 | Forest | 주 담당 | 참여·검증 | 상태 | 핵심 산출물 | 선행 조건 |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | [Data 02 Release Dataset Bootstrap](data/02_release_dataset_bootstrap.md) | Data | Backend·Frontend 소비 검토 | completed | 실제 정책 3,159건 bootstrap, 멱등 재실행, 품질 Profile과 안전한 검색 사례 인계 | Data 01, Integration 02, DT2부터 Integration 03 |
| 2 | [Integration 03 Policy Search Data Foundation](integration/03_policy_search_data_foundation.md) | Data·Backend 공동 | Frontend 소비·Team Leader Gate | completed | PSF0~PSF8 Source 중립 계약·지역 기준정보·mapping·원자적 적재·판정·소비·성능·actual 재생과 전체 Gate 완료 | Data 02 DT1 |
| 3 | [Backend 06 Policy Search](backend/06_policy_search.md) | Backend | Data 계약·Frontend 소비 검토 | completed | 구체 term anchor·일반어 fallback, 실제 golden 1위·2초 예산과 전체 PostgreSQL 회귀 통과 | Integration 03 판정 primitive, Data 02 DT2와 Gate G1 |
| 4 | [Frontend 04 Policy Search](frontend/04_policy_search.md) | Frontend | Backend API 검토 | completed (`DT7D actual 재검증`) | 자연어 원문 전달, Backend 해석 조건·검색 이유·미확인 조건·자격 비확정 안내, actual API Browser·E2E | Integration 03·Data 02 DT2·Gate G1, Integration 04 actual API |
| 5 | [Integration 04 Release 1 Acceptance](integration/04_release_1_acceptance.md) | Team Leader - Integration | Data·Backend·Frontend, 경량 QA·사용성 리뷰 | completed (`IA3F`, `G4 pass`) | golden 기술·기간 안전성·FE actual 검증, 경량 팀 리뷰와 Release 1 후보 승인 | Data 02, Integration 03, Backend 06, Frontend 04 |

위 Release 1 Forest 결과는 `2026-08-06` 커밋 `4629a61`로 `develop`에
병합됐고 PR #15의 `main` 커밋 `2b33ed7`과 `v0.1.0` tag로 발행됐다.
`develop`도 같은 커밋으로 fast-forward해 후속 Forest의 기준점을 맞췄다.

Data 02는 수집 시각의 전체 외부 데이터를 무조건 저장한다는 의미가 아니다.
API pagination·할당량·이용 조건을 확인해 “릴리스 수집 범위”를 먼저 고정한다.
그 범위 안에서는 첫 페이지만 임의로 적재하지 않고 재현 가능한 순회를
제공해야 한다.

Backend 06은 기존 Backend 04·05 번호를 관리자 Forest가 이미 사용하므로
번호를 바꾸지 않고 다음 번호를 사용한다. Frontend도 기존 Frontend 03을
보존한다.

Integration 03은 DT1에서 확인한 현재 지역·검색 필드 구조의 실제 충돌을
해결하는 공통 기반이다. 기존에 계획 이름만 있던 Release 1 Acceptance는
Integration 04로 이동한다. 완료 문서 번호를 바꾸지 않으며 아직 생성되지
않은 계획의 번호만 조정한다.

### `v0.1.0` 의존 흐름

```text
Data 02 DT0~DT1 실제 Source 근거
  → Integration 03 검색 데이터 기반
  → Data 02 DT2 Data 권고 + Backend 06·Frontend 04 초안
  → Gate G1 검색 계약 공동 승인
  ├→ Data 02 DT3~DT4 실제 데이터 기준선
  ├→ Backend 06 자연어 해석·서버 검색
  └→ Frontend 04 승인 Mock·검색 UI
                    ↓ Backend endpoint 준비
                 Frontend 실제 API 연결
  → Integration 04 실데이터 인수 검증
  → v0.1.0
```

Data 02의 actual profile, Backend 06의 API·Repository 계약 초안과 Frontend 04의
타입·표시 계약 초안은 Gate G1 입력으로 병행한다. G1 전에는 각 영역의
현재 구조 분석과 별도 Forest·Slice 계획만 준비하고 계약에 의존하는 코드
구현은 시작하지 않는다. G1 승인
뒤 Data DT3~DT4, Backend 06과 Frontend 04 본 구현을 병렬로 진행하고 실제
Frontend API 연결은 Backend endpoint를 기다린다.

## `v0.5.0` Forest

기존 관리자 계획은 폐기하지 않고 Integration 05 W4-G0 승인 뒤 실행한다.

| 순서 | Forest | 주 담당 | 참여·검증 | 상태 | 핵심 산출물 | 선행 조건 |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | [Integration 05 v0.5.0 Contract Baseline](integration/05_v0_5_0_contract_baseline.md) | Team Leader - Integration | Data·Backend·Frontend 공동 검토 | approved | 저장·인증·웹 Source·자격요건·추천·관리자 데이터·로그·수동 실행·품질 W4-G0 | `v0.1.0` publication |
| 2 | [Backend 04 Admin Access Control](backend/04_admin_access_control.md) | Backend | Team Leader 보안·통합 검토 | draft | 관리자 인증·권한 기준선 | Integration 05 |
| 3 | [Backend 05 CollectionRun Admin API](backend/05_collection_run_admin_api.md) | Backend | Data·Team Leader 운영 검토 | draft | 실행 이력·상세·수동 실행·stale 판정 | Backend 04 |
| 4 | [Frontend 03 CollectionRun Admin UI](frontend/03_collection_run_admin_ui.md) | Frontend | Backend 소비 검토 | draft | 이력·실패·수동 실행 UI | Backend 05 |
| 5 | [Data 04 Public HTTPS Policy Ingestion](data/04_public_https_policy_ingestion.md) | Data | Team Leader Source 승인, Backend 소비 검토 | in-progress | 공식 HTTPS Source 1곳의 목록·상세·조건 근거 수집과 DB 적재 | Integration 05, Data 01 |
| 6 | [Integration 08 Eligibility Evidence and Summary](integration/08_eligibility_evidence_summary.md) | Data·Backend·Frontend | Team Leader 계약·실제 E2E | in-progress | ES3 핵심 조건·제외·서류·문의처 UI 완료, ES4 실제 DB→API→Browser 대기 | Integration 05, Data 04 병렬 보강 |
| 7 | [Integration 09 Admin Data and Log Console](integration/09_admin_data_log_console.md) | Backend·Frontend | Team Leader 보안·운영 검토 | draft | 읽기 전용 정책 데이터 표, 구조화 파일 로그·조회·archive 삭제 UI | Integration 05, Backend 04 |
| 8 | [Integration 06 Recommendation Vertical Slice](integration/06_recommendation_vertical_slice.md) | Backend·Frontend | Data 조건 검토, 리뷰어·QA 검증 | draft | 결정적 추천, 이유·미확정 조건과 실제 UI | Integration 05·08, v0.1.0 검색 |
| 9 | [Frontend 05 User Service Features](frontend/05_user_service_features.md) | Frontend | Team Leader 계약, 리뷰어·QA 검증 | draft | localStorage 조건·즐겨찾기·D-Day·내부 알림·`.ics` | Integration 05 |
| 10 | [Data 03 Recurrent Collection and Quality Operations](data/03_recurrent_collection_quality_operations.md) | Data | Backend 소비·Team Leader 통합 | completed | 반복 수집, 수정·중복·실패 격리와 품질 통계 | Integration 05, Data 02 |
| 11 | [Integration 07 Release 2 Feature Acceptance](integration/07_release_2_feature_acceptance.md) | Team Leader - Integration | 전 담당, 사용성 리뷰어·QA·보고서 | draft | 4주차 midpoint, 5주차 hardening과 Release 2 Gate | 모든 v0.5.0 기능 |

Frontend 05는 W4-G0 제안대로 서버 사용자 계정 없이 브라우저 로컬 기능만
다루므로 Frontend 독립 Forest로 둔다. Data 04는 Source 선정·수집·추출·적재라는
독립 완료 기준이 있어 Data 03 품질 운영에 섞지 않는다. Integration 08은
Data Schema·Backend 상세 DTO·Frontend 상세 UI가 함께 바뀌므로 Integration
Forest로 관리한다. Integration 06은 승인된 조건 구조를 추천에 소비한다.
Integration 09는 관리자 인증 위에서 DB projection·파일 보존·API·UI와 삭제
감사 경계가 함께 바뀌므로 독립 Integration Forest로 둔다. Schema, `null`,
빈 배열 또는 enum을 바꾸면 Data·Backend·Frontend 소비 검토와 기준 문서를
같은 Forest에서 갱신한다.

### `v0.5.0` 의존 흐름

```text
v0.1.0 → W4-G0
  ├→ 관리자 인증 → 실행 API·데이터 표·로그 API → 관리자 UI ┐
  ├→ 공식 웹 Source → 자격요건 상세 API·UI ┤
  ├→ 자격요건 → 추천 API·UI ──────────────┤
  ├→ Frontend 로컬 사용자 기능 ───────────┤
  └→ 데이터 품질 운영 ────────────────────┘
                  → midpoint → 리뷰·수정 → v0.5.0
```

## `v1.0.0` Forest

| 순서 | Forest | 주 담당 | 참여·검증 | 상태 | 핵심 산출물 | 선행 조건 |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | Open-source Deployment Pipeline | Team Leader - Integration·Deploy | Data·Backend·Frontend 지원, QA 검증 | 계획 필요 | Dockerfile, Compose, Nginx, Volume, health check, CI | v0.5.0 기능 동결 |
| 2 | Clean-room Distribution Verification | Team Leader - Integration·Deploy | QA 주 검증, 리뷰어 사용성 확인 | 계획 필요 | 새 환경 clone-to-run, migration·bootstrap·전체 시나리오 | 배포 파이프라인 |
| 3 | Final Documentation and Submission | 보고서 담당 | Team Leader 최종 확인, 전 담당 근거 제공 | 계획 필요 | README, 계약 문서, LICENSE, SBOM, 최종보고서·시연 자료 | clean-room 검증 |

Docker·Compose는 영역별 구현이 `develop`에 병합되고 manifest·lockfile과 실행
방법이 준비된 뒤 통합 담당이 구성한다. Kubernetes는 현재 완료 조건이 아니다.

## 브랜치 계획

2주차 `fix/backend/week2-hardening` 작업은 완료됐다. 3주차 Data 02와
Integration 03 결과는 `feature/data/release-dataset-bootstrap`에 병합돼 있다.
Backend 06과
Frontend 04는 이 기준선에서 각 Forest 브랜치를 분기해 DT2/G1 초안을
준비한다. 정확한 공통 시작 SHA는
[검색 계약 Gate G1 인수인계](../weekly_plan/week_03_search_contract_handoff.md)의
해석 명령으로 확인한다. 브랜치 생성과 커밋은 각 담당자의 명시적 작업 요청을
따른다.

구현 브랜치는 Forest 단위로 만든다. 권장 예시는 다음과 같다.

```text
feature/data/release-dataset-bootstrap
feature/database/policy-search-foundation
feature/backend/policy-search
feature/frontend/policy-search
docs/docs/v0-5-contract-baseline
feature/backend/admin-run-management
feature/backend/recommendation
feature/frontend/recommendation
feature/frontend/user-service-features
feature/data/recurrent-quality-operations
feature/data/public-web-policy-source
feature/backend/admin-observability
feature/frontend/admin-observability
feature/deploy/open-source-runtime
```

`feature/database/policy-search-foundation`은 Data 02 DT1 커밋에서 파생해
완료 후 `feature/data/release-dataset-bootstrap`에 병합하는 stacked 예외다.
Backend 06·Frontend 04도 완료된 검색 기반을 소비하기 위해 위 공통 커밋에서
분기한다. 기반·대상 브랜치와 검증 순서는 해당 Forest 계획에 명시하고,
Data 02가 `develop`에 병합되기 전에는 stacked 의존 관계와 병합 순서를 PR에서
숨기지 않는다.

Slice마다 새 브랜치를 만들지 않는다. 서로 다른 릴리스 목표나 독립 완료
기준을 한 브랜치에 장기간 누적하지 않는다.

Integration 07은 Data·Backend·Frontend 실제 통합과 리뷰 증거를 함께 다루지만
현재 브랜치 전략에는 `integration` domain이 없다. 착수 전 기존 domain 중
하나로 귀속할지 `integration` domain을 추가할지 합의하고, 그 전에는 임의의
브랜치를 만들지 않는다.

## 범위 변경 규칙

- 릴리스 완료 조건을 만족하지 못하면 다음 릴리스 기능을 끌어와 완료처럼
  보이지 않고 해당 릴리스 일정을 조정한다.
- 실제 Source 구조가 Schema와 충돌하면 Source 값을 억지로 맞추지 않고
  Data·Backend·Frontend 영향과 선택지를 공동 검토한다.
- 지원 Source에 golden query에 맞는 정책이 없다면 검색 결과를 조작하지
  않고 Source 추가 또는 릴리스 범위 변경을 결정한다.
- Scheduler·worker 분리는 동시성·안정성 조건이 확인될 때 ADR로 결정한다.
- 상세 Forest가 승인되면 이 로드맵의 상태·링크·순서를 갱신한다.

## 관련 문서

- [Release와 Milestone 계획](release_roadmap.md)
- [주차별 실행 계획](weekly_delivery_plan.md)
- [3주차 상세 실행 계획](../weekly_plan/week_03_release_1.md)
- [4주차 상세 실행 계획](../weekly_plan/week_04_v0_5_0.md)
- [검색 계약 Gate G1 인수인계](../weekly_plan/week_03_search_contract_handoff.md)
- [v0.5.0 Contract Baseline](integration/05_v0_5_0_contract_baseline.md)
- [Recommendation Vertical Slice](integration/06_recommendation_vertical_slice.md)
- [User Service Features](frontend/05_user_service_features.md)
- [Data Quality Operations](data/03_recurrent_collection_quality_operations.md)
- [Release 2 Feature Acceptance](integration/07_release_2_feature_acceptance.md)
- [Backend Admin Access Control](backend/04_admin_access_control.md)
- [Backend CollectionRun Admin API](backend/05_collection_run_admin_api.md)
- [Frontend CollectionRun Admin UI](frontend/03_collection_run_admin_ui.md)
- [역할과 책임](../../governance/role_assignment.md)
