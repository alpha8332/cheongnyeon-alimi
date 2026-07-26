# 역할과 책임

## 1. 목적

이 문서는 프로젝트 영역별 책임과 협업 지점을 정의한다. 담당자 이름을
고정하는 문서가 아니며, 실제 담당자는 Issue와 Pull Request에서 확인한다.

## 2. 데이터 담당

주요 책임:

- 공식 API와 공개 웹사이트 등 데이터 소스 조사
- Collector 공통 인터페이스와 소스별 Collector 구현
- Raw 원문, 출처와 수집 메타데이터 보존
- Extractor, Normalizer와 Validator 구현
- 날짜, 지역, 연령과 카테고리 정규화
- JSON Schema, Fixture와 Seed 작성
- 중복, 수정 감지와 데이터 품질 처리
- 수집 실행 기록과 데이터 출처·라이선스 문서화

데이터 담당은 백엔드와 프론트엔드가 사용할 필드를 단독으로 확정하지 않는다.
Schema, 필수·선택 여부, `null` 규칙과 검색 필터는 공동 검토를 거친다.

## 3. 백엔드 담당

주요 책임:

- FastAPI 애플리케이션과 설정 구조
- PostgreSQL 연결, SQLAlchemy 모델과 Migration
- Repository, Service와 API 계층
- 정책 목록·상세·검색·추천 API
- 인증, 즐겨찾기, 알림과 관리자 API
- 데이터 적재 인터페이스와 트랜잭션
- API 및 통합 테스트
- 운영 로그, 보안과 배포 설정 지원

데이터 계약이 확정되기 전에 정책 필드나 정규화 규칙을 임의로 고정하지
않는다. 초기에는 합의된 Seed 또는 Fixture를 사용해 개발할 수 있다.

## 4. 프론트엔드 담당

주요 책임:

- React와 TypeScript 애플리케이션 기반
- 사용자 검색, 정책 목록·상세와 추천 화면
- 즐겨찾기, 알림과 캘린더 UI
- 관리자 대시보드와 데이터 품질 화면
- API Client와 TypeScript 타입
- 로딩, 빈 결과와 오류 상태
- 접근성, 반응형 동작과 사용자 시나리오 검증

실제 API가 준비되지 않았을 때는 합의된 Mock Data를 사용한다. 데이터 계약이
확정되기 전에 프론트엔드 전용 정책 타입을 임의로 확정하지 않는다.

## 5. 팀장·공통 책임

- Release 범위와 우선순위 관리
- Issue 분해, 의존성 조정과 통합 일정 관리
- 데이터·API·DB 계약의 공동 검토 주관
- PR 리뷰와 병합 기준 확인
- 각 영역 결과가 `develop`에 병합된 뒤 Dockerfile, Compose, 네트워크, Volume과
  health check를 구성하는 통합·배포 작업
- 배포 체크리스트와 시연 시나리오 관리
- README, 라이선스, SBOM, 결과보고서와 제출 자료 확인
- 사용자 시나리오 테스트와 시연 리허설

특정 담당자가 없는 공통 작업은 방치하지 않고 Issue에 책임자와 완료 기준을
명시한다.

## 6. 공동 계약과 통합 지점

다음 항목은 한 담당자가 단독으로 확정하지 않는다.

- 정규화 정책 Schema와 필드 이름
- 필수·선택 여부, `null`, 빈 배열과 enum 규칙
- 최소 DB 테이블과 데이터 적재 경계
- API 요청·응답 구조와 검색 필터
- Fixture와 Seed의 대표 사례
- 인증, 개인정보, 데이터 출처와 라이선스 정책

초기 통합 흐름은 다음과 같다.

```text
데이터 담당의 Fixture 또는 DB 데이터
→ 백엔드 정책 조회 API
→ 프론트엔드 API 연결
```

Collector가 늦어지더라도 합의된 Seed로 백엔드와 프론트엔드 개발을 진행할 수
있다. 계약 변경은 영향받는 담당자와 공동 검토하고 관련 문서를 함께
갱신한다.

