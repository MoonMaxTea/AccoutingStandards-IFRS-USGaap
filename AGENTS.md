# AGENTS.md - Codex 工作指令

## 语言规则
- 所有思考和回复必须使用**中文**，包括代码注释、技术分析、计划说明等。

## Vault 说明
- 这是一个 Obsidian Vault，作为 **IFRS + US GAAP 双准则知识库**，主要在 Cursor 中用于 Q&A
- 所有笔记为 Markdown 格式
- 修改 `.obsidian/` 下配置时需谨慎，避免破坏 Obsidian 正常工作
- 创建笔记时默认使用 frontmatter（YAML 头部）标注 tags、date、type、standards 等
- 自动化脚本在 `.scripts/`（见 `.scripts/README.md`）；PDF 缓存于 `.tmp/`
- **Cursor 工作日志**仅写入 `.logs/cursor/`；可读取 `.logs/codex/`，勿修改 Codex 日志

## 联动原则
- 用户可能同时在 Obsidian 和 Codex 中操作同一份文件
- 写入文件时遵循已有的目录结构和命名风格
- 优先使用 Obsidian 双向链接语法 `[[笔记名]]` 关联笔记

## 准则项目笔记

编写 IFRS / US GAAP 项目笔记时，用户说「**按项目编写说明写**」即按 `02 - 项目/项目编写说明.md`（现行唯一规范）执行：

1. **必须先加载** Skill：`.cursor/skills/writing-accounting-standards-notes/SKILL.md`
2. **完整规范**：`02 - 项目/项目编写说明.md`
3. **项目索引**：新建或更新笔记后同步更新 `02 - 项目/项目索引.md`
4. **准则依据仅限** `03 - 知识库/` 目录

### 笔记类型与目录

| 类型 | 目录 | 说明 |
|------|------|------|
| A 概念梳理 | `02 - 项目/IFRS项目/` 或 `USGAAP项目/` | 定义、分类、处理总览 |
| B 实务决策 | 同上 | 披露、选项、具体操作 |
| C 双准则对比 | `02 - 项目/双准则对比/` | IFRS vs US GAAP |

### 必选要素

- Frontmatter：`type`、`standards`、`status`、`related`
- 文首 **TL;DR**（三行）
- 结论分 **准则结论** / **操作结论**（B 型操作结论必选）
- 引用块后 **提炼表**；区分「知识库原文」与「知识库中文提炼」
