# 오픈소스 개발대회 제출 준비 체크리스트

## 기준

- 상태: QA 브랜치 actual 통과, 현재 HEAD 원격 clone·ZIP Final Gate 대기
- 대상 Release: `v1.0.2`
- 현재 작업 브랜치: `fix/qa/v1.0.2-v1`
- 현재 검증 SHA: `03eb506176ff6b081febdbcee013eece3fcc28e9`
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
- [x] v1.0.2 지역 검색·dataset 동등성·정렬·복수 분야·프로필 추천 개선 기록
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

## v1.0.2 원격 브랜치 clean-room actual

`2026-08-24`에 `feature/release/v1.0.2-submission-readiness`를 GitHub에 push한
뒤 commit `92f52fe55407103b1f87e16dcdeb77ec9e6efc9c`를 clone과 Download ZIP으로
각각 다시 받았다. 두 경로 모두 기존 후보 디렉터리와 다른 source, env, dataset
cache, Compose project, port, PostgreSQL·Redis·log Volume을 사용했다.

| 항목 | GitHub clone | GitHub Download ZIP |
| --- | --- | --- |
| source 기준 | 원격 HEAD와 local HEAD가 `92f52fe55407`로 일치 | README Git blob `9c48d070c3aa638a6c103559669315dcd7ee4e90` 일치 |
| 공개 파일·금지 파일 | `.env.compose`, `venv`, `.venv`, `node_modules`, `dist`, `runtime`, `.DS_Store` 없음 | 823개 파일, clone과 같은 금지 파일 없음 |
| Docker project | `v102clone92f52fe` | `v102zip92f52fe` |
| 격리 port | Frontend `13212`, Backend `18212` | Frontend `13213`, Backend `18213` |
| 공개 dataset | `public-bootstrap-20260824-f5883bb79c594f`, SHA-256 `6457a37f...ed1f9`, 457건 | 동일 version·hash·457건 |
| 최초 실행 | dataset 검증·Migration·bootstrap·6개 장기 service health 통과 | dataset 검증·Migration·bootstrap·6개 장기 service health 통과 |
| 실제 Browser | 홈, `서울 주거` 35건, 청년월세 상세·복지로 원문, PIN 로그인, 관리자 삽입 457건 | 홈, `서울 주거` 35건, PIN 로그인, 관리자 삽입 457건 |
| offline 재실행 | `inserted 0`, `updated 0`, `unchanged 457`, Backend health `ok` | `inserted 0`, `updated 0`, `unchanged 457`, Backend health `ok` |
| 종료·보존 | running container 0, named Volume 4개 보존 | running container 0, named Volume 4개 보존 |

Download ZIP 자체의 SHA-256은
`bbd7918f4f28b7b3ed8cf8fc71c43abdb7069b16fd9b01126099f09163b1868b`였다.
Windows clone의 README는 checkout 과정에서 LF가 CRLF로 변환되어 일반 파일
hash가 달랐지만, 줄바꿈 정규화 내용과 GitHub ZIP의 Git blob ID는 원격 commit과
일치했다.

## v1.0.2 QA 안정화 후 현재 후보

앞의 457건 clean-room은 당시 원격 commit `92f52fe`의 역사적 실행 증거다. 이후
작성자 DB와 심사자 DB의 사용자 결과 차이, 지역 정책 누락과 검색·추천 UX를
수정했으므로 현재 HEAD의 Final Gate를 대신하지 않는다.

`2026-08-25`에 `fix/qa/v1.0.2-v1`의 `03eb506`을 push하고 현재 source에서
`run_docker.bat -NoBrowser`를 재실행했다.

| 항목 | 실제 결과 |
| --- | --- |
| 원격 동기화 | local·`origin/fix/qa/v1.0.2-v1` SHA `03eb506` 일치 |
| 공개 dataset | `public-bootstrap-20260824-897152e7a18c15`, 2,052건 |
| Source 구성 | 복지로 461, 온통청년 1,587, 인천 공공데이터 4 |
| 활성 identity SHA-256 | `9f65f2b1dae66b7f07b61310f5f3d07c024e0ab9e86eee843387f06d04afd0e5` |
| Docker | Backend·Frontend image 재빌드, 장기 서비스 6개 healthy |
| 정책 API | 주거 목록 213건·자연어 검색 123건, category 불일치 0 |
| 추천 API | 주거 추천 135건, 첫 20건 category 불일치 0 |
| 실제 Browser | 복수 분야 카드·상세, 390×844 overflow 없음 |
| Backend 관련 회귀 | `19 passed` |
| 검색 actual E2E | `12 passed, 2 skipped` |
| 추천 actual E2E | `9 passed, 4 skipped` |

세부 변경과 커밋·검증은
[v1.0.2 QA 개선 기록](../troubleshooting/integration/v1_0_2_qa_improvements.md)에
고정했다. `CollectionRun`은 로컬 실행 감사이므로 환경별 건수는 비교하지 않고,
활성 dataset row 수와 identity hash를 사용자 결과 동등성 기준으로 사용한다.

## 최종 제출 Gate

- [ ] 후보 commit·PR CI 통과와 `main`·`develop` 동기화
- [ ] 원격 `main`의 fresh clone에서 README 절차 통과
- [ ] 원격 `main` Download ZIP에서 README 절차 통과
- [x] 이전 원격 후보 `92f52fe` clone·ZIP 각각 고유 env·cache·Volume에서 457건과 Browser 흐름 대조
- [ ] 현재 QA HEAD `03eb506` fresh clone에서 2,052건·identity hash·Browser 흐름 대조
- [ ] 현재 QA HEAD `03eb506` Download ZIP에서 2,052건·identity hash·Browser 흐름 대조
- [ ] Docker image/cache가 없는 별도 Windows PC 또는 동등한 신규 환경 검증
- [ ] `v1.0.2` annotated tag·Production Release·source archive 검증
- [ ] 대회 제출 양식·시연 URL·대표 화면·라이선스·SBOM·성과 근거 최종 대조

위 항목이 모두 끝나기 전에는 “README만으로 신규 PC 실행 완료”라고 판정하지
않는다.
