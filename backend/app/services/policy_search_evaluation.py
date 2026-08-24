from dataclasses import dataclass, replace
from enum import Enum
from typing import Protocol, Sequence

from sqlalchemy.orm import Session

from app.models.administrative_region import AdministrativeRegion
from app.models.policy import APPLICATION_STATUS_VALUES, Policy
from app.repositories.policy_search import PolicySearchRepository
from app.services.policy_search_projection import normalize_search_text


DEFAULT_REGION_SCHEME = "kr-bjd-20260803"


class MatchState(str, Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"


class RegionResolutionState(str, Enum):
    MATCHED = "matched"
    UNMAPPED = "unmapped"
    AMBIGUOUS = "ambiguous"


class RegionDecisionReason(str, Enum):
    EXACT = "exact"
    ANCESTOR = "ancestor"
    DESCENDANT = "descendant"
    NATIONWIDE = "nationwide"
    EXCLUDE = "exclude"
    OTHER_REGION = "other_region"
    QUERY_UNMAPPED = "query_unmapped"
    QUERY_AMBIGUOUS = "query_ambiguous"
    POLICY_UNKNOWN = "policy_unknown"
    UNRESOLVED_RULE = "unresolved_rule"


class AgeDecisionReason(str, Enum):
    WITHIN_RANGE = "within_range"
    UNRESTRICTED = "unrestricted"
    BELOW_MINIMUM = "below_minimum"
    ABOVE_MAXIMUM = "above_maximum"
    MISSING_BOUNDS = "missing_bounds"


class StatusDecisionReason(str, Enum):
    EQUAL = "equal"
    DIFFERENT = "different"
    MISSING_POLICY_STATUS = "missing_policy_status"


class ProjectionField(str, Enum):
    TITLE = "title_text"
    KEYWORD = "keyword_text"
    SUMMARY = "summary_text"
    ELIGIBILITY = "eligibility_text"
    SUPPORT = "support_text"


class SearchProjectionLike(Protocol):
    title_text: str
    keyword_text: str
    summary_text: str
    eligibility_text: str
    support_text: str


@dataclass(frozen=True)
class RegionCandidate:
    scheme: str
    code: str
    name: str
    full_name: str
    level: str
    status: str


@dataclass(frozen=True)
class RegionQueryResolution:
    status: RegionResolutionState
    candidates: tuple[RegionCandidate, ...]


@dataclass(frozen=True)
class RegionRuleEvidence:
    relation: str
    resolution_status: str
    region_scheme: str | None
    region_code: str | None
    region_status: str | None
    source_code: str | None
    source_text: str | None
    province_scheme: str | None = None
    province_code: str | None = None
    match_distance: int | None = None
    query_relation: str | None = None


@dataclass(frozen=True)
class RegionDecision:
    state: MatchState
    reason: RegionDecisionReason
    query: RegionQueryResolution
    evidence: RegionRuleEvidence | None = None


@dataclass(frozen=True)
class AgeDecision:
    state: MatchState
    reason: AgeDecisionReason
    requested_age: int
    age_min: int | None
    age_max: int | None


@dataclass(frozen=True)
class ApplicationStatusDecision:
    state: MatchState
    reason: StatusDecisionReason
    requested_status: str
    policy_status: str | None


@dataclass(frozen=True)
class ProjectionFieldMatch:
    field: ProjectionField
    terms: tuple[str, ...]


@dataclass(frozen=True)
class ProjectionMatchEvidence:
    fields: tuple[ProjectionFieldMatch, ...]
    unmatched_terms: tuple[str, ...]


def evaluate_age_condition(
    *,
    requested_age: int,
    age_min: int | None,
    age_max: int | None,
    age_condition_text: str | None,
) -> AgeDecision:
    if (
        not isinstance(requested_age, int)
        or isinstance(requested_age, bool)
        or not 0 <= requested_age <= 150
    ):
        raise ValueError("requested_age must be an integer from 0 to 150")
    if age_min == 0 and age_max == 0:
        age_min = None
        age_max = None
    if age_min is not None and requested_age < age_min:
        return AgeDecision(
            MatchState.MISMATCH,
            AgeDecisionReason.BELOW_MINIMUM,
            requested_age,
            age_min,
            age_max,
        )
    if age_max is not None and requested_age > age_max:
        return AgeDecision(
            MatchState.MISMATCH,
            AgeDecisionReason.ABOVE_MAXIMUM,
            requested_age,
            age_min,
            age_max,
        )
    if age_min is not None or age_max is not None:
        return AgeDecision(
            MatchState.MATCH,
            AgeDecisionReason.WITHIN_RANGE,
            requested_age,
            age_min,
            age_max,
        )
    normalized_text = normalize_search_text(age_condition_text)
    if normalized_text is not None and "제한 없음" in normalized_text:
        return AgeDecision(
            MatchState.MATCH,
            AgeDecisionReason.UNRESTRICTED,
            requested_age,
            age_min,
            age_max,
        )
    return AgeDecision(
        MatchState.UNKNOWN,
        AgeDecisionReason.MISSING_BOUNDS,
        requested_age,
        age_min,
        age_max,
    )


def evaluate_application_status(
    *,
    requested_status: str,
    policy_status: str | None,
) -> ApplicationStatusDecision:
    if requested_status not in APPLICATION_STATUS_VALUES:
        raise ValueError(
            "requested_status must be open, closed, or scheduled"
        )
    if policy_status is None:
        return ApplicationStatusDecision(
            MatchState.UNKNOWN,
            StatusDecisionReason.MISSING_POLICY_STATUS,
            requested_status,
            policy_status,
        )
    if policy_status == requested_status:
        return ApplicationStatusDecision(
            MatchState.MATCH,
            StatusDecisionReason.EQUAL,
            requested_status,
            policy_status,
        )
    return ApplicationStatusDecision(
        MatchState.MISMATCH,
        StatusDecisionReason.DIFFERENT,
        requested_status,
        policy_status,
    )


def evaluate_region_condition(
    *,
    coverage_scope: str,
    query: RegionQueryResolution,
    query_path: Sequence[RegionCandidate],
    rules: Sequence[RegionRuleEvidence],
) -> RegionDecision:
    if coverage_scope == "nationwide":
        return RegionDecision(
            MatchState.MATCH,
            RegionDecisionReason.NATIONWIDE,
            query,
        )
    if coverage_scope == "unknown":
        return RegionDecision(
            MatchState.UNKNOWN,
            RegionDecisionReason.POLICY_UNKNOWN,
            query,
        )
    if coverage_scope != "regional":
        raise ValueError("unsupported coverage_scope")
    if query.status is RegionResolutionState.UNMAPPED:
        return RegionDecision(
            MatchState.UNKNOWN,
            RegionDecisionReason.QUERY_UNMAPPED,
            query,
        )
    if query.status is RegionResolutionState.AMBIGUOUS:
        return RegionDecision(
            MatchState.UNKNOWN,
            RegionDecisionReason.QUERY_AMBIGUOUS,
            query,
        )
    if not query_path:
        return RegionDecision(
            MatchState.UNKNOWN,
            RegionDecisionReason.QUERY_UNMAPPED,
            query,
        )

    path_distance = {
        (candidate.scheme, candidate.code): distance
        for distance, candidate in enumerate(query_path)
    }
    matched: list[RegionRuleEvidence] = []
    unresolved: list[RegionRuleEvidence] = []
    active_includes = 0
    for rule in rules:
        if (
            rule.resolution_status != "matched"
            or rule.region_scheme is None
            or rule.region_code is None
            or rule.region_status != "active"
        ):
            unresolved.append(rule)
            continue
        if rule.relation == "include":
            active_includes += 1
        distance = path_distance.get(
            (rule.region_scheme, rule.region_code)
        )
        if distance is not None:
            matched.append(
                replace(
                    rule,
                    match_distance=distance,
                    query_relation=("exact" if distance == 0 else "ancestor"),
                )
            )
        elif rule.relation == "include" and rule.query_relation == "descendant":
            # 광역 시·도 또는 aggregate 시를 검색하면 그 하위 시·군·구에
            # 명시적으로 포함된 정책도 발견할 수 있어야 한다. 하위 exclude는
            # 광역 전체를 제외한다는 뜻이 아니므로 여기서는 포함하지 않는다.
            matched.append(rule)

    matching_excludes = sorted(
        (rule for rule in matched if rule.relation == "exclude"),
        key=_evidence_sort_key,
    )
    if matching_excludes:
        return RegionDecision(
            MatchState.MISMATCH,
            RegionDecisionReason.EXCLUDE,
            query,
            matching_excludes[0],
        )

    matching_includes = sorted(
        (rule for rule in matched if rule.relation == "include"),
        key=_evidence_sort_key,
    )
    if matching_includes:
        evidence = matching_includes[0]
        return RegionDecision(
            MatchState.MATCH,
            (
                RegionDecisionReason.DESCENDANT
                if evidence.query_relation == "descendant"
                else (
                    RegionDecisionReason.EXACT
                    if evidence.match_distance == 0
                    else RegionDecisionReason.ANCESTOR
                )
            ),
            query,
            evidence,
        )
    query_province = next(
        (
            (candidate.scheme, candidate.code)
            for candidate in query_path
            if candidate.level == "province"
        ),
        None,
    )
    relevant_unresolved = [
        rule
        for rule in unresolved
        if query_province is None
        or rule.province_scheme is None
        or rule.province_code is None
        or (rule.province_scheme, rule.province_code) == query_province
    ]
    if relevant_unresolved or active_includes == 0:
        evidence = (
            sorted(relevant_unresolved, key=_evidence_sort_key)[0]
            if relevant_unresolved
            else None
        )
        return RegionDecision(
            MatchState.UNKNOWN,
            RegionDecisionReason.UNRESOLVED_RULE,
            query,
            evidence,
        )
    return RegionDecision(
        MatchState.MISMATCH,
        RegionDecisionReason.OTHER_REGION,
        query,
    )


def match_projection_fields(
    *,
    document: SearchProjectionLike,
    terms: Sequence[str],
) -> ProjectionMatchEvidence:
    normalized_terms: list[str] = []
    seen: set[str] = set()
    for term in terms:
        normalized = normalize_search_text(term)
        if normalized is not None and normalized not in seen:
            seen.add(normalized)
            normalized_terms.append(normalized)

    field_matches: list[ProjectionFieldMatch] = []
    matched_terms: set[str] = set()
    for field in ProjectionField:
        value = normalize_search_text(getattr(document, field.value, "")) or ""
        folded_value = value.casefold()
        compact_value = folded_value.replace(" ", "")
        selected: list[str] = []
        for term in normalized_terms:
            folded = term.casefold()
            if folded in folded_value or (
                folded.replace(" ", "") in compact_value
            ):
                selected.append(term)
                matched_terms.add(term)
        if selected:
            field_matches.append(
                ProjectionFieldMatch(field, tuple(selected))
            )
    return ProjectionMatchEvidence(
        fields=tuple(field_matches),
        unmatched_terms=tuple(
            term for term in normalized_terms if term not in matched_terms
        ),
    )


def _evidence_sort_key(
    evidence: RegionRuleEvidence,
) -> tuple[int, str, str, str]:
    return (
        evidence.match_distance
        if evidence.match_distance is not None
        else 1_000_000,
        evidence.region_scheme or "",
        evidence.region_code or "",
        evidence.source_text or evidence.source_code or "",
    )


class PolicySearchEvaluationService:
    def __init__(
        self,
        db: Session,
        *,
        region_scheme: str = DEFAULT_REGION_SCHEME,
    ) -> None:
        self.db = db
        self.region_scheme = region_scheme
        self.repository = PolicySearchRepository(db)

    def resolve_region_alias(self, alias: str) -> RegionQueryResolution:
        if not isinstance(alias, str):
            raise TypeError("region alias must be a string")
        normalized = normalize_search_text(alias)
        if normalized is None:
            raise ValueError("region alias must be nonempty")
        candidates = tuple(
            _candidate(region)
            for region in self.repository.alias_candidates(
                scheme=self.region_scheme,
                alias=normalized,
                active_only=True,
            )
        )
        if not candidates:
            status = RegionResolutionState.UNMAPPED
        elif len(candidates) == 1:
            status = RegionResolutionState.MATCHED
        else:
            status = RegionResolutionState.AMBIGUOUS
        return RegionQueryResolution(status, candidates)

    def evaluate_policy_region(
        self,
        policy_id: int,
        query: RegionQueryResolution,
    ) -> RegionDecision:
        policy = self._policy(policy_id)
        rule_models = self.repository.policy_region_rules(policy_id)
        schemes = {
            rule.region_scheme
            for rule in rule_models
            if rule.region_scheme is not None
        }
        schemes.update(candidate.scheme for candidate in query.candidates)
        catalog = {
            (region.scheme, region.code): region
            for region in self.repository.regions_for_schemes(
                tuple(schemes)
            )
        }
        query_path = self._query_path(query, catalog)
        rules = _annotate_descendant_evidence(
            query,
            catalog,
            tuple(
                RegionRuleEvidence(
                    relation=rule.relation,
                    resolution_status=rule.resolution_status,
                    region_scheme=rule.region_scheme,
                    region_code=rule.region_code,
                    region_status=(
                        catalog[(rule.region_scheme, rule.region_code)].status
                        if (
                            rule.region_scheme is not None
                            and rule.region_code is not None
                            and (rule.region_scheme, rule.region_code) in catalog
                        )
                        else None
                    ),
                    source_code=rule.source_code,
                    source_text=rule.source_text,
                    **_province_evidence(
                        rule.region_scheme,
                        rule.region_code,
                        catalog,
                    ),
                )
                for rule in rule_models
            ),
        )
        return evaluate_region_condition(
            coverage_scope=policy.coverage_scope,
            query=query,
            query_path=query_path,
            rules=rules,
        )

    def evaluate_policy_regions(
        self,
        policies: Sequence[Policy],
        query: RegionQueryResolution,
    ) -> dict[int, RegionDecision]:
        """여러 정책의 지역 판정을 rule·region bulk query 두 번으로 계산한다."""
        selected = tuple(policies)
        grouped_rules = self.repository.policy_region_rules_for_policies(
            [policy.id for policy in selected]
        )
        schemes = {
            rule.region_scheme
            for rules in grouped_rules.values()
            for rule in rules
            if rule.region_scheme is not None
        }
        schemes.update(candidate.scheme for candidate in query.candidates)
        catalog = {
            (region.scheme, region.code): region
            for region in self.repository.regions_for_schemes(tuple(schemes))
        }
        query_path = self._query_path(query, catalog)

        decisions: dict[int, RegionDecision] = {}
        for policy in selected:
            evidence = _annotate_descendant_evidence(
                query,
                catalog,
                tuple(
                    RegionRuleEvidence(
                        relation=rule.relation,
                        resolution_status=rule.resolution_status,
                        region_scheme=rule.region_scheme,
                        region_code=rule.region_code,
                        region_status=(
                            catalog[
                                (rule.region_scheme, rule.region_code)
                            ].status
                            if (
                                rule.region_scheme is not None
                                and rule.region_code is not None
                                and (
                                    rule.region_scheme,
                                    rule.region_code,
                                )
                                in catalog
                            )
                            else None
                        ),
                        source_code=rule.source_code,
                        source_text=rule.source_text,
                        **_province_evidence(
                            rule.region_scheme,
                            rule.region_code,
                            catalog,
                        ),
                    )
                    for rule in grouped_rules.get(policy.id, ())
                ),
            )
            decisions[policy.id] = evaluate_region_condition(
                coverage_scope=policy.coverage_scope,
                query=query,
                query_path=query_path,
                rules=evidence,
            )
        return decisions

    def evaluate_policy_age(
        self,
        policy_id: int,
        requested_age: int,
    ) -> AgeDecision:
        policy = self._policy(policy_id)
        return evaluate_age_condition(
            requested_age=requested_age,
            age_min=policy.age_min,
            age_max=policy.age_max,
            age_condition_text=policy.age_condition_text,
        )

    def evaluate_policy_application_status(
        self,
        policy_id: int,
        requested_status: str,
    ) -> ApplicationStatusDecision:
        policy = self._policy(policy_id)
        return evaluate_application_status(
            requested_status=requested_status,
            policy_status=policy.application_status,
        )

    def match_policy_projection(
        self,
        policy_id: int,
        terms: Sequence[str],
    ) -> ProjectionMatchEvidence:
        self._policy(policy_id)
        document = self.repository.search_document(policy_id)
        if document is None:
            raise LookupError("policy search document was not found")
        return match_projection_fields(document=document, terms=terms)

    def _policy(self, policy_id: int) -> Policy:
        policy = self.db.get(Policy, policy_id)
        if policy is None:
            raise LookupError("policy was not found")
        return policy

    @staticmethod
    def _query_path(
        query: RegionQueryResolution,
        catalog: dict[tuple[str, str], AdministrativeRegion],
    ) -> tuple[RegionCandidate, ...]:
        if query.status is not RegionResolutionState.MATCHED:
            return ()
        if len(query.candidates) != 1:
            raise ValueError("matched region query requires one candidate")
        current = query.candidates[0]
        path: list[RegionCandidate] = []
        seen: set[tuple[str, str]] = set()
        while True:
            identity = (current.scheme, current.code)
            if identity in seen:
                raise RuntimeError("region hierarchy contains a cycle")
            seen.add(identity)
            path.append(current)
            model = catalog.get(identity)
            if model is None:
                raise LookupError("region hierarchy row was not found")
            parent_code = (
                model.aggregate_parent_code or model.parent_code
            )
            if parent_code is None:
                break
            parent = catalog.get((current.scheme, parent_code))
            if parent is None:
                raise LookupError("region hierarchy parent was not found")
            current = _candidate(parent)
        return tuple(path)


def _province_evidence(
    scheme: str | None,
    code: str | None,
    catalog: dict[tuple[str, str], AdministrativeRegion],
) -> dict[str, str | None]:
    """Return a canonical province only when the stored hierarchy proves one."""
    if scheme is None or code is None:
        return {"province_scheme": None, "province_code": None}
    current = catalog.get((scheme, code))
    seen: set[tuple[str, str]] = set()
    while current is not None:
        identity = (current.scheme, current.code)
        if identity in seen:
            break
        seen.add(identity)
        if current.level == "province":
            return {
                "province_scheme": current.scheme,
                "province_code": current.code,
            }
        parent_code = current.aggregate_parent_code or current.parent_code
        if parent_code is None:
            break
        current = catalog.get((current.scheme, parent_code))
    return {"province_scheme": None, "province_code": None}


def _annotate_descendant_evidence(
    query: RegionQueryResolution,
    catalog: dict[tuple[str, str], AdministrativeRegion],
    rules: tuple[RegionRuleEvidence, ...],
) -> tuple[RegionRuleEvidence, ...]:
    return tuple(
        replace(
            rule,
            match_distance=distance,
            query_relation="descendant",
        )
        if (
            rule.relation == "include"
            and (distance := _descendant_distance(query, rule, catalog))
            is not None
        )
        else rule
        for rule in rules
    )


def _descendant_distance(
    query: RegionQueryResolution,
    rule: RegionRuleEvidence,
    catalog: dict[tuple[str, str], AdministrativeRegion],
) -> int | None:
    if query.status is not RegionResolutionState.MATCHED:
        return None
    if len(query.candidates) != 1:
        return None
    if rule.region_scheme is None or rule.region_code is None:
        return None

    target = query.candidates[0]
    if rule.region_scheme != target.scheme:
        return None

    current_key = (rule.region_scheme, rule.region_code)
    target_key = (target.scheme, target.code)
    distance = 0
    seen: set[tuple[str, str]] = set()
    while current_key not in seen:
        seen.add(current_key)
        if current_key == target_key:
            return distance if distance > 0 else None
        current = catalog.get(current_key)
        if current is None:
            return None
        parent_code = current.aggregate_parent_code or current.parent_code
        if parent_code is None:
            return None
        current_key = (current.scheme, parent_code)
        distance += 1
    raise RuntimeError("region hierarchy contains a cycle")


def _candidate(region: AdministrativeRegion) -> RegionCandidate:
    return RegionCandidate(
        scheme=region.scheme,
        code=region.code,
        name=region.name,
        full_name=region.full_name,
        level=region.level,
        status=region.status,
    )
