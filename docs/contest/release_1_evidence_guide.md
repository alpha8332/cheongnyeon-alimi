# Release 1 독립 검증 증거 안내

## 목적

이 문서는 `v0.1.0` Gate G4의 DT7E에서 QA, 사용성 리뷰어와 보고서 담당이
동일한 실제 snapshot과 acceptance 계약을 독립적으로 검증하는 절차를 정한다.
합성 Seed나 Frontend Mock은 이 증거의 데이터 기준으로 사용하지 않는다.

기술 검증은 Team Leader가 준비할 수 있지만 각 독립 역할의 관찰·판정과
증거를 대신 작성하거나 승인하지 않는다. 세 역할의 증거가 모두 정합하더라도
Gate G4 최종 판정은 DT7F에서 별도로 수행한다.

## 고정 기준

| 항목 | 값 |
| --- | --- |
| Release / Gate | `v0.1.0` / `G4` |
| 실제 정책 수 | 3,156건 |
| 온통청년 snapshot | `6add34f7aad9456ab0abb19175b7621c` |
| 복지로 snapshot | `ffa74ef47e6048109f11bf40d1ac5e15` |
| acceptance contract SHA-256 | `c4d49caa90a8773a94e7e14b1e9dee30ebdfd3316d8144b9efc27ffd6462a327` |
| exact query | `천안 사는 27살 청년 단기숙소 지원 받을 수 있나?` |
| 기대 정책 | 온통청년 `20260430005400212969`, `청년단기숙소 지원사업` |

기준 계약은 [`data/release_1_acceptance.json`](../../data/release_1_acceptance.json),
작성 시작점은
[`release_1_evidence_template.json`](release_1_evidence_template.json)이다.
계약 hash나 snapshot identity가 다르면 기존 결과를 재사용하지 않고 Team
Leader에게 변경 이유와 재검증 필요 여부를 먼저 확인한다.

## 준비 절차

1. Team Leader는 현재 계약과 실제 PostgreSQL snapshot으로 기술 증거를 만든다.

   ```powershell
   python scripts/audit_release_1.py `
     --base-url http://127.0.0.1:8000 `
     --output docs/contest/release_1_technical_evidence.json
   ```

2. 템플릿을 `docs/contest/release_1_evidence.json`으로 복사한다. 원본 템플릿은
   수정하지 않는다.
3. QA, 사용성 리뷰어와 보고서 담당은 자신의 `reviews` 항목만 작성한다.
4. 모든 check는 실제 수행 뒤 `pass` 또는 `blocked`로 기록하고, 관찰 내용과
   검증 시 존재하는 저장소 상대 파일 경로 또는 검토 가능한 HTTP(S) URL을
   `evidence_refs`에 남긴다.
5. 다음 명령으로 snapshot·contract·query와 역할별 증거의 정합성을 검사한다.

   ```powershell
   python scripts/verify_release_1_evidence.py `
     --technical-evidence docs/contest/release_1_technical_evidence.json `
     --manual-evidence docs/contest/release_1_evidence.json
   ```

`ready-for-team-leader-decision`은 세 역할의 필수 증거가 정합하다는 뜻일 뿐
Gate 통과 판정이 아니다. 검증 도구의 `gate_verdict`는 DT7F 전까지 항상
`blocked`를 유지한다.

## QA 검증

QA는 실제 API 모드에서 다음을 확인한다.

| check ID | 확인 내용 |
| --- | --- |
| `actual-golden-search` | exact query의 첫 결과·정책 identity·조건·상태 |
| `empty-results` | 미일치 검색의 빈 결과 안내와 조건 유지 |
| `partial-unknown-boundary` | partial·unknown 정책의 경고와 자격 비확정 표현 |
| `api-error-retry` | API 실패 표시, 재시도와 복구 흐름 |

결함이 있으면 `blocked`로 기록하고 재현 절차·영향·증거를 notes와
`evidence_refs`에 남긴다. QA가 직접 수정한 결함은 다른 담당자 또는 Team
Leader가 재확인할 때까지 종료하지 않는다.

## 사용성 검증

사용성 리뷰어는 구현에 참여하지 않은 사용자 관점에서 다음을 확인한다.

| check ID | 확인 내용 |
| --- | --- |
| `query-and-condition-understanding` | 자연어 원문과 해석된 연령·지역·카테고리의 이해 가능성 |
| `result-reason-understanding` | 기대 정책이 노출된 이유와 미해석 키워드의 이해 가능성 |
| `source-and-freshness-understanding` | 출처와 KST 수집 시각이 최신성 보증과 다름을 이해하는지 |
| `eligibility-guidance-understanding` | 후보 안내가 실제 자격 확정이 아님을 이해하는지 |

리뷰어가 말한 표현과 혼란 지점을 요약하되 개인정보를 저장하지 않는다.

## 보고서 근거 대조

보고서 담당은 구현을 새로 승인하지 않고 다음 근거가 서로 일치하는지 확인한다.

| check ID | 확인 내용 |
| --- | --- |
| `dataset-baseline` | 실제 건수와 두 Source snapshot identity |
| `contract-and-query-identity` | contract hash, exact query와 기대 정책 identity |
| `technical-results` | 기술 감사·단위·통합·Browser 결과의 출처와 실제 실행 여부 |
| `scope-risk-and-gate-status` | 자격 비확정, 외부 데이터 변동 위험, 독립 증거와 Gate 상태 |

실행하지 않은 검증이나 미완료 기능을 성과로 기록하지 않는다.

## 증거 보안과 보존

- API key, DB password, pgpass 내용, 개인 식별 정보와 비공개 원문을 넣지 않는다.
- 자동 기술 증거는 검색 결과의 안전한 identity·판정 요약만 보존한다.
- screenshot에는 브라우저 주소창·터미널의 인증값이 포함되지 않았는지 확인한다.
- 외부 URL은 팀이 접근할 수 있는지 확인하고, 최종 제출에 필요한 자료는
  저장소 포함 여부와 라이선스를 별도로 검토한다.
