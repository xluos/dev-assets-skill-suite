# harvest.json schema

`apply` 命令读取的 patch 文件。结构：

```json
{
  "repo_overview": [
    { "section": "长期目标与边界", "body": "- ...", "mode": "append" }
  ],
  "repo_context": [
    { "section": "跨分支通用决策", "body": "- ...", "mode": "append" },
    { "section": "共享注意点", "body": "- ...", "mode": "append" }
  ],
  "repo_sources": [
    { "section": "共享入口", "body": "- ...", "mode": "append" }
  ],
  "notes": "短说明，落到 archive_summary.md 头部",
  "archive": true
}
```

## 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `repo_overview` / `repo_context` / `repo_sources` | array | 上提到对应 repo 文件的条目列表，可省略表示该文件无上提 |
| `section` | string | repo 文件中的目标 section title（必须是已存在的 section，否则会被新建） |
| `body` | string | 写入内容（markdown，允许多行） |
| `mode` | enum | `append`：追加到 section 末尾；`replace`：完全覆盖该 section |
| `notes` | string | 可选，会被写到 `archive_summary.md` 顶部 |
| `archive` | bool | 可选，默认 `true`。设 `false` 只做 harvest 不做归档（少见，用于先 review） |

## append 行为

- 已有 section 内容末尾追加换行 + body
- 多个同 target section 的 entry 会按顺序逐个追加
- 如果 section 不存在，创建该 section 并写入 body

## replace 行为

- 整个 section 内容被替换为 body
- 多个同 target 的 entry 时，**只有最后一个生效**（前面的被覆盖）—— 所以 replace 模式建议每个 section 只出现一次

## 不写入的字段

`development.md` / `branch overview.md` / `branch sources.md` / `branch context.md` 不接受 harvest patch —— 这些是 branch 级文件，归档时整体 mv 走，不存在"提炼后留下"的概念。
