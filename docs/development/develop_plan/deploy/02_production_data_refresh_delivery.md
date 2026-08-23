# Deploy 02 Production Data Refresh and Delivery 개발 계획

## 계획 정보

- 번호: Deploy 02
- 담당 영역: Team Leader - Integration·Deploy
- 상태: in-progress
- 현재 Gate: `W6-P3_BOOTSTRAP_PASS` (`2026-08-24`)
- 계획일: `2026-08-23`
- 권장 구현 브랜치: `feature/deploy/production-data-refresh`
- 대상 Release: `v1.0.0`
- 선행 Forest: Integration 07 `W5-G2_PASS`, Deploy 01
  `DOCKER_ACCEPTANCE_PASS`
- 주차 계획: [6주차 Final Release 실행 계획](../../weekly_plan/week_06_final_release.md)

## 목적

저장소를 clone하거나 ZIP으로 받은 사용자가 운영 API key나 비공개 DB dump 없이
검증된 공개 normalized dataset으로 서비스를 실행하게 한다. 중앙 운영 환경은
Celery·Redis 기반 수집 queue에서 신규·변경·종료 정책을 지속해서 반영하고,
성공한 완전 수집 결과만 versioned dataset으로 발행한다.

## 범위

- 공개 재배포 가능 필드와 라이선스·출처 표시 계약
- 공개 normalized bootstrap dataset과 versioned manifest
- `last_seen_at`, `last_verified_at`, `inactive_at` 생명주기
- Redis broker, Celery collector worker와 단일 Celery Beat scheduler
- 관리자 수동 실행 API와 실제 비동기 queue 연결
- Source별 lock·rate limit·timeout·제한된 재시도와 멱등 처리
- PostgreSQL `CollectionRun` 실행 상태와 정책 변경의 원자적 기록
- `run_docker.bat` clone/ZIP 최초 실행 자동화
- Production Compose, Nginx, image·dataset CI/CD와 GHCR 발행
- 새 PC clean-room, 재시작·복구·비밀·로그·실패 시나리오 검증

## 범위 밖

- 실제 API key, 비밀번호, Raw payload와 PostgreSQL dump의 Git·image 포함
- 사용자의 로컬 PC마다 중앙 Source를 자동 수집하는 구조
- Redis를 정책 데이터 또는 `CollectionRun` 상태의 원본으로 사용하는 구조
- 불완전하거나 실패한 수집 결과의 공개 dataset 발행
- Kubernetes, 다중 리전, 자동 수평 확장과 무중단 무상태 운영
- Source 이용약관이 허용하지 않는 원문·첨부파일·연락처의 재배포

## 선행 조건

- Integration 07이 `W5-G2_PASS`로 완료됨
- Deploy 01이 동일 SHA·snapshot의 `DOCKER_ACCEPTANCE_PASS`를 기록함
- 현재 Source별 수집 범위, identity, upsert와 `CollectionRun` 계약을 대조함
- 공개 필드별 이용약관·라이선스·출처 표시 근거를 확인할 책임자를 지정함
- Production secret 저장소와 GHCR·dataset 배포 위치를 구현 전에 확정함

## 공통 설계 원칙

- 공개 dataset은 normalized allowlist만 포함하며 Raw와 DB dump를 포함하지 않는다.
- Redis는 Celery message broker다. 실행 이력과 최종 상태의 원본은 PostgreSQL
  `CollectionRun`이다. Celery result backend를 운영 상태 원본으로 사용하지 않는다.
- task 전달은 중복될 수 있다고 가정하고 Source identity·run key·DB constraint로
  모든 수집과 발행 작업을 멱등하게 만든다.
- Celery Beat는 Production에서 한 instance만 실행한다. Source별 PostgreSQL
  advisory lock 또는 동등한 DB lock으로 겹치는 수집을 차단한다.
- 관리자 API는 긴 수집을 동기 실행하지 않는다. queue 접수 성공 시
  `202 Accepted`와 `CollectionRun` 식별자를 반환한다.
