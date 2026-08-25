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
    "단기숙소": "housing",
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

QUERY_FILLER_TERMS = frozenset(
    {
        "사는",
        "거주하는",
        "받는",
        "받을",
        "수",
        "있나",
        "있나요",
        "있어",
        "있을까",
        "알려줘",
        "찾아줘",
        "추천해줘",
    }
)

REGION_ADMINISTRATIVE_SUFFIXES = (
    "특별자치시",
    "특별자치도",
    "광역시",
    "특별시",
    "자치구",
    "시",
    "군",
    "구",
    "도",
)


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
    q_clean_normalized = normalize_search_text(q.strip() if q else "") or ""

    override_fields: list[SearchDimension] = []
    conditions: list[ConditionItem] = []
    consumed_tokens: list[str] = []
    parsed_category_token: str | None = None

    # 명시적 파라미터 유무 체크 및 override
    explicit_override_keys: set[SearchDimension] = set()

    if region is not None:
        explicit_override_keys.add("region")
        override_fields.append("region")
    if age is not None:
        explicit_override_keys.add("age")
        override_fields.append("age")
    if category is not None:
        explicit_override_keys.add("category")
        override_fields.append("category")
    if status is not None:
        explicit_override_keys.add("status")
        override_fields.append("status")
    if keyword is not None:
        explicit_override_keys.add("keyword")
        override_fields.append("keyword")

    # 1. 명시적 region 처리
    if region is not None:
        reg_val = region.strip()
        reg_res, reg_cands = _resolve_region_name(reg_val, db)
        conditions.append(
            ConditionItem(
                dimension="region",
                value=reg_val,
                source="explicit",
                resolution=reg_res,
                candidates=reg_cands,
            )
        )

    # 2. 명시적 age 처리
    if age is not None:
        conditions.append(
            ConditionItem(
                dimension="age",
                value=int(age),
                source="explicit",
                resolution="resolved",
                candidates=[],
            )
        )

    # 3. 명시적 category 처리
    if category is not None:
        conditions.append(
            ConditionItem(
                dimension="category",
                value=str(category),
                source="explicit",
                resolution="resolved",
                candidates=[],
            )
        )

    # 4. 명시적 status 처리
    if status is not None:
        conditions.append(
            ConditionItem(
                dimension="status",
                value=str(status),
                source="explicit",
                resolution="resolved",
                candidates=[],
            )
        )

    # 5. 명시적 keyword 처리
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

    # 6. q 자연어 파싱 (explicit 파라미터가 지정된 차원은 override)
    # 6-1. 자연어 연령 파싱
    if "age" not in explicit_override_keys:
        parsed_age = _extract_age_from_query(q_clean_normalized)
        if parsed_age is not None:
            age_token, age_val = parsed_age
            consumed_tokens.append(age_token)
            conditions.append(
                ConditionItem(
                    dimension="age",
                    value=int(age_val),
                    source="q",
                    resolution="resolved",
                    candidates=[],
                )
            )

    # 6-2. 자연어 신청 상태 파싱
    if "status" not in explicit_override_keys:
        parsed_status = _extract_status_from_query(q_clean_normalized)
        if parsed_status is not None:
            status_token, status_val = parsed_status
            consumed_tokens.append(status_token)
            conditions.append(
                ConditionItem(
                    dimension="status",
                    value=str(status_val),
                    source="q",
                    resolution="resolved",
                    candidates=[],
                )
            )

    # 6-3. 자연어 카테고리 파싱
    if "category" not in explicit_override_keys:
        parsed_cat = _extract_category_from_query(q_clean_normalized)
        if parsed_cat is not None:
            cat_token, cat_val = parsed_cat
            parsed_category_token = cat_token
            consumed_tokens.append(cat_token)
            conditions.append(
                ConditionItem(
                    dimension="category",
                    value=str(cat_val),
                    source="q",
                    resolution="resolved",
                    candidates=[],
                )
            )

    # 구체 카테고리 표현은 구조화 category와 함께 text anchor로 보존한다.
    if (
        parsed_category_token is not None
        and "keyword" not in explicit_override_keys
    ):
        conditions.append(
            ConditionItem(
                dimension="keyword",
                value=parsed_category_token,
                source="q",
                resolution="resolved",
                candidates=[],
            )
        )

    # 6-4. 자연어 지역 파싱 (DB 기반 동적 해석 적용)
    if "region" not in explicit_override_keys:
        parsed_reg = _extract_region_from_query(q_clean_normalized, db)
        if parsed_reg is not None:
            consumed_tokens.append(parsed_reg)
            reg_res, reg_cands = _resolve_region_name(parsed_reg, db)
            resolved_val = reg_cands[0] if reg_cands else parsed_reg
            conditions.append(
                ConditionItem(
                    dimension="region",
                    value=resolved_val,
                    source="q",
                    resolution=reg_res,
                    candidates=reg_cands,
                )
            )

    # 7. 해석되지 않은 토큰/단어(uninterpreted_terms) 수집
    tokens = q_clean_normalized.split()
    uninterpreted: list[str] = []
    for token in tokens:
        clean_token = token.strip(",.!?~[]()")
        if not clean_token:
            continue
        if clean_token in QUERY_FILLER_TERMS:
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


def _extract_age_from_query(query_text: str) -> tuple[str, int] | None:
    age_match = re.search(r"(?:만\s*)?(\d{1,3})\s*(?:세|살)", query_text)
    if not age_match:
        age_match = re.search(r"만\s*(\d{1,3})", query_text)

    if age_match:
        try:
            parsed_val = int(age_match.group(1))
            if 0 <= parsed_val <= 150:
                return age_match.group(0), parsed_val
        except ValueError:
            pass
    return None


