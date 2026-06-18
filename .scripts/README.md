# 知识库维护脚本

> 纯 Q&A 场景**不需要**运行这些脚本。仅在增量更新 IFRS/IAS/ASC 准则时使用。

## IFRS / IAS

| 脚本 | 用途 |
|------|------|
| `ifrs_pdf_append.py` | 从 IFRS Foundation PDF 追加全文到已有 IFRS 笔记 |
| `ias_pdf_create.py` | 从 PDF 新建 IAS 笔记 |
| `ias_add_summaries.py` | 为缺中文提炼的 IAS 添加概要 |
| `ifrs_normalize_summary.py` | 统一 frontmatter 与 `## 📌 中文提炼` 结构 |

## US GAAP / ASC（推荐 Browser MCP 导出）

| 脚本 | 用途 |
|------|------|
| `asc_topics.py` | 88 个有效 Topic 注册表 |
| `asc_missing_topics.py` | 列出尚未导出或校验失败的 Topic |
| `asc_import_cdp_json.py` | CDP JSON → Markdown（核心转换） |
| `asc_batch_export_runner.py` | CDP JSON 导入 + 写日志 |
| `asc_import_latest.py` | 从最新 CDP JSON 快速导入指定 Topic |
| `asc_batch_validate.py` | 批量校验已导出 ASC 文件 |
| `asc_browser_export.py` | 辅助：进度统计 |
| `asc_mcp_batch_state.py` | 批量导出状态追踪（`.tmp/asc-export-state.json`） |

完整流程见 [[03 - 知识库/US GAAP/ASC Codification 导出指引]]。

## 已移除的脚本

以下脚本已从仓库删除（废弃或 Q&A 场景不需要）：

- `asc_batch_selenium.py` / `asc_batch_playwright.mjs` — Playwright/Selenium 直连，Cloudflare 拦截
- `asc_codification_scrape.py` / `.mjs` / `asc_probe.mjs` — 同上
- `asc_pdf_create.py` / `asc_print_pdf_import.py` — 旧 PDF/ASU 路线
