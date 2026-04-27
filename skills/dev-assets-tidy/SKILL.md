---
name: dev-assets-tidy
description: 整理已结构化的 dev-assets 记忆 —— 当条目随时间漂移（陈旧 / 重复 / 错误 / 模板占位残留）时，dump 出一份带 agent 判断的浏览器审阅页，让用户在 HTML 里点 keep/delete/edit 决策、导出 plan.json，再 apply 落盘并自动备份。**按语义而非字面句式触发**，凡出现以下任一语义都要触发：1) 用户说"整理一下记忆"、"清下过期的"、"看看哪些还成立"、"记忆里好像有重复 / 旧条目 / 不对的地方"；2) 长期分支（master / main / develop 等）记忆累积到一定体量、context dump 看起来含 v1 残留 / 模板占位 / stale 信号；3) 用户做完一波 graduate 之后想再扫一遍剩下的；4) capture 改写单条不够用、需要批量 review 多条时。和 setup（unsorted → 分类）/ graduate（跨分支提炼+归档）的边界：tidy 不分类、不归档、不跨分支提炼，只对**已结构化**的条目做 keep/delete/edit。
---

# Dev Assets Tidy

Tidy 是 dev-assets 套件里**已结构化记忆的定期校准入口**。

| 命令 | 输入状态 | 输出状态 | 主要动作 |
|---|---|---|---|
| `setup` | 无序（unsorted.md） | 有序（分类到 decisions/progress/...） | add（分类塞进去） |
| `tidy` | 有序但漂移 | 有序且校准 | delete + edit + keep（破坏性） |
| `graduate` | branch 完成 | 跨分支知识上提 + 归档 | 提炼 + 归档 |

**Announce at start:** 用一句简短的话说明将先 dump 当前 branch（默认）或 branch+repo 的所有 entry，由 agent 在每条加 hint，再生成 HTML 让用户在浏览器审阅，导出 plan.json 后再 apply 落盘。

## DO / DON'T

**Do:**
- 用户说"整理记忆 / 清下过期的 / 看看哪些还成立 / 记忆有重复 / 这条早就不对了"
- 长期主分支记忆累积变多、context 输出看起来杂乱时主动建议
- 做完 graduate 后用户想再校准剩下的内容

**Don't:**
- 拿 tidy 来做"分类无序内容"（那是 setup 的活）
- 拿 tidy 来归档分支或提炼跨分支知识（那是 graduate 的活）
- 在没看 prepare 输出 / 没让用户审 HTML 的情况下直接 apply（destructive，必须人审）
- 给 unsorted.md 做 tidy（unsorted 应该走 setup 分类，不是 tidy 删/改）—— 但脚本不阻拦，因为偶尔用户就是想批量删

## Workflow（三步走）

### Step 1: 第一次 prepare —— 拿到 entries 列表

```bash
npx dev-assets tidy prepare \
  [--repo <repo-path>] [--branch <branch-name>] \
  [--scope branch|branch+repo]
```

默认 `--scope branch`，仅处理 `branch/*.md`。需要顺手清 repo 共享层时加 `--scope branch+repo`。

输出（节选）：

```json
{
  "review_html": "/Users/.../branches/master/tidy_review/review_<ts>.html",
  "open_url": "file:///Users/.../review_<ts>.html",
  "entry_count": 42,
  "entries": [
    {"id": "decisions::1::0", "file": "branch/decisions.md", "section": "关键决策与原因", "text": "...", "is_placeholder": false},
    ...
  ]
}
```

每条 entry 的 `id` 形如 `<file_key>::<section_idx>::<entry_idx>`，是 plan.json 里的稳定引用键。

### Step 2: agent 给每条加 hint，重跑 prepare 注入 hints

读完 entries 列表，**LLM 自己判断每条的 hint**：

