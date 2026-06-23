# IFRS/IAS 准则 HTML 导出 → Markdown 全流程指引

> 本指引涵盖从 IFRS 官网获取标准 HTML、转换为可读 Markdown、到写入知识库的完整流程。

## 概述

**目标**：用 IFRS 官网 HTML 版代替 PDF 版作为正文来源，产生格式清爽、无中英文混杂的 Markdown 文件。

**核心脚本**：`.scripts/ifrs_html_to_md.py`

**适用准则**：全部 IFRS 准则（IFRS 1–19）和 IAS 准则（IAS 1–41）

---

## 1. 前置条件

- Python 3.8+，**无需安装任何第三方包**（仅用内置 `html.parser`）
- IFRS 官网账号（需登录后才能访问标准全文）
- Cursor IDE 已启用 Browser Automation MCP（自动化下载时需要）

---

## 2. 获取 HTML 文件

### 方式 A：手动保存（推荐，最可靠）

1. 浏览器登录 [IFRS 官网](https://www.ifrs.org/)
2. 进入目标准则页面，例如 `IFRS 3 — Business Combinations`
3. 切换到 **"Standard"** 标签页
4. 在页面空白处右键 → **"另存为"** → 选择 **"网页，仅 HTML"**
5. 保存到项目 `.tmp/` 目录下

> HTML 文件命名规则（必须严格遵循）：
> - IFRS: `ifrs{N}.html`（如 `ifrs3.html`、`ifrs18.html`）
> - IAS: `ias{N}.html`（如 `ias1.html`、`ias36.html`）
>
> 此命名与 HTML 内部锚点链接一致，脚本依赖此规则进行解析。

### 方式 B：Browser MCP 自动化下载（批量导出首选）

1. 打开任意 IFRS 标准主站页面（确保已登录）
2. 通过 CDP `Runtime.evaluate` 在浏览器控制台执行 fetch + Blob 下载
3. 每触发一次下载会弹出保存对话框，保存到 `C:\Users\Administrator\Downloads\`

**一键触发下载的 CDP 命令模式**：

```javascript
(async() => {
  const r = await fetch('/content/dam/ifrs/publications/html-standards/english/2026/issued/ifrs{N}.html');
  const h = await r.text();
  const b = new Blob([h], {type: 'text/html'});
  const u = URL.createObjectURL(b);
  const a = document.createElement('a');
  a.href = u; a.download = 'ifrs{N}.html';
  document.body.appendChild(a); a.click();
  document.body.removeChild(a); URL.revokeObjectURL(u);
})()
```

替换 `{N}` 为目标标准编号即可。IAS 准则同理，URL 路径使用 `/content/dam/ifrs/publications/html-standards/english/2026/issued/ias{N}.html`。

---

## 3. 将 HTML 转换为 Markdown

### 单文件转换

```powershell
python .scripts/ifrs_html_to_md.py 输入HTML路径 [已有MD路径] [输出路径]
```

**参数说明**：

| 参数 | 必填 | 说明 |
|------|------|------|
| `html_path` | 是 | 源 HTML 文件路径 |
| `existing_md_path` | 否 | 已有 Markdown 文件路径，用于提取 frontmatter 和中文提炼区 |
| `output_path` | 否 | 输出文件路径，不填则打印到 stdout |

**示例**：

```powershell
# 不带中文提炼（纯 HTML → MD）
python .scripts/ifrs_html_to_md.py ".tmp/ifrs3.html"

# 带中文提炼（HTML → MD，合并现有 frontmatter + 中文提炼）
python .scripts/ifrs_html_to_md.py ".tmp/ifrs3.html" "03 - 知识库/IFRS/IFRS准则/IFRS 3 - Business Combinations.md" ".tmp/ifrs3_test.md"
```

### 批量转换

```powershell
# 批量转换 .tmp/ 下所有已下载的 HTML
Get-ChildItem ".tmp/*.html" | ForEach-Object {
    $name = $_.BaseName           # 如 ifrs3
    $std = $name.ToUpper()        # 如 IFRS3
    $num = $std -replace '\D', '' # 如 3
    $prefix = if ($name -match '^ifrs') { "IFRS" } else { "IAS" }
    
    # 查找已有 MD 文件（大小写不敏感）
    $existing = Get-ChildItem "03 - 知识库/IFRS/${prefix}准则/" -Filter "*$prefix $num*" | Select-Object -First 1
    
    if ($existing) {
        python .scripts/ifrs_html_to_md.py ".tmp/$($_.Name)" $existing.FullName ".tmp/$($_.BaseName)_new.md"
        Write-Host "OK: $($_.BaseName)"
    } else {
        Write-Host "SKIP: $($_.BaseName) — 没有找到已有 MD"
    }
}
```

---

## 4. 转换效果说明

### 保留内容

| 元素 | 处理方式 |
|------|----------|
| **Frontmatter** | 从已有 MD 原样保留 |
| **中文提炼区** | 从已有 MD 原样保留（正文前区域） |
| **标题 h1–h5** | 转换为 `#`–`#####` |
| **段落号** `<div.paranum>` | 捕获段落号，拼接到下一段落开头，格式为 `**N.** `（含附录号如 B1, B7A） |
| **段落 `<p>`** | 按原文输出，段落间留空行 |
| **有序列表** `<table.ol>` | 转换为 `1.` `2.` `3.` 格式 |
| **定义术语** `<span.definition>` | 保留 `*斜体*` 或原文，去除链接 |
| **脚注引用** `<span.fn_eduref>` | 保留 `[E1]`、`[E2]` 等标记 |
| **粗体/斜体** | 保留 `**粗体**` / `*斜体*` |
| **Board 成员表** | 转换为 `- Name (Title)` 列表 |

### 删除内容

| 元素 | 处理方式 |
|------|----------|
| **教育注释** `<span.note.edu>` / `<div.note.edu>` | 全部删除 |
| **目录 (TOC)** | 删除 |
| **使用说明 (rubric)** | 删除 |
| **脚注详细说明** | 删除 |
| **版权声明** | 删除 |
| **内部链接** `<a>` | 删除 href，仅保留文字 |

### 与 PDF 版本对比

| 指标 | PDF 版 | HTML 版 |
|------|--------|---------|
| 中文注释 | 存在大量 | **无** |
| 孤立段落号 | 存在 | **无** |
| 页眉/页脚 | 存在 | **无** |
| edu 注释 | 存在 | **无** |
| 正文行数（IFRS 3） | ~2,081 | **979**（减少 53%） |
| 可读性 | 差 | **优秀** |

---

## 5. 后续步骤（写入知识库前）

### 5.1 验证转换质量

```powershell
# 抽查：对比新旧版本的关键段落
python -c "
old = open('03 - 知识库/IFRS/IFRS准则/IFRS 3 - Business Combinations.md', encoding='utf-8').read()
new = open('.tmp/ifrs3_v3.md', encoding='utf-8').read()
print(f'旧版行数: {len(old.splitlines())}')
print(f'新版行数: {len(new.splitlines())}')
# 验证 Objective 段落存在
assert 'The objective of this IFRS' in new, 'Objective missing!'
print('✓ Objective 存在')
"
```

### 5.2 添加来源链接到 Frontmatter

在每条准则的 frontmatter 中添加 `url` 字段：

```yaml
---
tags: [ifrs, ifrs-3]
standard: IFRS 3
source: IFRS Foundation
url: https://www.ifrs.org/issued-standards/list-of-standards/ifrs-3-business-combinations/
key: true
---
```

> IFRS 官网 URL 规律：`https://www.ifrs.org/issued-standards/list-of-standards/ifrs-{编号}-{英文名-小写-连字符}/`

### 5.3 覆盖写入知识库

确认质量无误后：

```powershell
Copy-Item ".tmp/ifrs3_new.md" "03 - 知识库/IFRS/IFRS准则/IFRS 3 - Business Combinations.md" -Force
```

---

## 6. IFRS 官网 URL 速查表

| 标准 | URL |
|------|-----|
| IFRS 1 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-1-first-time-adoption-of-ifrs/` |
| IFRS 2 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-2-share-based-payment/` |
| IFRS 3 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-3-business-combinations/` |
| IFRS 5 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-5-non-current-assets-held-for-sale-and-discontinued-operations/` |
| IFRS 6 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-6-exploration-for-and-evaluation-of-mineral-resources/` |
| IFRS 7 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-7-financial-instruments-disclosures/` |
| IFRS 8 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-8-operating-segments/` |
| IFRS 9 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/` |
| IFRS 10 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-10-consolidated-financial-statements/` |
| IFRS 11 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-11-joint-arrangements/` |
| IFRS 12 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-12-disclosure-of-interests-in-other-entities/` |
| IFRS 13 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-13-fair-value-measurement/` |
| IFRS 14 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-14-regulatory-deferral-accounts/` |
| IFRS 15 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-15-revenue-from-contracts-with-customers/` |
| IFRS 16 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-16-leases/` |
| IFRS 17 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-17-insurance-contracts/` |
| IFRS 18 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-18-presentation-and-disclosure-in-financial-statements/` |
| IFRS 19 | `https://www.ifrs.org/issued-standards/list-of-standards/ifrs-19-subsidiaries-without-public-accountability-disclosures/` |

> IAS 准则同理，URL 命名：`https://www.ifrs.org/issued-standards/list-of-standards/ias-{编号}-{英文名小写连字符}/`
>
> 部分 IFRS 标准（如 IFRS 4）已被取代，网页可能重定向。建议从 [List of Standards](https://www.ifrs.org/issued-standards/list-of-standards/) 入口逐个确认。

---

## 7. 待完善事项

- [x] Browser MCP 批量自动化下载（fetch + Blob 弹窗方式，需用户逐个点击保存）
- [ ] HTML → MD 转换后自动添加 `url` 到 frontmatter
- [ ] 转换脚本适配 IAS 准则的 TOC ID 差异（`IFRS03_TOC` → `IAS01_TOC` 等，已通过动态匹配解决）
- [ ] 批量质量校验脚本（对比关键段落完整性）
- [x] 段落号提取（`_pending_paranum` / `_flush` 拼接）

---

## 8. 常见问题

**Q: 转换后某些段落丢失了？**
检查是否被 `div.note.edu` 包裹。查看原始 HTML 中该段落的父级 div 的 class 属性。

**Q: 脚注引用格式不对？**
应显示为 `[E1]`、`[E2,][E3]` 等。如果显示为纯文本如 `E1,`，说明 `fn_eduref` 处理有遗漏。

**Q: 标题层级不对？**
检查 HTML 中该标题的标签级别。IFRS 标准使用 h1–h5，脚本直接映射为 `#`–`#####`。

**Q: TOC 没有被跳过？**
检查 `_skip_element` 函数中的 ID 匹配。不同 IAS 准则的 TOC ID 不同（如 `IAS01_TOC`），需要在 `ifrs_html_to_md.py` 的 `_skip_element` 方法中补充对应的 ID。

**Q: 段落号没有出现在输出中？**
检查 `_pending_paranum` 变量是否正确传递。段落号在 `<div class="paranum"><p>N</p></div>` 中捕获，在下一个 `<p>` 段落的 `_flush()` 时自动拼接为 `**N.** `。

**Q: 转换速度慢？**
IFRS 3（~1700行HTML）转换耗时约 22 秒，属正常范围。
