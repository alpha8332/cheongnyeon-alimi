# Release 1 검증 증거 안내

## 목적

이 문서는 `v0.1.0` Gate G4의 DT7E에서 QA와 사용성 리뷰가 동일한 실제
snapshot과 acceptance 계약을 확인하는 절차를 정한다. 합성 Seed나 Frontend
Mock은 이 증거의 데이터 기준으로 사용하지 않는다.

`v0.1.0`은 기본 정책 검색 MVP이므로 `2026-08-06` Team Leader 결정에 따라
경량 팀 리뷰를 허용하고 역할 독립성과 보고서 대조를 필수 Gate에서 제외했다.
보고서와 API 오류 토스트 검증은 `v0.5.0`으로 이관한다. exact query와 기대
정책은 수동 리뷰가 아니라 실제 PostgreSQL 기술 증거로 계속 엄격하게
검증하며, Gate G4 최종 판정은 DT7F에서 별도로 수행한다.

## 고정 기준

| 항목 | 값 |
| --- | --- |
| Release / Gate | `v0.1.0` / `G4` |
| 실제 정책 수 | 3,156건 |
| 온통청년 snapshot | `6add34f7aad9456ab0abb19175b7621c` |
| 복지로 snapshot | `ffa74ef47e6048109f11bf40d1ac5e15` |
| acceptance contract SHA-256 | `53bc5ee18e028a050079559064eaf88a332d917099a9bad8f696d312838a411c` |
| exact query | `천안 사는 27살 청년 단기숙소 지원 받을 수 있나?` |
| 기대 정책 | 온통청년 `20260430005400212969`, `청년단기숙소 지원사업` |

기준 계약은 [`data/release_1_acceptance.json`](../../data/release_1_acceptance.json),
작성 시작점은
[`release_1_evidence_template.json`](release_1_evidence_template.json)이다.
계약 hash나 snapshot identity가 다르면 기존 결과를 재사용하지 않고 Team
Leader에게 변경 이유와 재검증 필요 여부를 먼저 확인한다.

## Windows 로컬 시스템 실행

저장소 루트의 `run.bat`를 더블클릭하면 로컬 `.venv`, Frontend
`node_modules`, PostgreSQL `127.0.0.1:5432`와 pgpass를 확인한 뒤 Backend와
Frontend를 같은 터미널에서 실행하고 기본 브라우저의 홈 화면을 연다. Frontend는
`VITE_USE_MOCK=false`인 actual API 모드로 실행된다.

이 실행기는 특정 검토나 검색어에 종속되지 않는다. acceptance 검사를 대신
수행하거나 golden query를 미리 검색하지 않으므로, 검토자는 실행된 웹 UI에서
필요한 검색을 직접 입력해 관찰한다. API key는 필요하지 않으며
외부 Source API를 다시 호출하지 않는다.

pgpass는 `PGPASSFILE`,
`%LOCALAPPDATA%\Temp\cheongnyeon-alimi-pgpass.conf`,
`%APPDATA%\postgresql\pgpass.conf` 순으로 찾는다. 별도 경로를 사용하려면 첫
번째 인자로 전달한다.

```bat
run.bat "C:\path\to\pgpass.conf"
```

종료할 때는 실행 중인 터미널에서 `Ctrl+C`를 누른다. 별도 종료 BAT, Runtime
상태 파일이나 전용 로그 파일은 만들지 않으며 브라우저 창이나 탭은 임의로
닫지 않는다.

## 준비 절차

