from datetime import datetime, date
from typing import Optional, List, Any, Dict
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, UniqueConstraint, Index, JSON
from app.core.database import Base

class Policy(Base):
    """
    청년 정책 ORM 모델 (NormalizedProgram 1.0.0 스키마 준수)
    """
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 식별 및 출처
    schema_version = Column(String(32), nullable=False, default="1.0.0")
    source_id = Column(String(128), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)
    external_id = Column(String(512), nullable=True, index=True)
    
    # 핵심 기본 정보
    title = Column(String(1000), nullable=False)
    organization = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    
    # 카테고리
    category_text = Column(String(255), nullable=True)
    categories = Column(JSON, nullable=False, default=list)
    
    # 신청 기간 및 일정
    application_period_text = Column(String(512), nullable=True)  # raw_apply_period
    application_start = Column(Date, nullable=True)
    application_end = Column(Date, nullable=True)
    application_schedule = Column(String(64), nullable=True)  # fixed_period, always, until_budget_exhausted
    application_status = Column(String(64), nullable=True)    # open, closed, scheduled
    
    # 지역
    region_text = Column(String(255), nullable=True)
    regions = Column(JSON, nullable=False, default=list)
    
    # 자격 요건 (연령, 학력, 취업 등)
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    age_condition_text = Column(Text, nullable=True)
    eligibility_text = Column(Text, nullable=True)
    
    # 지원 내용 및 신청 방법
    support_content = Column(Text, nullable=True)
    application_method = Column(Text, nullable=True)
    
    # 조건 세부 목록
    education_statuses = Column(JSON, nullable=False, default=list)
    employment_statuses = Column(JSON, nullable=False, default=list)
    required_conditions = Column(JSON, nullable=False, default=list)
    preferred_conditions = Column(JSON, nullable=False, default=list)
    excluded_conditions = Column(JSON, nullable=False, default=list)
    
    # 수집 메타데이터 & Provenance (4-A)
    source_url = Column(String(2048), nullable=False)
    collected_at = Column(DateTime, nullable=False)
    provenance = Column(JSON, nullable=False, default=list)
    
    # 품질 상태 (3-A: valid, partial, invalid)
    data_quality_status = Column(String(32), nullable=False, index=True)
    
    # DB 이력 시각
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # (source_id, external_id) 복합 고유 인덱스 (2-A)
        UniqueConstraint("source_id", "external_id", name="uq_policy_source_external"),
        Index("idx_policy_quality_status", "data_quality_status"),
    )