- recoverable 외부 오류만 지수 backoff·jitter로 제한 재시도한다. 계약·인증·
  검증 오류는 재시도 폭주 없이 실패로 종료한다.
- 종료일 경과 정책은 기본 검색에서 제외하되 상시 모집·예산 소진·종료일
  미확정 정책은 Source 근거 없이 날짜만으로 비활성화하지 않는다.
- 미발견 정책은 해당 Source의 권위 범위를 완전히 순회한 실행이 성공했을 때만
  `inactive_at`을 기록한다. 실패·부분 수집에서는 기존 활성 상태를 유지한다.
- dataset manifest에는 dataset·Schema version, 생성 시각, Git SHA, Source
  범위, row count, 파일 SHA-256과 직전 성공 version을 기록한다.
- 사용자는 API key 없이 최신 검증 dataset을 받을 수 있다. 직접 수집은 운영자
  또는 명시적으로 key를 설정한 개발자의 선택 기능으로 분리한다.

## Slice 계획

### W6-P0 - 공개 데이터·라이선스 계약

상태: completed (`2026-08-23`, `W6-P0_DATASET_CONTRACT_PASS`). 복지로
allowlist 후보 461건 중 개인 휴대전화 형식 10건을 제외한 451건 actual
artifact와 manifest hash를 생성·재검증했다.

#### 목적

오픈소스 실행에 포함하거나 별도로 내려받게 할 수 있는 공개 데이터 경계를
확정한다.

#### 산출물

- Source·필드별 재배포 가능 여부와 출처 표시 manifest
- Raw·첨부·개인정보 제외 allowlist
- normalized bootstrap dataset Schema와 version 규칙
- dataset 다운로드 위치·보존 기간·폐기 절차

#### 완료 기준

- 허용 근거가 없는 필드는 fail-closed로 dataset에서 제외됨
- 합성 fixture가 아닌 실제 공개 normalized 표본으로 Schema·hash를 검증함
- 사용자가 API key 없이 bootstrap할 수 있는 경계가 문서화됨

### W6-P1 - 정책 생명주기

상태: completed (`2026-08-24`, `W6-P1_LIFECYCLE_PASS`). 기존 3,273건을
생명주기 timestamp로 backfill하고 마감 1,093건을 기본 공개 조회에서 제외했다.
완전 수집만 soft-deactivation을 허용하며 부분·실패에서는 기존 상태를 보존한다.

#### 목적

신규·변경·종료 정책을 검색 결과와 공개 dataset에 결정적으로 반영한다.

#### 산출물

- `last_seen_at`, `last_verified_at`, `inactive_at` Migration·ORM·API 계약
- 종료일·상시 모집·미발견 처리 규칙
- Source별 complete·partial·failed 실행 판정

#### 완료 기준

- 종료 정책은 기본 검색·추천에서 제외되고 명시적 관리자 조회에는 보존됨
- 완전 수집 성공에서만 미발견 정책이 inactive로 전이됨
- 실패·부분 수집 재현에서 기존 정책이 잘못 비활성화되지 않음

### W6-P2 - 중앙 Celery Collector Worker·Scheduler

상태: completed (`2026-08-24`, `W6-P2_QUEUE_PASS`). API process 내부
`BackgroundTasks` 실행을 제거하고 Redis AOF broker·Celery worker·단일 Beat를
실제 Compose에 연결했다. queued broker 재시작 전달, PostgreSQL Source lock과
성공·실패 terminal 전이, worker 전용 egress의 실제 천안 Source 수집을 actual
환경에서 검증했다.

#### 목적

정기·수동 수집을 Backend 요청 처리와 분리된 실제 queue로 실행한다.

#### 실행 구조

```text
Celery Beat ─┐
             ├→ Redis broker → Celery collector worker → PostgreSQL
Admin API ───┘                                      ├→ Policy lifecycle
                                                   └→ CollectionRun
```

#### 산출물

