# 문제 해결 문서

이 디렉터리는 실제로 발생했고 원인과 해결 방법이 확인된 문제를 영역별로
기록한다.

## 문서화 대상

- 해결에 상당한 시간이 소요된 문제
- 다른 개발자나 환경에서도 반복될 수 있는 문제
- 원인이 직관적이지 않은 문제
- 재사용 가능한 해결 또는 예방 방법이 확인된 문제

각 기록에는 증상, 발생 환경, 실제 원인, 해결 방법, 확인 방법과 예방 방법을
포함한다.

## 담당 영역

실제 문제 해결 문서를 추가할 때 다음 영역 중 하나에 둔다.

| 영역 | 경로 | 사용 기준 |
| --- | --- | --- |
| Data | `data/` | 수집, 추출, 정규화, Schema와 Fixture·Seed |
| Backend | `backend/` | API, 서비스, 데이터베이스 연동과 서버 실행 |
| Frontend | `frontend/` | 화면, 상태 관리, 브라우저와 UI 빌드 |
| Integration | `integration/` | 영역 간 계약, 연결 과정과 공통 개발 환경 |

문서가 없는 영역의 빈 디렉터리는 미리 만들지 않는다. 여러 영역에 걸친 원인은
주된 해결 책임이 하나로 명확하지 않으면 `integration/`에 기록한다.

예:

```text
data/source_encoding_error.md
backend/favorites_duplicate_insert.md
frontend/calendar_timezone_rendering.md
integration/seed_api_contract_mismatch.md
```

예상 오류, 재현하지 않은 문제와 해결되지 않은 추측은 이 디렉터리에
확정적으로 기록하지 않는다. 해결되지 않은 항목은 관련 Issue 또는
`docs/development/develop_plan/`에서 확인된 사실과 시도한 방법을 구분해
관리한다.

## 현재 문서

- [v1.0.2 공개 데이터·검색·추천 QA 개선](integration/v1_0_2_qa_improvements.md):
  작성자·심사자 활성 dataset 동등성, 지역 검색, 예시·복수 분야·프로필·정렬 오류를
  실제 API·Docker·Browser로 수정·검증한 기록
- [Windows clone·ZIP clean-room 복구](integration/windows_clone_zip_clean_room_recovery.md):
  project Volume 소유권·PowerShell hash/ACL·ZIP env·partial 목록·추천 렌더 문제를
  새 GitHub ZIP과 독립 Volume actual로 수정·재검증한 기록
- [공개 dataset 중앙 발행 activation 복구](integration/public_dataset_release_activation.md):
  worker readiness·오류 진단·GitHub Secret 형식 문제로 네 차례 fail-closed된
  중앙 수집을 실제 Release까지 복구하고 readiness 시간을 94.9% 줄인 기록
- [실측 기반 문제 해결·개선율 보고서](integration/measured_improvement_report.md):
  실제 전후 수치로 확인한 응답시간·데이터 오류·지역정책 판정 개선을 퍼센트와
  해석 경계로 종합한 보고서
- [Windows PostgreSQL 테스트 환경 복구](backend/windows_postgresql_test_environment.md):
  다른 PC의 Unix 가상환경, PostgreSQL 역할 인증과 전용 테스트 DB를 Windows
  환경에서 복구한 실제 절차
- [Docker 수동 수집·재시작 복구](backend/docker_manual_collection_restart_recovery.md):
  실행 없이 `running`만 만들던 관리자 API와 가변 DB 재시작을 막던 restore
  baseline 검증을 실제 Docker 재현으로 수정한 기록
- [Docker Acceptance 사용성·판정 일관성 복구](integration/docker_acceptance_usability_consistency.md):
  격리 역할 검증에서 발견한 지역 불일치 혼입·연령 sentinel·추천 설명 충돌·
  저장 조건 우선순위·Mock/actual 회귀 경계를 실제 UI와 API로 바로잡은 기록
- [추천 전체 정책 판정의 N+1과 오추천 해결](backend/recommendation_full_inventory_performance.md):
  첫 200건 제한과 가산점 방식의 오추천을 바로잡고, 전체 3,273건 평가에서
  드러난 지역 판정 N+1을 bulk 조회로 개선한 실제 과정
- [연령 `0세~0세` placeholder 오판 보정](data/release_age_placeholder_normalization.md):
  실제 631건의 근거 없는 0세 bound를 해제하고 미확정 3값 판정과 멱등
  재적재로 복구한 과정
- [지역 Browser 수집 실패·drift 안전 복구](data/regional_browser_capture_recovery.md):
  page-context·timeout·total·identity drift를 checkpoint·canary·제한 재시도로
  격리하고 field evidence를 완전 분류한 과정
- [Review admission 현재성·지역 projection 오적재 복구](data/review_admission_currentness_recovery.md):
  종료 정책과 region rule 없는 승격을 중단·보상 rollback하고 실행일 재판정과
  post-admission manifest 멱등성을 복구한 과정
- [Windows actual Runtime·DB 연결 환경 복구](integration/windows_actual_runtime_acceptance.md):
  DB 권한·Migration·실행기 DB 선택·Node 탐색·Runtime log 경계를 정렬해 실제
  PostgreSQL→FastAPI→React 인수를 완료한 과정
