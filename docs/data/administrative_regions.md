# 행정구역 기준정보

## 현재 기준선

- canonical scheme: `kr-bjd-20260803`
- 기준일: `2026-08-03`
- 원천: 행정안전부 법정동코드 전체자료
- 원천 레코드: 53,387건(존재 20,560건, 폐지 32,827건)
- 정책 검색용 Seed: 538건(대한민국 루트 1건, 시·도 및 시·군·구 537건)
- 별칭 Seed: 1,080건

행정안전부 [법정동코드 조회](https://www.code.go.kr/stdcode/regCodeL.do)의
전체 존재·폐지 자료와 상세 다운로드 필드를 기준으로 한다. 공공데이터포털의
[법정동코드목록 조회서비스](https://www.data.go.kr/data/15077871/openapi.do)는
10자리 지역코드, 상위지역코드와 생성일을 설명하며 이용허락범위를
`제한 없음`으로 표시한다. 다운로드 시점, 수량과 정규화 CSV SHA-256은
`data/reference/administrative_regions/*.manifest.json`에 고정한다.

## 재현 절차

공식 사이트에서 같은 기준일 snapshot을 새로 받는 명령은 다음과 같다.

```powershell
.\.venv\Scripts\python.exe -B scripts/fetch_administrative_regions.py `
  --snapshot-date 2026-08-03
```

이 명령은 네트워크를 사용한다. 전체 목록과 2자리 지역 prefix별 상세
다운로드를 서로 대조한 뒤 결정적 gzip CSV와 manifest를 쓴다. 원천 전체
목록에만 있던 끝 공백 4건은 code·이름·상태 대조 전에 제거하며 그 밖의
이름이나 코드는 변경하지 않는다.

잠긴 snapshot으로 정책 검색 Seed를 만들거나 검증한다.

```powershell
.\.venv\Scripts\python.exe -B scripts/build_administrative_regions.py `
  --snapshot-date 2026-08-03

.\.venv\Scripts\python.exe -B scripts/build_administrative_regions.py `
  --snapshot-date 2026-08-03 --check
```

Seed 생성은 네트워크를 사용하지 않으며 manifest의 행 수와 정규화 CSV
SHA-256이 다르면 중단한다.

## 지역 모델

`administrative_regions.json`은 이름이 아니라 `(scheme, code)`를 identity로
사용한다. 모든 값은 다음 계약을 따른다.

| 필드 | 의미 |
| --- | --- |
| `scheme`, `code` | snapshot별 canonical identity와 10자리 법정동코드 |
| `name`, `full_name` | 공식 최하지역명과 전체 법정동명 |
| `level` | `country`, `province`, `district` |
| `status` | `active`, `retired` |
| `parent_code` | 공식 상위지역코드를 보존한 canonical parent |
| `source_parent_code` | 원천 상위지역코드 감사 값 |
| `aggregate_parent_code` | 검색 계층에 필요한 검증된 집계 지역 관계 |
| `valid_from`, `valid_to` | 원천 생성·폐지일, 없으면 `null` |
| `external_codes` | 명시적으로 생성한 외부 code crosswalk |

행정안전부 원천에서 `4413100000` 천안시 동남구와 `4413300000` 천안시
서북구의 상위지역은 모두 `4400000000` 충청남도다. 이 값은 바꾸지 않는다.
다만 천안시 정책 검색에는 중간 집계 관계가 필요하므로, 같은 공식 광역 부모
아래 현재 유효 레코드의 전체 이름이 정확히 일치하는 경우에만
`aggregate_parent_code=4413000000`을 만든다. 검색 ancestor는 집계 관계를
우선해 `동남구 → 천안시 → 충청남도 → 대한민국`으로 탐색한다. 문자열 prefix를
실행 시점에 추정하거나 근거 없는 폐지 code 후계 관계를 만들지 않는다.

대한민국 `0000000000`은 공식 시·도 parent가 가리키는 시스템 루트이며 법정동
원천 행은 아니다. 폐지 행에서 원천 parent가 비어 있으면 `null`을 유지한다.

## 별칭과 외부 code

별칭은 공식 전체 이름, 공식 최하지역명과 최소한의 승인 별칭 `전국`, `충남`,
`천안`으로 구성한다. 같은 별칭이 여러 active 지역을 가리킬 수 있으며
`중구` 같은 값은 `ambiguous`다. Unicode NFKC와 공백만 정규화하고 fuzzy
match는 하지 않는다.

`kr-bjd-prefix5`는 10자리 법정동코드의 앞 5자리를 Seed 생성 시 명시적으로
저장한 crosswalk다. 공공데이터포털의
[지역사랑상품권 이용 가능 지역코드 안내](https://www.data.go.kr/data/15108279/openapi.do)도
행정안전부 법정동코드 앞 5자리(시·도 2자리와 시·군·구 3자리)를 같은 구조로
설명한다. `44131`은 동남구와 exact match하지만 `4413`이나 없는
`99999`는 `unmapped`다. crosswalk 자체만으로 Source 의미를 추정하지 않는다.
온통청년 검증 표본의 고유 `zipCd` 260개가 모두 이 crosswalk와
유일하게 일치함을 확인해 숫자 5자리 목록만 exact resolver에 전달한다.
개편 전 code는 후계 지역으로 치환하지 않고, 새 미매핑 값과 숫자가 아닌
표현은 Source 근거가 추가될 때까지 `unknown`으로 유지한다.

## 소비 경계

- Backend는 파일 기준정보와 같은 필드의 PostgreSQL 지역·별칭 테이블과
  무변조·idempotent importer를 제공한다. Migration 적용 후 다음 명령으로
  적재한다.

  ```powershell
  Set-Location backend
  ..\.venv\Scripts\python.exe -B -m app.cli.import_regions
  ```

  `--dry-run`은 전체 지역·별칭을 검증하고 DB 변경을 rollback한다. 같은
  versioned scheme의 저장 값이 Seed와 다르거나 예상 밖 code·alias가 있으면
  덮어쓰지 않고 실패한다.
- 미매핑 code는 자동 보정하지 않고 `unmapped`로 전달해 Source 근거를
  보존한다.
- 폐지 code는 조회할 수 있지만 기본 resolver 후보는 active만 사용한다.
- 검색 query alias는 active 후보 0·1·다수에 따라 `unmapped`·`matched`·
  `ambiguous`로 판정한다. 계층 탐색은 `aggregate_parent_code`를 우선하고
  `parent_code`로 이어가며 cycle·누락 parent를 조용히 무시하지 않는다.
- 지역 데이터 version을 바꾸면 scheme, Seed, Fixture, DB Migration과
  Backend·Frontend 소비 영향을 함께 검토한다.
