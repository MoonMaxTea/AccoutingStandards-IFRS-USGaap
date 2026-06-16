#!/usr/bin/env python3
"""校验已导出的 ASC Markdown 文件。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from asc_topics import ASC_TOPICS, TOPIC_MAP

ROOT = Path(__file__).resolve().parents[1]
ASC_DIR = ROOT / "03 - 知识库/US GAAP/ASC准则"


def main() -> int:
    ok, missing, bad = [], [], []
    for num, name_en, _cn, _key in ASC_TOPICS:
        path = ASC_DIR / f"ASC {num} - {name_en}.md"
        if not path.exists():
            missing.append(num)
            continue
        head = path.read_text(encoding="utf-8")[:8000]
        if path.stat().st_size < 3000 or not re.search(rf"{num}-\d+-\d{{2}}-\d+", head):
            bad.append(num)
        else:
            ok.append(num)
    print(f"OK: {len(ok)}  缺失: {len(missing)}  异常: {len(bad)}")
    if missing:
        print("缺失:", ", ".join(str(n) for n in missing))
    if bad:
        print("异常:", ", ".join(str(n) for n in bad))
    return 0 if not missing and not bad else 1


if __name__ == "__main__":
    sys.exit(main())
