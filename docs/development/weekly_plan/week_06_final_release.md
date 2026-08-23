# 6주차 - Production Data Refresh와 Final Release

## 계획 정보

- 상태: in-progress (`2026-08-24`, `W6-P3_BOOTSTRAP_PASS`)
- 대상 Release: `v1.0.0`
- 선행 Gate: `W5-G2_PASS`, `DOCKER_ACCEPTANCE_PASS`
- 핵심 Forest: [Deploy 02 Production Data Refresh and Delivery](../develop_plan/deploy/02_production_data_refresh_delivery.md)
- 최종 Gate: `W6-G0_FINAL_RELEASE_PASS`
- 수행 역할: Data, Backend, Frontend, Team Leader - Integration·Deploy,
  보고서·사용성 리뷰·QA

## 목표

공개 normalized dataset, 중앙 Celery·Redis 수집, one-command 최초 실행과
Production Compose·CI/CD를 완성한다. 새 PC 사용자는 API key 없이 서비스를
실행하고, 중앙 운영 환경은 신규·변경·종료 정책을 안전하게 최신화한다.

## 시작 조건

- 5주차 Release 2가 `W5-G2_PASS`로 닫힘
- Deploy 01 동일 snapshot 환경이 `DOCKER_ACCEPTANCE_PASS`를 통과함
- 코드 검증 SHA와 Gate 문서 commit이 Final Release 작업 기준으로 고정됨
- 6주차 동안 새 사용자 기능은 동결하고 배포 blocker·보안·데이터 최신화만 수정함

## 현재 기준선

- PostgreSQL 실제 Acceptance snapshot 복원·Migration·재시작 보존 검증 완료
- Backend·Frontend Docker image와 actual Browser 흐름 검증 완료
- `CollectionRun` 목록·상세·수동 실행은 Redis·Celery 실제 queue에 연결됐고
  Source singleton·재전달·broker restart 회귀를 통과함
- 공개 dataset 계약·정책 inactive·중앙 queue와 `run_docker.bat` actual clean
  bootstrap은 완료됐으며 Production Nginx·CI와 자동 dataset 발행은 P4 범위

## 범위

- `W6-P0` 공개 데이터·라이선스와 normalized dataset 계약
- `W6-P1` 정책 생명주기와 안전한 inactive 전이
- `W6-P2` Redis broker·Celery worker·단일 Beat와 실제 queue
- `W6-P3` clone/ZIP `run_docker.bat` 최초 실행
- `W6-P4` Production Compose·Nginx·CI/CD·GHCR·dataset manifest
- `W6-P5` 독립 clean-room과 Final Gate

## 범위 밖

- API key·Raw·DB dump의 공개 저장소·image·dataset 포함
- 각 사용자 PC의 무조건적인 직접 크롤링
- Kubernetes·다중 리전·자동 수평 확장
- Final Release에 필요하지 않은 새 사용자 기능과 UI 확장

## 실행 원칙

- Redis는 broker, PostgreSQL은 Policy·CollectionRun 상태 원본으로 사용한다.
- queue task는 재전달과 중복 실행을 전제로 멱등하게 만든다.
- 완전 수집 성공에서만 미발견 정책을 inactive 처리한다.
- 실패·partial 수집은 기존 정책과 latest 공개 dataset을 유지한다.
- 공개 dataset은 라이선스 allowlist와 SHA-256 검증을 통과한 normalized 필드만
  발행한다.
- 사용자는 API key 없이 dataset bootstrap으로 실행하고, key는 중앙 운영
  worker 또는 직접 수집을 선택한 개발자에게만 요구한다.

## 선행 관계와 Critical Path

```text
W5-G2_PASS
  → W6-P0 공개 데이터·라이선스 계약
  → W6-P1 정책 생명주기
  → W6-P2 중앙 Celery·Redis 수집
  → W6-P3 clone/ZIP 최초 실행
  → W6-P4 Production Compose·CI/CD
  → W6-P5 clean-room
  → W6-G0_FINAL_RELEASE_PASS
```

P0의 dataset·라이선스 계약과 P1의 lifecycle 계약 전에는 공개 artifact와
미발견 inactive 기능을 구현 완료로 판정하지 않는다. P2 queue와 P3 bootstrap은
각자 준비할 수 있지만 P4 Production Compose Gate에서 동일 image·Migration·
dataset version으로 합친다.

## 단계별 Gate

| 단계 | Gate | 필수 증거 |
| --- | --- | --- |
| W6-P0 | `W6-P0_DATASET_CONTRACT_PASS` | 필드 allowlist·라이선스·Schema·manifest·hash |
| W6-P1 | `W6-P1_LIFECYCLE_PASS` | complete/partial/failed와 신규·변경·inactive PostgreSQL 회귀 |
| W6-P2 | `W6-P2_QUEUE_PASS` | 수동·Beat queue, worker 장애·재전달·lock·멱등성 |
| W6-P3 | `W6-P3_BOOTSTRAP_PASS` | API key 없는 clone/ZIP one-command 실행·hash·재실행 |
| W6-P4 | `W6-P4_PRODUCTION_PASS` | Production Compose·Nginx·CI·GHCR·dataset promotion/rollback |
| W6-P5 | `W6-G0_FINAL_RELEASE_PASS` | 독립 clean-room·전체 actual·보안·복구·blocker/high 0건 |

## 역할별 작업

### Data

