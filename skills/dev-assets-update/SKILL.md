---
name: dev-assets-update
description: Use when current branch memory needs to be corrected or supplemented, whether explicitly requested by the user or implicitly required because the conversation has produced new stable understanding or new source entry points.
---

# Dev Assets Update

把当前对话中已经形成且需要保留的新理解，结合已有上下文，改写到当前分支的开发记忆里，而不是只留在对话中。

**Announce at start:** 用一句简短的话说明将先重写当前分支记忆中的相关 section。

**Core principle:** `update` 不再把同类信息一直 append 到文档末尾，而是尽量改写对应 section 的当前状态。

## Trigger Principle

当当前记忆已经落后于对话中形成的新理解，或者当前记忆缺少后续工作会依赖的重要入口信息时，触发 `update`。

允许隐式触发，但要满足两个前提：

- 新理解已经足够稳定，适合覆盖旧记忆
- 这次更新会明显改善后续恢复上下文或回源的效率

不要因为局部措辞调整、一次性澄清或低价值往返而触发。

## Workflow

### Step 1: Locate the current branch asset directory

先运行：

```bash
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py show --repo <repo-path>
```

如果资产目录不存在，立即切到 `dev-assets-setup`。

### Step 2: Choose the right target file

按信息类型选择落点：

- 高层摘要、范围、阶段、约束 → `overview.md`
- 当前进展、阻塞、下一步 → `development.md`
- 稍详细但仍然有效的背景、决策、注意点 → `context.md`
- 源文档、链接、回源入口 → `sources.md`

不确定时，先运行：

```bash
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py suggest-target --kind <kind>
```

### Step 3: Summarize the session and the latest user input, then rewrite

先基于：

- 当前会话里已经形成的事实
- 用户这次明确补充的输入
- 你刚刚做出的整理与归纳

提炼出当前有效内容，再运行：

```bash
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py write --repo <repo-path> --kind <kind> --summary-file <summary-file> --user-input-file <user-input-file>
```

规则：

- 默认是覆盖式写 section，不是继续追加同类信息
- `summary-file` 存放你基于当前会话整理后的摘要
- `user-input-file` 存放用户这次原始补充内容
- 只有在你明确需要新增一个独立 section 时，才额外传 `--title`

### Step 4: Refresh manifest metadata

`write` 已经会刷新 `manifest.json`。只有在本轮没有新增正文、只是补更新时间时，才单独运行：

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

## Writing Rules

- 写入时优先整理成“当前有效结论”，不要原样转存口语。
- 需要具体事实时，优先写回源入口，而不是复制正文。
- 如果这次补充会改变整体理解，优先改写 `overview.md`。
- 如果是 why / caveat / workaround / decision，优先改写 `context.md`。

## Always / Never

**Always:**

- 先定位资产目录，再落盘
- 把更新理解成“改写当前记忆”，而不是“再记一段历史”
- 尽量使用固定 section，避免长文件不断膨胀
- 写完后确认 `manifest.json` 已刷新更新时间

**Never:**

- 把所有新增信息都堆到一个文件里
- 用“之后再整理”为理由跳过沉淀
- 继续把 `update` 当成 append-only 笔记工具
- 在资产目录不存在时手工拼一套临时文件
