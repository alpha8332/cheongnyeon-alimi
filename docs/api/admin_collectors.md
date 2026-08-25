# 관리자 수집기 상태 API

관리자 수집기 화면은 등록된 중앙 수집기와 실행 환경을 읽기 전용으로 조회한다.
API key·PIN·token·worker hostname·broker credential은 응답하지 않는다.

## 상태 조회

```http
GET /api/v1/admin/collectors
Authorization: Bearer <admin-session-token>
```

- 인증된 관리자만 호출할 수 있다.
- 응답은 현재 중앙 worker를 짧게 확인하므로 worker가 없거나 broker가 끊기면
  HTTP 오류 대신 `queue.worker_available=false`로 상태를 설명한다.
- 자동 수집 스케줄은 `schedule.enabled`로 구분하며 기본값은 비활성이다.

## 응답 경계

최상위 응답은 다음 세 영역으로 구성된다.

| 필드 | 의미 |
| --- | --- |
| `generated_at` | 서버가 상태 projection을 만든 UTC 시각 |
| `queue` | queue 이름, broker·worker 연결 여부, 응답 worker 수 |
| `schedule` | 활성 여부, source, 요청 수, cron 시·분, KST timezone |
| `collectors` | 등록 수집기별 안전한 운영 상태 |

수집기 항목은 `source_id`, 표시명, `api/file/web` 유형, worker 등록 여부,
인증정보의 `configured/missing/not_required/unknown` 상태, 활성 공개 dataset에
포함된 정책 수, 현재·최근 CollectionRun 요약을 제공한다. 인증정보는 존재 여부만
판정하며 값·길이·일부 문자열을 반환하지 않는다.

`runtime_status` 의미:

| 값 | 의미 |
| --- | --- |
| `ready` | worker에 등록됐고 필요한 인증정보가 준비됨 |
| `configuration_required` | worker는 있으나 해당 API 인증정보가 없음 |
| `unavailable` | worker가 없거나 해당 source가 worker에 등록되지 않음 |
| `unknown` | worker 응답만으로 안전하게 상태를 확정할 수 없음 |

`public_policy_count`는 로컬 전체 정책 수나 CollectionRun 삽입 수가 아니다. 현재
`active`인 공개 dataset membership에 포함된 source별 정책 수다. 따라서 작성자와
심사자의 CollectionRun 개수는 달라도 같은 dataset version이면 이 합계와 공개
정책 identity는 같아야 한다.

## 수동 실행

상태 API는 데이터를 변경하지 않는다. 화면의 수동 실행은 기존
`POST /api/v1/admin/collection-runs` 계약을 사용하며 source ID를 명시하고 확인
단계를 거친다. 수동 수집 결과는 검증·dataset 승격 전까지 공개 검색에 자동으로
포함되지 않는다.

## 상태 코드

| 상태 | 의미 |
| --- | --- |
| `200` | 상태 조회 성공; worker 장애도 안전한 상태 값으로 포함 |
| `401` | 관리자 세션 누락·만료·무효 |
| `403` | 관리자 역할 부족 |

