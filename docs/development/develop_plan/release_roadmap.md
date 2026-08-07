# Release와 Milestone 계획

## 문서 정보

- 상태: approved
- 기준일: 2026-08-07
- 범위: `v0.1.0`, `v0.5.0`, `v1.0.0`
- 역할: 여러 Forest의 릴리스 목표와 통합 완료 조건을 정하는 기준선

이 문서는 개별 Forest 계획을 대신하지 않는다. 실제 구현 전에
[Forest 로드맵](forest_roadmap.md)에서 담당 Forest와 선행 관계를 확인하고,
각 Forest 계획에 Slice와 검증 명령을 확정한다.

## 계획 해석 원칙

`opensource_plan`의 초기 계획은 방향을 정하는 읽기 전용 참고 자료다. 현재
코드, 자동화된 계약, 실행 결과와 `docs/`가 초기 계획과 다르면 현재 저장소를
우선한다. 구현하지 않았거나 실제 데이터로 검증하지 않은 항목은 릴리스 완료로
간주하지 않는다.

정책 검색 요청은 PostgreSQL만 조회한다. 온통청년·복지로 API 호출은 별도
수집·적재 흐름에서 수행하며 사용자 검색 요청마다 외부 API를 호출하지 않는다.

## 현재 기준선

2주차 기반과 3주차 Release 1 구현까지 다음이 완료됐다.

- 온통청년·복지로 제한 수집, Raw 저장, 정규화와 검증
- 합성 canonical Seed의 PostgreSQL 적재와 Policy API 통합
- Runtime Raw 재처리 CLI와 최소 `collection_runs` 실행 이력
- React 사용자 정책 목록·상세·필터 UI와 실제 Policy API 연결
- PostgreSQL 안전성 보강과 React Router advisory 대응
- `NormalizedProgram` 1.1.0, `kr-bjd-20260803` 행정구역 기준정보와
  Source 중립 지역 관계·검색 projection·3값 판정 primitive
- 실제 정책 3,156건 snapshot의 PostgreSQL bootstrap과 멱등 재실행
- Backend 자연어 해석·서버 검색, 검색 이유·미확인 조건 API
- Frontend 자연어 검색·pagination·목록·상세와 actual API Browser E2E
- 신청 가능한 golden 정책의 identity·순위·unknown·응답시간·신청기간 안전성
- Gate G4 경량 QA·사용성 검토와 Release 1 blocker 0건 판정

Release 1 구현과 근거는 `2026-08-06` 커밋 `4629a61`로 `develop`에 병합됐다.
PR #15의 `main` 커밋 `2b33ed7`에 `v0.1.0` tag를 생성해 publication을
완료했고 `develop`도 같은 커밋으로 fast-forward했다. 자동 주기 수집,
보고서 근거 대조와 API 오류 토스트 검증은 `v0.5.0` 후속 범위다.

## 릴리스 역할과 승인 증거

| 역할 | `v0.1.0` | `v0.5.0` | `v1.0.0` |
| --- | --- | --- | --- |
| Data | 실제 정책 bootstrap·품질 기준 | 반복 수집·중복·품질 운영 | 초기 적재·복구·Source 라이선스 |
| Backend | 자연어 해석·서버 검색 API | 추천·사용자·관리자 API 안정화 | Production image·migration·health·로그 |
| Frontend | 자연어 전달·해석 결과·실데이터 UI | 전체 사용자·관리자 UI·접근성 | Production build·배포 UI 회귀 |
| Team Leader - Integration·Deploy | 실제 데이터 E2E와 Release 1 결정 | 통합·결함 triage와 Release 2 결정 | 배포 파이프라인·clean-room과 Final 결정 |
| 보고서 | 데이터·검색·검증 근거 | 기능·리뷰·QA·수정 결과 | 최종보고서·README·LICENSE·SBOM·제출 |
| 사용성 리뷰어 | golden query 이해도 사전 확인 | 독립 사용자 시나리오와 수정본 확인 | 새 환경 실행 안내·최종 사용성 확인 |
| QA | 핵심 검색 smoke | 전체 기능·통합·회귀·탐색 테스트 | 설치·배포·재시작·데이터 유지·복구 테스트 |

역할이 늘어난다고 반드시 별도 인원이 늘어나는 것은 아니다. 겸임할 수 있지만
PR 승인, 사용성 리뷰, QA 통과와 팀장의 릴리스 결정은 서로 다른 증거로 남긴다.

## Release 1 - 실제 정책 검색 MVP

### 버전

`v0.1.0`

### 현재 판정

