import re
from typing import Any, Sequence
from sqlalchemy.orm import Session

from app.schemas.policy import ApplicationStatus, PolicyCategory
from app.schemas.policy_search import (
    ConditionItem,
    InterpretedConditions,
    SearchDimension,
)
from app.services.policy_search_projection import normalize_search_text


REGION_KEYWORD_MAP: dict[str, str] = {
    "서울": "서울특별시",
    "서울특별시": "서울특별시",
    "서울시": "서울특별시",
    "경기": "경기도",
    "경기도": "경기도",
    "인천": "인천광역시",
    "인천광역시": "인천광역시",
    "인천시": "인천광역시",
    "부산": "부산광역시",
    "부산광역시": "부산광역시",
    "부산시": "부산광역시",
    "대구": "대구광역시",
    "대구광역시": "대구광역시",
    "대구시": "대구광역시",
    "광주": "광주광역시",
    "광주광역시": "광주광역시",
    "광주시": "광주광역시",
    "대전": "대전광역시",
    "대전광역시": "대전광역시",
    "대전시": "대전광역시",
    "울산": "울산광역시",
    "울산광역시": "울산광역시",
    "울산시": "울산광역시",
    "세종": "세종특별자치시",
    "세종시": "세종특별자치시",
    "세종특별자치시": "세종특별자치시",
    "강원": "강원특별자치도",
    "강원도": "강원특별자치도",
    "강원특별자치도": "강원특별자치도",
    "충북": "충청북도",
    "충청북도": "충청북도",
    "충남": "충청남도",
    "충청남도": "충청남도",
    "전북": "전라북도",
    "전라북도": "전북특별자치도",
    "전북특별자치도": "전북특별자치도",
    "전남": "전라남도",
    "전라남도": "전라남도",
    "경북": "경상북도",
    "경상북도": "경상북도",
    "경남": "경상남도",
    "경상남도": "경상남도",
    "제주": "제주특별자치도",
    "제주도": "제주특별자치도",
    "제주특별자치도": "제주특별자치도",
    # 시/군/구 대표 예시
    "강남": "서울특별시 강남구",
    "강남구": "서울특별시 강남구",
    "서초": "서울특별시 서초구",
    "서초구": "서울특별시 서초구",
    "송파": "서울특별시 송파구",
    "송파구": "서울특별시 송파구",
    "마포": "서울특별시 마포구",
    "마포구": "서울특별시 마포구",
    "관악": "서울특별시 관악구",
    "관악구": "서울특별시 관악구",
    "수원": "경기도 수원시",
    "수원시": "경기도 수원시",
    "성남": "경기도 성남시",
    "성남시": "경기도 성남시",
    "고양": "경기도 고양시",
    "고양시": "경기도 고양시",
    "용인": "경기도 용인시",
    "용인시": "경기도 용인시",
}

AMBIGUOUS_REGION_CANDIDATES: dict[str, list[str]] = {
    "중구": ["서울특별시 중구", "부산광역시 중구", "대구광역시 중구", "인천광역시 중구", "광주광역시 중구", "대전광역시 중구", "울산광역시 중구"],
    "서구": ["부산광역시 서구", "대구광역시 서구", "인천광역시 서구", "광주광역시 서구", "대전광역시 서구"],
    "동구": ["부산광역시 동구", "대구광역시 동구", "인천광역시 동구", "광주광역시 동구", "대전광역시 동구", "울산광역시 동구"],
    "남구": ["부산광역시 남구", "대구광역시 남구", "인천광역시 미추홀구(구 남구)", "광주광역시 남구", "울산광역시 남구"],
    "북구": ["부산광역시 북구", "대구광역시 북구", "광주광역시 북구", "울산광역시 북구"],
}

CATEGORY_KEYWORD_MAP: dict[str, PolicyCategory] = {
    "주거": "housing",
    "월세": "housing",
    "전세": "housing",
    "주택": "housing",
    "청년주택": "housing",
    "보증금": "housing",
    "집": "housing",
    "금융": "finance",
    "대출": "finance",
    "적금": "finance",
    "자산": "finance",
    "통장": "finance",
    "금리": "finance",
    "목돈": "finance",
    "저축": "finance",
    "복지": "welfare",
    "의료": "welfare",
    "건강": "welfare",
    "수당": "welfare",
    "지원금": "welfare",
    "생계비": "welfare",
    "취업": "employment",
    "일자리": "employment",
    "구직": "employment",
    "인턴": "employment",
    "채용": "employment",
    "취업준비": "employment",
    "구직활동": "employment",
    "창업": "startup",
    "스타트업": "startup",
    "사업자": "startup",
    "교육": "education",
    "장학금": "education",
    "등록금": "education",
    "학비": "education",
    "역량강화": "education",
}

