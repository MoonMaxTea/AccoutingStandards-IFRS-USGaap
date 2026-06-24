#!/usr/bin/env python3
"""
ASC Codification HTML (from FASB SPA) → 干净 Markdown 转换器 V2。

核心修复：
- article.dita-content 关闭时 flush 段落
- div.p 支持独立段落（含术语定义）
- h4 术语标题
- ol.ol-norm 有序列表
- table.topic-table 表格
- strong/em/sup 内联格式
"""

import sys
import re
from html.parser import HTMLParser
from pathlib import Path


class ASCHTMLParser(HTMLParser):
    """将 ASC Codification HTML 正文解析为 Markdown 行列表。"""

    SKIP_CLASSES = {
        "hide-content", "sfragment-data", "linum",
    }

    def __init__(self):
        super().__init__()
        self.lines: list[str] = []
        self._buf: list[str] = []
        self._skip_depth = 0
        self._heading_level = 0
        self._pending_heading = ""
        self._pending_para_id = ""     # div.paragraphId 或 div.pn
        self._in_article = 0           # article.dita-content 内（0或1，非嵌套）
        self._in_div_p = 0             # div.p 深度（非 article 内）
        self._in_norm_text = 0         # div.norm-text 深度
        self._in_pn = 0               # div.pn（段落号）深度
        self._in_ol = 0               # ol.ol-norm 深度
        self._ol_counter = 0
        self._in_table = 0
        self._table_rows: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []
        self._in_cell = False
        self._in_info_box = 0
        self._in_strong = 0
        self._in_em = 0
        self._in_sup = 0

    def _flush(self):
        text = "".join(self._buf).strip()
        text = re.sub(r"\s+", " ", text).replace("\xad", "")
        self._buf = []
        if not text:
            self._pending_para_id = ""
            return

        para = self._pending_para_id
        self._pending_para_id = ""

        if para:
            self.lines.append(f"**{para}** {text}")
        else:
            self.lines.append(text)

    def _add_blank(self):
        if not self.lines or self.lines[-1] != "":
            self.lines.append("")

    def _skip_element(self, tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        dclass = dict(attrs).get("class", "")
        did = dict(attrs).get("id", "")
        if tag == "img":
            return True
        if any(c in self.SKIP_CLASSES for c in dclass.split()):
            return True
        if did in ("main-section-name", "section-name"):
            return True
        return False

    # ── start tag ──────────────────────────────────────────
    def handle_starttag(self, tag, attrs):
        dclass = dict(attrs).get("class", "")

        if self._skip_element(tag, attrs):
            self._skip_depth += 1
            if tag in ("img", "br", "hr", "input", "link", "meta"):
                self._skip_depth -= 1  # 自闭合标签，不泄露
            return

        if self._skip_depth > 0:
            self._skip_depth += 1
            return

        # ── 标题 h1/h2/h4 ──
        if tag in ("h1", "h2"):
            self._heading_level = int(tag[1])
            self._pending_heading = ""
            return

        if tag == "h4":
            self._heading_level = 4
            self._pending_heading = ""
            return

        # ── 段落 ID ──
        if tag == "div" and "paragraphId" in dclass.split():
            self._pending_para_id = ""
            return

        # ── article.dita-content ── (使用布尔值而非计数器，避免 Angular 嵌套干扰)
        if tag == "article" and "dita-content" in dclass.split():
            self._in_article = 1
            return

        # ── div.p（不在 article/ol/info_box 内）──
        if tag == "div" and "p" in dclass.split() and self._in_article == 0 and self._in_ol == 0 and self._in_info_box == 0:
            self._in_div_p += 1
            return

        # ── div.norm-text（ASC 正文段落容器）──
        if tag == "div" and "norm-text" in dclass.split():
            self._in_norm_text += 1
            # flush 之前积累的文本（如上一个段落号）
            if self._buf:
                self._flush()
            return

        # ── div.pn（段落号，如 350-10-05-3）──
        if tag == "div" and "pn" in dclass.split():
            self._in_pn += 1
            self._pending_para_id = ""
            return

        # ── Info Box ──
        if tag == "div" and "info-box" in dclass.split():
            self._in_info_box += 1
            self._add_blank()
            self._buf = []   # 清除导航 header 残留文本
            return

        # ── 有序列表 ol.ol-norm ──
        if tag == "ol" and "ol-norm" in dclass.split():
            self._in_ol += 1
            self._ol_counter = 0
            return

        if self._in_ol > 0 and tag == "li":
            self._ol_counter += 1
            self._buf = []  # 每个 li 单独收集
            return

        # ── 表格 ──
        if tag == "table" and "topic-table" in dclass.split():
            self._in_table += 1
            self._table_rows = []
            return

        if self._in_table > 0 and tag == "tr":
            self._current_row = []
            return

        if self._in_table > 0 and tag in ("td", "th"):
            self._in_cell = True
            self._current_cell = []

        # ── 内联格式 ──
        if tag == "strong":
            self._in_strong += 1
            self._buf.append("**")
            return

        if tag == "em":
            self._in_em += 1
            self._buf.append("*")
            return

        if tag == "sup":
            self._in_sup += 1
            self._buf.append("^")
            return

        # ── 链接：跳过，只保留文字 ──
        if tag == "a":
            return

        # ── span.sfragment（在 article 外跳过，在 article 内保留 source 文本）──
        if tag == "span" and dclass == "sfragment" and self._in_article == 0:
            return

    # ── end tag ────────────────────────────────────────────
    def handle_endtag(self, tag):
        dclass = ""  # placeholder, end tags don't have attrs in HTMLParser

        if self._skip_depth > 0:
            self._skip_depth -= 1
            return

        # ── 标题 ──
        if tag in ("h1", "h2", "h4"):
            heading = self._pending_heading.strip()
            self._pending_heading = ""
            lvl = self._heading_level
            self._heading_level = 0
            if heading:
                prefix = "#" * min(lvl + 1, 6)  # h1→##, h2→###, h4→#####
                self._add_blank()
                self.lines.append(f"{prefix} {heading}")
                self._add_blank()
            return

        # ── article 结束：flush 段落 ──
        if tag == "article" and self._in_article > 0:
            self._in_article = 0
            self._flush()
            return

        # ── div.p 结束 ──
        if tag == "div" and self._in_div_p > 0:
            self._in_div_p -= 1
            if self._in_div_p == 0:
                self._flush()
            return

        # ── div.norm-text 结束 ──
        if tag == "div" and self._in_norm_text > 0:
            self._in_norm_text -= 1
            if self._in_norm_text == 0:
                self._flush()
            return

        # ── div.pn 结束 ──
        if tag == "div" and self._in_pn > 0:
            self._in_pn -= 1
            # pn text is stored in _pending_para_id via _flush behaviour
            # The superclass ASC_ParaId_Wrapper handles pn data collection
            return

        # ── Info Box ──
        if tag == "div" and self._in_info_box > 0:
            self._in_info_box -= 1
            if self._in_info_box == 0:
                text = "".join(self._buf).strip()
                text = re.sub(r"\s+", " ", text).replace("\xad", "")
                # 去除内嵌 "General Note:" 前缀
                text = re.sub(r"^(General Note:\s*)+", "", text).strip()
                self._buf = []
                if text:
                    self.lines.append(f"> **General Note:** {text}")
                self._add_blank()
            return

        # ── 有序列表 ──
        if tag == "ol" and self._in_ol > 0:
            self._in_ol -= 1
            self._add_blank()
            return

        if tag == "li" and self._in_ol > 0:
            text = "".join(self._buf).strip()
            text = re.sub(r"\s+", " ", text).replace("\xad", "")
            self._buf = []
            if text:
                self.lines.append(f"{self._ol_counter}. {text}")
            return

        # ── 表格 ──
        if tag == "table" and self._in_table > 0:
            self._in_table -= 1
            if self._in_table == 0 and self._table_rows:
                self._emit_table()
            return

        if tag == "tr" and self._in_table > 0:
            if self._current_row:
                self._table_rows.append(self._current_row)
            self._current_row = []
            return

        if tag in ("td", "th") and self._in_table > 0:
            self._in_cell = False
            text = "".join(self._current_cell).strip()
            text = re.sub(r"\s+", " ", text).replace("\xad", "")
            self._current_row.append(text)
            return

        # ── 内联格式 ──
        if tag == "strong" and self._in_strong > 0:
            self._in_strong -= 1
            self._buf.append("**")
            return

        if tag == "em" and self._in_em > 0:
            self._in_em -= 1
            self._buf.append("*")
            return

        if tag == "sup" and self._in_sup > 0:
            self._in_sup -= 1
            self._buf.append("^")
            return

        # ── a / span ──
        if tag in ("a", "span"):
            return

    # ── data ────────────────────────────────────────────────
    def handle_data(self, data):
        if self._skip_depth > 0:
            return

        if self._heading_level > 0:
            self._pending_heading += data
            return

        if self._in_cell:
            self._current_cell.append(data)
            return

        if self._pending_para_id is not None and self._pending_para_id == "":
            # 检查是否正在收集 paragraphId
            # 但实际上 paragraphId div 已经启动了
            pass

        self._buf.append(data)

    # ── paragraphId 通过 handle_data 收集 ──
    # 不需要额外逻辑，data 直接进入 _buf，但我们需要区分
    # paragraphId 的内容和普通正文内容。
    # 修复：paragraphId div 内 data 收集到 _pending_para_id

    # ── entities ────────────────────────────────────────────
    def handle_entityref(self, name):
        if name == "nbsp":
            self.handle_data(" ")
        elif name == "amp":
            self.handle_data("&")
        elif name == "lt":
            self.handle_data("<")
        elif name == "gt":
            self.handle_data(">")
        elif name == "quot":
            self.handle_data('"')
        elif name == "reg":
            self.handle_data("\u00ae")

    def handle_charref(self, name):
        try:
            n = int(name[1:]) if name.startswith("x") else int(name)
            self.handle_data(chr(n))
        except (ValueError, OverflowError):
            self.handle_data(name)

    # ── table emit ──────────────────────────────────────────
    def _emit_table(self):
        if len(self._table_rows) < 1:
            return

        self._add_blank()
        header = self._table_rows[0]
        self.lines.append("| " + " | ".join(header) + " |")
        self.lines.append("|" + "|".join(" --- " for _ in header) + "|")

        for row in self._table_rows[1:]:
            while len(row) < len(header):
                row.append("")
            self.lines.append("| " + " | ".join(row[:len(header)]) + " |")

        self._add_blank()


class ASC_ParaId_Wrapper(ASCHTMLParser):
    """拦截 div.paragraphId / div.pn 中的 data，与正文 data 隔离。"""

    def __init__(self):
        super().__init__()
        self._in_para_id_div = 0
        self._in_pn_div = 0

    def handle_starttag(self, tag, attrs):
        dclass = dict(attrs).get("class", "")
        if tag == "div" and "paragraphId" in dclass.split():
            self._in_para_id_div += 1
            self._pending_para_id = ""
        elif tag == "div" and "pn" in dclass.split():
            self._in_pn_div += 1
            self._pending_para_id = ""
        else:
            super().handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "div" and self._in_para_id_div > 0:
            self._in_para_id_div -= 1
        elif tag == "div" and self._in_pn_div > 0:
            self._in_pn_div -= 1
        else:
            super().handle_endtag(tag)

    def handle_data(self, data):
        if self._in_para_id_div > 0 or self._in_pn_div > 0:
            self._pending_para_id += data
        else:
            super().handle_data(data)


def convert_html_to_md(html_content: str, existing_md_path: Path) -> str:
    """将 ASC HTML 转换为 Markdown，合并现有 MD 的 frontmatter 和中文摘要。"""
    parser = ASC_ParaId_Wrapper()
    parser.feed(html_content)
    parser._flush()

    # 清理多余空行 + 空 strong 对 + 空表格行
    clean_lines = []
    blank_count = 0
    for line in parser.lines:
        # 移除空 ** 对
        line = re.sub(r"\*\*\*\*\*\*\*\*+", "", line)
        if line.strip() == "**":
            continue
        # 移除纯空内容的表格行 (|  |  |  |)
        if re.match(r"^\|\s*(\|\s*)+$", line):
            continue

        if line == "":
            blank_count += 1
            if blank_count <= 2:
                clean_lines.append(line)
        else:
            blank_count = 0
            clean_lines.append(line)

    body = "\n".join(clean_lines).strip()

    # 从现有 MD 提取 frontmatter + 中文摘要
    frontmatter = ""
    chinese_summary = ""

    if existing_md_path and existing_md_path.exists():
        content = existing_md_path.read_text(encoding="utf-8")
        fm_match = re.match(r"^(---\n.*?\n---)", content, re.DOTALL)
        if fm_match:
            frontmatter = fm_match.group(1)

        summary_match = re.search(
            r"(##\s*📌\s*中文提炼[\s\S]*?)(?=\n##\s|\n---\n|\Z)",
            content
        )
        if summary_match:
            chinese_summary = summary_match.group(1).strip()

    parts = []
    if frontmatter:
        parts.append(frontmatter)
    if chinese_summary:
        parts.append("\n" + chinese_summary)
    if frontmatter or chinese_summary:
        parts.append("\n---\n")
    parts.append(body)

    return "\n".join(parts)


def main():
    if len(sys.argv) < 4:
        print("Usage: python asc_html_to_md.py <html_file> <existing_md> <output_md>")
        sys.exit(1)

    html_path = Path(sys.argv[1])
    existing_md = Path(sys.argv[2])
    out_path = Path(sys.argv[3])

    html_content = html_path.read_text(encoding="utf-8")
    result = convert_html_to_md(html_content, existing_md)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result, encoding="utf-8")
    print(f"Done: {out_path} ({len(result.splitlines())} lines)")


if __name__ == "__main__":
    main()
