#!/usr/bin/env python3
"""统一 IFRS/IAS 笔记结构：frontmatter 置顶，中文提炼格式一致。"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IFRS_DIR = ROOT / "03 - 知识库/IFRS"

# 重点准则：frontmatter 加 key: true，标题加 ⭐
KEY_STANDARDS = {
    "IFRS 3", "IFRS 9", "IFRS 10", "IFRS 13", "IFRS 15", "IFRS 16", "IFRS 17", "IFRS 18",
    "IAS 1", "IAS 8", "IAS 12", "IAS 19", "IAS 36", "IAS 37", "IAS 38",
}

# IFRS 1/4/6/14/17/19：旧概要 → 统一标题与 ## 📌 中文提炼
LEGACY_SUMMARY_FILES = {
    "IFRS 1 - 首次采用.md": {
        "h1": "# IFRS 1 — First-time Adoption of IFRS（首次采用）",
        "key": False,
    },
    "IFRS 4 - 保险合同（旧）.md": {
        "h1": "# IFRS 4 — Insurance Contracts（保险合同，旧）",
        "key": False,
    },
    "IFRS 6 - 矿产资源勘探与评价.md": {
        "h1": "# IFRS 6 — Exploration for and Evaluation of Mineral Resources（矿产资源勘探）",
        "key": False,
    },
    "IFRS 14 - 管制递延账户.md": {
        "h1": "# IFRS 14 — Regulatory Deferral Accounts（管制递延账户）",
        "key": False,
    },
    "IFRS 17 - 保险合同.md": {
        "h1": "# IFRS 17 — Insurance Contracts（保险合同）⭐ 重点准则",
        "key": True,
    },
    "IFRS 19 - 无公共受托责任子公司.md": {
        "h1": "# IFRS 19 — Subsidiaries without Public Accountability（披露简化）",
        "key": False,
    },
}


def parse_frontmatter(text: str) -> tuple[dict[str, str], str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    raw = text[4:end]
    body = text[end + 5 :]
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields, body


def serialize_frontmatter(fields: dict[str, str]) -> str:
    order = ["tags", "standard", "title", "effective", "source", "key"]
    lines: list[str] = []
    used = set()
    for k in order:
        if k in fields:
            lines.append(f"{k}: {fields[k]}")
            used.add(k)
    for k, v in fields.items():
        if k not in used:
            lines.append(f"{k}: {v}")
    return "---\n" + "\n".join(lines) + "\n---\n\n"


def ensure_key_field(fields: dict[str, str], is_key: bool) -> None:
    if is_key:
        fields["key"] = "true"
    elif fields.get("key") == "true" and not is_key:
        del fields["key"]


def has_star_in_h1(summary: str) -> bool:
    m = re.search(r"^# .+", summary, re.MULTILINE)
    return bool(m and "⭐" in m.group(0))


def strip_summary_prefix(summary: str) -> str:
    summary = summary.lstrip("\ufeff")
    while summary.startswith("---"):
        summary = summary[3:].lstrip("\n")
    return summary.strip()


def fix_codex_format(text: str) -> str | None:
    """Codex 格式：中文提炼在 tags frontmatter 之前。"""
    m = re.search(r"\n---\n(tags:.*?)\n---\n", text, re.DOTALL)
    if not m or "## 📌 中文提炼" not in text[: m.start()]:
        return None

    fm_raw = m.group(1)
    fields: dict[str, str] = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()

    summary = strip_summary_prefix(text[: m.start()])
    english = text[m.end() :].lstrip("\n")
    standard = fields.get("standard", "")
    is_key = has_star_in_h1(summary) or standard in KEY_STANDARDS
    ensure_key_field(fields, is_key)

    return serialize_frontmatter(fields) + summary + "\n\n---\n\n" + english


def extract_legacy_chinese(body: str) -> tuple[str, str]:
    """分离旧格式中文概要与英文全文。"""
    marker = "<!-- ifrs-foundation-full-text -->"
    if marker in body:
        idx = body.index(marker)
        chinese = body[:idx].strip()
        english = body[idx:].strip() + "\n"
        # 去掉 english 中 marker 后的内容单独处理
        rest = body[idx + len(marker) :].lstrip("\n")
        english = marker + "\n\n" + rest
        return chinese, english

    m = re.search(r"\n(IFRS \d+\n[A-Za-z])", body)
    if m:
        return body[: m.start()].strip(), body[m.start() + 1 :].lstrip("\n")
    return body.strip(), ""


def convert_legacy_summary(text: str, filename: str) -> str | None:
    meta = LEGACY_SUMMARY_FILES.get(filename)
    if not meta or "## 📌 中文提炼" in text:
        return None

    parsed = parse_frontmatter(text)
    if not parsed:
        return None
    fields, body = parsed
    chinese, english = extract_legacy_chinese(body)

    # 去掉旧 H1、## 我的注释，保留实质概要
    chinese = re.sub(r"^# IFRS \d+.*\n+", "", chinese, count=1, flags=re.MULTILINE)
    chinese = re.sub(r"^> ⚠️.*\n+", "", chinese, flags=re.MULTILINE)
    chinese = re.sub(r"^---\s*\n", "", chinese)
    chinese = re.sub(r"^## 我的注释\s*\n*", "", chinese).strip()
    chinese = re.sub(r"^## (?!我的注释)", "### ", chinese, flags=re.MULTILINE)

    is_key = meta["key"]
    ensure_key_field(fields, is_key)

    summary = meta["h1"] + "\n\n## 📌 中文提炼\n\n" + chinese
    parts = [serialize_frontmatter(fields).rstrip(), "", summary, "", "---", "", "## 我的注释", ""]
    if english.startswith("<!--"):
        parts.append(english)
    else:
        parts.append(english)
    return "\n".join(parts) + ("\n" if not english.endswith("\n") else "")


def cleanup_already_normalized(text: str) -> tuple[str, bool]:
    """修复已规范化文件中的残留问题。"""
    original = text
    text = text.lstrip("\ufeff")
    # frontmatter 后多余的 ---（含 BOM）
    text = re.sub(
        r"(---\n.*?\n---\n\n)(?:\ufeff)?---\n+",
        r"\1",
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = text.replace("\n### 我的注释\n", "\n## 我的注释\n")
    text = re.sub(
        r"(## 我的注释\n\n)---\n\n(<!-- ifrs-foundation)",
        r"\1\2",
        text,
    )
    return text, text != original


def process_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    original = text

    cleanup, changed = cleanup_already_normalized(text)
    if changed:
        text = cleanup

    if path.name in LEGACY_SUMMARY_FILES:
        new = convert_legacy_summary(text, path.name)
        if new:
            text = new
    else:
        new = fix_codex_format(text)
        if new:
            text = new

    if text != original:
        path.write_text(text, encoding="utf-8")
        if path.name in LEGACY_SUMMARY_FILES and "## 📌 中文提炼" in text:
            return "legacy"
        if "## 📌 中文提炼" in text and text.startswith("---\ntags"):
            return "codex"
        return "cleanup"
    return "skip"


def main() -> None:
    counts = {"legacy": 0, "codex": 0, "skip": 0}
    for folder in ["IFRS准则", "IAS准则"]:
        for path in sorted((IFRS_DIR / folder).glob("*.md")):
            result = process_file(path)
            counts[result] += 1
            if result != "skip":
                print(f"{result}: {path.name}")
    print(f"\n完成 legacy={counts['legacy']} codex={counts['codex']} skip={counts['skip']}")


if __name__ == "__main__":
    main()
