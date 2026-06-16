#!/usr/bin/env python3
"""内置 Browser 批量导出编排：读取缺失列表，输出待处理 Topic（供 Agent MCP 循环）。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asc_missing_topics import is_done
from asc_topics import ASC_TOPICS

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".tmp/asc-export-state.json"
CDP_LOG = Path.home() / ".cursor/browser-logs"
IMPORT = ROOT / ".scripts/asc_batch_export_runner.py"

# CDP 表达式：等待加载 + 提取正文并 padding 以强制写入 log 文件
EXTRACT_JS = """
(async (n) => {
  const re = new RegExp(`${n}-\\\\d{2}-\\\\d{2}-\\\\d+`);
  for (let i = 0; i < 40; i++) {
    const t = document.body.innerText || '';
    if (t.length > 3000 && re.test(t)) {
      return t + '\\n' + ' '.repeat(30000);
    }
    await new Promise(r => setTimeout(r, 1500));
  }
  throw new Error('timeout: ' + (document.body.innerText || '').length);
})(NUM)
"""


def missing_nums() -> list[int]:
    return [n for n, en, _, _ in ASC_TOPICS if not is_done(n, en)]


def import_latest(num: int) -> str:
    files = sorted(CDP_LOG.glob("cdp-response-Runtime.evaluate-*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        return "FAIL no cdp file"
    r = subprocess.run(
        [sys.executable, str(IMPORT), str(files[-1]), str(num)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return (r.stdout or r.stderr or "").strip() or f"exit {r.returncode}"


if __name__ == "__main__":
    if sys.argv[1] == "missing":
        print(",".join(str(n) for n in missing_nums()))
    elif sys.argv[1] == "js":
        num = int(sys.argv[2])
        print(EXTRACT_JS.replace("NUM", str(num)))
    elif sys.argv[1] == "import":
        print(import_latest(int(sys.argv[2])))
    elif sys.argv[1] == "count":
        done = len(ASC_TOPICS) - len(missing_nums())
        print(f"{done}/{len(ASC_TOPICS)}")
