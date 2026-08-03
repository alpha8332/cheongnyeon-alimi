from app.services.policy_search_projection import (
    POLICY_SEARCH_PROJECTION_VERSION,
    build_policy_search_document,
)


def test_projection_normalizes_and_groups_searchable_policy_fields():
    projection = build_policy_search_document(
        {
            "title": "  청년\n월세 지원  ",
            "category_text": "주거 지원",
            "categories": ["housing"],
            "keywords": ["월세", "월세"],
            "summary": "월세를 지원합니다.",
            "life_stages": ["청년"],
            "target_groups": ["저소득 청년"],
            "age_condition_text": "１９세 이상",
            "eligibility_text": "천안 거주자",
            "education_statuses": [],
            "employment_statuses": ["미취업"],
            "required_conditions": ["무주택"],
            "preferred_conditions": [],
            "excluded_conditions": [],
            "support_content": "월 20만원",
        }
    )

    assert projection == {
        "title_text": "청년 월세 지원",
        "keyword_text": "주거 지원 housing 월세",
        "summary_text": "월세를 지원합니다.",
        "eligibility_text": (
            "청년 저소득 청년 19세 이상 천안 거주자 미취업 무주택"
        ),
        "support_text": "월 20만원",
        "search_text": (
            "청년 월세 지원 주거 지원 housing 월세 "
            "월세를 지원합니다. 청년 저소득 청년 19세 이상 "
            "천안 거주자 미취업 무주택 월 20만원"
        ),
        "projection_version": POLICY_SEARCH_PROJECTION_VERSION,
    }
