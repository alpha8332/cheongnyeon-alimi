import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from app.models.policy import Policy


def parse_date(date_str: Any) -> Any:
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_datetime(dt_str: Any) -> datetime:
    if not dt_str or not isinstance(dt_str, str):
        return datetime.now(timezone.utc)
    try:
        # ISO format datetime parsing
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def import_seed_data(db: Session, seed_file_path: Path) -> Tuple[int, int, int]:
    """
    canonical JSON Seed 파일을 읽어 DB에 Upsert 방식으로 적재하는 서비스 함수
    Returns: (total_count, inserted_count, updated_count)
    """
    if not seed_file_path.exists():
        raise FileNotFoundError(f"Seed file not found at: {seed_file_path}")

    with open(seed_file_path, "r", encoding="utf-8") as f:
        seed_data: List[Dict[str, Any]] = json.load(f)

    inserted_count = 0
    updated_count = 0

    for item in seed_data:
        source_id = item.get("source_id")
        external_id = item.get("external_id")

        if not source_id:
            continue

        # 기존 레코드 검색 (source_id + external_id 2-A Upsert)
        existing = db.query(Policy).filter(
            Policy.source_id == source_id,
            Policy.external_id == external_id,
        ).first()

        policy_dict = {
            "schema_version": item.get("schema_version", "1.0.0"),
            "source_id": source_id,
            "source_name": item.get("source_name", ""),
            "external_id": external_id,
            "title": item.get("title", ""),
            "organization": item.get("organization"),
            "summary": item.get("summary"),
            "category_text": item.get("category_text"),
            "categories": item.get("categories", []),
            # 5-A 원문 텍스트 보존
            "application_period_text": item.get("application_period_text"),
            # 5-A Date 객체 파싱
            "application_start": parse_date(item.get("application_start")),
            "application_end": parse_date(item.get("application_end")),
            "application_schedule": item.get("application_schedule"),
            "application_status": item.get("application_status"),
            "region_text": item.get("region_text"),
            "regions": item.get("regions", []),
            "age_min": item.get("age_min"),
            "age_max": item.get("age_max"),
            "age_condition_text": item.get("age_condition_text"),
            "eligibility_text": item.get("eligibility_text"),
            "support_content": item.get("support_content"),
            "application_method": item.get("application_method"),
            "education_statuses": item.get("education_statuses", []),
            "employment_statuses": item.get("employment_statuses", []),
            "required_conditions": item.get("required_conditions", []),
            "preferred_conditions": item.get("preferred_conditions", []),
            "excluded_conditions": item.get("excluded_conditions", []),
            "source_url": item.get("source_url", ""),
            "collected_at": parse_datetime(item.get("collected_at")),
            "provenance": item.get("provenance", []),  # 4-A DB 전량 보존
            "data_quality_status": item.get("data_quality_status", "valid"),
            "updated_at": datetime.now(timezone.utc),
        }

        if existing:
            for key, val in policy_dict.items():
                setattr(existing, key, val)
            updated_count += 1
        else:
            new_policy = Policy(**policy_dict)
            db.add(new_policy)
            inserted_count += 1

    db.commit()
    return len(seed_data), inserted_count, updated_count
