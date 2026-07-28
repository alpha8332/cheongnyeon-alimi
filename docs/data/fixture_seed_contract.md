# Fixture와 Seed 계약

## 문서 상태

- 상태: 기술 기준선
- Data 검증: 완료
- Backend·Frontend 공동 승인: 대기
- 기준 Schema: `NormalizedProgram` 1.0.0

이 문서는 외부 네트워크 없이 Raw부터 Seed까지 재현하는 개발 데이터와
Backend·Frontend 소비 규칙을 정의한다. 실제 API 응답을 배포하는 자료가
아니며 모든 정책 내용과 식별자는 합성 데이터다.

## 담당자 착수 안내

Backend와 Frontend는 현재 Schema와 Seed로 기능 구현을 시작할 수 있다.
다만 구현 시작 가능 상태와 공동 계약 승인 완료는 다르다.

1. 담당 Agent는 이 문서의 소비 계약과 영역별 검토 항목을 먼저 읽는다.
2. Backend는 importer·API 테스트, Frontend는 타입·Mock 소비 테스트로
   실제 사용 가능성을 확인한다.
3. 확인 결과와 변경 요청을 아래 공동 검토 기록에 남긴다.
4. 두 영역이 승인한 뒤에만 Data 6와 Data Pipeline Forest를 완료 처리한다.

계약 변경이 필요하면 Python 모델, JSON Schema, Fixture, Seed와 영향 문서를
같은 변경에서 동기화한다.

## 산출물

| 경로 | 역할 | 레코드 |
| --- | --- | ---: |
| `data/fixtures/raw/` | 두 소스의 합성 Raw envelope | 8 |
| `data/fixtures/extracted/policies.json` | Extractor 결과 | 5 |
| `data/fixtures/normalized/programs.json` | valid·partial 결과 | 4 |
| `data/fixtures/rejected/programs.json` | invalid와 실패 사유 | 1 |
| `data/seeds/initial_programs.json` | canonical 개발 Seed | 4 |

Normalized Fixture와 canonical Seed는 byte가 같은 JSON 배열이다. rejected는
정상 Seed에 포함하지 않는다. 현재 Backend가 CSV importer를 요구하지 않았고
CSV는 배열·null 표현을 약화하므로 생성하지 않는다.

## 합성 Raw 경계

Raw Fixture는 실제 응답에서 확인한 JSON·XML 문서 역할과 필드 이름만
재현한다.

- 모든 external ID는 `SYN-`으로 시작한다.
- URL은 네트워크에서 사용되지 않는 `fixture.invalid` host만 사용한다.
- 정책명·기관·지원 내용은 실제 정책을 복사하지 않은 합성 문구다.
- 인증 파라미터, 인증키, 개인정보와 실제 API 응답 byte를 포함하지 않는다.
- 고정된 문서 ID·수집 시각·payload로 Hash와 provenance를 결정적으로 만든다.

운영 `runtime/raw/`는 생성 입력이나 fallback으로 사용하지 않는다. 따라서
로컬에 운영 Raw가 없어도 같은 결과를 만들 수 있다.

## 대표 사례

| ID | Source | 품질 | 대표 계약 |
| --- | --- | --- | --- |
| `SYN-YOUTH-001` | 온통청년 | valid | 연령 범위, 서울, 특정 기간, closed |
| `SYN-YOUTH-002` | 온통청년 | valid | 연령 제한 없음, 전국, 다중 category, always·open |
| `SYN-BOK-001` | 복지로 | partial | 목록·상세 결합, 다중 관심주제, 지역·연령·기간 null |
| `SYN-BOK-002` | 복지로 | partial | 목록만 존재, category·지역 배열 비어 있음 |
| `SYN-YOUTH-REJECTED` | 온통청년 | invalid | 필수 제목 누락과 `$.title` 오류 |

partial도 JSON Schema를 통과한 정상 전달 객체다. 검색 정보가 일부
부족하다는 품질 상태를 보존하며, invalid만 정상 Fixture와 Seed에서
분리한다.

