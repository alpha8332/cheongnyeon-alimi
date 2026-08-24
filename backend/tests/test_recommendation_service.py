from app.models.policy import Policy
from app.schemas.recommendation import RecommendationRequest
from app.services.policy_search_evaluation import (
    MatchState,
    RegionDecision,
    RegionDecisionReason,
    RegionQueryResolution,
    RegionResolutionState,
)
from app.services.recommendation import evaluate_policy_recommendation


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
    assert any("지역 제한 근거" in message for message in item.unknown_conditions)
