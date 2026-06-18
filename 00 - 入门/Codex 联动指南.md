---
tags: [guide, codex]
---

# Codex / Cursor 联动指南

本 Vault 的所有笔记均为 Markdown 文件，**Cursor Agent 可直接读写**。

## 主要用途

| 场景 | 做法 |
|------|------|
| 准则 Q&A | 在 Cursor 提问，Agent 检索 `03 - 知识库/` 并写项目笔记 |
| 浏览准则 | 在 Obsidian 中打开知识库，使用双向链接和搜索 |
| 增量更新准则 | 运行 `.scripts/` 中的维护脚本（见 `.scripts/README.md`） |

## 常用 Cursor 指令示例

> "IFRS 下合营和联营如何定义？仅查知识库，按项目编写说明写。"

> "US GAAP 下 lease modification 如何披露？查 ASC 842 和知识库。"

> "列出 `02 - 项目` 下所有 IFRS 项目笔记。"

## 自动化脚本

`.scripts/` 目录存放知识库维护脚本（Obsidian 中以 `.` 开头默认隐藏）：

- **IFRS/IAS**：PDF 导入、中文提炼格式统一
- **US GAAP/ASC**：Browser MCP 导出后的 JSON → Markdown 转换

纯 Q&A 场景不需要运行脚本。

## 配置文件

- `.obsidian/` — Obsidian 配置（可选，Cursor Q&A 不依赖）
- `.cursor/skills/` — Cursor Agent 编写准则笔记的 Skill
- `AGENTS.md` — Vault 全局工作指令

---

💡 所有笔记均为本地 `.md` 文件，可用任何编辑器打开。