## canonical JSON 소비 계약

`initial_programs.json`의 root는 `NormalizedProgram` 객체 배열이다.

- 모든 객체는 Schema의 31개 key를 가진다.
- 선택 단일 값 없음은 `null`, 복수 값 없음은 `[]`이다.
- enum과 `YYYY-MM-DD` 날짜는 JSON string으로 유지한다.
- `source_id + external_id`를 source-scoped 식별 경계로 사용한다.
- `data_quality_status`가 `valid` 또는 `partial`인 객체만 포함한다.
- Raw document ID·역할·Hash·시각·안전 URL provenance를 그대로 보존한다.
- 배열을 단일 string으로, null을 빈 문자열로 바꾸지 않는다.

### Backend 검토 항목

- JSON 배열을 적재 입력으로 받을지 별도 importer를 둘지 결정
- `source_id + external_id` uniqueness와 upsert 경계 확인
- partial 적재 여부와 품질 필터 동작 확인
- provenance의 DB 보존 범위와 외부 API 노출 여부 결정
- 날짜 string을 DB date로 바꿀 때 null과 원문 text 보존 확인

### Frontend 검토 항목

- `categories`, `regions`와 조건 필드를 항상 배열로 처리
- 선택 단일 필드를 nullable로 처리하고 빈 문자열로 치환하지 않음
- `application_schedule`과 `application_status`를 다른 의미로 표시
- partial 표시 또는 누락 필드 fallback 정책 확인
- provenance를 일반 화면에 노출할지 관리자 화면에만 사용할지 결정

Frontend는 2026-07-28 `feature/frontend/policy-discovery` Slice에서
TypeScript 타입·Mock·와이어프레임 UI 소비를 구현했다. Backend 모델·Importer는
아직 없다.

## 재생성과 검증

저장된 합성 사례로 전체 산출물을 다시 쓴다.

```powershell
uv run python -B scripts/build_data_fixtures.py --write
```

커밋된 파일이 결정적 재생성 결과와 같은지만 확인한다.

```powershell
uv run python -B scripts/build_data_fixtures.py --check
```

`--check`는 외부 API와 `runtime/raw/`를 사용하지 않는다. 예상 파일의 누락,
추가 JSON 파일과 byte 차이가 있으면 실패한다.

## 출처·개인정보·재배포 검토

2026-07-26에 다음 공식 자료를 확인했다.

- [복지로 중앙부처 복지서비스 API][bokjiro-api]는 이용허락범위를
  `제한 없음`으로 표시한다.
- [온통청년 OPEN API 이용방법][youth-api-guide]은 회원가입, 인증키 신청과
  담당자 승인을 요구한다.
- [온통청년 이용약관][youth-terms]은 대량 이용을 별도 계약 대상으로 두고,
  서비스에서 얻은 게시 자료의 무단 상업적 가공·판매를 제한한다.

온통청년 정책 API 원문의 저장·변환·Git 재배포 범위가 명시적으로 확인되지
않았으므로 실제 원문은 포함하지 않는다. 복지로도 소스 간 일관성, 최소성,
개인정보와 시점 의존성을 위해 실제 원문 대신 합성 Fixture를 사용한다. 이는
법률 판단이 아니라 저장소의 보수적인 재배포 경계다.

## 공동 검토 기록

| 영역 | 상태 | 확인 결과 또는 필요한 증거 |
| --- | --- | --- |
| Data | reviewed | Schema·재생성·committed Raw → Seed 종단 간 테스트 완료 |
| Backend | pending | 담당자 승인 또는 실제 importer 소비 테스트 필요 |
| Frontend | reviewed | 2026-07-28 TypeScript 타입·Seed Mock·와이어프레임 UI 소비 검증 완료 ([개발 기록](../development/development_notes/frontend/policy_discovery.md)) |

### Frontend 검토 결과 (2026-07-28)

