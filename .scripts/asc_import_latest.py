#!/usr/bin/env python3
"""内置 Browser 导出后：从最新 CDP JSON 导入指定 Topic（Agent 辅助）。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asc_batch_export_runner import import_one

CDP_LOG = Path.home() / ".cursor/browser-logs"


def latest_cdp() -> Path:
    files = sorted(CDP_LOG.glob("cdp-response-Runtime.evaluate-*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError("无 CDP JSON")
    return files[-1]


if __name__ == "__main__":
    num = int(sys.argv[1])
    cdp = Path(sys.argv[2]) if len(sys.argv) > 2 else latest_cdp()
    import_one(cdp, num)
