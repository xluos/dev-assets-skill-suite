---
name: dev-assets-setup
description: Use when a branch starts a new requirement stream or when the current branch has no development asset directory yet, and Codex should initialize a branch-named memory directory, then collect the branch's current summary and source-document entry points.
---

# Dev Assets Setup

为当前 Git 分支初始化一个“开发记忆目录”，并在初始化后主动向用户收集最小但关键的资料。

**Announce at start:** 用一句简短的话说明将先初始化当前分支记忆目录并补齐关键入口。

**Core principle:** 初始化负责建记忆骨架；资料 intake 的重点是当前摘要和源资料入口，不是复制一整套 PRD / 评审 / 方案文件。

## Workflow

1. 确认当前目录位于 Git 仓库内。
2. 运行 `scripts/init_dev_assets.py --repo <repo-path>` 初始化当前分支目录。
3. 告诉用户创建出的目录和资产文件清单。
4. 主动索要缺失资料，优先顺序：
   - 当前目标
   - 范围边界
   - 当前阶段
   - 关键约束
   - 已知风险或阻塞
   - 源文档 / 链接 / 代码入口
5. 收到资料后，优先调用 `dev-assets-update` 重写 `overview / development / context / sources` 中最合适的 section。

## Command

```bash
python3 /absolute/path/to/dev-assets-setup/scripts/init_dev_assets.py --repo <repo-path>
```

可选参数：

- `--context-dir .dev-assets`
- `--branch <branch-name>`

## What Gets Created

目录结构：

`<repo>/.dev-assets/<branch>/`

关键文件：

- `overview.md`
- `development.md`
- `context.md`
- `sources.md`
- `manifest.json`
- `artifacts/history/`

脚本还会：

- 将目录写入本地 Git config：`dev-assets.dir`
- 自动把 `.dev-assets/` 加入 `.git/info/exclude`

## Intake Rules

- 主动问用户要源文档或链接，不要要求用户把整份文档重新手打一遍。
- `.dev-assets/` 只保留当前有效记忆，不复制完整正文。
- 如果用户只给零散信息，先整理成当前有效摘要，再写入对应文件。
- 需要具体实现细节时，优先把入口写进 `sources.md`。

## Always / Never

**Always:**

- 把目录按分支名初始化
- 初始化后立即告诉用户缺哪些关键入口信息
- 优先收“当前摘要 + 源资料入口”
- 让 `.dev-assets/` 成为记忆入口，而不是文档镜像

**Never:**

- 只建目录不做资料 intake
- 继续复制 `prd / review / frontend / backend / test` 一整套正文
- 假装已经理解需求，只因为目录初始化完成了
