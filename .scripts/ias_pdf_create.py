#!/usr/bin/env python3
"""从 IFRS Foundation 官方 PDF 提取全文并新建 IAS 准则笔记。"""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / ".tmp" / "pdfs"
IAS_DIR = ROOT / "03 - 知识库/IFRS/IAS准则"

BASE = "https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2024/issued/part-a"

STANDARDS = [
    {
        "num": 1,
        "file": "IAS 1 - Presentation Of Financial Statements.md",
        "slug": "ias-1-presentation-of-financial-statements",
    },
    {
        "num": 8,
        "file": "IAS 8 - Accounting Policies Changes In Estimates And Errors.md",
        "slug": "ias-8-accounting-policies-changes-in-accounting-estimates-and-errors",
    },
    {
        "num": 10,
        "file": "IAS 10 - Events After The Reporting Period.md",
        "slug": "ias-10-events-after-the-reporting-period",
    },
    {
        "num": 36,
        "file": "IAS 36 - Impairment Of Assets.md",
        "slug": "ias-36-impairment-of-assets",
    },
    {
        "num": 37,
        "file": "IAS 37 - Provisions Contingent Liabilities And Contingent Assets.md",
        "slug": "ias-37-provisions-contingent-liabilities-and-contingent-assets",
    },
    {
        "num": 38,
        "file": "IAS 38 - Intangible Assets.md",
        "slug": "ias-38-intangible-assets",
    },
    {
        "num": 20,
        "file": "IAS 20 - Accounting For Government Grants And Disclosure Of Government Assistance.md",
        "slug": "ias-20-accounting-for-government-grants-and-disclosure-of-government-assistance",
    },
    {
        "num": 23,
        "file": "IAS 23 - Borrowing Costs.md",
        "slug": "ias-23-borrowing-costs",
    },
    {
        "num": 24,
        "file": "IAS 24 - Related Party Disclosures.md",
        "slug": "ias-24-related-party-disclosures",
    },
    {
        "num": 27,
        "file": "IAS 27 - Separate Financial Statements.md",
        "slug": "ias-27-separate-financial-statements",
    },
    {
        "num": 32,
        "file": "IAS 32 - Financial Instruments Presentation.md",
        "slug": "ias-32-financial-instruments-presentation",
    },
    {
        "num": 33,
        "file": "IAS 33 - Earnings Per Share.md",
        "slug": "ias-33-earnings-per-share",
    },
    {
        "num": 34,
        "file": "IAS 34 - Interim Financial Reporting.md",
        "slug": "ias-34-interim-financial-reporting",
    },
    {
        "num": 39,
        "file": "IAS 39 - Financial Instruments Recognition And Measurement.md",
        "slug": "ias-39-financial-instruments-recognition-and-measurement",
    },
    {
        "num": 40,
        "file": "IAS 40 - Investment Property.md",
        "slug": "ias-40-investment-property",
    },
    {
        "num": 41,
        "file": "IAS 41 - Agriculture.md",
        "slug": "ias-41-agriculture",
    },
]


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2011", "-")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub(r"[\x00-\x1f] IFRS Foundation", "© IFRS Foundation", text)
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip() + "\n"


def download_pdf(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        return
    print(f"  下载 PDF: {url}")
    urllib.request.urlretrieve(url, dest)


def extract_pdf_text(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return normalize_text("".join(parts))


def build_markdown(num: int, pdf_text: str) -> str:
    tag = f"ias-{num}"
    fm = f"""---
tags: [ias, {tag}]
standard: IAS {num}
source: IFRS Foundation
---
"""
    return fm + "\n" + pdf_text


def is_complete(md_path: Path) -> bool:
    if not md_path.exists():
        return False
    text = md_path.read_text(encoding="utf-8")
    return (
        "source: IFRS Foundation" in text
        and "© IFRS Foundation" in text
        and "CONTENTS" in text
        and len(text) > 5000
    )


def process(only: list[int] | None = None) -> int:
    TMP.mkdir(parents=True, exist_ok=True)
    IAS_DIR.mkdir(parents=True, exist_ok=True)
    created = 0

    for item in STANDARDS:
        num = item["num"]
        if only and num not in only:
            continue

        md_path = IAS_DIR / item["file"]
        print(f"IAS {num}: {item['file']}")

        if is_complete(md_path):
            print("  已有完整全文，跳过")
            continue

        pdf_url = f"{BASE}/{item['slug']}.pdf?bypass=on"
        pdf_path = TMP / f"ias{num}.pdf"
        download_pdf(pdf_url, pdf_path)
        pdf_text = extract_pdf_text(pdf_path)
        md_path.write_text(build_markdown(num, pdf_text), encoding="utf-8")
        print(f"  已创建: {md_path.name} ({md_path.stat().st_size:,} 字节)")
        created += 1

    return created


if __name__ == "__main__":
    nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else None
    count = process(nums)
    print(f"\n完成：新建/更新 {count} 个文件")
