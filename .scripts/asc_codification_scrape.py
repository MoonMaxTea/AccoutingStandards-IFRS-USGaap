#!/usr/bin/env python3
"""从 FASB ASC 官网 (asc.fasb.org) 抓取 Codification 现行全文并写入 Markdown 笔记。

用法:
  python asc_codification_scrape.py              # 试点 ASC 606
  python asc_codification_scrape.py 606 842      # 指定 Topic
  python asc_codification_scrape.py 606 --headed   # 有界面，便于调试
  python asc_codification_scrape.py 606 --debug    # 保存截图与 HTML 到 .tmp/asc-debug/
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import date
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ASC_DIR = ROOT / "03 - 知识库/US GAAP/ASC准则"
DEBUG_DIR = ROOT / ".tmp/asc-debug"
HOME = "https://asc.fasb.org/Home"

# Topic 元数据：num -> (英文名, 中文名, 要合并的 Subtopic 列表, 是否重点)
TOPICS: dict[int, dict] = {
    606: {
        "name_en": "Revenue From Contracts With Customers",
        "name_cn": "客户合同收入",
        "subtopics": ["606-10"],
        "key": True,
    },
    842: {
        "name_en": "Leases",
        "name_cn": "租赁",
        "subtopics": ["842-10", "842-20", "842-30"],
        "key": True,
    },
    805: {
        "name_en": "Business Combinations",
        "name_cn": "企业合并",
        "subtopics": ["805-10"],
        "key": True,
    },
    820: {
        "name_en": "Fair Value Measurement",
        "name_cn": "公允价值计量",
        "subtopics": ["820-10"],
        "key": True,
    },
}


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip() + "\n"


def slug_filename(num: int, name_en: str) -> str:
    return ASC_DIR / f"ASC {num} - {name_en}.md"


def build_markdown(meta: dict, num: int, parts: list[tuple[str, str]]) -> str:
    tag = f"asc-{num}"
    key_line = "key: true\n" if meta.get("key") else ""
    subtopics_yaml = ", ".join(f'"{s}"' for s in meta["subtopics"])
    today = date.today().isoformat()
    fm = f"""---
