# 시스템 흐름

## 문서 상태

- 상태: 기준선
- 현재 구현 상태: 문서 기반 구축 단계

이 문서는 데이터가 외부 소스에서 사용자 화면까지 이동하는 순서와 각
경계에서 사용하는 공통 용어를 정의한다.

## 전체 흐름

```text
공식 API ─────────────┐
                     ├→ Collector
공개 HTTPS 웹사이트 ─┘
                          ↓
                  RawPolicyDocument
                          ↓
                   Source Extractor
                          ↓
                    ExtractedPolicy
                          ↓
                      Normalizer
                          ↓
                  NormalizedProgram
                          ↓
                       Validator
                    ┌─────┴─────┐
                    ↓           ↓
              valid / partial  invalid
                    ↓           ↓
          Fixture·Seed 또는   Rejected Data
             PostgreSQL
                    ↓
                  FastAPI
                    ↓
                   React
```

## 1. 외부 소스에서 Raw까지

### 입력

- 인증이 필요한 공식 API 응답
- 공개 웹사이트의 목록 및 상세 HTML

### Collector 책임

- 인증키와 요청 설정 읽기
- HTTP 요청, Timeout, 재시도와 요청 간격 적용
- 상태 코드와 응답 형식 확인
- 원본 응답 또는 정책 항목 추출
- 출처 URL, 수집 시각과 응답 메타데이터 기록
- `RawPolicyDocument` 반환

Collector는 외부 필드를 서비스 필드로 정규화하지 않는다. API와 Web
Collector는 서로 다른 원문을 다뤄도 같은 Raw 계약을 반환한다.

## 2. Raw 보존

`RawPolicyDocument`는 원문과 다음과 같은 수집 문맥을 함께 보존한다.

- `source_id`와 source type
- 외부 식별자 또는 안정적인 대체 식별자
- 출처 URL
- 수집 시각
- content type과 raw format
- 원본 payload
- content hash
- HTTP 상태와 Collector 버전

Raw는 정규화 규칙이 바뀌었을 때 외부 소스를 다시 호출하지 않고 재처리할 수
있어야 한다. 개발용 최소 샘플과 실제 런타임 Raw의 저장 위치를 구분한다.

## 3. 소스별 추출

Source Extractor는 `RawPolicyDocument`에서 사람이 이해할 수 있는 중간 필드를
찾아 `ExtractedPolicy`로 만든다.

예:

- API 필드와 XML 태그 해석
- HTML 목록에서 상세 URL 추출
- 상세 페이지의 제목, 기관, 신청 기간과 지원 내용 추출
- 소스별 추가 필드는 `extra`에 보존

Normalizer는 XML 태그나 CSS Selector를 알아서는 안 된다. 소스 구조 변경은
해당 Collector 또는 Extractor에 한정한다.

## 4. 공통 정규화

Normalizer는 `ExtractedPolicy`를 `NormalizedProgram`으로 변환한다.

주요 처리:

- 공백, 줄바꿈, HTML 태그와 Entity 정리
- 날짜 범위와 상시·예산 소진 상태 해석
- 명시된 숫자 범위의 연령 변환
- 지역 표준 이름 변환
- 카테고리 enum 매핑
- 파싱할 수 없는 원문과 누락 상태 보존

정규화할 수 없는 값 하나 때문에 전체 실행을 중단하지 않는다. 알 수 없는
값을 임의로 만들어 정확한 값처럼 저장하지 않는다.

## 5. 검증과 품질 분기

Validator는 `NormalizedProgram`을 JSON Schema와 품질 규칙으로 확인한다.

- `valid`: 필수 필드와 주요 검색 필드가 정상
- `partial`: 필수 필드는 있으나 일부 선택·검색 필드가 누락
- `invalid`: 제목, 출처 URL 등 핵심 필드가 누락되거나 계약을 위반

valid와 허용된 partial 데이터는 Fixture·Seed 또는 PostgreSQL 입력으로
전달한다. invalid 데이터는 정상 데이터와 섞지 않고 rejected 결과와 검증
이유를 남긴다. 세부 판정 규칙은 데이터 기준선에서 확정한다.

## 6. Fixture, Seed와 PostgreSQL

### Fixture

고정된 JSON 데이터로 Schema, 백엔드, 프론트엔드와 테스트가 같은 사례를
사용하게 한다.

### Seed

개발 환경의 초기 DB에 적재할 데이터다. Collector가 완성되기 전에도 API와
UI 개발을 진행할 수 있게 한다.

### PostgreSQL

검증된 정규화 데이터를 서비스 조회가 가능한 형태로 저장한다. 원문,
정규화 데이터와 수집 실행의 관계를 추적할 수 있어야 한다.

## 7. API와 Web UI

FastAPI는 PostgreSQL 또는 합의된 개발 데이터를 사용해 정책 목록, 상세,
검색, 추천과 관리자 API를 제공한다. React는 같은 API 계약에 따라 사용자와
관리자 화면을 구성한다.

프론트엔드 Mock은 실제 API와 다른 독자 타입을 만들지 않고 합의된 Fixture와
응답 계약을 따른다.

## 실패 경계

- 외부 요청 실패는 해당 수집 실행에 기록하고 다른 소스의 처리와 구분한다.
- 소스별 필드 누락은 가능한 범위에서 `ExtractedPolicy`로 전달한다.
- 정규화 실패는 원문을 보존하고 품질 상태로 표현한다.
- 검증 실패 데이터는 PostgreSQL 정상 레코드나 배포용 Seed에 조용히
  포함하지 않는다.
- API와 UI는 데이터 수집 실패를 직접 외부 요청으로 우회하지 않는다.

구체적인 재시도, 저장 경로, Schema와 품질 기준은 데이터 및 운영 문서에서
구현 Slice에 맞춰 확정한다.
