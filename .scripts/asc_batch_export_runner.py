#!/usr/bin/env python3
"""批量导入 CDP JSON 并校验段落号。供 Agent 在每次 browser_cdp 后调用。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asc_import_cdp_json import import_cdp_json, validate_md
from asc_topics import ASC_TOPICS

LOG = Path(__file__).resolve().parents[1] / ".logs/cursor/asc-export.log"


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


def import_one(cdp_path: Path, num: int) -> str:
    try:
        out = import_cdp_json(cdp_path, num)
        ok = validate_md(out, num)
        m = re.search(rf"({num}-\d+-\d{{2}}-\d+)", out.read_text(encoding="utf-8")[:12000])
        para = m.group(1) if m else "?"
        status = "OK" if ok else "WARN"
        log(f"{status} ASC {num} -> {out.name} para={para} size={out.stat().st_size}")
        return status
    except Exception as e:
        log(f"FAIL ASC {num}: {e}")
        return "FAIL"


if __name__ == "__main__":
    if len(sys.argv) == 3:
        import_one(Path(sys.argv[1]), int(sys.argv[2]))
    elif len(sys.argv) == 2 and sys.argv[1] == "--list":
        for n, en, cn, k in ASC_TOPICS:
            print(n)
