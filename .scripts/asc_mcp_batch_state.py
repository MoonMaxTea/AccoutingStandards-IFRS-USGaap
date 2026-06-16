#!/usr/bin/env python3
"""MCP 批量导出状态追踪（仅读写 .tmp/asc-export-state.json）。"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".tmp/asc-export-state.json"


def load() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"ok": [], "fail": []}


def save(data: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record(num: int, status: str) -> None:
    data = load()
    key = "ok" if status == "OK" else "fail"
    lst = data.setdefault(key, [])
    if num in lst:
        lst.remove(num)
    (data["fail"] if status == "OK" else data["ok"])
    if status == "OK" and num in data.get("fail", []):
        data["fail"].remove(num)
    if status != "OK" and num in data.get("ok", []):
        data["ok"].remove(num)
    if num not in lst:
        lst.append(num)
    data["updated"] = datetime.now(timezone.utc).isoformat()
    save(data)
    print(f"{status} {num} | ok={len(data.get('ok',[]))} fail={len(data.get('fail',[]))}")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        record(int(sys.argv[1]), sys.argv[2])
    else:
        print(json.dumps(load(), indent=2))
