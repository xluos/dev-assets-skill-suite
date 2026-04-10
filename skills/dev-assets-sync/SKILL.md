---
name: dev-assets-sync
description: Use when the current conversation reaches a commit-related checkpoint or another clear persistence checkpoint, and Codex should write only this round's durable memory back into the current branch memory.
---

# Dev Assets Sync

在提交相关检查点，或在当前对话已经形成需要跨会话保留的稳定结论时，把这次会话结束后仍然有价值的信息同步到当前分支开发记忆。

**Announce at start:** 用一句简短的话说明将先沉淀本次检查点留下的关键信息。

**Core principle:** `sync` 的目标不是追加流水账，也不是刷新整个分支状态；它只沉淀“本次提交后仍然需要记住什么”。具体改动历史应优先回 Git。

## Trigger Principle

当对话已经到达一个明确的持久化检查点，并且本轮产生了需要跨会话保留的有效记忆时，触发 `sync`。

## Workflow

### Step 1: Decide whether this moment is worth syncing

只在当前时点已经形成明确的持久化价值时触发 `sync`。判断重点是：

- 这一轮是否已经有稳定结论
- 这些结论是否会在后续继续工作时被复用
- 这些信息是否更适合留在当前记忆，而不是仅存在本轮对话中

### Step 2: Summarize only what this commit should leave behind

不要把“做了什么”整段写进记忆。优先提炼：

- 当前进展
- 当前阻塞与注意点
- 下一步
- 关键决策与原因
- 本次提交新增的 source 入口

然后运行：

```bash
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py record-session --repo <repo-path> --summary-file <summary.json>
```

`summary.json` 推荐字段：

- `title`
- `implementation_notes`
- `risks`
- `next_steps`
- `memory`
- `decisions`
- `sources`

其中：

- `overview_summary` 只有在当前检查点明确改变了分支整体目标、范围或阶段时才传
- `changes` 只是可选兜底字段。若信息已经能从 Git 低成本恢复，不要把它当主要记忆内容。

### Step 3: Do not rebuild the whole branch memory

`record-session` 默认不做这些事：

- 不刷新 `development.md` 的 Git 自动区
- 不刷新 focus areas
- 不重建整个 `context.md`
- 不扫描整个仓库去更新导航信息

这些属于 `dev-assets-context` 的恢复阶段，或者 `sync-working-tree` 这种显式 Git 导航刷新。

如果希望不依赖对话触发，也可以安装 Git hooks：

```bash
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py install-hooks --repo <repo-path> --enable-pre-commit
```

其中：

- `post-commit` 只刷新当前 HEAD 元信息
- `pre-commit`（可选）才会刷新 working-tree-derived navigation
- hook 默认只做同步，不阻塞 commit

### Step 4: Keep commit history in Git

如果需要知道这次具体做了什么，应该去看：

- `git log --oneline <base>..HEAD`
- `git show <sha>`

不要再把 commit history 复制到 `.dev-assets/` 里。

## Commands

```bash
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py record-session --repo <repo-path> --summary-file <summary.json>
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py sync-working-tree --repo <repo-path>
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py record-head --repo <repo-path>
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py install-hooks --repo <repo-path> --enable-pre-commit
```

## Output Rules

- 不要只同步 Git 文件列表。
- 也不要把实现历史继续 append 到记忆文件里。
- 默认只改和“这次提交留下的有效信息”直接相关的 section。
- 只保留跨会话仍有价值的 why / caveat / next-step / risk。
- 需要具体改动时，引导模型去读 Git 历史。

## Always / Never

**Always:**

- 把提交检查点和阶段性里程碑都视为 `sync` 触发点
- 优先沉淀本次提交留下的关键信息，而不是累积历史
- 明确区分“当前记忆”和“Git 历史”

**Never:**

- 把 `sync` 继续当成 append-only 日志工具
- 把 `sync` 当成全局分支状态重建工具
- 为了“怕漏”就把所有改动详情抄进 `.dev-assets/`
- 把 commit history 当成 branch memory 的一部分
