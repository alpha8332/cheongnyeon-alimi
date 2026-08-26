# 공개 dataset과 데이터 생명주기

## 기능 목적

작성자 로컬 DB, Git clone 사용자와 Download ZIP 사용자가 같은 공개 청년정책
결과를 보게 한다. 원본 Source API key가 없는 PC도 검증된 dataset으로 실행하고,
로컬 수집·과거 개발 데이터가 사용자 검색에 섞이지 않게 한다.

## 세 가지 데이터 범위

시스템의 정책 수는 어떤 범위를 세느냐에 따라 다르다.

| 범위 | 의미 | 환경 간 동일 여부 |
| --- | --- | --- |
| 전체 `policies` DB | 공개·로컬·과거·inactive 정책 전체 | 달라도 정상 |
| CollectionRun | 해당 PC의 import·수집 감사 기록 | 달라도 정상 |
| 활성 공개 membership | 현재 사용자 API가 반환할 수 있는 identity | 같은 version이면 동일해야 함 |

사용자 검색 결과의 기준은 전체 DB row 수나 CollectionRun 수가 아니라 활성 공개
dataset membership이다.

## 현재 공개 dataset

2026-08-26에 검증한 현재 `dataset-latest` snapshot은 다음과 같다.

| 항목 | 값 |
| --- | --- |
| version | `public-bootstrap-20260825-38180bc7a837ef` |
| 전체 정책 | 2,051건 |
| 복지로 | 461건 |
| 온통청년 | 1,586건 |
| 인천 공개 파일 | 4건 |
| 활성 identity SHA-256 | `85b70773cb64c7f97e2ffb7270be4dd68c892c23624f807a971b1585b808d76e` |

이 값은 고정된 snapshot 증거다. 이후 `dataset-latest` pointer가 승격되면 새
manifest가 정책 수, source 구성과 hash의 권위값이 된다.

## Source 수집과 공개 허용의 차이

공식 웹에서 접근할 수 있거나 수집기가 구현됐다는 사실만으로 정규화 데이터를
재배포할 수 있는 것은 아니다.

```text
수집 기술 승인
≠ 서비스 내부 DB 적재 승인
≠ 공개 dataset 재배포 승인
```

공개 dataset은 default-deny source 계약을 사용한다. 재배포 허용 근거가 명시된
source와 field만 include하며, 지역·보완 웹 source는 별도 허가와 완전 수집 Gate를
통과하기 전까지 로컬 DB에만 보존할 수 있다.

## 중앙 수집 파이프라인

새 데이터는 다음 계층을 거친다.

```text
공식 API·파일·웹
→ RawPolicyDocument
→ Source Extractor
→ ExtractedPolicy
→ Normalizer
→ NormalizedProgram
→ Validator·중복·지역·생명주기 Gate
→ PostgreSQL
```

### Raw 수집

Collector는 외부 요청과 원문 획득을 담당하고 응답 byte, source, 수집 시각,
문서 역할과 hash를 Git 제외 Runtime 경계에 보존한다. Raw payload를 공개
dataset이나 일반 API에 포함하지 않는다.

### Source별 추출

Extractor는 Source의 API 필드, XML tag와 HTML selector를 공통 의미의 중간
필드로 해석한다. Source 구조 변경은 해당 extractor에 격리한다.

### 정규화

Normalizer는 날짜, 행정구역, 연령, 분야, 신청 상태와 자격정보를 공통
`NormalizedProgram`으로 변환한다. 해석할 수 없는 값은 추정하지 않고 warning과
미확정 상태를 남긴다.

### 검증과 admission

Schema, 청년 대상, 지역 근거, 신청 상태, 중복과 품질 규칙을 평가한다. 결과는
valid, partial, invalid, duplicate, rejected 등으로 분리해 CollectionRun count와
감사 증거에 반영한다.

## 공개 artifact 생성 원리

공개 후보는 DB 전체가 아니라 다음 경계를 모두 통과한 정책이다.

- 공개 source allowlist
- valid 또는 허용 가능한 partial 품질
- inactive가 아님
- 한국 표준시 기준 종료일이 지나지 않음
- 재배포 field allowlist
- 개인정보·비밀 query 안전 검사
- 결정적 source·external ID identity

Raw payload, DB 내부 시각, dump, API key, 기관 연락처와 비허용 source는 artifact에
포함하지 않는다. 이메일·개인 휴대전화나 비밀 query pattern이 있으면 임의
마스킹으로 의미를 바꾸지 않고 현재 계약에서는 row 전체를 제외한다.

## manifest와 무결성

각 공개 artifact에는 다음 내용을 가진 manifest가 있다.

- dataset version과 생성 Git SHA
- 예상 row 수
- source별 row 수와 출처
- artifact byte 수와 SHA-256
- Schema·source contract hash
- 안전 검사 count
- 이전 성공 version

artifact는 정해진 identity 순서와 UTF-8 JSON 형식으로 만들어 같은 입력에서 같은
hash를 낼 수 있어야 한다.

## 설치와 원자적 활성화

