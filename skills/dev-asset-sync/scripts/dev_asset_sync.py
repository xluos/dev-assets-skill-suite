#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[3] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from dev_asset_common import (
    append_commit_record,
    asset_paths,
    collect_git_facts,
    get_branch_paths,
    get_commit_payload,
    get_head_commit,
    read_json,
    sync_development,
    write_json,
)


def sync_manifest(paths, repo_root, branch_name, branch_key, context_dir, facts, last_recorded_commit=None):
    manifest = read_json(paths["manifest"])
    manifest.update(
        {
            "repo_root": str(repo_root),
            "branch": branch_name,
            "branch_key": branch_key,
            "context_dir": context_dir,
            "updated_at": facts["updated_at"],
            "scope_summary": facts["scope_summary"],
        }
    )
    if last_recorded_commit is not None:
        manifest["last_recorded_commit"] = last_recorded_commit
    write_json(paths["manifest"], manifest)


def command_sync_working_tree(args):
    repo_root, branch_name, branch_key, context_dir, branch_dir = get_branch_paths(
        args.repo, args.context_dir, args.branch
    )
    if not branch_dir.exists():
        raise RuntimeError(f"asset directory does not exist: {branch_dir}. Run dev-asset-setup first.")

    paths = asset_paths(branch_dir)
    facts = collect_git_facts(repo_root, branch_name, context_dir)
    sync_development(paths, facts)
    sync_manifest(paths, repo_root, branch_name, branch_key, context_dir, facts)

    print(
        json.dumps(
            {
                "repo_root": str(repo_root),
                "branch": branch_name,
                "context_dir": context_dir,
                "branch_dir": str(branch_dir),
                "mode": "sync-working-tree",
                "files_considered": len(
                    set(
                        facts["working_tree_files"]
                        + facts["staged_files"]
                        + facts["untracked_files"]
                        + facts["since_base_files"]
                    )
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def command_record_head(args):
    repo_root, branch_name, branch_key, context_dir, branch_dir = get_branch_paths(
        args.repo, args.context_dir, args.branch
    )
    if not branch_dir.exists():
        raise RuntimeError(f"asset directory does not exist: {branch_dir}. Run dev-asset-setup first.")

    paths = asset_paths(branch_dir)
    facts = collect_git_facts(repo_root, branch_name, context_dir)
    sync_development(paths, facts)

    manifest = read_json(paths["manifest"])
    current_head = args.commit or get_head_commit(repo_root)
    recorded = manifest.get("last_recorded_commit")
    recorded_new_commit = False

    if current_head and current_head != recorded:
        payload = get_commit_payload(repo_root, current_head)
        append_commit_record(paths["commits"], payload)
        recorded = current_head
        recorded_new_commit = True

    sync_manifest(paths, repo_root, branch_name, branch_key, context_dir, facts, recorded)

    print(
        json.dumps(
            {
                "repo_root": str(repo_root),
                "branch": branch_name,
                "context_dir": context_dir,
                "branch_dir": str(branch_dir),
                "mode": "record-head",
                "recorded_commit": recorded,
                "recorded_new_commit": recorded_new_commit,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser(description="Sync branch-scoped development assets around commits.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("sync-working-tree", "record-head"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--repo", default=".", help="Path inside the target Git repository")
        sub.add_argument("--context-dir", help="Repository-local storage root")
        sub.add_argument("--branch", help="Branch name. Defaults to the current checked-out branch")
        if name == "record-head":
            sub.add_argument("--commit", help="Explicit commit sha to record")

    args = parser.parse_args()
    try:
        if args.command == "sync-working-tree":
            command_sync_working_tree(args)
        else:
            command_record_head(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
