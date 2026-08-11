from typing import List
from app.models.policy import Policy
from app.schemas.policy import (
    EligibilitySummaryResponse,
    ItemCondition,
    ItemDocument,
    ItemEvidence,
    InstitutionalContact,
)


def build_eligibility_summary(policy: Policy) -> EligibilitySummaryResponse:
    """Policy ORM 모델로부터 구조화된 EligibilitySummaryResponse DTO를 생성한다."""
    evidence = ItemEvidence(
        source_id=policy.source_id,
        source_url=policy.source_url,
        collected_at=policy.collected_at.isoformat() if policy.collected_at else "",
    )

    requirements: List[ItemCondition] = []
    exclusions: List[ItemCondition] = []
    preferences: List[ItemCondition] = []
    required_documents: List[ItemDocument] = []
    unknown_conditions: List[str] = [
        "소득 및 자산 세부 자격 요건은 원문 확인이 필요합니다."
    ]
    institutional_contacts: List[InstitutionalContact] = []

    # 1. 연령 조건
    if policy.age_min is not None or policy.age_max is not None or policy.age_condition_text:
        age_text = policy.age_condition_text or f"만 {policy.age_min or 0}세 ~ 만 {policy.age_max or 120}세"
        requirements.append(
            ItemCondition(
                category="age",
                content=f"연령 조건: {age_text}",
                evidence=evidence,
            )
        )

    # 2. 거주지 조건
    if policy.regions or policy.region_text:
        reg_text = policy.region_text or (", ".join(policy.regions) if policy.regions else "전국")
        requirements.append(
            ItemCondition(
                category="region",
                content=f"거주지 조건: {reg_text}",
                evidence=evidence,
            )
        )

    # 3. 필수 조건 목록
    if policy.required_conditions:
        for cond in policy.required_conditions:
            requirements.append(
                ItemCondition(
                    category="other",
                    content=str(cond),
                    evidence=evidence,
                )
            )

    # 4. 제외 조건 목록
    if policy.excluded_conditions:
        for cond in policy.excluded_conditions:
            exclusions.append(
                ItemCondition(
                    category="other",
                    content=str(cond),
                    evidence=evidence,
                )
            )

    # 5. 우대 조건 목록
    if policy.preferred_conditions:
        for cond in policy.preferred_conditions:
            preferences.append(
                ItemCondition(
                    category="other",
                    content=str(cond),
                    evidence=evidence,
                )
            )

    # 6. 기관 정보가 있는 경우 문의처 생성
    if policy.organization:
        institutional_contacts.append(
            InstitutionalContact(
                label=policy.organization,
                value="공식 원문 페이지 참조",
                contact_type="url",
            )
        )

    # status 판정: 조건 항목이 2개 이상이면 complete, 1개 이상이면 partial, 없으면 unknown
    total_conditions_count = len(requirements) + len(exclusions) + len(preferences)
    if total_conditions_count >= 3:
        summary_status = "complete"
    elif total_conditions_count >= 1:
        summary_status = "partial"
    else:
        summary_status = "unknown"

    return EligibilitySummaryResponse(
        status=summary_status,
        requirements=requirements,
        exclusions=exclusions,
        preferences=preferences,
        required_documents=required_documents,
        unknown_conditions=unknown_conditions,
        institutional_contacts=institutional_contacts,
    )
