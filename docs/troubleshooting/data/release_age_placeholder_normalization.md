# 연령 `0세~0세` placeholder 오판 보정

## 문제 정보

- 발생·해결일: 2026-08-04
- 환경: 온통청년 완료 snapshot 2,698건, PostgreSQL 18
- 영역: Data 정규화·검색 3값 판정·Runtime 재적재
- 관련 Forest:
  [Release Dataset Bootstrap](../../development/develop_plan/data/02_release_dataset_bootstrap.md)

## 문제 상황

실제 완료 snapshot의 품질 Profile을 만들던 중 온통청년 631건이
`age_min=0`, `age_max=0`으로 구조화된 사실을 확인했다. Source는 연령 제한
사용 여부와 함께 최소·최대값 0을 제공했지만, 이 값은 실제 0세 전용 자격을
뜻하는 근거가 아니었다.

기존 구조화 결과에서는 27세 검색이 이 631건을 확정 mismatch로 제외했다.
원문 근거가 없는 숫자 bound가 사용자 검색 결과를 줄이는 데이터 정확성
문제였다.

## 조사와 실제 원인

다음 세 값을 함께 대조했다.

- Source의 연령 제한 사용 여부
- Source의 최소·최대 연령 숫자
- 사용자가 확인할 수 있는 원문 연령 문구

631건은 숫자 필드가 모두 0이었지만 실제 원문이 정확한 0세 제한을 증명하지
않았다. Normalizer가 Source의 placeholder와 실제 자격 bound를 구분하지 않고
동일한 숫자로 취급한 것이 원인이었다.

## 해결 과정

1. 원문 `0세 ~ 0세`는 provenance와 원문 필드에 그대로 보존했다.
2. 확정할 수 없는 `age_min`·`age_max`는 `null`로 변경했다.
3. 해당 정책의 품질을 `partial`로 분리했다.
4. Source 관찰 문제는 `placeholder_age_range`, 검색 가능한 bound 부재는
   `unstructured_age_condition`으로 구분했다.
5. 완료 snapshot을 같은 Normalizer로 다시 replay해 변경 범위를 계산했다.
6. 임시 pgpass를 사용해 실제 DB에 재적재하고 동일 snapshot을 다시 실행했다.

확정 숫자를 삭제했지만 정책 원문 자체를 삭제하거나 연령 무관 정책으로
단정하지 않았다. 검색에서는 연령 `match`가 아니라 `unknown`으로 남아 공식
원문 확인 대상으로 처리된다.

## 확인 결과

| 검증 | 결과 |
| --- | ---: |
| 보정 대상 | 631건 |
| 첫 재적재 | inserted 0·updated 631·unchanged 2,067 |
| 동일 snapshot 재실행 | inserted 0·updated 0·unchanged 2,698 |
| `age_min=0 AND age_max=0` | 0건 |
| skipped·rejected·failed | 0건 |

최종 SQL 집계는 온통청년 2,698 row·identity, `valid 1,462`, `partial 1,236`으로
offline Profile과 일치했다. 복지로 461건에는 이 보정을 소급 적용하지 않았다.

보정 후 기본 노출 1,187건의 27세 판정은 `match 544`, `mismatch 26`,
`unknown 617`이었다. 이는 631건을 모두 match로 바꿨다는 뜻이 아니라, 근거 없는
확정 mismatch를 제거하고 미확정으로 되돌린 결과다.

## 예방 방법

- 숫자 `0`을 Source별 의미 확인 없이 실제 자격 bound로 사용하지 않는다.
- 구조화 숫자와 원문 문구가 충돌하면 원문을 보존하고 숫자 확정을 해제한다.
- 보정 전후 `match`·`mismatch`·`unknown` 분포를 함께 비교한다.
- 재적재는 변경 건수와 동일 snapshot `unchanged`를 모두 확인한다.
- placeholder 판정은 Source 관찰 issue와 검색 issue를 별도 code로 남긴다.
- credential과 Raw payload는 명령 출력·문서·Git에 기록하지 않는다.

## 관련 근거

- [Release Dataset Bootstrap 개발 기록](../../development/development_notes/data/release_dataset_bootstrap.md)
- [Release 1 실데이터 품질 Profile](../../data/release_dataset_profile.md)
- `collectors/normalizer.py`
- `scripts/profile_release_dataset.py`
- `tests/test_normalization.py`
- `tests/test_release_dataset_profile.py`

