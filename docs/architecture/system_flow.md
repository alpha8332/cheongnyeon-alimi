# 시스템 흐름

이 문서는 정책이 공식 Source에서 공개 dataset과 사용자 화면까지 이동하는
현재 경로를 설명한다. 중앙 수집 경로와 사용자 PC의 설치·조회 경로는 분리된다.

## 전체 흐름

```text
공식 API·공개 웹
  → Collector
  → RawPolicyDocument
  → Source Extractor
  → ExtractedPolicy
  → Normalizer
  → NormalizedProgram
  → Validator
  → 중앙 PostgreSQL·품질 검증
  → 공개 허용 projection
  → versioned manifest + artifact
  → 사용자 PC 검증·설치
  → 활성 dataset membership
  → FastAPI 검색·추천·상세
  → React UI
```

## 1. 중앙 수집

Collector는 인증정보를 환경변수에서 읽고 요청 timeout, 재시도, rate limit과
Source별 범위를 적용한다. API와 웹 Collector는 외부 필드를 서비스 필드로
바꾸지 않고 원문과 provenance를 `RawPolicyDocument`로 남긴다.

Raw에는 `source_id`, 외부 identity, 원문 URL, 수집 시각, content type,
content hash와 payload가 포함된다. 실제 Raw는 Runtime 저장소에만 두며 Git,
로그와 공개 dataset에 넣지 않는다.

## 2. 추출·정규화·검증

Source Extractor는 API 필드, XML 태그와 HTML locator를 해석해 중간 필드를
만든다. Normalizer는 Source 구조를 모른 채 날짜, 지역, 연령, 분야와 신청
상태를 공통 형식으로 변환한다.

Validator는 Schema와 품질 규칙으로 다음 상태를 만든다.

- `valid`: 필수 필드와 검색 근거가 확인됨
- `partial`: 정책은 사용할 수 있지만 일부 조건 확인이 필요함
- `invalid`: 핵심 계약 위반으로 정상 projection에서 제외

해석할 수 없는 값은 전국, 제한 없음 또는 자격 충족으로 바꾸지 않는다.

## 3. DB import와 CollectionRun

검증된 `valid`·허용된 `partial`만 `(source_id, external_id)` identity로
PostgreSQL에 upsert한다. 실행 상태와 삽입·갱신·실패 집계는
`collection_runs`에 남기며 Raw payload, secret과 전체 오류 본문은 저장하지
않는다.

Source 완전 snapshot에서 사라진 정책은 즉시 삭제하지 않고 생명주기 규칙으로
inactive 처리한다. 실패·불완전 snapshot은 기존 정책을 대량 비활성화하지 않는다.

## 4. 공개 dataset 생성

중앙 Workflow는 수집 가능한 모든 Source가 아니라 재배포 근거와 품질 기준을
통과한 Source만 공개 후보로 선택한다. 후보는 다음 Gate를 모두 통과해야 한다.

- 포함 Source와 expected row count
- JSON Schema와 field allowlist
- 중복 identity와 lifecycle
- 개인정보·비밀 pattern
- artifact byte 수와 SHA-256
- 격리 DB 설치 후 공개 projection·검색 smoke

성공하면 불변 `dataset-<version>` Release에 artifact와 manifest를 올리고
`dataset-latest` pointer를 마지막에 갱신한다. 실패하면 기존 pointer를 유지한다.

## 5. 사용자 PC 설치

`run_docker.bat`은 pointer → manifest → artifact 순으로 내려받아 각 hash와
크기를 검증한다. Migration 후 공개 dataset import를 단일 transaction으로
실행한다.

설치 과정은 `public_dataset_installations`에 version·hash·상태를,
`public_dataset_memberships`에 공개 identity와 정책 FK를 기록한다. 모든 row와
membership 확인이 끝난 뒤에만 새 version을 활성화한다. 중간 실패 시 transaction을
rollback하고 이전 활성 version을 유지한다.

## 6. 사용자 조회

목록·검색·추천·상세 Repository는 다음 교집합만 반환한다.

```text
활성 공개 dataset membership
∩ 공개 가능한 lifecycle·품질 상태
∩ 사용자가 요청한 검색·필터 조건
```

따라서 작성자 DB에 과거 수집 정책이 더 많거나 CollectionRun 수가 달라도 같은
dataset version과 identity hash를 설치한 환경의 사용자 결과 집합은 같다.

## 7. 관리자 수동·정기 수집

관리자 수동 실행과 선택적 scheduler는 Redis queue에 CollectionRun을 enqueue하고
Celery worker가 Source 수집과 import를 수행한다. 결과는 로컬 DB와 Runtime에
남지만 중앙 검증·dataset 승격 없이는 일반 사용자 projection에 들어가지 않는다.

관리자 수집기 화면의 credential 상태는 새 수집 가능 여부를 나타낼 뿐, 이미
설치된 공개 dataset을 검색할 수 있는지와는 별개다.

## 8. Frontend와 개인 데이터

FastAPI는 PostgreSQL 결과와 보수적인 미확정 상태를 JSON으로 반환한다. React는
검색 조건, 추천 이유, 출처와 미확정 안내를 표시한다. 프로필과 즐겨찾기는
브라우저 `localStorage`에만 저장하고 외부 Source에 전송하지 않는다.

## 실패 경계

- 외부 Source 실패는 다른 Source와 분리하고 CollectionRun에 안전한 집계만 남긴다.
- invalid 정책은 공개 후보에 조용히 섞지 않는다.
- 새 dataset 검증·설치 실패는 이전 활성 version을 훼손하지 않는다.
- API와 UI는 수집 실패를 사용자 요청 시 외부 Source 직접 호출로 우회하지 않는다.
- 공식 원문과 구조화 값이 충돌하면 자동 자격 확정보다 원문 확인을 우선한다.

세부 실행은 [Collector 운영](../operations/collector.md), 공개 경계는
[공개 정책 dataset](../data/public_policy_dataset.md), DB 구조는
[정책 DB 매핑](policy_database_mapping.md)을 따른다.
