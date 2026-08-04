# 3주차 검색 계약 Gate G1 인수인계

## 문서 정보

- 상태: action-needed
- 담당 Gate: DT2·Gate G1
- 조정 담당: Data·Team Leader
- 다음 담당: Backend 06·Frontend 04
- 공통 시작 기준: 이 인수인계 문서를 마지막으로 변경한 커밋
- 작업 저장소: `C:\git\cheongnyeon-alimi`
- 완료 조건: Backend·Frontend 계약 초안과 Data 권고안을 공동 검토해 Gate G1
  승인 또는 수정사항을 기록함

이 문서는 Backend 06과 Frontend 04 담당자가 같은 검색 데이터 기준선에서
계획과 계약 초안을 작성하도록 돕는 실행 인수인계다. Release·Forest 범위는
[Release 로드맵](../develop_plan/release_roadmap.md),
[Forest 로드맵](../develop_plan/forest_roadmap.md)과 각 담당 Forest 계획이
권위 자료다. 이 문서와 현재 코드·실행 결과가 다르면 임의로 맞추지 말고
Data·Team Leader에게 차이와 선택지를 알린다.

이번 인수인계의 산출물은 **각 담당 Forest 계획 초안과 Gate G1 공동
계약 검토안**이다. Backend API·Repository, Frontend UI·API Client와
테스트 코드를 구현하는 작업은 범위에 포함하지 않는다. Gate G1 승인 뒤
각 담당자가 별도 Forest의 Slice 계획에 따라 본 구현을 시작한다.

## 현재 완료 기준선

- Data 02 DT0~DT1: 환경, 실제 Source preflight와 대표 Raw 확보 완료
- Integration 03 PSF0~PSF8: Source 중립 검색 데이터 기반 완료·병합
- DT2 Data 작업: PSF 이후 actual profile, Data 권고안과 Schema 영향 판정 완료
- Backend 06: W3-B0 계획·API 초안 병합 완료
- Frontend 04: W3-F0 계획·draft type·표시 초안 병합 완료
- Gate G1: DT2A 정합성·DT2B 결정 동결 완료, DT2C~DT2D 검증·승인 대기

현재 실제 표본의 PSF 이후 오프라인 재생 결과는 다음과 같다.

| Source | valid | partial | invalid | 지역 | 연령 | 신청 상태 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| 온통청년 10건 | 8 | 2 | 0 | regional·rule 10건 | 숫자 범위 9건 | open 6·closed 3·scheduled 1 |
| 복지로 10건 | 0 | 10 | 0 | unknown 10건 | unknown 10건 | unknown 10건 |

Raw payload, API 키와 DB credential은 담당자에게 전달하지 않는다. 필요한
경계 사례와 집계는
[Data 02 개발 기록](../development_notes/data/release_dataset_bootstrap.md)을
사용한다.

## DT2 종료 Slice

Backend·Frontend 담당자가 제출하지 못한 공동 계약 마감은 Data·Team Leader가
현재 Data 브랜치에서 다음 순서로 수행한다. 이 작업은 G1 전 계획·draft 계약
보완이며 각 영역의 본 구현을 대신하지 않는다.

| 순서 | Slice | 핵심 작업 | 완료 증거 |
| ---: | --- | --- | --- |
| 1 | DT2A 계약 정합성 보완 | Backend import·null status·경고 위치, Frontend `unknown_count`·Slice 참조 수정 | request·response parity 불일치 0건 |
| 2 | DT2B G1 결정 동결 | actual profile로 unknown·partial·상태·정렬·오류·reason 확정 | Data 근거가 연결된 결정표, blocker 0건 |
| 3 | DT2C 소비 검증 | Frontend build·lint, 문서 테스트·검증, diff·비밀 경계 확인 | 실제 명령·환경·결과 기록 |
| 4 | DT2D Gate 종료 | 상태·인계 보드·체크리스트 동기화와 `G1_APPROVED` | DT3·Backend·Frontend 본 구현 시작 신호 |

