---
tags: [us-gaap, asc, 操作指引, cursor, 脚本]
date: "2026-06-24"
---

# ASC HTML 提取与转换指引

本文档记录从 FASB ASC 网站提取 HTML 并转换为结构化 Markdown 的完整流程。  
**核心改进**：直接用 `innerHTML` 提取 → `asc_html_to_md.py` 解析，生成**含段落号、表格、有序列表**的 Markdown，质量远超旧版 `innerText` 导出。

## 一、工具链

| 脚本 / 工具 | 位置 | 用途 |
|------------|------|------|
| `asc_html_to_md.py` | `03 - 知识库/US GAAP/` | 核心转换：HTML → Markdown（保留 frontmatter 和中文提炼） |
| `batch_asc_convert.py` | `03 - 知识库/US GAAP/` | 批量转换脚本：遍历 `.tmp/` 所有 HTML → `asc{N}_new.md` |
| Cursor Browser MCP | 内置 | 浏览器自动化：导航 → CDP 提取 `innerHTML` |
| `.tmp/*.html` | `.tmp/` | HTML 原始备份（131 个，勿删） |

## 二、完整工作流程

### 阶段 1：浏览器提取 HTML（主要耗时）

对每个 ASC Topic 编号 `{N}`：

1. **导航**：`browser_navigate` → `https://asc.fasb.org/{N}/showallinonepage`
2. **等待 SPA 渲染**：Angular SPA 需 6–12 秒加载，用 `Shell` 命令 `sleep 8` 等待
3. **探测加载**：`browser_cdp` → `Runtime.evaluate`：
   ```js
   (function(){var el=document.querySelector('div.mb-2.ng-star-inserted');return el?el.innerHTML.length:0})()
   ```
   若返回 0，再等 5 秒重试
4. **提取**：`browser_cdp` → `Runtime.evaluate`：
   ```js
   (function(){var el=document.querySelector('div.mb-2.ng-star-inserted');return el.innerHTML})()
   ```
   CDP 自动将 >25KB 结果保存到 `~/.cursor/browser-logs/cdp-response-*.json`

### 阶段 2：从 CDP 日志提取 HTML

```powershell
python .tmp/batch_extract.py
```

该脚本扫描 `cdp-response-*.json`，提取 `innerHTML` 并包装为完整 HTML 文档保存到 `.tmp/asc{N}.html`。  
**注意**：此脚本需手动编写或已内置在 Cursor 会话中。

### 阶段 3：批量转换 HTML → Markdown

```powershell
python "03 - 知识库/US GAAP/batch_asc_convert.py"
```

此脚本：
- 遍历 `.tmp/asc*.html`
- 对每个 HTML 调用 `asc_html_to_md.py` 转换
- 自动合并对应旧 MD 的 `frontmatter` 和 `## 📌 中文提炼`
- 输出到 `.tmp/asc{N}_new.md`

### 阶段 4：替换旧文件

```powershell
python .tmp/replace_asc_md.py
```

从 `.tmp/` 读取 `asc{N}_new.md`，替换 `ASC准则/` 下的旧 `.md`，旧文件备份为 `.md.bak`。

### 阶段 5：清理

- 删除 `ASC准则/` 下所有 `.md.bak` 备份文件
- 删除 `.tmp/` 下所有 `.md` / `.py` / `.json` / `.js` 临时文件
- **保留** `.tmp/*.html` 作为原始数据备份

## 三、Cloudflare 应对

FASB 网站有 Cloudflare 保护，连续大量请求会触发验证：

1. **现象**：页面标题为 "Just a moment..."，出现安全验证
2. **处理**：
   - 先导航回 `https://asc.fasb.org/Home` 重建会话
   - 再导航到目标 Topic
   - 若持续被拦，请**手动在内置 Browser Tab 完成验证**
3. **策略**：每 10–15 个 Topic 暂停一次，回 Home 页刷新会话

## 四、HTML 解析器说明

`asc_html_to_md.py` 解析以下 HTML 结构：

| HTML 元素 | Markdown 输出 |
|-----------|--------------|
| `div.paragraphId` | `**{ID}** {text}` |
| `h1`, `h2` | `##`, `###` |
| `h4` | `#####` |
| `article.dita-content` / `div.p` | 段落正文 |
| `ol.ol-norm > li` | `1.`, `2.`, … |
| `table.topic-table` | Markdown 表格 |
| `div.info-box` | `> **General Note:** {text}` |
| `strong`, `em`, `sup` | `**bold**`, `*italic*`, `^superscript^` |

## 五、结果统计（2026-06-24）

| 指标 | 数值 |
|------|------|
| 有效 ASC Topic | 88 |
| HTML 提取完成 | 88 / 88 ✅ |
| Markdown 转换完成 | 88 / 88 ✅ |
| HTML 备份文件 | `.tmp/` 下 131 个（含 IAS/IFRS） |
| 转化后 MD 存放 | `ASC准则/` 下 88 个 |

## 六、相关链接

- [[ASC Codification 导出指引]] — 旧版 `innerText` 导出方式（已弃用，仅供参考）
- [[US GAAP 知识库总览]]
- 转换脚本：[asc_html_to_md.py](asc_html_to_md.py) / [batch_asc_convert.py](batch_asc_convert.py)
