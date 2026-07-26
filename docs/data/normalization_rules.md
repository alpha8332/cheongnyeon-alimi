# 데이터 정규화 규칙

## 문서 상태

- 상태: 기준선
- 현재 구현 상태: Normalizer·Validator와 Normalized Schema 1.0.0 구현

정규화는 `ExtractedPolicy`의 소스별 표현을 공통
`NormalizedProgram`으로 변환한다. 원문에 없는 값을 추정해 정확한 값처럼
만들지 않는 것을 우선한다.

## 공통 원칙

- Normalizer는 API 필드명, XML 태그와 CSS Selector를 알지 않는다.
- 원문 text는 Raw 또는 Extracted 단계에 보존한다.
- 파싱할 수 없는 선택 필드는 null 또는 빈 배열로 표현한다.
- 필드 하나를 파싱하지 못해 전체 실행을 중단하지 않는다.
- 필수 필드 누락과 Schema 위반은 Validator가 invalid로 분류한다.
- 같은 입력과 규칙은 같은 결과를 생성해야 한다.
- application 상태의 기준일은 입력 `collected_at`의 Asia/Seoul 날짜다.

## 텍스트

텍스트 정규화는 다음 처리를 기본으로 한다.

- HTML 태그 제거
- HTML Entity 변환
- 앞뒤 공백 제거
- 연속 공백 정리
- 줄바꿈 정리

문장 의미, 금액과 자격 조건을 요약하거나 재작성하지 않는다. LLM 기반 추출은
별도 설계와 검증 기준이 승인되기 전까지 기본 정규화 범위에 포함하지 않는다.

## 날짜

### 지원할 입력

```text
2026-07-01
2026.07.01
2026. 7. 1.
2026/07/01
20260701
2026-07-01 ~ 2026-07-31
상시
마감
예산 소진 시
```

### 출력 원칙

- 명시된 날짜는 `YYYY-MM-DD`로 변환한다.
- 명시된 시작일과 종료일은 각각 `application_start`,
  `application_end`에 저장한다.
- 종료일이 없거나 `예산 소진 시`이면 임의의 종료일을 만들지 않는다.
- `상시`, `예산 소진 시` 같은 원문 의미는 구조화 결과와 별도로 보존한다.
- 유효하지 않은 달력 날짜는 보정하지 않고 파싱 실패로 처리한다.
- 두 날짜가 있으면 `application_schedule=fixed_period`로 두고 수집 기준일이
  시작 전이면 `scheduled`, 기간 안이면 `open`, 종료 뒤면 `closed`다.
- 시작일 하나만 있고 기준일보다 미래면 `scheduled`지만 시작 뒤 상태는
  종료일 없이 추정하지 않아 null이다.
- `상시`는 `application_schedule=always`,
  `application_status=open`으로 전달한다.
- `마감`은 명시된 상태이므로 `application_status=closed`다.
- `예산 소진 시`는 `application_schedule=until_budget_exhausted`로 두고
  실제 소진 여부를 알 수 없어 상태는 null이다.
- 알 수 없는 상태를 `"unknown"`으로 만들지 않고 null로 둔다.

## 연령

지원할 대표 입력:

```text
만 19세 이상 34세 이하
19~39세
청년기본법상 청년
연령 제한 없음
```

원칙:

- 숫자가 명확한 경우에만 `age_min`과 `age_max`를 구조화한다.
- 한쪽 경계만 명확하면 확인된 경계만 기록한다.
- 법령명이나 모호한 표현에서 숫자를 추정하지 않는다.
- 원문은 `age_condition_text`에 보존한다.
- 연령 제한 없음과 연령 정보 누락을 같은 의미로 취급하지 않는다.
- 허용 범위는 0~150이고 최소 연령이 최대 연령보다 클 수 없다.

예:

```json
{
  "age_min": 19,
  "age_max": 34,
  "age_condition_text": "만 19세 이상 34세 이하"
}
```

```json
{
  "age_min": null,
  "age_max": null,
  "age_condition_text": "청년기본법상 청년"
}
```

## 지역

행정구역 코드 체계가 별도 계약으로 확정되기 전에는 표준 이름만 정리한다.

| 원문 예 | 정규화 값 |
| --- | --- |
| 서울시 | 서울특별시 |
| 경북 | 경상북도 |
| 포항 | 포항시 |
| 전국 | 전국 |

