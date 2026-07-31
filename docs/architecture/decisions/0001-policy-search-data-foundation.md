# ADR 0001: 정책 검색 데이터 기반

- 상태: proposed
- 작성일: 2026-07-31
- 결정자: Data·Backend·Frontend·Team Leader 공동 검토 예정
- 관련 Issue/PR: 미정

## 맥락

현재 `NormalizedProgram` 1.0.0은 지역을 원문 `region_text`와 표준 이름
`regions` 배열로 보존하고 PostgreSQL JSONB exact membership으로 조회한다.
이 구조는 합성 Seed와 단일 지역 필터에는 적합하지만 다음 요구를 처리하기
어렵다.

- 천안 검색에서 천안시·충청남도·전국 정책을 함께 판정
- 지역 미상 중앙정부 정책과 명시적 전국 정책 구분
- 지역 포함·제외 규칙
- 행정구역 code의 개편·폐지·분할·별칭
- 온통청년·복지로와 향후 지역 웹사이트의 서로 다른 key 통합
- 사용자 표시 text와 검색 전용 projection 분리

2026-07-31 DT1 실제 표본에서 온통청년 10건은 `zipCd` 원문이 있지만 승인된
code-to-name 표가 없어 정규화 지역이 모두 비었고, 복지로 10건은
지역·연령·신청기간이 모두 없었다. 누락을 전국으로 추정하면 오탐이 되고,
현재 partial 기본 비노출을 유지하면 실제 정책이 검색에서 사라진다.

또한 온통청년 `plcyExplnCn`·`mclsfNm`·`plcyKywdNm`, 복지로
`wlfareInfoOutlCn`·`lifeArray`·`trgterIndvdlArray`는 Raw에 보존되지만 현재
공통 검색 필드에서 충분히 사용되지 않는다.

## 결정

다음 구조를 채택할지 Integration 03 PSF0에서 공동 검토한다.

1. Source Adapter가 원본 key를 Source 중립 공통 필드로 변환한다.
2. 정책 지역 적용 범위는 `nationwide`, `regional`, `unknown`으로 구분한다.
3. 행정구역은 이름 배열을 identity로 쓰지 않고 versioned code·parent·alias
   기준정보를 사용한다.
4. 정책과 지역은 include·exclude 관계로 저장하고 Source code와 근거 원문을
   보존한다.
5. 기존 `regions` 배열은 공개 호환용 파생 표현으로 유지한다.
6. Source 설명은 기존 `summary`에 채우고 keywords·life stages·target groups
   후보를 additive 계약으로 검토한다.
7. Korean text 검색용 projection은 공개 Policy DTO와 별도 저장 책임으로
   둔다.
8. 지역·연령·상태 판정은 `match`, `mismatch`, `unknown` 3값을 사용한다.
9. 기존 row에 근거가 없으면 `coverage_scope=unknown`으로 backfill하고
   전국이나 지역을 추정하지 않는다.
10. Source 간 canonical deduplication과 최종 자연어 검색 가중치는 별도
    Forest에 남긴다.

이 ADR은 `proposed`이며 현재 구현 계약을 변경하지 않는다. PSF0 공동 검토와
영향 확인 뒤 채택 여부와 최종 필드·테이블 이름을 결정한다.

## 고려한 대안

### 기존 `regions` JSONB 배열 유지

구현은 단순하지만 상위 지역·전국·제외·행정구역 변경을 표현하기 어렵고
문자열 exact match가 이름 변경과 별칭에 취약하다.

### 누락 지역을 모두 전국으로 처리

검색 결과는 늘지만 Source가 제공하지 않은 적용 범위를 생성해 잘못된 신청
가능성을 안내할 위험이 있어 채택하지 않는다.

### 모든 Source 원본 key를 Backend 검색에서 직접 사용

Source 추가마다 Repository와 query가 바뀌고 Raw key가 API·UI까지 누출되므로
채택하지 않는다.

### 모든 지역·검색 정보를 하나의 JSONB에 저장

초기 Migration은 쉽지만 FK·계층·유효기간·참조 무결성과 query plan을
보장하기 어려워 기준정보와 관계는 관계형 저장을 우선한다.

### Source 간 canonical 정책 테이블을 동시에 도입

장기적으로 유용하지만 현재 동일 정책 판정 근거가 없고 제목 기반 병합은
오탐 위험이 크다. source-scoped identity와 provenance를 유지해 향후
canonical layer를 추가할 수 있게만 한다.

## 결과

예상 장점:

- 중앙정부 API와 향후 지역 crawler가 같은 검색 계약 사용
- 천안·충남·전국·미확인·타 지역의 결정적 판정
- Source 누락을 숨기지 않는 검색 이유와 미확인 조건
- 행정구역 변경과 별칭의 추적 가능성
- 사용자 표시 DTO와 검색 index의 책임 분리

예상 비용:

- Normalized Schema·Fixture·Seed 공동 검토
- Alembic Migration, 기준정보 생성과 PostgreSQL 관계 테스트
- Importer transaction과 projection 동기화 복잡도 증가
- Backend·Frontend 소비 계약 재검증

호환성:

- 기존 `(source_id, external_id)`와 provenance를 유지한다.
- 기존 공개 목록·상세는 additive 또는 내부 전용 변경을 우선한다.
- breaking contract가 필요하면 version과 Migration 영향을 명시한다.

## 검증 방법

- Schema·Python 모델·Fixture·Seed field set과 enum 검증
- 빈 DB·populated DB Migration upgrade·downgrade
- region parent·alias·validity의 고아·중복·순환 검사
- 전국·상위·정확·타 지역·미확인·exclude PostgreSQL 통합 테스트
- DT1 실제 Raw의 오프라인 재처리
- Importer idempotency·rollback과 search projection 동기화
- 기존 Policy API·Frontend 타입 회귀
- 합성 규모 `EXPLAIN (ANALYZE, BUFFERS)` 기록

## 후속 작업

- Integration 03 PSF0에서 Data·Backend·Frontend 공동 검토
- 채택 후 데이터 Schema·정규화·DB·API 기준 문서 갱신
- Data 02 DT2에서 검색 노출 의미와 Backend 06 계약 승인
- 별도 지역 Source Forest에서 공식 웹사이트 crawler 구현

