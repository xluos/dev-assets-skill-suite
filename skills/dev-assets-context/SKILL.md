---
name: dev-assets-context
description: Use when starting work in any Git repository conversation on an existing branch, before code edits, before repo exploration, or before clarifying implementation details, when Codex should first recover the current branch's saved development memory and identify missing source materials.
---

# Dev Assets Context

把当前分支目录下已经沉淀的开发记忆读出来，作为默认上下文入口。

**Announce at start:** 用一句简短的话说明将先恢复当前分支记忆。

**Core principle:** 先恢复分支记忆，再进入编码、排查或补问细节。

## Workflow

### Step 1: Locate branch assets

先确认当前目录位于 Git 仓库内，然后运行：

```bash
python3 /absolute/path/to/dev-assets-context/scripts/dev_asset_context.py show --repo <repo-path>
```

如果资产目录不存在，立即切换到 `dev-assets-setup`，不要直接开始编码。

### Step 2: Optionally refresh lightweight Git-derived navigation

在继续工作前，可以轻量刷新 `development.md` 的 Git 自动区和 focus areas：

```bash
python3 /absolute/path/to/dev-assets-context/scripts/dev_asset_context.py sync --repo <repo-path>
```

### Step 3: Read in layers, not all at once

默认先读：

- `overview.md`
- `development.md`

如果还不够，再读：

- `context.md`

只有当你确实需要原始事实时，才去读：

- `sources.md` 中列出的源文档、链接或 Git 历史

### Step 4: Call out gaps before acting

如果文件仍是模板占位或明显缺失：

- 先指出缺口
- 再决定是否向用户索要资料
- 不要把占位模板当成真实需求事实

## Commands

```bash
python3 /absolute/path/to/dev-assets-context/scripts/dev_asset_context.py show --repo <repo-path>
python3 /absolute/path/to/dev-assets-context/scripts/dev_asset_context.py sync --repo <repo-path>
```

## Reading Strategy

- 不要一上来全量读取整个目录。
- 先读 `overview.md` 和 `development.md`。
- 只在本次任务确实需要时再读 `context.md`。
- 只有需要具体来源时，再按 `sources.md` 回源。

## Always / Never

**Always:**

- 在 Git 仓库内继续已有分支工作时优先使用本 skill
- 在开始代码修改前先刷新一次 `development.md`
- 先读短摘要和工作态，再决定是否补读 context 或 sources
- 发现缺失资产时明确说出来

**Never:**

- 不经读取资产目录就直接声称“我已经理解当前需求”
- 默认把整个 `.dev-assets/<branch>/` 全部灌进上下文
- 把模板占位内容当成真实背景
- 资产目录缺失时跳过 setup 直接开始改代码
