#!/usr/bin/env python3

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Prefer the bundled lib/ when available so the graduate skill stays in sync
# with the rest of the suite. There is no scripts-local copy of
# dev_asset_common.py here — graduate is lib-only by design.
_lib = Path(__file__).resolve().parents[3] / "lib"
if _lib.exists() and str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))

from dev_asset_common import (
    ARCHIVE_INDEX_NAME,
    append_archive_index,
    append_to_section,
    archive_branch_dir,
    archive_root_dir,
    asset_paths,
    build_archive_summary,
    detect_no_git_mode,
    get_branch_paths,
    git_lines,
    git_stdout,
    read_json,
    split_sections,
    upsert_markdown_section,
)


def _read_sections(path):
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    _, sections = split_sections(content)
    return [{"title": title, "body": body} for title, body in sections]


def _git_status(repo_root, default_base):
    if default_base is None:
        return {"ahead": None, "uncommitted": None, "default_base": None}
    ahead = len(git_lines(["rev-list", "--count", f"{default_base}..HEAD"], cwd=repo_root, check=False) or [])
    # rev-list --count returns one line with a number; lines parsing above is
    # off — use stdout directly:
    raw = git_stdout(["rev-list", "--count", f"{default_base}..HEAD"], cwd=repo_root, check=False)
    try:
        ahead = int(raw)
    except (TypeError, ValueError):
        ahead = None
    uncommitted = bool(git_lines(["status", "--porcelain"], cwd=repo_root, check=False))
    return {"ahead": ahead, "uncommitted": uncommitted, "default_base": default_base}


