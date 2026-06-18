---
tags: [vault, readme]
date: 2026-06-18
---

# 双准则会计知识库（IFRS + US GAAP）

本仓库是 Obsidian Vault，用于在 Cursor 中检索准则、分析会计问题并沉淀项目笔记。

## 目录结构

| 目录 | 用途 |
|------|------|
| `03 - 知识库/` | **核心**：IFRS / US GAAP 准则全文（唯一允许的准则来源） |
| `02 - 项目/` | 实务 Q&A 项目笔记（[[02 - 项目/项目编写说明\|编写说明]] · [[02 - 项目/项目索引\|项目索引]]） |
| `00 - 入门/` | Obsidian 使用说明 |
| `04 - Cursor协作/` | Agent 任务交接（可选） |
| `.scripts/` | 知识库维护脚本 |
| `.cursor/skills/` | Cursor Agent 编写准则笔记的 Skill |

### 项目笔记子目录

| 子目录 | type | 说明 |
|--------|------|------|
| `IFRS项目/` | A-概念梳理 / B-实务决策 | 单一 IFRS 问题 |
| `USGAAP项目/` | A-概念梳理 / B-实务决策 | 单一 US GAAP 问题 |
| `双准则对比/` | C-双准则对比 | IFRS vs US GAAP 对比 |

## 如何使用

1. 在 Cursor 中打开本仓库作为工作区
2. 提出 IFRS 或 US GAAP 问题，说「**按项目编写说明写**」— Agent **仅查知识库**并按 `02 - 项目/项目编写说明.md` 生成笔记
3. Agent 自动加载 `.cursor/skills/writing-accounting-standards-notes/SKILL.md`

**示例提问**：

> 「IFRS 与 US GAAP 下 DTA 处理有何不同？按项目编写说明写。」

## 项目笔记规范（摘要）

- **TL;DR** 三行摘要 + 结构化「问题」节
- **A-概念梳理 / B-实务决策 / C-双准则对比** 三种 type（字母后附中文）
- 准则引用仅限知识库；引用后附提炼表
- 结论分「准则结论」与「操作结论」
- 详见 [[02 - 项目/项目编写说明]]

## 知识库规模

- IFRS 准则：19 篇 + IAS 23 篇（含中文提炼）
- US GAAP：88 个 ASC Topic（Codification 英文原文）
- 索引：[[03 - 知识库/IFRS/IFRS 知识库总览]]、[[03 - 知识库/US GAAP/US GAAP 知识库总览]]

## 维护

- 更新 ASC：[[03 - 知识库/US GAAP/ASC Codification 导出指引]]
- 更新 IFRS/IAS：`.scripts/README.md`
- 工作指令：[[AGENTS.md]]
- **桌面 App**（准则离线阅读 + AI 写项目文档）：[AccoutingStandards-Desktop](https://github.com/MoonMaxTea/AccoutingStandards-Desktop) · 本地推送说明 [[04 - Cursor协作/双准则桌面App/SETUP]]
