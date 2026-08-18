from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.administrative_region import (
    AdministrativeRegion,
    AdministrativeRegionAlias,
)
from app.models.policy_search import PolicyRegionRule, PolicySearchDocument


REGION_RULE_FIELDS = (
    "relation",
    "resolution_status",
    "region_scheme",
    "region_code",
    "source_code",
    "source_text",
)
SEARCH_DOCUMENT_FIELDS = (
    "title_text",
    "keyword_text",
    "summary_text",
    "eligibility_text",
    "support_text",
    "search_text",
    "projection_version",
)
GENERIC_RELEVANCE_TERMS = frozenset(
    {
        "청년",
        "지원",
        "지원금",
        "정책",
        "사업",
        "혜택",
        "프로그램",
        "정보",
    }
)


def _deduplicated_search_terms(values: Sequence[str]) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for value in values:
        term = value.strip()
        folded = term.casefold()
        if term and folded not in seen:
            seen.add(folded)
            terms.append(term)
    return terms


def _candidate_search_terms(
    uninterpreted_terms: Sequence[str],
    keyword: str | None,
) -> tuple[list[str], bool]:
    all_terms = _deduplicated_search_terms(
        [*uninterpreted_terms, *([keyword] if keyword is not None else [])]
    )
    anchor_terms = [
        term
        for term in all_terms
        if term.casefold() not in GENERIC_RELEVANCE_TERMS
    ]
    if keyword is not None and keyword not in anchor_terms:
        anchor_terms.append(keyword)
    return (anchor_terms or all_terms), bool(anchor_terms)


def _rule_key(value: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(value.get(field) or "") for field in REGION_RULE_FIELDS)