DT2A~DT2C 중 불일치나 실패가 남으면 DT2D에서 승인 문구를 기록하지 않는다.
Node/npm 등 검증 환경 부재도 통과로 간주하지 않는다.

DT2A는 `2026-08-04`에 완료했다. Backend·Frontend request·response parity
정적 검사, 문서 검증 테스트 10건, `validate_docs.py`와 `git diff --check`가
통과했다. Frontend build·lint는 아직 실행하지 않았으며 DT2C 완료 증거로
남긴다. 현재 다음 Slice는 DT2B다.

## 브랜치 기준

두 담당자는 2주차 기준 SHA가 아닌, 이 인수인계 문서를 마지막으로
변경한 커밋에서 분기한다. Git 커밋은 자기 SHA를 자신의 파일 내용에
포함할 수 없으므로 담당자는 다음 명령으로 불변 SHA를 해석한다.

```powershell
$handoffRef = 'origin/feature/data/release-dataset-bootstrap'
git fetch origin feature/data/release-dataset-bootstrap
$handoffBase = git log -1 --format=%H $handoffRef -- `
  docs/development/weekly_plan/week_03_search_contract_handoff.md
$handoffBase
```

Team Leader가 이 문서 커밋을 remote에 push하기 전이라면 `$handoffRef`를
로컬 `feature/data/release-dataset-bootstrap`로 바꿔 확인한다. 해석 결과가
빈 값이거나 40자리 SHA가 아니면 브랜치를 만들지 않고 Team Leader에게
기준 커밋 전달 상태를 확인한다.

Backend:

```powershell
git fetch origin
git switch -c feature/backend/policy-search $handoffBase
git rev-parse HEAD
```

Frontend:

```powershell
git fetch origin
git switch -c feature/frontend/policy-search $handoffBase
git rev-parse HEAD
```

`git rev-parse HEAD`가 공통 커밋과 같지 않으면 구현을 시작하지 않는다.
이번 인수인계는 Backend·Frontend 담당자가 위 지정 브랜치를 생성하고 자신의
계획·초안 변경을 직접 커밋하는 것까지 허용한다. merge는 Team Leader가
수행한다. 다른 PC의 커밋을 전달하기 위한 push는 실제 작업 요청에서 별도로
허용된 경우에만 수행한다.

## 커밋 인계와 fast-forward 병합

담당자의 최종 보고에는 Team Leader가 정확한 대상을 검증할 수 있도록 다음
정보가 반드시 있어야 한다.

```text
HANDOFF_BRANCH=<branch-name>
HANDOFF_BASE=<인수인계 문서를 마지막으로 변경한 40자리 커밋 SHA>
HANDOFF_HEAD=<40-character-commit-sha>
HANDOFF_COMMITS=<base 이후 커밋 수>
WORKTREE_CLEAN=<true|false>
```

확인 명령은 다음과 같다.

```powershell
git branch --show-current
git rev-parse HEAD
git rev-list --count "$handoffBase..HEAD"
git log --oneline "$handoffBase..HEAD"
git status --short
```

담당 에이전트는 관련 검증이 통과한 변경만 커밋하고 실제 40자리 HEAD SHA를
공유한다. 테스트 실패나 미확정 계약 때문에 안전한 커밋을 만들 수 없으면
커밋하지 않고 `W3-B0_BLOCKED` 또는 `W3-F0_BLOCKED`와 원인·다음 조치를
보고한다.

fast-forward merge는 merge commit을 만들지 않지만 담당자의 일반 커밋을 Git
이력에서 숨기지는 않는다. GitKraken에서 분기선을 최소화할 수 있을 뿐 커밋은
대상 브랜치의 직선 이력으로 남는다. 하나의 새 커밋만 남기려면 squash 또는
cherry-pick이 필요하지만 이는 fast-forward가 아니며 Team Leader가 별도로
선택한다.

Backend와 Frontend가 같은 공통 커밋에서 병렬 분기하면 첫 번째 브랜치 병합
뒤 두 번째 브랜치는 자동으로 fast-forward할 수 없다. 충돌이 적은 권장 순서는
다음과 같다.

1. Backend W3-B0 계획·계약 commit을 먼저 검토해 Data 브랜치에 `--ff-only`
   병합한다.
2. 새 Data HEAD를 Frontend 담당자에게 공유한다.
3. Frontend 담당자는 명시적 승인 아래 자신의 브랜치를 새 Data HEAD 위로
   rebase하고 관련 문서·테스트를 다시 검증한다.
4. Frontend가 새 `HANDOFF_HEAD`를 보고하면 Team Leader가 `--ff-only` 가능
   여부를 다시 확인한다.
5. rebase·충돌 해결·병합은 담당자나 Team Leader의 명시적 권한 없이 AI
   Agent가 수행하지 않는다.

각 담당자가 `docs/index.md`나 공통 주차 문서를 동시에 바꾸면 rebase 충돌이
날 수 있다. 상세 내용은 담당 Forest 계획에 두고, 공통 weekly plan의 최종
통합은 Team Leader가 담당한다.

## 이미 고정된 방향

다음은 현재 Release 1·Integration 03 계약이며 담당자가 임의로 되돌리지 않는다.

- 검색 요청은 PostgreSQL만 사용하며 사용자 검색 중 외부 Source API를 호출하지
  않는다.
- Frontend는 자연어 원문을 `q`로 전달하고 별도 자연어 parser를 만들지 않는다.
- Backend가 결정적인 한국어 규칙으로 자연어를 구조화하는 단일 기준이다.
- LLM·벡터 검색은 `v0.1.0` 필수 경로가 아니다.
- 지역·연령·신청 상태는 `match|mismatch|unknown`을 구분한다.
- 지역 근거가 없으면 전국으로 추정하지 않고 `unknown`을 보존한다.
- Source Raw key를 Backend query가 직접 참조하지 않고 versioned search
  projection과 판정 primitive를 사용한다.
- invalid 정책은 공개하지 않는다.
- 기존 `/api/v1/policies` 목록·상세와 `include_partial` 계약은 새 검색 API가
  승인되기 전까지 유지한다.
- `NormalizedProgram` 1.1.0, Fixture, Seed, DB enum, `null`과 빈 배열 규칙은
  현재 DT2 Data 권고에서 변경하지 않는다.

## DT2B Gate G1 결정 동결

Backend W3-B0, Frontend W3-F0와 Data actual profile을 대조해 다음을 Release 1
승인 후보 계약으로 동결한다. DT2C 실행 검증과 DT2D 상태 동기화 전까지
`G1_APPROVED` 신호는 기록하지 않는다.

| 결정 영역 | DT2B 동결 계약 | Data 근거·소비 영향 |
| --- | --- | --- |
| endpoint | `GET /api/v1/policies/search`, trim 후 1~200자인 `q` 필수 | 자연어 검색 전용 route이며 `/programs` 기존 목록·exact filter는 유지 |
| explicit filter | flat `keyword`, `region`, `age`, `category`, `status`; 명시 값이 같은 q dimension을 override | Frontend parser 없이 수정 조건을 다시 요청할 수 있음 |
| pagination | `page=1`, `limit=20`, 최대 100; `total`은 pagination 전 필터 결과 | q·filter·limit 변경 시 Frontend가 `page=1`로 재설정 |
| mismatch·unknown | confirmed mismatch는 DB에서 제외, unknown은 hard cutoff 없이 후보에 포함하고 `unknown_count ASC`로 감점 | 복지로 10건이 지역·연령·상태 unknown이므로 전부 제거하지 않고 미확인을 표시 |
| 품질 | invalid는 제외, 검색 API만 `include_partial=true` 기본; 기존 목록 API 기본 false 유지 | 복지로 표본 10건 모두 partial이며 누락 조건을 row에 표시 |
| 상태 | 기본은 open·scheduled·`application_status=null`, closed 제외; 명시적 `status=closed`에서 closed 검색 | null은 enum이 아닌 unknown bucket이며 미확인 후보 규칙 적용 |
| 정렬 | `score DESC` → `unknown_count ASC` → open·scheduled·null·closed → `policy.id ASC` | Frontend sort UI·score 숫자 노출 없이 Backend 순서를 그대로 사용 |
| 해석 경고 | q의 unmapped·ambiguous는 `interpreted_conditions.conditions[]`; 명시 region 실패는 400 | query-level 경고와 row-level 정책 근거 부족을 분리 |
| 검색 이유 | row의 `reason_codes`, `message`, `unconfirmed_conditions`; 알 수 없는 code는 Backend message fallback | 정책 적용 가능성을 추정하지 않고 사용자 확인 필요를 설명 |
| URL state | 사용자 입력 flat parameter만 저장하고 Backend 해석·verdict·score는 저장하지 않음 | 공유 URL은 재검색으로 응답 상태를 복원 |
| 오류 | 의미 오류 400, validation 422, 정상 빈 결과 200·빈 items, 잘못된 route 404, 내부정보 없는 500 | loading·empty·error를 Frontend에서 분리 |

### 위험·미확정 항목 분류

| ID | DT2B 판정 | Release 1 처리 |
| --- | --- | --- |
| `G1-REASON` | resolved | 확장 가능한 string code와 Backend message fallback 사용 |
| `G1-UNK` | resolved | unknown 포함·감점·미확인 표시, hard cutoff 없음 |
| `G1-ROUTE` | resolved | 자연어 검색 `/search`, 기존 목록 `/programs` 병행 |
| `FF-REBASE` | resolved | 두 담당 HEAD가 Data 브랜치에 병합됨 |
| category 다중 선택 | non-blocking | v0.1.0은 단일 `category`, 다중 선택은 후속 검토 |
| 지역 ambiguous 후보 정확도 | implementation-risk | 임의 선택 금지, Backend B1·B4 parser·통합 테스트에서 검증 |

본 구현을 막는 미확정 검색 의미는 0건이다. NormalizedProgram 1.1.0,
Fixture, Seed, Migration, DB enum, `null`·빈 배열과 기존 Policy API 계약은
변경하지 않는다.

DT2B는 `2026-08-04`에 완료했다. G1 결정 정적 검사와 문서 검증 테스트
10건이 통과했다. 최초 `validate_docs.py`는 Backend·Frontend Forest 계획의
필수 `위험과 미확정 사항` 제목을 바꿔 2건 실패했고, 제목을 복원한 뒤 최종
검증과 `git diff --check`가 통과했다. 현재 다음 Slice는 DT2C다.

## Backend 06 인수 범위

### 계획 문서

구현 전에 다음 Forest 계획을 생성하고 관련 README와 `docs/index.md`에
등록한다.

```text
docs/development/develop_plan/backend/06_policy_search.md
```

구현을 시작해 계획 상태를 `in-progress`로 바꿀 때 대응 개발 기록을 만든다.

```text
docs/development/development_notes/backend/policy_search.md
```

### W3-B0 계약 초안

- 검색 endpoint·method와 request query/body
- `q`와 구조화 조건의 Pydantic request 모델
- 자연어 해석 Service와 Repository 책임 경계
- region·age·status 3값 판정 조합
- unknown·partial 포함과 관련도 감점 제안
- 검색 이유·미확인 조건·pagination response DTO
- 입력 오류·해석 실패·빈 결과 응답
- 기존 목록·상세 API 호환 방식
- 실제 snapshot에서 재검토할 query plan·index 항목

### 이번 인수 작업

- 기존 Repository·Service·API 분석
- request·response DTO의 문서 초안
- G1 승인 뒤 수행할 Backend 06 Slice·테스트 계획

G1 승인 전에는 parser·query builder·API·테스트 코드를 구현하지 않는다.

## Frontend 04 인수 범위

### 계획 문서

구현 전에 다음 Forest 계획을 생성하고 관련 README와 `docs/index.md`에
등록한다.

```text
docs/development/develop_plan/frontend/04_policy_search.md
```

구현을 시작해 계획 상태를 `in-progress`로 바꿀 때 대응 개발 기록을 만든다.

```text
docs/development/development_notes/frontend/policy_search.md
```

### W3-F0 소비 초안

- 자연어 `q` request와 구조화 조건 TypeScript 타입
- Backend 해석 조건 표시·수정 흐름
- 결과별 검색 이유와 미확인 조건 타입·표시 의미
- partial·지역/연령/상태 unknown 표시와 오해 방지 방식
- pagination·정렬과 URL query state
- loading·empty·error·404·422·500 상태
- 승인 Mock 계약과 실제 API Client 전환 계획
- Browser·반응형·접근성 검증 계획

현재 화면은 임시 Mock UI이므로 G1에 최종 시각 디자인을 요구하지 않는다.
Backend 응답을 같은 의미로 소비할 수 있는 타입과 사용자 흐름 초안이 필요하다.

### 이번 인수 작업

- 기존 API Client·query state·화면 소비 구조 분석
- Backend 제안과 대조할 TypeScript 타입·표시 의미의 문서 초안
- G1 승인 뒤 수행할 Frontend 04 Slice·Browser 검증 계획

G1 승인 전에는 UI component·Mock·API Client·Frontend 전용 parser를
구현하지 않는다.

## Gate G1 검토 절차

1. Backend 담당자가 W3-B0 계약 초안을 공유한다.
2. Frontend 담당자가 W3-F0 소비 초안을 공유한다.
3. Data 담당자가 actual profile과 Data 권고에 대조한다.
4. Team Leader가 parameter·unknown·partial·상태·정렬·reason 계약의 차이를
   표로 정리한다.
5. 세 담당자가 Schema·DB·API·Frontend 영향을 확인한다.
6. 승인된 결과를 담당 Forest 계획과 기준 문서에 반영한다.
7. `docs/index.md`의 `R1-SEARCH-DATA-SEMANTICS`를 종료하거나 후속 인계로
   전환한다.

Gate G1 완료 증거는 다음을 모두 포함한다.

- 실제 Data 표본과 각 결정의 연결
- Backend request·response·오류 계약
- Frontend TypeScript query·response와 UI 의미
- Schema·Fixture·Seed·DB·API 영향 판정
- 미확정 사항의 Release 1 차단 여부와 다음 담당

## 완료 통보와 개발 시작 신호

담당 에이전트는 계획·초안 작성이 끝난 마지막 보고에서 상태를 모호하게
표현하지 않고 다음 신호 중 하나를 사용한다.

### Backend 초안 완료 신호

Backend 계획과 W3-B0 계약 초안, 문서 검증이 끝나면 다음 문구로 보고한다.

```text
W3-B0_READY
Backend 06 계획과 검색 API·Repository 계약 초안 준비가 끝났습니다.
Team Leader는 이 초안을 Data 권고안·Frontend 초안과 대조하는 DT2 Gate G1
공동 검토를 시작해도 됩니다. 아직 G1 승인 전이므로 DT3 계약 의존 작업과
Backend·Frontend 본 구현 시작을 승인한 것은 아닙니다.
```

### Frontend 초안 완료 신호

Frontend 계획과 W3-F0 소비 초안, 문서 검증이 끝나면 다음 문구로 보고한다.

```text
W3-F0_READY
Frontend 04 계획과 검색 타입·UI 소비 초안 준비가 끝났습니다.
Team Leader는 이 초안을 Data 권고안·Backend 초안과 대조하는 DT2 Gate G1
공동 검토를 시작해도 됩니다. 아직 G1 승인 전이므로 DT3 계약 의존 작업과
Backend·Frontend 본 구현 시작을 승인한 것은 아닙니다.
```

각 담당자는 자신의 초안만으로 다른 담당자의 준비나 Gate G1 통과를 대신
승인하지 않는다. 최종 보고에는 변경 문서, 제안 request·response 또는 타입,
미확정 항목, 실행한 검증과 실패·미실행 항목, `HANDOFF_BRANCH`·
`HANDOFF_BASE`·`HANDOFF_HEAD`·`HANDOFF_COMMITS`·`WORKTREE_CLEAN`도 함께 적는다.

### Team Leader의 최종 시작 신호

Team Leader는 `W3-B0_READY`와 `W3-F0_READY`를 모두 받은 뒤 다음을 확인한다.

- Backend parameter·response와 Frontend request·response 타입이 일치함
- unknown·partial·상태·정렬·pagination 의미가 Data 권고와 모순되지 않음
- Schema·Fixture·Seed·DB·API 변경 여부와 담당자가 명확함
- Release 1을 막는 미확정 항목이 없거나 해결 책임·시점이 승인됨
- 필요한 기준 문서와 `docs/index.md` 인계 상태가 갱신됨

모두 충족하면 Team Leader가 다음 문구를 기록한다.

```text
G1_APPROVED
DT2 검색 계약 공동 검토가 완료됐습니다. Data는 DT3 계약 의존 수집·bootstrap
Slice를, Backend는 Backend 06 본 구현을, Frontend는 Frontend 04 승인 Mock과
UI 본 구현을 시작해도 됩니다. Frontend 실제 API 연결은 Backend endpoint가
준비된 뒤 진행합니다.
```

불일치나 차단사항이 남으면 `G1_BLOCKED`로 기록하고 원인·다음 담당·재검토
조건을 함께 적는다. `W3-B0_READY` 또는 `W3-F0_READY`만 받은 상태에서는
DT2를 완료하거나 G1 뒤 본 구현을 시작 가능하다고 기록하지 않는다.

## G1 이후 병렬 실행

```text
DT2·Gate G1 승인
  ├→ Data DT3: pagination·수집·Raw 재처리·PostgreSQL bootstrap
  ├→ Backend 06: 자연어 해석·검색 Repository·Service·API
  └→ Frontend 04: 자연어·조건·reason UI와 승인 Mock
                         ↓ Backend endpoint 준비
                    실제 API Client 연결
  └──────────────→ Integration 04 실제 DB → API → UI
