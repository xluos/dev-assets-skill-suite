---
name: dev-assets-tidy
description: 整理已结构化的 dev-assets 记忆 —— 当条目随时间漂移（陈旧 / 重复 / 错误 / 模板占位残留）时，agent 把相关条目聚合成一个个**事项级 proposal**（"清掉 X / 重置 Y / 删除 section Z"），生成浏览器审阅页让用户对每个 proposal accept/reject、导出 plan.json，再 apply 落盘并自动备份。**按语义而非字面句式触发**，凡出现以下任一语义都要触发：1) 用户说"整理一下记忆"、"清下过期的"、"看看哪些还成立"、"记忆里好像有重复 / 旧条目 / 不对的地方"；2) 长期分支（master / main / develop 等）记忆累积到一定体量、context dump 看起来含 v1 残留 / 模板占位 / stale 信号；3) 用户做完一波 graduate 之后想再扫一遍剩下的；4) capture 改写单条不够用、需要批量 review 多条时。和 setup（unsorted → 分类）/ graduate（跨分支提炼+归档）的边界：tidy 不分类、不归档、不跨分支提炼，只对**已结构化**的条目做 keep/delete/edit/section-delete/file-reset。
---

# Dev Assets Tidy

Tidy 是 dev-assets 套件里**已结构化记忆的定期校准入口**。

| 命令 | 输入状态 | 输出状态 | 主要动作 |
|---|---|---|---|
| `setup` | 无序（unsorted.md） | 有序（分类到 decisions/progress/...） | add（分类塞进去） |
| `tidy` | 有序但漂移 | 有序且校准 | delete + edit + reset（破坏性） |
| `graduate` | branch 完成 | 跨分支知识上提 + 归档 | 提炼 + 归档 |

**Announce at start:** 用一句简短的话说明将先扫描当前 branch（默认）或 branch+repo 的所有 entry，由 agent 把相关条目聚合成几个**事项级 proposal**，生成 HTML 让用户在浏览器对每个 proposal accept/reject，导出 plan.json 后再 apply 落盘。

## 核心思路：以"事项 / proposal"为决策单元

旧版 tidy 把每条 entry 暴露给用户做决策，66 条 entry 就 66 个决策点 —— 太重。新版 tidy 让 **agent 聚合相关条目成 proposal**（一个语义单元，对应"做一件事"），用户对 proposal 整体 accept/reject。决策点从 N 条 entry 降到 ~3-8 个 proposal。

四种 proposal action 类型，agent 按场景挑：

| 类型 | 场景 | 写法 |
|---|---|---|
| `delete-entries` | 同 section 内删一组 bullet | `{"type": "delete-entries", "ids": ["overview::6::0", "overview::6::1", ...]}` |
| `delete-section` | 整个 H2 section 都该删 | `{"type": "delete-section", "file_key": "overview", "section_idx": 7}` |
| `reset-file` | 整个文件骨架都过期了，重置回 v2 模板最干净 | `{"type": "reset-file", "file_key": "unsorted"}` |
| `edit-entries` | 改写一组 entry 文本 | `{"type": "edit-entries", "edits": [{"id": "...", "new_text": "..."}]}` |

聚合原则：
- **同因同果合并**：所有"删 demo 资产模板列表"的条目合一个 proposal，不是 8 条 delete
- **section / file 颗粒度优先**：能用 `delete-section` 就别枚举 entries；能用 `reset-file` 就别 `delete-section` 一堆
- **写好 title 和 reason**：title 要让用户一眼看懂"做什么"，reason 解释"为什么"。proposal 是给用户审的，不是给脚本对账的

## DO / DON'T

**Do:**
- 用户说"整理记忆 / 清下过期的 / 看看哪些还成立 / 记忆有重复 / 这条早就不对了"
- 长期主分支记忆累积变多、context 输出看起来杂乱时主动建议
- 做完 graduate 后用户想再校准剩下的内容

**Don't:**
- 拿 tidy 来做"分类无序内容"（那是 setup 的活）
- 拿 tidy 来归档分支或提炼跨分支知识（那是 graduate 的活）
- 在没让用户审 HTML 的情况下直接 apply（destructive，必须人审）
- 把每条 entry 单独做成一个 proposal —— 那只是把决策从 entry 抬到 proposal、用户决策点没减少

## Workflow（三步）

### Step 1: 扫描 —— 拿到 entries / sections / files 清单

```bash
npx dev-assets tidy prepare \
  [--repo <repo-path>] [--branch <branch-name>] \
  [--scope branch|branch+repo]
```

默认 `--scope branch`，仅处理 `branch/*.md`。需要顺手清 repo 共享层时加 `--scope branch+repo`。

输出节选：

```json
{
  "review_html": "/Users/.../branches/master/tidy_review/review_<ts>.html",
  "open_url": "file:///Users/.../review_<ts>.html",
  "entry_count": 66,
  "section_count": 22,
  "proposal_count": 0,
  "entries": [...],
  "sections": [...]
}
```

第一次跑没 proposals，HTML 空着 —— 这是给 agent 看 entries / sections 的。

### Step 2: agent 把相关条目聚合成 proposals，重跑 prepare 注入

读完 entries / sections 列表，**LLM 把相关条目聚合成几个 proposal**，每个 proposal 写好 title + reason + 一组 actions。例：

