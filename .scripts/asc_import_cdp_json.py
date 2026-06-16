#!/usr/bin/env python3
"""从 cursor-ide-browser CDP Runtime.evaluate JSON 导入 ASC Markdown。"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asc_topics import TOPIC_MAP

ROOT = Path(__file__).resolve().parents[1]
ASC_DIR = ROOT / "03 - 知识库/US GAAP/ASC准则"


def trim_nav(text: str, num: int, name_en: str) -> str:
    """去掉侧栏导航，保留 Topic 正文。"""
    m = re.search(rf"(?<=\n){num} [^\n]{{8,120}}", text)
    if m:
        return text[m.start() + 1 :]
    m2 = re.search(rf"{num}-\d+-\d{{2}}-\d+", text)
    if m2:
        return text[m2.start() :]
    return text


def import_text(text: str, num: int) -> Path:
    if num not in TOPIC_MAP:
        raise ValueError(f"未配置 ASC {num}")

    name_en, name_cn, key = TOPIC_MAP[num]
    text = text.replace("\r\n", "\n").replace("\u00a0", " ")
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    text = trim_nav(text, num, name_en)

    if not re.search(rf"{num}-\d+-\d{{2}}-\d+", text):
        raise ValueError(f"ASC {num}: 未检测到段落号 {num}-xx-xx-x")

    today = date.today().isoformat()
    key_line = "key: true\n" if key else ""
    star = " ⭐ 重点准则" if key else ""
    fm = f"""---
tags: [us-gaap, asc-{num}]
standard: ASC {num}
source: FASB ASC
source_url: https://asc.fasb.org/{num}/showallinonepage
source_type: Codification
import_method: cursor-ide-browser
scraped_date: "{today}"
subtopics: ["{num}-10"]
{key_line}---

# ASC {num} — {name_en}（{name_cn}）{star}

---

"""
    out = ASC_DIR / f"ASC {num} - {name_en}.md"
    ASC_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(fm + text, encoding="utf-8")
    return out


def import_cdp_json(cdp_path: Path, num: int) -> Path:
    if num not in TOPIC_MAP:
        raise ValueError(f"未配置 ASC {num}")

    data = json.loads(cdp_path.read_text(encoding="utf-8"))
    text = data["result"]["value"]
    if not isinstance(text, str):
        raise ValueError("CDP JSON 中未找到字符串正文")
    # 强制落盘时可能附带 padding
    text = re.sub(r"\n{2,} +$", "", text.rstrip())
    return import_text(text, num)


def validate_md(path: Path, num: int) -> bool:
    if not path.exists() or path.stat().st_size < 3000:
        return False
    head = path.read_text(encoding="utf-8")[:8000]
    return bool(re.search(rf"{num}-\d+-\d{{2}}-\d+", head))


if __name__ == "__main__":
    cdp_path = Path(sys.argv[1])
    num = int(sys.argv[2])
    out = import_cdp_json(cdp_path, num)
    ok = validate_md(out, num)
    print(f"{'OK' if ok else 'WARN'} {out.name} ({out.stat().st_size:,} 字节)")
