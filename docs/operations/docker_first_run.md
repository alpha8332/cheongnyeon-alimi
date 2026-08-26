# Windows Docker 최초 실행

## 적용 범위

저장소를 Git clone 또는 GitHub ZIP으로 받은 Windows 사용자가 API key 없이
검증된 공개 normalized dataset을 PostgreSQL에 적재하고 전체 Web UI를 실행하는
절차다. 실제 Source 수집과 정기 scheduler 활성화는
[Collector 실행](collector.md)의 중앙 운영자 범위다.

Git clone·GitHub ZIP clean-room 검증을 완료했다. 기본 GitHub Release pointer는
활성 상태이며 API key 없이 pointer가 가리키는 검증된 공개
dataset을 내려받는다. 현재 정책 수·Source별 건수·SHA-256은 함께 받은 manifest로
확인한다. `-DatasetManifestPath`는 별도 검증 artifact를 고정해 재현할 때만
사용한다.

`2026-08-25` actual 재검증에서 latest pointer는
`public-bootstrap-20260824-897152e7a18c15` 2,052건을 제공했고, 복지로 461건,
온통청년 1,587건, 인천 공공데이터 4건을 설치했다. 이 값은 해당 version의
검증 snapshot이며 pointer가 승격되면 새 manifest의 row 수와 hash를 우선한다.

## 요구 환경

- Windows 10 또는 11
- 실행 중인 Docker Desktop과 Docker Compose v2
- cache와 image·Volume을 위한 여유 공간 2 GiB 이상
- 기본 host port `3000`, `8000` 또는 `.env.compose`에서 지정한 빈 port
- 최초 실행 때 입력할 관리자용 4자리 PIN

Node.js·Python·PostgreSQL을 host에 별도로 설치할 필요는 없다. API key, Raw와
DB dump도 최초 공개 실행에 필요하지 않다.

## 최초 실행

저장소 루트에서 다음 파일을 실행한다.

```powershell
.\run_docker.bat
```

첫 실행에서는 4자리 관리자 PIN을 한 번 입력한다. 실행기는 비밀번호·token을
무작위 생성해 Git에서 제외된 `.env.compose`에 저장하며 PIN 평문은 저장하지
않는다. 이어서 다음 순서로 처리한다.

1. Docker engine·Compose·disk·port·기존 Volume 충돌 사전 점검
2. HTTPS latest pointer 다운로드
3. manifest SHA-256과 dataset SHA-256·byte 수 검증
4. immutable local cache 작성
5. Backend·Frontend image build
6. PostgreSQL Migration
7. 컨테이너 안에서 manifest·Schema·Source allowlist·내용 안전성 재검증
8. 공개 dataset 멱등 import
9. PostgreSQL·Redis·Backend·worker·scheduler·Frontend health 대기
10. `http://127.0.0.1:3000` Browser 열기

manifest 전체 검증과 DB import가 성공한 뒤에만 cache의 `latest.pointer.json`을
갱신한다. 다운로드 중단·hash 불일치·Schema drift에서는 기존 latest cache와
Volume을 변경하지 않는다.

## 관리자 PIN 변경과 분실 복구

현재 PIN을 알고 있으면 관리자 로그인 후 `관리자 > 보안`에서 현재 PIN, 새 PIN과
확인을 입력한다. 성공하면 모든 기존 관리자 세션이 무효화되고 로그인 화면으로
이동한다. 정책과 CollectionRun 데이터는 변경하지 않는다.

PIN을 잊었으면 서버 PC의 저장소 루트에서 다음 host-only 복구 도구를 실행한다.

```powershell
.\reset_admin_pin.bat
```

Backend가 실행 중이어야 하며 새 4자리 PIN을 두 번 보안 프롬프트로 입력한다.
도구는 PIN을 명령 인자, shell history 또는 로그에 넣지 않고 실행 중인 Backend
컨테이너의 표준입력으로만 전달한다. DB의 관리자 인증 상태만 transaction으로
갱신하므로 PostgreSQL Volume, 공개 정책, 즐겨찾기 참조와 CollectionRun 감사
기록은 보존된다. 기존 관리자 세션은 모두 무효화된다.

