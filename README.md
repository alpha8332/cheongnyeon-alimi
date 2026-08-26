# 청년정책알리미

[![CI](https://github.com/alpha8332/cheongnyeon-alimi/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/alpha8332/cheongnyeon-alimi/actions/workflows/ci.yml)
[![GitHub Release](https://img.shields.io/github/v/release/alpha8332/cheongnyeon-alimi)](https://github.com/alpha8332/cheongnyeon-alimi/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

청년정책알리미는 지역·연령·관심 분야와 검색어에 맞는 청년정책을 찾고 추천받는
오픈소스 웹 프로그램입니다. 정책의 핵심 신청 조건, 지원 내용, 마감일과 공식
원문을 한곳에서 확인할 수 있습니다.

일반 사용자와 대회 심사자는 원본 정책 API key, Python, Node.js나 PostgreSQL을
직접 설치할 필요가 없습니다. Windows와 Docker Desktop만 있으면 검증된 공개
정책 dataset을 포함한 전체 서비스를 실행할 수 있습니다.

## 무엇을 할 수 있나요?

| 기능 | 설명 |
| --- | --- |
| 정책 검색 | 검색어, 지역, 연령, 분야와 신청 상태로 정책을 찾고 정렬·페이지 이동 |
| 정책 상세 | 핵심 신청 조건, 미확정 정보, 지원 내용, D-Day와 공식 원문 확인 |
| 맞춤 추천 | 저장한 거주지역·연령·복수 관심 분야에 맞는 정책과 추천 이유 확인 |
| 관심 정책 | 폴더형 즐겨찾기, 마감 알림, 달력과 `.ics` 일정 다운로드 |
| 관리자 | PIN 로그인·변경·분실 복구, 수집기·CollectionRun·정책·품질·로그 확인 |

회원가입은 필요하지 않습니다. 프로필과 즐겨찾기는 현재 브라우저에만 저장되며
다른 PC나 브라우저와 자동 동기화되지 않습니다.

## 바로 실행하기

### 1. 준비 사항

- Windows 10 또는 11
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)과 Docker
  Compose v2
- image·cache·Volume을 위한 여유 공간 2 GiB 이상
- 기본 포트 `3000`, `8000`을 다른 프로그램이 사용하지 않는 환경
- 최초 dataset을 내려받을 인터넷 연결

Docker Desktop을 실행하고 Engine 시작이 끝날 때까지 기다립니다. 그 외 개발
도구는 필요하지 않습니다.

### 2. 소스 받기

Git을 사용할 수 있으면 PowerShell에서 다음 명령을 실행합니다.

```powershell
git clone https://github.com/alpha8332/cheongnyeon-alimi.git
cd cheongnyeon-alimi
```

Git이 없으면 GitHub의 **Code → Download ZIP**을 선택하고 압축을 풉니다. 이후
저장소 또는 압축을 푼 폴더에서 PowerShell을 엽니다.

### 3. 서비스 시작

저장소 루트에서 다음 한 줄을 실행합니다.

```powershell
.\run_docker.bat
```

최초 실행에서는 관리자 화면에 사용할 숫자 4자리 PIN을 직접 입력합니다.
고정된 기본 PIN은 없으며 `0000`도 자동 설정되지 않습니다. 입력한 PIN 평문은
저장하지 않으므로 본인이 정한 PIN을 기억해 두세요.

실행기는 다음 작업을 자동으로 처리합니다.

1. Docker·Compose·디스크·포트 확인
2. 공개 정책 dataset 다운로드와 SHA-256·정책 수 검증
3. Backend·Frontend image build
4. PostgreSQL Migration과 공개 dataset 적재
5. Redis·Backend·수집 worker·scheduler·Frontend 시작
6. health check 통과 후 사용자 화면 열기

첫 build는 Docker image 다운로드 때문에 시간이 걸릴 수 있습니다. 마지막에
다음 코드가 표시되면 실행에 성공한 것입니다.

```text
W6_P3_BOOTSTRAP_READY: url=http://127.0.0.1:3000 ...
```

- 사용자 화면: <http://127.0.0.1:3000>
- 관리자 로그인: <http://127.0.0.1:3000/admin/login>
- Backend 상태: <http://127.0.0.1:8000/health>

## 처음 사용할 때

1. 홈에서 예시 검색어나 원하는 문장을 입력합니다.
2. 정책 목록에서 지역·연령·분야·신청 상태를 조정하고 결과를 정렬합니다.
3. 정책 상세에서 신청 조건과 공식 원문을 확인합니다.
4. 맞춤 추천을 사용하려면 프로필에 거주지역·연령·관심 분야를 저장합니다.
5. 관심 정책은 즐겨찾기에 넣어 마감 알림과 달력에서 확인합니다.

검색과 추천에는 다음 원칙이 적용됩니다.

- 시·군·구를 선택하면 해당 지역, 상위 시·도와 전국 대상 정책을 함께 찾습니다.
- 지역 근거가 없는 정책을 전국 정책으로 임의 추정하지 않습니다.
- `대학생`처럼 넓거나 유사한 표현에는 관련 검색어를 함께 안내합니다.
- 프로필 관심 분야는 여러 개 저장할 수 있고 검색 조건을 덮지 않으면서 결과
  우선순위를 보정합니다.
- 복지와 주거처럼 여러 분야에 해당하는 정책은 모든 해당 분야를 표시합니다.
- 검색과 추천은 신청 가능성을 확정하지 않으므로 최종 조건은 공식 원문에서
  확인해야 합니다.

## 관리자 PIN과 관리자 화면

관리자 로그인에는 최초 실행에서 정한 4자리 PIN을 사용합니다.

### PIN 변경

1. <http://127.0.0.1:3000/admin/login>에서 로그인합니다.
2. 관리자 메뉴의 **보안**으로 이동합니다.
3. 현재 PIN, 새 PIN과 새 PIN 확인을 입력합니다.

PIN을 변경하면 기존 관리자 세션이 모두 종료되며 새 PIN으로 다시 로그인해야
합니다.

### PIN 분실 복구

PIN을 잊었다면 먼저 `run_docker.bat`으로 Backend를 실행한 뒤, 저장소 루트의
PowerShell에서 다음 명령을 실행합니다.

```powershell
.\reset_admin_pin.bat
```

새 숫자 4자리 PIN을 두 번 입력하면 됩니다. 이 복구는 정책 DB, 공개 dataset,
즐겨찾기와 CollectionRun을 삭제하지 않습니다. `.env.compose` 삭제나
`docker compose --env-file .env.compose down -v`는 PIN 복구 방법이 아닙니다.

### 관리자 화면에서 확인할 수 있는 것

- 대시보드: 공개 정책과 최근 수집·품질 상태
- 수집기: 등록 Source, worker·queue, 인증정보 설정 여부와 공개 정책 수
- CollectionRun: 이 PC에서 실행된 적재·수집 이력과 stale 상태
- 정책·품질·로그: 정책 데이터, 품질 지표와 비밀정보가 제거된 구조화 로그

공개 정책 검색에는 API key가 필요하지 않습니다. 관리자 수집 화면의 수동 실행은
새 원본 데이터를 수집하는 중앙 운영 기능이므로 Source에 따라 API key가 없으면
비활성화될 수 있습니다. 수동 수집에 성공해도 검증·승격 전에는 사용자 검색에
자동 공개되지 않습니다.

## 종료와 재실행

정책 DB와 설정을 보존하면서 컨테이너를 종료하려면 다음 명령을 사용합니다.

```powershell
docker compose --env-file .env.compose down
```

다시 사용할 때는 `run_docker.bat`을 실행합니다. 기존 DB를 재사용하고 최신 공개
dataset을 다시 검증해 멱등 반영합니다.

`docker compose --env-file .env.compose down -v`는 DB와 실행 이력을 포함한
Docker Volume을 삭제합니다. 완전 초기화가 목적일 때만 사용하세요.

## 공개 정책 데이터

최초 실행에는 온통청년·복지로 API key가 필요하지 않습니다. `run_docker.bat`은
GitHub Release의 `dataset-latest` pointer가 가리키는 artifact를 내려받고
manifest의 SHA-256, 파일 크기와 정책 수를 모두 확인한 뒤 설치합니다.

2026-08-25에 검증한 `v1.0.2` dataset은 다음과 같습니다.

| Source | 정책 수 |
| --- | ---: |
| 복지로 중앙부처 복지서비스 | 461건 |
| 온통청년 청년정책 API | 1,587건 |
| 인천광역시 청년공간 유유기지 공개 파일 | 4건 |
| 합계 | 2,052건 |

dataset version은 `public-bootstrap-20260824-897152e7a18c15`입니다. 이후 새
dataset이 승격되면 내려받은 manifest의 version과 정책 수가 우선합니다.

같은 dataset version을 설치한 PC는 같은 공개 정책 identity 집합을 검색합니다.
반면 관리자 화면의 CollectionRun은 각 PC의 설치·재실행·수동 수집 감사 기록이므로
환경마다 개수가 달라도 정상입니다.

## 자주 발생하는 문제

| 증상 | 해결 방법 |
| --- | --- |
| `docker.exe`를 찾지 못함 | Docker Desktop 설치 후 새 PowerShell에서 `docker version` 확인 |
| Docker engine이 실행 중이 아님 | Docker Desktop을 실행하고 Engine 시작 완료 후 재시도 |
| `3000` 또는 `8000` 포트 충돌 | 아래 포트 변경 명령 사용 |
| dataset 다운로드 실패 | 네트워크 확인; 검증된 이전 cache가 있을 때만 `run_docker.bat -Offline` 사용 |
| `.env.compose` 없이 기존 DB Volume 발견 | 기존 `.env.compose`를 복구하거나 기존 환경의 소유 관계를 먼저 확인 |
| 관리자 PIN을 잊음 | Backend 실행 후 `reset_admin_pin.bat` 실행 |
| 브라우저가 자동으로 열리지 않음 | <http://127.0.0.1:3000>을 직접 열고 `docker compose --env-file .env.compose ps` 확인 |

포트를 바꿔 실행할 수 있습니다.

```powershell
.\run_docker.bat -FrontendPort 3100 -BackendPort 8100
```

같은 환경을 재실행할 때도 같은 포트를 지정하거나 `.env.compose`의
`FRONTEND_HOST_PORT`, `BACKEND_HOST_PORT`를 수정합니다. 더 자세한 실행·cache·복구
절차는 [Windows Docker 실행 안내](docs/operations/docker_first_run.md)를
참고하세요.

> 현재 한 줄 실행은 Windows 10/11과 Docker Desktop에서 검증했습니다. macOS와
> Linux는 `run_docker.bat` 실행 대상이 아닙니다.

## 더 자세한 문서

- 기능별 사용법과 원리: [제품 기능 설명서](docs/product/README.md)
- 전체 문서 색인: [문서 안내](docs/index.md)
- 현재 서비스·컨테이너 구조: [아키텍처 개요](docs/architecture/overview.md),
  [컨테이너 구조](docs/architecture/container_structure.md)
- 공개 데이터 범위: [공개 정책 dataset 계약](docs/data/public_policy_dataset.md)
- 관리자 PIN 변경·복구: [Windows Docker 실행 안내](docs/operations/docker_first_run.md#관리자-pin-변경과-분실-복구)
- 변경 이력: [CHANGELOG](CHANGELOG.md)
- 기여 방법: [CONTRIBUTING](CONTRIBUTING.md)

## 보안과 개인정보

- 관리자 PIN 평문, API key, DB 비밀번호와 token을 문서·Issue·commit에 올리지
  마세요.
- `.env.compose`, Runtime Raw·로그와 PostgreSQL 데이터는 Git에서 제외됩니다.
- 프로필과 즐겨찾기는 현재 브라우저의 `localStorage`에 저장됩니다.
- 검색·추천에 필요한 조건은 사용자의 로컬 Backend에만 전달하며 외부 정책
  Source나 중앙 운영 서버에 사용자 프로필로 저장하지 않습니다.

## 라이선스

프로젝트 코드는 [MIT License](LICENSE)로 배포합니다. 정책 데이터는 코드
라이선스와 별도이며 각 Source의 이용 조건과
[공개 정책 dataset 계약](docs/data/public_policy_dataset.md)을 따릅니다.
