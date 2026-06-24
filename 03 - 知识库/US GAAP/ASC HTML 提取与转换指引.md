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
| `extract_cdp.py` / `save_cdp.py` / `batch_extract.py` | `.tmp/` | CDP 日志 → HTML 提取脚本（按需创建） |
| `quality_check_v2.py` | `.tmp/` | 质量检查：检测 SubTopic 覆盖度、段落完整性 |
| Cursor Browser MCP | 内置 | 浏览器自动化：导航 → CDP 提取 `outerHTML` |
| `.tmp/*.html` | `.tmp/` | HTML 原始备份（87 个，勿删） |

### 关键注意事项

- **CSS 选择器**：用 `.main-content-container` 提取 `outerHTML`（全量），**不要**用 `div.mb-2.ng-star-inserted`（仅信息框）。
- **`returnByValue`**：设为 `false`（CDP 自动将大结果保存为日志文件）。
- **并行限制**：见 [[#三、Cloudflare 应对]]。

## 二、推荐工作流：子代理提取 + 主代理复核（2026-06-24 实战验证）

> **核心策略**：1 个 `browser-use` 子代理串行提取全部 Topic → 主代理批量 CDP 日志解析 → HTML→MD 转换 → SubTopic 质量复核 → 增量替换。**全流程约 40–60 分钟**。

### 阶段 1：子代理批量提取（并行进行，不阻塞主代理）

启动 **单个** `browser-use` 子代理，传入完整 Topic 列表（最多 35 个），由它**串行** navigate → wait → CDP evaluate。

**SubAgent Prompt 模板**：

```
You are extracting HTML from FASB ASC Codification website.

CRITICAL: Use the EXISTING browser tab. Do NOT create a new tab.
List tabs first, use its viewId.

For each topic {N} in [list all topic numbers with commas]:

1. browser_navigate → https://asc.fasb.org/{N}/showallinonepage
2. Shell sleep 25  (SPA render wait)
3. browser_cdp → Runtime.evaluate, returnByValue: true:
   (() => { const mc = document.querySelector('.main-content-container');
    return JSON.stringify({title: document.title, mcLen: mc ? mc.outerHTML.length : 0}); })()
   → If mcLen == 0 or title lacks "Combine Sections", wait 10s and retry
4. browser_cdp → Runtime.evaluate, returnByValue: false:
   (() => { const mc = document.querySelector('.main-content-container');
    return mc ? mc.outerHTML : 'ERROR'; })()

After ALL topics extracted, run batch save Python script (attached).
```

**关键参数**：
- `run_in_background: true` — 不阻塞主代理
- `subagent_type: browser-use` — 使用内置浏览器标签页（共享主会话）
- **禁止**：同时启动多个 browser-use 子代理（见 [[#三、Cloudflare 应对]]）

### 阶段 2：主代理批量 CDP 日志解析

子代理完成后，所有 `outerHTML` 已保存为 CDP 日志（`~/.cursor/browser-logs/cdp-response-Runtime.evaluate-*.json`）。

**取最优版**：CDP 日志可能有同一 Topic 的多个版本（部分渲染 vs 完全渲染），需选每个 Topic 的最大版本：

```powershell
python .tmp/save_best.py
```

此脚本：
- 扫描所有 CDP 日志
- 对每个 Topic 取 `paragraphId` 数最多且 `outerHTML` 最大的版本
- 包装为完整 `<DOCTYPE html>`，保存到 `.tmp/asc{N}.html` + `asc{N}_full.html`
- 输出每个 Topic 的大小和段落数摘要

> `save_best.py` 在当前会话中按需编写，核心逻辑：遍历 CDP JSON → 取 `result.result.value` → 正则匹配 `{N}-{YY}-{ZZ}-{NNN}` 识别 Topic → 保留最大版。

### 阶段 3：批量转换 HTML → Markdown

```powershell
python .tmp/batch_convert_all.py
```

脚本遍历 `.tmp/asc{N}.html`，调用 `asc_html_to_md.py` 转换，仅当新 MD ≥ 旧 MD 95% 大小时替换（防止退化）。输出每 Topic 的 SubTopic 段落分布。

**转换命令**：
```
asc_html_to_md.py <html_file> <existing_md> <output_md>
```

### 阶段 4：SubTopic 质量复核

**4.1 快速扫描** — 识别仅有 SubTopic 10 的文件：

```powershell
python .tmp/scan_s_headers.py
```

逻辑：扫描 Markdown 中 `## S{YY}` 章节标记 vs 段落号 `{N}-{YY}-ZZ-NNN` 前缀。若文件有 `S20`/`S30` 等多章节但段落号全是 `{N}-10-XX-XX` → 标记为可疑。

**4.2 浏览器核实** — 对可疑文件逐个在浏览器中确认：

```js
// CDP 探测
(() => { const txt = document.body.innerText || ''; const st = {};
  for (let i = 10; i <= 100; i += 5) {
    const re = new RegExp('{N}-' + String(i).padStart(2,'0') + '-', 'g');
    const m = txt.match(re); if (m && m.length > 0) st[i] = m.length;
  }
  return JSON.stringify({title: document.title, st: st}); })()
```

若浏览器显示多 SubTopic 但现有 HTML 中缺失 → 该 Topic 的旧 HTML 不完整，需从浏览器重新提取（重复阶段 1 单 Topic 流程）。

**4.3 增量修复** — 对确认缺失的 Topic，逐 topic 重新提取→转换→替换。

### 阶段 5：清理

```powershell
# 删除中间产物
python -c "import os, glob, shutil; [os.remove(f) for f in glob.glob('.tmp/*.md')]"
python -c "import os, glob; [os.remove(f) for f in glob.glob('.tmp/*_new.md')]"
python -c "import os, glob; [os.remove(f) for f in glob.glob('.tmp/*.bak')]"

# 删除 CDP 日志（HTML 已保存到 .tmp/）
python -c "import os, glob; [os.remove(f) for f in glob.glob(os.path.expanduser('~/.cursor/browser-logs/cdp-response-*.json'))]"
```

**保留项**：
- `.tmp/*.html` — HTML 原始数据备份（唯一真实来源，勿删）
- `.tmp/save_cdp.py` / `save_best.py` — 可复用工具脚本
- `03 - 知识库/US GAAP/asc_html_to_md.py` — 核心转换器

## 三、Cloudflare 应对

FASB 网站有 Cloudflare 保护，连续大量请求会触发验证：

1. **现象**：页面标题为 "Just a moment..."，出现安全验证
2. **处理**：
   - 先导航回 `https://asc.fasb.org/Home` 重建会话
   - 待首页加载后（10–15 秒），再导航到目标 Topic
   - 若持续被拦，请**手动在内置 Browser Tab 完成验证**（点击 checkbox）
3. **策略**：每 10–15 个 Topic 暂停一次，回 Home 页刷新会话

### ⚠️ 多 SubAgent 并行限制（重要）

**禁止使用多个 `browser-use` 子代理并行抓取 FASB 网站**。原因：

- 每个子代理拥有**独立的浏览器上下文**（独立 cookies / session / Cloudflare 令牌），彼此不共享登录态。
- 多个独立浏览器实例同时访问 `asc.fasb.org` 会触发 Cloudflare **速率限制**，迅速导致所有子代理被重定向到登录页或弹出 reCAPTCHA 验证。
- FASB 网站仅允许**单一浏览器会话**稳定访问；SubAgent 即使建立了会话，后续请求也会因频繁切换上下文被拦截。

**推荐方案**：

- **仅使用主 Cursor 浏览器标签页**串行提取：navigate → wait 25s → CDP evaluate → save → 下一个
- 每个 Topic 约 30–40 秒，87 个 Topic 约 1 小时完成
- 串行提取比并行子代理**更可靠**，避免各自撞墙

### 历史经验（2026-06-24 批量提取）

- 5 个子代理并行提取 49 个 Topic，其中 3 个子代理成功（各自建立独立会话且未超限），2 个子代理被登录墙拦截
- 主浏览器标签页串行提取 12 个 Topic 后，因连续导航触发了 Cloudflare 交互式验证（checkbox）
- 子代理 CDP 日志通过批量解析脚本恢复，最终 87/87 全部提取成功

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

## 五、结果统计

### 2026-06-24 第三次全量刷新（子代理提取 + 主代理复核）

| 指标 | 数值 |
|------|------|
| 有效 ASC Topic | 88 |
| 提取方式 | 1 个 browser-use 子代理串行提取 34 个 + 主代理串行提取 12 个 |
| HTML 提取完成 | 87 / 87 ✅（ASC 410 无 HTML 源，保留旧版） |
| Markdown 转换完成 | 87 / 87 ✅ |
| 多 SubTopic 文件 | 41 |
| 总段落数 | 51,426 |
| 关键改善 | ASC 944 (+42x), ASC 815 (+4x), ASC 805 (+3x), ASC 718 (+90%) |
| CDP 日志数 | 201 个（255 MB，清理后保留 HTML 备份） |
| 解析器关键修复 | 自闭合标签堆栈泄漏 + `_in_article` 布尔逻辑 |

### 2026-06-10 初次提取（已覆盖）

| 指标 | 数值 |
|------|------|
| 有效 ASC Topic | 88 |
| HTML 提取完成 | 88 / 88 ✅ |
| 已知缺陷 | 仅提取 SubTopic 10，缺失后续 SubTopic；HTML 在 SPA 未完全渲染时截断 |

## 六、相关链接

- [[ASC Codification 导出指引]] — 旧版 `innerText` 导出方式（已弃用）
- [[US GAAP 知识库总览]]
- 核心转换：[`asc_html_to_md.py`](asc_html_to_md.py)
- 提取脚本：[`.tmp/save_cdp.py`](../../.tmp/save_cdp.py) — 单文件 CDP → HTML
- HTML 备份：[`.tmp/asc*.html`](../../.tmp/) — 87 个 Topic 原始数据