`2026-08-06` Gate G4는 `pass`다. 새 contract hash의 actual 기술 재검증에서
golden 자연어·control은 모두 1건 중 1위·unknown 0이며 95.95ms·78.68ms로
기술 기준을 통과했다. Source 신청기간 안전성, Frontend actual API
E2E·Browser와 경량 QA·사용성 리뷰도 통과했고 evidence verifier blocker는
0건이다. 보고서와 API 오류 토스트 검증은 `v0.5.0`으로 이관했다. 상세 근거는
[Release 1 Acceptance 개발 기록](../development_notes/integration/release_1_acceptance.md)을
따른다.

### 목표

실제로 진행 중인 정책 데이터가 PostgreSQL에 적재돼 있고, 사용자가 일반적인
한국어 문장이나 명시적 조건으로 검색하면 현재 신청 가능한 관련 정책을
목록과 상세 화면에서 확인할 수 있다.

### 필수 범위

#### 실데이터 기준선

- 온통청년과 복지로 중앙부처 복지서비스의 릴리스 수집 범위를 문서로 고정한다.
- 페이지 순회, 중단·재시도, 중복 방지와 upsert를 포함한 초기 적재 절차를
  제공한다.
- 정책별 출처, 수집 시각, 신청 기간과 품질 상태를 보존한다.
- 릴리스 시점 DB에는 합성 Seed가 아닌 실제 정책 snapshot이 존재해야 한다.
- 실제 데이터에서 `valid`, `partial`, `invalid`, 누락과 중복 건수를 확인하고
  사용자 노출 규칙을 검증한다.
- 갱신은 검색 요청과 분리한다. `v0.1.0`은 문서화된 수동 갱신을 허용하지만
  검색 시점 외부 API 호출은 허용하지 않는다.

#### 검색 계약

- [Policy Search Data Foundation](integration/03_policy_search_data_foundation.md)에서
  완료한 Source 중립 검색 필드, `nationwide|regional|unknown`, versioned
  행정구역 계층·정책 관계와 Korean search projection을 Backend·Frontend
  검색 계약의 기준선으로 사용한다.
- 현재 목록·상세의 source-scoped identity와 provenance는 유지하고,
  지역·검색 내부 구조는 향후 지자체 Source가 같은 Adapter 계약을 사용할 수
  있게 공개 DTO와 분리한다.
- Frontend는 사용자의 자연어 원문을 `q`로 전달하고 Backend를 검색 해석의
  단일 기준으로 사용한다. Frontend가 별도의 자연어 parser를 갖지 않는다.
- Backend는 결정적인 한국어 규칙으로 `q`에서 `keyword`, 지역, 연령,
  카테고리와 신청 상태를 구조화하고 PostgreSQL 검색과 pagination을 처리한다.
- Backend는 구조화된 해석 조건, 관련도순 결과, 각 결과의 검색 이유와
  소득·거주·무주택 여부처럼 데이터만으로 판정하지 못한 조건을 함께 반환한다.
- 지역은 시·도와 시·군·구 표현을 표준 지역 값으로 해석하고, 전국 정책의
  포함 규칙을 명시한다. 지역이 없는 정책은 자동으로 전국 처리하지 않고
  `unknown` 판정과 사용자 미확인 조건을 제공한다.
- 연령은 `age_min`·`age_max`와 비교하며 조건 미상 정책의 포함 여부를
  계약으로 정한다.
- 기본 사용자 검색은 신청 가능 정책을 우선하고 마감·예정 정책의 표시 규칙을
  구분한다.
- 자연어 입력은 Backend의 결정적인 한국어 조건 추출로 처리한다.
  LLM·벡터 검색은 `v0.1.0`의 필수 조건이 아니다.
- Frontend는 목록 100건 전체를 받은 뒤 로컬에서만 검색하지 않고 Backend
  해석·검색·pagination 결과를 사용한다. 해석된 조건을 표시하고 사용자가
  수정한 조건은 승인된 API 계약으로 다시 요청한다.
- 결과가 없으면 조건과 이유를 보여주며 존재하지 않는 정책을 생성하거나
  적용 가능성을 단정하지 않는다.

#### 통합과 사용자 화면

- 홈 검색 → 검색 결과 → 정책 상세 흐름이 실제 DB와 API를 사용한다.
- loading, 빈 결과, 404, 422, 500과 partial 표시가 유지된다.
- 출처 링크, 수집 시각, 신청 기간과 주요 자격 조건을 사용자가 확인할 수 있다.
- 실제 데이터 양을 기준으로 pagination, 응답 시간과 기본 인덱스를 검토한다.

### 대표 인수 시나리오

다음 문장은 `v0.1.0`의 필수 golden query다.

```text
천안 사는 27살 청년 단기숙소 지원 받을 수 있나?
```

릴리스 후보 데이터 snapshot에서 이 문장은 `천안`, `27세`, 주거·단기숙소
의미와 신청 가능 상태를 반영해야 한다. 기대 정책은 온통청년
`20260430005400212969`의 `청년단기숙소 지원사업`이며 결과 20위 이내,
unknown 0, 응답 2초 이내여야 한다. `단기숙소`와 천안·27세를 명시한
control은 1위·1초 이내를 유지한다.

