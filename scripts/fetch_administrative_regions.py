"""Fetch a versioned Korean legal-dong reference snapshot from code.go.kr."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PAGE_URL = "https://www.code.go.kr/stdcode/regCodeL.do"
FULL_DOWNLOAD_URL = "https://www.code.go.kr/etc/codeFullDown.do"
SEARCH_DOWNLOAD_URL = (
    "https://www.code.go.kr/stdcode/regCodeFileDown.do"
)
LICENSE_URL = "https://www.data.go.kr/data/15077871/openapi.do"
USER_AGENT = "cheongnyeon-alimi-psf2/1.0"
SCHEMA_VERSION = "1.0.0"
CSV_FIELDS = (
    "code",
    "full_name",
    "status",
    "parent_code",
    "display_order",
    "valid_from",
    "valid_to",
    "source_updated_on",
    "lowest_name",
    "resident_code",
    "cadastre_code",
)
XLSX_HEADERS = (
    "법정동코드",
    "법정동명",
    "폐지구분",
    "상위지역코드",
    "서열",
    "생성일",
    "폐지일",
    "최종작업일",
    "최하지역명",
    "법정동코드(주민)",
    "법정동코드(지적)",
)
XML_NAMESPACE = {
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
}


class RegionFetchError(RuntimeError):
    """Raised when an official response cannot produce a safe snapshot."""


@dataclass(frozen=True, slots=True)
class OfficialRegionRow:
    code: str
    full_name: str
    status: str
    parent_code: str | None
    display_order: str | None
    valid_from: str | None
    valid_to: str | None
    source_updated_on: str | None
    lowest_name: str
    resident_code: str | None
    cadastre_code: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            field: getattr(self, field)
            for field in CSV_FIELDS
        }


def _request(
    opener: urllib.request.OpenerDirector,
    url: str,
    fields: dict[str, str] | None = None,
) -> bytes:
    data = None
    if fields is not None:
        data = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"User-Agent": USER_AGENT},
        method="POST" if data is not None else "GET",
    )
    with opener.open(request, timeout=60) as response:
        payload = response.read()
    if not payload:
        raise RegionFetchError(f"empty response from {url}")
    return payload


def _outer_zip_member(payload: bytes) -> bytes:
    if not payload.startswith(b"PK"):
        raise RegionFetchError("official download is not a ZIP archive")
    with ZipFile(io.BytesIO(payload)) as archive:
        members = tuple(
            name for name in archive.namelist() if not name.endswith("/")
        )
        if len(members) != 1:
            raise RegionFetchError(
                "official archive must contain exactly one file"
            )
        return archive.read(members[0])


def _full_listing(payload: bytes) -> tuple[tuple[str, str, str], ...]:
    text = _outer_zip_member(payload).decode("cp949")
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    expected = ("법정동코드", "법정동명", "폐지여부")
    if tuple(reader.fieldnames or ()) != expected:
        raise RegionFetchError("unexpected full listing columns")

    rows: list[tuple[str, str, str]] = []
    for source in reader:
        status = _status(source["폐지여부"])
        rows.append(
            (
                source["법정동코드"].strip(),
                source["법정동명"].strip(),
                status,
            )
        )
    if len(rows) != len({row[0] for row in rows}):
        raise RegionFetchError("official full listing has duplicate codes")
    return tuple(rows)


def _column_index(reference: str) -> int:
    letters = "".join(character for character in reference if character.isalpha())
    result = 0
    for character in letters:
        result = result * 26 + (ord(character.upper()) - ord("A") + 1)
    return result - 1


def _xlsx_rows(payload: bytes) -> tuple[tuple[str, ...], ...]:
    with ZipFile(io.BytesIO(_outer_zip_member(payload))) as workbook:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            root = ElementTree.fromstring(
                workbook.read("xl/sharedStrings.xml")
            )
            shared = [
                "".join(
                    node.text or ""
                    for node in item.findall(".//x:t", XML_NAMESPACE)
                )
                for item in root.findall("x:si", XML_NAMESPACE)
            ]
        sheet = ElementTree.fromstring(
            workbook.read("xl/worksheets/sheet1.xml")
        )

    rows: list[tuple[str, ...]] = []
    for row in sheet.findall(".//x:sheetData/x:row", XML_NAMESPACE):
        values = [""] * len(XLSX_HEADERS)
        for cell in row.findall("x:c", XML_NAMESPACE):
            index = _column_index(cell.attrib.get("r", ""))
            if index < 0 or index >= len(values):
                continue
            if cell.attrib.get("t") == "inlineStr":
                values[index] = "".join(
                    node.text or ""
                    for node in cell.findall(".//x:t", XML_NAMESPACE)
                )
                continue
            value = cell.find("x:v", XML_NAMESPACE)
            raw = "" if value is None else value.text or ""
            if cell.attrib.get("t") == "s" and raw:
                values[index] = shared[int(raw)]
            else:
                values[index] = raw
        rows.append(tuple(values))
    if not rows or rows[0] != XLSX_HEADERS:
        raise RegionFetchError("unexpected detailed listing columns")
    return tuple(rows[1:])


def _status(value: str) -> str:
    if value in {"존재", "현존"}:
        return "active"
    if value == "폐지":
        return "retired"
    raise RegionFetchError(f"unexpected region status: {value!r}")


def _optional(value: str) -> str | None:
    selected = value.strip()
    return selected or None


def _optional_date(value: str) -> str | None:
    selected = _optional(value)
    if selected is None:
        return None
    try:
        return datetime.strptime(selected, "%Y%m%d").date().isoformat()
    except ValueError as exc:
        raise RegionFetchError(
            f"invalid official date value: {selected!r}"
        ) from exc


def _region_row(values: tuple[str, ...]) -> OfficialRegionRow:
    source = dict(zip(XLSX_HEADERS, values, strict=True))
    code = source["법정동코드"].strip()
    full_name = source["법정동명"].strip()
    lowest_name = source["최하지역명"].strip()
    if not re.fullmatch(r"\d{10}", code):
        raise RegionFetchError(f"invalid official region code: {code!r}")
    if not full_name or not lowest_name:
        raise RegionFetchError(f"missing official region name for {code}")
    return OfficialRegionRow(
        code=code,
        full_name=full_name,
        status=_status(source["폐지구분"]),
        parent_code=_optional(source["상위지역코드"]),
        display_order=_optional(source["서열"]),
        valid_from=_optional_date(source["생성일"]),
        valid_to=_optional_date(source["폐지일"]),
        source_updated_on=_optional_date(source["최종작업일"]),
        lowest_name=lowest_name,
        resident_code=_optional(source["법정동코드(주민)"]),
        cadastre_code=_optional(source["법정동코드(지적)"]),
    )


def _base_fields(challenge: str, prefix: str) -> dict[str, str]:
    return {
        "cPage": "1",
        "pageSize": "10",
        "regionCd": "",
        "locataddNm": "",
        "sidoCd": prefix,
        "sggCd": "*",
        "umdCd": "*",
        "riCd": "*",
        "disuseAt": "ALL",
        "stdate": "",
        "enddate": "",
        "searchOk": "0",
        "codeseId": "00002",
        "challenge": challenge,
        "chkHigh": "0",
        "chkOrder": "0",
        "chkCrtDt": "0",
        "chkClsDt": "0",
        "chkLocatDt": "0",
        "chkLow": "0",
        "chkJumin": "0",
        "chkJijuk": "0",
        "chkWantCnt": "8",
    }


def fetch_rows() -> tuple[OfficialRegionRow, ...]:
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(CookieJar())
    )
    page = _request(opener, SOURCE_PAGE_URL).decode("utf-8")
    challenge_match = re.search(
        r'name="challenge"[^>]*value="([^"]+)"',
        page,
    )
    if challenge_match is None:
        raise RegionFetchError("download challenge was not found")
    challenge = challenge_match.group(1)

    full_payload = _request(
        opener,
        FULL_DOWNLOAD_URL,
        {"codeseId": "법정동코드", "challenge": challenge},
    )
    full_rows = _full_listing(full_payload)
    prefixes = sorted({code[:2] for code, _, _ in full_rows})

    detailed: list[OfficialRegionRow] = []
    for prefix in prefixes:
        fields = _base_fields(challenge, prefix)
        search_page = _request(
            opener,
            SOURCE_PAGE_URL,
            fields,
        ).decode("utf-8")
        count_match = re.search(r"var cnt\s*=\s*([0-9]+)", search_page)
        if count_match is None:
            raise RegionFetchError(f"count missing for prefix {prefix}")
        count = int(count_match.group(1))
        if count < 1 or count > 20_000:
            raise RegionFetchError(
                f"unsupported result count for prefix {prefix}: {count}"
            )
        payload = _request(
            opener,
            f"{SEARCH_DOWNLOAD_URL}?cPage=1&pageSize={count}",
            fields,
        )
        rows = tuple(_region_row(row) for row in _xlsx_rows(payload))
        if len(rows) != count:
            raise RegionFetchError(
                f"download count mismatch for prefix {prefix}"
            )
        if any(not row.code.startswith(prefix) for row in rows):
            raise RegionFetchError(
                f"download prefix mismatch for {prefix}"
            )
        detailed.extend(rows)

    if len(detailed) != len({row.code for row in detailed}):
        raise RegionFetchError("detailed downloads have duplicate codes")
    full_contract = set(full_rows)
    detailed_contract = {
        (row.code, row.full_name, row.status)
        for row in detailed
    }
    if full_contract != detailed_contract:
        missing = sorted(full_contract - detailed_contract)
        unexpected = sorted(detailed_contract - full_contract)
        raise RegionFetchError(
            "full and detailed official downloads do not describe the same "
            f"rows: missing={len(missing)} {missing[:3]!r}, "
            f"unexpected={len(unexpected)} {unexpected[:3]!r}"
        )
    return tuple(sorted(detailed, key=lambda row: row.code))


def _csv_bytes(rows: Iterable[OfficialRegionRow]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=CSV_FIELDS,
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row.to_dict())
    return output.getvalue().encode("utf-8")


def _gzip_bytes(payload: bytes) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as archive:
        archive.write(payload)
    return output.getvalue()


def write_snapshot(snapshot_date: date, rows: tuple[OfficialRegionRow, ...]) -> None:
    version = snapshot_date.strftime("%Y%m%d")
    target_root = ROOT / "data" / "reference" / "administrative_regions"
    csv_path = target_root / f"legal_dong_codes_{version}.csv.gz"
    manifest_path = target_root / f"legal_dong_codes_{version}.manifest.json"
    csv_payload = _csv_bytes(rows)
    active = sum(row.status == "active" for row in rows)
    retired = sum(row.status == "retired" for row in rows)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "scheme": f"kr-bjd-{version}",
        "snapshot_date": snapshot_date.isoformat(),
        "source_page_url": SOURCE_PAGE_URL,
        "source_api_url": (
            "https://apis.data.go.kr/1741000/StanReginCd/"
            "getStanReginCdList"
        ),
        "license_name": "이용허락범위 제한 없음",
        "license_url": LICENSE_URL,
        "record_count": len(rows),
        "active_count": active,
        "retired_count": retired,
        "normalized_csv_sha256": hashlib.sha256(csv_payload).hexdigest(),
    }
    target_root.mkdir(parents=True, exist_ok=True)
    csv_path.write_bytes(_gzip_bytes(csv_payload))
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {len(rows)} official region rows to {csv_path}")
    print(f"Wrote snapshot manifest to {manifest_path}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a locked legal-dong reference snapshot",
    )
    parser.add_argument(
        "--snapshot-date",
        required=True,
        type=date.fromisoformat,
        help="Explicit snapshot date in YYYY-MM-DD format",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        write_snapshot(args.snapshot_date, fetch_rows())
    except (OSError, RegionFetchError) as exc:
        print(f"Administrative region fetch failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
