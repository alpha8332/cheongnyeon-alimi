# 개발 계획 안내

이 디렉터리는 아직 완료하지 않은 작업의 범위, 의존성, 수행 순서와 완료
기준을 Forest 단위로 관리한다. 실제 구현과 검증 결과는
[`development_notes/`](../development_notes/README.md)에 기록한다.

## 현재 개발 계획

| 번호 | Forest | 계획 | 상태 |
| --- | --- | --- | --- |
| Integration 01 | Docs System | [개발 계획](integration/01_docs_system.md) | completed |
| Data 01 | Data Pipeline | [개발 계획](data/01_data_pipeline.md) | completed |
| Data 02 | Release Dataset Bootstrap | [개발 계획](data/02_release_dataset_bootstrap.md) | completed |
| Data 03 | Recurrent Collection and Quality Operations | [개발 계획](data/03_recurrent_collection_quality_operations.md) | completed |
| Data 04 | Public HTTPS Policy Ingestion | [개발 계획](data/04_public_https_policy_ingestion.md) | in-progress |
| Data 05 | Regional Youth Policy Ingestion | [개발 계획](data/05_regional_youth_policy_ingestion.md) | completed |
| Data 06 | Supplemental Official Policy Ingestion | [개발 계획](data/06_supplemental_official_policy_ingestion.md) | approved |
| Frontend 01 | Policy Discovery | [개발 계획](frontend/01_policy_discovery.md) | completed |
| Frontend 02 | React Router Advisory Review | [개발 계획](frontend/02_react_router_advisory.md) | completed |
| Frontend 03 | CollectionRun Admin UI | [개발 계획](frontend/03_collection_run_admin_ui.md) | draft |
| Frontend 04 | Policy Search | [개발 계획](frontend/04_policy_search.md) | completed |
| Frontend 05 | User Service Features | [개발 계획](frontend/05_user_service_features.md) | draft |
| Frontend 06 | Recommendation UI | [개발 계획](frontend/06_recommendation_ui.md) | draft |
| Frontend 07 | Eligibility Summary UI | [개발 계획](frontend/07_eligibility_summary_ui.md) | draft |
| Frontend 08 | Admin Observability UI | [개발 계획](frontend/08_admin_observability_ui.md) | draft |
| Frontend 09 | Integration Fix and Regression | [개발 계획](frontend/09_integration_and_regression.md) | draft |
| Backend 01 | Backend Baseline | [개발 계획](backend/01_policy_baseline.md) | completed |
| Backend 02 | Policy Persistence Hardening | [개발 계획](backend/02_policy_persistence_hardening.md) | completed |
| Backend 03 | Policy Runtime Safety | [개발 계획](backend/03_policy_runtime_safety.md) | completed |
| Backend 04 | Admin Access Control | [개발 계획](backend/04_admin_access_control.md) | draft |
| Backend 05 | CollectionRun Admin API | [개발 계획](backend/05_collection_run_admin_api.md) | draft |
| Backend 06 | Policy Search | [개발 계획](backend/06_policy_search.md) | completed |
| Integration 02 | Policy Data Database Integration | [개발 계획](integration/02_policy_data_database_integration.md) | completed |
| Integration 03 | Policy Search Data Foundation | [개발 계획](integration/03_policy_search_data_foundation.md) | completed |
| Integration 04 | Release 1 Acceptance | [개발 계획](integration/04_release_1_acceptance.md) | completed |
| Integration 05 | v0.5.0 Contract Baseline | [개발 계획](integration/05_v0_5_0_contract_baseline.md) | completed |
| Integration 06 | Recommendation Vertical Slice | [개발 계획](integration/06_recommendation_vertical_slice.md) | draft |
| Integration 07 | Release 2 Feature Acceptance | [개발 계획](integration/07_release_2_feature_acceptance.md) | in-progress |
| Integration 08 | Eligibility Evidence and Summary | [개발 계획](integration/08_eligibility_evidence_summary.md) | completed |
| Integration 09 | Admin Data and Log Console | [개발 계획](integration/09_admin_data_log_console.md) | draft |

새 Forest 계획을 추가하면 이 표와 [`docs/index.md`](../../index.md)를 함께
갱신한다.

## Release·Forest·주차 로드맵

다음 문서는 개별 Forest 계획을 대신하지 않고 여러 Forest의 릴리스 목표와
실행 순서를 동기화한다.

- [Release와 Milestone 계획](release_roadmap.md): `v0.1.0`, `v0.5.0`,
  `v1.0.0` 목표와 통합 완료 조건
- [전체 Forest 로드맵](forest_roadmap.md): 완료 기반, 후속 Forest,
  의존성과 권장 브랜치 단위
- [주차별 실행 계획](weekly_delivery_plan.md): 1~6주차 인계 순서와
  릴리스별 검증 게이트
- [주차별 상세 실행 계획](../weekly_plan/README.md): 실제 주차의 병렬 작업,
  역할별 책임과 단계별 Gate

