#!/usr/bin/env python3
"""从 IFRS Foundation 官方 PDF 提取全文并追加到已有概要笔记。"""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / ".tmp" / "pdfs"

STANDARDS = [
    {
        "num": 1,
        "md": ROOT / "03 - 知识库/IFRS/IFRS准则/IFRS 1 - 首次采用.md",
        "pdf": "https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2024/issued/part-a/ifrs-1-first-time-adoption-of-international-financial-reporting-standards.pdf?bypass=on",
    },
    {
        "num": 4,
        "md": ROOT / "03 - 知识库/IFRS/IFRS准则/IFRS 4 - 保险合同（旧）.md",
        "pdf": "https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2017/issued/part-a/ifrs-4-insurance-contracts.pdf?bypass=on",
    },
    {
        "num": 6,
        "md": ROOT / "03 - 知识库/IFRS/IFRS准则/IFRS 6 - 矿产资源勘探与评价.md",
        "pdf": "https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2024/issued/part-a/ifrs-6-exploration-for-and-evaluation-of-mineral-resources.pdf?bypass=on",
    },
    {
        "num": 14,
        "md": ROOT / "03 - 知识库/IFRS/IFRS准则/IFRS 14 - 管制递延账户.md",
        "pdf": "https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2024/issued/part-a/ifrs-14-regulatory-deferral-accounts.pdf?bypass=on",
    },
    {
        "num": 17,
        "md": ROOT / "03 - 知识库/IFRS/IFRS准则/IFRS 17 - 保险合同.md",
        "pdf": "https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2024/issued/part-a/ifrs-17-insurance-contracts.pdf?bypass=on",
    },
    {
        "num": 19,
        "md": ROOT / "03 - 知识库/IFRS/IFRS准则/IFRS 19 - 无公共受托责任子公司.md",
        "pdf": "https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2025/issued/part-a/ifrs-19-subsidiaries-without-public-accountability-disclosures.pdf?bypass=on",
    },
]

MARKER = "<!-- ifrs-foundation-full-text -->"


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2011", "-")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
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


def parse_frontmatter(content: str) -> tuple[str | None, str]:
    if not content.startswith("---\n"):
        return None, content
    end = content.find("\n---\n", 4)
    if end == -1:
        return None, content
    fm = content[4:end]
    body = content[end + 5 :]
    return fm, body


def ensure_source_in_frontmatter(fm: str) -> str:
    if re.search(r"^source:\s*IFRS Foundation\s*$", fm, re.MULTILINE):
        return fm
    return fm.rstrip() + "\nsource: IFRS Foundation\n"


def already_has_full_text(body: str) -> bool:
    if MARKER in body:
        return True
    if "© IFRS Foundation" in body and "CONTENTS" in body and len(body) > 8000:
        return True
    return False


def split_summary_body(body: str) -> str:
    """保留概要部分；若已有全文标记则截断到标记之前。"""
    if MARKER in body:
        body = body.split(MARKER, 1)[0]
    # 若误追加过全文（无标记），尝试在第一个 IFRS N 官方正文块前截断
    m = re.search(r"\nIFRS \d+\n[A-Za-z]", body)
    if m and "© IFRS Foundation" in body[m.start() :]:
        # 保留 ## 我的注释 之前的概要
        note_idx = body.find("## 我的注释")
        if note_idx != -1 and m.start() > note_idx + 20:
            body = body[: note_idx + len("## 我的注释")] + "\n\n"
    return body.rstrip() + "\n\n"


def merge_markdown(md_path: Path, pdf_text: str) -> bool:
    original = md_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(original)
    if fm is None:
        print(f"  跳过（无 frontmatter）: {md_path.name}")
        return False

    if already_has_full_text(body):
        print(f"  已有全文，跳过: {md_path.name}")
        return False

    summary = split_summary_body(body)
    fm = ensure_source_in_frontmatter(fm)
    merged = f"---\n{fm}---\n\n{summary}{MARKER}\n\n{pdf_text}"
    md_path.write_text(merged, encoding="utf-8")
    print(f"  已写入: {md_path.name} ({len(merged):,} 字符)")
    return True


def process(only: list[int] | None = None) -> int:
    TMP.mkdir(parents=True, exist_ok=True)
    updated = 0
    for item in STANDARDS:
        num = item["num"]
        if only and num not in only:
            continue
        md_path: Path = item["md"]
        print(f"IFRS {num}: {md_path.name}")
        if not md_path.exists():
            print("  文件不存在，跳过")
            continue
        pdf_path = TMP / f"ifrs{num}.pdf"
        download_pdf(item["pdf"], pdf_path)
        pdf_text = extract_pdf_text(pdf_path)
        if merge_markdown(md_path, pdf_text):
            updated += 1
    return updated


if __name__ == "__main__":
    nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else None
    count = process(nums)
    print(f"\n完成：更新 {count} 个文件")