def command_dry_run(args):
    if detect_no_git_mode(args.repo):
        print(json.dumps({"error": "no-git mode: graduate has nothing to archive (no branches exist)"}, ensure_ascii=False))
        return 1

    repo_root, branch_name, branch_key, _, repo_key, repo_dir, branch_dir = get_branch_paths(args.repo, args.context_dir, args.branch)

    if not branch_dir.exists():
        print(json.dumps({"error": f"branch memory not initialized: {branch_dir}"}, ensure_ascii=False))
        return 1

    paths = asset_paths(repo_dir, branch_dir)
    branch_manifest = read_json(paths["manifest"])
    repo_manifest = read_json(paths["repo_manifest"])
    default_base = branch_manifest.get("default_base") or repo_manifest.get("default_base")

    payload = {
        "repo_root": str(repo_root),
        "repo_key": repo_key,
        "branch": branch_name,
        "branch_key": branch_key,
        "branch_dir": str(branch_dir),
        "archive_destination": str(archive_root_dir(repo_dir) / f"{branch_key}__{datetime.now(timezone.utc).strftime('%Y%m%d')}"),
        "git_status": _git_status(repo_root, default_base),
        "branch_files": {
            "development.md": _read_sections(paths["development"]),
            "context.md": _read_sections(paths["context"]),
            "sources.md": _read_sections(paths["sources"]),
            "overview.md": _read_sections(paths["overview"]),
        },
        "repo_files": {
            "overview.md": _read_sections(paths["repo_overview"]),
            "context.md": _read_sections(paths["repo_context"]),
            "sources.md": _read_sections(paths["repo_sources"]),
        },
        "harvest_targets": {
            "repo_overview": ["长期目标与边界", "仓库级关键约束"],
            "repo_context": ["长期有效背景", "跨分支通用决策", "共享注意点"],
            "repo_sources": ["共享入口"],
        },
        "instructions": (
            "读 branch_files 抓取通用知识（剥离业务名词后），按 harvest-schema.md 写出 harvest.json，"
            "确认无误后跑 graduate apply。"
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _apply_entries(target_path, entries):
    """entries: list of {section, body, mode}. Returns count applied."""
    n = 0
    for entry in entries or []:
        section = entry.get("section")
        body = entry.get("body", "")
        mode = entry.get("mode", "append")
        if not section:
            raise ValueError(f"harvest entry missing 'section': {entry}")
        if mode == "append":
            append_to_section(target_path, section, body)
        elif mode == "replace":
            upsert_markdown_section(target_path, section, body)
        else:
            raise ValueError(f"harvest entry has unknown mode '{mode}': {entry}")
        n += 1
    return n


def command_apply(args):
    if detect_no_git_mode(args.repo):
        print(json.dumps({"error": "no-git mode: graduate has nothing to archive"}, ensure_ascii=False))
        return 1

    repo_root, branch_name, branch_key, _, repo_key, repo_dir, branch_dir = get_branch_paths(args.repo, args.context_dir, args.branch)

    if not branch_dir.exists():
        print(json.dumps({"error": f"branch memory not initialized: {branch_dir}"}, ensure_ascii=False))
        return 1

    harvest = read_json(Path(args.harvest_file))
    if not harvest:
        print(json.dumps({"error": f"harvest file empty or missing: {args.harvest_file}"}, ensure_ascii=False))
        return 1

    paths = asset_paths(repo_dir, branch_dir)

    applied = {
        "repo_overview": _apply_entries(paths["repo_overview"], harvest.get("repo_overview")),
        "repo_context": _apply_entries(paths["repo_context"], harvest.get("repo_context")),
        "repo_sources": _apply_entries(paths["repo_sources"], harvest.get("repo_sources")),
    }
    total = sum(applied.values())

    branch_manifest = read_json(paths["manifest"])
    default_base = branch_manifest.get("default_base")
    git_log = []
    if default_base:
        git_log = git_lines(["log", "--oneline", f"{default_base}..HEAD"], cwd=repo_root, check=False)

    summary_md = build_archive_summary(branch_manifest, git_log, harvest_notes=harvest.get("notes"))
    summary_path = branch_dir / "archive_summary.md"
    summary_path.write_text(summary_md, encoding="utf-8")

    do_archive = harvest.get("archive", True)
    archive_dst = None
    if do_archive:
        date_tag = datetime.now(timezone.utc).strftime("%Y%m%d")
        archive_dst = archive_root_dir(repo_dir) / f"{branch_key}__{date_tag}"
        archive_branch_dir(branch_dir, archive_dst)
        head = branch_manifest.get("last_seen_head") or "<unknown>"
        notes_short = (harvest.get("notes") or "").splitlines()[0][:80] if harvest.get("notes") else ""
        index_line = f"- {date_tag[:4]}-{date_tag[4:6]}-{date_tag[6:8]} {branch_name} (HEAD {head}) → harvested {total} entries: {notes_short}"
        append_archive_index(archive_root_dir(repo_dir) / ARCHIVE_INDEX_NAME, index_line)

    print(json.dumps({
        "branch": branch_name,
        "harvested": applied,
        "harvested_total": total,
        "archive_summary": str((archive_dst or branch_dir) / "archive_summary.md"),
        "archived_to": str(archive_dst) if archive_dst else None,
    }, ensure_ascii=False, indent=2))
    return 0


def command_index(args):
    if detect_no_git_mode(args.repo):
        print(json.dumps({"error": "no-git mode: no archive index"}, ensure_ascii=False))
        return 1

    repo_root, _, _, _, _, repo_dir, _ = get_branch_paths(args.repo, args.context_dir, args.branch or "HEAD")
    index_path = archive_root_dir(repo_dir) / ARCHIVE_INDEX_NAME
    if not index_path.exists():
        print(json.dumps({"index_path": str(index_path), "exists": False, "entries": []}, ensure_ascii=False))
        return 0
    text = index_path.read_text(encoding="utf-8")
    entries = [line for line in text.splitlines() if line.startswith("- ")]
    print(json.dumps({
        "index_path": str(index_path),
        "exists": True,
        "entries": entries,
    }, ensure_ascii=False, indent=2))
    return 0


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", default=".", help="Path inside the target Git repository")
    common.add_argument("--context-dir", help="User-home storage root override")
    common.add_argument("--branch", help="Branch name override (defaults to current)")

    parser = argparse.ArgumentParser(description="Graduate a branch's dev-assets: harvest reusable knowledge, then archive.")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    p_dry = sub.add_parser("dry-run", parents=[common], help="Dump branch + repo sections for harvest review")
    p_dry.set_defaults(func=command_dry_run)

    p_apply = sub.add_parser("apply", parents=[common], help="Apply harvest patch and archive branch dir")
    p_apply.add_argument("--harvest-file", required=True, help="Path to harvest.json")
    p_apply.set_defaults(func=command_apply)

    p_idx = sub.add_parser("index", parents=[common], help="List archived branches")
    p_idx.set_defaults(func=command_index)

    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
