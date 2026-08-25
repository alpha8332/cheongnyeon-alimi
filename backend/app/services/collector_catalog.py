"""Public, secret-free metadata for registered policy collectors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CollectorSourceType = Literal["api", "file", "web"]


@dataclass(frozen=True)
class CollectorDescriptor:
    source_id: str
    display_name: str
    source_type: CollectorSourceType
    credential_required: bool = False


COLLECTOR_CATALOG = (
    CollectorDescriptor(
        "bokjiro-central-welfare-api",
        "복지로 중앙부처 복지서비스",
        "api",
        credential_required=True,
    ),
    CollectorDescriptor(
        "cheonan-youthcenter-web",
        "천안청년센터이음 공지사항",
        "web",
    ),
    CollectorDescriptor(
        "data-go-kr-incheon-youth-programs",
        "인천광역시 청년공간 유유기지 프로그램",
        "file",
    ),
    CollectorDescriptor(
        "kinfa-financial-product-web",
        "서민금융진흥원 금융상품",
        "web",
    ),
    CollectorDescriptor(
        "kosaf-scholarship-web",
        "한국장학재단 장학금",
        "web",
    ),
    CollectorDescriptor(
        "kpass-transit-refund-web",
        "모두의카드 교통비 환급",
        "web",
    ),
    CollectorDescriptor(
        "lh-housing-announcement-web",
        "LH청약플러스 임대주택 공고",
        "web",
    ),
    CollectorDescriptor(
        "regional-busan-youth-platform",
        "부산청년플랫폼",
        "web",
    ),
    CollectorDescriptor(
        "regional-gyeongbuk-youth-platform",
        "경북청년포털 청년e끌림",
        "web",
    ),
    CollectorDescriptor(
        "work24-policy-web",
        "고용24 정책",
        "web",
    ),
    CollectorDescriptor(
        "youthcenter-api",
        "온통청년 청년정책 API",
        "api",
        credential_required=True,
    ),
)

