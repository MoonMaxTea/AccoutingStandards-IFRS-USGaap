---
tags: [cursor, codex, 协作]
date: "2026-06-18"
---

# Cursor 协作区

可选目录：用于 Cursor / Codex 之间的任务交接。日常 Q&A **不依赖**此目录。

## 何时使用

- 需要 Agent 执行跨会话的维护任务（如批量更新准则、格式统一）
- 需要记录待办并跟踪 status

## 笔记模板

```yaml
---
to: cursor | codex
status: pending | in_progress | done
priority: low | medium | high
date: "YYYY-MM-DD"
tags: [task]
---
```

## 相关文档

- 工作指令：[[AGENTS.md]]
- 项目笔记规范：[[02 - 项目/项目编写说明]]
- ASC 更新流程：[[03 - 知识库/US GAAP/ASC Codification 导出指引]]
