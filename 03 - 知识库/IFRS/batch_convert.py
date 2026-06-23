"""批量将 IFRS/IAS HTML 转为 Markdown，写入 .tmp/ 目录。"""
import subprocess
import sys
from pathlib import Path

SRC_DIR = Path(r"C:\Users\Administrator\Desktop\IFRSprincipal")
SCRIPT_DIR = Path(__file__).resolve().parent
TMP_DIR = SCRIPT_DIR.parent.parent / ".tmp"
KB_BASE = SCRIPT_DIR   # 脚本在 IFRS/ 下，KB_BASE 即自身
KB_IFRS = KB_BASE / "IFRS准则"
KB_IAS = KB_BASE / "IAS准则"
CONVERTER = Path(__file__).resolve().parent / "ifrs_html_to_md.py"

CONVERTER = CONVERTER.resolve()
SRC_DIR = SRC_DIR.resolve()
TMP_DIR = TMP_DIR.resolve()
KB_IFRS = KB_IFRS.resolve()
KB_IAS = KB_IAS.resolve()


def name_to_md(html_name: str) -> tuple[str, Path] | None:
    """从 HTML 文件名推断对应的知识库 MD 文件名。返回 (md_name, kb_dir)。"""
    import re
    stem = Path(html_name).stem
    m = re.match(r'^(ifrs|ias)(\d+)$', stem.lower())
    if not m:
        return None
    prefix = m.group(1).upper()
    num = m.group(2)

    kb_dir = KB_IFRS if prefix == "IFRS" else KB_IAS
    for md in kb_dir.glob(f"{prefix} {num}*.md"):
        return (md.name, kb_dir)
    return None


def main():
    html_files = sorted(SRC_DIR.glob("*.html"))
    print(f"Found {len(html_files)} HTML files")

    TMP_DIR.mkdir(parents=True, exist_ok=True)

    ok = 0
    failed = []

    for html_path in html_files:
        result = name_to_md(html_path.name)
        if result is None:
            print(f"  [SKIP] {html_path.name}: no matching MD found")
            failed.append((html_path.name, "no matching MD"))
            continue

        md_name, kb_dir = result
        existing_md = kb_dir / md_name
        out_md = TMP_DIR / (html_path.stem + "_new.md")

        cmd = [
            sys.executable, str(CONVERTER),
            str(html_path), str(existing_md), str(out_md),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            ok += 1
            print(f"  [OK] {html_path.name} -> {out_md.name} ({out_md.stat().st_size} bytes)")
        else:
            failed.append((html_path.name, r.stderr.strip()[:200]))
            print(f"  [FAIL] {html_path.name}: {r.stderr.strip()[:200]}")

    print(f"\nDone: {ok}/{len(html_files)} success, {len(failed)} failed")
    if failed:
        print("Failures:")
        for name, reason in failed:
            print(f"  - {name}: {reason}")


if __name__ == "__main__":
    main()
