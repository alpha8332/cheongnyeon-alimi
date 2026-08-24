from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class LogFileItem(BaseModel):
    """로그 파일 단건 정보 DTO."""
    file_id: str = Field(description="안전한 파일 식별자 (예: app.log, app.log.1)")
    filename: str
    size_bytes: int
    is_active: bool = Field(description="현재 기록 중인 활성 파일 여부")
    modified_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LogFileListResponse(BaseModel):
    """로그 파일 목록 응답 DTO."""
    files: List[LogFileItem]


class LogEventItem(BaseModel):
    """파싱된 구조화 JSON 로그 이벤트 DTO."""
    timestamp: str
    level: LogLevel
    component: str = "app"
    event: str
    request_id: Optional[str] = None
    collection_run_id: Optional[str] = None
    source_id: Optional[str] = None
    duration_ms: Optional[float] = None
    error_type: Optional[str] = None


class LogEventListResponse(BaseModel):
    """파싱된 로그 이벤트 목록 응답 DTO."""
    total: int
    page: int
    limit: int
    events: List[LogEventItem]


class LogDeleteResponse(BaseModel):
    """로그 Archive 파일 삭제 및 감사 결과 DTO."""
    file_id: str
    deleted: bool
    audit_id: str = Field(description="생성된 삭제 감사 기록 ID")
    message: str


class LogRotateResponse(BaseModel):
    """Result of rotating and clearing only the current application log."""

    rotated_file_id: str = Field(description="Active log file recreated after rotation")
    deleted_archive_file_id: str = Field(
        description="Archive created from the active log and then deleted"
    )
    audit_id: str = Field(description="Audit trail ID for the rotate-and-clear action")
    message: str
