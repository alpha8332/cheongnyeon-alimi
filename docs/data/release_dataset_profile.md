# Release 1 실데이터 품질 Profile

## 문서 정보

- 기준일: 2026-08-06
- Profile version: `1.2.0`
- 대상: Integration 04 DT7 Release 1 인수 snapshot
- 용도: Backend·Frontend 검색 구현과 Integration 04 인수 검증 인계

이 문서는 Git 제외 Runtime Raw의 payload를 공개하지 않고, 완료 manifest를
오프라인 재생해 얻은 집계와 안전한 정책 식별자만 기록한다. 인증키, 요청
query와 DB credential은 포함하지 않는다.

## 재현 방법

외부 API와 PostgreSQL에 연결하지 않고 다음 명령으로 같은 JSON Profile을
표준 출력에 생성한다.

```powershell
.\.venv\Scripts\python.exe -B scripts\profile_release_dataset.py `
  --require-period-safety
```

기본값은 다음 완료 snapshot ID를 명시적으로 고정한다.

| Source | snapshot ID | 완료 시각 UTC | 성공 요청 | 항목 |
| --- | --- | --- | ---: | ---: |
| 온통청년 | `6add34f7aad9456ab0abb19175b7621c` | `2026-08-06T00:18:54.586978+00:00` | 6 | 2,695 |
| 복지로 | `ffa74ef47e6048109f11bf40d1ac5e15` | `2026-08-06T00:19:03.630716+00:00` | 6 | 461 |

## 품질 기준선

### 전체와 기본 노출

| 구분 | 정책 수 |
| --- | ---: |
| accepted | 3,156 |
| valid | 1,459 |
| partial | 1,697 |
| invalid | 0 |
| 기본 노출 | 1,184 |
| 기본 노출 valid / partial | 484 / 700 |

Gate G1에 따라 기본 노출은 `open`, `scheduled`와
`application_status=null`을 포함하고 `closed`를 제외한다. 기본 노출 상태는
open 705건, scheduled 17건, null 462건이다. null은 신청 가능을 뜻하지 않고
Source에서 현재 상태를 확정할 근거가 없다는 뜻이다.

### Source별

| Source | accepted | valid | partial | invalid | 기본 노출 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 온통청년 | 2,695 | 1,459 | 1,236 | 0 | 723 |
| 복지로 | 461 | 0 | 461 | 0 | 461 |

온통청년은 2,695건 모두 regional이고 복지로 461건은 모두 coverage unknown이다.
현재 snapshot에는 nationwide로 정규화된 정책이 없다. 복지로는 목록·제한 상세
계약만으로 지역·연령·신청기간을 확정할 수 없어 전건 partial이다.

## DT7C 신청기간·상태 안전성 감사

Release 1 profile 1.2.0은 신청기간을 일반 본문에서 추정하지 않고 Source별
명시적 mapping만 허용하는 감사를 포함한다. `--require-period-safety`는 Source
근거 없는 승격, 기간·상태 불일치 또는 golden 정책 근거 누락이 있으면 0이 아닌
종료 코드를 반환한다.

| 감사 항목 | 전체 3,156건 | 기본 노출 1,184건 |
| --- | ---: | ---: |
| Source 신청기간 원문 있음 | 2,695 | 723 |
| 일정 또는 상태 구조화 | 2,694 | 722 |
| 기간·상태 모두 unknown | 461 | 461 |
| Source 원문은 있으나 구조화하지 않음 | 1 | 1 |
| 일반 본문 날짜 표기 관찰·미승격 | 2 | 2 |
| Source 근거 없는 승격 | 0 | 0 |
| 기간·상태 불일치 | 0 | 0 |

온통청년의 신청기간 근거는 `aplyYmd`와 검증된 `aplyPrdSeCd` 코드 mapping이다.
복지로 목록·상세 응답에는 신청기간 전용 필드가 없으므로 461건을 모두
`application_period_text`, 시작·종료일, 일정과 상태 `null`로 유지한다.

복지로 `청년내일저축계좌`와 `청년월세 지원사업`의 summary·support content에는
날짜처럼 보이는 표현이 있다. 이는 관찰·원문 보존 대상일 뿐 신청기간 필드라는
계약 근거가 아니므로 구조화하지 않았다. 특히 월세 정책의 원문은 축약 연도와
월·일 범위를 포함하지만 이를 현재 신청 가능 상태로 승격하지 않는다.

golden 정책 `20260430005400212969`는 온통청년 Source 신청기간 원문 `상시`에서
`application_schedule=always`, `application_status=open`으로 구조화됐고 상태
불일치와 본문 승격은 없다. 후보 노출은 허용하지만 사용자 자격 확정 표현은
계속 금지한다. DT7C 안전성 감사 결과는 `passed=true`다.

## DT4 연령 보정

온통청년 631건은 Source가 `sprtTrgtAgeLmtYn=Y`, 최소 0, 최대 0을 함께
제공했다. 이를 실제 0세 한정으로 보면 일반 청년 검색에서 confirmed mismatch가
되어 불확실한 Source 값을 확정값으로 바꾸게 된다. 따라서 다음 경계를 적용했다.

- `age_condition_text`의 `0세 ~ 0세` 원문은 보존한다.
- `age_min`과 `age_max`는 모두 null로 둔다.
- `placeholder_age_range`와 `unstructured_age_condition` 경고를 남긴다.
- 품질은 partial, 연령 판정은 unknown으로 처리한다.

이 변경은 기존 null 표현을 올바르게 적용한 Data 품질 수정이다. Schema version,
Fixture, Seed, enum과 API 필드는 변경하지 않았다. 수정 후 온통청년의 연령
경계는 양쪽 bound 578건, bound 없음 2,117건이다.

## 실제 검색 분포

Backend search projection과 같은 텍스트 결합 규칙으로 집계했다.

| 검색어 | 전체 | 기본 노출 |
| --- | ---: | ---: |
| 월세 | 165 | 51 |
| 주거 | 429 | 168 |
| 주거비 | 114 | 35 |
| 전세 | 70 | 26 |
| 임대 | 176 | 54 |
| 청년 | 2,202 | 717 |

따라서 “월세 지원 정책 찾아줘” 같은 일반 탐색에는 실제 후보가 있다. 다만
텍스트 포함은 자격 충족이나 신청 가능 상태를 보장하지 않는다.

### Release 1 조건 경계

기본 노출 1,184건을 Gate G1의 3값 판정으로 평가했다.

| 조건 | match | mismatch | unknown |
| --- | ---: | ---: | ---: |
| 27세 | 541 | 26 | 617 |
| 천안시 `4413000000` | 54 | 668 | 462 |
| 충청남도 `4400000000` | 0 | 0 | 1,184 |

충청남도 broad query의 match 0은 현재 evaluator가 query의 canonical ancestor
path에 있는 정책 규칙만 match로 보는 계약 결과다. 천안시·다른 시군에만
명시된 정책을 충청남도 전체 적용으로 확대하지 않는다. 현재 broad query는
온통청년 지역 규칙도 `query_ambiguous`로 평가하므로 전체가 unknown이다.

## Golden query 판정

현재 대상 문장은 다음과 같다.

```text
천안 사는 27살 청년 단기숙소 지원 받을 수 있나?
```

기존 `27세 천안 청년 월세 지원`은 현재 신청 가능한 정책을 검증하기에
부적합해 DT6 실행 이력으로만 보존하고 인수 기준에서는 폐기했다. 새 기준은
[Release 1 acceptance 계약](../../data/release_1_acceptance.json)에 snapshot과
기대 identity를 고정한다.

| Source / external ID | 제목 | 상태·일정 | 연령 | 지역 | 품질·분류 |
| --- | --- | --- | --- | --- | --- |
| 온통청년 / `20260430005400212969` | 청년단기숙소 지원사업 | open·always | match | match | valid·housing |

기본 노출 중 `청년`, `단기숙소`, `지원`을 모두 포함하는 정책과 모든 필수
조건이 confirmed인 정책은 각각 1건이다. DT7A 기준 자연어 문장은 일반
term의 OR 후보 확대로 495건 중 49위·약 9.3초였지만, DT7B의 구체 term
anchor 적용 뒤 자연어와 명시 조건 control 모두 1건 중 1위가 됐다. cold
실행은 각각 317.04ms·109.92ms, warm 5회 최대는 91.89ms·109.16ms로
Release 1 응답시간 예산을 통과했다.

후보 노출은 허용하지만 연령·지역·상태 match만으로 실제 자격을 확정하지
않는다. 신청 전 원문과 세부 요건을 확인하도록 안내해야 한다.

### 폐기한 DT6 월세 기준

DT6의 월세 query에서는 `주거안정 월세대출`과 `청년월세 지원사업`만
confirmed mismatch를 피했지만 둘 다 연령·지역·상태가 unknown인 partial이었다.
특히 `청년월세 지원사업`의 텍스트상 신청기간은 현재 기준으로 종료됐다.
이 결과는 회귀·unknown 표시 참고 자료이며 현재 golden 성공 기준이 아니다.

## Identity와 provenance

- `(source_id, external_id)` 고유 identity는 3,156개로 accepted 수와 같다.
- 제목 중복은 270개 group, 609개 row이며 같은 제목은 최대 6건이다.
- 따라서 제목을 identity나 upsert key로 사용하면 안 된다.
- 온통청년 전건은 provenance 문서 2개를 보존한다.
- 복지로 456건은 2개, 제한 상세가 결합된 5건은 3개를 보존한다.

## Backend 인계

- 기본 노출 예상 cardinality는 1,184건이고 partial이 700건이다.
- `application_status=null` 462건을 open으로 바꾸지 않는다.
- 0~0 placeholder 631건은 연령 unknown이며 DB 재적재 후 0~0 structured
  bound가 남아 있으면 안 된다.
- 새 golden의 기대 정책은 confirmed 1건이며 DT7B 자연어 query와 명시 조건
  control에서 모두 1위를 확인했다. 이후 변경도 같은 acceptance 계약으로
  순위·응답시간을 회귀 검증한다.
- 폐기한 월세 query의 두 복지로 후보는 age·region·status unknown을 response
  reason에 계속 보존한다.
- 제목 중복이 있으므로 identity는 `(source_id, external_id)`를 사용한다.
- 충청남도 broad query가 하위 시군 정책을 포함하지 않는 현재 계약을 유지한다.
  포함 semantics가 필요하면 Integration에서 별도 계약 변경으로 검토한다.

## Frontend 인계

- partial과 `application_status=null`은 “신청 가능”이 아니라 미확인으로
  표시한다.
- age·region confirmed mismatch는 결과에서 제외되고, unknown 후보는 경고와
  함께 보일 수 있다.
- 새 golden 후보도 사용자에게 자격 확정 결과로 표시하지 않는다.
- 결과 카드와 상세에서 실제 Source 링크를 확인할 수 있게 유지한다.
- 0건 결과와 unknown 후보만 있는 결과를 서로 다른 사용자 상태로 표현한다.

## 계약 영향

NormalizedProgram 1.1.0의 Schema, 필드 nullability, 빈 배열, enum, Fixture와
Seed는 변경하지 않았다. Backend는 기존 nullable integer column을, Frontend는
기존 nullable age·status와 unknown reason 계약을 그대로 사용한다. 따라서
이번 DT4 보정에 따른 Schema migration이나 Frontend type 변경은 없다.
