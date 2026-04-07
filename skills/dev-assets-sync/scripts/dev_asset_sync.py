#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

from dev_asset_common import (
    append_development_section,
    append_markdown_section,
    append_commit_record,
    asset_paths,
    collect_git_facts,
    detect_repo_root,
    get_branch_paths,
    get_commit_payload,
    get_head_commit,
    read_json,
    sync_development,
    write_json,
)

HOOK_START = "# >>> dev-assets-sync >>>"
HOOK_END = "# <<< dev-assets-sync <<<"


def hook_block(command, script_path):
    return "\n".join(
        [
            HOOK_START,
            'REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"',
            f'python3 "{script_path}" {command} --repo "$REPO_ROOT" >/dev/null 2>&1 || true',
            HOOK_END,
        ]
    )


def merge_hook_content(existing, block):
    if HOOK_START in existing and HOOK_END in existing:
        before, remainder = existing.split(HOOK_START, 1)
        _, after = remainder.split(HOOK_END, 1)
        merged = before.rstrip()
        if merged:
            merged += "\n"
        merged += block
        if after.strip():
            merged += "\n" + after.lstrip("\n")
        else:
            merged += "\n"
        return merged

    stripped = existing.rstrip()
    if not stripped:
        return "#!/bin/sh\n" + block + "\n"
    if not stripped.startswith("#!"):
        stripped = "#!/bin/sh\n" + stripped
    return stripped + "\n\n" + block + "\n"


def install_hook(hook_path, block):
    existing = hook_path.read_text(encoding="utf-8") if hook_path.exists() else ""
    updated = merge_hook_content(existing, block)
    hook_path.write_text(updated, encoding="utf-8")
    hook_path.chmod(0o755)


def bullets(items):
    return "\n".join(f"- {item}" for item in items if item)


def decision_body(item):
    parts = [f"- 结论: {item['decision']}"]
    if item.get("reason"):
        parts.append(f"- 原因: {item['reason']}")
    if item.get("impact"):
        parts.append(f"- 影响范围: {item['impact']}")
    return "\n".join(parts)


def load_session_payload(args):
    if args.summary_json:
        return json.loads(args.summary_json)
    if args.summary_file:
        return json.loads(Path(args.summary_file).read_text(encoding="utf-8"))
    raise RuntimeError("one of --summary-json or --summary-file is required")


def command_record_session(args):
    payload = load_session_payload(args)
    repo_root, branch_name, branch_key, context_dir, branch_dir = get_branch_paths(
        args.repo, args.context_dir, args.branch
    )
    if not branch_dir.exists():
        raise RuntimeError(f"asset directory does not exist: {branch_dir}. Run dev-assets-setup first.")

    paths = asset_paths(branch_dir)
    facts = collect_git_facts(repo_root, branch_name, context_dir)
    sync_development(paths, facts)

    title = payload.get("title") or f"会话同步 {facts['updated_at'][:10]}"
    touched = []

    overview_items = payload.get("overview_summary") or []
    if overview_items:
        append_markdown_section(paths["overview"], title, bullets(overview_items))
        touched.append("overview.md")

    dev_parts = []
    if payload.get("changes"):
        dev_parts.append("### 本次改动\n\n" + bullets(payload["changes"]))
    if payload.get("implementation_notes"):
        dev_parts.append("### 实现备注\n\n" + bullets(payload["implementation_notes"]))
    if payload.get("risks"):
        dev_parts.append("### 风险与阻塞\n\n" + bullets(payload["risks"]))
    if payload.get("next_steps"):
        dev_parts.append("### 后续事项\n\n" + bullets(payload["next_steps"]))
    if dev_parts:
        append_development_section(paths["development"], title, "\n\n".join(dev_parts))
        touched.append("development.md")

    decision_items = [decision_body(item) for item in (payload.get("decisions") or []) if item.get("decision")]
    if decision_items:
        append_markdown_section(paths["decision_log"], title, "\n\n".join(decision_items))
        touched.append("decision-log.md")

    review_items = payload.get("review_notes") or []
    if review_items:
        append_markdown_section(paths["review_notes"], title, bullets(review_items))
        touched.append("review-notes.md")

    frontend_items = payload.get("frontend_updates") or []
    if frontend_items:
        append_markdown_section(paths["frontend_design"], title, bullets(frontend_items))
        touched.append("frontend-design.md")

    backend_items = payload.get("backend_updates") or []
    if backend_items:
        append_markdown_section(paths["backend_design"], title, bullets(backend_items))
        touched.append("backend-design.md")

    test_items = payload.get("test_updates") or []
    if test_items:
        append_markdown_section(paths["test_cases"], title, bullets(test_items))
        touched.append("test-cases.md")

    manifest = read_json(paths["manifest"])
    manifest.update(
        {
            "repo_root": str(repo_root),
            "branch": branch_name,
            "branch_key": branch_key,
            "context_dir": context_dir,
            "updated_at": facts["updated_at"],
            "scope_summary": facts["scope_summary"],
            "last_session_sync_title": title,
        }
    )
    write_json(paths["manifest"], manifest)

    print(
        json.dumps(
            {
                "repo_root": str(repo_root),
                "branch": branch_name,
                "context_dir": context_dir,
                "branch_dir": str(branch_dir),
                "mode": "record-session",
                "title": title,
                "touched_files": touched,
            },
            ensure_ascii=False,
            indent=2,
        )
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
        raise RuntimeError(f"asset directory does not exist: {branch_dir}. Run dev-assets-setup first.")

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
        raise RuntimeError(f"asset directory does not exist: {branch_dir}. Run dev-assets-setup first.")

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


def command_install_hooks(args):
    repo_root = detect_repo_root(args.repo)
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        raise RuntimeError(f"not a git repository: {repo_root}")

    hooks_dir = Path(args.hooks_dir).expanduser().resolve() if args.hooks_dir else git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    script_path = Path(__file__).resolve()
    installed = []

    post_commit = hooks_dir / "post-commit"
    install_hook(post_commit, hook_block("record-head", script_path))
    installed.append(str(post_commit))

    if args.enable_pre_commit:
        pre_commit = hooks_dir / "pre-commit"
        install_hook(pre_commit, hook_block("sync-working-tree", script_path))
        installed.append(str(pre_commit))

    print(
        json.dumps(
            {
                "repo_root": str(repo_root),
                "hooks_dir": str(hooks_dir),
                "installed_hooks": installed,
                "pre_commit_enabled": args.enable_pre_commit,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser(description="Sync branch-scoped development assets around commits.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("sync-working-tree", "record-head", "install-hooks", "record-session"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--repo", default=".", help="Path inside the target Git repository")
        if name != "install-hooks":
            sub.add_argument("--context-dir", help="Repository-local storage root")
            sub.add_argument("--branch", help="Branch name. Defaults to the current checked-out branch")
        if name == "record-head":
            sub.add_argument("--commit", help="Explicit commit sha to record")
        if name == "install-hooks":
            sub.add_argument("--hooks-dir", help="Hook directory. Defaults to .git/hooks under --repo")
            sub.add_argument(
                "--enable-pre-commit",
                action="store_true",
                help="Also install a pre-commit hook to sync the working tree before commits",
            )
        if name == "record-session":
            sub.add_argument("--summary-file", help="Path to a JSON file containing the session summary payload")
            sub.add_argument("--summary-json", help="Inline JSON session summary payload")

    args = parser.parse_args()
    try:
        if args.command == "sync-working-tree":
            command_sync_working_tree(args)
        elif args.command == "install-hooks":
            command_install_hooks(args)
        elif args.command == "record-session":
            command_record_session(args)
        else:
            command_record_head(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
