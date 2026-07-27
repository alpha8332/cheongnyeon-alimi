from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import String

from app.core.database import get_db
from app.models.policy import Policy
from app.schemas.policy import PolicyRead, PolicyListResponse

router = APIRouter()

@router.get("", response_model=PolicyListResponse, summary="정책 목록 조회")
def get_policies(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
    category: Optional[str] = Query(None, description="카테고리 (e.g. housing, employment)"),
    region: Optional[str] = Query(None, description="지역 (e.g. 서울, 전국)"),
    status: Optional[str] = Query(None, description="신청 상태 (e.g. open, closed)"),
    include_partial: bool = Query(False, description="품질 partial 데이터 포함 여부 (기본값: False, valid만)"),
    db: Session = Depends(get_db)
):
    query = db.query(Policy)

    # 3-A: 품질 필터링 (기본적으로 valid 데이터만 노출)
    if not include_partial:
        query = query.filter(Policy.data_quality_status == "valid")
    else:
        query = query.filter(Policy.data_quality_status.in_(["valid", "partial"]))

    # 카테고리 필터
    if category:
        query = query.filter(Policy.categories.cast(String).like(f"%{category}%"))

    # 지역 필터
    if region:
        query = query.filter(Policy.region_text.like(f"%{region}%") | Policy.regions.cast(String).like(f"%{region}%"))

    # 신청 상태 필터
    if status:
        query = query.filter(Policy.application_status == status)

    total = query.count()
    offset = (page - 1) * limit
    items = query.order_by(Policy.id.asc()).offset(offset).limit(limit).all()

    return PolicyListResponse(
        total=total,
        page=page,
        limit=limit,
        items=items
    )

@router.get("/{policy_id}", response_model=PolicyRead, summary="정책 상세 조회")
def get_policy_detail(
    policy_id: int,
    db: Session = Depends(get_db)
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with id {policy_id} not found."
        )
    return policy
