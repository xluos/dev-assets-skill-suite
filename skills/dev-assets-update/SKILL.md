---
name: dev-assets-update
description: Use when current development memory needs to be corrected or supplemented, whether explicitly requested by the user or implicitly required because the conversation produced new stable understanding or new shared source entry points for the current repository.
---

# Dev Assets Update

把当前对话中已经形成且需要保留的新理解，改写到 branch 或 repo 共享层的开发记忆里，而不是只留在对话中。

**Announce at start:** 用一句简短的话说明将先重写相关 section，而不是继续追加历史。

## Workflow

### Step 1: Locate the current assets

先运行：

```bash
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py show --repo <repo-path>
```

如果 branch 目录不存在，立即切到 `dev-assets-setup`。

### Step 2: Choose the right target

默认落点：

- branch `overview.md`：目标、范围、阶段、约束
- branch `development.md`：进展、阻塞、下一步
- branch `context.md`：why / caveat / workaround / decision
- repo `sources.md`：共享资料入口

如果是显式 repo 共享层更新，使用这些 kind：

- `shared-overview`
- `shared-constraint`
- `shared-context`
- `shared-decision`
- `shared-source`

不确定时先运行：

```bash
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py suggest-target --kind <kind>
```

### Step 3: Rewrite current memory

先基于当前会话和用户新输入整理出当前有效内容，再运行：

```bash
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py write --repo <repo-path> --kind <kind> --summary-file <summary-file> --user-input-file <user-input-file>
```

规则：

- 默认是覆盖式写 section，不是 append
- `summary-file` 放整理后的有效摘要
- `user-input-file` 放用户本次原始补充
- 只有确实需要新 section 时才额外传 `--title`

### Step 4: Refresh manifest metadata

`write` 已经会刷新 branch / repo manifest。只有本轮没有正文改写时，才单独运行：

```bash
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py touch-manifest --repo <repo-path>
```

## Commands

```bash
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py show --repo <repo-path>
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py suggest-target --kind <kind>
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py write --repo <repo-path> --kind <kind> --summary-file <summary-file> --user-input-file <user-input-file>
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py touch-manifest --repo <repo-path>
```

## Always / Never

**Always:**

- 先定位资产目录，再落盘
- 把更新理解成“改写当前记忆”，而不是“再记一段历史”
- 分清 branch 记忆和 repo 共享记忆
- 写完后确认 manifest 已刷新

**Never:**

- 把所有新增信息都堆到一个文件里
- 用“之后再整理”为理由跳过沉淀
- 继续把 `update` 当成 append-only 笔记工具
- 把 branch-specific 当前工作态写进 repo 共享层