1. Team Leader는 현재 계약과 실제 PostgreSQL snapshot으로 기술 증거를 만든다.

   ```powershell
   python scripts/audit_release_1.py `
     --base-url http://127.0.0.1:8000 `
     --output docs/contest/release_1_technical_evidence.json
   ```

2. 템플릿을 `docs/contest/release_1_evidence.json`으로 복사한다. 원본 템플릿은
   수정하지 않는다.
3. QA와 사용성 리뷰어는 자신의 `reviews` 항목을 작성한다.
4. 모든 check는 실제 수행 뒤 `pass` 또는 `blocked`로 기록하고, 관찰 내용과
   검증 시 존재하는 저장소 상대 파일 경로 또는 검토 가능한 HTTP(S) URL을
   `evidence_refs`에 남긴다.
5. 다음 명령으로 snapshot·contract·query와 역할별 증거의 정합성을 검사한다.

   ```powershell
   python scripts/verify_release_1_evidence.py `
     --technical-evidence docs/contest/release_1_technical_evidence.json `
     --manual-evidence docs/contest/release_1_evidence.json
   ```

`ready-for-team-leader-decision`은 현재 계약의 두 필수 리뷰가 정합하다는 뜻일 뿐
Gate 통과 판정이 아니다. 검증 도구의 `gate_verdict`는 DT7F 전까지 항상
`blocked`를 유지한다.

DT7F의 최종 Team Leader 판정은
[`release_1_gate_decision.json`](release_1_gate_decision.json)에 별도로
기록한다. 현재 G4는 `pass`이며 Release 1은 `main` 커밋 `2b33ed7`에 병합되고
`v0.1.0` tag로 발행됐다. 이후 `develop`도 같은 커밋으로 fast-forward해
다음 Forest의 공통 기준점을 맞췄다.

## QA 검증

QA는 실제 API 모드에서 다음을 확인한다.

| check ID | 확인 내용 |
| --- | --- |
| `basic-search-and-detail` | 검색 결과·정책 상세의 기본 흐름과 안전한 정보 표시 |
| `empty-results` | 미일치 검색의 빈 결과 안내와 조건 유지 |
| `partial-unknown-boundary` | partial·unknown 정책의 경고와 자격 비확정 표현 |

결함이 있으면 `blocked`로 기록하고 재현 절차·영향·증거를 notes와
`evidence_refs`에 남긴다. QA가 직접 수정한 결함은 다른 담당자 또는 Team
Leader가 재확인할 때까지 종료하지 않는다.

## 사용성 검증

사용성 리뷰어는 사용자 관점에서 다음을 확인한다. Release 1 경량 정책은 역할
독립성을 필수로 요구하지 않지만 실제 관찰과 개선 의견을 구분해 기록한다.

| check ID | 확인 내용 |
| --- | --- |
| `query-and-condition-understanding` | 자연어 원문과 해석된 연령·지역·카테고리의 이해 가능성 |
| `result-reason-understanding` | 기대 정책이 노출된 이유와 미해석 키워드의 이해 가능성 |
| `source-and-freshness-understanding` | 출처와 KST 수집 시각이 최신성 보증과 다름을 이해하는지 |
| `eligibility-guidance-understanding` | 후보 안내가 실제 자격 확정이 아님을 이해하는지 |

리뷰어가 말한 표현과 혼란 지점을 요약하되 개인정보를 저장하지 않는다.

## `v0.5.0` 이관 항목

- API 오류·재시도 토스트와 닫기 동작의 실제 Browser 검증
- 데이터·contract·기술 결과·범위·위험의 보고서 근거 대조
- 더 넓은 사용자 시나리오와 역할 독립성을 갖춘 QA·사용성 검증

이번 Release에서 실행하지 않은 검증을 통과로 기록하지 않는다.

## 증거 보안과 보존

- API key, DB password, pgpass 내용, 개인 식별 정보와 비공개 원문을 넣지 않는다.
- 자동 기술 증거는 검색 결과의 안전한 identity·판정 요약만 보존한다.
- screenshot에는 브라우저 주소창·터미널의 인증값이 포함되지 않았는지 확인한다.
- 외부 URL은 팀이 접근할 수 있는지 확인하고, 최종 제출에 필요한 자료는
  저장소 포함 여부와 라이선스를 별도로 검토한다.
