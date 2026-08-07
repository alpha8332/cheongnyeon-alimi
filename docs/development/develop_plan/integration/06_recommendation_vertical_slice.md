# Integration 06 Recommendation Vertical Slice Forest 개발 계획

## 계획 정보

- 번호: Integration 06
- 담당 영역: Backend·Frontend
- 상태: draft
- 계획일: `2026-08-07`
- 대상 Release: `v0.5.0`
- 선행 Forest: Integration 05 Contract Baseline, Integration 08의 승인 조건 계약
- 후속 Forest: Integration 07 Release 2 Feature Acceptance
- 권장 브랜치: `feature/backend/recommendation`, `feature/frontend/recommendation`

## 목적

사용자 조건을 기존 결정적 검색·판정 기반에 적용해 추천 정책, 구조화된 이유와
미확정 조건을 반환하고 실제 UI까지 연결한다. 추천은 자격 충족이나 수혜
가능성을 확정하지 않는다.

## 범위

- 승인된 사용자 조건과 추천 request·response DTO
- 기존 지역·연령·카테고리·신청상태 판정 primitive 재사용
- Integration 08의 구조화된 조건·확인 필요 의미 재사용
- 요청 내부 추천 순서와 결정적인 동률 처리
- 추천 이유, 제외 이유와 데이터로 확인할 수 없는 조건
- 검색 결과와 추천 결과의 의미·route 구분
- Mock 소비 테스트, 실제 PostgreSQL API와 Browser E2E
- API 오류·재시도 토스트와 자격 비확정 안내

## 범위 밖

- ML·LLM·embedding·vector DB
- 사용자 행동 학습과 개인 프로필 서버 저장
- 서로 다른 요청의 점수 비교와 자격 확률 표시
- 정책 데이터에 없는 조건을 추정하거나 자동 보강
- 자격요건 Source 수집·구조화와 정책 상세 조건 UI 구현

## 선행 조건

- Integration 05의 `W4-G0_APPROVED`와 Integration 08의 조건 구조·비단정
  문구 소비 검토가 완료돼야 한다.
- 기존 검색 판정 primitive와 Release 1 golden 회귀가 통과하는 기준선을 쓴다.
- 추천 평가에 사용할 실제·경계 표본과 기대 이유가 승인돼야 한다.

## 공통 설계 원칙

- 같은 입력과 snapshot은 같은 순서와 이유를 반환한다.
- 추천 점수는 자격 확률이나 요청 간 절대 점수로 사용하지 않는다.
- Source에 없는 자격 조건을 추정하지 않고 미확정 조건으로 반환한다.
- Backend 의미와 Frontend 표시가 달라지면 공동 계약부터 갱신한다.

## Slice 계획

### R0 - 계약 소비와 평가 표본

- W4-G0 추천 계약을 Backend Schema와 Frontend 타입 초안으로 대조한다.
- 실제·경계 표본에 기대 이유·미확정·제외 결과를 고정한다.

### R1 - Backend 결정적 추천

- 승인된 조건을 기존 판정 primitive에 연결한다.
- 안정적인 정렬, 이유와 미확정 조건을 API로 제공한다.
- PostgreSQL 단위·통합·성능 회귀를 추가한다.

### R2 - Frontend 추천 UI

- 조건 입력·수정, loading·empty·error·partial 상태를 제공한다.
- 추천 이유와 확인 필요 조건을 숫자보다 우선해 표시한다.
- 긴 지역 목록 축약과 API 오류·재시도 UX를 함께 검증한다.

### R3 - 실제 세로 인수

- 실제 snapshot DB → FastAPI → React 추천 목록·상세를 검증한다.
- 추천이 자격을 단정하지 않고 Source·수집 시각을 유지하는지 확인한다.

## Forest 완료 기준

- 같은 입력·snapshot에서 추천 순서와 이유가 결정적임
- 정책 identity, 이유, 제외·미확정 조건과 날짜 상태가 API·UI에서 일치함
- loading·empty·error·partial과 긴 지역 목록이 Browser에서 검증됨
- 실제 PostgreSQL 추천 E2E와 기존 검색 회귀가 통과함
- 구현·검증 결과가 대응 개발 기록과 API 문서에 반영됨

## 검증 계획

```powershell
$env:TEST_DATABASE_URL = '<dedicated-postgresql-test-url>'
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q
Set-Location frontend
npm run test
npm run lint
npm run build
npm run test:e2e
Set-Location ..
python scripts/validate_docs.py
git diff --check
```

실제 실행하지 않은 명령은 개발 기록에 통과로 적지 않는다.

## 위험과 미확정 사항

- 기존 검색 score를 추천 score로 그대로 노출하면 자격 가능성으로 오해될 수
  있어 W4-G0에서 공개 필드와 UI 구간을 확정해야 한다.
- Backend가 관리자 Critical Path와 추천을 함께 맡으므로 새 평가 엔진이나
  비필수 endpoint를 추가하면 4주차 일정이 지연될 수 있다.
- 실제 데이터 분포 변화로 기대 순위가 달라질 수 있어 고정 snapshot 회귀와
  actual 재검증을 구분해야 한다.

## 관련 문서

- [v0.5.0 Contract Baseline](05_v0_5_0_contract_baseline.md)
- [Eligibility Evidence and Summary](08_eligibility_evidence_summary.md)
- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
- [Policy Search 계획](../backend/06_policy_search.md)
- [Policy API 계약](../../../api/policies.md)
