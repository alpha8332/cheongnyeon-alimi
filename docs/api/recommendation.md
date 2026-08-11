# 맞춤 정책 추천 API 계약 (Recommendation API Contract)

## 개요

이 문서는 사용자 조건(연령, 거주지, 관심 분야, 신청 상태 등)을 기반으로 결정적 규칙에 따라 맞춤 정책을 추천하고, 추천 사유(`reasons[]`) 및 미확정 조건(`unknown_conditions[]`)을 반환하는 API 계약을 정의한다.

추천 API는 자격 충족이나 최종 수혜 가능성을 단정하지 않으며 비단정 안내 문구(`disclaimer`)를 응답에 포함한다.

---

## 1. 맞춤 정책 추천 요청

- **Endpoint**: `POST /api/v1/recommendations` (또는 `GET /api/v1/policies/recommendations`)
- **Content-Type**: `application/json`
- **인증**: 필요 없음 (공개 API)

### 요청 바디 (Request Body)

```json
{
  "age": 25,
  "region": "서울특별시",
  "category": "finance",
  "status": "open",
  "include_partial": false,
  "limit": 10
}
```

| 필드명 | 타입 | 필수 여부 | 기본값 | 제약 조건 / 예시 | 설명 |
| --- | --- | --- | --- | --- | --- |
| `age` | `integer` | 선택 | `null` | 0~120 (예: `25`) | 사용자 만 연령 |
| `region` | `string` | 선택 | `null` | 예: `서울특별시` | 거주 지역 |
| `category` | `string` | 선택 | `null` | `finance`, `housing`, `employment`, `education` | 관심 분야 |
| `status` | `string` | 선택 | `null` | `open`, `upcoming`, `closed` | 신청 상태 필터 |
| `include_partial` | `boolean` | 선택 | `false` | `true`, `false` | partial 품질 상태 정책 포함 여부 |
| `limit` | `integer` | 선택 | `10` | 1~50 | 최대 반환 정책 수 |

---

### 성공 응답 (200 OK)

```json
{
  "items": [
    {
      "id": 1,
      "source_id": "initial_programs",
      "external_id": "R20260730001",
      "title": "청년 월세 특별지원",
      "lead": "무주택 청년 월세 지원 정책",
      "category": "housing",
      "regions": ["서울특별시"],
      "min_age": 19,
      "max_age": 34,
      "application_start": "2026-01-01T00:00:00Z",
      "application_end": "2026-12-31T23:59:59Z",
      "application_status": "open",
      "data_quality_status": "valid",
      "score": 90,
      "reasons": [
        {
          "code": "MATCHED_REGION",
          "label": "거주지 조건 부합 (서울특별시)"
        },
        {
          "code": "MATCHED_AGE",
          "label": "연령 조건 부합 (25세)"
        },
        {
          "code": "MATCHED_STATUS",
          "label": "현재 신청 가능 상태"
        }
      ],
      "unknown_conditions": [
        "소득 및 자산 세부 조건은 원문 확인이 필요합니다."
      ],
      "disclaimer": "본 추천 결과는 자격을 확정하지 않으며, 상세 자격 및 신청 조건은 공식 원문에서 확인해야 합니다."
    }
  ],
  "total": 1,
  "evaluated_at": "2026-08-11T00:00:00Z"
}
```

---

## 2. 정렬 및 결정성 규칙

1. **정렬 기준**: `score DESC`, `id ASC` (동일 점수 시 ID 오름차순으로 결정성 보장)
2. **점수 부여 규칙 (Scoring Rules)**:
   - `category` 일치: +30점
   - `region` 일치 (전국 포함 또는 해당 거주지 포함): +30점
   - `age` 일치 (`min_age <= age <= max_age`): +30점
   - `status == 'open'`: +10점
3. **미확정 조건 (`unknown_conditions`)**:
   - 데이터 원문에 소득/자산 등 세부 자산 조건이 자동 판정 불가능한 경우 상시 포함하여 정보 과장 방지

---

## 3. 오류 응답 규격 (Error Responses)

#### 422 Unprocessable Entity (유효성 검사 실패)
잘못된 연령 범위 (`age < 0` 또는 `age > 120`), 무효한 `limit` 입력 시 반환한다.

```json
{
  "detail": [
    {
      "loc": ["body", "age"],
      "msg": "Input should be less than or equal to 120",
      "type": "less_than_equal"
    }
  ]
}
```