- Redis, `collector-worker`, `scheduler` Compose services와 health check
- 실제 Celery task와 관리자 `202 Accepted` queue endpoint
- `queued → running → succeeded|partial|failed` 상태 전이
- Source별 singleton lock, rate limit, timeout, retry·backoff 정책
- worker·broker 장애 후 재전달과 멱등 회귀

#### 완료 기준

- 관리자 수동 실행과 Beat 정기 실행이 같은 task 경계를 사용함
- Backend API process에서 collector를 직접 동기 실행하지 않음
- 단일 Beat와 Source lock이 중복 실행·겹침을 차단함
- Redis·worker 재시작과 task 재전달에서도 Policy·CollectionRun 중복이 없음
- Redis 유실 후에도 PostgreSQL의 최종 실행 이력과 정책 상태가 보존됨

### W6-P3 - clone/ZIP 최초 실행

상태: completed (`2026-08-24`, `W6-P3_BOOTSTRAP_PASS`). actual 공개 dataset
451건을 API key 없는 새 Compose project·새 PostgreSQL Volume에 `insert 451`로
적재하고, offline 재실행에서 `unchanged 451`과 전체 service health를 확인했다.
기본 GitHub Release pointer 발행은 W6-P4 promotion 입력으로 넘긴다.

#### 목적

Windows 사용자가 저장소와 README만으로 공개 dataset을 검증·복원하고 Web UI를
실행하게 한다.

#### 산출물

- 저장소 루트 `run_docker.bat`과 실제 로직 PowerShell
- Docker·Compose·환경·port·디스크 사전 점검
- 최신 dataset manifest 다운로드·SHA-256 검증·원자적 cache
- PostgreSQL bootstrap·Migration·서비스 health 대기·Browser 열기
- 재실행, offline cache와 실패 복구 안내

#### 완료 기준

- API key 없는 새 환경에서 one-command 최초 실행이 성공함
- hash 불일치·다운로드 중단·기존 Volume 충돌은 파괴 없이 fail-closed함
- 두 번째 실행은 기존 검증 dataset·Volume을 안전하게 재사용함

### W6-P4 - Production Compose·CI/CD

상태: in-progress (`2026-08-24`). Production Compose·Nginx·dataset promotion·
rollback·GHCR Workflow 구현과 로컬 actual smoke는 통과했다. 원격 GHCR image와
GitHub dataset Release가 아직 발행되지 않았으므로 현재 공식 Gate는
`W6-P3_BOOTSTRAP_PASS`를 유지한다.

#### 목적

검증된 code image와 dataset만 버전이 연결된 배포 산출물로 발행한다.

#### 산출물

- PostgreSQL·Redis·backend·collector-worker·scheduler·frontend/Nginx Compose
- image build·Backend/Data/Frontend test·Migration·Compose smoke CI
- GHCR immutable image tag와 versioned dataset manifest
- 수집→검증→dataset 발행 promotion Gate와 rollback 절차

#### 완료 기준

- image digest, Git SHA, Migration, Schema와 dataset version이 대조됨
- 실패·partial 수집은 새 latest dataset 또는 manifest를 발행하지 않음
- Nginx `/api` reverse proxy와 정적 UI, health·로그·Volume이 검증됨
- 실제 secret과 Raw·dump가 image·Git·CI artifact에 없음

#### 현재 검증 증거와 남은 활성화

- clean project에서 Migration `20260824_0010`, 공개 dataset 451건 import,
  PostgreSQL·Redis·Backend·worker·Beat·Frontend·Nginx health를 확인함
- Nginx `/health`, `/api/v1/policies`, SPA 정적 응답과 단일 host port를 확인함
- 최신 Source별 성공·`is_complete_snapshot=true` CollectionRun만 허용하는
  promotion Gate와 불변 asset
  재다운로드 검증 뒤 latest pointer 갱신 순서를 구현함
- tag/release Workflow를 원격에서 실행해 GHCR digest·attestation,
  `production-release.json`, dataset Release가 일치해야
  `W6-P4_PRODUCTION_PASS`로 닫음

### W6-P5 - clean-room과 Final Gate