## 다음 Forest 실행 순서

`v0.1.0`은 `main` 커밋 `2b33ed7`과 tag `v0.1.0`으로 발행됐다. 4주차 결과는
`develop`의 `f0d3dd3`에 병합되고 `W4-G4_MIDPOINT_PASS`를 통과했다. 다음
작업은 Data 06 구현·안정화와 Integration 07의 독립 검증·Release 2 Gate다.

| 우선순위 | 작업 또는 조건부 위험 | 결정 | 권장 브랜치 |
| ---: | --- | --- | --- |
| 완료 | 2주차 Backend 안전성·Router advisory | Backend 03과 Frontend 02 완료 | `fix/backend/week2-hardening` |
| 완료 | `R1-REAL-DATA-BOOTSTRAP` | 실제 Source 릴리스 범위 수집·DB 초기 적재 | `feature/data/release-dataset-bootstrap` |
| 완료 | `R1-SEARCH-DATA-FOUNDATION` | Source 중립 검색 필드·지역 계층·DB 관계·projection | `feature/database/policy-search-foundation` |
| 완료 | `R1-POLICY-SEARCH` | Backend 서버 검색 → Frontend 자연어 조건 연결 | `feature/backend/policy-search`, `feature/frontend/policy-search` |
| 완료 | `R1-REAL-DATA-ACCEPTANCE` | golden query와 실제 DB·API·Browser 인수, G4 통과 | `feature/data/release-dataset-bootstrap` |
| 완료 | `R2-CONTRACT-BASELINE` | 저장·인증·웹 Source·자격요건·추천·수동 실행·품질 노출 W4-G0~G4 통합 | `feature/integration/week-04-acceptance` |
| W4-G0 뒤 | `BE-ADMIN-RUN-HISTORY` | Backend 04 → Backend 05 → Frontend 03 | `feature/backend/admin-run-management` |
| W4-G0 뒤 필수 | `R2-ADMIN-DATA-LOG` | 읽기 전용 정책 데이터 표와 구조화 파일 로그·조회·archive 삭제·감사 | Backend·Frontend observability 브랜치 |
| W4-G0 뒤 필수 | `R2-PUBLIC-WEB-SOURCE` | 공식 HTTPS Source 1곳 목록·상세 → DB 적재 | `feature/data/public-web-policy-source` |
| W4-G0 뒤 필수 | `R2-ELIGIBILITY-SUMMARY` | 원문 근거 → 상세 API → 핵심 신청 조건 UI | 영역별 브랜치, 병합 순서는 W4-G0 확정 |
| W4-G0 뒤 | `R2-RECOMMENDATION` | 결정적 추천 API → 이유·미확정 조건 UI | Backend·Frontend 추천 브랜치 |
| W4-G0 뒤 | `R2-USER-SERVICE` | localStorage 조건·즐겨찾기·D-Day·알림·`.ics` | `feature/frontend/user-service-features` |
| W4-G0 뒤 | `R2-DATA-QUALITY` | 반복 수집·수정·중복·실패 통계 | `feature/data/recurrent-quality-operations` |
| W4-G1 병렬·`v0.5.0` 필수 | `REGIONAL-YOUTH-POLICY-INGESTION` | 지역 고유 정책 Source 탐색·중복 제외·실데이터 적재 | `feature/data/regional-youth-policy-ingestion` |
| 다음·`v0.5.0` 필수 | `SUPPLEMENTAL-OFFICIAL-POLICY-INGESTION` | 온통청년·복지로 누락 중앙·공공기관 Source 중복 감사·실데이터 적재 | `feature/data/supplemental-official-policy-ingestion` |
| Data 06 뒤 | `R2-FEATURE-ACCEPTANCE` | actual E2E·독립 사용성·QA·수정본 재검증과 Release 2 판정 | 착수 전 integration domain 합의 |
| 보류 | `SOURCE-NULL-ID` | external ID 없는 새 Source가 실제 도입될 때 재개 | 현재 브랜치 생성 안 함 |

```text
fix/backend/week2-hardening
  → develop 병합
  → Data 02 DT0~DT1 실제 Source 근거
  → Integration 03 검색 데이터 기반
  → DT2 Data 권고 + Backend 06·Frontend 04 초안
  → Gate G1 검색 계약 공동 승인
  ├→ Data 02 DT3~DT4 실제 데이터 기준선
  ├→ Backend 06 서버 검색
  └→ Frontend 04 승인 Mock·검색 UI → Backend endpoint 뒤 실제 API 연결
  → Integration 04 실데이터 인수
  → v0.1.0 (`main` 2b33ed7)
  → Integration 05 W4-G0
  ├→ Backend 04 → Backend 05 → Frontend 03
  ├→ Backend 04 → Integration 09 Admin Data and Log Console
  ├→ Data 04 Public Web → Integration 08 Eligibility Summary
  ├→ Integration 08 → Integration 06 Recommendation
  ├→ Frontend 05 User Service Features
  └→ Data 03 Quality Operations
  → Integration 07 midpoint·리뷰·Release 2 Gate
```

