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

## 二、完整工作流程

### 阶段 1：浏览器提取 HTML（主要耗时）

对每个 ASC Topic 编号 `{N}`：

1. **导航**：`browser_navigate` → `https://asc.fasb.org/{N}/showallinonepage`
2. **等待 SPA 渲染**：Angular SPA 需 10–25 秒加载，用 `time.sleep(25)` 等待
3. **探测加载**：`browser_cdp` → `Runtime.evaluate`：
   ```js
   (() => { const t = document.title; const mc = document.querySelector('.main-content-container'); return JSON.stringify({title: t, mcLen: mc ? mc.outerHTML.length : 0}); })()
   ```
   若 `mcLen` 为 0 或标题不含 `Combine Sections`，再等 10 秒重试
4. **提取**：`browser_cdp` → `Runtime.evaluate`（`returnByValue: false`）：
   ```js
   (() => { const mc = document.querySelector('.main-content-container'); return mc ? mc.outerHTML : 'ERROR'; })()
   ```
   CDP 自动将 >25KB 结果保存到 `~/.cursor/browser-logs/cdp-response-Runtime.evaluate-*.json`
5. **保存**：
   ```powershell
   python .tmp/save_cdp.py {N} cdp-response-Runtime.evaluate-YYYY-MM-DDTHH-MM-SS.json
   ```
   脚本自动从 CDP 日志提取 `outerHTML`，包装为完整 HTML 文档并保存到 `.tmp/asc{N}_full.html` + 替换 `.tmp/asc{N}.html`

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

## 五、结果统计

### 2026-06-24 全量重新提取（第二次 — 修复 SubTopic 缺失）

| 指标 | 数值 |
|------|------|
| 有效 ASC Topic | 88 |
| 本次重新提取 Topic | 41（原仅含 SubTopic 10） |
| HTML 提取完成 | 41 / 41 ✅ |
| Markdown 转换完成 | 41 / 41 ✅ |
| 改善后多 SubTopic 文件 | 39 / 41（vs 此前 23） |
| 文件变更 | 41 files, +~800K / -~200K 行 |
| 提取策略 | 主浏览器串行 + CDP 日志最佳选择 |
| 关键改善示例 | ASC 326: 504KB, ASC 842: 895KB, ASC 310: 685KB |
| 解析器关键修复 | 自闭合标签堆栈泄漏 + `_in_article` 布尔逻辑 |

### 2026-06-10 初次提取（已覆盖）

| 指标 | 数值 |
|------|------|
| 有效 ASC Topic | 88 |
| HTML 提取完成 | 88 / 88 ✅ |
| Markdown 转换完成 | 88 / 88 ✅ |
| 已知缺陷 | 仅提取 SubTopic 10，缺失后续 SubTopic |

## 六、相关链接

- [[ASC Codification 导出指引]] — 旧版 `innerText` 导出方式（已弃用，仅供参考）
- [[US GAAP 知识库总览]]
- 转换脚本：[asc_html_to_md.py](asc_html_to_md.py)
- 质量检查脚本：`.tmp/quality_check_v2.py` — 按 SubTopic 覆盖度 + 段落完整性评分
