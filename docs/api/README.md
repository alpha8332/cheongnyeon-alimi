# API 문서

이 디렉터리는 프론트엔드, 외부 클라이언트와 운영 도구가 사용하는 API 계약을
관리한다.

## 포함하는 내용

- 엔드포인트, HTTP 메서드와 인증 요구사항
- 요청 파라미터와 요청·응답 Schema
- 상태 코드와 오류 응답
- 페이지네이션, 필터, 정렬과 사용 예시
- 호환성을 깨는 변경과 전환 방법

## 포함하지 않는 내용

- 구현 전 API 초안: `docs/development/develop_plan/`
- 데이터 수집 원문과 정규화 규칙: `docs/data/`
- 내부 서비스와 Repository 구현 상세: `docs/development/`

API 문서는 실제 구현 및 자동화된 Schema와 일치해야 한다. 엔드포인트가
구현되기 전에는 빈 문서나 확정된 계약처럼 보이는 예시를 만들지 않는다.

## 현재 API 계약

- [Policy API](policies.md): 정책 목록·상세, pagination, 정확한 배열 필터,
  품질 노출과 오류 계약
- [관리자 인증 API](admin_access.md): 관리자 PIN 세션 생성 및 토큰 인증/권한 계약
- [CollectionRun 관리자 API](admin_collection_runs.md): CollectionRun 실행 이력 목록·상세, 수동 수집 실행 및 stale 판정 계약
- [관리자 정책 데이터 표 API](admin_policies.md): 관리자 읽기 전용 정책 데이터 표 목록·상세, 페이징 및 Allowlist 정렬 계약
- [관리자 로그 및 감사 API](admin_logs.md): 관리자 서버 로그 파일/이벤트 조회, 회전 archive 삭제 및 Audit 감사 기록 계약
- [맞춤 정책 추천 API](recommendation.md): 결정적 맞춤 정책 추천, 부합도 점수, 추천 사유 및 비단정 계약
