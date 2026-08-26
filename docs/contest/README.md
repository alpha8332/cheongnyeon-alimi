# 오픈소스 개발대회 제출 문서

이 디렉터리는 심사자가 현재 제출 후보의 재현성, 기능, 데이터 경계와 공개
준비 상태를 빠르게 확인할 수 있는 최종 자료만 관리한다. 초기 릴리스별 Gate
기록과 주차별 진행 자료는 현재 계약과 최종 검증 문서에 흡수한 뒤 제외했다.

## 제출 자료

- [최종 제출 체크리스트](open_source_submission_checklist.md): 공개 저장소,
  clean-room 실행, 데이터 동등성, QA와 남은 외부 확인 항목
- [프로젝트 README](../../README.md): 설치, 실행, 핵심 기능과 제한사항
- [제품 기능 문서](../product/README.md): 기능별 원리와 사용자·관리자 경계
- [v1.0.2 QA 개선 기록](../troubleshooting/integration/v1_0_2_qa_improvements.md):
  2,052건 공개 dataset, 지역 검색, 복수 분야와 추천 개선의 실제 검증
- [Production 배포 기록](../operations/production_delivery.md): image, SBOM,
  provenance와 공개 dataset 발행 구조

## 제출 시 권위 기준

- 코드 라이선스: 루트 `LICENSE`
- 데이터 재배포 범위: `docs/data/public_policy_dataset.md`
- 현재 공개 정책 집합: `dataset-latest`가 가리키는 manifest
- 설치 절차: `docs/operations/docker_first_run.md`
- 변경 이력: 루트 `CHANGELOG.md`

영상, 발표자료, 원본 정책 payload, DB dump, 실제 비밀정보와 개인 PC 전용
검증 산출물은 공개 저장소에 포함하지 않는다.
