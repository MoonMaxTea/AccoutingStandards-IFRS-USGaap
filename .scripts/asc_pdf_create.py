#!/usr/bin/env python3
"""从 FASB 官方 PDF（ASU / Legacy SFAS）提取全文并新建 ASC 准则笔记。"""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / ".tmp" / "pdfs" / "asc"
ASC_DIR = ROOT / "03 - 知识库/US GAAP/ASC准则"
BASE = "https://storage.fasb.org"

# 每个 Topic 对应一份或多份 FASB 官方 PDF
STANDARDS: list[dict] = [
    # —— Presentation ——
    {
        "num": 205,
        "name_en": "Presentation of Financial Statements",
        "name_cn": "财务报表列报",
        "pdfs": ["ASU%202014-08.pdf"],
        "asu": "2014-08",
    },
    {
        "num": 230,
        "name_en": "Statement of Cash Flows",
        "name_cn": "现金流量表",
        "pdfs": ["fas95.pdf"],
        "asu": "SFAS 95",
        "legacy": True,
    },
    {
        "num": 250,
        "name_en": "Accounting Changes and Error Corrections",
        "name_cn": "会计变更与差错更正",
        "pdfs": ["fas154.pdf"],
        "asu": "SFAS 154",
        "legacy": True,
    },
    {
        "num": 260,
        "name_en": "Earnings Per Share",
        "name_cn": "每股收益",
        "pdfs": ["fas128.pdf"],
        "asu": "SFAS 128",
        "legacy": True,
    },
    {
        "num": 270,
        "name_en": "Interim Reporting",
        "name_cn": "中期财务报告",
        "pdfs": ["fas21.pdf"],
        "asu": "SFAS 21",
        "legacy": True,
    },
    {
        "num": 280,
        "name_en": "Segment Reporting",
        "name_cn": "分部报告",
        "pdfs": ["ASU%202023-07.pdf"],
        "asu": "2023-07",
    },
    # —— Assets ——
    {
        "num": 320,
        "name_en": "Investments—Debt and Equity Securities",
        "name_cn": "债务与权益证券投资",
        "pdfs": ["fas115.pdf"],
        "asu": "SFAS 115",
        "legacy": True,
    },
    {
        "num": 321,
        "name_en": "Investments—Equity Securities",
        "name_cn": "权益证券投资",
        "pdfs": ["ASU%202020-01.pdf"],
        "asu": "2020-01",
    },
    {
        "num": 323,
        "name_en": "Investments—Equity Method and Joint Ventures",
        "name_cn": "权益法与合营投资",
        "pdfs": ["ASU%202015-17.pdf"],
        "asu": "2015-17",
    },
    {
        "num": 326,
        "name_en": "Financial Instruments—Credit Losses",
        "name_cn": "金融工具——信用损失",
        "pdfs": ["ASU%202016-13.pdf"],
        "asu": "2016-13",
        "key": True,
    },
    {
        "num": 330,
        "name_en": "Inventory",
        "name_cn": "存货",
        "pdfs": ["ASU%202015-11.pdf"],
        "asu": "2015-11",
    },
    {
        "num": 350,
        "name_en": "Intangibles—Goodwill and Other",
        "name_cn": "无形资产——商誉及其他",
        "pdfs": ["fas142.pdf"],
        "asu": "SFAS 142",
        "legacy": True,
        "key": True,
    },
    {
        "num": 360,
        "name_en": "Property Plant and Equipment",
        "name_cn": "不动产、厂房和设备",
        "pdfs": ["fas144.pdf"],
        "asu": "SFAS 144",
        "legacy": True,
        "key": True,
    },
    # —— Liabilities ——
    {
        "num": 410,
        "name_en": "Asset Retirement and Environmental Obligations",
        "name_cn": "资产退役与环境义务",
        "pdfs": ["fas47.pdf"],
        "asu": "SFAS 47",
        "legacy": True,
    },
    {
        "num": 450,
        "name_en": "Contingencies",
        "name_cn": "或有事项",
        "pdfs": ["fas5.pdf"],
        "asu": "SFAS 5",
        "legacy": True,
        "key": True,
    },
    {
        "num": 480,
        "name_en": "Distinguishing Liabilities From Equity",
        "name_cn": "负债与权益的区分",
        "pdfs": ["fas150.pdf"],
        "asu": "SFAS 150",
        "legacy": True,
    },
    # —— Revenue & Expenses ——
    {
        "num": 606,
        "name_en": "Revenue From Contracts With Customers",
        "name_cn": "客户合同收入",
        "pdfs": ["ASU%202014-09_Section%20A.pdf"],
        "asu": "2014-09",
        "key": True,
    },
    {
        "num": 715,
        "name_en": "Compensation—Retirement Benefits",
        "name_cn": "雇员退休福利",
        "pdfs": ["fas87.pdf", "fas106.pdf"],
        "asu": "SFAS 87 / SFAS 106",
        "legacy": True,
        "key": True,
    },
    {
        "num": 718,
        "name_en": "Compensation—Stock Compensation",
        "name_cn": "股份支付",
        "pdfs": ["fas123r.pdf"],
        "asu": "SFAS 123(R)",
        "legacy": True,
        "key": True,
    },
    {
        "num": 740,
        "name_en": "Income Taxes",
        "name_cn": "所得税",
        "pdfs": ["fas109.pdf"],
        "asu": "SFAS 109",
        "legacy": True,
        "key": True,
    },
    # —— Broad Transactions ——
    {
        "num": 805,
        "name_en": "Business Combinations",
        "name_cn": "企业合并",
        "pdfs": ["fas141r.pdf"],
        "asu": "SFAS 141(R)",
        "legacy": True,
        "key": True,
    },
    {
        "num": 810,
        "name_en": "Consolidation",
        "name_cn": "合并报表",
        "pdfs": ["fas160.pdf", "fas167.pdf"],
        "asu": "SFAS 160 / SFAS 167",
        "legacy": True,
        "key": True,
    },
    {
        "num": 815,
        "name_en": "Derivatives and Hedging",
        "name_cn": "衍生工具与套期",
        "pdfs": ["fas133.pdf"],
        "asu": "SFAS 133",
        "legacy": True,
        "key": True,
    },
    {
        "num": 820,
        "name_en": "Fair Value Measurement",
        "name_cn": "公允价值计量",
        "pdfs": ["fas157.pdf"],
        "asu": "SFAS 157",
        "legacy": True,
        "key": True,
    },
    {
        "num": 825,
        "name_en": "Financial Instruments",
        "name_cn": "金融工具",
        "pdfs": ["ASU%202016-01.pdf"],
        "asu": "2016-01",
        "key": True,
    },
    {
        "num": 830,
        "name_en": "Foreign Currency Matters",
        "name_cn": "外币事项",
        "pdfs": ["fas52.pdf"],
        "asu": "SFAS 52",
        "legacy": True,
    },
    {
        "num": 835,
        "name_en": "Interest",
        "name_cn": "利息",
        "pdfs": ["fas34.pdf"],
        "asu": "SFAS 34",
        "legacy": True,
    },
    {
        "num": 842,
        "name_en": "Leases",
        "name_cn": "租赁",
        "pdfs": ["ASU%202016-02_Section%20A.pdf"],
        "asu": "2016-02",
        "key": True,
    },
    {
        "num": 848,
        "name_en": "Reference Rate Reform",
        "name_cn": "参考利率改革",
        "pdfs": ["ASU%202020-04.pdf"],
        "asu": "2020-04",
    },
    {
        "num": 850,
        "name_en": "Related Party Disclosures",
        "name_cn": "关联方披露",
        "pdfs": ["fas57.pdf"],
        "asu": "SFAS 57",
        "legacy": True,
    },
    {
        "num": 855,
        "name_en": "Subsequent Events",
        "name_cn": "期后事项",
        "pdfs": ["fas165.pdf"],
        "asu": "SFAS 165",
        "legacy": True,
    },
    {
        "num": 860,
        "name_en": "Transfers and Servicing",
        "name_cn": "转移与服务",
        "pdfs": ["fas166.pdf"],
        "asu": "SFAS 166",
        "legacy": True,
    },
    {
        "num": 944,
        "name_en": "Financial Services—Insurance",
        "name_cn": "保险",
        "pdfs": ["ASU%202018-12.pdf"],
        "asu": "2018-12",
        "key": True,
    },
]


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2011", "-")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub(r"[\x00-\x1f] FASB", "© FASB", text)
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


