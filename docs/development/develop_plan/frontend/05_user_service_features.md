# Frontend User Service Features Forest 개발 계획

## 계획 정보

- 번호: Frontend 05
- 담당 영역: Frontend
- 상태: draft
- 계획일: `2026-08-07`
- 대상 Release: `v0.5.0`
- 선행 Forest: Integration 05 Contract Baseline
- 후속 Forest: Integration 07 Release 2 Feature Acceptance
- 권장 브랜치: `feature/frontend/user-service-features`

## 목적

일반 사용자 계정 없이 브라우저에 최소 조건과 즐겨찾기를 저장하고, 정책의
신청 종료일을 기반으로 D-Day·앱 내부 알림·`.ics` 다운로드를 제공한다.

## 범위

- versioned localStorage 사용자 조건과 즐겨찾기
- 저장 데이터 검증, 손상 복구, version 불일치 초기화와 전체 삭제
- 정책 identity 기반 즐겨찾기 추가·해제
- `Asia/Seoul` 기준 D-Day와 날짜 미상·상시·마감 상태
- 즐겨찾기 정책의 앱 내부 마감 임박 알림
- 정책별 `.ics` 생성·다운로드와 안전한 텍스트 escaping
- 검색·추천·상세 route 간 상태 일치
- loading·empty·error·partial, 키보드·모바일 기본 검증

## 범위 밖

- 회원가입·로그인·서버 저장과 다중 기기 동기화
- 외부 push·이메일·SMS와 Service Worker 알림
- 외부 캘린더 계정 OAuth·자동 등록
- Source에 종료일이 없는 정책의 임의 D-Day 생성

## 선행 조건

- Integration 05의 `W4-G0_APPROVED`와 localStorage·날짜 계약이 필요하다.
- Policy identity와 신청기간 상태의 현재 API 의미를 확인한다.
- 지원 Browser와 `.ics` 다운로드 검증 방법을 합의한다.

## 공통 설계 원칙

- 저장 데이터는 최소화하고 사용자가 한 번에 초기화할 수 있게 한다.
- 날짜 미상·상시 정책에 임의 마감일을 만들지 않는다.
- localStorage 오류가 검색·상세 기본 기능을 막지 않게 격리한다.
- 앱 내부 알림은 외부 전송이나 background notification을 의미하지 않는다.

## Slice 계획

### U0 - 로컬 저장 계약

- key, schema version, 허용 필드와 최대 저장 범위를 고정한다.
- 잘못된 JSON·구버전·삭제·브라우저 저장소 실패를 테스트한다.

### U1 - 조건과 즐겨찾기

- 조건 저장·복원·초기화와 즐겨찾기 추가·해제를 구현한다.
- 목록·추천·상세에서 같은 정책 identity를 사용한다.

### U2 - D-Day와 내부 알림

- KST 날짜 경계, 오늘·마감·상시·미상 상태를 구현한다.
- 즐겨찾기 중 마감 임박 정책을 앱 내부에서만 계산한다.

### U3 - 캘린더와 Browser 인수

- `.ics` 필수 필드·시간대·escaping을 검증하고 다운로드를 제공한다.
- mobile, keyboard, loading·empty·error·partial과 실제 API 회귀를 확인한다.

## Forest 완료 기준

- 새로고침 후 조건·즐겨찾기가 계약대로 복원됨
- 손상·구버전 저장 데이터가 안전하게 복구 또는 초기화됨
- D-Day·알림이 KST와 Source 날짜 경계를 지키고 날짜를 추정하지 않음
- `.ics`가 대표 정책과 특수문자 표본에서 유효하게 생성됨
- localStorage 외 서버·로그·URL에 사용자 조건을 영구 저장하지 않음
- Frontend unit·lint·build·Browser 검증과 문서 검증 통과

## 검증 계획

```powershell
Set-Location frontend
npm run test
npm run lint
npm run build
npm run test:e2e
Set-Location ..
python scripts/validate_docs.py
git diff --check
```

## 위험과 미확정 사항

- localStorage key·version·최대 저장량과 migration 정책은 W4-G0 전 미확정이다.
- `.ics`의 all-day event와 마감일 포함 범위는 캘린더별 해석 차이가 있어 대표
  client에서 확인해야 한다.
- Source 신청기간이 null인 정책은 D-Day·알림 대상에서 제외해야 하며 임의
  보강은 Data 계약 변경 없이는 허용하지 않는다.

## 관련 문서

- [v0.5.0 Contract Baseline](../integration/05_v0_5_0_contract_baseline.md)
- [Recommendation Vertical Slice](../integration/06_recommendation_vertical_slice.md)
- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
- [Policy API 계약](../../../api/policies.md)
