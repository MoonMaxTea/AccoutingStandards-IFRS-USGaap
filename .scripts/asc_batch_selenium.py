#!/usr/bin/env python3
"""DEPRECATED: 勿用。会唤起本机 Edge，请改用 cursor-ide-browser MCP。"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asc_topics import ASC_TOPICS

ROOT = Path(__file__).resolve().parents[1]
CDP_DIR = ROOT / ".tmp/asc-cdp"
LOG = ROOT / ".logs/cursor/asc-export.log"
IMPORT = ROOT / ".scripts/asc_batch_export_runner.py"


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now().isoformat()}] {msg}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def is_done(num: int, name_en: str) -> bool:
    p = ROOT / "03 - 知识库/US GAAP/ASC准则" / f"ASC {num} - {name_en}.md"
    if not p.exists() or p.stat().st_size < 3000:
        return False
    head = p.read_text(encoding="utf-8")[:8000]
    return bool(re.search(rf"{num}-\d{{2}}-\d{{2}}-\d+", head))


def wait_body(driver, num: int, timeout: int = 90) -> str:
    pat = re.compile(rf"{num}-\d{{2}}-\d{{2}}-\d+")

    def ready(d):
        t = d.find_element("tag name", "body").text
        return len(t) > 5000 and pat.search(t)

    WebDriverWait(driver, timeout).until(ready)
    return driver.find_element("tag name", "body").text


def export_one(driver, num: int) -> None:
    url = f"https://asc.fasb.org/{num}/showallinonepage"
    driver.get(url)
    text = wait_body(driver, num)
    if re.search(r"cloudflare|verify you are human", text[:2000], re.I):
        raise RuntimeError("Cloudflare 拦截")

    CDP_DIR.mkdir(parents=True, exist_ok=True)
    cdp_path = CDP_DIR / f"asc-{num}.json"
    cdp_path.write_text(json.dumps({"result": {"value": text}}), encoding="utf-8")

    import subprocess

    r = subprocess.run(
        [sys.executable, str(IMPORT), str(cdp_path), str(num)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr or r.stdout or "import failed")


def main() -> None:
    skip_done = "--skip-done" in sys.argv
    only = None
    for i, a in enumerate(sys.argv):
        if a == "--only" and i + 1 < len(sys.argv):
            only = [int(x.strip()) for x in sys.argv[i + 1].split(",")]

    topics = ASC_TOPICS
    if only:
        topics = [t for t in topics if t[0] in only]
    if skip_done:
        topics = [t for t in topics if not is_done(t[0], t[1])]

    log(f"Selenium 批量导出 {len(topics)} 个 Topic")

    opts = Options()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Edge(options=opts)
    failed: list[tuple[int, str]] = []

    try:
        for num, en, _, _ in topics:
            try:
                export_one(driver, num)
            except Exception as e:
                log(f"FAIL ASC {num}: {e}")
                failed.append((num, str(e)))
                time.sleep(2)
    finally:
        driver.quit()

    log(f"完成。失败 {len(failed)}/{len(topics)}")
    if failed:
        (ROOT / ".logs/cursor/asc-export-failed.json").write_text(
            json.dumps([{"num": n, "error": e} for n, e in failed], indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