def _normalized_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class PolicySearchRepository:
    """Store policy search relations without owning the transaction."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def region_rule_keys(self, policy_id: int) -> tuple[tuple[str, ...], ...]:
        rules = self.db.scalars(
            select(PolicyRegionRule).where(
                PolicyRegionRule.policy_id == policy_id
            )
        ).all()
        return tuple(
            sorted(
                _rule_key(
                    {
                        field: getattr(rule, field)
                        for field in REGION_RULE_FIELDS
                    }
                )
                for rule in rules
            )
        )

    def policy_region_rules(
        self,
        policy_id: int,
    ) -> tuple[PolicyRegionRule, ...]:
        return tuple(
            self.db.scalars(
                select(PolicyRegionRule)
                .where(PolicyRegionRule.policy_id == policy_id)
                .order_by(PolicyRegionRule.id)
            ).all()
        )

    def policy_region_rules_for_policies(
        self,
        policy_ids: Sequence[int],
    ) -> dict[int, tuple[PolicyRegionRule, ...]]:
        selected_ids = tuple(sorted(set(policy_ids)))
        if not selected_ids:
            return {}
        grouped: dict[int, list[PolicyRegionRule]] = {
            policy_id: [] for policy_id in selected_ids
        }
        rules = self.db.scalars(
            select(PolicyRegionRule)
            .where(PolicyRegionRule.policy_id.in_(selected_ids))
            .order_by(PolicyRegionRule.policy_id, PolicyRegionRule.id)
        ).all()
        for rule in rules:
            grouped[rule.policy_id].append(rule)
        return {
            policy_id: tuple(policy_rules)
            for policy_id, policy_rules in grouped.items()
        }

    def alias_candidates(
        self,
        *,
        scheme: str,
        alias: str,
        active_only: bool = True,
    ) -> tuple[AdministrativeRegion, ...]:
        statement = (
            select(AdministrativeRegion)
            .join(
                AdministrativeRegionAlias,
                (
                    AdministrativeRegionAlias.scheme
                    == AdministrativeRegion.scheme
                )
                & (
                    AdministrativeRegionAlias.region_code
                    == AdministrativeRegion.code
                ),
            )
            .where(
                AdministrativeRegionAlias.scheme == scheme,
                AdministrativeRegionAlias.alias == alias,
            )
            .order_by(AdministrativeRegion.code)
        )
        if active_only:
            statement = statement.where(
                AdministrativeRegion.status == "active"
            )
        return tuple(self.db.scalars(statement).unique().all())

    def regions_for_schemes(
        self,
        schemes: Sequence[str],
    ) -> tuple[AdministrativeRegion, ...]:
        selected_schemes = tuple(sorted(set(schemes)))
        if not selected_schemes:
            return ()
        return tuple(
            self.db.scalars(
                select(AdministrativeRegion)
                .where(AdministrativeRegion.scheme.in_(selected_schemes))
                .order_by(
                    AdministrativeRegion.scheme,
                    AdministrativeRegion.code,
                )
            ).all()
        )

    def search_document(
        self,
        policy_id: int,
    ) -> PolicySearchDocument | None:
        return self.db.get(PolicySearchDocument, policy_id)

    def replace_region_rules(
        self,
        policy_id: int,
        rules: Sequence[Mapping[str, Any]],
    ) -> bool:
        incoming_keys = tuple(sorted(_rule_key(rule) for rule in rules))
        if self.region_rule_keys(policy_id) == incoming_keys:
            return False

        self.db.execute(
            delete(PolicyRegionRule).where(
                PolicyRegionRule.policy_id == policy_id
            )
        )
        self.db.add_all(
            PolicyRegionRule(
                policy_id=policy_id,
                **{
                    field: rule.get(field)
                    for field in REGION_RULE_FIELDS
                },
            )
            for rule in rules
        )
        return True

    def synchronize_document(
        self,
        policy_id: int,
        values: Mapping[str, str],
        *,
        updated_at: datetime,
    ) -> bool:
        document = self.db.get(PolicySearchDocument, policy_id)
        if document is None:
            self.db.add(
                PolicySearchDocument(
                    policy_id=policy_id,
                    **{
                        field: values[field]
                        for field in SEARCH_DOCUMENT_FIELDS
                    },
                    updated_at=updated_at,
                )
            )
            return True

        if all(
            getattr(document, field) == values[field]
            for field in SEARCH_DOCUMENT_FIELDS
        ):
            return False

        for field in SEARCH_DOCUMENT_FIELDS:
            setattr(document, field, values[field])
        if _normalized_datetime(updated_at) > _normalized_datetime(
            document.updated_at
        ):
            document.updated_at = updated_at
        return True

    def search_policies(
        self,
        interpreted: "InterpretedConditions",
        *,
        include_partial: bool = True,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list["PolicySearchResultItem"], int]:
        """PostgreSQL/DB 기반 정책 검색 Query Builder.

        mismatch 항목을 확정 제외하고 4단계 결정적 정렬을 적용한다:
        score DESC -> unknown_count ASC -> status 우선순위 -> policy.id ASC
        """
        from app.models.policy import Policy
        from app.schemas.policy import PolicyRead
        from app.schemas.policy_search import (
            DimensionVerdicts,
            PolicySearchResultItem,
            UnconfirmedCondition,
        )
        from app.services.policy_search_evaluation import (
            AgeDecisionReason,
            MatchState,
            PolicySearchEvaluationService,
            RegionDecisionReason,
            StatusDecisionReason,
        )

        eval_service = PolicySearchEvaluationService(self.db)

        # 1. 차원별 검색 조건 수집
        cond_map = {cond.dimension: cond for cond in interpreted.conditions}
        req_region = cond_map.get("region")
        req_age = cond_map.get("age")
        req_category = cond_map.get("category")
        req_status = cond_map.get("status")
        req_keyword = cond_map.get("keyword")

        # 2. 기본 정책 쿼리 생성
        from sqlalchemy import and_, or_
        query = select(Policy).where(Policy.data_quality_status != "invalid")
        if not include_partial:
            query = query.where(Policy.data_quality_status == "valid")

        # 2-1. 미해석 term과 q/explicit keyword의 SQL 후보 필터링
        keyword_value = (
            str(req_keyword.value) if req_keyword is not None else None
        )
        search_terms = _deduplicated_search_terms(
            [
                *interpreted.uninterpreted_terms,
                *([keyword_value] if keyword_value is not None else []),
            ]
        )
        candidate_terms, require_all_terms = _candidate_search_terms(
            interpreted.uninterpreted_terms,
            keyword_value,
        )

        if candidate_terms:
            term_clauses = []
            for term in candidate_terms:
                term_clean = term.strip()
                if term_clean:
                    pattern = f"%{term_clean}%"
                    term_clauses.append(
                        or_(
                            PolicySearchDocument.search_text.ilike(pattern),
                            Policy.title.ilike(pattern),
                            Policy.summary.ilike(pattern),
                        )
                    )

            if term_clauses:
                query = query.outerjoin(
                    PolicySearchDocument, PolicySearchDocument.policy_id == Policy.id
                ).where(
                    and_(*term_clauses)
                    if require_all_terms
                    else or_(*term_clauses)
                )

        policies = tuple(self.db.scalars(query).all())

        # 지역 조건 사전 해석
        query_resolution = None
        if req_region is not None:
            query_resolution = eval_service.resolve_region_alias(str(req_region.value))

        evaluated_items: list[tuple[float, int, int, int, PolicySearchResultItem]] = []

        for policy in policies:
            verdicts = DimensionVerdicts()
            unconfirmed: list[UnconfirmedCondition] = []
            reason_codes: list[str] = []
            is_mismatch = False

            # --- Status 판정 ---
            if req_status is not None:
                status_dec = eval_service.evaluate_policy_application_status(
                    policy.id, str(req_status.value)
                )
                if status_dec.state == MatchState.MATCH:
                    verdicts.status = "match"
                    reason_codes.append("STATUS_MATCH")
                elif status_dec.state == MatchState.MISMATCH:
                    verdicts.status = "mismatch"
                    is_mismatch = True
                else:
                    verdicts.status = "unknown"
                    reason_codes.append("STATUS_UNKNOWN")
                    unconfirmed.append(
                        UnconfirmedCondition(
                            field="status",
                            reason_code="DATA_MISSING_STATUS",
                            message="신청 기간 또는 신청 상태 정보가 누락되었습니다.",
                        )
                    )
            else:
                # 명시/해석된 status 조건이 없으면 closed 정책은 기본 제외 (mismatch)
                if policy.application_status == "closed":
                    verdicts.status = None
                    is_mismatch = True
                else:
                    verdicts.status = None

            if is_mismatch:
                continue

            # --- Age 판정 ---
            if req_age is not None:
                try:
                    requested_age_int = int(req_age.value)
                    age_dec = eval_service.evaluate_policy_age(
                        policy.id, requested_age_int
                    )
                    if age_dec.state == MatchState.MATCH:
                        verdicts.age = "match"
                        reason_codes.append("AGE_MATCH")
                    elif age_dec.state == MatchState.MISMATCH:
                        verdicts.age = "mismatch"
                        is_mismatch = True
                    else:
                        verdicts.age = "unknown"
                        reason_codes.append("AGE_UNKNOWN")
                        unconfirmed.append(
                            UnconfirmedCondition(
                                field="age",
                                reason_code="DATA_MISSING_AGE",
                                message="연령 제한 근거 데이터가 누락되었습니다.",
                            )
                        )
                except ValueError:
                    verdicts.age = "unknown"
            else:
                verdicts.age = None

            if is_mismatch:
                continue

            # --- Category 판정 ---
            if req_category is not None:
                cat_val = str(req_category.value)
                policy_cats = policy.categories or []
                if isinstance(policy_cats, list) and cat_val in policy_cats:
                    verdicts.category = "match"
                    reason_codes.append("CATEGORY_MATCH")
                elif not policy_cats:
                    verdicts.category = "unknown"
                    reason_codes.append("CATEGORY_UNKNOWN")
                    unconfirmed.append(
                        UnconfirmedCondition(
                            field="category",
                            reason_code="DATA_MISSING_CATEGORY",
                            message="카테고리 분류가 명확하지 않습니다.",
                        )
                    )
                else:
                    verdicts.category = "mismatch"
                    is_mismatch = True
            else:
                verdicts.category = None

            if is_mismatch:
                continue

            # --- Region 판정 ---
            if req_region is not None and query_resolution is not None:
                reg_dec = eval_service.evaluate_policy_region(
                    policy.id, query_resolution
                )
                if reg_dec.state == MatchState.MATCH:
                    verdicts.region = "match"
                    reason_codes.append("REGION_MATCH")
                elif reg_dec.state == MatchState.MISMATCH:
                    verdicts.region = "mismatch"
                    is_mismatch = True
                else:
                    verdicts.region = "unknown"
                    if req_region.source == "explicit":
                        is_mismatch = True
                    else:
                        reason_codes.append("REGION_UNKNOWN")
                        unconfirmed.append(
                            UnconfirmedCondition(
                                field="region",
                                reason_code="DATA_MISSING_REGION",
                                message="지역 제한 근거 데이터가 누락되었습니다.",
                            )
                        )
            else:
                verdicts.region = None

            if is_mismatch:
                continue

            # Partial 데이터 추가 안내
            if policy.data_quality_status == "partial":
                unconfirmed.append(
                    UnconfirmedCondition(
                        field="general",
                        reason_code="PARTIAL_POLICY_DATA",
                        message="partial 품질 등급 정책으로 일부 정보가 유보되었습니다.",
                    )
                )

            # unknown_count 계산 (null 제외)
            v_list = [verdicts.region, verdicts.age, verdicts.status, verdicts.category]
            unknown_count = sum(1 for v in v_list if v == "unknown")

            # --- Score 및 relevance 계산 ---
            score = 1.0
            if search_terms:
                doc = self.search_document(policy.id)
                if doc is not None:
                    evidence = eval_service.match_policy_projection(
                        policy.id, search_terms
                    )
                    if not evidence.fields and not any(t.lower() in (policy.title or "").lower() or t.lower() in (policy.summary or "").lower() for t in search_terms):
                        # 검색어가 주어졌으나 projection 및 title/summary에서 단 한 개 토큰도 매칭되지 않은 경우 제외
                        continue
                    score += len(evidence.fields) * 2.0
                    for field_match in evidence.fields:
                        score += len(field_match.terms) * 1.0

            # status 정렬 순위: open(0) > scheduled(1) > null/unknown(2) > closed(3)
            status_order = 2
            if policy.application_status == "open":
                status_order = 0
            elif policy.application_status == "scheduled":
                status_order = 1
            elif policy.application_status == "closed":
                status_order = 3

            msg = f"{policy.title} - 판정 완료"
            item = PolicySearchResultItem(
                policy=PolicyRead.model_validate(policy),
                score=score,
                verdicts=verdicts,
                unknown_count=unknown_count,
                reason_codes=reason_codes,
                message=msg,
                unconfirmed_conditions=unconfirmed,
            )

            evaluated_items.append((score, unknown_count, status_order, policy.id, item))

        # 4단계 결정적 정렬: score DESC -> unknown_count ASC -> status_order ASC -> policy.id ASC
        evaluated_items.sort(
            key=lambda x: (-x[0], x[1], x[2], x[3])
        )

        total = len(evaluated_items)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_items = [x[4] for x in evaluated_items[start_idx:end_idx]]

        return paginated_items, total
