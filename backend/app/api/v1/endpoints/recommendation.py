from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation import recommend_policies_service

router = APIRouter()


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="맞춤 정책 추천 API (POST)",
    responses={
        200: {"description": "맞춤 정책 추천 성공"},
        422: {"description": "파라미터 유효성 검사 실패"},
    },
)
def post_recommendations(
    request: RecommendationRequest = RecommendationRequest(),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    """
    사용자 조건(연령, 거주지, 관심분야, 신청상태 등)을 기반으로 결정적 규칙에 따라 추천 정책을 반환한다.
    - 정렬: score DESC, id ASC (결정적 순서 보장)
    - 비단정 안내 문구(disclaimer) 및 추천 사유(reasons), 미확정 조건(unknown_conditions)을 포함한다.
    """
    return recommend_policies_service(db=db, request=request)


@router.get(
    "/policies/recommendations",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="맞춤 정책 추천 API (GET Query)",
    responses={
        200: {"description": "맞춤 정책 추천 성공"},
        422: {"description": "파라미터 유효성 검사 실패"},
    },
)
def get_recommendations(
    age: Optional[int] = Query(default=None, ge=0, le=120, description="사용자 만 연령"),
    region: Optional[str] = Query(default=None, description="거주지"),
    category: Optional[str] = Query(default=None, description="관심 분야"),
    status_param: Optional[str] = Query(default=None, alias="status", description="신청 상태 필터"),
    include_partial: bool = Query(default=False, description="partial 포함 여부"),
    limit: int = Query(default=10, ge=1, le=50, description="최대 반환 추천 수"),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    """Query Parameter 방식으로 맞춤 정책 추천을 수행한다."""
    req = RecommendationRequest(
        age=age,
        region=region,
        category=category,
        status=status_param,
        include_partial=include_partial,
        limit=limit,
    )
    return recommend_policies_service(db=db, request=req)
