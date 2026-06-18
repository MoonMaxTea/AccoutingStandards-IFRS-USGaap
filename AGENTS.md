# AGENTS.md - Codex 工作指令

## 语言规则
- 所有思考和回复必须使用**中文**，包括代码注释、技术分析、计划说明等。

## Vault 说明
- 这是一个 Obsidian Vault，作为 **IFRS + US GAAP 双准则知识库**，主要在 Cursor 中用于 Q&A
- 所有笔记为 Markdown 格式
- 修改 `.obsidian/` 下配置时需谨慎，避免破坏 Obsidian 正常工作
- 创建笔记时默认使用 frontmatter（YAML 头部）标注 tags 和日期
- 自动化脚本在 `.scripts/`（见 `.scripts/README.md`）；PDF 缓存于 `.tmp/`（以 `.` 开头，Obsidian 中默认隐藏）
- **Cursor 工作日志**仅写入 `.logs/cursor/`；可读取 `.logs/codex/`，勿修改 Codex 日志

## 联动原则
- 用户可能同时在 Obsidian 和 Codex 中操作同一份文件
- 写入文件时遵循已有的目录结构和命名风格
- 优先使用 Obsidian 双向链接语法 `[[笔记名]]` 关联笔记

## 准则项目笔记
- IFRS / US GAAP 问题写成项目笔记时，**必须先加载** Skill：`.cursor/skills/writing-accounting-standards-notes/SKILL.md`
- 完整编写规范见 `02 - 项目/项目编写说明.md`
- 准则依据**仅限** `03 - 知识库/` 目录
