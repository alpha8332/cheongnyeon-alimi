from sqlalchemy import ColumnElement, exists, select

from app.models.public_dataset import (
    PublicDatasetInstallation,
    PublicDatasetMembership,
)


def active_public_dataset_membership_predicate(
    policy_id: ColumnElement[int],
) -> ColumnElement[bool]:
    """Require an exact membership in the one active verified release."""

    return exists(
        select(1)
        .select_from(PublicDatasetMembership)
        .join(
            PublicDatasetInstallation,
            PublicDatasetInstallation.dataset_version
            == PublicDatasetMembership.dataset_version,
        )
        .where(
            PublicDatasetInstallation.status == "active",
            PublicDatasetMembership.policy_id == policy_id,
        )
    )
