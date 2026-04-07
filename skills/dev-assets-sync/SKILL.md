---
name: dev-assets-sync
description: Use when the user mentions commit, 提交, commit message, stage, staging, or when the agent notices meaningful code changes, reusable conclusions, constraints, risks, implementation notes, or milestone progress that should be silently persisted into the current branch's development assets. Prefer this skill proactively for low-friction, automatic branch memory sync, even if the user did not explicitly ask to record anything.
---

# Dev Assets Sync

在用户提到“提交”相关行为时，或当 agent 判断当前已经出现值得沉淀的改动与结论时，主动把这些信息同步到当前分支开发资产，并在需要时记录提交。

**Announce at start:** `我先用 dev-assets-sync 同步当前分支的开发资产和提交记录。`

**Core principle:** `sync` 不应该只在 commit 语义下被动触发。只要当前会话已经形成了值得复用的变更、结论、约束、风险、实现备注或阶段性进展，就应尽量无感地自动执行一次同步。

## Trigger Intent

典型触发语义：

- 帮我提交
- 准备 commit
- 生成 commit message
- 把这些改动提交掉
- 提交前同步一下
- stage 一下这些改动
- 提交之后记一下这次变更

以及以下 agent 主动判断场景：

- 已经完成一段有实际产出的代码修改
- 已经形成了后续会复用的实现结论或约束
- 已经明确了风险、阻塞、回归口径或后续事项
- 已经结束一个小阶段，适合留下阶段性记录
- 即将切换到新的子任务，当前上下文值得先沉淀

## Workflow

### Step 1: Decide whether this moment is worth recording

不要只盯着 commit 关键词。只要满足任一条件，就优先考虑触发 `sync`：

- 用户明确提到提交、stage、commit message
- 当前工作区已经有明确改动，且本轮会话补充了可复用解释
- 这轮对话刚形成了后续会反复引用的结论、约束、风险或测试口径
- agent 判断现在同步一次可以减少后续重复解释

目标是“无感执行”：尽量在自然节点自动做，而不是每次都等用户开口要求记录。

### Step 2: Summarize the current session first

先从当前会话提炼出可复用内容，不要直接跑脚本就结束。至少判断并整理：

- 本次改动做了什么
- 哪些实现备注后续还会用到
- 哪些风险、阻塞、边界条件需要记
- 哪些结论、取舍、约束值得写入 `decision-log.md`
- 哪些前端 / 后端 / 测试信息应该进入专项文档
- 当前用户输入里哪些原始表述值得和整理结果一起保留

把这些内容整理成结构化摘要后，运行：

```bash
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py record-session --repo <repo-path> --summary-file <summary.json>
```

`summary.json` 推荐字段：

- `title`
- `overview_summary`
- `changes`
- `implementation_notes`
- `risks`
- `next_steps`
- `decisions`
- `review_notes`
- `frontend_updates`
- `backend_updates`
- `test_updates`

其中 `decisions` 为对象数组，每项可包含：

- `decision`
- `reason`
- `impact`

### Step 3: Sync working tree facts as part of the session record

`record-session` 会在写入会话摘要前顺手刷新：

- `development.md` 的 Git 自动区
- `manifest.json`

如果希望不依赖对话触发，也可以先安装 Git hooks：

```bash
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py install-hooks --repo <repo-path> --enable-pre-commit
```

其中：

- `post-commit` 会自动执行 `record-head`
- `pre-commit`（可选）会自动执行 `sync-working-tree`
- hook 默认只做同步，不阻塞 commit

但要明确：

- hook 只能做 Git checkpoint
- hook 不能替代当前会话的语义总结
- 不要把 hook 当成完整的 `dev-assets-sync`

### Step 4: Record the latest commit if one exists

如果已经有新的 HEAD 提交，再运行：

```bash
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py record-head --repo <repo-path>
```

把最新提交写入 `commits.md`。

## Commands

```bash
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py record-session --repo <repo-path> --summary-file <summary.json>
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py sync-working-tree --repo <repo-path>
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py record-head --repo <repo-path>
python3 /absolute/path/to/dev-assets-sync/scripts/dev_asset_sync.py install-hooks --repo <repo-path> --enable-pre-commit
```

## Output Rules

- 不要只同步 Git 文件列表。
- 不要把 `sync` 限制在 commit 场景。
- 只要当前会话里已经有值得复用的内容，就应主动总结并沉淀。
- 至少更新：
  - `development.md`
  - `manifest.json`
- 有结论、约束、风险时，补写到最合适的文件，而不是只留在会话里。
- 如存在新提交，再更新 `commits.md`。
- 如果没有新提交，明确说明“已完成会话内容同步，未新增提交记录”。

## Always / Never

**Always:**

- 把提交检查点和阶段性里程碑都视为 `sync` 触发点
- 在不打断用户的前提下优先无感执行
- 明确区分“会话内容同步完成”和“提交记录完成”
- 有新提交时把 sha 和 message 落到 `commits.md`

**Never:**

- 只在用户说了 commit 才想到 `sync`
- 只刷新 Git 事实，不沉淀当前会话内容
- 只记录 commit，不刷新相关资产文件
- 在没有新提交时假装已经记录了提交
- 把提交动作当成纯 Git 操作，不沉淀任何开发资产

## Red Flags

- “用户没提提交，就先不记”
- “这次只是一个小阶段，不值得同步”
- “先继续写，记录回头再补”
- “反正 commit 的时候再统一说”

这些都说明你在绕过自动、无感的沉淀流程。
