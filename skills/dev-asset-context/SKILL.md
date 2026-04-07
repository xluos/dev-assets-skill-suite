---
name: dev-asset-context
description: Read and refresh the current branch's development asset directory as default context for ongoing work. Use when starting a new session on an existing branch, when Codex should recover saved PRD and technical context automatically, or when Codex needs to identify which asset files are still missing before coding.
---

# Dev Asset Context

把当前分支目录下已经沉淀的开发资产读出来，作为默认上下文入口。

## Workflow

1. 确认当前目录位于 Git 仓库内。
2. 运行 `show` 定位当前分支资产目录。
3. 运行 `sync` 刷新 `development.md` 的 Git 自动区。
4. 优先读取：
   - `overview.md`
   - `development.md`
5. 按需补读：
   - 产品问题看 `prd.md`
   - 评审口径看 `review-notes.md`
   - 前端实现看 `frontend-design.md`
   - 后端约束看 `backend-design.md`
   - 测试范围看 `test-cases.md`
6. 如果存在缺失资产，先指出缺口，再决定是否向用户索要。

## Commands

```bash
python3 /absolute/path/to/dev-asset-context/scripts/dev_asset_context.py show --repo <repo-path>
python3 /absolute/path/to/dev-asset-context/scripts/dev_asset_context.py sync --repo <repo-path>
```

## Reading Strategy

- 不要一上来全量读取整个目录。
- 先读 `overview.md` 和 `development.md`。
- 只在本次任务确实需要时再读其它文档。
- 对于仍然是模板占位的文件，明确告诉用户“已有槽位但内容缺失”。
