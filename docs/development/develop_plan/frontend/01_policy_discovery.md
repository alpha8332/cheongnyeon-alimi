# Frontend Policy Discovery Forest 개발 계획

## 계획 정보

- 상태: completed
- 담당 영역: Frontend
- Forest: Policy Discovery
- 브랜치: `feature/frontend/policy-discovery`

## 목적

Data Pipeline Forest가 제공한 canonical Seed와 Backend의 공개 `PolicyDto`
계약을 Frontend 타입·Mock·API Client·와이어프레임 UI로 소비하고, 정책
검색·목록·상세 화면의 기본형 구현을 완료한다.

## 범위

- TypeScript 타입과 Seed Mock 바인딩
- `/api/v1/policies` 목록·상세 API Client와 Mock 계약 통일
- pagination envelope, 숫자 `id`와 partial opt-in 소비
- 정책 카드, 목록, 검색·필터, 상세 페이지 와이어프레임 UI
- Loading / Empty / Error 상태 처리
- Data 6 Frontend 공동 계약 검토 기록

## 범위 밖

- 인증이 필요한 Backend API와 관리자 전용 provenance API
- 즐겨찾기, 알림, 캘린더
- 디자이너급 UI 스타일링
- Schema·Fixture·Seed 변경

## 선행 조건

- `develop`에 Data Pipeline Foundation과 Frontend Foundation 병합
- `data/seeds/initial_programs.json`과 `normalized_program.schema.json` 1.0.0
  사용 가능

## 공통 설계 원칙

- 최종 데이터 경로는 Backend API이며 Mock은 동일 계약을 유지한다.
- 선택 단일 값은 null, 복수 값은 빈 배열을 그대로 소비한다.
- 와이어프레임 수준의 Card·Border·기본 텍스트 UI만 사용한다.

## Slice 계획

| Slice | 상태 | 내용 |
| --- | --- | --- |
| FE 1 | completed | Frontend Foundation: 라우터, 레이아웃, 기본 UI |
| FE 2 | completed | Policy Discovery: 타입, Mock, 목록·상세·필터 UI |
| FE 2A | completed | 공개 Policy API 계약 정합화와 소비 테스트 |

## 검증 계획

- `npm run build`와 `npm run lint`
- canonical Seed → 공개 DTO Mock 소비와 provenance·invalid 비노출
- 기본 valid 2건, partial opt-in 4건과 pagination·숫자 ID 확인
- Mock/실제 API 요청 경로와 query 계약 소비 테스트
- `python scripts/validate_docs.py`

## Forest 완료 기준

- 정책 타입·Mock·API Client·목록·상세·필터·예외 UI가 공개 Policy API
  계약과 일치
- Frontend 공동 계약 검토 기록과 개발 기록 작성
- 실제 Backend endpoint 연결은 `VITE_USE_MOCK=false`로 전환 가능

## 위험과 미확정 사항

- Node 기반 FE 2A build·lint·소비 테스트, 실제 PostgreSQL Policy API
  HTTP 검증과 실제 API 모드 홈·목록 브라우저 렌더링을 완료함
- 관리자 provenance 조회는 공개 Policy API 범위 밖이며 별도 인증·관리자
  API 계약이 필요
- `npm audit`이 client-only 앱에서 사용하지 않는 React Router RSC mode
  취약점 high 2건을 보고하며 호환 가능한 의존성 조정 여부를 별도로 검토

## 관련 문서

- [Fixture와 Seed 계약](../../../data/fixture_seed_contract.md)
- [데이터 Schema 기준선](../../../data/data_schema.md)
- [개발 기록](../../development_notes/frontend/policy_discovery.md)