```json
[
  {
    "id": "p1",
    "title": "清掉 overview.md 的 demo 资产列表",
    "reason": "这些是 dev-assets 模板默认填的 demo 文件名（prd.md/review-notes.md 等），不是本仓库真实存在的文件",
    "actions": [
      {"type": "delete-entries", "ids": ["overview::6::0", "overview::6::1", "overview::6::2", "overview::6::3", "overview::6::4", "overview::6::5", "overview::6::6", "overview::6::7"]}
    ]
  },
  {
    "id": "p2",
    "title": "删除 overview.md 的 v1 残留 section '提交前同步 dev-assets 会话重构'",
    "reason": "整个 section 描述的是 v1 时代的 update / sync 工作，已被 v2 capture 取代",
    "actions": [
      {"type": "delete-section", "file_key": "overview", "section_idx": 7}
    ]
  },
  {
    "id": "p3",
    "title": "重置 unsorted.md 回 v2 模板",
    "reason": "v1 时代留下的 H3 骨架 + AUTO-GENERATED 块（v1 错位 bug），所有内容都已过期；整体重置最干净",
    "actions": [
      {"type": "reset-file", "file_key": "unsorted"}
    ]
  }
]
```

重跑 prepare 注入：

```bash
npx dev-assets tidy prepare \
  --scope branch+repo \
  --proposals-file /tmp/tidy-proposals.json
```

也可以同时给 `--hints-json`（entry-level）和 `--proposals-json`（proposal-level）—— 不冲突，前者给"未提议"折叠区里的 entry 标颜色，后者驱动主卡片。

### Step 3: 用户在浏览器审 + 导出 plan.json

引导用户：

> 我已经生成 review HTML：`<open_url>`
> 主视图是 N 张 proposal 卡片，每张代表一件事。默认全部 accept，不同意的点 reject 即可。
> 想看具体动了哪些 entry → 点卡片底部"查看影响 entries"。
> "未提议"折叠区可以扫漏网之鱼。
> 审完点蓝色"导出 plan.json"下载到 Downloads，告诉我路径。

### Step 4: apply

```bash
npx dev-assets tidy apply \
  --plan-file ~/Downloads/tidy_plan_<ts>.json \
  [--repo <repo-path>] [--branch <branch-name>]
```

行为：
- **先备份**：scope 内所有 .md 整份 copy 到 `branches/<branch>/tidy_backup_<ts>/` + 写 manifest
- 按 plan.actions 落盘：reset-file 优先（覆盖该文件其他动作）→ delete-section → entry-level delete/edit
- 在 `branches/<branch>/tidy_review/summary_<ts>.md` 写一份 summary（已接受的 proposal id、计数、rewritten / invalid 列表）

## plan.json 格式（HTML 导出形态）

```json
{
  "tidy_id": "20260427T160000Z",
  "scope": { "include_repo": false },
  "accepted_proposals": ["p1", "p2", "p3"],
  "actions": [
    {"type": "delete-entries", "ids": ["overview::6::0", ...]},
    {"type": "delete-section", "file_key": "overview", "section_idx": 7},
    {"type": "reset-file", "file_key": "unsorted"},
    {"id": "extra::1::0", "action": "delete"}
  ],
  "notes": "用户备注"
}
```

`actions` 是被接受 proposal 里所有 actions 的 flatten 结果 + "未提议"折叠区里用户额外手动标 delete 的 entry-level actions。Apply 不区分来源，按字段类型 (`type` vs `id`) 调度。

## 设计取舍

- **以 proposal 为决策单元**：把"删 8 条 demo 资产" 折成 1 个决策，不是 8 个；用户从 66 个决策点降到 3-5 个 proposal
- **HTML 静态文件 + 浏览器**：不开 server，`file://` 协议；和 skill-creator 的 `eval_review.html` 同款 export-download 工作流
- **agent proposals 是建议不是判决**：用户可以 reject 任一个 proposal，也可以从"未提议"折叠区手工标 delete
- **备份永远跑**：tidy 是破坏性动作，备份开销极小（KB 级），不提供 `--no-backup`
- **reset-file 优先级最高**：同文件如果同时有 reset 和 delete-section / entry-level，reset 赢，其他动作丢弃
- **不动 manifest.json / artifacts/**：tidy 只整理 prose 类 markdown，结构化数据交给其他命令
- **不动 progress.md 的 AUTO-GENERATED 块**：rewrite 时整块原样保留；section 删除时如果该 section 含 auto 块，**不要**用 delete-section（用 entry-level 更安全）

## Always / Never

**Always:**
- prepare 第一次跑完，先把 entries / sections 读一遍再聚合 proposals
- 每个 proposal 写好 title + reason，title 让用户一眼懂、reason 解释 why
- 优先用 section / file 级别的 action 减少 plan.json 长度
- apply 完看 summary_*.md 确认 accepted proposal 数 / rewritten 数都对得上

**Never:**
- 跳过 HTML 审阅直接 apply（哪怕 proposals 是 agent 自己生成的）
- 给一个 entry 同时塞进 delete 和 edit（apply 以最后一个为准，未定义）
- 给 progress.md 的"自动同步区" section 用 delete-section（auto 块会被一起删掉，下次 capture sync 会重建但中间状态不一致）
- 用 reset-file 然后又给同文件加 delete-section / entry actions —— reset 会赢，其他动作徒劳
