# Dev Asset Skill Suite

Branch-scoped development asset skills for Codex and similar agent runtimes.

This repository packages a small skill suite for maintaining requirement continuity on long-running feature branches:

- `using-dev-assets` — entry router for Git-repository development conversations
- `dev-assets-setup` — initialize `.dev-assets/<branch>/` and collect reusable requirement materials
- `dev-assets-context` — recover and refresh the current branch's saved development assets before coding
- `dev-assets-update` — actively add or correct requirement context in the current branch's asset files
- `dev-assets-sync` — proactively treat commit-related moments and meaningful implementation milestones as checkpoints, then sync branch assets with low-friction automatic recording

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

## Notes

- The skills use `.dev-assets/<branch>/` as the branch-local asset directory.
- `dev-assets-update` is the manual ingestion entry for cases where the user proactively provides new requirement context mid-stream. The agent should first organize the new facts, then use the bundled `write` command to append them to the mapped asset files.
- `dev-assets-sync` is primarily a session-to-assets sync skill: summarize the current conversation, write reusable facts into the right asset files, then record commits when relevant. It should also trigger proactively when the agent notices meaningful progress or reusable changes worth recording, even without explicit commit wording.
- `dev-assets-sync` can also install non-blocking Git hooks. `post-commit` records the latest commit, and optional `pre-commit` refreshes the working tree snapshot. Hooks are only a Git-side fallback, not a replacement for session summarization.
- `npx skills` does not need `scripts/install_suite.py`; the repository already follows standard skill discovery rules.
- `scripts/install_suite.py` remains useful for local symlink-based installs during development.
