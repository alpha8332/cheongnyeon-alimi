# 추천 전체 정책 판정의 N+1과 오추천 해결

## 문제 정보

- 발생일: 2026-08-19
- 환경: Windows, PostgreSQL 18.4, 실제 Policy 3,273건
- 영역: Backend 추천 API·정책 검색 판정·PostgreSQL 조회
- 관련 구현 커밋:
  `874c0f808c4a3cd9ef73135b7dbd3a11cedb27aa`

## 문제 상황

actual Browser에서 대구광역시·25세 조건으로 추천을 조회했을 때 제주·인천 등
확정적으로 다른 지역의 정책과 마감 정책이 결과에 포함됐다. 신규 적재한 지역
정책은 전체 정책의 뒤쪽에 있어 일부 조건에서는 추천 평가 대상에도 들어오지
않았다.

정확성 문제를 먼저 수정해 승인된 전체 정책을 평가하자 같은 실제 DB에서 추천
응답이 약 `14,845 ms` 걸렸다. 응답 결과는 정확해졌지만 사용자가 기다리기에는
긴 시간이었다.

이 문제는 다음 두 단계로 구분해야 한다.

1. 기존 첫 200건 평가는 빠를 수 있지만 결과가 불완전하고 지역·마감 mismatch를
   제외하지 못했다.
2. 전체 3,273건을 정확하게 평가하도록 바꾸자 정책별 지역 근거 조회가 반복돼
   N+1 성능 문제가 드러났다.

## 재현 조건

실제 서비스 DB와 actual API mode에서 다음 조건을 사용했다.

```json
{
  "region": "대구광역시",
  "age": 25,
  "include_partial": true,
  "limit": 50
}
```

호출 대상은 `POST /api/v1/policies/recommendations`다. 당시 DB 기준은 Policy
3,273건, `valid` 1,469건, `partial` 1,804건이었다.

관찰 순서는 다음과 같다.

1. Browser 결과에 다른 시도와 `closed` 정책이 포함되는지 확인한다.
2. 전체 승인 정책 평가 단계에서 API 응답 완료 시간을 측정한다.
3. 응답의 지역 판정, 신청 상태, 신규 stable identity 포함 여부를 대조한다.

측정값은 같은 PC·DB·조건에서 수정 전후를 비교한 RA4 실제 관찰값이다. 반복
부하 시험의 평균이나 운영 SLA 값으로 사용하지 않는다.

## 실제 원인

### 추천이 필터가 아니라 가산점 방식으로 동작했다

기존 추천 서비스는 지역·연령·분야가 맞으면 점수를 더했지만 확정 mismatch를
후보에서 제거하지 않았다. 지역이 다르거나 마감된 정책도 다른 점수를 얻으면
추천 결과에 남을 수 있었다.

연령 하한·상한이 없을 때 `0~120세`로 간주한 것도 근거 없는 match였다. 명시한
지역을 해석하지 못한 `unknown`과 상태 미지정 시 `closed` 역시 fail-closed로
제외되지 않았다.

### 첫 200건 제한이 전체 데이터 정확성을 깨뜨렸다

추천 서비스는 Repository에서 최대 200건만 가져온 뒤 점수를 계산했다. 최종
응답 `limit`과 평가 대상 `limit`가 섞여 있었기 때문에 ID가 뒤에 있는 신규·지역
정책은 조건에 맞아도 영구적으로 추천 후보가 될 수 없었다.

### 전체 평가 전환 뒤 정책별 지역 조회가 반복됐다

정확성을 위해 전체 승인 snapshot을 평가하면서 기존 단건 지역 판정을 그대로
반복하면 정책마다 다음 조회가 발생한다.

- 해당 Policy의 `policy_region_rules` 조회
- rule이 참조하는 행정구역 catalog 조회
- query 지역의 상위 경로 확인

즉, 정책 수가 늘어날수록 DB round trip도 함께 늘어나는 N+1 구조였다. 전체
3,273건 평가에서 약 14.8초가 관찰된 직접 원인이다.

## 해결 과정

### 1. 검색과 추천의 3값 판정을 통합

추천 전용 문자열 포함 비교를 제거하고 검색에서 이미 사용하는
`PolicySearchEvaluationService`의 `match`, `mismatch`, `unknown` 판정을
재사용했다.

