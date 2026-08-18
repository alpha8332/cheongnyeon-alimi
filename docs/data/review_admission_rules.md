# Review Admission 규칙

## 적용 범위

`review-admission-v1`은 완료된 지역 checkpoint의 `review` 후보를 기존 수집
producer와 분리해 다시 판정한다. producer의 과거 outcome과 Raw는 바꾸지 않고,
승인된 identity만 기존 Normalizer·Importer에 전달한다.

규칙 버전은 `review-admission-v1`, 청년 대상 taxonomy는 `2.0.0`이다.

## 판정 순서

1. `(source_id, external_id)`, 공식 HTTP(S) URL과 Raw provenance 확인
2. checkpoint의 failed·closed·duplicate hard exclusion 확인
3. item 제목·대상·연령·category에서 taxonomy v2 표지 확인
4. item-level 지역 근거와 현재 신청 가능 근거 확인
5. Normalizer 결과가 `partial`이고 residual unknown이 보존되는지 확인
6. 현재 PostgreSQL aggregator 기준선에서 exact·URL·fingerprint 중복 판정
7. 모든 조건을 통과한 후보만 `promote_partial`

`hold_review`는 DB를 변경하지 않는다. `exclude_closed`, `exclude_duplicate`,
`exclude_invalid`, `exclude_failed`도 Importer에 전달하지 않는다.

## Taxonomy v2

- 직접 대상: 청년, 청소년, 대학생
- 가족·부모: 신혼부부, 예비신혼부부, 미혼모·미혼부, 청소년부모
- 돌봄·자립: 가족돌봄청년·청소년, 영케어러, 자립준비청년, 보호종료아동
- 취약·전환: 고립·은둔, 학교밖·가정밖·쉼터퇴소, 경계선지능, 장애·저소득·
  주거취약·다문화·탈북, 니트·구직단념·장기미취업, 전입·지역정착 청년
- 취업·교육: 취업준비생, 구직자, 미취업자, 졸업생·졸업예정자, 대학원생,
  학자금, 장학생, 사회초년생, 신입사원
- 가구·사업: 1인가구, 예비창업자, 초기창업, 스타트업, 귀농, 후계농,
  청년농업인·청년창업자
- 세대·병역: 정확한 2030세대, ROTC·사관후보생, 군복무, 전역자·전역청년

NFKC, 대소문자, 공백과 괄호 차이는 비교할 때 정규화한다. `2030세대`의 공백
변형은 인정하지만 단순 연도 `2030년`은 인정하지 않는다. taxonomy 표지는 청년
대상 조건만 충족하며 지역·현재성·중복·Schema 조건을 우회하지 않는다.

## 감사 manifest

감사 결과는 Git 제외 `runtime/decisions/review-admission-v1.json`에 저장한다.
manifest에는 rule·taxonomy·Git·Migration·checkpoint hash, identity, 원래 reason,
최종 판정, taxonomy 표지, residual unknown, provenance ID와 정규화 fingerprint만
기록한다. Raw payload, 정책 본문, credential과 개인 연락처는 복사하지 않는다.

[Review Admission Audit JSON Schema](../../data/schema/review_admission_audit.schema.json)가
실행 가능한 계약이다. apply 명령은 Schema와 manifest hash를 검증하고 같은
Raw·checkpoint·DB 기준선으로 manifest를 다시 만들 수 없으면 실패한다.

## RA2 실제 기준선

`2026-08-19` 감사에서 지역 review 1,140건 중 `promote_partial` 5건,
`hold_review` 1,135건으로 판정됐다. 외부 duplicate producer의 보류 2건도 별도
기록했다. 사전 후보였던 경북 `1009`는
`same_title_with_incomplete_comparison_evidence`로 보류했다.

변경 전 dump를 PostgreSQL 18 scratch DB에 복원한 뒤 5건의 Policy·region·search
projection write를 수행했고 transaction 전체 rollback 후 정책 수는 3,270건으로
유지됐다. 별도 멱등성 검증에서는 첫 적용 `inserted 5`, 같은 manifest 재적용
`unchanged 5`, 검증 identity 정리 후 3,270건을 확인했다. 이 결과는 실제 서비스
DB 적재 승인이 아니며 RA3 전에는 적용하지 않는다.
