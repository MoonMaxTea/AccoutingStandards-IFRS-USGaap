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
| `02 - 项目/` | 实务 Q&A 项目笔记（[[02 - 项目/项目编写说明]]） |
| `00 - 入门/` | Obsidian 与 Cursor 使用说明 |
| `04 - Cursor协作/` | Agent 任务交接（可选） |
| `.scripts/` | 知识库维护脚本（增量更新准则时用） |
| `.cursor/skills/` | Cursor Agent 编写准则笔记的 Skill |

## 如何使用

1. 在 Cursor 中打开本仓库作为工作区
2. 提出 IFRS 或 US GAAP 问题，要求 Agent **仅查知识库**并写成项目笔记
3. Agent 会自动加载 `.cursor/skills/writing-accounting-standards-notes/SKILL.md`

## 知识库规模

- IFRS 准则：19 篇 + IAS 23 篇（含中文提炼）
- US GAAP：88 个 ASC Topic（Codification 英文原文）
- 索引：[[03 - 知识库/IFRS/IFRS 知识库总览]]、[[03 - 知识库/US GAAP/US GAAP 知识库总览]]

## 维护

- 更新 ASC：见 [[03 - 知识库/US GAAP/ASC Codification 导出指引]]
- 更新 IFRS/IAS：见 `.scripts/README.md`
- 工作指令：[[AGENTS.md]]
