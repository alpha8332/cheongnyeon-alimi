# 관리자 수집 운영

## 기능 목적

중앙 수집기의 준비 상태와 각 수집 실행의 결과를 비밀정보 없이 확인하고, 필요한
경우 관리자가 source별 제한 수집을 요청하게 한다. 공개 dataset 정책 수와 로컬
실행 이력을 혼동하지 않는 것이 핵심이다.

## 사용하는 화면

| 화면 | 주소 | 역할 |
| --- | --- | --- |
| 대시보드 | `/admin` | 최신 CollectionRun과 주요 품질 지표 요약 |
| 수집기 | `/admin/collectors` | source·worker·queue·스케줄·공개 포함 수 확인 |
| 실행 목록 | `/admin/runs` | CollectionRun 필터·페이지·수동 실행 |
| 실행 상세 | `/admin/runs/{runId}` | 한 실행의 전체 count와 오류 유형 확인 |

모든 화면과 API는 유효한 관리자 session을 요구한다.

## 수집기 registry 원리

수집 가능한 source는 stable `source_id`와 factory로 registry에 등록된다. 관리자
화면의 수동 실행 source 계약과 registry가 달라지지 않도록 자동 테스트로
대조한다.

현재 관리자 화면은 등록 수집기 11개의 다음 정보만 제공한다.

- source ID와 사람이 읽을 표시명
- `api`, `file`, `web` 유형
- worker 등록 여부
- 필요한 인증정보의 상태
- 활성 공개 dataset 포함 정책 수
- 진행 중 실행과 최근 실행

수집기 등록은 공개 dataset 포함을 뜻하지 않는다. 기술적으로 수집 가능한 공식
웹 source라도 재배포 근거와 완전 수집 Gate를 통과하기 전에는 공개 정책 수가
0일 수 있다.

## queue와 worker 원리

관리자 수동 실행과 scheduler는 작업 내용을 HTTP process에서 직접 실행하지 않고
Redis queue에 CollectionRun ID와 제한된 실행 인자를 등록한다. Celery worker가
작업을 받아 source lock, 수집, 정규화와 DB 기록을 처리한다.

```text
관리자 요청 또는 scheduler
→ PostgreSQL에 queued CollectionRun 생성
→ Redis collection queue 발행
→ Celery worker 수신
→ source별 lock
→ 수집·정규화·검증·DB 반영
→ terminal CollectionRun 기록
```

DB에 실행 row를 먼저 기록해 broker 오류가 발생해도 요청 사실과 실패 분류를
잃지 않는다. queue 발행이 실패하면 queued 상태로 방치하지 않고 안전한 terminal
실패 상태로 닫는다.

## worker 상태 확인

Backend container에는 원본 Source API key를 주입하지 않는다. collection worker가
관리자 상태 probe에 다음 값만 응답한다.

- 등록 source ID 목록
- 필요한 인증정보의 `설정됨/미설정` boolean

Backend는 여러 worker 응답을 합쳐 broker 연결 여부, 응답 worker 수와 source별
준비 상태를 만든다. worker 이름, hostname, API key 값·길이·일부 문자열은
응답하지 않는다.

| 상태 | 의미 |
| --- | --- |
| 실행 준비됨 | worker 등록과 필요한 인증정보가 확인됨 |
| 인증정보 필요 | worker는 있으나 해당 API credential이 없음 |
| 실행 환경 없음 | worker가 없거나 source가 worker registry에 없음 |
| 상태 확인 필요 | 안전한 응답만으로 확정할 수 없음 |

이 상태는 새 데이터를 수집할 준비 여부다. 이미 설치된 공개 dataset 검색에는
API key가 필요하지 않다.

## scheduler 원리

자동 수집 scheduler는 기본적으로 비활성이다. 중앙 운영 환경에서 명시적으로
활성화하면 설정된 source, 요청 수, KST cron 시·분과 snapshot 옵션으로 단일
Beat 작업을 등록한다.

Backend 상태 화면과 worker·scheduler가 같은 비밀 없는 schedule 설정을 사용해
화면 표시와 실제 실행 설정의 drift를 줄인다. 일반 clone·ZIP 사용자는 scheduler를
켜지 않아도 공개 정책을 검색할 수 있다.

