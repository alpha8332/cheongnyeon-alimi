from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class CollectionRunAdminItem(BaseModel):
    """CollectionRun 관리자 목록 아이템 DTO."""
    run_id: UUID
    source_id: Optional[str] = None
    run_type: str
    trigger_type: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    is_stale: bool = False
    inserted_count: int = 0
    updated_count: int = 0
    failed_count: int = 0
    error_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CollectionRunAdminDetail(BaseModel):
    """CollectionRun 관리자 단건 상세 DTO."""
    run_id: UUID
    source_id: Optional[str] = None
    run_type: str
    trigger_type: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    is_stale: bool = False
    requested_count: int = 0
    raw_document_count: int = 0
    extracted_count: int = 0
    accepted_count: int = 0
    partial_count: int = 0
    invalid_count: int = 0
    duplicate_count: int = 0
    rejected_count: int = 0
    inserted_count: int = 0
    updated_count: int = 0
    unchanged_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    error_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CollectionRunAdminListResponse(BaseModel):
    """CollectionRun 관리자 목록 조회 응답 DTO (Pagination 포함)."""
    items: List[CollectionRunAdminItem]
    total: int
    page: int
    size: int
    pages: int


class CollectionRunTriggerRequest(BaseModel):
    """CollectionRun 수동 실행 요청 DTO."""
    source_id: Optional[str] = Field(default="youthcenter", description="수동 수집원 ID")
    requested_count: Optional[int] = Field(default=100, ge=1, le=1000, description="수집 요청 문서 수")


class CollectionRunTriggerResponse(BaseModel):
    """CollectionRun 수동 실행 요청 응답 DTO (202 Accepted)."""
    run_id: UUID
    source_id: Optional[str] = None
    run_type: str = "collection"
    trigger_type: str = "admin"
    status: str = "running"
    started_at: datetime
    message: str = "Manual collection run initiated successfully."