tags: [us-gaap, {tag}]
standard: ASC {num}
source: FASB ASC
source_url: https://asc.fasb.org/
source_type: Codification
scraped_date: "{today}"
subtopics: [{subtopics_yaml}]
{key_line}---
"""
    title = f"# ASC {num} — {meta['name_en']}（{meta['name_cn']}）"
    if meta.get("key"):
        title += " ⭐ 重点准则"
    body_parts: list[str] = [f"{fm}\n{title}\n"]
    for subtopic, text in parts:
        body_parts.append(f"\n---\n\n## Subtopic {subtopic}\n\n{text}")
    return "\n".join(body_parts)


def accept_home(page: Page, debug: bool) -> None:
    page.goto(HOME, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(1500)
    for label in ("Access", "ACCESS", "Access the Basic View"):
        btn = page.get_by_role("button", name=re.compile(label, re.I))
        if btn.count() > 0:
            btn.first.click()
            page.wait_for_timeout(2000)
            break
        link = page.get_by_role("link", name=re.compile(label, re.I))
        if link.count() > 0:
            link.first.click()
            page.wait_for_timeout(2000)
            break
    if debug:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=DEBUG_DIR / "01-after-access.png", full_page=True)


def goto_subtopic(page: Page, subtopic: str) -> None:
    """导航到 Subtopic  landing page。"""
    # 常见 URL 模式
    candidates = [
        f"https://asc.fasb.org/{subtopic}/tableOfContent",
        f"https://asc.fasb.org/{subtopic.replace('-', '')}/tableOfContent",
        f"https://asc.fasb.org/{subtopic}",
    ]
    topic_num = subtopic.split("-")[0]
    candidates.append(f"https://asc.fasb.org/{topic_num}/tableOfContent")

    last_err: Exception | None = None
    for url in candidates:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(2000)
            if subtopic.replace("-", "") in page.url or subtopic in page.content():
                return
        except Exception as exc:
            last_err = exc
    # Go To 搜索框
    try:
        goto_input = page.locator(
            "input[placeholder*='Go'], input[id*='GoTo'], input[name*='GoTo'], #GoToInput"
        ).first
        if goto_input.count() > 0:
            goto_input.fill(subtopic)
            goto_input.press("Enter")
            page.wait_for_timeout(3000)
            return
    except Exception as exc:
        last_err = exc
    if last_err:
        raise RuntimeError(f"无法导航到 Subtopic {subtopic}: {last_err}")


def click_join_all_sections(page: Page) -> bool:
    """点击 Join All Sections / Show All in One Page。"""
    patterns = [
        re.compile(r"join\s*all\s*sections", re.I),
        re.compile(r"show\s*all\s*in\s*one\s*page", re.I),
        re.compile(r"join\s*all", re.I),
    ]
    for pat in patterns:
        for role in ("button", "link"):
            loc = page.get_by_role(role, name=pat)
            if loc.count() > 0:
                loc.first.click()
                return True
    # 文本匹配 fallback
    loc = page.locator("a, button, span").filter(has_text=patterns[0])
    if loc.count() > 0:
        loc.first.click()
        return True
    return False


def wait_for_content(page: Page, subtopic: str, timeout_ms: int = 120_000) -> None:
    """等待合并页出现段落号。"""
    prefix = subtopic  # e.g. 606-10
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        body = page.inner_text("body")
        if re.search(rf"{re.escape(prefix)}-\d+-\d+", body):
            return
        page.wait_for_timeout(2000)
    raise TimeoutError(f"等待 Subtopic {subtopic} 合并内容超时")


def extract_body_text(page: Page) -> str:
    """尽量只取正文区域。"""
    selectors = [
        "#content",
        ".content",
        "#mainContent",
        "main",
        "#codificationContent",
        ".codification-content",
        "article",
    ]
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count() > 0:
            text = loc.first.inner_text()
            if len(text) > 500:
                return normalize_text(text)
    return normalize_text(page.inner_text("body"))


def scrape_subtopic(page: Page, subtopic: str, debug: bool) -> str:
    goto_subtopic(page, subtopic)
    if debug:
        page.screenshot(path=DEBUG_DIR / f"02-{subtopic}-landing.png", full_page=True)

    if not click_join_all_sections(page):
        # 可能已在合并页，或按钮文案不同
        print(f"  警告: 未找到 Join All Sections，尝试直接提取当前页")

    page.wait_for_timeout(3000)
    wait_for_content(page, subtopic)
    if debug:
        page.screenshot(path=DEBUG_DIR / f"03-{subtopic}-merged.png", full_page=True)
        (DEBUG_DIR / f"03-{subtopic}-merged.html").write_text(
            page.content(), encoding="utf-8"
        )

    return extract_body_text(page)


def scrape_topic(num: int, headed: bool, debug: bool) -> bool:
    if num not in TOPICS:
        print(f"ASC {num}: 未在 TOPICS 配置中，请先在脚本里添加")
        return False

    meta = TOPICS[num]
    ASC_DIR.mkdir(parents=True, exist_ok=True)
    md_path = slug_filename(num, meta["name_en"])
    print(f"ASC {num}: {meta['name_en']}")

    parts: list[tuple[str, str]] = []
    with sync_playwright() as p:
        launch_opts: dict = {"headless": not headed}
        for channel in ("chrome", "msedge", None):
            try:
                if channel:
                    browser = p.chromium.launch(channel=channel, **launch_opts)
                else:
                    browser = p.chromium.launch(**launch_opts)
                break
            except Exception as exc:
                if channel is None:
                    raise RuntimeError(
                        "无法启动浏览器。请运行: python -m playwright install chromium"
                    ) from exc
        else:
            browser = p.chromium.launch(**launch_opts)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1400, "height": 900},
        )
        page = context.new_page()
        try:
            accept_home(page, debug)
            for subtopic in meta["subtopics"]:
                print(f"  Subtopic {subtopic} …")
                text = scrape_subtopic(page, subtopic, debug)
                print(f"  提取 {len(text):,} 字符")
                parts.append((subtopic, text))
        finally:
            browser.close()

    if not parts or all(len(t) < 1000 for _, t in parts):
        print("  失败: 提取内容过短")
        return False

    md_path.write_text(build_markdown(meta, num, parts), encoding="utf-8")
    print(f"  已写入: {md_path.name} ({md_path.stat().st_size:,} 字节)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="从 asc.fasb.org 抓取 ASC Codification")
    parser.add_argument("topics", nargs="*", type=int, default=[606])
    parser.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    parser.add_argument("--debug", action="store_true", help="保存截图与 HTML")
    args = parser.parse_args()

    ok = 0
    for num in args.topics:
        if scrape_topic(num, args.headed, args.debug):
            ok += 1
    print(f"\n完成: {ok}/{len(args.topics)} 个 Topic")
    return 0 if ok == len(args.topics) else 1


if __name__ == "__main__":
    sys.exit(main())
