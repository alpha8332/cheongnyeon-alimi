# Frontend Policy Discovery Forest 개발 계획

## 계획 정보

- 상태: in-progress
- 담당 영역: Frontend
- Forest: Policy Discovery
- 브랜치: `feature/frontend/policy-discovery`

## 목적

Data Pipeline Forest가 제공한 `NormalizedProgram` 1.0.0 Schema와 canonical
Seed를 Frontend 타입·Mock·와이어프레임 UI로 소비하고, 정책 검색·목록·상세
화면의 기본형 구현을 완료한다.

## 범위

- TypeScript 타입과 Seed Mock 바인딩
- 정책 카드, 목록, 검색·필터, 상세 페이지 와이어프레임 UI
- Loading / Empty / Error 상태 처리
- Data 6 Frontend 공동 계약 검토 기록

## 범위 밖

- Backend API 실연동과 인증
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
| FE 2 | in-progress | Policy Discovery: 타입, Mock, 목록·상세·필터 UI |

## 검증 계획

- `npm run build`와 `npm run lint`
- Seed 4건 Mock 소비 및 partial·null·빈 배열 UI 확인
- `python scripts/validate_docs.py`

## Forest 완료 기준

- 정책 타입·Mock·목록·상세·필터·예외 UI가 Seed 계약과 일치
- Frontend 공동 계약 검토 기록과 개발 기록 작성
- Backend API 연동은 후속 Slice에서 수행

## 위험과 미확정 사항

- Backend API 경로·응답 envelope는 아직 확정되지 않음
- Data 6 공동 승인은 Backend 검토 완료 후 최종 확정

## 관련 문서

- [Fixture와 Seed 계약](../../../data/fixture_seed_contract.md)
- [데이터 Schema 기준선](../../../data/data_schema.md)
- [개발 기록](../../development_notes/frontend/policy_discovery.md)