`.env.compose` 삭제나 `docker compose down -v`는 PIN 복구 절차가 아니다.
특히 `down -v`는 PostgreSQL Volume을 삭제하므로 데이터 보존이 필요한 복구에
사용하지 않는다. DB Volume을 새로 만든 경우에는 `.env.compose`의 최초 설치
verifier가 다시 bootstrap 기준이 된다.

## 고정 manifest 개발 검증 경로

검증된 별도 artifact를 가진 개발자는 manifest와 같은 디렉터리에 dataset을 둔
뒤 다음처럼 실행한다.

```powershell
.\run_docker.bat `
  -DatasetManifestPath "C:\verified\public-bootstrap.manifest.json"
```

경로에 있는 파일도 동일한 host hash 검사와 컨테이너 전체 계약 검증을 거친다.
검증을 생략하거나 DB dump로 대체하지 않는다.

## 재실행과 offline cache

두 번째 이후 실행도 같은 명령을 사용한다. 정책 identity upsert가 멱등하므로
변경이 없으면 `unchanged`로 끝나며 기존 PostgreSQL Volume을 재사용한다.

Git pull 또는 새 ZIP으로 소스 코드를 갱신한 뒤에는 기존 컨테이너만 재시작하지
말고 `run_docker.bat`을 다시 실행한다. 실행기가 Backend·Frontend image를 현재
소스로 재빌드하므로 새 API·UI 계약과 실행 이미지가 어긋나지 않는다. 공개
dataset version이 같아도 로컬 dataset 설치 `CollectionRun`은 재실행마다 감사
행이 추가될 수 있다.

네트워크 없이 마지막으로 성공한 dataset을 사용하려면 다음과 같이 실행한다.

```powershell
.\run_docker.bat -Offline
```

기본 cache는
`%LOCALAPPDATA%\cheongnyeon-alimi\public-dataset`에 있다. `-Offline`은 전체
검증과 import까지 성공해 latest로 승인된 cache만 사용하며, cache가 없거나
변조됐으면 실행을 중단한다.

Browser를 자동으로 열지 않으려면 `-NoBrowser`를 추가한다. `.env.compose`에서
host port를 바꿨으면 실행기가 해당 값을 읽는다. 일시적으로 지정하려면
`-FrontendPort`, `-BackendPort`를 사용한다.

port 인자는 해당 실행에만 적용된다. 같은 project를 다시 시작할 때는 최초와
같은 `-FrontendPort`, `-BackendPort`를 다시 전달하거나 `.env.compose`의 host
port를 영구 변경한다. 인자를 생략하면 기본 3000·8000으로 돌아가며 다른
project가 사용 중이면 안전하게 중단한다.

## 상태 확인과 종료

```powershell
docker compose --env-file .env.compose ps
docker compose --env-file .env.compose logs --tail 100 backend collection-worker
docker compose --env-file .env.compose down
```

`down`은 컨테이너와 network를 내리지만 PostgreSQL·Redis·로그 Volume은
보존한다. 실행기는 기존 Volume을 자동 삭제하거나 초기화하지 않는다.

## 실패 시 안전 경계

- `.env.compose` 없이 같은 기본 이름의 DB Volume이 있으면 소유권을 추측하지
  않고 중단한다.
- 다른 프로세스가 port를 쓰면 해당 port가 현재 Compose 서비스의 실제 mapping인지
  확인하고, 아니면 중단한다.
- manifest 또는 dataset hash·크기·Schema·Source 계약이 다르면 DB import 전에
  중단한다.
- 다운로드만 성공하고 전체 검증·import가 실패한 version은 offline latest로
  승격하지 않는다.
- 외부 endpoint 장애 때만 직전 검증 cache로 대체한다. hash 불일치는 cache
  fallback으로 숨기지 않는다.

환경을 강제로 초기화하기 전에 Volume과 `.env.compose`의 소유 관계를 확인한다.
삭제·재생성이 필요한 경우 이 실행기가 자동 판단하지 않는다.
