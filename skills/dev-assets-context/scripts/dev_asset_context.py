#!/usr/bin/env python3

import argparse
import json
import sys

from dev_asset_common import (
    asset_paths,
    collect_git_facts,
    get_branch_paths,
    list_missing_docs,
    read_json,
    sync_development,
    write_json,
)


def command_show(args):
    repo_root, branch_name, branch_key, resolved_context_dir, branch_dir = get_branch_paths(
        args.repo, args.context_dir, args.branch
    )
    if not branch_dir.exists():
        raise RuntimeError(f"asset directory does not exist: {branch_dir}. Run dev-assets-setup first.")

    paths = asset_paths(branch_dir)
    payload = {
        "repo_root": str(repo_root),
        "branch": branch_name,
        "branch_key": branch_key,
        "context_dir": resolved_context_dir,
        "branch_dir": str(branch_dir),
        "files": {key: str(value) for key, value in paths.items()},
        "missing_or_placeholder": list_missing_docs(paths),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_sync(args):
    repo_root, branch_name, branch_key, resolved_context_dir, branch_dir = get_branch_paths(
        args.repo, args.context_dir, args.branch
    )
    if not branch_dir.exists():
        raise RuntimeError(f"asset directory does not exist: {branch_dir}. Run dev-assets-setup first.")

    paths = asset_paths(branch_dir)
    facts = collect_git_facts(repo_root, branch_name, resolved_context_dir)
    sync_development(paths, facts)

    manifest = read_json(paths["manifest"])
    manifest.update(
        {
            "repo_root": str(repo_root),
            "branch": branch_name,
            "branch_key": branch_key,
            "context_dir": resolved_context_dir,
            "updated_at": facts["updated_at"],
            "scope_summary": facts["scope_summary"],
        }
    )
    write_json(paths["manifest"], manifest)

    payload = {
        "repo_root": str(repo_root),
        "branch": branch_name,
        "context_dir": resolved_context_dir,
        "branch_dir": str(branch_dir),
        "missing_or_placeholder": list_missing_docs(paths),
        "files_considered": len(
            set(
                facts["working_tree_files"]
                + facts["staged_files"]
                + facts["untracked_files"]
                + facts["since_base_files"]
            )
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Read or refresh branch-scoped development assets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("show", "sync"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--repo", default=".", help="Path inside the target Git repository")
        sub.add_argument("--context-dir", help="Repository-local storage root")
        sub.add_argument("--branch", help="Branch name. Defaults to the current checked-out branch")

    args = parser.parse_args()
    try:
        if args.command == "show":
            command_show(args)
        else:
            command_sync(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
