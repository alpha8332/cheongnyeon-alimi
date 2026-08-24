# 대회 제출 문서

이 디렉터리는 오픈소스 개발대회 출품과 시연에 필요한 자료를 관리한다.

## 포함하는 내용

- 결과보고서 원고와 근거 자료
- 시연 시나리오와 발표 준비
- 제출 체크리스트
- 화면 캡처 및 성과 자료의 관리 기준
- SBOM과 오픈소스 라이선스 제출 자료

## 포함하지 않는 내용

- 일상적인 개발 기록: `docs/development/`
- 제품 기능의 미확정 계획: `docs/development/develop_plan/`
- 현재 시스템 계약의 기준 문서: `docs/architecture/`, `docs/api/`,
  `docs/data/`

제출 양식과 증빙 파일이 확정되었을 때 필요한 하위 문서를 생성한다. 대용량
영상, 빌드 산출물과 자동 생성 파일은 저장소 포함 여부를 먼저 검토한다.

## 역할과 근거

보고서 담당은 1주차부터 개발 기록, 실제 테스트 결과, 화면과 데이터 품질
통계를 주차별로 연결하고 6주차에 최종보고서·시연·제출 자료를 완성한다.
구현 완료와 릴리스 통과는 보고서 담당이 대신 승인하지 않으며 Team Leader,
사용성 리뷰어와 QA가 제공한 실제 증거를 사용한다.

상세 주차별 책임은
[주차별 실행 계획](../development/develop_plan/weekly_delivery_plan.md),
역할 겸임과 독립성 기준은
[역할과 책임](../governance/role_assignment.md)을 따른다.

## 현재 Release 증거

- [프로젝트 MIT License](../../LICENSE): 코드 사용·복제·수정·배포 조건. 정책
  dataset의 재배포 조건은 별도 Source 계약을 따른다.
- [Release 1 검증 증거 안내](release_1_evidence_guide.md): DT7E 경량 QA·사용성 수행 절차와 정합성 검증
- [Release 1 수동 증거 템플릿](release_1_evidence_template.json): 현재 contract hash·actual snapshot에 고정된 작성 시작점
- [Release 1 기술 증거](release_1_technical_evidence.json): 실제 PostgreSQL 검색 acceptance의 안전한 JSON 결과
- [Release 1 경량 리뷰 근거](release_1_review_summary.md): 제공된 Word 리뷰의
  QA·사용성 관찰과 `v0.5.0` 비차단 후속사항
- [Release 1 수동 증거](release_1_evidence.json): 경량 QA·사용성 판정의
  contract 고정 JSON
- [Release 1 Gate 결정](release_1_gate_decision.json): Team Leader의 G4
  `pass`, 비차단 후속과 릴리스 publication 상태

템플릿 자체는 Gate 통과를 뜻하지 않는다. 실제 QA·사용성 결과는
`release_1_evidence.json`에 기록했고 Team Leader가 DT7F에서 기술 증거와
대조해 Gate G4를 `pass`로 판정했다.
