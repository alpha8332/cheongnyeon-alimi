"""Build the deterministic Data 06 candidate and Source inventory from XLSX."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import tempfile
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from xml.etree import ElementTree
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT / "data/reference/supplemental_official_policy_inventory.json"
)
EXPECTED_SHA256 = (
    "c03aa55fba844639a89a4f62ec083dc74c5397b3ea7fbfab91450fbef97f2095"
)
SHEET_NAME = "청년정책 세부 수집방안"
SHEET_RANGE = "A1:F71"
HEADERS = (
    "정책 분야",
    "정책명",
    "기관명",
    "수집 방법 (가능한 모든 방법)",
    "정책 설명 링크",
    "비고 (신청 필요 서류 및 안내)",
)
XML_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}


HOST_GROUPS = {
    "www.bokjiro.go.kr": "approved-aggregator-comparison",
    "www.youthcenter.go.kr": "approved-aggregator-comparison",
    "www.work24.go.kr": "work24-policy",
    "apply.lh.or.kr": "lh-housing-announcements",
    "www.k-startup.go.kr": "k-startup-announcements",
    "www.kosaf.go.kr": "kosaf-scholarships",
    "fill4young.kinfa.or.kr": "kinfa-financial-products",
    "www.kinfa.or.kr": "kinfa-financial-products",
    "enhuf.molit.go.kr": "housing-fund-products",
    "www.molit.go.kr": "housing-fund-products",
    "www.gov.kr": "government-data-and-service",
    "www.data.go.kr": "government-data-and-service",
    "mois.go.kr": "central-ministry-boards",
    "www.mofa.go.kr": "central-ministry-boards",
    "job.kosmes.or.kr": "employment-business-portals",
    "www.sbcplan.or.kr": "employment-business-portals",
    "pms.ripc.org": "education-and-training-portals",
    "www.nais.or.kr": "education-and-training-portals",
    "www.matchup.kr": "education-and-training-portals",
    "www.kmooc.kr": "education-and-training-portals",
    "www.all.go.kr": "education-and-training-portals",
    "www.nia.or.kr": "education-and-training-portals",
    "www.kofpi.or.kr": "education-and-training-portals",
    "ccei.creativekorea.or.kr": "regional-discovery-seed",
    "cyber.ccrs.or.kr": "counseling-and-support-sites",
    "www.rainbowyouth.or.kr": "counseling-and-support-sites",
    "www.artloan.kr": "culture-and-benefit-sites",
    "edu.kobaco.co.kr": "culture-and-benefit-sites",
    "www.ncas.or.kr": "culture-and-benefit-sites",
    "youthculturepass.or.kr": "culture-and-benefit-sites",
    "www.foodvoucher.go.kr": "culture-and-benefit-sites",
    "korea-pass.kr": "kpass-transit-refund",
}


def _budget() -> dict[str, int]:
    return {
        "max_list_requests": 1,
        "max_detail_requests": 3,
        "minimum_interval_seconds": 2,
    }


SOURCE_GROUPS = {
    "approved-aggregator-comparison": {
        "operator": "한국고용정보원·보건복지부/한국사회보장정보원",
        "status": "rejected",
        "implementation_status": "rejected",
        "source_id": None,
        "decision_reason": (
            "이미 승인·구현된 온통청년/복지로 Source의 직접 링크다. "
            "새 Adapter가 아니라 SOP1 exact-ID 비교 fixture로만 사용한다."
        ),
        "robots": ("allowed", "https://www.youthcenter.go.kr/robots.txt"),
        "terms": ("restricted", "https://www.youthcenter.go.kr/"),
        "license": ("restricted", "https://www.youthcenter.go.kr/"),
        "technical_access": "available",
        "list_urls": [],
        "detail_patterns": [],
        "external_identity": None,
        "request_budget": None,
        "resume_condition": "없음. 기존 승인 Source와 DB row를 유지한다.",
    },
    "work24-policy": {
        "operator": "고용노동부·한국고용정보원",
        "status": "approved",
        "implementation_status": "implemented_http",
        "source_id": "work24-policy-web",
        "decision_reason": (
            "공개 고용정책 목록과 systId 상세가 재현되고 대상 경로가 robots에서 "
            "차단되지 않는다. 저작권정책에 따라 출처를 남긴 최소 정책 사실만 수집한다."
        ),
        "robots": ("allowed", "https://www.work24.go.kr/robots.txt"),
        "terms": (
            "restricted",
            "https://www.work24.go.kr/cm/c/d/0130/retrieveUtzeStpt.do",
        ),
        "license": (
            "allowed_with_attribution",
            "https://m.work24.go.kr/cm/c/d/0130/retrieveCpyrPoly.do",
        ),
        "technical_access": "available",
        "list_urls": [
            "https://www.work24.go.kr/cm/c/f/1100/selecPolicyInfo.do"
        ],
        "detail_patterns": [
            "https://www.work24.go.kr/cm/c/f/1100/"
            "selecSystInfo.do?systId={SI followed by digits}"
        ],
        "external_identity": "systId",
        "request_budget": _budget(),
        "resume_condition": None,
    },
    "lh-housing-announcements": {
        "operator": "한국토지주택공사",
        "status": "approved",
        "implementation_status": "implemented_http",
        "source_id": "lh-housing-announcement-web",
        "decision_reason": (
            "공개 임대주택 공고 목록과 panId 상세가 재현되고 robots는 로그인·파일 "
            "경로만 제한한다. 첨부를 내려받지 않고 공개 HTML의 최소 사실만 수집한다."
        ),
        "robots": ("allowed", "https://apply.lh.or.kr/robots.txt"),
        "terms": ("restricted", "https://apply.lh.or.kr/lhapply/"),
        "license": ("restricted", "https://apply.lh.or.kr/lhapply/"),
        "technical_access": "available",
        "list_urls": [
            "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1026"
        ],
        "detail_patterns": [
            "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/"
            "selectWrtancInfo.do?panId={non_empty}&aisTpCd={non_empty}"
            "&uppAisTpCd={non_empty}&ccrCnntSysDsCd={non_empty}"
        ],
        "external_identity": "panId",
        "request_budget": _budget(),
        "resume_condition": None,
    },
    "k-startup-announcements": {
        "operator": "중소벤처기업부·창업진흥원",
        "status": "blocked",
        "implementation_status": "blocked",
        "source_id": None,
        "decision_reason": (
            "robots.txt가 XLSX의 webCMRCZN, bizpbanc-ongoing, "
            "bizpbanc-deadline 경로를 명시적으로 차단한다. 우회하지 않는다."
        ),
        "robots": ("disallowed", "https://www.k-startup.go.kr/robots.txt"),
        "terms": ("restricted", "https://www.k-startup.go.kr/web/main/index.do"),
        "license": ("not_found", "https://www.k-startup.go.kr/web/main/index.do"),
        "technical_access": "blocked",
        "list_urls": [],
        "detail_patterns": [],
        "external_identity": None,
        "request_budget": None,
        "resume_condition": "운영 주체의 API 승인 또는 robots 경로 변경을 공식 확인한다.",
    },
    "kosaf-scholarships": {
        "operator": "한국장학재단",
        "status": "approved",
        "implementation_status": "implemented_http",
        "source_id": "kosaf-scholarship-web",
        "decision_reason": (
            "robots가 공개 경로를 허용하고 장학금 landing/detail의 pg identity와 "
            "신청 기간이 공개 HTML에서 재현된다. 원문을 복제하지 않고 최소 사실만 수집한다."
        ),
        "robots": ("allowed", "https://www.kosaf.go.kr/robots.txt"),
        "terms": ("restricted", "https://www.kosaf.go.kr/ko/agreement.do"),
        "license": ("restricted", "https://www.kosaf.go.kr/ko/customer.do"),
        "technical_access": "available",
        "list_urls": [
            "https://www.kosaf.go.kr/ko/scholar.do?pg=scholarship_submain01"
        ],
        "detail_patterns": [
            "https://www.kosaf.go.kr/ko/scholar.do?pg={approved scholarship page key}"
        ],
        "external_identity": "pg",
        "request_budget": _budget(),
        "resume_condition": None,
    },
    "kinfa-financial-products": {
        "operator": "서민금융진흥원",
        "status": "approved",
        "implementation_status": "implemented_http",
        "source_id": "kinfa-financial-product-web",
        "decision_reason": (
            "robots가 공개 금융상품 경로를 허용하고 공식 전체보기와 개별 상품 "
            "페이지가 재현된다. 인증·상담 경로는 수집하지 않는다."
        ),
        "robots": ("allowed", "https://www.kinfa.or.kr/robots.txt"),
        "terms": ("restricted", "https://www.kinfa.or.kr/"),
        "license": ("restricted", "https://www.kinfa.or.kr/"),
        "technical_access": "available",
        "list_urls": [
            "https://www.kinfa.or.kr/financialProduct/peopleFinancial.do"
        ],
        "detail_patterns": [
            "https://www.kinfa.or.kr/financialProduct/{approved product page}.do"
        ],
        "external_identity": "detail-page-key",
        "request_budget": _budget(),
        "resume_condition": None,
    },
    "kpass-transit-refund": {
        "operator": (
            "국토교통부 대도시권광역위원회·한국교통안전공단·전국 지자체"
        ),
        "status": "approved",
        "implementation_status": "implemented_http",
        "source_id": "kpass-transit-refund-web",
        "decision_reason": (
            "공개 홈의 모두의카드소개 링크와 intro 상세, 가입조건 상세가 stable path로 "
            "재현된다. robots는 공개 경로를 허용하며 로그인·가입 요청 없이 최소 정책 "
            "사실만 수집한다. 후보는 실제 aggregator 중복 Gate에서 별도 판정한다."
        ),
        "robots": ("allowed", "https://korea-pass.kr/robots.txt"),
        "terms": ("restricted", "https://korea-pass.kr/term/term01.do"),
        "license": ("restricted", "https://korea-pass.kr/"),
        "technical_access": "available",
        "list_urls": ["https://korea-pass.kr/"],
        "detail_patterns": [
            "https://korea-pass.kr/info/intro.do",
            "https://korea-pass.kr/info/use_join.do",
        ],
        "external_identity": "static-program-page:intro",
        "request_budget": _budget(),
        "resume_condition": None,
        "checked_at": "2026-08-17T15:05:06+09:00",
    },
}


REJECTED_GROUPS = {
    "housing-fund-products": (
        "국토교통부·주택도시기금",
        "XLSX가 서로 다른 상품에 같은 범용 홈 URL을 사용해 stable detail identity를 확정할 수 없다.",
        "공식 상품 목록과 상품별 stable detail identity를 별도 재탐색한다.",
    ),
    "government-data-and-service": (
        "정부24·공공데이터포털",
        "정책 상세 1건과 범용 포털 홈뿐이며 Data 06용 목록·상세 계약이 없다.",
        "승인된 정책 API 또는 목록 dataset 식별자를 확보한다.",
    ),
    "central-ministry-boards": (
        "행정안전부·외교부",
        "서로 다른 운영자의 단일 게시물 seed로 공통 Source 계약을 만들 수 없다.",
        "운영자별 목록과 stable 게시물 identity를 분리 검증한다.",
    ),
    "employment-business-portals": (
        "중소벤처기업진흥공단·중소벤처기업부",
        "사업 소개 landing만 있고 청년 정책의 결정적 목록·상세 계약이 없다.",
        "현재 모집 목록과 공고 identity를 공식 경로에서 확인한다.",
    ),
    "education-and-training-portals": (
        "교육·훈련 공공기관 다수",
        "운영자가 다른 landing·단일 상세를 한 Source로 승인할 수 없다.",
        "운영자별 Source profile과 현재 모집 경계를 각각 만든다.",
    ),
    "regional-discovery-seed": (
        "부산창조경제혁신센터",
        "Data 05 부산 inventory에 discovery seed로 이미 이관됐으며 중앙 보완 Source가 아니다.",
        "Data 05의 지역 Source 경계에서만 재검토한다.",
    ),
    "counseling-and-support-sites": (
        "신용회복위원회·이주배경청소년지원재단",
        "신청·상담 form 또는 단일 안내만 있어 공개 정책 목록 identity가 없다.",
        "개인정보 없는 공식 정책 목록과 상세를 별도로 확인한다.",
    ),
    "culture-and-benefit-sites": (
        "문화·교통·식품 지원 운영기관 다수",
        "운영자와 신청 경계가 다른 단일 페이지 묶음이라 공통 Source 계약을 승인할 수 없다.",
        "운영자별 공식 목록·상세·현재 신청 기간을 분리 검증한다.",
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xlsx", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = args.xlsx.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"unexpected XLSX sha256: {digest}")
    rows = _read_sheet(payload, SHEET_NAME)
    inventory = build_inventory(args.xlsx.name, digest, rows)
    _atomic_write(args.output, inventory)
    print(
        "supplemental inventory "
        f"url_rows={inventory['quality_summary']['url_row_count']} "
        f"candidates={inventory['quality_summary']['candidate_identity_count']} "
        f"sources={len(inventory['source_groups'])} output={args.output}"
    )
    return 0


def build_inventory(
    file_name: str,
    sha256: str,
    rows: tuple[tuple[str, ...], ...],
) -> dict[str, object]:
    if not rows or rows[0] != HEADERS or len(rows) != 71:
        raise ValueError("unexpected worksheet contract")
    url_rows: list[dict[str, object]] = []
    for row_number, cells in enumerate(rows[1:], start=2):
        url = cells[4].strip()
        if not url:
            continue
        canonical_url = _canonical_url(url)
        hostname = urlsplit(canonical_url).hostname
        if hostname not in HOST_GROUPS:
            raise ValueError(f"unmapped hostname at row {row_number}: {hostname}")
        url_rows.append(
            {
                "row": row_number,
                "category": cells[0].strip(),
                "title": cells[1].strip(),
                "agency": cells[2].strip(),
                "method": cells[3].strip(),
                "url": url,
                "canonical_url": canonical_url,
                "hostname": hostname,
                "note": cells[5].strip(),
            }
        )
    if len(url_rows) != 64:
        raise ValueError(f"expected 64 URL rows, got {len(url_rows)}")

    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in url_rows:
        grouped[(str(row["title"]), str(row["canonical_url"]))].append(row)

    candidates: list[dict[str, object]] = []
    for (title, canonical_url), duplicates in sorted(
        grouped.items(), key=lambda item: int(item[1][0]["row"])
    ):
        first = duplicates[0]
        input_rows = [int(row["row"]) for row in duplicates]
        status, reason = _inventory_status(input_rows)
        identity = _external_identity(canonical_url)
        candidates.append(
            {
                "candidate_id": _candidate_id(input_rows[0], title, canonical_url),
                "input_rows": input_rows,
                "category": first["category"],
                "title": title,
                "agency": first["agency"],
                "url": first["url"],
                "canonical_url": canonical_url,
                "hostname": first["hostname"],
                "source_group": HOST_GROUPS[str(first["hostname"])],
                "external_identity": identity,
                "inventory_status": status,
                "decision_reason": reason,
                "untrusted_input": {
                    "collection_method_sha256": _text_hash(str(first["method"])),
                    "note_sha256": _text_hash(str(first["note"])),
                    "note_present": bool(first["note"]),
                },
            }
        )

    url_to_candidates: dict[str, list[dict[str, object]]] = defaultdict(list)
    for candidate in candidates:
        url_to_candidates[str(candidate["canonical_url"])].append(candidate)
    conflicts = [
        {
            "canonical_url": url,
            "candidate_ids": [str(item["candidate_id"]) for item in items],
            "input_rows": sorted(
                row for item in items for row in item["input_rows"]
            ),
        }
        for url, items in url_to_candidates.items()
        if len({str(item["title"]) for item in items}) > 1
    ]

    source_rows: dict[str, set[int]] = defaultdict(set)
    source_domains: dict[str, set[str]] = defaultdict(set)
    for candidate in candidates:
        group = str(candidate["source_group"])
        source_rows[group].update(candidate["input_rows"])
        source_domains[group].add(str(candidate["hostname"]))
    source_groups = [
        _source_group(group, source_rows[group], source_domains[group])
        for group in sorted(source_rows)
    ]
    statuses: dict[str, int] = defaultdict(int)
    for candidate in candidates:
        statuses[str(candidate["inventory_status"])] += 1
    return {
        "schema_version": "1.0.0",
        "inventory_id": "supplemental-official-policy-inventory-20260817",
        "inventory_date": "2026-08-17",
        "input_evidence": {
            "file_name": file_name,
            "sha256": sha256,
            "sheet_name": SHEET_NAME,
            "range": SHEET_RANGE,
            "url_row_count": len(url_rows),
            "excluded_fields": [
                "수집 방법 (가능한 모든 방법)",
                "비고 (신청 필요 서류 및 안내)",
            ],
            "exclusion_reason": (
                "공식 원문으로 검증되지 않은 수집 힌트와 필요서류는 정책 evidence로 import하지 않는다."
            ),
        },
        "quality_summary": {
            "url_row_count": len(url_rows),
            "candidate_identity_count": len(candidates),
            "collapsed_exact_duplicate_rows": len(url_rows) - len(candidates),
            "same_url_title_conflict_count": len(conflicts),
            "direct_aggregator_row_count": sum(
                1
                for row in url_rows
                if row["hostname"]
                in {"www.bokjiro.go.kr", "www.youthcenter.go.kr"}
            ),
            "inventory_status_counts": dict(sorted(statuses.items())),
        },
        "same_url_title_conflicts": sorted(
            conflicts, key=lambda item: item["input_rows"][0]
        ),
        "policy_candidates": candidates,
        "source_groups": source_groups,
    }


def _source_group(
    group_id: str,
    input_rows: set[int],
    official_domains: set[str],
) -> dict[str, object]:
    config = SOURCE_GROUPS.get(group_id)
    if config is None:
        operator, reason, resume = REJECTED_GROUPS[group_id]
        config = {
            "operator": operator,
            "status": "rejected",
            "implementation_status": "rejected",
            "source_id": None,
            "decision_reason": reason,
            "robots": ("unchecked_not_required", None),
            "terms": ("not_found", None),
            "license": ("not_found", None),
            "technical_access": "unchecked",
            "list_urls": [],
            "detail_patterns": [],
            "external_identity": None,
            "request_budget": None,
            "resume_condition": resume,
        }
    return {
        "source_group_id": group_id,
        "input_rows": sorted(input_rows),
        "input_domains": sorted(official_domains),
        "operator": config["operator"],
        "status": config["status"],
        "implementation_status": config["implementation_status"],
        "source_id": config["source_id"],
        "decision_reason": config["decision_reason"],
        "preflight": {
            "checked_at": config.get(
                "checked_at", "2026-08-17T11:29:04+09:00"
            ),
            "robots": {
                "status": config["robots"][0],
                "url": config["robots"][1],
            },
            "terms": {
                "status": config["terms"][0],
                "url": config["terms"][1],
            },
            "license": {
                "status": config["license"][0],
                "url": config["license"][1],
            },
            "technical_access": config["technical_access"],
        },
        "approved_list_urls": config["list_urls"],
        "approved_detail_url_patterns": config["detail_patterns"],
        "external_identity": config["external_identity"],
        "request_budget": config["request_budget"],
        "resume_condition": config["resume_condition"],
    }


def _inventory_status(input_rows: list[int]) -> tuple[str, str]:
    row_set = set(input_rows)
    if row_set & {13, 16, 54, 58, 59}:
        return (
            "data_error",
            "같은 URL의 다른 제목 또는 정책명과 URL의 불일치로 원문 identity를 확정할 수 없다.",
        )
    if row_set == {17}:
        return (
            "discovery_reference",
            "범용 공공데이터포털 홈은 정책 목록·상세 endpoint가 아니다.",
        )
    return "candidate", "SOP1 중복 감사와 Source preflight 대상이다."


def _candidate_id(row: int, title: str, url: str) -> str:
    digest = hashlib.sha256(f"{title}\n{url}".encode("utf-8")).hexdigest()[:12]
    return f"xlsx-row-{row:03d}-{digest}"


def _text_hash(value: str) -> str | None:
    if not value:
        return None
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError(f"only public HTTPS URLs are accepted: {value}")
    host = parsed.hostname.lower()
    netloc = host if parsed.port is None else f"{host}:{parsed.port}"
    path = parsed.path or "/"
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    return urlunsplit(("https", netloc, path, query, ""))


def _external_identity(url: str) -> dict[str, str] | None:
    parsed = urlsplit(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    for key in ("wlfareInfoId", "systId", "pbancSn", "panId", "pg", "nttId", "seq"):
        value = query.get(key)
        if value:
            return {"kind": key, "value": value}
    youth_match = re.search(r"/ythPlcyDetail/([0-9]+)", parsed.path)
    if youth_match:
        return {"kind": "plcyNo", "value": youth_match.group(1)}
    if parsed.hostname == "www.k-startup.go.kr" and query.get("id"):
        return {"kind": "id", "value": query["id"]}
    return None


def _read_sheet(payload: bytes, sheet_name: str) -> tuple[tuple[str, ...], ...]:
    # XLSX is an OPC zip. Read only the selected sheet and shared strings.
    import io

    with ZipFile(io.BytesIO(payload)) as archive:
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(
            archive.read("xl/_rels/workbook.xml.rels")
        )
        relation_targets = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in relationships.findall("r:Relationship", REL_NS)
        }
        target = None
        relation_key = (
            "{http://schemas.openxmlformats.org/"
            "officeDocument/2006/relationships}id"
        )
        for sheet in workbook.findall("x:sheets/x:sheet", XML_NS):
            if sheet.attrib.get("name") == sheet_name:
                target = relation_targets[sheet.attrib[relation_key]]
                break
        if target is None:
            raise ValueError(f"worksheet not found: {sheet_name}")
        sheet_path = posixpath.normpath(posixpath.join("xl", target))
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.findall(".//x:t", XML_NS))
                for item in root.findall("x:si", XML_NS)
            ]
        sheet_root = ElementTree.fromstring(archive.read(sheet_path))
    values_by_row: dict[int, list[str]] = {}
    for row in sheet_root.findall(".//x:sheetData/x:row", XML_NS):
        row_number = int(row.attrib["r"])
        values = [""] * 6
        for cell in row.findall("x:c", XML_NS):
            index = _column_index(cell.attrib.get("r", ""))
            if not 0 <= index < 6:
                continue
            if cell.attrib.get("t") == "inlineStr":
                values[index] = "".join(
                    node.text or "" for node in cell.findall(".//x:t", XML_NS)
                )
                continue
            node = cell.find("x:v", XML_NS)
            raw = "" if node is None else node.text or ""
            values[index] = (
                shared[int(raw)]
                if cell.attrib.get("t") == "s" and raw
                else raw
            )
        values_by_row[row_number] = values
    return tuple(tuple(values_by_row.get(number, [""] * 6)) for number in range(1, 72))


def _column_index(reference: str) -> int:
    letters = "".join(character for character in reference if character.isalpha())
    result = 0
    for character in letters:
        result = result * 26 + ord(character.upper()) - ord("A") + 1
    return result - 1


def _atomic_write(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        import os

        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
