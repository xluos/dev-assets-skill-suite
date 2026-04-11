# Dev Asset Skill Suite

Repo-aware and branch-coupled development memory skills for Codex and similar agent runtimes.

This repository packages a small skill suite for one job: keep development memory usable across sessions without turning the Git worktree into a second document store.

- `using-dev-assets` — entry router for Git-repository development conversations
- `dev-assets-setup` — initialize user-home repo+branch memory storage for the current repository
- `dev-assets-context` — recover current branch memory first, then pull repo-shared memory when needed
- `dev-assets-update` — rewrite current durable memory or shared source indexes when new understanding appears
- `dev-assets-sync` — treat commit-related moments as checkpoints and persist only durable memory

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

## Storage Layout

By default the suite stores memory outside the repository:

```text
~/.codex/dev-assets/repos/<repo-key>/
  repo/
    overview.md
    context.md
    sources.md
    manifest.json
  branches/
    <branch>/
      overview.md
      development.md
      context.md
      sources.md
      manifest.json
      artifacts/
        history/
```

- `repo/`: shared memory for the whole Git repository
- `branches/<branch>/`: branch-local working memory
- `repo-key`: derived from repository identity, not just the folder name

## Notes

- The suite no longer stores its primary memory inside the Git worktree by default.
- Branch memory is still the main execution context. Repo memory is a shared supplement, not a replacement.
- Detailed implementation history should stay in Git. When the agent needs exact changes, it should read `git log` / `git show` instead of copying commit history into dev assets.
- Shared document entrances can live in repo-level `sources.md`; branch-specific progress and next-step live in branch files.
- `dev-assets-setup` can migrate legacy `.dev-assets/<branch>/` content into the new user-home branch directory.
- `dev-assets-sync` can still install non-blocking Git hooks. `post-commit` refreshes HEAD metadata, and optional `pre-commit` refreshes working-tree-derived navigation.
- `npx skills` does not need `scripts/install_suite.py`; the repository already follows standard skill discovery rules.
- `scripts/install_suite.py` remains useful for local symlink-based installs during development.
