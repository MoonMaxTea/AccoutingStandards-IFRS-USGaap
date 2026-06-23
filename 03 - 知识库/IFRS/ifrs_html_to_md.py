#!/usr/bin/env python3
"""
IFRS HTML (saved from IFRS website) → 干净 Markdown 转换器 V3。

改进点：
  - edu note 使用堆叠深度计数器，所有嵌套标签统一增减
  - 正确处理 inline <span class="note edu"> 和 standalone <div class="note edu">
  - 正确处理脚注引用（fn_eduref），保留 [E1] 等标记
  - 正确处理定义链接：保留 *term* 文字，移除 href
  - 正确处理标题中的 linebreak → 空格
  - 跳过 callout box（div.div border-table）中的内容
"""

import sys
import re
from html.parser import HTMLParser
from pathlib import Path


class IFRSHTMLParser(HTMLParser):
    """将 IFRS 标准 HTML 正文解析为 Markdown 行列表。"""

    def __init__(self):
        super().__init__()
        self.lines: list[str] = []
        self._buf: list[str] = []
        self._skip_depth = 0
        self._in_ol = 0               # ol nesting depth (0 = not in ol)
        self._ol_counters: list[int] = []  # li_counter per nesting level
        self._ol_depth = 0            # init for attribute existence
        self._in_board = False
        self._board_entry: list[str] = []
        self._heading_level = 0
        self._pending_heading = ""
        self._in_paranum = False
        self._pending_paranum = ""   # 当前段落的段落号（如 "1", "2A", "B1"）
        self._edu_depth = 0
        self._edu_div_depth = 0
        self._in_fn = False

    def _flush(self):
        text = "".join(self._buf).strip()
        text = re.sub(r"\s+", " ", text)
        text = text.replace("\xad", "").replace("\u00ad", "")
        if not text:
            self._buf = []
            return
        if self._pending_paranum:
            text = f"**{self._pending_paranum}.** {text}"
            self._pending_paranum = ""
        self.lines.append(text)
        self._buf = []

    def _add_blank(self):
        self._flush()
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def _skip_element(self, attrs):
        d = dict(attrs)
        did = d.get("id", "")
        dclass = d.get("class", "")
        # 通用 TOC 匹配: IFRS03_TOC, IAS02_TOC0001, IAS16_TOC0001 等
        if re.match(r'^(IFRS|IAS)\d{2,3}_TOC', did):
            return True
        # 通用 rubric 匹配: IFRS03_rubric, IAS02_rubric 等
        if re.match(r'^(IFRS|IAS)\d{2,3}_rubric', did):
            return True
        if did and did.startswith("IFRS03_FN"):
            return True
        if "edu_fn_table" in dclass:
            return True
        if "fn_eduref_ref" in dclass:
            return True
        return False

    # ── handle_starttag ──

    def handle_starttag(self, tag, attrs):
        if self._skip_depth:
            self._skip_depth += 1
            return
        if self._edu_depth or self._edu_div_depth:
            if self._edu_depth:
                self._edu_depth += 1
            if self._edu_div_depth:
                self._edu_div_depth += 1
            return

        d = dict(attrs)
        dclass = d.get("class", "")
        did = d.get("id", "")

        if self._skip_element(attrs):
            self._skip_depth = 1
            return

        # 标题
        if tag in ("h1", "h2", "h3", "h4", "h5"):
            self._heading_level = int(tag[1])
            self._pending_heading = ""
            self._pending_paranum = ""  # 新章节开始，重置段落号
            return

        # span.note.edu
        if tag == "span" and "note edu" in dclass:
            self._edu_depth = 1
            return

        # div.note.edu
        if tag == "div" and "note edu" in dclass:
            self._edu_div_depth = 1
            return

        # footnotes section
        if tag == "div" and "footnotes" in dclass:
            self._skip_depth = 1
            return

        # linebreak
        if tag == "span" and "linebreak" in dclass:
            if self._heading_level:
                self._pending_heading += " "
            else:
                self._buf.append("\n")
            return

        # paranum
        if tag == "div" and dclass == "paranum":
            self._in_paranum = True
            return

        # 有序列表
        if tag == "table" and "ol" in dclass:
            self._add_blank()
            self._ol_depth = len(self._ol_counters) + 1
            self._ol_counters.append(0)
            return

        if self._ol_depth:
            # 嵌套 ol：检测内层 table.ol
            if tag == "table" and "ol" in dclass:
                self._ol_counters.append(0)
                self._ol_depth += 1
                return
            if tag in ("tr", "td", "table"):
                if tag == "td" and dclass == "ol_col2":
                    self._buf = []
                return
            if tag == "p" and dclass == "ph li_value":
                return
            # 允许 fn_eduref、a、em、strong 等内联标签穿透到通用处理

        # board members
        if tag == "table" and "boardmembers" in dclass:
            self._in_board = True
            return
        if self._in_board:
            if tag == "tr":
                self._board_entry = []
            elif tag == "td":
                self._board_entry.append("")
            return

        # callout box (div.div border-table)
        if tag == "div" and dclass == "div":
            self._skip_depth = 1
            return

        # fn_eduref
        if tag == "span" and "fn_eduref" in dclass:
            self._in_fn = True
            self._buf.append("[")
            return

        if tag == "p":
            return
        if tag == "a":
            return
        if tag == "span" and "definition" in dclass:
            return
        if tag == "span" and "standard_ref" in dclass:
            return

        if tag == "strong":
            self._buf.append("**")
        elif tag == "em":
            self._buf.append("*")
        elif tag == "sub":
            self._buf.append("<sub>")
        elif tag == "sup":
            self._buf.append("<sup>")

    # ── handle_endtag ──

    def handle_endtag(self, tag):
        if self._skip_depth:
            self._skip_depth -= 1
            return
        if self._edu_depth or self._edu_div_depth:
            if self._edu_depth:
                self._edu_depth -= 1
            if self._edu_div_depth:
                self._edu_div_depth -= 1
            return

        if tag in ("h1", "h2", "h3", "h4", "h5"):
            level = int(tag[1])
            text = self._pending_heading or "".join(self._buf).strip()
            text = re.sub(r"\s+", " ", text).replace("\xad", "")
            text = re.sub(r"\s*\n\s*", " ", text)
            self._buf = []
            self._pending_heading = ""
            if text:
                self._add_blank()
                self.lines.append(f"{'#' * level} {text}")
                self._add_blank()
            self._heading_level = 0
            return

        if tag == "div" and self._in_paranum:
            self._in_paranum = False
            return

        if self._ol_depth:
            if tag == "td":
                return
            if tag == "p":
                return  # 在 ol 内，由 tr 处理输出
            if tag == "tr":
                text = "".join(self._buf).strip()
                text = re.sub(r"\s+", " ", text).replace("\xad", "")
                if text:
                    self._ol_counters[-1] += 1
                    self.lines.append(f"{self._ol_counters[-1]}. {text}")
                self._buf = []
                return
            if tag == "table":
                self._ol_counters.pop()
                self._ol_depth = len(self._ol_counters)
                self._add_blank()
                return
            # 其他标签穿透到通用处理

        if self._in_board:
            if tag == "td":
                return
            if tag == "tr":
                if self._board_entry:
                    name = self._board_entry[0].strip() if len(self._board_entry) > 0 else ""
                    title = self._board_entry[1].strip() if len(self._board_entry) > 1 else ""
                    self.lines.append(f"- {name} ({title})" if title else f"- {name}")
                self._board_entry = []
                return
            if tag == "table":
                self._in_board = False
                self._add_blank()
                return
            return

        if tag == "p":
            if self._in_paranum:
                return
            self._flush()
            self._add_blank()
            return

        if tag == "strong":
            self._buf.append("**")
        elif tag == "em":
            self._buf.append("*")
        elif tag == "sub":
            self._buf.append("</sub>")
        elif tag == "sup":
            self._buf.append("</sup>")

        if self._in_fn:
            # footnote reference span closed; close the bracket inline
            self._in_fn = False
            self._buf.append("]")
            return

    # ── handle_data ──

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._edu_depth or self._edu_div_depth:
            return

        clean = data.replace("\xad", "").replace("\u00ad", "")

        if self._in_paranum:
            c = clean.strip()
            if c:
                self._pending_paranum += c
            return

        if self._heading_level:
            c = clean.strip()
            if c:
                self._pending_heading += (" " + c) if self._pending_heading else c
            return

        if self._in_board and self._board_entry:
            idx = len(self._board_entry) - 1
            if 0 <= idx < len(self._board_entry):
                self._board_entry[idx] += data
            return

        self._buf.append(clean)

    def handle_entityref(self, name):
        if self._skip_depth or self._edu_depth or self._edu_div_depth or self._in_paranum:
            return
        if name == "nbsp":
            self._buf.append(" ")
        else:
            self._buf.append(f"&{name};")

    def handle_charref(self, name):
        if self._skip_depth or self._edu_depth or self._edu_div_depth or self._in_paranum:
            return
        self._buf.append(f"&#{name};")


