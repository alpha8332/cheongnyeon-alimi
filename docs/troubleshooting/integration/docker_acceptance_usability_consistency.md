# Docker Acceptance 사용성·판정 일관성 복구

## 문제 상황

2026-08-23 DEP5 사용성 리뷰와 QA를 역할별 Compose project·Volume에서 대체
수행하던 중 실제 snapshot UI에서 다음 문제가 재현됐다.

1. 홈 예시 `천안시 24세 청년 지원금`이 알려진 인천 지역 정책
   `군복무 인천청년 상해보험 지원`을 첫 결과로 표시했다. 카드에는 인천 지역이
   명시됐지만 조건 분석은 천안을 `미확인`으로 표시했다.
2. 정책 `3342`의 수집 placeholder가 카드에 `0세 ~ 0세`로 노출됐다.
3. 연령 제한이 없는 추천 정책은 이유에 `만 24세 부합`, 카드에는
   `연령 정보 없음`으로 서로 다르게 표시됐다.
4. 저장 조건이 `24세·주거`인 상태에서 예시 `천안 취업`을 누르면 저장된 주거
   분야가 검색어의 취업 의도를 덮었다.
5. actual Browser 회귀에서 Mock-first 주차 통합 경로가 합성 정책명과 PIN
   `0000`을 그대로 요구해 제품과 무관한 3건 실패를 만들었다.

## 실제 원인

지역 판정기는 active include rule과 retired rule이 섞인 정책에서 retired rule을
하나라도 발견하면 모든 다른 지역 질의를 `unknown`으로 처리했다. 인천 정책의
retired 중구·동구·서구 rule 때문에 충남 천안 질의까지 미확정이 된 것이다.

연령 화면은 `0/0` numeric sentinel과 같은 내용의 `age_condition_text`를 실제
연령 범위로 표시했고, 추천 DTO는 `unrestricted` 판정 이유를 일반 연령 일치와
같은 code·문구로 축약했다. 검색 조건 merge는 URL flat category가 없으면
자연어에 분야가 이미 있어도 저장 category를 항상 명시 filter로 보냈다.

주차 회귀 spec은 파일 주석대로 Mock-first였지만 actual 모드 skip 경계가 세
Critical Path에 적용되지 않았다.

## 해결

- retired·unresolved 지역 rule의 province를 행정구역 hierarchy로 증명하고,
  질의 province와 다른 unresolved rule은 해당 질의의 미확정 근거에서 제외했다.
  active include가 있고 같은 province의 미해결 rule이 없으면 다른 province는
  결정적으로 `mismatch`다. province를 증명할 수 없는 rule은 계속 `unknown`이다.
- `age_min=0`, `age_max=0`은 검색 판정에서 unknown, 사용자 카드에서는
  `연령 정보 없음`으로 처리했다.
- 추천의 연령 제한 없음은 `AGE_UNRESTRICTED`와 `연령 제한 없음`으로 분리해
  이유와 카드 표시를 일치시켰다.
- 자연어에 Backend category taxonomy 키워드가 있으면 저장 category를 flat
  filter로 합치지 않고 자연어 의도를 우선했다. 지역·연령 저장 조건은 유지한다.
- 홈 예시는 실제 상단에 지역 정책이 나오는 `천안 취업`으로 교체했다.
- Mock-first 주차 경로는 actual 모드에서 이유를 남기고 skip하며, actual 전용
  검색·추천·자격·사용자 서비스 spec과 관리자 API·Browser 검증을 별도로 쓴다.
- 관리자 대시보드의 `run_id`, `source`, `started_at` 등은 한국어 의미와 API
  필드명을 함께 표시했다.

## 확인 결과

- 천안 질의에서 정책 `3649` 인천 known-region 누출: `1건 → 0건`
- 정책 `3342` age verdict: 확정 mismatch가 아니라 `unknown`
- 추천 정책 `3162`: 이유와 카드 모두 `연령 제한 없음`
- 저장 분야가 주거여도 `천안 취업`은 `카테고리: 취업`, 주거 chip 없음
- `0세 ~ 0세` 사용자 카드 노출 없음
- actual 전용 5개 spec 최종 실행: 39 pass, 11 명시 skip, 0 fail
- Mock-first actual 경계 수정 후 주차 spec: 3 pass, 3 명시 skip, 0 fail
- Frontend unit: 220 pass

최종 전체 회귀 수치는 DEP5 개발 기록에 별도로 고정한다. 이 기록은 commit 전
수정 worktree에서 실제 재현·수정한 내용이며 새 receipt 검증을 대신하지 않는다.

## 예방 규칙

- `unknown`은 근거가 없는 범위에만 전파하고, hierarchy로 다른 province임을
  증명할 수 있는 정책을 지역 후보에 남기지 않는다.
- sentinel과 실제 무제한 조건을 같은 문구·reason code로 합치지 않는다.
- 저장 조건보다 사용자가 현재 자연어에 명시한 조건을 우선한다.
- Mock과 actual spec은 실행 모드를 코드로 분리하고 skip 이유를 결과에 남긴다.