STATUS_KEYWORD_MAP: dict[str, ApplicationStatus] = {
    "모집중": "open",
    "신청중": "open",
    "접수중": "open",
    "진행중": "open",
    "모집 중": "open",
    "신청 중": "open",
    "접수 중": "open",
    "진행 중": "open",
    "예정": "scheduled",
    "모집예정": "scheduled",
    "신청예정": "scheduled",
    "모집 예정": "scheduled",
    "신청 예정": "scheduled",
    "마감": "closed",
    "종료": "closed",
    "신청마감": "closed",
    "마감됨": "closed",
}


def parse_search_query(
    *,
    q: str,
    keyword: str | None = None,
    region: str | None = None,
    age: int | None = None,
    category: PolicyCategory | None = None,
    status: ApplicationStatus | None = None,
    db: Session | None = None,
) -> InterpretedConditions:
    """한국어 자연어 검색어 q 및 명시적 파라미터를 규칙 기반으로 해석하고 override를 적용한다."""
    q_raw = q
    q_clean = (q.strip() if q else "")
    # 다중 공백 정리
    q_clean_normalized = re.sub(r"\s+", " ", q_clean)

    conditions: list[ConditionItem] = []
    override_fields: list[SearchDimension] = []
    consumed_tokens: set[str] = set()

    # 1. 연령(age) 파싱
    q_parsed_age: int | None = None
    age_match = re.search(r"(?:만\s*)?(\d{1,3})\s*(?:세|살)", q_clean_normalized)
    if not age_match:
        age_match = re.search(r"만\s*(\d{1,3})", q_clean_normalized)

    if age_match:
        try:
            parsed_val = int(age_match.group(1))
            if 0 <= parsed_val <= 150:
                q_parsed_age = parsed_val
                consumed_tokens.add(age_match.group(0))
        except ValueError:
            pass

    if age is not None:
        if q_parsed_age is not None:
            override_fields.append("age")
        conditions.append(
            ConditionItem(
                dimension="age",
                value=age,
                source="explicit",
                resolution="resolved",
                candidates=[],
            )
        )
    elif q_parsed_age is not None:
        conditions.append(
            ConditionItem(
                dimension="age",
                value=q_parsed_age,
                source="q",
                resolution="resolved",
                candidates=[],
            )
        )

    # 2. 신청 상태(status) 파싱
    q_parsed_status: ApplicationStatus | None = None
    for kw, stat in STATUS_KEYWORD_MAP.items():
        if kw in q_clean_normalized:
            q_parsed_status = stat
            consumed_tokens.add(kw)
            break

    if status is not None:
        if q_parsed_status is not None:
            override_fields.append("status")
        conditions.append(
            ConditionItem(
                dimension="status",
                value=status,
                source="explicit",
                resolution="resolved",
                candidates=[],
            )
        )
    elif q_parsed_status is not None:
        conditions.append(
            ConditionItem(
                dimension="status",
                value=q_parsed_status,
                source="q",
                resolution="resolved",
                candidates=[],
            )
        )

    # 3. 카테고리(category) 파싱
    q_parsed_category: PolicyCategory | None = None
    for kw, cat in CATEGORY_KEYWORD_MAP.items():
        if kw in q_clean_normalized:
            q_parsed_category = cat
            consumed_tokens.add(kw)
            break

    if category is not None:
        if q_parsed_category is not None:
            override_fields.append("category")
        conditions.append(
            ConditionItem(
                dimension="category",
                value=category,
                source="explicit",
                resolution="resolved",
                candidates=[],
            )
        )
    elif q_parsed_category is not None:
        conditions.append(
            ConditionItem(
                dimension="category",
                value=q_parsed_category,
                source="q",
                resolution="resolved",
                candidates=[],
            )
        )

    # 4. 지역(region) 파싱 및 resolution
    q_parsed_region_raw: str | None = None
    q_region_candidates: list[str] = []
    q_region_resolution: str = "resolved"

    # 명시적 region 처리 혹은 q에서 region 파싱
    if region is not None:
        # 명시적 region 검증
        explicit_reg_clean = region.strip()
        reg_res, reg_cands = _resolve_region_name(explicit_reg_clean, db)
        if q_parsed_region_raw is not None or _has_region_in_query(q_clean_normalized):
            override_fields.append("region")
        conditions.append(
            ConditionItem(
                dimension="region",
                value=explicit_reg_clean,
                source="explicit",
                resolution=reg_res,  # resolved, unmapped, ambiguous
                candidates=reg_cands,
            )
        )
    else:
        # q에서 지역 파싱
        matched_reg_kw = _extract_region_from_query(q_clean_normalized)
        if matched_reg_kw:
            consumed_tokens.add(matched_reg_kw)
            reg_res, reg_cands = _resolve_region_name(matched_reg_kw, db)
            resolved_val = REGION_KEYWORD_MAP.get(matched_reg_kw, matched_reg_kw)
            conditions.append(
                ConditionItem(
                    dimension="region",
                    value=resolved_val,
                    source="q",
                    resolution=reg_res,
                    candidates=reg_cands,
                )
            )

    # 5. 명시적 키워드(keyword) 처리
    if keyword is not None:
        conditions.append(
            ConditionItem(
                dimension="keyword",
                value=keyword.strip(),
                source="explicit",
                resolution="resolved",
                candidates=[],
            )
        )

    # 6. 해석되지 않은 토큰/단어(uninterpreted_terms) 수집
    tokens = q_clean_normalized.split()
    uninterpreted: list[str] = []
    for token in tokens:
        clean_token = token.strip(",.!?~[]()")
        if not clean_token:
            continue
        # 이미 파싱에 소비된 단어인지 확인
        is_consumed = False
        for consumed in consumed_tokens:
            if clean_token in consumed or consumed in clean_token:
                is_consumed = True
                break
        if not is_consumed:
            uninterpreted.append(clean_token)

    return InterpretedConditions(
        q_raw=q_raw,
        q_clean=q_clean_normalized,
        conditions=conditions,
        override_fields=override_fields,
        uninterpreted_terms=uninterpreted,
    )


