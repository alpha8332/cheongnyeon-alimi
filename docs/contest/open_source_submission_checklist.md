# 오픈소스 개발대회 최종 제출 체크리스트

## 현재 기준

- 공개 Release: `v1.1.0`
- Release Git SHA: annotated `v1.1.0` tag가 가리키는 commit
- 공개 dataset: `public-bootstrap-20260825-38180bc7a837ef`
- 공개 정책: 2,051건
- Source 구성: 복지로 461건, 온통청년 1,586건, 인천 공공데이터 4건
- 활성 identity SHA-256:
  `85b70773cb64c7f97e2ffb7270be4dd68c892c23624f807a971b1585b808d76e`

이 값은 `2026-08-26`의 `v1.1.0` 검증 기준이다. 제출 직전에
`dataset-latest`가 새 version을 가리키면 함께 받은 manifest의 version, row
count와 hash를 우선한다.

## 공개 저장소

- [x] MIT `LICENSE` 포함
- [x] README에 Windows·Docker 요구사항과 clone·ZIP 실행 절차 명시
- [x] `run_docker.bat` 한 줄 실행과 종료·재실행 방법 명시
- [x] API key 없이 공개 dataset을 설치하는 경계 명시
- [x] `.env*`, API key, PIN, DB, Raw, Runtime, log와 build 산출물 ignore
- [x] `CONTRIBUTING.md`, 보안·브랜치·리뷰·커밋 규칙 제공
- [x] `SECURITY.md`에 비공개 취약점 제보와 비밀정보 제외 절차 명시
- [x] 완료된 계획·주차 문서와 초기 릴리스 증거를 제출본에서 정리
- [x] 제품·아키텍처·API·데이터·운영 문서를 현재 구현 기준으로 연결
- [ ] GitHub description과 topics 확인
- [ ] GitHub 비공개 취약점 제보 기능 확인
- [ ] GitHub social preview 확인

## 설치와 데이터 동등성

- [x] 깨끗한 Docker Volume에서 API key 없이 2,051건 설치
- [x] manifest·artifact hash와 row count 검증
- [x] 작성자 DB의 기존 로컬 정책과 분리된 활성 dataset projection 검증
- [x] 양산·경남·인천·부산·제주 등 다중 지역 검색 검증
- [x] 검색·추천·상세 API가 활성 dataset membership만 공개하는지 검증
- [x] CollectionRun 수가 환경마다 달라도 공개 identity hash가 같은지 확인
- [ ] 최종 제출 Git SHA의 GitHub fresh clone에서 README 전체 절차 재검증
- [ ] 최종 제출 Git SHA의 Download ZIP에서 README 전체 절차 재검증
- [ ] 별도 물리 PC 또는 동등한 신규 환경 결과 수령·기록

## 기능 QA

- [x] 홈 예시 검색과 자연어 검색
- [x] 지역·연령·복수 관심 분야·상태 필터, 정렬과 페이지 이동
- [x] 정책 상세, 신청 조건, 미확정 정보와 공식 원문
- [x] 프로필 저장, 복수 관심 분야, 추천 순위와 추천 이유
- [x] 즐겨찾기, D-Day, 달력, 내부 알림과 `.ics`
- [x] 관리자 PIN, 보호 route, 만료, 로그아웃과 PIN 변경
- [x] 관리자 대시보드, 수집기 상태, CollectionRun, 정책·품질·로그 조회
- [x] 390×844 모바일, 키보드 focus와 주요 ARIA label
- [ ] 최종 제출 Git SHA 병합 후 전체 회귀 CI와 핵심 Browser smoke 재실행

## 데이터·보안·라이선스

- [x] 공개 dataset은 허용된 source와 최소 정책 사실만 포함
- [x] Raw HTML·원본 API payload·개인정보·비밀 query를 Release에서 제외
- [x] PIN 평문을 저장하지 않고 관리자 token을 브라우저 메모리에만 유지
- [x] 관리자 로그·정책 API가 allowlist 필드만 반환
- [x] image SBOM·provenance와 digest-qualified release receipt 생성
- [ ] 최종 제출 양식의 라이선스·데이터 출처·성과 수치를 현재 manifest와 대조

## 최종 제출 직전 기록할 값

| 항목 | 값 |
| --- | --- |
| 제출 브랜치·Git SHA | 최종 병합 후 기록 |
| CI run | 최종 병합 후 기록 |
| 공개 dataset version·row count | latest manifest에서 기록 |
| identity SHA-256 | clean-room DB에서 기록 |
| clone 검증 환경·결과 | 최종 실행 후 기록 |
| ZIP 검증 환경·결과 | 최종 실행 후 기록 |
| 별도 PC 검증 결과 | 결과 수령 후 기록 |

체크되지 않은 외부 검증을 추정으로 완료 처리하지 않는다. 최종 SHA가 바뀌면
문서만 검토하지 않고 설치·검색·관리자 핵심 흐름을 다시 실행한다.
