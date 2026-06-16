---
tags: [cursor, codex, 协作]
date: "2026-05-30"
---

# 🤝 Codex ↔ Cursor 协作区

本目录是 **Codex** 与 **Cursor** 之间的"消息板"——双方通过这里的笔记进行任务交接和信息同步。

## 使用方式

### Codex → Cursor（委托任务）
创建一个笔记，用 frontmatter 标明 	o: cursor，内容描述需要 Cursor 协助的事项。
完成后 Cursor 将 status 改为 done 并补充回复。

### Cursor → Codex（委托任务）
同上，frontmatter 标明 	o: codex，由 Codex 执行并更新状态。

### 共享上下文
一些需要双方共同知晓的信息（如项目规范、命名约定、当前进度）放在本目录下，双方随时查阅。

## 笔记模板

\\\yaml
---
to: cursor | codex
status: pending | in_progress | done
priority: low | medium | high
date: "YYYY-MM-DD"
tags: [task]
---
\\\

## 当前任务

- [x] IFRS 缺失准则补齐（6 个）— 2026-05-30 完成
- [x] 核心 IAS 准则新建（6 个）— 2026-05-30 完成
- [x] 次要 IAS 准则（10 个）— 2026-05-30 完成
- [x] Codex 中文提炼格式统一 — 2026-05-30 Cursor 检查并修复
- [ ] 原文行内中文注释 — 待 Codex 继续（见 [[Codex中文注释工作检查]]）
- [x] 16 个 IAS 中文提炼 — 2026-05-30 Cursor 完成
- [x] `.scripts` / `.tmp` 点文件夹隐藏 — 2026-05-30
- [x] Cursor 工作日志 — [[../.logs/cursor/2026-05-30]]（`.logs/cursor/`）
