# 역할과 책임

## 목적

이 문서는 프로젝트의 책임 경계를 정의한다. 실제 담당자는 GitHub Issue와
Pull Request에서 확인하며, 한 사람이 여러 역할을 맡아도 검증 대상과 승인
근거는 분리한다.

## Data

- 공식 API·공개 웹 Source와 이용·재배포 조건 조사
- Raw envelope, Extractor, Normalizer, Validator와 JSON Schema 관리
- 지역·연령·분야·기간·생명주기 판정과 근거 보존
- 공개 dataset 후보 생성, row·hash·identity와 품질 검증
- 개인정보·비밀정보와 공개 불가 원문 제외

Data 변경은 `docs/data/`, 관련 Collector 테스트와 공개 dataset Gate를 함께
갱신한다. Source를 수집할 수 있다는 사실만으로 재배포를 승인하지 않는다.

## Backend

- FastAPI endpoint, Service·Repository와 PostgreSQL 모델 관리
- Migration, transaction, 동시성·멱등성과 rollback 경계 관리
- 검색·추천·상세의 결정적 판정과 활성 dataset projection 적용
- 관리자 인증, 수집 queue, CollectionRun, 품질·정책·로그 API 보호
- 구조화 로그 allowlist와 비밀정보 차단

Backend는 Raw 수집 규칙을 API route에 복제하지 않고 `collectors/` 계약을
사용한다.

## Frontend

- React 사용자·관리자 화면과 API client·type 관리
- 로딩·빈 결과·오류·partial·inactive 상태 표현
- 모바일 반응형, 키보드, focus, label과 색상 외 상태 표현
- 프로필·즐겨찾기 localStorage schema와 복구 경계 관리
- 추천 이유, 미확정 정보와 공식 원문 확인 동선 제공

Frontend는 신청 자격을 자체 추정하지 않고 Backend의 근거·미확정 계약을
사용한다.

## Integration·Release

- Data → DB → API → UI 계약 연결과 회귀 범위 결정
- Compose 서비스, 네트워크, Volume, health와 clean-room 재현 검증
- branch·PR·CI·tag·Release 순서와 공급망 증거 관리
- 공개 dataset과 image receipt의 version·digest 대조
- README, 제품·아키텍처·운영·제출 문서의 현재성 확인

환경 간 동등성은 CollectionRun 개수가 아니라 활성 dataset version, row count와
identity hash로 판정한다.

## QA·사용성 검토

- 실제 Browser에서 사용자·관리자 주요 흐름 재현
- 검색·필터·추천·상세·개인 기능과 관리자 보호 route 검증
- 날짜·지역·연령·한국어 문구와 데이터 근거 대조
- 모바일·키보드·접근성과 오류·빈 결과·느린 응답 확인
- Git clone·Download ZIP과 새 Volume 실행 결과 기록

QA는 실행하지 않은 항목을 통과로 표시하지 않고, 결함은 URL·재현 절차·기대·
실제 결과와 증거를 남긴다.

## Documentation·Report

- 사용자에게 필요한 README와 기능 설명 정리
- 현재 코드·Compose·manifest 기준으로 수치와 구조 대조
- 대회 제출 체크리스트, 대표 화면과 성과 근거 관리
- 중복된 계획·작업 일지를 권위 문서에 흡수한 뒤 정리

보고 문서는 기능 완료를 대신 승인하지 않으며 실제 CI·QA·Release 영수증을
근거로 사용한다.

## 공통 완료 기준

- 변경 코드와 계약 문서가 일치한다.
- 관련 자동 테스트와 필요한 실제 Browser 검증을 실행했다.
- API key, PIN, DB 비밀번호, 개인정보와 Raw 원문이 노출되지 않는다.
- 기존 데이터와 Volume 보존·rollback 영향을 확인했다.
- 사용자에게 의미 있는 변경을 `CHANGELOG.md`에 반영했다.
- PR이 브랜치 전략과 리뷰 정책을 따른다.
