---
name: dev-assets-update
description: Use when the user wants to actively add, correct, summarize, or persist new requirement information into the current branch's development assets, including PRD details, review notes, technical plans, test cases, links, risks, decisions, or implementation notes.
---

# Dev Assets Update

把用户刚刚补充的新信息，沉淀到当前分支的开发资产里，而不是只留在对话中。

**Announce at start:** `我先用 dev-assets-update 把这次补充的信息落到当前分支的开发资产里。`

**Core principle:** 新获得的需求背景、评审结论、技术约束、测试口径、风险判断，只要后续还会复用，就应该及时归档到对应资产文件。

## Trigger Intent

典型触发语义：

- 把这个信息记进去
- 补充一下需求背景
- 更新一下 PRD / 评审记录 / 技术方案
- 把这条结论写到开发资产里
- 把这个风险记下来
- 这个测试口径也补进去
- 整理一下刚才说的内容并存起来

## Workflow

### Step 1: Locate the current branch asset directory

先运行：

```bash
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py show --repo <repo-path>
```

如果资产目录不存在，立即切到 `dev-assets-setup`，不要直接新建零散文件。

### Step 2: Choose the right target file

按信息类型选择落点，不要把所有内容都堆进一个文件：

- 需求范围、目标、验收口径 → `prd.md`
- 评审结论、争议点、action items → `review-notes.md`
- 前端实现思路、交互状态、页面范围 → `frontend-design.md`
- 后端接口、模型、兼容性、发布影响 → `backend-design.md`
- 测试场景、回归口径、边界条件 → `test-cases.md`
- 当前需求点、实现备注、阻塞、临时范围说明 → `development.md`
- 会被反复引用的结论、约束、取舍 → `decision-log.md`
- 高层摘要变化 → `overview.md`

不确定时，先运行：

```bash
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py suggest-target --kind <kind>
```

### Step 3: Update the file cleanly

- 先保留原有结构
- 优先追加到最相关章节
- 必要时补一个新小节，但不要把文档改成流水账
- 如果内容会影响总体认知，同步更新 `overview.md`

### Step 4: Refresh manifest metadata

写完后运行：

```bash
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py touch-manifest --repo <repo-path>
```

## Commands

```bash
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py show --repo <repo-path>
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py suggest-target --kind <kind>
python3 /absolute/path/to/dev-assets-update/scripts/dev_asset_update.py touch-manifest --repo <repo-path>
```

`kind` 可用值：

- `summary`
- `prd`
- `review`
- `frontend`
- `backend`
- `test`
- `development`
- `decision`
- `risk`
- `constraint`
- `link`

## Writing Rules

- 写入时优先整理成后续可复用的表达，不要原样转存对话口语。
- 如果信息只是临时想法，不要伪装成正式结论。
- 如果这次补充会改变整体理解，同步更新 `overview.md`。
- 如果是强约束或重要取舍，优先进入 `decision-log.md`，不要只写在 `development.md`。

## Always / Never

**Always:**

- 把“主动补充资料”视为独立触发场景
- 先定位资产目录，再落盘
- 把信息写进最合适的文件，而不是一股脑塞到 `development.md`
- 写完后刷新 `manifest.json` 的更新时间

**Never:**

- 把所有新增信息都堆到一个文件里
- 用“之后再整理”为理由跳过沉淀
- 把用户随口猜测写成正式结论
- 在资产目录不存在时手工拼一套临时文件

## Red Flags

- “这只是补充一句，先不记”
- “先放在聊天里，回头再整理”
- “反正 overview 里写一下就行”
- “不确定放哪，就都塞进 development.md”

这些都说明你在绕过可复用资产的沉淀流程。