- 지역·연령·분야·상태의 확정 mismatch는 즉시 후보 제외
- 사용자가 명시한 지역의 `unknown`도 fail-closed 제외
- status 미지정 기본 추천에서 `closed` 제외
- API의 `upcoming`을 DB의 `scheduled`로 매핑
- 명시한 status가 `unknown`이면 제외하고 잘못된 status는 HTTP 422
- 연령 근거 누락은 match가 아니라 확인 필요로 유지

### 2. 평가 대상과 응답 limit 분리

먼저 승인 품질 범위의 전체 건수를 확인한 뒤 `valid`, 또는
`include_partial=true`이면 `valid+partial` 전체 snapshot을 평가한다. 요청의
`limit`은 결정적 정렬이 끝난 최종 응답에만 적용한다.

이 변경으로 뒤쪽 ID의 신규 지역 정책도 추천 대상에 포함됐다.

### 3. 지역 근거를 bulk 조회

`PolicySearchRepository.policy_region_rules_for_policies()`를 추가해 대상 Policy
ID 전체의 지역 rule을 한 번에 읽고 Policy ID별로 묶었다.

`PolicySearchEvaluationService.evaluate_policy_regions()`는 다음 두 bulk 입력을
준비한 뒤 각 정책을 메모리에서 결정적으로 판정한다.

1. 모든 대상 Policy의 region rule 집합
2. 필요한 scheme의 행정구역 catalog 집합

정책마다 같은 rule·catalog SQL을 다시 실행하지 않으므로 전체 정책 수와 DB
round trip 수가 함께 증가하지 않는다.

### 4. 회귀 계약 추가

추천 API 테스트에 다음 경계를 추가했다.

- 지역·연령의 확정 mismatch 제외
- 기본 추천의 `closed` 제외
- `upcoming` → `scheduled`
- 허용하지 않은 status의 HTTP 422
- 같은 입력의 결정적 정렬
- partial 포함 여부

## 확인 결과

같은 실제 DB와 대구광역시·25세·partial 포함 조건의 단일 관찰값은 다음과 같다.

| 항목 | bulk 적용 전 | bulk 적용 후 |
| --- | ---: | ---: |
| 추천 응답 시간 | 약 14,845 ms | 약 1,386 ms |
| 단축 시간 | - | 약 13,459 ms |
| 감소율 | - | 약 90.7% |
| 속도 배율 | 1배 | 약 10.7배 |

정확성 결과도 함께 확인했다.

- 대구 조건 결과 34건 전부 지역 `match`
- `closed` 정책 0건
- 신규 대구 stable identity `regional-daegu-youth-platform/8357` 포함
- 경상남도·25세·valid-only 결과 7건
- 경상남도 결과의 타 시도 혼입 0건, `closed` 0건
- 신규 경남 stable identity `regional-gyeongnam-youth-platform/2091` 포함
- 미확정 자격은 비단정 문구와 확인 필요 상태 유지
- 최종 RA4 전체 회귀 508 passed, 27 skipped, 241 subtests passed

## 예방 방법

- 추천과 검색이 같은 조건을 해석하면 별도 문자열 비교를 만들지 않고 공통 3값
  판정기를 사용한다.
- 점수 계산 전에 확정 mismatch의 제외 경계를 먼저 적용한다.
- 평가 대상 전체 범위와 최종 응답 pagination·limit을 분리한다.
- 전체 snapshot loop 안에서 Repository 단건 조회를 호출하지 않는다.
- 다수 Policy 판정은 rule·catalog를 bulk로 읽고 메모리에서 계산한다.
- 성능 개선을 기록할 때 데이터 건수, 입력 조건, correctness 결과를 응답 시간과
  함께 남긴다.
- 단일 수동 측정값을 SLA나 반복 부하 시험 결과로 확대 해석하지 않는다.
- 이후 데이터 규모가 커지면 추천 endpoint에 동일 fixture 기반 query-count 또는
  별도 성능 회귀 예산을 추가한다.

## 관련 파일

- `backend/app/services/recommendation.py`
- `backend/app/services/policy_search_evaluation.py`
- `backend/app/repositories/policy_search.py`
- `backend/app/schemas/recommendation.py`
- `backend/app/api/v1/endpoints/recommendation.py`
- `backend/tests/test_recommendation_api.py`
- [추천 API 계약](../../api/recommendation.md)