```

G1 전에는 Data 근거, Backend·Frontend의 현재 구조 분석과 계획·계약 초안만
병렬로 준비한다. Data DT3, Backend 06과 Frontend 04 본 구현은 G1 승인
신호 뒤 각 담당 Forest의 별도 Slice로 수행한다.

## 공통 작업 원칙

- `opensource_plan`은 읽기 전용이며 수정하지 않는다.
- Schema, Fixture, Seed, `null`, 빈 배열 또는 enum 변경이 필요하면 단독으로
  적용하지 않고 세 영역 영향과 대안을 먼저 공유한다.
- Source·현재 코드·계획이 다르면 데이터를 추정해 맞추지 않는다.
- API 키, Raw payload, DB 비밀번호와 credential은 문서·로그·커밋에 넣지 않는다.
- 담당 Forest 밖의 관리자·추천·배포 기능을 추가하지 않는다.
- 직접 실행하지 않은 테스트와 Browser 검증을 통과로 기록하지 않는다.
- 담당자는 커밋 전에 관련 테스트, `python scripts/validate_docs.py`와
  `git diff --check`를 실행한다.

## Backend 담당자 시작 프롬프트

다음 문구를 작업 요청에 사용한다.

```text
작업 저장소 C:\git\cheongnyeon-alimi에서 Backend 06 검색 Forest 계획과
W3-B0 계약 초안을 작성해라.

