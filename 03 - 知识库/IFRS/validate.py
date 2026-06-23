"""验证转换后的 IFRS/IAS Markdown 文件质量。"""
import re
from pathlib import Path

TMP_DIR = Path(__file__).resolve().parent.parent.parent / ".tmp"


def check_file(md_path: Path) -> dict:
    """检查单个 MD 文件，返回问题列表。"""
    issues = []
    content = md_path.read_text(encoding="utf-8")

    # 1. 检查 frontmatter
    if not content.startswith("---"):
        issues.append("缺少 frontmatter")

    # 2. 检查中文摘要
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", content))
    if not has_chinese:
        issues.append("缺少中文内容")

    # 3. 检查正文段落号（**N.** 或 **N.N.** 等多级格式）
    paras = re.findall(r"^\*\*\d+[A-Za-z]?\.\*\*", content, re.MULTILINE)
    paras_multi = re.findall(r"^\*\*\d+(\.\d+)+\.\*\*", content, re.MULTILINE)
    if not paras and not paras_multi:
        issues.append("缺少段落号")

    # 4. 检查是否有泄漏的 HTML
    leaked = []
    if re.search(r'class="TOC"', content): leaked.append("TOC")
    if re.search(r'class="rubric"', content): leaked.append("rubric")
    if re.search(r'class="note edu"', content): leaked.append("edu note")
    if leaked:
        issues.append(f"HTML泄漏: {', '.join(leaked)}")

    # 5. 行数
    line_count = content.count("\n")
    if line_count < 20:
        issues.append(f"内容过少({line_count}行)")

    return {
        "file": md_path.name,
        "lines": line_count,
        "paras": len(paras) + len(paras_multi),
        "issues": issues,
        "ok": len(issues) == 0,
    }


def main():
    md_files = sorted(TMP_DIR.glob("*_new.md"))
    if not md_files:
        print("No *_new.md files found")
        return

    results = [check_file(f) for f in md_files]
    ok_count = sum(1 for r in results if r["ok"])
    fail_count = len(results) - ok_count

    print(f"{'File':<35} {'Lines':>6} {'Paras':>5} | Issues")
    print("-" * 75)
    for r in results:
        status = "OK" if r["ok"] else "FAIL"
        issues = "; ".join(r["issues"]) if r["issues"] else "-"
        print(f"{status} {r['file']:<33} {r['lines']:>6} {r['paras']:>5} | {issues}")

    print(f"\nTotal: {ok_count}/{len(results)} passed, {fail_count} with issues")


if __name__ == "__main__":
    main()
