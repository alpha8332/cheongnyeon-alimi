# Fixture와 Seed 계약

## 목적

외부 네트워크와 실제 정책 원문 없이 Raw → Extracted → Normalized → Seed를
결정적으로 재현하고 Backend·Frontend가 같은 경계 사례를 사용하게 한다.
모든 정책 내용과 identity는 합성 데이터다.

## 주요 산출물

| 경로 | 역할 |
| --- | --- |
| `data/fixtures/raw/` | 합성 API·웹 Raw envelope |
| `data/fixtures/extracted/` | Source Extractor 결과 |
| `data/fixtures/normalized/programs.json` | valid·partial 정규화 정책 |
| `data/fixtures/rejected/` | invalid와 검증 사유 |
| `data/fixtures/contracts/` | 검색·추천·자격·반복 실행 경계 |
| `data/fixtures/regional/` | 지역 evidence와 중복 판정 사례 |
| `data/seeds/initial_programs.json` | canonical 개발 Seed |
| `data/seeds/administrative_regions.json` | 행정구역 기준 Seed |
| `data/seeds/administrative_region_aliases.json` | 검색 별칭 Seed |

`normalized/programs.json`과 `initial_programs.json`은 같은 canonical JSON
배열이다. rejected와 지역 판정 전용 Fixture는 정상 Seed에 포함하지 않는다.

## 합성 경계

- 합성 external ID는 실제 Source identity와 충돌하지 않는 prefix를 사용한다.
- URL은 네트워크에서 사용되지 않는 `fixture.invalid` host를 사용한다.
- 정책명·기관·본문과 연락처는 실제 정책을 복사하지 않는다.
- 실제 API key, query, 개인정보와 원본 response byte를 포함하지 않는다.
- 고정 document ID·시각·payload로 content hash와 provenance를 결정한다.
- 운영 `runtime/raw/`를 생성 입력이나 fallback으로 사용하지 않는다.

## Normalized 소비 규칙

- root는 `NormalizedProgram` 객체 배열이다.
- 현재 Schema required key를 모두 가진다.
- 선택 단일 값 없음은 `null`, 복수 값 없음은 `[]`로 표현한다.
- enum과 `YYYY-MM-DD` 날짜를 문자열 계약 그대로 유지한다.
- identity는 `(source_id, external_id)`다.
- 정상 Seed에는 `valid`와 허용된 `partial`만 포함한다.
- provenance는 DB에 보존하지만 공개 목록 DTO에 자동 노출하지 않는다.

Backend importer는 전체 batch를 먼저 검증하고 invalid·identity admission 거부·
DB write 실패가 있으면 batch를 rollback한다. `--dry-run`도 실제 upsert 경로를
실행한 뒤 rollback한다.

Frontend Mock은 공개 API DTO와 pagination envelope를 사용하며 Raw provenance와
`invalid`를 사용자 타입으로 노출하지 않는다. 실제 API 모드 검증은
[Frontend 실제 API 테스트](../development/frontend_real_api_manual_testing_guide.md)를
따른다.

## 대표 경계

- 연령 제한과 연령 제한 없음
- 전국·시도·시군구·지역 미확인
- 복수 분야와 빈 배열
- 고정 기간·상시·예산 소진·날짜 미확정
- valid·partial·invalid
- 동일 snapshot·내용 변경·중복·persist 실패
- 자격 조건 없음·미확정·충돌·긴 원문
- 교차 Source exact·fingerprint·검토 필요 중복

## 재생성과 검증

```powershell
uv run python -B scripts/build_data_fixtures.py --check
```

Fixture를 의도적으로 갱신할 때만 `--write`를 사용하고 diff를 검토한다.

```powershell
uv run python -B scripts/build_data_fixtures.py --write
.\.venv\Scripts\python.exe -B scripts/build_administrative_regions.py `
  --snapshot-date 2026-08-03 --check
```

생성기 변경 시 Python model, JSON Schema, Fixture, Seed, Backend importer와
Frontend 소비 테스트를 같은 변경에서 대조한다.

## 공개·라이선스 경계

합성 Fixture는 실제 API 원문 재배포 허가와 무관하게 테스트 구조만 재현한다.
공개 dataset은 별도의 [공개 정책 dataset 계약](public_policy_dataset.md)을
통과해야 하며 Fixture·Seed를 사용자 정책 수의 근거로 사용하지 않는다.
