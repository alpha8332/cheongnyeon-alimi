from typing import Literal
from pydantic import BaseModel, Field


class AdminSessionCreate(BaseModel):
    """관리자 세션 생성(로그인) 요청 DTO."""
    pin: str = Field(
        ...,
        min_length=4,
        max_length=4,
        pattern=r"^\d{4}$",
        description="4자리 숫자 관리자 PIN",
        examples=["0000"],
    )


class AdminSessionResponse(BaseModel):
    """관리자 세션 생성 성공 응답 DTO."""
    access_token: str = Field(..., description="관리자 인증 세션 토큰")
    token_type: Literal["bearer"] = Field("bearer", description="토큰 타입")
    expires_in: int = Field(..., description="토큰 만료 시간(초)")
    role: Literal["admin"] = Field("admin", description="인증된 사용자 역할")


class AdminPinChange(BaseModel):
    """Authenticated administrator PIN change request."""

    current_pin: str = Field(
        ...,
        min_length=4,
        max_length=4,
        pattern=r"^\d{4}$",
        description="현재 4자리 숫자 관리자 PIN",
    )
    new_pin: str = Field(
        ...,
        min_length=4,
        max_length=4,
        pattern=r"^\d{4}$",
        description="새 4자리 숫자 관리자 PIN",
    )


class AdminErrorDetail(BaseModel):
    """관리자 API 표준 에러 세부사항 DTO."""
    message: str = Field(..., description="오류 메시지")
    details: dict = Field(default_factory=dict, description="추가 오류 세부 정보")


class AdminErrorResponse(BaseModel):
    """관리자 API 표준 에러 응답 DTO."""
    error: AdminErrorDetail
