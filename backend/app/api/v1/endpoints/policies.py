from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter()

@router.get("", summary="정책 목록 조회 Stub")
def list_policies() -> Dict[str, Any]:
    """
    청년정책 목록 조회 API Stub (구현 초기 단계)
    """
    return {
        "total": 0,
        "items": []
    }
