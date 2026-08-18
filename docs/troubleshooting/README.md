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

- [Windows PostgreSQL 테스트 환경 복구](backend/windows_postgresql_test_environment.md):
  다른 PC의 Unix 가상환경, PostgreSQL 역할 인증과 전용 테스트 DB를 Windows
  환경에서 복구한 실제 절차
- [추천 전체 정책 판정의 N+1과 오추천 해결](backend/recommendation_full_inventory_performance.md):
  첫 200건 제한과 가산점 방식의 오추천을 바로잡고, 전체 3,273건 평가에서
  드러난 지역 판정 N+1을 bulk 조회로 개선한 실제 과정
