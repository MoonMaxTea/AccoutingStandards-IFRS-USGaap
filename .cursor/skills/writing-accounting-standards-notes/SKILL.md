---
name: writing-accounting-standards-notes
description: Use when the user asks IFRS or US GAAP accounting questions and wants project notes created in this Obsidian vault, including definition, classification, measurement, disclosure, or practical decision analysis based on the workspace knowledge base.
---

# 准则项目笔记编写

## Overview

在本 Vault 中，IFRS / US GAAP 问题应写成**结构化项目笔记**，存于 `02 - 项目/`，准则依据**仅限** `03 - 知识库/`。

**完整规范**：[[02 - 项目/项目编写说明]]

## When to Use

- 用户提出 IFRS / US GAAP 会计处理、披露、分类问题
- 需要从知识库检索准则并写成可复用项目文档
- 用户要求「按项目样式」「做成 md 文档」「仅查知识库」

**When NOT to use**：
- 纯代码、Obsidian 配置、与准则无关的任务
- 知识库外准则原文可用时仍应标注缺失，不得编造

## Quick Reference

| 项目 | 规则 |
|------|------|
| IFRS 路径 | `02 - 项目/IFRS项目/{主题}/` |
| US GAAP 路径 | `02 - 项目/USGAAP项目/{主题}/` |
| 准则来源 | 仅 `03 - 知识库/IFRS/` 或 `03 - 知识库/US GAAP/` |
| 语言 | 中文正文；引用块保留英文原文 |
| 链接 | Obsidian `[[路径\|显示名]]` |

## 笔记类型

| 类型 | 适用 | 必选章节 |
|------|------|---------|
| **A 概念梳理** | 定义、分类、处理总览 | 问题 → 总体框架 → 分节分析 → 对比 → 结论 → 准则索引 → 日志 |
| **B 实务决策** | 披露列示、选项选择、具体操作 | 问题（含决策问题）→ 准则原文 → 决策分析 → 结论（含操作结论）→ 日志 |

**样例**：
- A 型：[[02 - 项目/IFRS项目/合营联营会计处理/合营联营定义与会计处理]]
- B 型：[[02 - 项目/IFRS项目/租赁修改披露/租赁修改披露]]

## 工作流程（必须按序执行）

1. **检索知识库**：在 `03 - 知识库/` Grep 相关准则；先读 `## 📌 中文提炼`，再读对应段落原文
2. **确认覆盖**：知识库缺失 → 笔记标注「知识库暂无」，不引用外部准则
3. **选类型**：概念问题用 A 型；具体决策用 B 型
4. **建文件**：`02 - 项目/{IFRS项目|USGAAP项目}/{主题文件夹}/{主题}.md`
5. **写 Frontmatter**：`tags`（含准则编号）、`date`、`status: active`
6. **引用准则**：使用强制格式（见下）
7. **写结论**：编号列表；B 型加「本公司操作结论」
8. **自检**：对照 [[02 - 项目/项目编写说明#八、章节速查清单]]

## 准则引用格式（强制）

```markdown
> **IFRS 11 Paragraph 7–8（知识库原文）：**
>
> [英文原文]

[[03 - 知识库/IFRS/IFRS准则/IFRS 11 - Joint Arrangements|IFRS 11]]
```

- 必须标注段落号 + `（知识库原文）`
- 引用后附 Wiki 链接
- 可用表格做「原则 | 原文依据 | 提炼」

## Frontmatter 模板

```yaml
---
tags: [ifrs, ifrs11, 合营]
date: YYYY-MM-DD
status: active
---
```

## Common Mistakes

| 错误 | 正确做法 |
|------|---------|
| 引用网络或记忆中的准则原文 | 只引用知识库文件内容 |
| 无「问题」节直接写结论 | 先写背景与决策问题 |
| 大段粘贴知识库全文 | 摘录关键段落 + 表格提炼 |
| 结论模糊 | 编号结论，B 型写操作结论 |
| 文件放错目录 | IFRS → `IFRS项目/`；US GAAP → `USGAAP项目/` |
| 缺少日志 | 文末 `## 日志` 记录日期与变更 |

## Red Flags — STOP

- 知识库找不到准则却写了「依据 IFRS X §Y」→ 停止，标注缺失
- 用户要求「仅查知识库」却用了外部来源 → 删除外部内容
- 没有 Wiki 链接 → 补链接后再完成
