#!/usr/bin/env python3
"""将用户在 asc.fasb.org 通过 Print 保存的 PDF 转为 ASC Markdown 笔记。

适用场景：系统浏览器（Chrome/Edge）可正常打开 ASC 合并页并 Print，
但 Cursor 内置浏览器 Print 无效，或自动化脚本被 Cloudflare 拦截。

步骤（用户）：
  1. 在 Chrome/Edge 打开 asc.fasb.org → 606-10 → Join All Sections
  2. 点击 Print → 目标选「另存为 PDF」
  3. 保存到: .tmp/pdfs/asc/606-10.pdf
  4. 运行: python asc_print_pdf_import.py 606

也可一次导入多个 Subtopic PDF，脚本会自动合并：
  .tmp/pdfs/asc/606-10.pdf
  .tmp/pdfs/asc/606-20.pdf  (如有)
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / ".tmp" / "pdfs" / "asc"
ASC_DIR = ROOT / "03 - 知识库/US GAAP/ASC准则"

TOPICS: dict[int, dict] = {
    606: {
        "name_en": "Revenue From Contracts With Customers",
        "name_cn": "客户合同收入",
        "subtopics": ["606-10"],
        "key": True,
    },
    842: {
        "name_en": "Leases",
        "name_cn": "租赁",
        "subtopics": ["842-10", "842-20", "842-30"],
        "key": True,
    },
    805: {
        "name_en": "Business Combinations",
        "name_cn": "企业合并",
        "subtopics": ["805-10"],
        "key": True,
    },
    820: {
        "name_en": "Fair Value Measurement",
        "name_cn": "公允价值计量",
        "subtopics": ["820-10"],
        "key": True,
    },
}


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip() + "\n"


def extract_pdf(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    parts = [page.get_text() for page in doc]
    doc.close()
    return normalize_text("".join(parts))


def find_pdfs(num: int, subtopics: list[str]) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    for sub in subtopics:
        candidates = [
            PDF_DIR / f"{sub}.pdf",
            PDF_DIR / f"ASC {sub}.pdf",
            PDF_DIR / f"{num}-{sub.split('-', 1)[-1]}.pdf",
        ]
        for path in candidates:
            if path.exists() and path.stat().st_size > 5000:
                found.append((sub, path))
                break
        else:
            print(f"  缺少 PDF: {sub} → 请保存到 {PDF_DIR / (sub + '.pdf')}")
    return found


def build_markdown(meta: dict, num: int, parts: list[tuple[str, str]]) -> str:
    today = date.today().isoformat()
    subtopics_yaml = ", ".join(f'"{s}"' for s in meta["subtopics"])
    key_line = "key: true\n" if meta.get("key") else ""
    fm = f"""---
tags: [us-gaap, asc-{num}]
standard: ASC {num}
source: FASB ASC
source_url: https://asc.fasb.org/
source_type: Codification
import_method: Print-to-PDF
scraped_date: "{today}"
subtopics: [{subtopics_yaml}]
{key_line}---
"""
    title = f"# ASC {num} — {meta['name_en']}（{meta['name_cn']}）"
    if meta.get("key"):
        title += " ⭐ 重点准则"
    body = f"{fm}\n{title}\n"
    for sub, text in parts:
        body += f"\n---\n\n## Subtopic {sub}\n\n{text}\n"
    return body


def is_codification_text(text: str, subtopic: str) -> bool:
    prefix = subtopic.replace("-", r"\-")
    return bool(re.search(rf"{prefix}-\d+-\d+", text)) and len(text) > 3000


def process(num: int) -> bool:
    if num not in TOPICS:
        print(f"ASC {num}: 未配置")
        return False

    meta = TOPICS[num]
    pdfs = find_pdfs(num, meta["subtopics"])
    if not pdfs:
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\n请将 Print PDF 放入: {PDF_DIR}")
        return False

    parts: list[tuple[str, str]] = []
    for sub, path in pdfs:
        text = extract_pdf(path)
        if not is_codification_text(text, sub):
            print(f"  警告: {path.name} 可能不是 Codification 正文（未检测到 {sub}-xx-x 段落号）")
        parts.append((sub, text))
        print(f"  {path.name}: {len(text):,} 字符")

    ASC_DIR.mkdir(parents=True, exist_ok=True)
    out = ASC_DIR / f"ASC {num} - {meta['name_en']}.md"
    out.write_text(build_markdown(meta, num, parts), encoding="utf-8")
    print(f"  已写入: {out.name} ({out.stat().st_size:,} 字节)")
    return True


if __name__ == "__main__":
    nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [606]
    ok = sum(process(n) for n in nums)
    print(f"\n完成: {ok}/{len(nums)}")