snapshot, 기대 identity와 자동 기준은 `data/release_1_acceptance.json`에
고정한다. 후보가 확인되더라도 실제 자격을 단정하지 않는다. `v0.1.0` 수동
Gate는 경량 QA·사용성 리뷰를 요구하고 역할 독립·보고서 대조·API 오류 UX는
`v0.5.0`으로 이관한다.

### 릴리스 완료 조건

- 정의된 릴리스 수집 범위의 실제 데이터 초기 적재와 재실행이 성공한다.
- Source 중립 검색 필드, 행정구역 계층·정책 관계와 search projection
  Migration이 빈 DB와 기존 데이터 DB에서 검증된다.
- DB를 새로 준비한 뒤 문서화된 절차로 같은 실데이터 기준선을 만들 수 있다.
- golden query를 포함한 지역·연령·카테고리·마감 상태 검색 인수 테스트가
  통과한다.
- 실제 DB → FastAPI → React UI의 목록·상세를 Browser에서 확인한다.
- 관련 Data, Backend, Frontend 단위·통합 테스트와 문서 검증이 통과한다.
- 보안키, 실제 Raw와 DB 파일이 Git 추적 대상에 포함되지 않는다.
- 미완료 자동 Scheduler나 배포 구성을 완료로 안내하지 않는다.

### 제외 범위

- 개인화 추천 점수와 추천 이유
- 즐겨찾기, 알림과 캘린더
- 완성형 관리자 대시보드
- LLM·벡터 검색을 필수 검색 경로로 사용
- Production Docker·Nginx·CI/CD 배포 파이프라인

## Release 2 - 전체 기능 완성과 사용자 검증

### 버전

`v0.5.0`

### 목표

사용자 기능과 관리자 기능을 모두 연결하고, 팀 외 리뷰어가 실제 시스템을
사용한 결과를 반영해 시연 가능한 서비스 수준으로 안정화한다.

4주차 구현 전 계약은
[Integration 05 v0.5.0 Contract Baseline](integration/05_v0_5_0_contract_baseline.md),
기능 연결과 최종 Gate는
[Integration 07 Release 2 Feature Acceptance](integration/07_release_2_feature_acceptance.md)를
따른다.

### 필수 범위

- 사용자 조건 기반 추천과 이해 가능한 추천 이유
- 공공 API를 보강하는 승인 공식 HTTPS Source 한 곳의 제한 수집·DB 적재
- 정책 상세의 근거 있는 핵심 신청 조건·제외 조건·필요 서류·확인 필요 표시
- 즐겨찾기, D-Day, 웹 내부 알림과 `.ics` 캘린더 등록
- 사용자 조건 입력·저장 방식과 필요한 인증 경계 확정
- 관리자 인증·권한
- 수집 실행 이력, 수동 실행, stale 실행 판정과 오류 표시
- 관리자 읽기 전용 정책 데이터 표·row 상세·pagination·filter
- 구조화된 영속 파일 로그, 단계·request·run correlation과 관리자 조회 UI
- 회전 archive 로그의 보호된 삭제와 별도 감사 기록
- 파싱 실패, partial·invalid, 중복 후보와 데이터 품질 확인 UI
- 실데이터 갱신 절차, 실패 복구와 데이터 유지 검증
- 검색·추천 정확도, DB migration, transaction과 주요 API 안정화
- 접근성, 반응형, 빈 화면·오류 화면과 핵심 사용자 흐름 개선

웹 수집은 임의 사이트 범용 크롤러가 아니라 승인된 공식 Source 한 곳을
기준선으로 한다. 자격요건 화면은 Source 근거가 있는 조건을 요약하되 데이터가
부분적이면 `추가 확인 필요`로 표시하고 수혜·선정 가능성을 확정하지 않는다.

이 릴리스에서 “모든 기능 완성”은 이메일 발송이나 Google Calendar 직접
연동 같은 확장 기능까지 의미하지 않는다. 웹 내부 알림과 `.ics`를 기준으로
완료하고, 외부 연동은 별도 합의가 있을 때만 추가한다.

### 리뷰어 검증

팀원이 아닌 리뷰어가 최소한 다음 흐름을 수행한다.

1. 조건 또는 자연어로 정책 검색
2. 상세의 핵심 신청 조건·제외·서류·확인 필요와 공식 근거 확인
3. 결과와 상세의 자격·신청 정보 확인
4. 추천 이유 확인
5. 즐겨찾기와 D-Day·알림 확인
6. 캘린더 파일 등록
7. 관리자로 적재 정책 데이터를 표·상세로 확인
8. 관리자로 수집 이력·실패·품질 상태 확인과 수동 실행
9. 오류 로그를 run·request·단계로 찾고 회전 archive 삭제 확인