Data 02와 Integration 04에서 실제 Release snapshot 3,156건의 Runtime DB
적재, Backend 서버 검색과 Frontend actual API 연결을 검증했다. 공개 목록 API의
client-only 검색이 아니라 `GET /api/v1/policies/search`를 Release 1 검색
기준으로 사용한다.

관리자 기능은 `v0.5.0` 범위에서 인증·권한 → Backend API → Frontend UI
의존 순서를 지킨다. 이 표의 미래 작업은 `docs/index.md`의 활성 인계사항이
아니며, 구현 중 실제 영역 간 차단 조건이 생길 때만 인계 보드에 기록한다.

`SOURCE-NULL-ID`는 실제 대상 Source가 없을 때 대체 identity 규칙을
일반화하지 않고 `trigger-based` 상태를 유지한다.

## Forest 기준

- 하나의 목표와 결과 흐름을 공유하는 작업 집합을 Forest로 관리한다.
- Forest마다 개발 계획 문서 하나를 둔다. 실제 구현을 시작하면 같은 담당
  영역에 개발 기록 문서 하나를 만든다.
- Forest 안의 Slice는 계획 문서 내부에서 순서, 의존성과 완료 기준을
  구분한다.
- Slice마다 별도 계획 파일을 만들지 않는다.
- 독립적인 목표, 산출물과 완료 기준이 생길 때 새 Forest 계획을 만든다.

담당 영역이 명확한 Forest는 다음 경로를 사용한다.

| 영역 | 경로 | 사용 기준 |
| --- | --- | --- |
| Data | `data/` | 수집, 추출, 정규화, 검증과 Fixture·Seed |
| Backend | `backend/` | API, 서비스, DB 연동과 Backend 기능 |
| Frontend | `frontend/` | 화면, 상태 관리와 사용자 상호작용 |
| Integration | `integration/` | 둘 이상의 영역 또는 팀 공통 기반 |

실제 계획 문서가 생길 때만 해당 디렉터리를 생성한다. 담당 영역이 불명확하면
임의로 분류하지 않고 범위를 먼저 합의한다.

예:

```text
data/01_data_pipeline.md
backend/01_favorites.md
frontend/01_calendar.md
integration/01_policy_delivery.md
```

현재 데이터·API 계약 자체는 Forest 계획에만 적지 않고 각각 `docs/data/`와
`docs/api/`의 기준 문서에도 반영한다.

## 상태

| 상태 | 의미 |
| --- | --- |
| `draft` | 검토 전 초안 |
| `approved` | 범위와 완료 기준이 합의됨 |
| `in-progress` | 하나 이상의 Slice를 구현 중 |
| `completed` | Forest 전체 완료 기준과 검증을 충족함 |
| `superseded` | 다른 계획으로 대체됨 |

Forest가 `completed`가 되면 관련 개발 기록과 커밋 또는 PR을 연결한다.
`superseded`가 되면 대체 계획과 변경 이유를 기록한다.
`draft`와 `approved` 계획은 아직 구현 결과가 없으므로 개발 기록을 요구하지
않는다. `in-progress`로 변경할 때 대응하는 개발 기록을 생성한다.

## 계획 문서 필수 항목

```markdown
# Forest 이름

## 계획 정보
## 목적
## 범위
## 범위 밖
## 선행 조건
## 공통 설계 원칙
## Slice 계획
## 검증 계획
## Forest 완료 기준
## 위험과 미확정 사항
## 관련 문서
```

각 Slice에는 목적, 산출물, 선행 조건과 완료 기준을 포함한다. Issue, 브랜치나
구현 파일이 확정되지 않았다면 `미정`으로 표시한다.

## 운영 규칙

1. Forest 시작 전에 목적, 범위, 범위 밖과 전체 완료 기준을 검토한다.
2. Slice를 시작할 때 선행 조건과 미확정 사항을 확인한다.
3. 구현 중 설계가 바뀌면 계획의 결정과 이유를 갱신한다.
4. 완료한 Slice의 결과와 검증은 Forest 개발 기록에 상세히 남긴다.
5. 계획과 개발 기록에 같은 내용을 장문으로 중복하지 않고 서로 연결한다.
6. 완료된 계획을 삭제하지 않고 추적 정보를 유지한다.
7. 비밀키, 개인정보와 비공개 원문을 기록하지 않는다.
8. 실제 내용이 없는 계획 파일과 빈 디렉터리를 만들지 않는다.
9. `draft`나 진행 중인 계획 자체는 CHANGELOG에 기록하지 않고, Forest 완료
   결과가 팀이나 사용자에게 의미 있을 때만 1~2개 항목으로 요약한다.
