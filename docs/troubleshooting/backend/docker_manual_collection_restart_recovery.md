# Docker 수동 수집·재시작 복구

## 문제 상황

2026-08-23 DEP5 Backend 역할 검증에서 receipt `e5d18bd`를 독립 Compose project와
빈 Volume에 복원했다. 초기 기준은 Policy 3,273건, CollectionRun 61건,
Alembic `20260810_0006`이었다.

인증된 관리자가 `POST /api/v1/admin/collection-runs`를 호출하자 `202 Accepted`와
`running` 행은 생성됐지만 실제 Collector·import process가 실행되지 않았다.
3초 뒤에도 `finished_at`은 `null`, 모든 처리 count는 0, backend runtime Raw 파일은
0건이었고 container process 목록에는 Uvicorn만 존재했다.

새 행 때문에 CollectionRun이 62건이 된 상태에서 Compose를 재기동하면 `migrate`
service가 `verify_restored_database.py`를 다시 실행해 snapshot 고정 수치 61과
다르다는 이유로 종료했다. 즉, 정상적인 애플리케이션 쓰기가 다음 재시작을 막는
차단 결함이었다.

## 원인

원인은 서로 독립적인 두 구현 오류였다.

1. 수동 실행 service는 DB에 `running` 행만 commit하고 실제 Collector 호출이나
   종료 상태 갱신을 연결하지 않았다.
2. restore 무결성 검사와 일반 Migration이 한 service에 묶여 있어, restore 직후
   한 번만 확인해야 할 불변 snapshot 집계를 모든 재시작에 강제했다.

단위 테스트도 `202`와 `running` 행 생성만 확인했기 때문에 실제 상태 전이 누락을
탐지하지 못했다.

## 해결 과정

- `verify-restored`를 restore profile의 별도 one-shot service로 만들고
  `restore.ps1`이 data restore 직후 실행하도록 순서를 고정했다.
- 일반 `migrate`는 `alembic upgrade head`만 수행해 운영 중 추가·변경된 데이터를
  보존하도록 했다.
- 관리자 수동 실행은 같은 `run_id`를 사용해 등록된 live Collector, Runtime Raw
  replay, PostgreSQL import와 terminal 상태 기록을 background task로 연결했다.
- 등록되지 않은 Source와 500건 초과 요청은 `422`로 차단하고, 키 누락·Source
  drift·import 실패는 `running`에 방치하지 않고 `failed`로 종결한다.
- Docker Backend에 선택적으로 `YOUTHCENTER_API_KEY`와 `BOKJIRO_API_KEY`를
  전달하되 실제 값은 무시되는 `.env.compose` 밖으로 노출하지 않는다.

## 실제 결과

수정 작업tree를 새 BE Volume에 다시 복원하고 키가 필요 없는 공식 천안 청년센터
Source를 1건 요청했다.

| 항목 | 수정 전 | 수정 후 |
| --- | --- | --- |
| API 응답 | `202`, 실행 없음 | `202`, 실제 background 실행 |
| 최종 상태 | `running` 고착 | `succeeded`, `finished_at` 기록 |
| 처리 근거 | Raw 0, count 전부 0 | Raw 3, accepted 1, unchanged 1 |
| 재시작 | CollectionRun 62에서 Migration 차단 | stop/up 성공 |
| 재시작 전후 DB | 검증 불가 | Policy 3,273·Run 62 유지 |
| 서비스 health | Backend·Frontend 기동 실패 | DB·Backend·Frontend 모두 healthy |

관련 Backend 회귀는 `177 passed, 17 skipped`였으며 PostgreSQL actual에서 이번
수동 실행의 failed count는 0이었다. snapshot에 원래 포함된 과거 running 1건은
이번 실행과 다른 이력으로 그대로 보존했다.

## 남은 경계

이 구현은 W4에서 승인한 단일 API process 내부 수동 실행 경계다. 자동 주기 실행,
다중 instance lease, 중앙 queue·worker, 정책 마감 일일 정산은 Production 데이터
갱신 파이프라인의 별도 범위다. 또한 위 수치는 commit 전 수정 작업tree에서 얻은
값이므로 새 receipt의 역할별 재검증이 끝나기 전에는 Docker Acceptance PASS
근거로 사용하지 않는다.
