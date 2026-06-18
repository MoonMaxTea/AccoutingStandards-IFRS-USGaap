---
tags: [product, desktop, setup]
date: 2026-06-18
---

# 创建 AccoutingStandards-Desktop GitHub 仓库

Cloud Agent 环境无建库权限时，请在本机执行以下步骤。

## 方式 A：从 Git bundle 恢复（推荐）

本目录下的 `AccoutingStandards-Desktop.bundle` 含完整初始 commit（设计说明、130 条 registry 骨架、examples 等）。

```bash
# 1. 在 GitHub 创建空仓库（Web 或 CLI）
gh repo create MoonMaxTea/AccoutingStandards-Desktop --public \
  --description "双准则桌面 App：IFRS/US GAAP 离线准则包 + AI 项目文档（Tauri）"

# 2. 从 bundle 克隆
git clone "/path/to/Vault/04 - Cursor协作/双准则桌面App/AccoutingStandards-Desktop.bundle" \
  AccoutingStandards-Desktop

cd AccoutingStandards-Desktop

# 3. 关联远程并推送
git remote set-url origin https://github.com/MoonMaxTea/AccoutingStandards-Desktop.git
git push -u origin main
```

## 方式 B：仅验证 bundle 内容

```bash
git clone AccoutingStandards-Desktop.bundle -b main /tmp/desktop-check
ls /tmp/desktop-check
# 应含：docs/DESIGN.md, standards-registry.yaml, README.md, ...
```

## 仓库初始内容

| 路径 | 说明 |
|------|------|
| `docs/DESIGN.md` | 完整设计说明 |
| `standards-registry.yaml` | 130 条准则骨架（`official_url` 待人工核验） |
| `examples/` | manifest / registry 示例 |
| `updates/manifest.json` | 更新检查占位 |
| `tools/pack-builder/` | Phase 0 待实现 |

## 推送完成后

- 在 Vault `README.md` 可增加 Desktop 仓库链接（可选）
- 删除本目录 `AccoutingStandards-Desktop.bundle`（可选，减小 Vault 体积）

## 相关

- Vault 内容源：https://github.com/MoonMaxTea/AccoutingStandards-IFRS-USGaap
