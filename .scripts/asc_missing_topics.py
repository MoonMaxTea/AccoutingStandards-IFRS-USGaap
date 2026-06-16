#!/usr/bin/env python3
"""列出尚未导出的 ASC Topic 编号。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asc_topics import ASC_TOPICS

ROOT = Path(__file__).resolve().parents[1]
ASC_DIR = ROOT / "03 - 知识库/US GAAP/ASC准则"


def is_done(num: int, name_en: str) -> bool:
    p = ASC_DIR / f"ASC {num} - {name_en}.md"
    if not p.exists() or p.stat().st_size < 3000:
        return False
    head = p.read_text(encoding="utf-8")[:8000]
    return bool(re.search(rf"{num}-\d+-\d{{2}}-\d+", head))


if __name__ == "__main__":
    missing = [n for n, en, _, _ in ASC_TOPICS if not is_done(n, en)]
    print("done:", len(ASC_TOPICS) - len(missing), "missing:", len(missing))
    print(",".join(str(n) for n in missing))
