---
name: using-dev-assets
description: >-
  Use when starting any Git-repository development conversation, before code edits,
  before repository exploration, before clarifying implementation details, or
  whenever the agent may need to silently recover, update, or sync the current
  branch's development memory.
---

# Using Dev Assets

这是开发资产套件的总入口 skill。它不直接沉淀资料，而是决定在当前对话起点，或在会话进行中出现阶段性沉淀时，是否应该先走 `dev-assets-context`、`dev-assets-setup`、`dev-assets-update` 或 `dev-assets-sync`。

**Announce at start:** 用一句简短的话说明将先判断当前对话是否需要进入 dev-assets 套件。

**Core principle:** 在 Git 仓库里继续需求开发时，优先维护“当前有效记忆”，而不是让 agent 完全依赖聊天历史。

## The Rule

如果当前对话已经进入 Git 仓库中的持续开发语境，或者已经出现需要恢复、修正、沉淀当前记忆的信号，就优先调用对应的 dev-assets skill。

## Routing

### Route to `dev-assets-context`

当用户是在已有分支上继续开发、排查、解释、修改时：

- 先恢复当前分支记忆
- 先读 `overview.md` / `development.md`
- 还不够时再读 `context.md`
- 只有需要原始事实时再看 `sources.md`

### Route to `dev-assets-setup`

当当前分支还没有资产目录，或者用户明确表示这是新需求/新分支第一次开始时：

- 初始化 `.dev-assets/<branch>/`
- 先搭好当前记忆和源资料入口，而不是复制完整文档

### Route to `dev-assets-sync`

当当前对话已经到达明确的检查点，并且本轮产生了需要跨会话保留的稳定记忆时：

把它视为“提交时沉淀本次关键信息”的检查点，而不是生成流水账或重建整个分支状态的检查点。

### Route to `dev-assets-update`

当当前记忆需要被补充或纠正，并且更新后的内容会明显改善后续恢复上下文或回源效率时，路由到 `dev-assets-update`：

进入后：

- 定位当前分支资产目录
- 选择最合适的目标文件和 section
- 把本轮新信息和相关会话上下文整理后重写进去

## Always / Never

**Always:**

- 在 Git 仓库开发对话开头先做一次路由判断
- 把“继续开发”“提交检查点”和“阶段性里程碑”都视为高优先级触发场景
- 优先维护当前有效记忆
- 在当前记忆已经落后于新理解时，主动判断是否该隐式触发 `update`

**Never:**

- 明知道在继续分支开发，却跳过 dev-assets 判断
- 把提交相关对话直接当成纯 Git 操作
- 在资产目录缺失时直接开始实现
- 明知道这一段内容后续会复用，却因为用户没开口就不更新记忆
- 因为低价值波动或一次性澄清就频繁触发 `update`
