# 현재 컨테이너 구조

## 기준

이 문서는 현재 `compose.yaml`, `compose.dev.yaml`과
`compose.production.yaml`의 실제 실행 단위를 설명한다. 사용자가
`run_docker.bat`을 실행하는 Acceptance 구성과 중앙 운영용 Production 구성은
노출 포트와 dataset 준비 방식이 다르다.

## 사용자·심사자 실행 구조

`run_docker.bat`은 다음 순서로 실행한다.

1. Docker Desktop·Compose v2, 포트, 디스크와 로컬 env 소유권 확인
2. `dataset-latest` pointer, manifest와 artifact를 HTTPS로 다운로드
3. manifest·artifact SHA-256, byte 수와 row 수 검증
4. Backend·Frontend image 빌드
5. PostgreSQL과 Redis 시작
6. 일회성 `migrate` 실행과 행정구역 기준 적재
7. 일회성 `public-dataset-bootstrap` 실행
8. Backend·worker·scheduler·Frontend 시작
9. Backend·Frontend health check 후 브라우저 열기

네트워크가 없으면 마지막으로 검증된 immutable cache가 있을 때만 `-Offline`
재실행을 허용한다. 검증된 cache도 없으면 임의의 내장 Seed로 대체하지 않고
실행을 중단한다.

### 장기 실행 서비스 6개

| 서비스 | 책임 | Host 노출 |
| --- | --- | --- |
| `database` | PostgreSQL 정책·dataset·CollectionRun·관리자 상태 저장 | 없음 |
| `redis` | Celery collection queue와 AOF | 없음 |
| `backend` | FastAPI 사용자·관리자 API | `127.0.0.1:8000` 기본 |
| `collection-worker` | 외부 Source 수집·정규화·DB import | 없음 |
| `collection-scheduler` | 선택적 정기 수집 enqueue | 없음 |
| `frontend` | React 정적 파일과 SPA fallback 제공 | `127.0.0.1:3000` 기본 |

`migrate`와 `public-dataset-bootstrap`은 작업을 마치고 종료되는 일회성
서비스이므로 장기 서비스 수에 포함하지 않는다. `restore`, `schema-bootstrap`,
`verify-restored`와 `database-test`는 명시적 profile에서만 실행한다.

```text
Browser
  ├─ http://127.0.0.1:3000 → frontend
  └─ http://127.0.0.1:8000 → backend
                                   ├→ database
                                   └→ redis → collection-worker → official Sources
                                                ↑
                                      collection-scheduler
```

Frontend build에는 브라우저에서 접근할 Backend URL만 들어가며 API key와
관리자 secret은 포함하지 않는다.

## Production 구조

Production Compose는 digest-qualified Backend·Frontend image와 외부에서
검증한 공개 dataset 디렉터리를 사용한다. Host에는 Nginx 하나만 노출한다.

### 장기 실행 서비스 7개

| 서비스 | 책임 |
| --- | --- |
| `database` | Production PostgreSQL |
| `redis` | collection queue |
| `backend` | FastAPI |
| `collection-worker` | 중앙 수집 작업 |
| `collection-scheduler` | 단일 Beat scheduler |
| `frontend` | 정적 SPA 서버 |
| `nginx` | `127.0.0.1:8080`, `/api/` Backend proxy와 Frontend routing |

`migrate`와 `public-dataset-bootstrap`이 성공한 뒤 Backend와 worker가
시작한다. Nginx는 Backend와 Frontend health가 모두 통과한 뒤 요청을 받는다.

```text
Browser → nginx:8080
            ├─ /api/ → backend → database
            └─ /*    → frontend

backend → redis → collection-worker → official Sources
                   ↑
             collection-scheduler
```

TLS와 외부 공개 도메인은 저장소의 loopback-only Compose 바깥에 있는 운영
reverse proxy 또는 플랫폼에서 종료한다. 기본 Production Compose 자체는
인터넷에 직접 포트를 개방하지 않는다.

## 네트워크

| 네트워크 | 연결 서비스 | 경계 |
| --- | --- | --- |
| `app` | Frontend·Backend, Production Nginx | Web 요청 |
| `database` | PostgreSQL·Migration·bootstrap·Backend·worker | internal |
| `queue` | Redis·Backend·worker·scheduler | internal |
| `collector-egress` | collection worker | 공식 Source HTTPS outbound |
| `database-test` | 테스트 PostgreSQL | test profile 전용 internal |

DB와 Redis는 Host port를 공개하지 않는다. 개발 override인
`compose.dev.yaml`을 명시했을 때만 PostgreSQL을 loopback host port로 열고
Backend·Frontend 소스 mount와 hot reload를 사용한다.

## Volume과 데이터 보존

| Acceptance Volume | 내용 |
| --- | --- |
| `acceptance-db` | PostgreSQL 데이터 |
| `redis-data` | Redis AOF |
| `backend-logs` | 구조화 로그 |
| `backend-runtime` | Runtime Raw·checkpoint·처리 산출물 |
| `acceptance-test-db` | test profile 전용 PostgreSQL |

Production은 같은 역할의 `production-db`, `production-redis`,
`production-logs`, `production-runtime` Volume을 사용한다. 일반 `down`은
Volume을 보존한다. `down -v`는 DB·queue·로그·Runtime을 삭제하므로 명시적인
초기화나 clean-room 검증에서만 정확한 Compose project를 확인한 뒤 사용한다.

## 보안과 장애 격리

- 장기 애플리케이션 컨테이너는 read-only root filesystem과 제한된 `tmpfs`를
  사용한다.
- 모든 서비스에 `no-new-privileges`를 적용한다.
- PostgreSQL·Redis·Backend·Frontend에는 health check가 있다.
- scheduler는 기본 비활성화이며 중앙 운영자가 승인한 Source와 시간에만 켠다.
- Source별 DB lock, active run unique 조건과 멱등 import로 중복 실행을 방어한다.
- 공개 dataset 설치가 실패하면 이전 활성 version을 유지한다.
- worker 재시작과 CollectionRun 이력은 공개 dataset membership을 자동 변경하지
  않는다.

## 관련 파일

- `compose.yaml`: 사용자·Acceptance 기준
- `compose.dev.yaml`: 개발용 override
- `compose.production.yaml`: 중앙 Production 기준
- `backend/Dockerfile`, `frontend/Dockerfile`: image 정의
- `scripts/run_docker.ps1`: Windows 한 줄 실행 orchestration
- `deployment/nginx/nginx.conf`: Production proxy
- [Windows Docker 최초 실행](../operations/docker_first_run.md)
- [Production 배포](../operations/production_delivery.md)