혼란, 기대와 다른 결과, 빈 화면, 오류와 접근성 문제를 기록한다. 심각도와
재현 조건을 분류하고, 릴리스 범위로 승인한 문제를 수정한 뒤 같은 시나리오를
재검증한다.

### 릴리스 완료 조건

- 승인된 사용자·관리자 기능이 실제 API와 DB로 동작한다.
- 승인 웹 Source의 제한 actual 수집과 조건 요약 lineage가 검증됐다.
- 관리자 정책 데이터 표와 파일 로그·조회·보호된 삭제가 실제 환경에서
  검증됐다.
- 주요 데이터 오류, migration과 transaction 문제가 해결됐다.
- 리뷰어 시나리오를 통과하고 승인된 피드백이 반영됐다.
- QA가 전체 기능·통합·회귀 테스트를 수행하고 릴리스 차단 결함의 수정본을
  재검증했다.
- 핵심 단위·통합·Browser 테스트와 문서 검증이 통과한다.
- 알려진 제약과 미해결 낮은 위험 문제가 릴리스 노트에 기록됐다.

## Final Release - 재현 가능한 오픈소스 배포

### 버전

`v1.0.0`

### 목표

새 환경의 사용자가 저장소를 받아 문서만 보고 시스템을 실행하고, 실제
데이터를 적재해 사용자·관리자 시나리오를 재현할 수 있는 오픈소스 배포본을
완성한다.

### 필수 범위

- Frontend·Backend Production Dockerfile과 PostgreSQL을 포함한 Compose
- Nginx 정적 파일 제공과 `/api` reverse proxy
- 환경변수와 비밀 분리, Volume, health check와 데이터 유지
- Migration, 초기 실데이터 bootstrap 또는 명시적 수집 절차
- Frontend build, Backend·Data 테스트, 이미지 build를 수행하는 CI
- 버전·이미지 tag와 릴리스 체크리스트
- 새 PC 또는 깨끗한 환경의 clone-to-run 검증
- 설치, 수집, 검색, 사용자·관리자 기능, 로그와 복구 안내
- README, 아키텍처, 데이터 Schema, API, Collector 가이드
- LICENSE, SBOM, CHANGELOG, 최종보고서, 시연 스크립트와 제출 자료

### 릴리스 완료 조건

- 깨끗한 환경에서 README만 따라 build·migration·초기 적재·실행이 성공한다.
- 컨테이너 재시작 후 DB와 필요한 Runtime 데이터가 유지된다.
- 사용자 검색·추천·부가 기능과 관리자 시나리오가 배포 구성에서 통과한다.
- QA가 clean-room 설치, 배포, 재시작, 로그와 복구 시나리오를 재검증했다.
- CI와 릴리스 문서가 실제 명령 및 산출물과 일치한다.
- `main`의 릴리스 커밋에 `v1.0.0` 태그를 만들 준비가 끝난다.

## 원안에서 변경한 핵심 결정

| 초기 계획 | 현재 계획 | 변경 이유 |
| --- | --- | --- |
| `v0.1.0`에서 실제 또는 sample 데이터 허용 | 실제 진행 중 정책 snapshot 필수 | 합성 Seed만으로는 실제 검색 MVP를 증명할 수 없음 |
| 검색이 keyword·기본 필터 중심 | Backend 자연어 해석과 서버 검색을 `v0.1.0` 필수로 포함 | 해석 기준을 한곳에 두고 현재 사용자 기대 시나리오를 client-only 문자열 검색 없이 만족해야 함 |
| `v0.1.0`에 Docker Compose 포함 | Production 배포 파이프라인은 `v1.0.0`으로 이동 | 사용자가 정한 Final Release 목표와 현재 컨테이너 아키텍처 시점을 반영 |
| 3주차와 병행해 관리자 기능 진행 | `v0.1.0` 실데이터·검색 차단 조건을 먼저 처리 | 관리자 기능보다 Release 1의 검색 결과 신뢰성이 선행함 |
| LLM·벡터 검색을 후속 실험으로 검토 | 그대로 유지 | 기본 SQL·조건 검색을 먼저 완성하고 복잡도를 검증 후 추가 |

## 관련 문서

- [Forest 로드맵](forest_roadmap.md)
- [주차별 실행 계획](weekly_delivery_plan.md)
- [3주차 상세 실행 계획](../weekly_plan/week_03_release_1.md)
- [검색 계약 Gate G1 인수인계](../weekly_plan/week_03_search_contract_handoff.md)
- [시스템 흐름](../../architecture/system_flow.md)
- [컨테이너 구조](../../architecture/container_structure.md)
- [Policy API 계약](../../api/policies.md)
- [Collector 실행](../../operations/collector.md)
- [역할과 책임](../../governance/role_assignment.md)