def slug_filename(item: dict) -> str:
    return f"ASC {item['num']} - {item['name_en']}.md"


def build_markdown(item: dict, pdf_text: str) -> str:
    num = item["num"]
    tag = f"asc-{num}"
    key_line = "key: true\n" if item.get("key") else ""
    legacy = item.get("legacy", False)
    source_type = "FASB Legacy SFAS" if legacy else "FASB ASU"
    fm = f"""---
tags: [us-gaap, {tag}]
standard: ASC {num}
source: FASB
source_type: {source_type}
source_asu: {item["asu"]}
---
"""
    title = f"# ASC {num} — {item['name_en']}（{item['name_cn']}）"
    if item.get("key"):
        title += " ⭐ 重点准则"
    header = f"{fm}\n{title}\n\n---\n\n"
    return header + pdf_text


def is_complete(md_path: Path) -> bool:
    if not md_path.exists():
        return False
    text = md_path.read_text(encoding="utf-8")
    return (
        "source: FASB" in text
        and len(text) > 8000
        and ("Topic " in text or "STATEMENT" in text or "Statement" in text)
    )


def process(only: list[int] | None = None) -> int:
    TMP.mkdir(parents=True, exist_ok=True)
    ASC_DIR.mkdir(parents=True, exist_ok=True)
    created = 0

    for item in STANDARDS:
        num = item["num"]
        if only and num not in only:
            continue

        md_path = ASC_DIR / slug_filename(item)
        print(f"ASC {num}: {item['name_en']}")

        if is_complete(md_path):
            print("  已有完整全文，跳过")
            continue

        texts: list[str] = []
        for i, pdf_name in enumerate(item["pdfs"]):
            pdf_url = f"{BASE}/{pdf_name}"
            pdf_path = TMP / f"asc{num}_{i}.pdf"
            try:
                download_pdf(pdf_url, pdf_path)
                texts.append(extract_pdf_text(pdf_path))
            except Exception as exc:
                print(f"  下载失败 {pdf_name}: {exc}")
                continue

        if not texts:
            print("  无可用 PDF，跳过")
            continue

        combined = "\n\n<!-- fasb-pdf-separator -->\n\n".join(texts)
        md_path.write_text(build_markdown(item, combined), encoding="utf-8")
        print(f"  已创建: {md_path.name} ({md_path.stat().st_size:,} 字节)")
        created += 1

    return created


if __name__ == "__main__":
    nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else None
    count = process(nums)
    print(f"\n完成：新建/更新 {count} 个文件")
