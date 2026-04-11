---
name: using-dev-assets
description: >-
  Use when starting any Git-repository development conversation, before code edits,
  before repository exploration, before clarifying implementation details, or
  whenever the agent may need to recover, update, or sync repo+branch development memory.
---

# Using Dev Assets

这是开发资产套件的总入口 skill。它不直接沉淀资料，而是决定在当前对话起点或会话进行中，是否应该先走 `dev-assets-context`、`dev-assets-setup`、`dev-assets-update` 或 `dev-assets-sync`。

**Announce at start:** 用一句简短的话说明将先判断当前对话是否需要进入 dev-assets 套件。

## Routing

### Route to `dev-assets-context`

当用户是在已有分支上继续开发、排查、解释、修改时：

- 先恢复当前 branch 记忆
- 还不够时再看 repo 共享层
- 只有需要原始事实时再看 branch / repo `sources.md`

### Route to `dev-assets-setup`

当当前仓库还没有当前 branch 的资产目录，或者用户明确表示这是新需求 / 新分支第一次开始时：

- 初始化用户目录下的 repo+branch 存储
- 先搭好当前记忆和共享资料入口，而不是复制完整文档

### Route to `dev-assets-sync`

当当前对话已经到达明确的检查点，并且本轮产生了需要跨会话保留的稳定记忆时：

- 把它视为“沉淀本次检查点留下的关键信息”的时刻
- 不是生成流水账，也不是重建整个状态

### Route to `dev-assets-update`

当当前记忆需要被补充或纠正，并且更新后的内容会明显改善后续恢复上下文或回源效率时：

- 定位 repo + branch 资产目录
- 选择最合适的目标文件和 section
- 把本轮新信息和相关会话上下文整理后重写进去

## Always / Never

**Always:**

- 在 Git 仓库开发对话开头先做一次路由判断
- 把“继续开发”“提交检查点”和“阶段性里程碑”都视为高优先级触发场景
- 优先维护当前 branch 的有效记忆
- 在新理解会影响后续恢复时，主动判断是否该隐式触发 `update`

**Never:**

- 明知道在继续分支开发，却跳过 dev-assets 判断
- 把 repo 共享层当成 branch 当前工作态的替代品
- 在 branch 资产缺失时直接开始实现
- 因为低价值波动或一次性澄清就频繁触发 `update`
