# 개발 기록 안내

이 디렉터리는 완료한 기능과 주요 구조 변경의 구현·검증 결과를 Forest
단위로 관리한다. Slice마다 문서를 만들거나 모든 개발 이력을 하나의 파일에
누적하지 않는다.

## 현재 개발 기록

| Forest | 문서 | 관련 Slice | 내용 |
| --- | --- | --- | --- |
| Docs System | [개발 기록](integration/docs_system.md) | D0~D6 | 문서 구조, 정책, 기준선, 계획과 품질 검증 |
| Data Pipeline | [개발 기록](data/data_pipeline.md) | Data 0 | API Source Preflight와 비밀정보 경계 |
| Release Dataset Bootstrap | [개발 기록](data/release_dataset_bootstrap.md) | DT0~DT4 | Release 1 실제 정책 수집·적재 기준선과 검증 |
| Policy Discovery | [개발 기록](frontend/policy_discovery.md) | FE 2~FE 2A | 공개 Policy DTO·Mock/API Client·정책 UI |
| Policy Search | [개발 기록](frontend/policy_search.md) | FE4-11~ | Gate G1 search contract types·Mock-first Search UI |
| Recommendation UI | [개발 기록](frontend/recommendation_ui.md) | FE6-00 | recommendation DTO·Mock·`/recommendations` route |
| Recommendation UI | [개발 기록](frontend/recommendation_ui.md) | FE6-00~05 | 조건 form·결과·error·Browser E2E |
| User Service Features | [개발 기록](frontend/user_service_features.md) | FE5-00~08, FE5-07 E2E | localStorage·즐겨찾기·조건·D-Day·Browser |
| CollectionRun Admin UI | [개발 기록](frontend/collection_run_admin_ui.md) | FE3-00~04 | PIN session·실행 기록·수동 실행 |
| Eligibility Summary UI | [개발 기록](frontend/eligibility_summary_ui.md) | FE7-00 | eligibility_summary DTO·Mock fixtures |
| Admin Observability UI | [개발 기록](frontend/admin_observability_ui.md) | FE8-00 | admin policy·log DTO·Mock handlers |
| React Router Advisory Review | [개발 기록](frontend/react_router_advisory.md) | F0~F3 | v8 migration·자동 회귀 완료, 데스크톱 Browser 회귀 대기 |
| Backend Baseline | [개발 기록](backend/policy_baseline.md) | Backend 0 | DB Schema, ORM 모델, Importer 및 Policy API 구축 |
| Backend Policy Persistence Hardening | [개발 기록](backend/policy_persistence_hardening.md) | B0~B6 | PostgreSQL 저장·Importer·Repository·Policy API 종단 검증 |
| Backend Policy Runtime Safety | [개발 기록](backend/policy_runtime_safety.md) | R0~R3 | Policy timestamp 순서와 SQL parameter logging 안전화 |
| Backend Policy Search | [개발 기록](backend/policy_search.md) | W3-B0~B4 | PostgreSQL 기반 정책 검색 API·파서 및 DTO 구현 |
| Policy Data Database Integration | [개발 기록](integration/policy_data_database_integration.md) | D0~D6 | Seed·Runtime의 PostgreSQL 적재와 Policy API 통합 검증·Frontend 인계 |
| Policy Search Data Foundation | [개발 기록](integration/policy_search_data_foundation.md) | PSF0~PSF8 | Source 중립 검색 데이터·지역 관계·projection 기반과 소비 검증 |
| Release 1 Acceptance | [개발 기록](integration/release_1_acceptance.md) | IA0~IA3F | 실제 snapshot DB → API → UI 인수, 경량 팀 리뷰와 Release 1 G4 통과 |

새 Forest 개발 기록을 추가하면 이 표와 [`docs/index.md`](../../index.md)를
함께 갱신한다.

## Forest 기준

- 하나의 Forest마다 계획과 같은 담당 영역에 개발 기록 문서 하나를 작성한다.
- Forest 내부의 Slice는 문서 안의 섹션과 진행 표로 구분한다.
- 같은 목표와 결과 흐름을 가진 Slice를 별도 문서로 쪼개지 않는다.
- 목표, 산출물과 완료 기준이 독립적인 새 Forest가 시작될 때 새 문서를
  만든다.
- 파일명은 Forest를 나타내는 소문자 `snake_case`를 사용한다.

예:

```text
docs_system.md
data/data_pipeline.md
backend/favorites.md
frontend/calendar.md
integration/policy_delivery.md
```

담당 영역과 독립적인 완료 기준을 가진 Forest별로 상세 개발 기록을 작성한다.
예시는 파일 이름 형식이며 현재 구현 완료나 해당 디렉터리의 사전 생성을
뜻하지 않는다.

Data, Backend와 Frontend 중 한 영역의 구현 결과는 해당 영역에 기록한다.
Seed → API → 화면처럼 여러 영역을 하나의 완료 기준으로 검증한 결과는
`integration/`에 기록한다. 한 영역의 상세 구현 기록과 통합 검증 결과가 모두
필요하면 서로 링크하고 같은 내용을 장문으로 복제하지 않는다.

## 필수 항목

각 Forest 개발 기록은 다음 내용을 포함한다.

```markdown
# Forest 이름

## 작업 정보
## 목적
## Forest 범위
## Slice 진행 현황
## 구현 내용
## 주요 변경 파일
## 설계 결정
## 검증 결과
## 남은 작업
```

- 작업 정보에는 기간, 영역, 브랜치와 관련 Forest 계획 또는 Issue를
  기록한다.
- Slice별 구현 내용은 같은 문서 안에 누적하되 Forest 전체 맥락과 결정이
  보이도록 유지한다.
- 실행한 검증만 결과로 기록한다.
- 미실행·실패 항목과 알려진 제약을 숨기지 않는다.
- 미래 구현 상세는 `docs/development/develop_plan/`에 둔다.
- Forest가 완료되면 사용자와 팀에 의미 있는 결과만 루트 `CHANGELOG.md`에
  1~2개 항목으로 요약하고 이 개발 기록을 링크한다.
- 실제 발생하고 해결된 문제는 `docs/troubleshooting/`에 기록한다.

## 상태와 변경

개발 기록은 Forest가 진행되는 동안 같은 문서에 정확하게 누적한다. Forest가
완료되면 최종 결과와 남은 제약을 정리한다. 후속 Forest가 기존 결정을
변경하면 이전 기록을 조용히 다시 쓰지 않고 새 개발 기록에서 변경 이유와
영향을 연결한다.
