# 정책 생명주기 계약

## 문서 상태

- 상태: current
- 확정일: `2026-08-24`
- Gate: `W6-P1_LIFECYCLE_PASS`
- Migration: `20260824_0007`

## 목적

정책 이력을 삭제하지 않으면서 현재 검색 가능한 정책과 더 이상 노출하지 않을
정책을 결정적으로 구분한다. 종료일 경과는 즉시 공개 조회에서 제외하고,
Source 미발견에 따른 inactive 전이는 완전하고 성공한 수집에서만 허용한다.

## 저장 필드

| 필드 | 의미 | 갱신 규칙 |
| --- | --- | --- |
| `last_seen_at` | Source에서 해당 identity를 마지막으로 관측한 시각 | accepted import의 `collected_at` 최댓값 |
| `last_verified_at` | 정규화·검증을 통과해 DB에 반영한 마지막 시각 | accepted import 시각의 최댓값 |
| `inactive_at` | 완전 수집에서 identity가 미발견된 시각 | complete success에서만 기록, 재등장하면 `null` |

Migration은 기존 행의 `collected_at`을 `last_seen_at`, `updated_at`을
`last_verified_at`으로 backfill한다. `inactive_at`은 기존 데이터에 대해 추정하지
않고 `null`로 유지한다.

## 공개 조회 경계

사용자 정책 목록·상세·검색·추천과 공개 bootstrap 후보에는 다음 조건을 모두
적용한다.

```text
inactive_at IS NULL
AND (application_end IS NULL OR application_end >= 오늘[Asia/Seoul])
AND data_quality_status가 공개 허용 상태
```

- `application_end`가 오늘이면 당일까지 노출한다.
- 종료일이 오늘보다 이전이면 `application_status` 값과 무관하게 제외한다.
- 상시 모집·예산 소진·종료일 미확정은 날짜를 추정해 제외하지 않는다.
- 종료일 경과만으로 `inactive_at`을 기록하지 않는다. 행은 관리자 조회와
  감사·재수집을 위해 보존한다.
- 관리자 읽기 전용 API는 inactive·마감 행을 포함하고 세 생명주기 시각을
  반환한다.

## 수집 전이

| 실행 결과 | 기존 정책 | 미발견 정책 |
| --- | --- | --- |
| 완전 snapshot·검증·DB commit 성공 | 관측·검증 시각 갱신, 재등장 시 active 복구 | `inactive_at` 기록 |
| snapshot limit이 전체 item 수보다 작음 | 포함된 identity만 갱신 | 기존 상태 유지 |
| normalization invalid 존재 | batch write와 inactive 전이 중단 | 기존 상태 유지 |
| DB skipped·rejected·failed | inactive 전이 중단 | 기존 상태 유지 |
| 지역 checkpoint에 `FAILED` 결정 존재 | accepted 갱신 외 inactive 전이 중단 | 기존 상태 유지 |
| dry-run | DB를 변경하지 않음 | 기존 상태 유지 |

일반 Source의 완전성은 검증된 `SnapshotManifest.item_count` 전체를 limit 안에서
재생했는지로 판정한다. 지역 Source는 discovery·decision checkpoint가 complete이고
`FAILED` identity가 없을 때만 `discovered_ids`를 완전 관측 집합으로 사용한다.
review·closed·duplicate처럼 발견됐지만 신규 admission되지 않은 identity도
미발견으로 오판하지 않는다.

## 물리 삭제 금지와 재등장

완전 수집에서 사라진 정책도 `DELETE`하지 않는다. Search projection과 관계형
근거를 포함한 기존 행을 보존하고 `inactive_at`만 기록한다. 같은
`source_id + external_id`가 다시 검증되면 upsert가 `inactive_at`을 `null`로
되돌린다. 내용 변경이 없어도 재등장은 `updated` 결과로 집계해 공개 가시성
변화를 감사할 수 있게 한다.

## 2026-08-24 actual 기준선

Acceptance PostgreSQL을 `20260810_0006 → 20260824_0007`로 migration했다.

| 지표 | 결과 |
| --- | ---: |
| 전체 정책 | 3,273건 |
| `last_seen_at` 미backfill | 0건 |
| `last_verified_at` 미backfill | 0건 |
| migration 직후 inactive | 0건 |
| `application_end < 2026-08-24` | 1,093건 |
| 기본 공개 lifecycle 후보 | 2,180건 |

실제 Backend image를 rebuild한 뒤 공개 목록 `include_partial=true`가 2,180건을
반환했고, 마감 정책 ID 표본의 공개 상세가 `404`임을 확인했다. 관리자·DB에는
해당 행이 그대로 보존된다.

## 검증 기준

- SQLite·API·검색·추천·migration 전체 회귀
- PostgreSQL upgrade·backfill·downgrade와 JSONB·검색·upsert 회귀
- active 재등장, incomplete snapshot, invalid·rejected 실행의 fail-closed 회귀
- 공개 artifact builder가 같은 lifecycle predicate를 사용하는지 검증
- 실제 DB 총 row 수와 migration 전후 보존 확인

## 관련 문서

- [공개 bootstrap dataset 계약](public_policy_dataset.md)
- [수집 정책](collection_policy.md)
- [Deploy 02 계획](../development/develop_plan/deploy/02_production_data_refresh_delivery.md)
- [Deploy 02 개발 기록](../development/development_notes/deploy/production_data_refresh_delivery.md)
