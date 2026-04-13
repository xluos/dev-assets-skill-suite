---
name: dev-assets-sync
description: Use when the current conversation reaches a commit-related checkpoint or another clear persistence checkpoint where this round's progress, risks, next steps, and decisions should now be snapshotted for the next session. Use this skill for commit-time, handoff-ready, lifecycle-hook, or milestone snapshots, not for correcting existing memory or persisting one-off clarifications. Repo-shared source updates here mean shared documents and links, not branch-only hot paths.
---

# Dev Assets Sync

在提交相关检查点，或在当前对话已经形成需要跨会话保留的稳定结论时，把这次会话结束后仍然有价值的信息同步到当前 branch 记忆，并顺带刷新 repo 共享层的轻量元信息。

**Announce at start:** 用一句简短的话说明将先沉淀本次检查点留下的关键信息。

## Workflow

### Step 1: Decide whether this moment is worth syncing

只在当前时点已经形成明确的持久化价值时触发 `sync`。

典型信号：

- 刚完成一次提交、准备提交、或刚完成一轮代码/排查检查点
- 当前进展、阻塞、下一步已经清晰到值得 handoff 或跨会话延续
- 阶段性方向已经收敛，适合在这个检查点留一份快照
- 本轮新增了仓库共享层之后还会复用的文档入口、链接或决策结论

单次排查里刚确认 root cause、scope 或某条规则，但这一刻还不是检查点时，不要直接用 `sync`；那类情况要么暂不落盘，要么在确实需要修正现有记忆时改用 `dev-assets-update`。

如果这一刻更像“需要改写某条当前记忆”，优先用 `dev-assets-update`；如果更像“这轮阶段性结果该留个检查点快照”，优先用 `dev-assets-sync`。

### Step 2: Summarize only what this checkpoint should leave behind

优先提炼：

- 当前进展
- 当前阻塞与注意点
- 下一步
- 关键决策与原因
- 本次新增的共享资料入口

这里的“共享资料入口”只指仓库共享层应该复用的文档、链接、外部资料，不包括当前分支后续要看的 hot paths、目录或局部代码入口。

然后运行：

```bash
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py record-session --repo <repo-path> --summary-file <summary.json>
```

### Step 3: Keep branch state and repo metadata separate

`record-session` 的默认落点是：

- 进展 / 风险 / 下一步 / 分支级决策 → branch 文件
- 新增资料入口 → repo `sources.md`
- HEAD / 最近访问分支 → manifest

额外约束：

- 写进 `repo/sources.md` 的必须是 repo 共享资料入口
- branch-only 导航、hot paths、局部代码入口不属于这里的 `sources`

它默认不做这些事：

- 不重建整个 branch memory
- 不把实现流水账写回记忆
- 不把 branch-specific 当前状态写进 repo 共享正文

### Step 4: Lifecycle hooks are the default low-friction path

如果希望不依赖对话里显式触发，就使用仓库提供的生命周期 hook 模板与脚本：

- `SessionStart` 恢复当前 repo+branch 记忆
- `PreCompact` 刷新 working-tree-derived navigation
- `Stop` / `SessionEnd` 只保留轻量 HEAD marker

推荐的 repo-local 落地点：

- Claude: `.claude/settings.local.json`
- Codex: `.codex/hooks.json`

可复用模板：

- Claude: `hooks/hooks.json`
- Codex: `hooks/codex-hooks.json`

## Commands

```bash
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py record-session --repo <repo-path> --summary-file <summary.json>
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py sync-working-tree --repo <repo-path>
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py record-head --repo <repo-path>
```

## Always / Never

**Always:**

- 把提交检查点和阶段性里程碑都视为 `sync` 触发点
- 优先沉淀本次提交留下的关键信息，而不是累积历史
- 明确区分 branch 当前记忆、repo 共享入口、Git 历史

**Never:**

- 把 `sync` 当成 append-only 日志工具
- 把 `sync` 当成全局状态重建工具
- 为了“怕漏”就把所有改动详情抄进记忆
- 把 commit history 当成 dev-assets 的一部分
