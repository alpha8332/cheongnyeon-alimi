from dataclasses import dataclass

from app.models.policy import Policy
from app.repositories.policy import PolicyPage, PolicyRepository


VALID_QUALITY_STATUSES = ("valid",)
PUBLIC_QUALITY_STATUSES = ("valid", "partial")


@dataclass(frozen=True)
class PolicyListRequest:
    page: int
    limit: int
    category: str | None = None
    region: str | None = None
    application_status: str | None = None
    include_partial: bool = False
    sort: str = "default"


class PolicyService:
    def __init__(self, repository: PolicyRepository) -> None:
        self.repository = repository

    @staticmethod
    def quality_statuses(include_partial: bool) -> tuple[str, ...]:
        return (
            PUBLIC_QUALITY_STATUSES
            if include_partial
            else VALID_QUALITY_STATUSES
        )

    def list(self, request: PolicyListRequest) -> PolicyPage:
        return self.repository.list(
            quality_statuses=self.quality_statuses(
                request.include_partial
            ),
            page=request.page,
            limit=request.limit,
            category=request.category,
            region=request.region,
            application_status=request.application_status,
            sort=request.sort,
        )

    def get(
        self,
        policy_id: int,
        *,
        include_partial: bool,
    ) -> Policy | None:
        return self.repository.get_by_id(
            policy_id,
            quality_statuses=self.quality_statuses(include_partial),
        )