def _extract_status_from_query(query_text: str) -> tuple[str, ApplicationStatus] | None:
    for kw, stat in STATUS_KEYWORD_MAP.items():
        if kw in query_text:
            return kw, stat
    return None


def _extract_category_from_query(query_text: str) -> tuple[str, PolicyCategory] | None:
    for kw, cat in CATEGORY_KEYWORD_MAP.items():
        if kw in query_text:
            return kw, cat
    return None


def _extract_region_from_query(query_text: str, db: Session | None = None) -> str | None:
    """q 문장에서 알려진 또는 DB 내 행정구역 별칭/이름 키워드 매칭"""
    # 1. DB의 활성 정식 지역명은 광역 키워드보다 먼저, 가장 긴 이름부터
    # 매칭한다. 예: "경상남도 양산시"가 "경상남도"로 축약되는 것을 방지한다.
    if db is not None:
        try:
            from sqlalchemy import literal, select
            from app.models.administrative_region import AdministrativeRegion

            full_names = db.scalars(
                select(AdministrativeRegion.full_name)
                .where(
                    AdministrativeRegion.status == "active",
                    literal(query_text).contains(
                        AdministrativeRegion.full_name
                    ),
                )
                .distinct()
            ).all()
            for full_name in sorted(full_names, key=len, reverse=True):
                if len(full_name) >= 2 and full_name in query_text:
                    return full_name
        except Exception:
            pass

    # 2. ambiguous 지역 키워드 확인
    for amb_kw in AMBIGUOUS_REGION_CANDIDATES.keys():
        if amb_kw in query_text:
            return amb_kw

    # 3. REGION_KEYWORD_MAP의 키워드를 길이가 긴 순서대로 매칭
    sorted_kws = sorted(REGION_KEYWORD_MAP.keys(), key=len, reverse=True)
    for kw in sorted_kws:
        if kw in query_text:
            return kw

    # 4. DB 세션이 전달된 경우 DB AdministrativeRegionAlias / AdministrativeRegion 동적 검색
    if db is not None:
        try:
            from sqlalchemy import select
            from app.models.administrative_region import AdministrativeRegion, AdministrativeRegionAlias

            aliases = db.scalars(
                select(AdministrativeRegionAlias.alias).distinct()
            ).all()
            for alias_str in sorted(aliases, key=len, reverse=True):
                if len(alias_str) >= 2 and alias_str in query_text:
                    return alias_str

            names = db.scalars(
                select(AdministrativeRegion.name).distinct()
            ).all()
            for name_str in sorted(names, key=len, reverse=True):
                if len(name_str) >= 2 and name_str in query_text:
                    return name_str

            # 사용자는 보통 '양산시'보다 '양산', '김해시'보다 '김해'처럼
            # 행정구역 접미사를 생략한다. active 지역명에서 안전하게 파생한
            # 2자 이상 shorthand도 후보로 사용하고, 실제 해석 단계에서
            # 중복 지역은 ambiguous로 돌려보낸다.
            active_names = db.scalars(
                select(AdministrativeRegion.name).where(
                    AdministrativeRegion.status == "active"
                )
            ).all()
            shorthand_names = {
                shorthand
                for name in active_names
                if (shorthand := _strip_region_suffix(name)) is not None
            }
            for shorthand in sorted(shorthand_names, key=len, reverse=True):
                if shorthand in query_text:
                    return shorthand
        except Exception:
            pass

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
                exact_candidates = _resolve_exact_region_candidates(
                    name_clean,
                    db,
                )
                if len(exact_candidates) == 1:
                    return "resolved", exact_candidates
                if len(exact_candidates) > 1:
                    return "ambiguous", exact_candidates
                suffixless_candidates = _resolve_suffixless_region_candidates(
                    name_clean,
                    db,
                )
                if len(suffixless_candidates) == 1:
                    return "resolved", suffixless_candidates
                if len(suffixless_candidates) > 1:
                    return "ambiguous", suffixless_candidates
                return "unmapped", []
        except Exception:
            pass

    # 기본 키워드 맵에 없고 ambiguous에도 없는 일반 문자열의 경우 unmapped 판정
    return "unmapped", []


def _resolve_exact_region_candidates(
    region_name: str,
    db: Session,
) -> list[str]:
    from sqlalchemy import or_, select

    from app.models.administrative_region import AdministrativeRegion

    active_regions = db.scalars(
        select(AdministrativeRegion).where(
            AdministrativeRegion.status == "active",
            or_(
                AdministrativeRegion.full_name == region_name,
                AdministrativeRegion.name == region_name,
            ),
        )
    ).all()
    return sorted({region.full_name for region in active_regions})


def _strip_region_suffix(name: str) -> str | None:
    normalized = name.strip()
    for suffix in REGION_ADMINISTRATIVE_SUFFIXES:
        if normalized.endswith(suffix):
            shorthand = normalized[: -len(suffix)].strip()
            return shorthand if len(shorthand) >= 2 else None
    return None


def _resolve_suffixless_region_candidates(
    shorthand: str,
    db: Session,
) -> list[str]:
    from sqlalchemy import select

    from app.models.administrative_region import AdministrativeRegion

    active_regions = db.scalars(
        select(AdministrativeRegion).where(
            AdministrativeRegion.status == "active"
        )
    ).all()
    return sorted(
        {
            region.full_name
            for region in active_regions
            if _strip_region_suffix(region.name) == shorthand
        }
    )
