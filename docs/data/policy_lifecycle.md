# 정책 생명주기 계약

## 현재 기준

- 상태: current
- 도입 Migration: `20260824_0007`
- 시간 기준: `Asia/Seoul`

정책 이력을 물리 삭제하지 않으면서 현재 공개할 정책과 더 이상 노출하지 않을
정책을 결정적으로 구분한다.

## 저장 필드

| 필드 | 의미 | 갱신 규칙 |
| --- | --- | --- |
| `last_seen_at` | Source에서 identity를 마지막으로 관측 | accepted 수집 시각의 최댓값 |
| `last_verified_at` | 정규화·검증을 마지막으로 통과 | accepted import 시각의 최댓값 |
| `inactive_at` | 완전 수집에서 identity가 사라진 시각 | complete success에서만 기록, 재등장하면 `null` |

Migration은 기존 `collected_at`·`updated_at`을 관측·검증 시각으로 backfill하고
기존 row의 inactive 상태는 추정하지 않는다.

## 사용자 공개 경계

```text
inactive_at IS NULL
AND (application_end IS NULL OR application_end >= 오늘[Asia/Seoul])
AND data_quality_status가 공개 허용 상태
AND active public dataset membership
```

- 종료일이 오늘이면 당일까지 공개한다.
- 종료일이 지났으면 `application_status`와 무관하게 사용자 API에서 제외한다.
- 상시·예산 소진·종료일 미확정은 임의 날짜로 제외하지 않는다.
- 날짜 경과만으로 `inactive_at`을 기록하지 않는다.
- 관리자 정책 조회는 감사 목적으로 inactive·마감 row를 포함한다.

## 수집 전이

| 실행 결과 | 관측 identity | 미발견 identity |
| --- | --- | --- |
| 완전 snapshot·검증·commit 성공 | 시각 갱신, 재등장 active 복구 | `inactive_at` 기록 |
| 일부 limit·불완전 checkpoint | 포함 identity만 갱신 | 기존 상태 유지 |
| invalid·rejected·persist 실패 | batch rollback | 기존 상태 유지 |
| dry-run | rollback | 기존 상태 유지 |

일반 Source는 manifest item count 전체를 limit 안에서 처리했을 때만 완전
snapshot으로 본다. 지역 Source는 discovery·decision checkpoint가 complete이고
실패 identity가 없을 때만 완전 관측 집합을 사용한다. review·closed·duplicate도
발견된 identity이므로 미발견으로 오판하지 않는다.

## 물리 삭제와 재등장

완전 수집에서 사라진 정책도 `DELETE`하지 않는다. FK와 과거 실행 근거를 보존하고
`inactive_at`만 기록한다. 같은 `(source_id, external_id)`가 다시 검증되면
upsert가 inactive를 해제한다. 내용이 같아도 공개 가시성이 바뀌므로 재등장은
`updated`로 집계한다.

## 공개 dataset 교체

새 dataset membership에 없는 기존 정책도 삭제하지 않는다. 사용자 projection만
새 active membership으로 원자적으로 바꾸며 설치 실패 시 이전 version을 유지한다.
수동 수집은 lifecycle 시각을 갱신할 수 있지만 공개 membership을 자동 변경하지
않는다.

## 검증 항목

- Migration upgrade·backfill·downgrade와 row 보존
- active 재등장과 완전 snapshot 미발견
- 일부 limit·invalid·failed의 fail-closed
- KST 종료일 경계와 상세 `404`
- 공개 artifact builder와 사용자 Repository의 같은 lifecycle predicate

관련 계약:

- [데이터 수집 정책](collection_policy.md)
- [공개 정책 dataset](public_policy_dataset.md)
- [환경 간 동등성](public_dataset_parity.md)