def _extract_region_from_query(query_text: str) -> str | None:
    """q 문장에서 알려진 지역 키워드 매칭"""
    # ambiguous 지역 키워드 먼저 확인
    for amb_kw in AMBIGUOUS_REGION_CANDIDATES.keys():
        if amb_kw in query_text:
            return amb_kw
    # REGION_KEYWORD_MAP의 키워드를 길이가 긴 순서대로 매칭
    sorted_kws = sorted(REGION_KEYWORD_MAP.keys(), key=len, reverse=True)
    for kw in sorted_kws:
        if kw in query_text:
            return kw
    return None


def _has_region_in_query(query_text: str) -> bool:
    return _extract_region_from_query(query_text) is not None


def _resolve_region_name(region_name: str, db: Session | None) -> tuple[str, list[str]]:
    """지역명의 매핑 상태(resolved, ambiguous, unmapped) 및 후보군 반환"""
    name_clean = region_name.strip()
    if name_clean in AMBIGUOUS_REGION_CANDIDATES:
        return "ambiguous", AMBIGUOUS_REGION_CANDIDATES[name_clean]

    if name_clean in REGION_KEYWORD_MAP:
        return "resolved", [REGION_KEYWORD_MAP[name_clean]]

    # DB 세션이 전달된 경우 repository alias candidate 조회 검증도 가능
    if db is not None:
        try:
            from app.services.policy_search_evaluation import PolicySearchEvaluationService
            service = PolicySearchEvaluationService(db)
            res = service.resolve_region_alias(name_clean)
            if res.status == "matched":
                cands = [c.full_name for c in res.candidates]
                return "resolved", cands
            elif res.status == "ambiguous":
                cands = [c.full_name for c in res.candidates]
                return "ambiguous", cands
            else:
                return "unmapped", []
        except Exception:
            pass

    # 기본 키워드 맵에 없고 ambiguous에도 없는 일반 문자열의 경우 unmapped 판정
    return "unmapped", []
