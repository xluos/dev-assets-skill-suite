# Branch Memory Principles

## Goal

这个仓库的目标是维护“跨会话的、与分支耦合的开发资产记忆”。

它不是：

- 源文档镜像
- 提交历史镜像
- 会话流水账系统

## File Roles

- `overview.md`
  最短摘要。只保留当前目标、范围边界、阶段、关键约束。
- `development.md`
  当前工作态。只保留冷启动时先看哪些目录、当前进展、阻塞与注意点、下一步。
- `context.md`
  稍详细但仍然有效的分支记忆。重点保留 why / caveat / workaround / handoff。
- `sources.md`
  源文档、链接、Git 历史入口。这里只放入口，不复制正文。
- `manifest.json`
  结构化元信息，例如当前 HEAD、默认基线、scope 摘要、focus areas。

## Skill Boundaries

### `dev-assets-context`

- 主职责是恢复上下文，不是重建上下文。
- 默认先读 `overview.md`、`development.md`、`context.md`。
- 只有在需要原始事实时才回源到 `sources.md`。
- 允许做轻量的 Git 导航刷新，例如 focus areas、scope summary、HEAD 元信息。
- 不要重写语义记忆正文。

### `dev-assets-sync`

- 触发时机默认是提交前后或提交相关节点。
- 主职责是沉淀“本次提交后仍然有价值的内容”，不是刷新整个分支状态。
- 只关注本次这轮会话的 why / constraint / caveat / next-step / risk。
- 不要把 commit history 复制到 `.dev-assets/`。
- 不要在 `sync` 里做全局语义重建。
- 只有在本次提交明确改变了分支整体目标 / 范围 / 阶段时，才允许触碰 `overview.md`。

### `dev-assets-update`

- 用于补充或修正记忆，既可以由用户显式提出，也可以由 agent 隐式触发。
- 允许隐式触发的典型场景只有两类：
  - 会话中反复出现理解偏差、口径被纠正、先前结论已失效。
  - 用户提供了新的相关资料、链接、文档入口，且这些信息明显会影响后续理解。
- 可以重写 `overview.md`、`development.md`、`context.md`、`sources.md` 的当前 section。
- 它负责当前记忆的显式或隐式修正，不负责提交时的轻量沉淀。
- 不要因为轻微措辞变化、普通问答往返或一次性澄清就频繁触发 `update`。

## Git Rules

- “做了什么、改了哪些文件、什么时候改的”优先回 Git：
  - `git log`
  - `git show`
  - `git diff`
- `.dev-assets/` 只保留下一次继续工作时最需要知道的内容。

## Writing Rules

- 优先覆盖写当前状态，不要持续 append 同类历史。
- 能从源文档低成本恢复的内容，不要在 `.dev-assets/` 里复制正文。
- 能从 Git 历史低成本恢复的内容，不要在 `.dev-assets/` 里复制实现历史。