공통 시작 커밋은 인수인계 문서를 마지막으로 변경한 커밋이고,
권장 브랜치는 feature/backend/policy-search다.

작업 전에 다음 문서를 읽어라.
C:\git\cheongnyeon-alimi\docs\index.md
C:\git\cheongnyeon-alimi\docs\governance\README.md
C:\git\cheongnyeon-alimi\docs\governance\documentation_policy.md
C:\git\cheongnyeon-alimi\docs\governance\role_assignment.md
C:\git\cheongnyeon-alimi\docs\development\weekly_plan\week_03_search_contract_handoff.md

인수인계 문서의 고정 계약과 범위를 따르고, 먼저
docs/development/develop_plan/backend/06_policy_search.md를 작성해라.
이번 작업에서는 코드를 구현하지 말고 request·response·오류,
unknown·partial·정렬·검색 이유 계약 초안을
우선 제시하고 Gate G1 공동 결정이 필요한 항목을 분리해라.
Schema·Fixture·Seed·DB enum을 임의로 변경하지 말고, 다른 담당자 영향이
있으면 변경 전에 채팅으로 알려라. 지정 Backend 브랜치를 생성하고 검증된
계획·초안 변경을 커밋하되 merge는 하지 마라. push는 별도 요청이 있을 때만
수행해라.
최종 보고 마지막에는 인수인계 문서의 `W3-B0_READY` 문구를 그대로 포함하고,
Gate G1 승인 전에는 DT3나 세 영역 본 구현을 시작해도 된다고 말하지 마라.
정확한 40자리 HEAD SHA, base 이후 커밋 목록과 clean worktree를 보고해라.
```

## Frontend 담당자 시작 프롬프트

다음 문구를 작업 요청에 사용한다.

```text
작업 저장소 C:\git\cheongnyeon-alimi에서 Frontend 04 검색 Forest 계획과
W3-F0 소비 초안을 작성해라.

