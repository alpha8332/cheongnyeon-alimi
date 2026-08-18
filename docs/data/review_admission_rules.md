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
4. checkpoint의 과거 상태를 신뢰하지 않고 실행 기준일의 regional Gate로
   item-level 지역 근거와 현재 신청 가능 근거 재평가
5. Normalizer 결과가 `valid` 또는 `partial`이고 residual unknown이 보존되는지
   확인
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

`database.policy_count`는 승격 전 기준선 수다. 이미 같은 manifest의
`promote_partial` identity가 존재하는 post-admission DB에서 audit를 다시 실행하면
그 identity 수를 현재 Policy 수에서 제외한다. 따라서 최초 적용 전과 멱등 재적용
후에 생성한 manifest가 같은 기준선 의미를 유지하며, apply는 전체 Policy 수에서
이미 존재하는 승격 identity를 뺀 값과 이를 대조한다.

## RA2·RA3 실제 기준선

`2026-08-19` 최종 감사에서 지역 review 1,140건은 `promote_partial` 3건,
`hold_review` 1,071건, `exclude_closed` 66건으로 판정됐다. 외부 duplicate
producer의 보류 2건도 별도 기록했다. 사전 후보였던 경북 `1009`는
`same_title_with_incomplete_comparison_evidence`로 보류했다. 대구 `8187`과
`8375`는 각각 8월 18일과 8월 14일에 종료돼 최종 승격에서 제외했다.

최종 manifest SHA-256은
`d6d781aaefa41e12a73d6f868fd5f291e83dc41e7930382441467795e9f4fdad`다. 변경 전
dump를 복원한 PostgreSQL 18 scratch DB에서 첫 적용 `inserted 3`, 동일 manifest
재적용 `unchanged 3`, canonical region rule·search projection 3건과 cleanup 후
3,270건을 확인했다.

RA3 서비스 DB 첫 적용은 `inserted 3`, 두 번째는 `unchanged 3`이었으며 최종
Policy는 3,273건이다. 대구 `8357`과 강원
`A2026010600300200900600001`은 `partial`, 경남 `2091`은 `valid`다. 세 정책 모두
`open`, `regional`, matched canonical region rule과 search projection을 가진다.
