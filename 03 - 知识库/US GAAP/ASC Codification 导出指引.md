---
tags: [us-gaap, asc, 操作指引, cursor, 已弃用]
date: "2026-06-09"
updated: "2026-06-24"
status: deprecated
---

# ASC Codification 导出指引（已弃用）

> ⚠️ **本文档已弃用**。新版流程已迁移至 [[ASC HTML 提取与转换指引]]。  
> 新版使用 `innerHTML` + `asc_html_to_md.py` 解析，生成含段落号、表格、有序列表的 Markdown，质量远超本文档描述的 `innerText` 方式。

本文档记录旧版从 [FASB ASC](https://asc.fasb.org) **现行 Codification** 批量导出 Topic 至 Markdown 的流程。  
**仅作历史参考**，请使用新流程。

## 一、前置条件

1. **Cursor → Settings → 开启 Browser Automation**（内置 Browser Tab）。
2. 在内置 Browser Tab 打开 [asc.fasb.org](https://asc.fasb.org) 并完成 **FASB 账号登录**（需订阅权限）。
3. Vault 根目录：`03 - 知识库/US GAAP/ASC准则/` 为输出目录。
4. Python 3 可用；脚本位于 `.scripts/`。

## 二、标准导出流程（单 Topic）

对每个 Topic 编号 `{num}`（如 606）重复以下步骤：

```
browser_lock
  → browser_navigate  https://asc.fasb.org/{num}/showallinonepage
  → browser_cdp       Runtime.evaluate（等待正文 + 提取 innerText）
  → python 导入脚本   将 CDP JSON 转为 MD
  → 校验段落号
browser_unlock（全部完成后）
```

### 2.1 导航

- **推荐 URL**：`https://asc.fasb.org/{num}/showallinonepage`（Join All Sections 合并页）。
- **禁止**先打开 `https://asc.fasb.org/Home`（易触发 Cloudflare 验证）。
- 导航后若 snapshot 为空，等待 3–8 秒再 CDP 探测。

### 2.2 CDP 提取（`browser_cdp`）

参数示例（`viewId` 为当前 Browser Tab ID）：

```json
{
  "method": "Runtime.evaluate",
  "params": {
    "awaitPromise": true,
    "expression": "(async (n) => { const re = new RegExp(`${n}-\\\\d+-\\\\d{2}-\\\\d+`); for (let i = 0; i < 40; i++) { const t = document.body.innerText || ''; if (t.length > 3000 && re.test(t) && document.title.includes(String(n))) { return t + '\\n' + ' '.repeat(30000); } await new Promise(r => setTimeout(r, 1500)); } throw new Error(document.title + ' len=' + (document.body.innerText||'').length); })(606)",
    "returnByValue": true
  },
  "viewId": "a627a1"
}
```

说明：

- 等待正文出现 **段落号**（见下文校验规则）且 `document.title` 含 Topic 编号。
- 末尾 `padding` 强制大结果写入 `%USERPROFILE%\.cursor\browser-logs\cdp-response-*.json`，避免撑爆对话上下文。
- 小 Topic 可将 `3000` 降为 `2000`；超大 Topic（815、944）CDP 可能需 60s+。

### 2.3 本地导入

```powershell
python .scripts/asc_batch_export_runner.py `
  "C:\Users\WINDOWS\.cursor\browser-logs\cdp-response-Runtime.evaluate-YYYY-MM-DDTHH-MM-SS.json" `
  606
```

成功输出示例：`OK ASC 606 -> ASC 606 - Revenue From Contracts With Customers.md para=606-10-05-1 size=492615`

### 2.4 段落号校验

- 正则：`{num}-\d+-\d{2}-\d+`（如 `606-10-05-1`、`950-350-00-1`）。
- 606 专项抽检：`606-10-05-1` 应存在于文件前部。
- 文件大小一般 **> 3 KB**；过短多为导航失败或空页。

## 三、批量与进度脚本

| 脚本 | 用途 |
|------|------|
| `.scripts/asc_topics.py` | **88 个有效 Topic** 注册表（勿含已废止空号） |
| `.scripts/asc_missing_topics.py` | 列出尚未导出或校验失败的 Topic |
| `.scripts/asc_batch_export_runner.py` | CDP JSON → MD + 写日志 |
| `.scripts/asc_import_cdp_json.py` | 核心转换（trim 侧栏、frontmatter） |
| `.scripts/asc_batch_validate.py` | 批量校验 OK / 缺失 / 异常 |
| `.scripts/asc_browser_export.py` | 辅助：`count` / `missing` |

常用命令：

```powershell
# 进度
python .scripts/asc_missing_topics.py
python .scripts/asc_browser_export.py count

# 全库校验
python .scripts/asc_batch_validate.py

# 日志
type .logs\cursor\asc-export.log
```

## 四、生成 MD 的结构

- 路径：`03 - 知识库/US GAAP/ASC准则/ASC {num} - {English Name}.md`
- Frontmatter 关键字段：
  - `source_type: Codification`
  - `import_method: cursor-ide-browser`
  - `source_url: https://asc.fasb.org/{num}/showallinonepage`
- **不做中文提炼**（除非另行要求）；正文为英文 Codification 原文。

## 五、异常处理（必读）

### 5.1 Cloudflare「Just a moment…」/ checkbox

**现象**：页面标题为 `Just a moment...`，或 snapshot 出现 “Performing security verification”。

**处理**：

1. **暂停自动导航**，通知用户在内置 Browser Tab **手动勾选 checkbox** 并完成验证。
2. 验证通过后，先打开一个**已成功加载过的 Topic**（如 606）确认恢复，再继续批量导出。
3. 连续大量 `browser_navigate` 易再次触发验证；可适当间隔或分批。

> **Agent 必须主动提醒用户操作 checkbox**，不可反复用 Playwright/Selenium 绕过。

### 5.2 URL 正确但正文是其他 Topic（SPA 缓存）

**现象**：

- URL 为 `/862/showallinonepage`，标题/正文却是 **860**；
- URL 为 `/608/showallinonepage`，正文却是 **605/606/610**。

**处理（Double-check 是否存在）**：

1. 看 `document.title` 是否包含目标 `{num}`。
2. 在正文中搜索 `{num}-\d+-\d{2}-\d+` 段落号。
3. 若 **URL 编号 ≠ 标题编号 ≠ 段落号前缀** → 该编号很可能 **不是有效 Topic**，不要强行导入。
4. 从 `.scripts/asc_topics.py` 移除无效编号，并记录原因。

**已确认不存在的编号（勿再导出）**：

| 编号 | 说明 |
|------|------|
| **608** | 无独立 Topic；贡献相关见 **ASC 958**（NFP）等 |
| **862** | 无独立 Topic；债务/权益证券见 **320 / 321 / 323 / 325** |
| **865** | 无独立 Topic；保险见 **944** 等 |

Broad Transactions 官方区段至 **860**；Industry 自 **905** 起。

**缓解 SPA 错位**（仅对**确认存在**的 Topic）：

- 先访问邻近已成功的 Topic，再导航目标；
- 或先打开 `{num}-10-00-1` 段落页，再进 `showallinonepage`；
- 仍错位则 **请用户手动在 Browser Tab 打开正确合并页** 后，Agent 仅做 CDP 提取。

### 5.3 CDP 超时 / 正文过短

- 延长等待轮数，或手动刷新 Browser Tab。
- 若 Topic 确实很小（如 915，~4 KB），降低长度阈值后直接 `document.body.innerText` 提取。

### 5.4 已移除的脚本

以下脚本已从仓库删除，**勿再引用**：

| 脚本 | 原因 |
|------|------|
| `asc_batch_playwright.mjs` | Playwright 直连，Cloudflare 拦截 |
| `asc_batch_selenium.py` | Selenium 直连，同上 |
| `asc_codification_scrape.py` / `.mjs` | 同上 |
| `asc_pdf_create.py` | 旧 PDF/ASU 路线，非现行 Codification |
| `asc_print_pdf_import.py` | 旧 Print-to-PDF 路线 |

## 六、推荐批量策略（Agent）

1. `python .scripts/asc_missing_topics.py` 取缺失列表。
2. `browser_lock` → 按列表逐个 **navigate + cdp + import**。
3. 每 10–15 个 Topic 运行一次 `asc_batch_validate.py`。
4. 遇 Cloudflare → **停止并提醒用户**。
5. 遇 SPA 错位 → **Double-check 是否存在**，不存在则跳过并更新 `asc_topics.py`。
6. 全部完成后更新 [[US GAAP 知识库总览]]，日志写入 `.logs/cursor/asc-export.log`。

## 七、本次导出摘要（2026-06-09）

- 删除旧 PDF/ASU 版 MD，改从 Codification 重导。
- **88 / 88** 有效 Topic 已导出至 `ASC准则/`。
- 剔除无效编号：608、862、865。
- 606 校验：`606-10-05-1` ✅。

## 相关链接

- [[US GAAP 知识库总览]]
- [FASB ASC](https://asc.fasb.org)
- Cursor 工作日志：`.logs/cursor/2026-06-09-asc-codification-export.md`