#### 목적

작성자 로컬 상태가 없는 새 PC에서 설치·최신화·복구를 독립 재현한다.

#### 검증 시나리오

- README만 보고 clone과 GitHub ZIP 각각 실행
- 신규 정책 insert·변경 update·마감·inactive 정책 기본 검색 제외
- 완전 수집과 partial·failed 수집의 비활성화 경계
- Redis 중단, worker 재시작, Beat 중복 방지와 task 재전달
- 컨테이너 재시작·Volume 유지·backup/restore·dataset rollback
- API key·PIN·DB 비밀번호·로그·Browser bundle 비밀 경계

#### 완료 기준

- 독립 clean-room에서 전체 사용자·관리자 actual Browser 시나리오가 통과함
- 장애 주입 뒤 데이터 손실·중복·잘못된 inactive 전이가 없음
- 설치·운영·복구 문서가 검증자가 사용한 명령과 일치함
- blocker/high 결함 0건과 `W6-G0_FINAL_RELEASE_PASS`를 기록함

## 검증 계획

- Data lifecycle·manifest·hash·라이선스 allowlist 단위 테스트
- Celery task eager/unit와 Redis 실제 broker 통합 테스트
- PostgreSQL Migration·lock·멱등·transaction·동시 실행 회귀
- complete·partial·failed Source의 신규·변경·inactive 결정 테스트
- Production image build, Compose health와 Nginx actual API smoke
- Mock·actual Browser 전체 회귀와 관리자 queue 상태 전이 확인
- Windows clone/ZIP clean-room 및 재시작·복구·offline cache 검증
- `python scripts/validate_docs.py`, 비밀·대용량 산출물 추적 검사

## Forest 완료 기준

- W6-P0~P5 완료 기준을 모두 충족함
- 공개 dataset의 재배포 근거·allowlist·manifest·hash가 확정됨
- Celery·Redis queue가 정기·수동 수집을 실제 worker와 연결함
- PostgreSQL이 CollectionRun·정책 lifecycle의 원본이고 중복 task에 안전함
- API key 없는 clone/ZIP one-command bootstrap이 새 PC에서 통과함
- 실패·partial 수집은 기존 정책과 latest dataset을 안전하게 유지함
- Production Compose·GHCR image·versioned dataset과 CI가 동일 SHA로 연결됨
- clean-room·보안·복구·전체 회귀가 통과하고 `W6-G0_FINAL_RELEASE_PASS`가 기록됨

## 위험과 미확정 사항

- Source별 재배포 허용 범위가 다르면 하나의 dataset에 무조건 합치지 않고
  Source 또는 필드 단위로 제외·분리해야 한다.
- Redis broker는 영구 정책 저장소가 아니다. broker 장애·visibility timeout과
  재전달을 전제로 task 멱등성·DB 상태 전이를 검증해야 한다.
- Beat를 여러 개 실행하거나 긴 수집이 다음 주기와 겹치면 중복 실행될 수 있어
  단일 scheduler와 Source별 DB lock을 필수로 둔다.
- GitHub Release·GHCR·dataset hosting의 용량·트래픽·보존 정책은 W6-P0에서
  확정한다.
- API key 없는 사용자와 중앙 운영자의 설정을 같은 `.env`에 섞지 않는다.

## 관련 문서

- [6주차 Final Release 실행 계획](../../weekly_plan/week_06_final_release.md)
- [Release와 Milestone 계획](../release_roadmap.md)
- [주차별 실행 계획](../weekly_delivery_plan.md)
- [Deploy 01 Docker Acceptance](01_docker_acceptance_environment.md)
- [CollectionRun DB 계약](../../../architecture/collection_run_database.md)
- [컨테이너 구조](../../../architecture/container_structure.md)
- [Collector 실행](../../../operations/collector.md)
- [수집 정책](../../../data/collection_policy.md)
- [Celery periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)
- [Celery task retry](https://docs.celeryq.dev/en/stable/userguide/tasks.html#retrying)
