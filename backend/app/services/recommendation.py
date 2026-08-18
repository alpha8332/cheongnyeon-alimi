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
from app.services.policy_search_evaluation import (
    evaluate_age_condition,
    evaluate_application_status,
    MatchState,
    PolicySearchEvaluationService,
    RegionDecision,
)


def evaluate_policy_recommendation(
    policy: Policy,
    request: RecommendationRequest,
    *,
    region_decision: RegionDecision | None,
) -> Optional[RecommendationItem]:
    """검색의 3값 판정을 재사용해 추천·제외·미확정을 결정한다."""
    score = 0
    reasons: List[RecommendationReason] = []
    unknown_conditions: List[str] = [
        "소득 및 자산 세부 자격 요건은 공식 원문 확인이 필요합니다."
    ]

    # 1. 관심 분야 (Category) 판정 (+30점)
    if request.category:
        if policy.categories and request.category in policy.categories:
            score += 30
            reasons.append(
                RecommendationReason(
                    code="MATCHED_CATEGORY",
                    label=f"관심 분야 부합 ({request.category})",
                )
            )
        elif policy.categories:
            return None
        else:
            unknown_conditions.append(
                "관심 분야 분류가 없어 공식 원문 확인이 필요합니다."
            )

    # 2. 거주지 (Region) 판정 (+30점). 확정 불일치는 추천에서 제외한다.
    if request.region and region_decision is not None:
        if region_decision.state is MatchState.MATCH:
            score += 30
            matched_region = (
                "전국"
                if region_decision.reason.value == "nationwide"
                else request.region
            )
            reasons.append(
                RecommendationReason(
                    code="MATCHED_REGION",
                    label=f"거주지 조건 부합 ({matched_region})",
                )
            )
        elif region_decision.state is MatchState.MISMATCH:
            return None
        else:
            # 사용자가 명시한 지역은 검색 API와 같은 fail-closed 경계를 쓴다.
            # 근거가 unknown인 다른 지역 정책을 추천 후보에 섞지 않는다.
            return None

    # 3. 연령 (Age) 판정 (+30점). 누락은 일치로 추정하지 않는다.
    if request.age is not None:
        age_decision = evaluate_age_condition(
            requested_age=request.age,
            age_min=policy.age_min,
            age_max=policy.age_max,
            age_condition_text=policy.age_condition_text,
        )
        if age_decision.state is MatchState.MATCH:
            score += 30
            reasons.append(
                RecommendationReason(
                    code="MATCHED_AGE",
                    label=f"연령 조건 부합 (만 {request.age}세)",
                )
            )
        elif age_decision.state is MatchState.MISMATCH:
            return None
        else:
            unknown_conditions.append(
                "연령 제한 근거가 없어 공식 원문 확인이 필요합니다."
            )

    # 4. 신청 상태 (Status) 판정 (+10점). 기본 추천에서도 마감은 제외한다.
    app_status = str(policy.application_status) if policy.application_status else "unknown"
    requested_status = (
        "scheduled" if request.status == "upcoming" else request.status
    )
    if requested_status:
        status_decision = evaluate_application_status(
            requested_status=requested_status,
            policy_status=policy.application_status,
        )
        if status_decision.state is MatchState.MISMATCH:
            return None
        if status_decision.state is MatchState.UNKNOWN:
            return None
    elif app_status == "closed":
        return None

    if app_status == "open" and (requested_status in (None, "open")):
        score += 10
        reasons.append(
            RecommendationReason(
                code="MATCHED_STATUS",
                label="현재 신청 가능 상태 (open)",
            )
        )

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
    evaluator = PolicySearchEvaluationService(db)
    quality_statuses = ("valid", "partial") if request.include_partial else ("valid",)
    region_query = (
        evaluator.resolve_region_alias(request.region)
        if request.region
        else None
    )

    # 고정 200건 slice는 신규·지역 정책을 영구 제외하므로 전체 승인 snapshot을
    # 평가한다. 최종 응답 개수만 request.limit으로 제한한다.
    inventory = repository.list(
        quality_statuses=quality_statuses,
        page=1,
        limit=1,
    )
    page_result = repository.list(
        quality_statuses=quality_statuses,
        page=1,
        limit=max(inventory.total, 1),
    )
    region_decisions = (
        evaluator.evaluate_policy_regions(page_result.items, region_query)
        if region_query is not None
        else {}
    )

    evaluated_items: List[RecommendationItem] = []
    for policy in page_result.items:
        item = evaluate_policy_recommendation(
            policy,
            request,
            region_decision=region_decisions.get(policy.id),
        )
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
