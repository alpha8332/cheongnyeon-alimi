# Review admission 현재성·지역 projection 오적재 복구

## 문제 정보

- 발생·해결일: 2026-08-19
- 환경: PostgreSQL 18.4, Policy 기준선 3,270건, 지역 review 1,140건
- 영역: Data review 재판정·Normalizer·Importer·manifest 멱등성
- 관련 구현 커밋:
  `603a0bcd4c7e2b6ef6c0926f768adebfcdd5e51a`,
  `424514165b1e2c92f477d04005521d9d5e5d4bb2`,
  `f3f67aac242b29e0494dd1a3f667fcaa7d9ca9d0`
- 관련 Forest:
  [Integration 10 Review Admission](../../development/develop_plan/integration/10_review_admission_docker_acceptance.md)

## 문제 상황

지역 review 1,140건에서 사용자에게 제한적으로 공개할 수 있는 partial 정책을
선별하기 위해 admission v1을 만들었다. 최초 manifest는 5건을
`promote_partial`로 판정했고 scratch·서비스 적용 과정에서 두 결함이 확인됐다.

1. 승격 Policy의 canonical region rule이 0건이었다.
2. 실행일에는 종료된 대구 정책 2건이 과거 checkpoint의 `open`을 근거로 승격
   후보에 남았다.

Policy row 수와 동일 manifest `unchanged`만 확인한 기존 검증으로는 검색
projection 누락과 현재성 오판을 발견할 수 없었다.

## 조사와 실제 원인

### Regional Gate 결과를 물질화하지 않음

review의 원본 `ExtractedPolicy`를 바로 Normalizer에 전달했다. Regional Gate가
확인한 canonical region이 `accepted_policy`에 반영되지 않아 Policy는 생겼지만
`policy_region_rules`와 검색 projection이 만들어지지 않았다.

### 과거 checkpoint 상태를 실행일 현재성으로 사용

checkpoint의 `open`은 수집 당시의 관찰값이다. admission 실행일
`2026-08-19`에 신청 가능하다는 보장이 없지만 현재성 재평가 없이 재사용했다.
대구 `8375`는 8월 14일, `8187`은 8월 18일에 종료된 정책이었다.

### 적재 후 manifest baseline 의미 불일치

세 정책을 정상 적재한 뒤 audit를 다시 실행하면 현재 Policy 3,273건을
`database.policy_count`로 기록했다. apply는 기존 승격 identity 3건을 제외한
승격 전 기준선 3,270건을 요구해 새 manifest가 자기 자신을 재적용하지 못했다.

## 해결 과정

### 1. Gate 중단과 제한 보상 rollback

최초 서비스 적용 5건 직후 region rule 0건을 확인해 Gate를 중단했다. 해당
시도로 생성된 Policy 5건과 정확히 연결된 CollectionRun 3건만 보상 rollback해
Policy 3,270·CollectionRun 40 기준선으로 되돌렸다. 다른 기존 row와
checkpoint는 변경하지 않았다.

### 2. 실행일 기준 지역·현재성 재평가

admission은 기존 Regional Gate를 `2026-08-19` 기준으로 다시 실행하고, 그
Gate가 만든 canonical region 포함 `accepted_policy`를 Normalizer에 전달하도록
수정했다. 청년 대상 조건만 taxonomy v2로 대체하고 지역·현재성·중복·provenance
Gate는 우회하지 않았다.

종료된 대구 2건을 `exclude_closed`로 전환하고 최종 승격을 다음 3건으로 줄였다.

- `regional-daegu-youth-platform/8357`
- `regional-gangwon-youth-platform/A2026010600300200900600001`
- `regional-gyeongnam-youth-platform/2091`

### 3. projection·멱등성 검증 확대

scratch DB에서 Policy 수뿐 아니라 다음을 함께 확인했다.

- canonical region rule 3건
- search projection 3건
- 첫 적용 `inserted 3`
- 동일 manifest 재실행 `unchanged 3`
- cleanup 후 Policy 기준선 3,270 복원

### 4. post-admission baseline 안정화

audit의 `database.policy_count`를 승격 전 기준선으로 정의했다. 이미 같은
`promote_partial` identity가 존재하면 현재 Policy 수에서 그 identity 수를
제외한다. 최초 적용 전과 post-admission 재생성 후 모두 baseline 3,270을
사용하도록 회귀 테스트를 추가했다.

## 확인 결과

| 항목 | 최초 결함 manifest | 최종 manifest |
| --- | ---: | ---: |
| regional review | 1,140 | 1,140 |
| `promote_partial` | 5 | 3 |
| `hold_review` | 1,135 | 1,071 |
| `exclude_closed` | 0 | 66 |
| 승격 canonical region rule | 0 | 3 |
| hard exclusion 오승격 | 0 | 0 |

최종 서비스 적용은 `inserted 3`, 이후 동일 입력 재실행은 전건
`inserted 0·updated 0·unchanged 3`이었다. 최종 DB는 Policy 3,273건,
`valid 1,469`, `partial 1,804`, `open 821`이었다.

확정 구현 SHA `f3f67aac242b29e0494dd1a3f667fcaa7d9ca9d0`의 최종 manifest
계약 SHA-256은
`789f8e3b61c144843e93bc762d60f114179c6bfb8e5effd260138c73484e1203`다.
post-admission 서비스 재적용도 `unchanged 3`으로 통과했다.

## 예방 방법

- 과거 checkpoint 상태를 실행일의 신청 가능 상태로 사용하지 않는다.
- Regional Gate가 확인한 정책 객체와 원본 ExtractedPolicy를 구분한다.
- 적재 검증에 Policy row 수뿐 아니라 region rule·search projection을 포함한다.
- 실제 DB 적용 전에 복원 가능한 dump와 scratch dry-run을 준비한다.
- 실패 rollback은 해당 실행이 만든 identity·run만 정확히 대상으로 삼는다.
- manifest의 policy count가 pre-admission인지 post-admission인지 의미를 고정한다.
- 동일 manifest 재생성과 재적용을 별도 테스트한다.
- review 수를 줄이기 위해 근거가 부족한 후보를 자동 승격하지 않는다.

## 관련 근거

- [Review Admission 개발 기록](../../development/development_notes/integration/review_admission_docker_acceptance.md)
- [Review Admission 규칙](../../data/review_admission_rules.md)
- `collectors/review_admission.py`
- `scripts/audit_review_admission.py`
- `scripts/apply_review_admission.py`
- `tests/integration/test_review_admission_to_database.py`
- `tests/test_review_admission_audit.py`

