# 제품 기능 문서 안내

이 디렉터리는 현재 구현된 기능을 사용자와 운영자의 관점에서 설명한다.
개발 순서나 과거 구현 과정 대신 기능이 왜 존재하고 어떤 원리와 경계로
동작하는지 기록한다.

## 전체 요약

- [청년정책알리미 기능 총정리](system_features.md)

## 기능별 상세 설명

### 일반 사용자

- [검색과 정책 탐색](features/search_and_discovery.md)
- [정책 상세와 자격정보](features/policy_detail_and_eligibility.md)
- [맞춤 추천과 프로필](features/recommendations_and_profile.md)
- [즐겨찾기·달력·알림](features/favorites_calendar_notifications.md)

### 관리자

- [관리자 인증과 보안](features/admin_access_and_security.md)
- [관리자 수집 운영](features/admin_collection_operations.md)
- [관리자 데이터 품질과 감사](features/admin_data_quality_and_logs.md)

### 데이터

- [공개 dataset과 데이터 생명주기](features/public_dataset_and_data_lifecycle.md)

## 상세 문서 공통 구성

각 문서는 다음 순서로 설명한다.

1. 기능 목적과 사용자가 해결하는 문제
2. 화면과 주요 흐름
3. 기능이 결과를 만드는 원리
4. 저장·API·개인정보 경계
5. 빈 결과, 미확정, 오류 등 예외 상태
6. 현재 제한사항
7. 권위 계약과 관련 구현 문서