원칙:

- 결과는 `regions` 배열에 저장한다.
- 시·도와 시·군·구가 모두 확인되면 필요한 계층을 배열에 보존한다.
- 동명이인 지역이나 불명확한 축약어는 추정하지 않는다.
- 값이 없으면 `[]`을 사용한다.
- 원문은 `region_text`에 보존한다.
- 5자리 행정구역 코드 목록은 승인된 code-to-name 기준표가 아직 없으므로
  추정하지 않고 `regions=[]`과 `unmapped_region_code` 경고를 남긴다.
- 서울·부산 등 시·도 축약과 문서에 정의된 포항 사례만 표준 이름으로
  치환하고, 이미 행정구역 접미사가 있는 이름은 그대로 보존한다.

## 카테고리

Normalized 1.0.0은 실제 복지로 관심주제의 다중값을 보존하기 위해
`categories` 배열을 사용한다. 같은 enum은 중복하지 않고 원문 순서를
유지한다.

현재 기준 매핑:

| 원문 | enum |
| --- | --- |
| 주거 | `housing` |
| 금융, 서민금융, 금융·생활지원 | `finance` |
| 복지·문화, 생활지원, 건강, 보육, 보호·돌봄, 문화·여가, 안전·위기 | `welfare` |
| 취업·일자리 | `employment` |
| 창업 | `startup` |
| 교육·직업훈련 | `education` |
| 기타 또는 매핑 불가 | `other` |

쉼표로 구분된 복지로 관심주제는 각각 매핑한다. 온통청년
`금융･복지･문화`는 `finance`, `welfare` 두 값을 만든다. 매핑되지 않은
명시적 분류는 `other`를 사용하되 `unmapped_category` 경고와
`category_text` 원문을 함께 유지한다. 분류 자체가 없으면 `other`를 만들지
않고 빈 배열을 사용한다.

## 누락과 오류

- 선택 단일 값 없음: null
- 배열 값 없음: `[]`
- 필수 값 없음: invalid
- category·지역·연령·신청기간 검색 필드 일부 누락: partial
- 파서 예외: 원문과 오류 이유를 보존하고 다음 문서 처리를 계속

파싱 실패를 빈 문자열이나 `other`로 무조건 숨기지 않는다. `other`는
카테고리 의미가 실제로 기타이거나 정의된 매핑에 속하지 않을 때만 사용하고,
원문을 함께 보존한다.

## Validator와 오류 위치

Validator는
[`normalized_program.schema.json`](../../data/schema/normalized_program.schema.json)
과 날짜·연령 범위, 품질 상태 일치 규칙을 함께 검사한다.

- `ValidationIssue.path`: `$.title`, `$.regions`, `$.provenance[0]` 같은
  JSON path
- `code`: Schema keyword 또는 정규화·품질 규칙 식별자
- `message`: 비밀값과 원문 전체를 포함하지 않는 설명
- `severity`: `warning` 또는 `error`

Schema 오류, 필수 필드 누락, 날짜·연령 역전과 잘못 선언한 품질 상태는
invalid다. 선택 필드 파싱 경고와 주요 검색 필드 누락은 partial이다.
valid·partial 결과는 Schema-valid Python 모델을 포함하고 invalid 결과는
candidate와 오류만 남겨 정상 결과와 분리한다.

Data 5의 정상·경계·실패 사례는 개인정보나 외부 원문이 없는 합성 테스트
데이터를 사용한다. Data 6의 Raw·Extracted·Normalized Fixture와 canonical
Seed도 실제 API 원문을 복사하지 않고 source 구조를 재현한 합성 데이터다.
구체적인 대표 사례와 소비자 검토 상태는
[Fixture와 Seed 계약](fixture_seed_contract.md)을 따른다.

## 규칙 변경

정규화 규칙을 변경할 때는 다음을 함께 확인한다.

- `data/schema/normalized_program.schema.json`
- 이 문서
- 파서와 Normalizer 테스트
- 정상·경계·실패 Fixture
- 기존 Seed의 재생성 필요성
- Backend 필터와 Frontend 표시 영향

현재 Backend·Frontend 소비 구현은 없지만 단일 category에서 배열로의 전환,
신청 일정·상태 분리, null·빈 배열과 provenance 필드는 안정적인 영역 간
계약으로 승인하기 전에 공동 검토해야 한다.
