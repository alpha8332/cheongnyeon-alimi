from app.models.policy import Policy
from app.schemas.recommendation import (
    RecommendationItem,
    RecommendationReason,
    RecommendationRequest,
)
from app.services.policy_search_evaluation import (
    MatchState,
    RegionDecision,
    RegionDecisionReason,
    RegionQueryResolution,
    RegionResolutionState,
)
from app.services.recommendation import (
    _recommendation_region_sort_key,
    evaluate_policy_recommendation,
)


def test_unknown_region_is_unconfirmed_candidate_not_nationwide() -> None:
    policy = Policy(
        id=1,
        source_id="public-test",
        source_name="공개 테스트",
        external_id="PUBLIC-UNKNOWN-REGION",
        title="지역 미확인 청년 지원",
        categories=["welfare"],
        regions=[],
        coverage_scope="unknown",
        application_status="open",
        data_quality_status="partial",
    )
    query = RegionQueryResolution(RegionResolutionState.MATCHED, ())
    decision = RegionDecision(
        MatchState.UNKNOWN,
        RegionDecisionReason.POLICY_UNKNOWN,
        query,
    )

    item = evaluate_policy_recommendation(
        policy,
        RecommendationRequest(
            region="경상남도 양산시",
            category="welfare",
            include_partial=True,
        ),
        region_decision=decision,
    )

    assert item is not None
    assert item.regions == []
    assert not any(
        reason.code == "MATCHED_REGION" for reason in item.reasons
    )
    assert any(
        reason.code == "REGION_UNCONFIRMED" for reason in item.reasons
    )
    assert any("지역 제한 근거" in message for message in item.unknown_conditions)


def test_recommendation_region_sort_prioritizes_local_scope() -> None:
    request = RecommendationRequest(region="경상남도 양산시")
    base = dict(
        source_id="test",
        external_id="test",
        title="테스트 정책",
        category="welfare",
        min_age=None,
        max_age=None,
        application_start=None,
        application_end=None,
        application_status="open",
        data_quality_status="valid",
        score=30,
        unknown_conditions=[],
        disclaimer="원문 확인",
    )
    local = RecommendationItem(
        id=1,
        regions=["경상남도 양산시"],
        reasons=[
            RecommendationReason(
                code="MATCHED_REGION",
                label="거주지 조건 부합 (경상남도 양산시)",
            )
        ],
        **base,
    )
    broad = local.model_copy(
        update={"id": 2, "regions": [f"지역 {index}" for index in range(200)]}
    )
    nationwide = local.model_copy(
        update={
            "id": 3,
            "regions": [],
            "reasons": [
                RecommendationReason(
                    code="MATCHED_REGION",
                    label="거주지 조건 부합 (전국)",
                )
            ],
        }
    )

    assert _recommendation_region_sort_key(
        local, request
    ) < _recommendation_region_sort_key(broad, request)
    assert _recommendation_region_sort_key(
        broad, request
    ) < _recommendation_region_sort_key(nationwide, request)


def test_multiple_interest_categories_use_or_matching() -> None:
    policy = Policy(
        id=10,
        source_id="public-test",
        source_name="공개 테스트",
        external_id="PUBLIC-MULTI-CATEGORY",
        title="청년 금융 지원",
        categories=["finance"],
        regions=[],
        coverage_scope="nationwide",
        application_status="open",
        data_quality_status="valid",
    )

    matched = evaluate_policy_recommendation(
        policy,
        RecommendationRequest(categories=["housing", "finance"]),
        region_decision=None,
    )
    mismatched = evaluate_policy_recommendation(
        policy,
        RecommendationRequest(categories=["housing", "education"]),
        region_decision=None,
    )

    assert matched is not None
    assert matched.score == 40
    assert matched.category == "finance"
    assert matched.categories == ["finance"]
    assert any(
        reason.code == "MATCHED_CATEGORY" for reason in matched.reasons
    )
    assert mismatched is None