| Hint | 含义 | 一般对应动作 |
|---|---|---|
| `STALE` | 已过期 / 历史残留 / 描述的工作早已落地 | 多半 delete |
| `DUP` | 与别处重复（含跨文件、跨 section） | delete 一份留一份 |
| `OK` | 当前仍成立、无歧义 | keep |
| `UNCLEAR` | 看不出来还成不成立、需要用户拍板 | 由用户决定 |

构造 hints_json：

```json
{
  "decisions::1::0": {"label": "STALE", "reason": "提到的 dev-assets-update / sync 已被 v2 capture 取代"},
  "overview::5::0": {"label": "DUP", "reason": "同样内容在 progress::2::1 也有"}
}
```

重跑 prepare 注入 hints，HTML 会带颜色标签 + 理由：

```bash
npx dev-assets tidy prepare \
  --hints-json '{"decisions::1::0":{"label":"STALE","reason":"..."}, ...}'
```

或写到文件：

```bash
npx dev-assets tidy prepare --hints-file /tmp/tidy-hints.json
```

### Step 3: 用户在浏览器审 + 导出 plan.json

引导用户：

> 我已经生成 review HTML：`<open_url>`
> 用浏览器打开，每条 entry 三个按钮 keep/delete/edit；agent 标的 hint 只是参考，可以推翻。
> 顶部"按 hint 建议"按钮会一键把 STALE/DUP 标 delete、OK 标 keep。
> 审完点"导出 plan.json"，文件会下载到 Downloads。
> 完成后告诉我下载文件路径，我来 apply。

### Step 4: apply

```bash
npx dev-assets tidy apply \
  --plan-file ~/Downloads/tidy_plan_<ts>.json \
  [--repo <repo-path>] [--branch <branch-name>]
```

行为：
- **先备份**：受影响的所有文件原样 copy 到 `branches/<branch>/tidy_backup_<ts>/`，并写一个 `manifest.json` 记录每个备份的来源
- 按 plan.actions 重写每个文件（delete 删 bullet、edit 替换为 new_text、未提到的 entry 默认 keep）
- 在 `branches/<branch>/tidy_review/summary_<ts>.md` 写一份 summary（备注、计数、备份位置）

## plan.json 格式

```json
{
  "tidy_id": "20260427T160000Z",
  "scope": { "include_repo": false },
  "actions": [
    {"id": "decisions::1::0", "action": "delete"},
    {"id": "overview::5::0", "action": "edit", "new_text": "改写后的文本，可多行"}
  ],
  "notes": "用户的备注"
}
```

`action` 可选值：`keep` / `delete` / `edit`。HTML 导出时会省略 keep 条目让 plan.json 更紧凑 —— 没出现在 actions 里的 entry 默认是 keep。

## 设计取舍

- **HTML 静态文件 + 浏览器**：不开 server，用 `file://` 协议；和 skill-creator 的 `eval_review.html` 同款工作流（用户在页面里点点 → 下载 JSON → agent 读取继续）
- **agent hint 是建议不是判决**：脚本不会因为 hint=STALE 就自动删，必须用户在 HTML 里显式选 delete
- **备份永远跑**：tidy 是破坏性动作，备份开销极小（branch 文件总量 KB 级），不提供 `--no-backup`
- **不动 manifest.json / artifacts/**：tidy 只整理 prose 类的 markdown，结构化数据交给其他命令
- **不动 progress.md 的 AUTO-GENERATED 块**：那是机器同步区，每条 entry 解析时跳过这块；rewrite 时整块原样保留

## Always / Never

**Always:**
- prepare 第一次跑完，先把 entries 列表读一遍再决定 hints
- 给的 hint 要附 reason，HTML 里用户看到 reason 才知道为什么标 STALE
- apply 完看 summary_*.md 确认计数对得上

**Never:**
- 跳过 HTML 审阅直接 apply（哪怕 plan 是 agent 自己生成的）
- 给 unsorted.md 跑完 tidy 然后又跑 setup —— 顺序反了。setup 优先，tidy 跑在结构化之后
- 给一条 entry 同时标 delete 又给 new_text（apply 以 action 为准，new_text 被忽略）
