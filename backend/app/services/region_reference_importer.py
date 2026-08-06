from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.administrative_region import (
    AdministrativeRegion,
    AdministrativeRegionAlias,
)
from collectors.regions import RegionReference


class RegionReferenceImportError(RuntimeError):
    """Raised when a versioned DB reference differs from its locked Seed."""


@dataclass(frozen=True, slots=True)
class RegionReferenceImportResult:
    scheme: str
    inserted_regions: int
    unchanged_regions: int
    inserted_aliases: int
    unchanged_aliases: int
    committed: bool
    dry_run: bool


class _DryRunRollback(Exception):
    """Internal control flow for a successful region-reference dry run."""


def _region_values(region) -> dict:
    return {
        "scheme": region.scheme,
        "code": region.code,
        "name": region.name,
        "full_name": region.full_name,
        "level": region.level.value,
        "status": region.status.value,
        "parent_code": region.parent_code,
        "aggregate_parent_code": region.aggregate_parent_code,
        "source_parent_code": region.source_parent_code,
        "valid_from": region.valid_from,
        "valid_to": region.valid_to,
        "external_codes": dict(region.external_codes),
    }


def _stored_region_values(region: AdministrativeRegion) -> dict:
    return {
        column.name: getattr(region, column.name)
        for column in AdministrativeRegion.__table__.columns
    }


def _alias_identity(alias) -> tuple[str, str, str, str]:
    return (alias.scheme, alias.alias, alias.region_code, alias.kind)


def import_region_reference(
    db: Session,
    regions_path: Path,
    aliases_path: Path,
    *,
    dry_run: bool = False,
) -> RegionReferenceImportResult:
    reference = RegionReference.from_seed_files(regions_path, aliases_path)
    incoming_regions = {
        region.code: _region_values(region)
        for region in reference.regions
    }
    incoming_aliases = {
        _alias_identity(alias)
        for alias in reference.aliases
    }
    inserted_regions = 0
    unchanged_regions = 0
    inserted_aliases = 0
    unchanged_aliases = 0

    try:
        with db.begin():
            stored_regions = {
                region.code: region
                for region in db.scalars(
                    select(AdministrativeRegion).where(
                        AdministrativeRegion.scheme == reference.scheme
                    )
                )
            }
            unexpected_codes = set(stored_regions) - set(incoming_regions)
            if unexpected_codes:
                raise RegionReferenceImportError(
                    "stored region scheme contains unexpected codes"
                )
            for code, values in incoming_regions.items():
                stored = stored_regions.get(code)
                if stored is None:
                    db.add(AdministrativeRegion(**values))
                    inserted_regions += 1
                elif _stored_region_values(stored) == values:
                    unchanged_regions += 1
                else:
                    raise RegionReferenceImportError(
                        "stored region differs from locked versioned Seed"
                    )
            db.flush()

            stored_aliases = {
                (
                    alias.scheme,
                    alias.alias,
                    alias.region_code,
                    alias.kind,
                )
                for alias in db.scalars(
                    select(AdministrativeRegionAlias).where(
                        AdministrativeRegionAlias.scheme == reference.scheme
                    )
                )
            }
            if stored_aliases - incoming_aliases:
                raise RegionReferenceImportError(
                    "stored region scheme contains unexpected aliases"
                )
            for identity in sorted(incoming_aliases):
                if identity in stored_aliases:
                    unchanged_aliases += 1
                    continue
                scheme, alias, region_code, kind = identity
                db.add(
                    AdministrativeRegionAlias(
                        scheme=scheme,
                        alias=alias,
                        region_code=region_code,
                        kind=kind,
                    )
                )
                inserted_aliases += 1
            db.flush()
            if dry_run:
                raise _DryRunRollback
    except _DryRunRollback:
        pass

    return RegionReferenceImportResult(
        scheme=reference.scheme,
        inserted_regions=inserted_regions,
        unchanged_regions=unchanged_regions,
        inserted_aliases=inserted_aliases,
        unchanged_aliases=unchanged_aliases,
        committed=not dry_run,
        dry_run=dry_run,
    )