# ─── 主流程 ────────────────────────────────────────────────────

def convert_html_to_md(html_path: str, existing_md_path: str | None = None) -> str:
    html_content = Path(html_path).read_text(encoding="utf-8")
    html_content = html_content.replace("\u2009", " ").replace("\xa0", " ")
    html_content = html_content.replace("&nbsp;", " ")

    parser = IFRSHTMLParser()
    parser.feed(html_content)
    parser.close()
    parser._flush()

    cleaned: list[str] = []
    blank_count = 0
    for line in parser.lines:
        s = line.strip()
        if s == "":
            blank_count += 1
            if blank_count <= 2:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(line)

    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    body_md = "\n".join(cleaned)

    if existing_md_path:
        existing = Path(existing_md_path).read_text(encoding="utf-8")
        parts = existing.split("---", 2)
        if len(parts) >= 3:
            frontmatter = f"---{parts[1]}---"
            remaining = parts[2]
            chinese_end = remaining.rfind("\n---\n")
            if chinese_end == -1:
                chinese_end = remaining.rfind("\n---")
            if chinese_end > 0:
                chinese_section = remaining[:chinese_end].strip()
            else:
                m = re.search(r"\n#+\s|\nIFRS\s", remaining)
                chinese_section = remaining[:m.start()].strip() if m else remaining.strip()
            return f"{frontmatter}\n\n{chinese_section}\n\n---\n\n{body_md}"

    return body_md


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ifrs_html_to_md.py <html_path> [existing_md_path] [output_path]")
        sys.exit(1)

    html_path = sys.argv[1]
    existing_md = sys.argv[2] if len(sys.argv) >= 3 else None
    output_path = sys.argv[3] if len(sys.argv) >= 4 else None

    result = convert_html_to_md(html_path, existing_md)
    if output_path:
        Path(output_path).write_text(result, encoding="utf-8")
        print(f"Done: {output_path} ({len(result.split(chr(10)))} lines)")
    else:
        print(result)
