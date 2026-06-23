"""批量将 ASC HTML 转为 Markdown。"""
import subprocess
import sys
from pathlib import Path

TMP_DIR = Path(__file__).resolve().parent.parent.parent / ".tmp"
KB_DIR = Path(__file__).resolve().parent / "ASC准则"
CONVERTER = Path(__file__).resolve().parent / "asc_html_to_md.py"

TMP_DIR.mkdir(parents=True, exist_ok=True)


def convert_one(num: int) -> bool:
    """将 ASC {num} 的 HTML 转为 MD。"""
    html_path = TMP_DIR / f"asc{num}.html"

    # 找对应 MD
    md_candidates = list(KB_DIR.glob(f"ASC {num}*.md"))
    if not md_candidates:
        print(f"  [SKIP] ASC {num}: no MD found")
        return False

    existing_md = md_candidates[0]
    out_md = TMP_DIR / f"asc{num}_new.md"

    cmd = [sys.executable, str(CONVERTER), str(html_path), str(existing_md), str(out_md)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        lines = out_md.read_text(encoding="utf-8").count("\n")
        print(f"  [OK] ASC {num} -> asc{num}_new.md ({lines} lines)")
        return True
    else:
        print(f"  [FAIL] ASC {num}: {r.stderr.strip()[:150]}")
        return False


def main():
    import re
    # 检查 .tmp/ 下有哪些 HTML
    html_files = sorted(TMP_DIR.glob("asc*.html"), key=lambda p: int(re.search(r"asc(\d+)", p.name).group(1)))
    print(f"Found {len(html_files)} HTML files")

    ok = 0
    for h in html_files:
        num = int(re.search(r"asc(\d+)", h.name).group(1))
        if convert_one(num):
            ok += 1

    print(f"\nDone: {ok}/{len(html_files)}")


if __name__ == "__main__":
    main()
