---
name: dev-assets-graduate
description: Use when the user explicitly indicates a branch's work is done and should be wrapped up — e.g. "归档"、"分支收尾"、"需求做完了"、"merge 完了清一下"、"这个分支可以归档了"、"把分支知识沉淀一下". This skill harvests cross-branch reusable knowledge from branch memory into the repo-shared layer (after stripping business-specific names), then archives the branch directory under `branches/_archived/`. Do not trigger implicitly — destructive moves require explicit user intent. In no-git working directories this skill refuses, since there are no branches to graduate.
---

# Dev Assets Graduate

把已完成分支的开发记忆做"毕业"处理：

1. **提炼上提**：从 branch 记忆里挑出跨分支可复用的知识（剥离业务名词），写到 repo 共享层
2. **归档**：把 branch 目录搬到 `branches/_archived/<branch>__<date>/`，append `INDEX.md`

这是显式用户动作，不要 implicit 触发——destructive move 需要用户授权。

**Announce at start:** 用一句简短的话说明将先 dump 当前 branch+repo 内容做对比，再让用户确认上提哪些条目。

## Workflow

### Step 1: Pre-flight check

确认这是真的"分支收尾"：

- 当前 branch 已经初始化（`branch_dir` 存在）
- 用户语义上是 "结束这一轮工作"——不是 "checkpoint"（那走 dev-assets-sync）也不是 "改一段错的记忆"（那走 dev-assets-update）
- 如果 git ahead `origin/master..HEAD` 还非空，提示用户："有 N 个 commit 尚未合并，仍要归档吗？"
- 如果是 no-git 模式，直接拒绝

### Step 2: Dry-run harvest

跑：

```bash
python3 /absolute/path/to/dev-assets-graduate/scripts/dev_asset_graduate.py dry-run --repo <repo-path>
```

脚本输出当前 branch 三份文件（`development.md` / `context.md` / `sources.md`）的所有 section 和 repo 共享层三份文件的对应 section，**完整内容**，方便你做对比判断。

### Step 3: Decide what to harvest

按下表把 branch section 上提到 repo section（**剥离当前业务相关命名**）：

| branch 来源 | repo 目标 | 上提原则 |
|---|---|---|
| `context.md` 「关键决策与原因」 | `context.md` 「跨分支通用决策」 | 去掉具体 RPC、字段、业务名；保留约定、规则、原理 |
| `sources.md` 「当前分支优先阅读」中**通用**条目 | `sources.md` 「共享入口」 | 必须是跨分支可复用的文档/链接 |
| `context.md` 「后续继续前要注意」 | `context.md` 「共享注意点」 | 仅挑反复可能复用的工程约定 |
| `development.md` 「阻塞与注意点」 | 视情况 → repo 「共享注意点」 或丢弃 | 只挑跨分支会再次遇到的，**不**上提具体业务卡点 |

**不上提**的内容：当前 commit hash、进度、下一步、具体业务字段名、临时 mock。这些和分支强绑定，归档即弃。

把决定写成 `harvest.json`（schema 见 `references/harvest-schema.md`）。

### Step 4: Apply

```bash
python3 /absolute/path/to/dev-assets-graduate/scripts/dev_asset_graduate.py apply \
  --repo <repo-path> --harvest-file harvest.json
```

脚本会：

1. 按 `harvest.json` 把上提条目写入 repo 共享层（mode=append 追加，mode=replace 覆盖整个 section）
2. 在 branch dir 内生成 `archive_summary.md`：归档时间 / 最终 HEAD / git log 摘要 / harvest 概要
3. `mv branches/<key>/` → `branches/_archived/<key>__<YYYYMMDD>/`
4. append 一行到 `branches/_archived/INDEX.md`

### Step 5: Verify

跑：

```bash
python3 /absolute/path/to/dev-assets-graduate/scripts/dev_asset_graduate.py index --repo <repo-path>
```

确认归档条目已经在 INDEX.md 里。同时建议跑一次 `dev-assets-context` 确认 SessionStart 注入不再带这个分支的内容。

## Always / Never

**Always:**

- 显式触发，绝不 implicit 调用
- dry-run 必跑，让用户看完整对比再决定
- 上提前必须剥离业务名词，repo 共享层是给"任何分支"看的
- 归档前生成 `archive_summary.md` 留快照

**Never:**

- 在 no-git 模式触发（无意义）
- 跳过 dry-run 直接 apply
- 把当前业务的 RPC/字段名照搬到 repo 共享层
- 对未合并、未 ahead 的分支强归档（先和用户确认）

## Commands

```bash
# 看 branch + repo 完整内容对比
python3 /absolute/path/to/dev-assets-graduate/scripts/dev_asset_graduate.py dry-run --repo <repo-path>

# 应用 harvest + 归档
python3 /absolute/path/to/dev-assets-graduate/scripts/dev_asset_graduate.py apply --repo <repo-path> --harvest-file harvest.json

# 列已归档分支
python3 /absolute/path/to/dev-assets-graduate/scripts/dev_asset_graduate.py index --repo <repo-path>
```
