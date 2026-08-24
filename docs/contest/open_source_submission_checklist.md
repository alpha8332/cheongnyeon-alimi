# 오픈소스 개발대회 제출 준비 체크리스트

## 기준

- 상태: in progress
- 대상 Release: `v1.0.2`
- 목표: 심사자가 README만 읽고 Git clone 또는 GitHub ZIP에서 전체 서비스를
  재현하고, 공개 저장소의 코드·문서·라이선스·데이터 경계를 확인할 수 있게 한다.

## 공개 저장소 정리

- [x] 루트 `.DS_Store` Git 추적 해제와 재유입 차단
- [x] 플랫폼 종속 `venv/` 605개 파일, 7.87 MiB Git 추적 해제
- [x] 참조되지 않는 Vite·React starter image와 social icon sprite 제거
- [x] `.env*`, API key, DB, Raw, Runtime, log, build, coverage, Playwright,
  IDE·OS 메타파일 ignore 경계 정리
- [x] 계획·개발 기록은 로컬 산출물이 아니라 공개 설계·검증 근거로 유지
- [x] 추적 파일의 개인 로컬 절대경로 감사
- [x] 현재 tree와 Git history의 비밀정보 경로·대용량 blob 감사
- [ ] GitHub repository description·topics·social preview·Issue/PR 설정 확인
- [ ] 민감 취약점의 비공개 제보 채널 확정

`.gitignore` 추가만으로 이미 추적 중인 파일이 제거되지는 않는다. 이번 후보에서는
로컬 `venv/` 파일을 삭제하지 않고 Git index에서만 제거했다. 과거 commit의 blob을
제거하는 history rewrite는 별도 파괴적 작업이므로 이번 정리 범위에 포함하지 않는다.
과거 `backend/logs/app.log` 2개와 현재 제거된 API 안내 DOCX에는 credential
assignment, 프로젝트 secret 이름, DB URL, private key 패턴이 모두 0건이었다.
history의 `venv/`와 안내 문서 blob은 남아 있지만 현재 checkout과 source ZIP에는
포함되지 않는다.

## README와 공개 문서

- [x] 프로젝트 목적·핵심 기능·아키텍처를 사용자 관점으로 재작성
- [x] Windows·Docker Desktop 요구사항과 clone·ZIP 경로 명시
- [x] `run_docker.bat` 한 줄 실행, PIN, 성공 marker, URL, 종료·재실행 명시
- [x] API key 불필요 범위와 중앙 dataset 최신화 구조 명시
- [x] 제한사항·문제 해결·보안·코드/데이터 라이선스 경계 명시
- [x] `CONTRIBUTING.md` 추가
- [ ] 최종 UI 대표 화면과 대체 텍스트 확정
- [ ] `v1.0.2` Release와 CHANGELOG 확정

## v1.0.2 사전 clean-room actual

`2026-08-24`에 현재 working tree의 Git 추적 후보만 별도 디렉터리로 복사했다.
이 검증은 commit 전 후보 검증이며 GitHub 원격 clone·ZIP 최종 Gate를 대체하지
않는다.

| 항목 | 실제 결과 |
| --- | --- |
| 격리 후보 | `v1.0.2-candidate-a007bc16` |
| 공개 파일 | 825개, 7,339,371 bytes |
| 제외 확인 | `.git`, `.env.compose`, `venv`, `.venv`, `node_modules`, `dist`, `runtime`, `.DS_Store` 없음 |
| Docker project | `v102-readme-a007bc16` |
| 격리 port | Frontend `13202`, Backend `18202` |
| dataset cache | 후보 전용 빈 디렉터리 |
| 공개 dataset | `public-bootstrap-20260824-f5883bb79c594f`, 457건 |
| 최초 import | `inserted 457`, Migration `20260824_0010` |
| 장기 service | PostgreSQL·Redis·Backend·worker·scheduler·Frontend 기동 |
| 성공 marker | `W6_P3_DATASET_VERIFIED`, `W6_P3_BOOTSTRAP_READY` |
| offline 재실행 | `inserted 0`, `updated 0`, `unchanged 457` |
| 최종 API 대조 | Backend health `ok`, 공개 정책 `total=457` |
| 종료·보존 | running container 0, named Volume 4개 보존 |

실제 Browser에서 다음 흐름을 확인했다.

1. 홈 화면과 주요 내비게이션
2. `서울 주거` 검색 조건 추출과 35건 결과
3. 청년월세 지원사업 상세·공식 원문 링크
4. 새 4자리 PIN 관리자 로그인
5. 관리자 대시보드의 공개 dataset Seed import 성공·삽입 457건

같은 Windows host의 기존 Docker layer cache는 공유했지만 source, env, dataset
cache, project, port, PostgreSQL·Redis·log Volume은 모두 분리했다. 따라서
소스·상태 격리 실행 증거로는 유효하지만 “Docker를 처음 설치한 물리적 새 PC”
검증으로 표기하지 않는다.

## 최종 제출 Gate

- [ ] 후보 commit·PR CI 통과와 `main`·`develop` 동기화
- [ ] 원격 `main`의 fresh clone에서 README 절차 통과
- [ ] 원격 `main` Download ZIP에서 README 절차 통과
- [ ] clone·ZIP 각각 고유 env·cache·Volume에서 457건과 Browser 흐름 대조
- [ ] Docker image/cache가 없는 별도 Windows PC 또는 동등한 신규 환경 검증
- [ ] `v1.0.2` annotated tag·Production Release·source archive 검증
- [ ] 대회 제출 양식·시연 URL·대표 화면·라이선스·SBOM·성과 근거 최종 대조

위 항목이 모두 끝나기 전에는 “README만으로 신규 PC 실행 완료”라고 판정하지
않는다.