- Source·필드별 재배포 허용 근거와 normalized allowlist 확정
- lifecycle 결정, complete/partial/failed 판정과 dataset manifest 구현
- 신규 insert·변경 update·미발견 inactive actual fixture·회귀 제공

### Backend

- lifecycle Migration·ORM·검색 기본 제외와 관리자 보존 조회 구현
- 관리자 수동 실행을 Celery queue와 연결하고 `CollectionRun` 상태 전이 구현
- task 멱등성·Source lock·timeout·retry·rate limit과 보안 회귀 제공

### Frontend

- queue 접수·실행 중·성공·partial·실패 상태를 실제 관리자 API로 표시
- inactive 정책이 기본 검색·추천에 노출되지 않는 actual Browser 회귀
- Production Nginx 경로와 최초 실행·오류 UI 검증

### Team Leader - Integration·Deploy

- Redis·worker·Beat·PostgreSQL·Backend·Nginx Compose와 CI/CD 통합
- `run_docker.bat`, dataset download·hash·bootstrap·복구 흐름 구현
- image digest·Git SHA·Migration·dataset version 대조와 Gate 판정

### 보고서·사용성 리뷰·QA

- 보고서 담당은 라이선스·성능·장애 복구와 최종 제출 근거를 대조
- 사용성 리뷰어는 README만 보고 clone/ZIP 최초 실행과 핵심 흐름 검증
- QA는 queue 장애, 중복 task, partial 수집, 재시작·Volume·비밀·복구와
  Production actual 회귀 검증

## 산출물

- 공개 dataset 계약·manifest·versioned artifact
- lifecycle Migration·수집·검색·관리자 계약
- Celery app·task, Redis broker, worker·Beat service
- `run_docker.bat`과 Windows PowerShell bootstrap
- Production Dockerfile·Compose·Nginx·CI/CD·GHCR image
- 운영·백업·복구·dataset rollback·Collector·README 문서
- clean-room receipt와 `W6-G0_FINAL_RELEASE_PASS` 기록

## 테스트와 검증

- Data·Backend·Frontend 단위·lint·build 전체 회귀
- PostgreSQL lifecycle·lock·transaction·Migration·성능 회귀
- 실제 Redis broker와 Celery worker·Beat 통합·장애 주입
- Production Compose health, Nginx API·정적 파일과 Browser actual
- clone과 GitHub ZIP 각각의 Windows clean-room·재실행·offline cache
- dataset hash 불일치·partial/failed 수집·Redis/worker 중단·rollback
- 비밀·Raw·dump·로그·image·Git 추적 검사와 문서 검증

## 위험과 결정 필요 사항

- Source별 라이선스가 공개 dataset을 허용하지 않으면 해당 Source 또는 필드를
  제외하고 중앙 서비스 API 제공 범위를 별도로 결정한다.
- Celery·Redis 도입으로 service·장애 지점이 늘어나므로 health, retry, lock,
  clean-room 검증 중 하나라도 빠지면 `W6-P2_QUEUE_PASS`를 부여하지 않는다.
- 공개 dataset hosting과 GHCR 보존·용량 정책은 W6-P0에서 확정한다.
- 운영 API key와 공개 실행 설정을 같은 배포 artifact에 포함하지 않는다.

## 인계사항 발생 조건

- 라이선스 근거 미확정 Source는 Data·보고서 담당 확인 전 발행에서 제외
- Migration·검색 기본 제외 계약 변경은 Backend·Frontend actual 소비 검토 필요
- queue 상태·오류 DTO 변경은 Backend·Frontend 공동 승인 필요
- dataset·image version 불일치는 Team Leader가 promotion을 중단하고 P4로 반환
- clean-room blocker/high 결함은 담당 영역 수정 뒤 새 SHA로 P5 전체 재검증

## 완료 체크리스트

- [x] `W6-P0_DATASET_CONTRACT_PASS` (복지로 451건 actual artifact·manifest hash)
- [x] `W6-P1_LIFECYCLE_PASS` (3,273건 backfill, 마감 1,093건 제외,
  PostgreSQL 18건·전체 548건 회귀)
- [x] `W6-P2_QUEUE_PASS` (Redis AOF·worker·Beat healthy, actual queue 성공·
  외부 Source 실패 종료·egress 보정 후 live 수집 성공·broker restart 재전달·
  PostgreSQL Source lock)
- [ ] `W6-P3_BOOTSTRAP_PASS`
- [ ] `W6-P4_PRODUCTION_PASS`
- [ ] clone·ZIP 독립 clean-room과 전체 actual 회귀
- [ ] README·Collector·운영·복구·LICENSE·SBOM·CHANGELOG·제출 문서 대조
- [ ] blocker/high 결함 0건과 `W6-G0_FINAL_RELEASE_PASS`
- [ ] 사용자 승인 뒤 `main`·`v1.0.0` 후보 지정

## 관련 문서

- [Deploy 02 Production Data Refresh and Delivery](../develop_plan/deploy/02_production_data_refresh_delivery.md)
- [Release와 Milestone 계획](../develop_plan/release_roadmap.md)
- [주차별 실행 계획](../develop_plan/weekly_delivery_plan.md)
- [5주차 Release 2 계획](week_05_release_2.md)
- [Deploy 01 Docker Acceptance](../develop_plan/deploy/01_docker_acceptance_environment.md)
- [컨테이너 구조](../../architecture/container_structure.md)
- [CollectionRun DB 계약](../../architecture/collection_run_database.md)
