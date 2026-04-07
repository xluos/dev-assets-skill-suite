---
name: dev-asset-sync
description: Sync the current branch's development asset directory around Git commit activity. Use when the user mentions commit, 提交, commit message, stage, or preparing to commit, and Codex should refresh changed files, update development notes, and record the latest commit into the branch asset directory.
---

# Dev Asset Sync

在用户提到“提交”相关行为时，刷新当前分支开发资产，并把提交记录沉淀下来。

## Trigger Intent

典型触发语义：

- 帮我提交
- 准备 commit
- 生成 commit message
- 把这些改动提交掉
- 提交前同步一下

## Workflow

1. 确认当前目录位于 Git 仓库内。
2. 运行 `sync-working-tree` 更新 `development.md` 的自动区。
3. 如果已经存在新提交，运行 `record-head` 把最新 commit 写入 `commits.md`。
4. 如果本轮开发沉淀出了重要结论，同时把结论写入 `decision-log.md`。

## Commands

```bash
python3 /absolute/path/to/dev-asset-sync/scripts/dev_asset_sync.py sync-working-tree --repo <repo-path>
python3 /absolute/path/to/dev-asset-sync/scripts/dev_asset_sync.py record-head --repo <repo-path>
```

## Output Rules

- 不要只同步 Git 文件列表。
- 至少更新：
  - `development.md`
  - `manifest.json`
  - `commits.md`（如存在新提交）
- 如果没有新提交，明确说明“只完成工作区同步，未新增提交记录”。
