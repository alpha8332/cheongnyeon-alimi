# 공개 dataset 중앙 발행 activation 복구

> 이 문서는 최초 457건 dataset 발행 당시의 장애 기록이다. 현재 공개 기준은
> [2,052건 공개 dataset 계약](../../data/public_policy_dataset.md)을 따른다.

## 요약

- 발생일: `2026-08-24`
- 범위: `public-dataset-release.yml` 중앙 완전 수집과 dataset promotion
- 기준 Git: `f5883bbbc5a830f18114cb6677251389505e9ecc`
- 결과: 네 차례 발행 전 fail-closed 후 다섯 번째 실행 성공
- 개선: worker readiness `79초 → 4초`, `94.9%` 감소

## 문제 상황

공개 dataset을 처음 발행하려고 했지만 GitHub-hosted job의 Celery worker
준비 확인과 실패 진단이 실제 Runtime 특성에 맞지 않았다. 첫 네 실행은 모두
artifact 작성 전에 중단됐다. 이때 불변 dataset Release와 `dataset-latest`는
발행 또는 갱신되지 않아 기존 공개 상태를 보존했다.

| 시도 | Workflow run | 확인된 증상 |
| --- | --- | --- |
| 1 | [32686580763](https://github.com/alpha8332/cheongnyeon-alimi/actions/runs/32686580763) | worker destination hostname을 정확히 찾지 못해 readiness가 79초 뒤 실패 |
| 2 | [32686921421](https://github.com/alpha8332/cheongnyeon-alimi/actions/runs/32686921421) | worker는 ready였지만 `celery inspect ping` remote-control 응답이 없어 실패 |
| 3 | [32687275829](https://github.com/alpha8332/cheongnyeon-alimi/actions/runs/32687275829) | queue 실행 실패를 일반 `CompleteCollectionError`로만 보여 실제 원인을 숨김 |
| 4 | [32687544980](https://github.com/alpha8332/cheongnyeon-alimi/actions/runs/32687544980) | 진단 보강 뒤 `CollectorConfigurationError`와 잘못된 secret 형식을 확인 |
| 5 | [32687869888](https://github.com/alpha8332/cheongnyeon-alimi/actions/runs/32687869888) | 완전 수집·검증·불변 Release·latest promotion 성공 |

## 실제 원인

### 1. readiness가 worker 생존과 준비 상태를 직접 보지 않았다

첫 구현은 실행 환경에서 만들어지는 destination hostname의 정확한 문자열과
Celery remote-control channel의 `inspect ping` 응답에 의존했다. 그러나 worker
process가 broker에 연결되어 `ready` 로그까지 남긴 상태에서도 control reply가
오지 않을 수 있어, 실제 수집 가능 여부와 readiness 판정이 어긋났다.

### 2. queue 경계가 안전한 오류 유형을 지웠다

세 번째 실행은 실제 수집 task까지 도달했지만 상위 실행기가 모든 실패를
일반 오류로 감쌌다. 따라서 secret·Source 설정 오류와 외부 전송 오류를 Workflow
화면에서 구분할 수 없었다.

### 3. Environment Secret에 값 이외의 문자가 포함됐다

`BOKJIRO_API_KEY`에는 복지로 중앙부처복지서비스 key 값 한 줄만 필요하다.
초기 입력에는 API 이름 라벨과 다른 key를 포함한 여러 줄이 들어갔다. Collector의
필수 secret 검증은 공백·줄바꿈이 포함된 값을 거부하므로 완전 수집이 시작되지
않았다. key 자체는 문서나 로그에 기록하지 않고 GitHub Environment Secret에서만
교체했다.

## 해결 과정

1. PR [#23](https://github.com/alpha8332/cheongnyeon-alimi/pull/23)에서 readiness
   진단과 실패 시 worker log 출력을 추가했다.
2. PR [#24](https://github.com/alpha8332/cheongnyeon-alimi/pull/24)에서
   remote-control ping 대신 worker PID 생존과 고정된 `ready` log를 확인하도록
   바꿨다.
3. PR [#25](https://github.com/alpha8332/cheongnyeon-alimi/pull/25)에서 안전하게
   공개 가능한 실제 오류 유형을 보존하고 실패 시 worker log를 남겼다.
4. `production-data` Environment의 `BOKJIRO_API_KEY`를 라벨·줄바꿈 없는 복지로
   key 값 한 줄로 다시 저장했다.

## 결과와 개선율

- worker readiness는 첫 시도 79초에서 성공 시도 4초로 줄었다.
  `(79 - 4) / 79 × 100 = 94.9%` 감소다.
- 성공 Workflow 전체 시간은 57초, 완전 수집 단계는 11초였다.
- CollectionRun `27c8c69d-7c4f-4b6a-aa1c-4f2bc800b445`는 후보 461건,
  accepted 461건, invalid·rejected·failed 각 0건과 complete snapshot을 기록했다.
- 공개 경계가 개인 휴대전화 패턴 4건, 후보의 약 0.9%를 제외해 457건을
  `public-bootstrap-20260824-f5883bb79c594f`로 발행했다.
- 발행 artifact의 email·개인 휴대전화·금지 query pattern match는 모두 0이다.
- artifact SHA-256은
  `6457a37f109381384eb238bb84fd43dd5b60f0d37bc3a262d2c4e483a27ed1f9`,
  manifest SHA-256은
  `03bc9ce4d396c727a1277c1525d1a10a2fff7eb6d23cc08a2d31ac6113930487`다.
- 불변 [dataset Release](https://github.com/alpha8332/cheongnyeon-alimi/releases/tag/dataset-public-bootstrap-20260824-f5883bb79c594f)를
  먼저 검증한 뒤 [dataset-latest](https://github.com/alpha8332/cheongnyeon-alimi/releases/tag/dataset-latest)를
  이동했다.

## 재발 방지

- worker readiness는 환경별 hostname이나 선택적인 remote-control reply가 아니라
  process 생존과 수집 준비 완료 로그를 함께 확인한다.
- 실패 경계는 secret 값을 노출하지 않으면서 오류 유형과 worker tail log를
  보존한다.
- GitHub Environment Secret에는 라벨·주석·따옴표·줄바꿈 없이 해당 API의 값만
  입력한다.
- 공개 발행은 complete snapshot, terminal success, invalid·rejected·failed 0건을
  모두 만족하기 전까지 fail-closed한다.
- 불변 Release 업로드와 재다운로드 hash 검증이 끝난 뒤에만 latest pointer를
  갱신한다.