브랜치 `feature/frontend/policy-discovery`에서 `NormalizedProgram` 1.0.0
Schema와 `initial_programs.json` Seed 4건을 TypeScript·Mock·와이어프레임
UI로 소비했다. Schema·Fixture·Seed는 변경하지 않았다.

#### null과 빈 배열([]) 처리

- 선택 단일 필드(`organization`, `summary`, `application_start` 등)는 Seed·API
  응답의 `null`을 그대로 유지하고 빈 문자열(`""`)로 치환하지 않는다.
- UI fallback은 표시 시점에만 적용한다. 예: `organization ?? '기관 정보 없음'`.
- 복수 값 필드(`categories`, `regions`, `education_statuses` 등)는 항상
  배열로 취급하고 `null`을 기대하지 않는다. Seed 계약대로 값 없음은 `[]`이다.
- 렌더링은 `array.length === 0`일 때 "분류 없음", "지역 미정" 등 안내 문구를
  표시한다.

#### categories 배열

- 단일 `category` enum이 아닌 `categories: PolicyCategory[]` 배열을 수용한다.
- 다중 값(예: `SYN-YOUTH-002`의 `finance`, `welfare`)은 태그 목록으로 표시한다.
- `categories: []`이고 `category_text: null`인 partial(예: `SYN-BOK-002`)은
  "분류 없음"으로 표시하고 `category_text` 원문이 있으면 보조 텍스트로 병행
  표시한다.

#### application_schedule과 application_status 구분

- `application_schedule`은 일정 **유형**(`fixed_period`, `always`,
  `until_budget_exhausted`)이며 "기간 한정", "상시", "예산 소진 시까지"로
  표시한다.
- `application_status`는 수집 기준 시점 **접수 상태**(`open`, `closed`,
  `scheduled`)이며 "접수 중", "마감", "예정"으로 표시한다.
- 두 필드는 같은 UI 라벨로 합치지 않는다. 예: `always`+`open`은 "상시 · 접수
  중"처럼 별도 영역에 병기한다.
- 판단 근거가 없으면 Schema대로 `null`을 유지하고 "일정 미확인", "상태
  미확인"으로 표시한다. `"unknown"` enum은 사용하지 않는다.

#### partial 데이터 처리

- `data_quality_status: "partial"`은 invalid가 아니며 목록·상세에 정상 노출한다.
- partial 항목에는 "정보 일부 누락" 와이어프레임 배지를 표시한다.
- 구조화 필드가 `null`이면 원문 text(`region_text`, `age_condition_text`,
  `application_period_text`, `category_text`)를 우선 표시하고, text도 `null`이면
  필드별 fallback 문구를 사용한다.

#### source_id + external_id 식별 경계

- 정책 식별 키는 `source_id + external_id` 복합 경계를 사용한다.
- 상세 라우트 ID는 `{source_id}--{external_id}` URL-safe 단일 파라미터로
  인코딩한다(예: `youthcenter-api--SYN-YOUTH-001`).
- Mock·향후 Backend API 모두 동일 lookup(`source_id`, `external_id`)으로
  상세를 조회한다. DB primary key나 단일 numeric ID는 Frontend에서 사용하지
  않는다.

#### provenance 저장·노출 범위

- `provenance` 배열은 타입·Mock·API 응답에 포함하되 일반 사용자
  목록·상세·검색 UI에는 노출하지 않는다.
- 관리자 `DataQualityPage`에서만 Raw document ID·역할·수집 시각 등
  디버깅·품질 확인용으로 표시한다.

Backend와 Frontend의 승인 증거가 생기기 전에는 Data 6의 기술 산출물을
안정적인 영역 간 계약으로 확정하지 않는다. 두 영역 검토 후 이 표와 Forest
계획·개발 기록을 갱신하고 Data 6를 `completed`로 전환한다.

[bokjiro-api]: https://www.data.go.kr/data/15090532/openapi.do
[youth-api-guide]: https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiGuide
[youth-terms]: https://www.youthcenter.go.kr/cmnFooter/termsInfo