## CollectionRun 원리

CollectionRun은 한 번의 Seed import, Runtime import 또는 수집 실행을 나타내는
PostgreSQL 감사 row다.

주요 상태 전이는 다음과 같다.

```text
queued → running → succeeded
                 ↘ partial_failure
                 ↘ failed
```

terminal 상태는 종료 시각이 있어야 하고 queued·running은 종료 시각이 없어야
한다. 요청·Raw·추출·승인·부분·무효·중복·거부·삽입·갱신·unchanged·skip·실패
count는 음수가 될 수 없다.

한 source에는 동시에 하나의 queued 또는 running 실행만 허용한다. API와 DB
unique 경계를 함께 사용해 동시 요청 race에서도 중복 실행을 막는다.

## 수동 실행 원리

수동 실행은 source와 요청 문서 수를 명시한 뒤 확인 대화상자를 거친다.

1. source가 수동 실행 allowlist에 있는지 확인
2. 같은 source의 활성 실행 조회
3. 오래된 활성 실행인지 판정
4. 새 queued CollectionRun 생성
5. Redis queue 발행
6. worker가 source별 lock을 얻은 뒤 실행

버튼을 누르면 외부 Source 호출과 로컬 DB 변경이 발생할 수 있다. 실행 준비가
안 됐거나 동일 source가 실행 중이면 버튼을 비활성화하거나 충돌 응답을 표시한다.

수동 제한 수집은 공개 dataset 발행 작업이 아니다. 성공해도 정책 row는 활성
공개 membership에 자동 추가되지 않는다.

## stale 판정

queued 또는 running 상태로 종료 시각 없이 기준 시간 이상 머문 실행은
`is_stale=true`로 표시한다. stale은 실제 worker가 성공·실패했다는 판정이 아니라
관리자의 확인이 필요한 감사 신호다.

새 수동 실행을 요청할 때 계약상 교체 가능한 stale 실행은 실패 유형과 종료
시각을 기록한 뒤 새 실행을 만든다. 정상 진행 중 실행은 임의로 종료하지 않는다.

## 실행 목록과 환경 차이

목록은 source, 상태, 실행 유형, trigger와 기간으로 필터링하고 페이지 단위로
조회한다. 상세에서는 모든 count, snapshot 여부, 오류 유형과 시간을 확인한다.

CollectionRun은 다음 이유로 PC마다 개수가 다르다.

- 최초 bootstrap 횟수
- `run_docker.bat` 재실행 횟수
- 수동 수집 실행 여부
- 중앙 scheduler 사용 여부
- 과거 로컬 개발·복구 이력

따라서 작성자 75건, 심사자 8건처럼 달라도 오류가 아니다. 공개 정책 동등성은
CollectionRun 수가 아니라 활성 dataset version, 정책 수와 identity SHA-256으로
확인한다.

## 실패 안전성

- broker 발행 실패: 실행을 명시적 실패로 닫음
- worker 중단: queued/running과 stale로 감사 가능
- source lock 충돌: 제한된 재시도 후 실패 분류
- 부분 수집: 기존 미발견 정책을 자동 inactive 처리하지 않음
- complete snapshot 성공: 전체 목록 증거가 있을 때만 생명주기 변경 허용
- 수동 실행 결과: 공개 membership 자동 변경 금지

## 현재 제한사항

- 화면에서 API key 값을 입력·편집하지 않는다.
- 수동 실행은 모든 source의 완전 release snapshot을 만드는 기능이 아니다.
- worker probe는 짧은 현재 상태이며 네트워크 순간 상태에 따라 unavailable일 수
  있다.
- CollectionRun count를 공개 dataset 최신성 지표로 사용할 수 없다.

## 관련 계약

- [관리자 수집기 상태 API](../../api/admin_collectors.md)
- [CollectionRun 관리자 API](../../api/admin_collection_runs.md)
- [CollectionRun DB 계약](../../architecture/collection_run_database.md)
- [Collector 운영](../../operations/collector.md)
- [정책 생명주기](../../data/policy_lifecycle.md)
