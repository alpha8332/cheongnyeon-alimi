# Release 1 실데이터 품질 Profile

## 문서 정보

- 기준일: 2026-08-04
- Profile version: `1.0.0`
- 대상: Data 02 DT3 완료 snapshot
- 용도: Backend·Frontend 검색 구현과 Integration 04 인수 검증 인계

이 문서는 Git 제외 Runtime Raw의 payload를 공개하지 않고, 완료 manifest를
오프라인 재생해 얻은 집계와 안전한 정책 식별자만 기록한다. 인증키, 요청
query와 DB credential은 포함하지 않는다.

## 재현 방법

외부 API와 PostgreSQL에 연결하지 않고 다음 명령으로 같은 JSON Profile을
표준 출력에 생성한다.

```powershell
.\.venv\Scripts\python.exe -B scripts\profile_release_dataset.py
```

기본값은 다음 완료 snapshot ID를 명시적으로 고정한다.

| Source | snapshot ID | 완료 시각 UTC | 성공 요청 | 항목 |
| --- | --- | --- | ---: | ---: |
| 온통청년 | `4580234be1df46cbbe4a700fc4e02630` | `2026-08-04T13:15:46.697703+00:00` | 6 | 2,698 |
| 복지로 | `2e0b8100348544b3b023b27017025218` | `2026-08-04T13:16:02.682157+00:00` | 6 | 461 |

## 품질 기준선

### 전체와 기본 노출

| 구분 | 정책 수 |
| --- | ---: |
| accepted | 3,159 |
| valid | 1,462 |
| partial | 1,697 |
| invalid | 0 |
| 기본 노출 | 1,187 |
| 기본 노출 valid / partial | 486 / 701 |

Gate G1에 따라 기본 노출은 `open`, `scheduled`와
`application_status=null`을 포함하고 `closed`를 제외한다. 기본 노출 상태는
open 708건, scheduled 17건, null 462건이다. null은 신청 가능을 뜻하지 않고
Source에서 현재 상태를 확정할 근거가 없다는 뜻이다.

### Source별

| Source | accepted | valid | partial | invalid | 기본 노출 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 온통청년 | 2,698 | 1,462 | 1,236 | 0 | 726 |
| 복지로 | 461 | 0 | 461 | 0 | 461 |

온통청년은 2,698건 모두 regional이고 복지로 461건은 모두 coverage unknown이다.
현재 snapshot에는 nationwide로 정규화된 정책이 없다. 복지로는 목록·제한 상세
계약만으로 지역·연령·신청기간을 확정할 수 없어 전건 partial이다.

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
경계는 양쪽 bound 581건, bound 없음 2,117건이다.

## 실제 검색 분포

Backend search projection과 같은 텍스트 결합 규칙으로 집계했다.

| 검색어 | 전체 | 기본 노출 |
| --- | ---: | ---: |
| 월세 | 165 | 51 |
| 주거 | 429 | 168 |
| 주거비 | 114 | 35 |
| 전세 | 70 | 26 |
| 임대 | 176 | 54 |
| 청년 | 2,205 | 720 |

따라서 “월세 지원 정책 찾아줘” 같은 일반 탐색에는 실제 후보가 있다. 다만
텍스트 포함은 자격 충족이나 신청 가능 상태를 보장하지 않는다.

### Release 1 조건 경계

기본 노출 1,187건을 Gate G1의 3값 판정으로 평가했다.

| 조건 | match | mismatch | unknown |
| --- | ---: | ---: | ---: |
| 27세 | 544 | 26 | 617 |
| 천안시 `4413000000` | 54 | 671 | 462 |
| 충청남도 `4400000000` | 0 | 725 | 462 |

충청남도 broad query의 match 0은 현재 evaluator가 query의 canonical ancestor
path에 있는 정책 규칙만 match로 보는 계약 결과다. 천안시·다른 시군에만
명시된 정책을 충청남도 전체 적용으로 확대하지 않는다. 복지로 461건은 지역
근거가 없어 unknown이며, 온통청년 1건은 unresolved rule 때문에 unknown이다.

