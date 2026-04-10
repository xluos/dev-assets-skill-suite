# Dev Asset Skill Suite

Branch-scoped development memory skills for Codex and similar agent runtimes.

This repository packages a small skill suite for one job: keep branch-coupled development memory usable across sessions without turning `.dev-assets/` into a second copy of every source document.

- `using-dev-assets` — entry router for Git-repository development conversations
- `dev-assets-setup` — initialize `.dev-assets/<branch>/` and create the branch memory scaffold
- `dev-assets-context` — recover the branch's current memory and refresh Git-derived navigation before coding
- `dev-assets-update` — rewrite the current branch memory when the user adds or corrects important context, or when the conversation clearly reveals that stored understanding should be corrected
- `dev-assets-sync` — treat commit-related moments as checkpoints, then persist only this commit's durable memory instead of appending a running journal

Detailed guide:

- [docs/dev-asset-skill-suite-guide.md](docs/dev-asset-skill-suite-guide.md)

## Install with `npx skills`

List available skills:

```bash
npx skills add xluos/dev-asset-skill-suite --list
```

Install the whole suite for Codex globally:

```bash
npx skills add xluos/dev-asset-skill-suite --skill '*' -a codex -g -y
```

Install the whole suite for all detected agents:

```bash
npx skills add xluos/dev-asset-skill-suite --all -g -y
```

## Repository Layout

```text
skills/
  using-dev-assets/
  dev-assets-setup/
  dev-assets-context/
  dev-assets-update/
  dev-assets-sync/
lib/
  dev_asset_common.py
scripts/
  install_suite.py
```

## Branch Memory Layout

```text
.dev-assets/<branch>/
  overview.md
  development.md
  context.md
  sources.md
  manifest.json
  artifacts/
    history/
```

- `overview.md`: 最短摘要，只保留当前目标、范围、阶段、关键约束
- `development.md`: 当前工作态，重点是冷启动时先看哪些目录、当前进展、阻塞、下一步
- `context.md`: 稍详细但仍然有效的分支记忆，保留 why / caveat / handoff
- `sources.md`: 源文档和 Git 历史入口，不复制正文
- `manifest.json`: 结构化元信息，包括当前 HEAD、默认基线、scope 摘要、focus areas

## Notes

- The skills use `.dev-assets/<branch>/` as the branch-local memory directory.
- The suite no longer treats branch assets as an append-only journal. `update` rewrites current memory sections, and it may be triggered implicitly when the conversation reveals a real understanding drift or introduces new source material. `sync` only persists this commit's durable memory.
- Detailed implementation history should stay in Git. When the agent needs to know exactly what changed, it should read `git log` / `git show` instead of duplicating commit history into `.dev-assets/`.
- Source documents stay in their original locations. `.dev-assets/` keeps only the current memory and a source index.
- `dev-assets-sync` can still install non-blocking Git hooks. `post-commit` refreshes HEAD metadata, and optional `pre-commit` refreshes working-tree-derived navigation.
- `npx skills` does not need `scripts/install_suite.py`; the repository already follows standard skill discovery rules.
- `scripts/install_suite.py` remains useful for local symlink-based installs during development.