`run_docker.bat`은 latest pointer, manifest와 artifact 순서로 내려받고 각 hash와
row를 다시 검증한다. 설치는 다음 DB 구조를 사용한다.

- `public_dataset_installations`: version, manifest·artifact hash, 예상 수,
  설치·활성 상태
- `public_dataset_memberships`: version에 포함된 `source_id + external_id`와
  정책 row 연결

정책 upsert, 모든 membership write와 새 version 활성화를 하나의 transaction으로
처리한다. 모든 검증이 끝나기 전에는 새 version을 active로 바꾸지 않는다.

중간 실패가 발생하면 transaction을 rollback하고 이전 active version을 유지한다.
기존 정책 row를 물리적으로 삭제하지 않아 과거 감사와 참조를 보존한다.

## 사용자 API projection

목록, 자연어 검색, 추천과 상세 API는 active membership과 공개 생명주기 조건을
동시에 만족한 정책만 읽는다.

```text
전체 policies
∩ active dataset membership
∩ inactive_at IS NULL
∩ 종료일이 없거나 KST 오늘 이상
∩ 공개 품질 상태
= 사용자 정책 projection
```

active dataset이 없으면 DB 전체를 임시 대체 데이터로 공개하지 않고 빈 목록 또는
상세 `404`를 반환한다.

## 환경 간 동등성

깨끗한 심사자 DB와 로컬 수집 정책이 많은 작성자 DB에 같은 dataset version을
설치하면 다음 값이 같아야 한다.

- 공개 정책 수
- 정렬된 `source_id + external_id` identity hash
- 목록·검색·추천·상세의 공개 후보 집합
- source별 공개 membership 수

로컬 CollectionRun 수와 전체 DB 수는 비교 대상이 아니다. 즐겨찾기 같은 기존
정책 ID 참조는 dataset 교체 중에도 보존해야 한다.

## 데이터 생명주기

정책이 DB에 있다는 사실과 현재 공개된다는 사실을 구분한다.

### 새 정책과 갱신

같은 source·external ID는 기존 row를 갱신하고, 새 identity는 새 row를 만든다.
수집 시각과 마지막 확인 시각은 과거로 되돌리지 않는다.

### 미발견 정책

제한 수집이나 partial_failure에서 보이지 않았다는 이유로 기존 정책을 inactive
처리하지 않는다. Source 전체 목록을 완전하게 수집했다는 증거가 있는 complete
snapshot 성공에서만 미발견 생명주기를 평가한다.

### 재등장

inactive 정책이 이후 검증된 complete 수집에서 다시 나타나면 기존 identity를
유지한 채 inactive 상태를 해제할 수 있다.

### 종료일 경과

날짜가 지났다는 이유만으로 DB row를 삭제하지 않는다. 관리자 감사에는 남기고
사용자 projection에서 한국 표준시 기준으로 제외한다.

## 수동 수집과 승격

관리자 수동 실행은 DB와 CollectionRun을 갱신할 수 있지만 active membership을
바꾸지 않는다. 새 데이터를 사용자에게 공개하려면 별도의 완전 수집, 품질,
라이선스, 안전, parity와 지역 coverage Gate를 거쳐 새 version을 발행해야 한다.

## 실패 안전성

- latest 다운로드 실패: 검증된 cache 또는 release 고정 fallback 사용
- manifest·artifact hash 불일치: 설치 중단
- 예상 row 수 불일치: 설치 중단
- identity 중복·불일치: 설치 중단
- 정책·membership write 실패: 전체 transaction rollback
- 공개 parity·지역 coverage 실패: release pointer 승격 금지
- 수집 partial_failure: 직전 공개 dataset 유지

## 비밀정보와 재배포 경계

공개 Git·Release·문서에 다음을 넣지 않는다.

- Source API key와 비밀 query
- DB 비밀번호와 dump
- 관리자 PIN·token
- Runtime Raw API/XML/HTML
- 개인 이메일·휴대전화
- 재배포 허용이 확인되지 않은 source의 정규화 정책

GitHub Secret의 API key는 중앙 workflow 수집에만 사용할 수 있으며 공개 artifact에
key를 넣거나 일반 사용자에게 배포하지 않는다.

## 현재 제한사항

- 공개 dataset은 실시간 원문 mirror가 아니라 검증된 snapshot이다.
- 수집 가능한 11개 source 전체가 공개 dataset에 포함되는 것은 아니다.
- 재배포 권한이 불명확한 지역 웹 정책은 로컬 DB에 있어도 사용자에게 공개되지
  않는다.
- 신규 dataset 발행 전에는 원본 Source의 최신 변경이 사용자 결과에 반영되지
  않을 수 있다.

## 관련 계약

- [공개 정책 dataset 계약](../../data/public_policy_dataset.md)
- [공개 dataset 동등성](../../data/public_dataset_parity.md)
- [정책 생명주기](../../data/policy_lifecycle.md)
- [데이터 수집 정책](../../data/collection_policy.md)
- [시스템 흐름](../../architecture/system_flow.md)
- [Production 배포](../../operations/production_delivery.md)
