#!/usr/bin/env python3

import argparse
import json
import sys

from dev_asset_common import get_branch_paths, initialize_assets


def main():
    parser = argparse.ArgumentParser(description="Initialize branch-scoped development assets.")
    parser.add_argument("--repo", default=".", help="Path inside the target Git repository")
    parser.add_argument("--context-dir", help="Repository-local storage root")
    parser.add_argument("--branch", help="Branch name. Defaults to the current checked-out branch")
    args = parser.parse_args()

    try:
        repo_root, branch_name, branch_key, resolved_context_dir, branch_dir = get_branch_paths(
            args.repo, args.context_dir, args.branch
        )
        paths = initialize_assets(repo_root, branch_name, branch_key, resolved_context_dir, branch_dir)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "repo_root": str(repo_root),
                "branch": branch_name,
                "context_dir": resolved_context_dir,
                "branch_dir": str(branch_dir),
                "files": {key: str(value) for key, value in paths.items()},
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
