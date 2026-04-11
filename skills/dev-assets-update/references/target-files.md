# Target Files

Branch scope:

- `overview.md`: 当前目标、范围边界、当前阶段、关键约束
- `development.md`: 建议优先查看的目录、当前进展、阻塞与注意点、下一步
- `context.md`: 当前有效上下文、关键决策与原因、后续继续前要注意
- `sources.md`: 分支级资料入口、Git 历史入口、回源提示

Repo scope:

- `repo/overview.md`: 跨分支长期目标、边界、稳定约束
- `repo/context.md`: 跨分支长期背景、共享决策、共享注意点
- `repo/sources.md`: 共享文档入口、评审入口、外部链接入口

Rule of thumb:

- 能从源文档低成本恢复的内容，不要在 dev-assets 里复制正文
- 能从 Git 历史低成本恢复的内容，不要在 dev-assets 里记实现流水账
- branch-specific 当前工作态不要写进 repo 共享层