공통 시작 커밋은 인수인계 문서를 마지막으로 변경한 커밋이고,
권장 브랜치는 feature/frontend/policy-search다.

작업 전에 다음 문서를 읽어라.
C:\git\cheongnyeon-alimi\docs\index.md
C:\git\cheongnyeon-alimi\docs\governance\README.md
C:\git\cheongnyeon-alimi\docs\governance\documentation_policy.md
C:\git\cheongnyeon-alimi\docs\governance\role_assignment.md
C:\git\cheongnyeon-alimi\docs\development\weekly_plan\week_03_search_contract_handoff.md

인수인계 문서의 고정 계약과 범위를 따르고, 먼저
docs/development/develop_plan/frontend/04_policy_search.md를 작성해라.
이번 작업에서는 코드나 UI를 구현하지 말고 TypeScript
request·response, 해석 조건 수정,
검색 이유·미확인 조건·partial 표시와 query state 초안을 우선 제시해라.
Frontend 전용 자연어 parser를 만들거나 미승인 API 계약을 확정하지 말고,
다른 담당자 영향이 있으면 변경 전에 채팅으로 알려라. 지정 Frontend 브랜치를
생성하고 검증된 계획·초안 변경을 커밋하되 merge는 하지 마라. push는 별도
요청이 있을 때만 수행해라.
최종 보고 마지막에는 인수인계 문서의 `W3-F0_READY` 문구를 그대로 포함하고,
Gate G1 승인 전에는 DT3나 세 영역 본 구현을 시작해도 된다고 말하지 마라.
정확한 40자리 HEAD SHA, base 이후 커밋 목록과 clean worktree를 보고해라.
```

## 관련 문서

- [3주차 Release 1 상세 계획](week_03_release_1.md)
- [3주차 Data·Team Leader 계획](week_03_data_team_leader.md)
- [Data 02 계획](../develop_plan/data/02_release_dataset_bootstrap.md)
- [Integration 03 계획](../develop_plan/integration/03_policy_search_data_foundation.md)
- [Data 02 개발 기록](../development_notes/data/release_dataset_bootstrap.md)
- [Policy DB 매핑](../../architecture/policy_database_mapping.md)
- [Policy API 계약](../../api/policies.md)
- [Fixture·Seed 계약](../../data/fixture_seed_contract.md)