## Golden query 판정

대상 문장은 `27세 천안 청년 월세 지원`이다. 기본 노출 중 `청년`, `월세`,
`지원`을 모두 포함한 정책은 36건이지만, 27세와 천안시가 모두 confirmed
match인 정책은 0건이다. confirmed mismatch를 제외하면 다음 두 실제 후보만
남는다.

| Source / external ID | 제목 | 상태 | 연령 | 지역 | 품질 |
| --- | --- | --- | --- | --- | --- |
| 복지로 / `WLF00001063` | 주거안정 월세대출 | null | unknown | unknown | partial |
| 복지로 / `WLF00004661` | 청년월세 지원사업 | null | unknown | unknown | partial |

- [주거안정 월세대출 원문](https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00001063&wlfareInfoReldBztpCd=01)
- [청년월세 지원사업 원문](https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00004661&wlfareInfoReldBztpCd=01)

두 정책 모두 실제 정책 후보지만 현재 snapshot만으로 27세 천안 거주자의
자격과 신청 가능 상태를 확정할 수 없다. Backend는 unknown 후보로만 포함하고
Frontend는 미확인 연령·지역·상태를 표시해야 한다. “받을 수 있다”는 자격
확정 문구를 사용하면 안 된다.

Integration 04에서는 다음 중 하나를 명시적으로 선택해야 한다.

1. 일반 탐색 문장인 “월세 지원 정책 찾아줘”로 실제 검색 흐름을 검증하고,
   별도로 27세·천안 조건의 unknown 표시를 검증한다.
2. 27세·천안의 confirmed golden policy가 반드시 필요하면 Source 범위를
   보강한 뒤 Data snapshot과 근거를 다시 승인한다.

정책이 없는 상태에서 합성 기대 결과를 만들지는 않는다.

## Identity와 provenance

- `(source_id, external_id)` 고유 identity는 3,159개로 accepted 수와 같다.
- 제목 중복은 270개 group, 609개 row이며 같은 제목은 최대 6건이다.
- 따라서 제목을 identity나 upsert key로 사용하면 안 된다.
- 온통청년 전건은 provenance 문서 2개를 보존한다.
- 복지로 456건은 2개, 제한 상세가 결합된 5건은 3개를 보존한다.

## Backend 인계

- 기본 노출 예상 cardinality는 1,187건이고 partial이 701건이다.
- `application_status=null` 462건을 open으로 바꾸지 않는다.
- 0~0 placeholder 631건은 연령 unknown이며 DB 재적재 후 0~0 structured
  bound가 남아 있으면 안 된다.
- 천안·27세·청년·월세·지원의 confirmed 결과는 0건이다. 두 복지로 후보는
  age·region·status unknown을 response reason에 보존한다.
- 제목 중복이 있으므로 identity는 `(source_id, external_id)`를 사용한다.
- 충청남도 broad query가 하위 시군 정책을 포함하지 않는 현재 계약을 유지한다.
  포함 semantics가 필요하면 Integration에서 별도 계약 변경으로 검토한다.

## Frontend 인계

- partial과 `application_status=null`은 “신청 가능”이 아니라 미확인으로
  표시한다.
- age·region confirmed mismatch는 결과에서 제외되고, unknown 후보는 경고와
  함께 보일 수 있다.
- 두 golden 후보를 사용자에게 자격 확정 결과로 표시하지 않는다.
- 결과 카드와 상세에서 실제 Source 링크를 확인할 수 있게 유지한다.
- 0건 결과와 unknown 후보만 있는 결과를 서로 다른 사용자 상태로 표현한다.

## 계약 영향

NormalizedProgram 1.1.0의 Schema, 필드 nullability, 빈 배열, enum, Fixture와
Seed는 변경하지 않았다. Backend는 기존 nullable integer column을, Frontend는
기존 nullable age·status와 unknown reason 계약을 그대로 사용한다. 따라서
이번 DT4 보정에 따른 Schema migration이나 Frontend type 변경은 없다.