## 7. 의존성과 컨테이너 책임

각 담당 영역은 통합 환경에서 같은 결과를 재현할 수 있도록 코드와 함께 실제
사용한 의존성 정보를 제공한다.

### Frontend

- `frontend/package.json`과 팀에서 선택한 하나의 lockfile을 함께 관리한다.
- 라이브러리를 추가·제거·갱신하면 manifest와 lockfile을 같은 작업에서
  갱신하고 고정된 의존성으로 실행 및 테스트한다.
- 필요한 환경변수 예시와 로컬 실행·테스트 명령을 제공한다.

### Backend

- 합의한 Python 도구에 따라 `backend/pyproject.toml`과 lockfile 또는
  `backend/requirements.txt`와 `backend/requirements-dev.txt`를 관리한다.
- 두 방식을 임의로 혼용하지 않고, 라이브러리 변경과 의존성 파일을 같은
  작업에서 갱신한다.
- 필요한 환경변수 예시와 로컬 실행·테스트 명령을 제공한다.

### Data

- Data 코드가 Backend 실행 환경을 공유하면 새 Python 라이브러리를 Backend의
  합의된 의존성 파일에 반영한다.
- 별도 Python 패키지나 실행 환경은 관련 Forest 또는 ADR에서 경계가 확정된
  경우에만 독립 manifest를 만든다.
- 데이터 담당이 다른 영역의 패키지 관리 방식이나 컨테이너 경계를 임의로
  변경하지 않는다.

### Integration·Deploy

- Frontend, Backend와 Data 담당자는 관련 Forest에 명시되지 않은 Dockerfile,
  Compose 또는 배포 구성을 의무적으로 만들지 않는다.
- 각 영역 결과가 `develop`에 병합되고 manifest·lockfile과 실행 방법이 준비된
  뒤 통합·배포 담당이 Dockerfile과 Compose를 작성한다.
- 통합 단계에서 Frontend, Backend와 Database 컨테이너의 빌드, 네트워크,
  환경변수, Volume, health check와 전체 실행을 검증한다.
- 실제 라이브러리 목록과 버전을 통합 담당자가 추측하거나 수동으로 다시
  작성하지 않고 각 영역의 manifest와 lockfile을 설치 기준으로 사용한다.

현재 Forest가 컨테이너 통합을 범위에 포함하지 않으면 컨테이너 작업을
추가하지 않는다. 컨테이너 변경이 선행돼야만 구현 가능한 문제가 발견되면
임의로 확장하지 않고 통합·배포 담당에게 필요한 변경을 알린다.

## 8. 역할별 문서화 책임

담당자는 자신의 구현 기록뿐 아니라 작업이 변경한 공통 계약도 함께
갱신한다.

| 작업 책임 | 계획·개발 기록 | 함께 확인할 기준 문서 |
| --- | --- | --- |
| Data | `develop_plan/data/`, `development_notes/data/` | `docs/data/`, 영향받는 `docs/api/` |
| Backend | `develop_plan/backend/`, `development_notes/backend/` | `docs/api/`, DB·아키텍처·운영 문서 |
| Frontend | `develop_plan/frontend/`, `development_notes/frontend/` | API 사용 계약, 화면 흐름·접근성 문서 |
| 공동 통합 | `develop_plan/integration/`, `development_notes/integration/` | 영향받는 모든 공통 계약 |

실제로 해결한 장애는 같은 책임 영역의 `docs/troubleshooting/` 하위 문서에
기록한다. 담당자가 누구인지가 아니라 변경 또는 문제의 책임 영역을 기준으로
분류한다.

## 9. 실제 담당 확인

역할 배정은 계획 문서보다 현재 Issue, Pull Request, CODEOWNERS와 저장소
설정을 우선하여 확인한다. 이 문서와 실제 배정이 다르면 임의로 책임을
변경하지 않고 차이를 알린 뒤 합의된 변경을 반영한다.

브랜치와 리뷰 절차는 [브랜치 전략](branch_strategy.md)과
[코드 리뷰 정책](code_review.md)을 따른다.
