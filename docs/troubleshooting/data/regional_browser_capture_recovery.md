# 지역 Browser 수집 실패·drift 안전 복구

## 문제 정보

- 발생·해결 기간: 2026-08-13~2026-08-14
- 환경: 지역 Source 13개, Browser capture, Runtime Raw·checkpoint
- 영역: Data 수집·재현·현재성·실패 복구

## 문제 상황

지역 Source 확장 중 다음 문제가 동시에 확인됐다.

- 강원 상세 325건이 실패 상태로 남음
- 제주 상세 2건은 HTTP 성공 후에도 공통 field row가 없음
- 충북·울산 순회 중 navigation timeout 반복
- 화면 total과 실제 unique identity 수가 다름
- 현재 공식 목록과 완료 checkpoint 사이에 신규·교체 identity drift가 존재
- 과거 `null_unverifiable` field가 전체 11,430 slot 중 2,760개 남음

단순 전체 재수집은 호출량을 크게 늘리고, 현재 목록의 신규 identity를 과거
checkpoint에 조용히 섞거나 종료 이력을 바꿀 위험이 있었다.

## 조사와 실제 원인

### 강원 page-context 불일치

강원 checkpoint는 1 page 12건만 captured했고 2~29 page의 325건이 failed였다.
대표 page의 공식 identity를 직접 열자 상세 27행은 정상적으로 존재했다. 기존
수집기가 목록 page를 유지하지 않은 채 `goto(listUrl)` 후 현재 page와 다른
identity를 클릭한 계약 오류가 원인이었다.

이 원인 분류는 322건의 현재 상세가 모두 정상임을 뜻하지 않는다. 대표 canary로
공통 실패 유형만 재현했고, 잔여 identity는 별도 failed evidence로 보존했다.

### 준비 완료 판정과 실제 DOM의 불일치

충북에서는 locator wait가 timeout을 반환했지만 URL·본문·준비 selector가 이미
정상인 경우가 있었다. 반대로 URL이나 DOM이 다르면 timeout을 성공으로 바꾸면
안 됐다.

### 화면 total과 identity의 의미 차이

울산 화면은 total 596을 표시했지만 60 page에 반복되는 고정 공지 1건을 포함한
unique identity는 597개였다. checkpoint 597건과 현재 목록 digest는 같았다.
화면 total만 믿고 596건으로 줄였다면 정상 identity 1건을 누락할 수 있었다.

대전·서울·광주·인천에서는 현재 목록의 추가·교체 identity가 확인됐다. 이는
수집 실패가 아니라 checkpoint와 현재 목록의 시간 차이이므로 자동 편입하지
않았다.

## 해결 과정

### 1. failed identity만 제한 복구

`/recover`는 완료 checkpoint에 이미 존재하는 failed identity만 입력으로 받게
했다. Raw 저장 후 같은 checkpoint 범위를 replay하고 결과가 `review` 또는
`closed`일 때만 `failed → captured/outcome`을 원자적으로 교체했다.

강원 325건 전체를 재요청하지 않고 page 2·15·29 대표 3건과 제주 2건만 actual
복구했다. accepted 후보는 집계 Source 중복 기준선 확인 전 자동 승격하지 않았다.

### 2. canary와 실패 유형 분리

identity 존재, 클릭·POST, 동적 selector, 제목 일치, field row, 삭제·비공개를
순서대로 확인하고 다음 유형 중 하나로만 기록했다.

- `healthy`
- `page_or_identity_changed`
- `detail_click_or_post_contract`
- `dynamic_render_wait`
- `response_success_without_field_dom`
- `deleted_or_private`

canary 단계에서는 checkpoint·Raw·DB를 쓰지 않았다.

### 3. 제한 timeout fallback

요청한 origin·path·query와 준비 DOM이 이미 일치하는 경우에만 페이지 내부 DOM을
최대 20초 polling하도록 보강했다. URL·DOM이 맞지 않으면 기존 timeout을 그대로
발생시켰다. 같은 오류가 반복되면 지정 page에서 중단하고 이후 Source를 시작하지
않았다.

### 4. total·identity digest fail-closed

화면 total, page slot, dedupe identity, checkpoint identity를 분리해 비교했다.
total이나 identity가 다르면 Raw·checkpoint·DB write 전에 중단했다. 신규
current-only identity는 별도 승인된 예외 목록이 있을 때만 제외하고, 선택 상세는
계속 checkpoint identity 부분집합으로 제한했다.

### 5. field 관찰 상태 완전 분류

각 field를 `value_extracted`, `label_present_value_empty`, `label_not_found`,
`null_unverifiable` 중 하나로 기록했다. Source별 제한 재캡처를 거쳐 legacy
`null_unverifiable`를 0으로 만들되 원문에 없는 값을 생성하지 않았다.

## 확인 결과

| 검증 | 전 | 후 |
| --- | ---: | ---: |
| 강원 review/closed/failed | 12/0/325 | 14/1/322 |
| 제주 review/closed/failed | 207/924/2 | 207/926/0 |
| 전체 failed 분류 | 미완전 | 322/322 |
| legacy `null_unverifiable` | 2,760 | 0 |
| RYP8 blocker | 1 | 0 |
| RYP8 `data_ready` | false | true |

RYP8 완료 시 고정 outcome은 `accepted 18`, `duplicate 1`, `review 1,905`,
`closed 2,360`, `failed 322`였다. 잔여 failed 322건을 성공으로 바꾸지 않았고,
원인 분류와 현재 상세 전건 검증을 구분해 기록했다.

이 복구·감사 경계를 바탕으로 RYP9는 근거가 완전한 정책만 재판정했다. 최종
Data 05 결과는 `accepted 109`, `duplicate 2`, `review 1,140`, `closed 3,033`,
`failed 322`, transition 0·blocker 0이었다.

## 예방 방법

- page 기반 Source는 현재 page와 클릭 identity 일치를 먼저 검증한다.
- timeout은 URL·DOM 준비가 실제로 확인된 경우에만 제한적으로 복구한다.
- 동일 오류가 반복되면 이후 page와 Source를 자동 진행하지 않는다.
- 화면 total, 노출 slot, unique identity, checkpoint total을 같은 값으로 가정하지
  않는다.
- checkpoint 밖 신규 identity를 기존 완료 회차에 자동 편입하지 않는다.
- closed 이력은 재수집하지 않고 저장 Raw·provenance로 대조한다.
- 미복구 failed는 성공으로 계산하지 않고 원인 분류와 검증 범위를 명시한다.
- DB 동기화 전 dry-run·감사 transition 0·동일 Raw `unchanged`를 확인한다.

## 관련 근거

- [현재 데이터 Source 경계](../../data/data_sources.md)
- `collectors/regional_expansion.py`
- `collectors/regional_pilot.py`
- `scripts/audit_regional_ryp8.py`
- `scripts/audit_regional_ryp9.py`
- `tests/test_regional_browser_capture_runtime.mjs`
- `tests/test_regional_review_audit.py`

