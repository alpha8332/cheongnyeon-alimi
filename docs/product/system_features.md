# 청년정책알리미 기능 총정리

## 문서 정보

- 기준: `v1.0.2`과 현재 `Unreleased` 관리자 개선
- 확인일: 2026-08-26
- 역할: 전체 기능을 빠르게 찾는 제품 기능 요약·색인

이 문서는 기능의 존재와 위치만 요약한다. 동작 원리, 판정 기준, 예외 상태와
데이터 경계는 각 기능별 상세 설명서를 따른다.

## 서비스 목적

청년정책알리미는 여러 공공기관의 정책을 공통 형식으로 정리해 사용자가 지역,
연령, 관심 분야와 검색어에 맞는 청년정책을 찾고 비교할 수 있게 하는 오픈소스
웹 프로그램이다. 일반 사용자는 회원가입이나 원본 Source API key 없이 실행할
수 있다.

## 일반 사용자 기능

| 기능 | 화면 | 설명 | 상세 문서 |
| --- | --- | --- | --- |
| 홈·자연어 검색 | `/`, `/programs` | 검색어와 지역·연령·분야 조건으로 정책 탐색 | [검색과 정책 탐색](features/search_and_discovery.md) |
| 정책 상세 | `/programs/{id}` | 신청 조건, 혜택, 기간, 미확정 정보와 공식 원문 확인 | [정책 상세와 자격정보](features/policy_detail_and_eligibility.md) |
| 맞춤 추천·프로필 | `/recommendations`, `/profile` | 저장한 지역·연령·복수 관심 분야 기반 추천과 이유 | [맞춤 추천과 프로필](features/recommendations_and_profile.md) |
| 즐겨찾기·일정 | `/favorites`, `/calendar`, `/notifications` | 폴더형 즐겨찾기, D-Day, 달력, 내부 마감 알림 | [즐겨찾기·달력·알림](features/favorites_calendar_notifications.md) |

## 관리자 기능

| 기능 | 화면 | 설명 | 상세 문서 |
| --- | --- | --- | --- |
| 인증·보안 | `/admin/login`, `/admin/security` | 4자리 PIN, 보호 route, 세션, PIN 변경·분실 복구 | [관리자 인증과 보안](features/admin_access_and_security.md) |
| 수집 운영 | `/admin`, `/admin/collectors`, `/admin/runs` | 수집기·queue·worker·스케줄과 CollectionRun 확인·수동 실행 | [관리자 수집 운영](features/admin_collection_operations.md) |
| 품질·정책·로그 | `/admin/quality`, `/admin/policies`, `/admin/logs` | 데이터 품질, 정책 DB, 구조화 로그의 안전한 조회 | [관리자 데이터 품질과 감사](features/admin_data_quality_and_logs.md) |

## 데이터 기능

| 기능 | 설명 | 상세 문서 |
| --- | --- | --- |
| 공개 dataset | API key 없는 최초 실행, 활성 dataset membership과 환경 간 동일 결과 | [공개 dataset과 데이터 생명주기](features/public_dataset_and_data_lifecycle.md) |
| 중앙 수집 | 공식 Source 수집, 정규화·검증, 공개 허용 범위 판정과 승격 | [공개 dataset과 데이터 생명주기](features/public_dataset_and_data_lifecycle.md) |

## 현재 공개 데이터

2026-08-25에 검증한 `v1.0.2` 공개 dataset은 총 2,052건이다.

| Source | 정책 수 |
| --- | ---: |
| 복지로 중앙부처 복지서비스 | 461건 |
| 온통청년 청년정책 API | 1,587건 |
| 인천광역시 청년공간 유유기지 공개 파일 | 4건 |

기준 version은 `public-bootstrap-20260824-897152e7a18c15`이다. 이후 latest
pointer가 승격되면 새 manifest의 version과 정책 수를 우선한다.

## 공통 원칙

- 검색과 추천은 신청 자격이나 선정 가능성을 확정하지 않는다.
- 확인할 수 없는 조건은 임의로 채우지 않고 미확정으로 표시한다.
- 프로필과 즐겨찾기는 현재 브라우저에만 저장되며 다른 PC와 동기화되지 않는다.
- 관리자 PIN, token, API key, DB 비밀번호와 Raw 원문은 화면·문서에 노출하지
  않는다.
- 사용자 API는 활성 공개 dataset의 정책만 반환한다.
- 수동 수집 결과는 검증·승격 전까지 사용자 검색에 자동 공개되지 않는다.
- CollectionRun은 로컬 감사 기록이므로 PC마다 개수가 달라도 정상이다.

## 현재 제한사항

- 일반 사용자 계정과 서버 기반 프로필·즐겨찾기 동기화는 제공하지 않는다.
- 알림은 웹 내부 기능이며 push·이메일·문자를 발송하지 않는다.
- 외부 캘린더 자동 동기화 대신 `.ics` 다운로드를 제공한다.
- 공식 Source 변경은 중앙 검증과 새 dataset 승격 뒤에 반영된다.
- one-command clean-room 실행은 Windows 10/11과 Docker Desktop 기준으로
  검증됐다.

## 기능 문서 읽는 순서

1. 일반 사용자는 [검색과 정책 탐색](features/search_and_discovery.md)부터 읽는다.
2. 추천 결과의 의미는 [맞춤 추천과 프로필](features/recommendations_and_profile.md)에서 확인한다.
3. 관리자는 [관리자 인증과 보안](features/admin_access_and_security.md)과
   [관리자 수집 운영](features/admin_collection_operations.md)을 함께 확인한다.
4. 작성자 DB와 심사자 DB의 차이는
   [공개 dataset과 데이터 생명주기](features/public_dataset_and_data_lifecycle.md)를 따른다.

전체 제품 기능 문서 색인은 [제품 기능 문서 안내](README.md)에서 확인한다.

