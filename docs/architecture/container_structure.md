# 컨테이너 구조

## 문서 상태

- 상태: 초기 목표 기준선, Acceptance 구현 계획 승인
- 현재 구현 상태: Docker 구성 미구현 (`Deploy 01` 실행 전)

이 문서는 초기 개발과 Release 1에서 목표로 하는 실행 단위를 정의한다.
아래 서비스 이름과 연결은 구현 시 검증해야 하며, 현재 실행 가능하다는
의미가 아니다.

구현은 두 단계로 나눈다. 5주차
[Deploy 01 Docker Acceptance Environment](../development/develop_plan/deploy/01_docker_acceptance_environment.md)은
BE·FE 담당자, 리뷰어와 QA가 동일 Git SHA·실제 DB snapshot으로 검증하기 위한
내부 Acceptance 환경을 만든다. 6주차 `v1.0.0` 배포 Forest는 이를 Nginx,
Production image, CI, 초기 bootstrap과 운영 복구까지 확장한다. Deploy 01
통과만으로 Production 배포가 완료된 것은 아니다.

## 초기 구성

초기에는 다음 세 컨테이너로 시작한다.

```text
Browser
   ↓
frontend
   ↓ HTTP / API
backend
   ↓ SQL
database
```

```yaml
services:
  frontend:
  backend:
  database:
```

목표 완료 상태는 `docker compose up`으로 세 서비스가 시작되고, 프론트엔드,
백엔드 health check와 PostgreSQL 연결을 확인할 수 있는 것이다.

## 서비스별 책임

### `frontend`

- React 정적 자산의 개발 또는 배포
- 사용자·관리자 Web UI 제공
- `/api` 계약에 따른 Backend 호출
- 런타임 비밀정보를 번들에 포함하지 않음

Frontend Dockerfile의 목표 위치는 `frontend/`이다. 파일 작성과 이미지 빌드는
Frontend Forest의 기본 책임이 아니라 통합·배포 Forest에서 수행한다.

### `backend`

- FastAPI 애플리케이션 실행
- 정책 조회·검색·추천과 운영 API 제공
- PostgreSQL 접근
- 초기 단계에서 Collector와 Scheduler 실행 진입점 제공

Collector 코드는 최상위 `collectors/`의 독립 모듈로 유지한다. 초기에는 별도
상시 컨테이너를 만들지 않고 Backend 이미지 또는 개발 환경에서 명시적인
명령으로 실행한다. API 요청 처리 과정에서 긴 수집 작업을 동기 실행하는
구조를 의미하지 않는다.

Backend Dockerfile의 목표 위치는 `backend/`이다. 파일 작성과 이미지 빌드는
Backend Forest의 기본 책임이 아니라 통합·배포 Forest에서 수행한다.

### `database`

- PostgreSQL 실행
- 정규화된 정책, 출처, 수집 실행과 서비스 데이터 저장
- 영속 Volume을 사용해 컨테이너 재시작 후 데이터 유지
- health check를 제공해 Backend 연결 순서를 검증

DB 비밀번호와 실제 연결 정보는 `.env` 또는 배포 환경의 비밀 관리 수단에서
주입하고 Git에 커밋하지 않는다.

## 코드와 실행 단위의 관계

```text
repository
├── frontend/       → frontend container
├── backend/        → backend container
├── collectors/     → backend image에서 초기 실행, 향후 분리 가능
├── data/schema/    → 데이터 계약
├── data/fixtures/  → 개발·테스트 입력
├── database/       → ERD와 초기 DB 자료
└── deployment/     → 공통 배포 설정
```

논리적 모듈과 컨테이너를 반드시 1:1로 만들지 않는다. Collector를 최상위
모듈로 분리하는 이유는 책임과 테스트 경계를 유지하기 위해서이며, 초기부터
별도 운영 컨테이너가 필요하다는 뜻은 아니다.

## 개발 산출물과 컨테이너 통합

각 영역은 컨테이너 파일보다 먼저 재현 가능한 애플리케이션 산출물을
제공한다.

| 영역 | 통합 전에 제공할 산출물 |
| --- | --- |
| Frontend | 소스 코드, `package.json`, 단일 lockfile, 환경변수 예시, 실행·테스트 명령 |
| Backend | 소스 코드, 합의된 Python manifest·lockfile, 환경변수 예시, 실행·테스트 명령 |
| Data | 데이터 처리 코드, Schema·Fixture·Seed와 확정된 실행 환경에 반영한 Python 의존성 |

관련 Forest 결과가 `develop`에 병합된 뒤 통합·배포 Forest에서 다음을
수행한다.

1. Frontend와 Backend Dockerfile 작성
2. Database를 포함한 Compose 구성
3. 서비스 네트워크, 환경변수, Volume과 health check 설정
4. manifest와 lockfile을 이용한 재현 가능한 이미지 빌드
5. `docker compose up` 기반 전체 실행과 통합 테스트

통합 담당은 라이브러리와 버전을 추측하지 않고 각 영역이 제공한 manifest와
lockfile을 사용한다. 개별 영역 Forest에서 컨테이너 작업이 필요하면 해당
Forest 계획에 범위와 완료 기준을 명시해야 한다.

## 데이터 저장

| 데이터 | 저장 위치 | Git 포함 |
| --- | --- | --- |
| JSON Schema | `data/schema/` | 포함 |
| 검토된 최소 Fixture·Seed | `data/fixtures/`, `data/seeds/` | 포함 |
| 실제 수집 Raw | Runtime Volume 또는 운영 저장소 | 제외 |
| 처리 결과와 rejected 데이터 | Runtime Volume 또는 DB | 제외 |
| PostgreSQL 데이터 | Database Volume | 제외 |

운영 Raw와 DB Volume을 컨테이너 이미지 안에 굽지 않는다. 백업과 복구 절차는
운영 기능이 구현될 때 별도 문서로 검증한다.

## Production 진입점

최종 배포에서는 Nginx가 React 정적 파일을 제공하고 `/api` 요청을 FastAPI로
전달하는 구성을 목표로 한다.

```text
Nginx
├── React 정적 파일
└── /api → FastAPI → PostgreSQL
```

Nginx 도입 시점, TLS, 도메인과 네트워크 설정은 배포 Slice에서 확정한다.
초기 개발 기준선에 구현 완료 사항으로 포함하지 않는다.

## 향후 분리 조건

다음 조건이 생기면 Collector Worker와 Scheduler의 별도 컨테이너 분리를 ADR로
검토한다.

- 수집 작업이 API 프로세스의 자원 또는 안정성에 영향을 줌
- 독립적인 재시작, 확장 또는 배포 주기가 필요함
- 정기 작업과 수동 실행의 동시성 제어가 필요함

검토 대상 구조:

```text
frontend
backend
collector-worker
scheduler
database
```

조건을 충족하기 전에는 복잡도를 미리 늘리지 않는다. 실행 단위를 변경하면
[아키텍처 결정 기록](decisions/README.md)에 근거와 영향을 남긴다.
