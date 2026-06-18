---
name: writing-accounting-standards-notes
description: Use when the user asks IFRS or US GAAP accounting questions and wants project notes created in this Obsidian vault, including definition, classification, measurement, disclosure, dual-standard comparison, or practical decision analysis based on the workspace knowledge base.
---

# 准则项目笔记编写

## Overview

IFRS / US GAAP 问题 → **结构化项目笔记**，存于 `02 - 项目/`，准则**仅限** `03 - 知识库/`。

**完整规范**：[[02 - 项目/项目编写说明]]（现行唯一规范）| **索引**：[[02 - 项目/项目索引]]

用户说「按项目编写说明写」→ 直接按该文件最新内容执行。

## type 取值（字母-中文）

| type | 含义 | 目录 |
|------|------|------|
| `A-概念梳理` | 定义、分类、处理框架 | `IFRS项目/` 或 `USGAAP项目/` |
| `B-实务决策` | 选项、披露、具体操作 | `IFRS项目/` 或 `USGAAP项目/` |
| `C-双准则对比` | IFRS vs US GAAP | `双准则对比/` |

## Frontmatter（必选）

```yaml
---
tags: [ias12, 递延所得税]
date: YYYY-MM-DD
status: active
type: B-实务决策              # A-概念梳理 | B-实务决策 | C-双准则对比
standards: [IAS 12]
related:
  - "[[适用税率选择及计算]]"
---
```

## 正文必选结构

1. **TL;DR**（三行 blockquote）
2. **问题**（背景 + 决策问题 + 边界可选）
3. **准则原文** + **提炼表**
4. **分析**
5. **结论**：`### 准则结论` + `### 操作结论`（B-实务决策 必选）
6. **相关项目** / **准则索引** / **日志**
7. 更新 **[[02 - 项目/项目索引]]**

## 工作流程

1. 检索知识库 → 确认覆盖
2. 选 type 与目录
3. 按结构撰写
4. 更新项目索引
5. 自检 [[02 - 项目/项目编写说明#九、章节速查清单]]

## Common Mistakes

| 错误 | 正确 |
|------|------|
| `type: B` 无中文 | `type: B-实务决策` |
| 对比文放 IFRS项目 | C-双准则对比 放 `双准则对比/` |
| 无 TL;DR | 标题下必有三行摘要 |

## Red Flags — STOP

- 知识库无准则却引用 → 标注缺失
- 外部准则来源 → 删除
