from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.policy import Policy
from app.repositories.policy import PolicyRepository
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItem,
    RecommendationReason,
)


def evaluate_policy_recommendation(
    policy: Policy,
    request: RecommendationRequest,
) -> Optional[RecommendationItem]:
    """단일 정책에 대해 추천 관련도 점수(score), 추천 사유(reasons) 및 미확정 조건 계산."""
    score = 0
    reasons: List[RecommendationReason] = []
    unknown_conditions: List[str] = [
        "소득 및 자산 세부 자격 요건은 공식 원문 확인이 필요합니다."
    ]

    # 1. 관심 분야 (Category) 매핑 (+30점)
    if request.category:
        matched_cat = False
        if policy.categories and any(request.category.lower() in str(c).lower() or str(c).lower() in request.category.lower() for c in policy.categories):
            matched_cat = True
        elif policy.category_text and (request.category.lower() in policy.category_text.lower() or policy.category_text.lower() in request.category.lower()):
            matched_cat = True

        if matched_cat:
            score += 30
            cat_label = policy.categories[0] if policy.categories else (policy.category_text or request.category)
            reasons.append(
                RecommendationReason(
                    code="MATCHED_CATEGORY",
                    label=f"관심 분야 부합 ({cat_label})",
                )
            )

    # 2. 거주지 (Region) 매핑 (+30점)
    if request.region:
        matched_region = False
        matched_region_str = request.region

        if not policy.regions or "전국" in policy.regions or (policy.region_text and "전국" in policy.region_text):
            matched_region = True
            matched_region_str = "전국"
        elif policy.regions:
            for r in policy.regions:
                r_str = str(r)
                if request.region in r_str or r_str in request.region:
                    matched_region = True
                    matched_region_str = r_str
                    break

        if matched_region:
            score += 30
            reasons.append(
                RecommendationReason(
                    code="MATCHED_REGION",
                    label=f"거주지 조건 부합 ({matched_region_str})",
                )
            )

    # 3. 연령 (Age) 매핑 (+30점)
    if request.age is not None:
        min_age = policy.age_min if policy.age_min is not None else 0
        max_age = policy.age_max if policy.age_max is not None else 120
        if min_age <= request.age <= max_age:
            score += 30
            reasons.append(
                RecommendationReason(
                    code="MATCHED_AGE",
                    label=f"연령 조건 부합 (만 {request.age}세)",
                )
            )

    # 4. 신청 상태 (Status) 매핑 (+10점)
    app_status = str(policy.application_status) if policy.application_status else "unknown"
    if app_status == "open":
        score += 10
        reasons.append(
            RecommendationReason(
                code="MATCHED_STATUS",
                label="현재 신청 가능 상태 (open)",
            )
        )

    # 특정 status 필터가 지정된 경우 필터 조건 체크
    if request.status and app_status != request.status:
        return None

    # 추천 아이템 DTO 생성
    return RecommendationItem(
        id=policy.id,
        source_id=policy.source_id,
        external_id=policy.external_id or "",
        title=policy.title,
        lead=policy.summary,
        category=policy.categories[0] if policy.categories else (policy.category_text or "기타"),
        regions=policy.regions or ["전국"],
        min_age=policy.age_min,
        max_age=policy.age_max,
        application_start=policy.application_start.isoformat() if policy.application_start else None,
        application_end=policy.application_end.isoformat() if policy.application_end else None,
        application_status=app_status,
        data_quality_status=str(policy.data_quality_status),
        score=score,
        reasons=reasons,
        unknown_conditions=unknown_conditions,
        disclaimer="본 추천 결과는 자격을 확정하지 않으며, 상세 자격 및 신청 조건은 공식 원문에서 확인해야 합니다.",
    )


def recommend_policies_service(
    db: Session,
    request: RecommendationRequest,
) -> RecommendationResponse:
    """
    사용자 입력 조건 기반 결정적 맞춤 추천 서비스.
    정렬 규칙: score DESC, id ASC (결정성 보장)
    """
    repository = PolicyRepository(db)
    quality_statuses = ("valid", "partial") if request.include_partial else ("valid",)

    # DB에서 대상 정책 조회
    page_result = repository.list(
        quality_statuses=quality_statuses,
        page=1,
        limit=200,  # 충분한 후보군 수집
    )

    evaluated_items: List[RecommendationItem] = []
    for policy in page_result.items:
        item = evaluate_policy_recommendation(policy, request)
        if item is not None:
            evaluated_items.append(item)

    # 결정적 정렬: score 내림차순, id 오름차순
    evaluated_items.sort(key=lambda x: (-x.score, x.id))

    # limit 개수 제한
    result_items = evaluated_items[: request.limit]

    return RecommendationResponse(
        items=result_items,
        total=len(evaluated_items),
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
