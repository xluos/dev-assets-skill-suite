#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

from dev_asset_common import (
    append_development_section,
    append_markdown_section,
    asset_paths,
    get_branch_paths,
    list_missing_docs,
    now_iso,
    read_json,
    write_json,
)


SECTION_TITLE_MAP = {
    "overview": "补充记录",
    "prd": "需求补充",
    "review_notes": "评审补充",
    "frontend_design": "前端补充",
    "backend_design": "后端补充",
    "test_cases": "测试补充",
    "development": "开发补充",
    "decision_log": "决策补充",
}

KIND_MAP = {
    "summary": {
        "targets": ["overview", "development"],
        "reason": "高层摘要变化通常要同步到 overview，必要时在 development 留当前实现说明。",
    },
    "prd": {
        "targets": ["prd", "overview"],
        "reason": "需求背景、目标范围、验收口径优先进入 prd，必要时回写概览。",
    },
    "review": {
        "targets": ["review_notes", "decision_log"],
        "reason": "评审结论与争议点写入 review-notes，长期有效的结论可同步到 decision-log。",
    },
    "frontend": {
        "targets": ["frontend_design", "development"],
        "reason": "前端实现方案优先进入 frontend-design，当前阶段补充可落到 development。",
    },
    "backend": {
        "targets": ["backend_design", "development"],
        "reason": "后端接口与兼容性优先进入 backend-design，当前阶段说明可补到 development。",
    },
    "test": {
        "targets": ["test_cases", "overview"],
        "reason": "测试口径和回归范围进入 test-cases，若影响整体验收认知可同步到 overview。",
    },
    "development": {
        "targets": ["development"],
        "reason": "实现备注、当前需求点、临时阻塞优先写入 development。",
    },
    "decision": {
        "targets": ["decision_log", "overview"],
        "reason": "会被反复引用的结论或取舍应进入 decision-log，必要时更新概览。",
    },
    "risk": {
        "targets": ["development", "decision_log"],
        "reason": "当前阻塞和风险先写 development，若形成明确约束再写 decision-log。",
    },
    "constraint": {
        "targets": ["decision_log", "backend_design", "frontend_design"],
        "reason": "明确限制条件优先写 decision-log，再按影响范围补到前后端方案。",
    },
    "link": {
        "targets": ["overview", "prd", "review_notes", "frontend_design", "backend_design", "test_cases"],
        "reason": "链接应放到与内容最相关的文档，不建议集中堆放在单独文件中。",
    },
}


def normalize_body(text):
    stripped = text.strip()
    if not stripped:
        raise RuntimeError("content is empty")
    return stripped


def load_optional_text(value, file_path=None):
    if value:
        return normalize_body(value)
    if file_path:
        return normalize_body(Path(file_path).read_text(encoding="utf-8"))
    return None


def load_content(args):
    inline_content = load_optional_text(args.content, args.content_file)
    session_summary = load_optional_text(args.summary, args.summary_file)
    user_input = load_optional_text(args.user_input, args.user_input_file)

    if session_summary or user_input:
        sections = []
        if user_input:
            sections.append("### 用户这次输入\n\n" + user_input)
        if session_summary:
            sections.append("### 基于当前会话整理\n\n" + session_summary)
        if inline_content:
            sections.append("### 补充备注\n\n" + inline_content)
        return "\n\n".join(sections), "session+input"

    if inline_content:
        return inline_content, "content-only"

    raise RuntimeError(
        "one of --content/--content-file or --summary/--summary-file or --user-input/--user-input-file is required"
    )


def resolve_targets(kind):
    payload = KIND_MAP.get(kind)
    if not payload:
        raise RuntimeError(f"unsupported kind: {kind}")
    return payload["targets"]


def append_to_target(path, target_key, title, content):
    if target_key == "development":
        append_development_section(path, title, content)
    else:
        append_markdown_section(path, title, content)


def command_show(args):
    repo_root, branch_name, branch_key, resolved_context_dir, branch_dir = get_branch_paths(
        args.repo, args.context_dir, args.branch
    )
    if not branch_dir.exists():
        raise RuntimeError(f"asset directory does not exist: {branch_dir}. Run dev-assets-setup first.")

    paths = asset_paths(branch_dir)
    print(
        json.dumps(
            {
                "repo_root": str(repo_root),
                "branch": branch_name,
                "branch_key": branch_key,
                "context_dir": resolved_context_dir,
                "branch_dir": str(branch_dir),
                "files": {key: str(value) for key, value in paths.items()},
                "missing_or_placeholder": list_missing_docs(paths),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def command_suggest_target(args):
    kind = args.kind.lower()
    if kind not in KIND_MAP:
        raise RuntimeError(f"unsupported kind: {args.kind}")
    payload = KIND_MAP[kind]
    print(json.dumps({"kind": kind, **payload}, ensure_ascii=False, indent=2))


def command_write(args):
    repo_root, branch_name, branch_key, resolved_context_dir, branch_dir = get_branch_paths(
        args.repo, args.context_dir, args.branch
    )
    if not branch_dir.exists():
        raise RuntimeError(f"asset directory does not exist: {branch_dir}. Run dev-assets-setup first.")

    kind = args.kind.lower()
    targets = resolve_targets(kind)
    paths = asset_paths(branch_dir)
    title = (args.title or SECTION_TITLE_MAP.get(targets[0]) or "补充记录").strip()
    content, update_mode = load_content(args)

    touched = []
    for target_key in targets:
        append_to_target(paths[target_key], target_key, title, content)
        touched.append(paths[target_key].name)

    manifest = read_json(paths["manifest"])
    manifest.update(
        {
            "repo_root": str(repo_root),
            "branch": branch_name,
            "branch_key": branch_key,
            "context_dir": resolved_context_dir,
            "updated_at": now_iso(),
            "last_update_kind": kind,
            "last_update_title": title,
            "last_update_mode": update_mode,
        }
    )
    write_json(paths["manifest"], manifest)

    print(
        json.dumps(
            {
                "repo_root": str(repo_root),
                "branch": branch_name,
                "context_dir": resolved_context_dir,
                "branch_dir": str(branch_dir),
                "mode": "write",
                "update_mode": update_mode,
                "kind": kind,
                "title": title,
                "touched_files": touched,
                "updated_at": manifest["updated_at"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def command_touch_manifest(args):
    repo_root, branch_name, branch_key, resolved_context_dir, branch_dir = get_branch_paths(
        args.repo, args.context_dir, args.branch
    )
    if not branch_dir.exists():
        raise RuntimeError(f"asset directory does not exist: {branch_dir}. Run dev-assets-setup first.")

    paths = asset_paths(branch_dir)
    manifest = read_json(paths["manifest"])
    manifest.update(
        {
            "repo_root": str(repo_root),
            "branch": branch_name,
            "branch_key": branch_key,
            "context_dir": resolved_context_dir,
            "updated_at": now_iso(),
        }
    )
    write_json(paths["manifest"], manifest)
    print(
        json.dumps(
            {
                "repo_root": str(repo_root),
                "branch": branch_name,
                "context_dir": resolved_context_dir,
                "branch_dir": str(branch_dir),
                "mode": "touch-manifest",
                "updated_at": manifest["updated_at"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser(description="Update branch-scoped development asset documents.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    show = subparsers.add_parser("show")
    show.add_argument("--repo", default=".", help="Path inside the target Git repository")
    show.add_argument("--context-dir", help="Repository-local storage root")
    show.add_argument("--branch", help="Branch name. Defaults to the current checked-out branch")

    suggest = subparsers.add_parser("suggest-target")
    suggest.add_argument("--kind", required=True, help="Update kind to classify")

    write = subparsers.add_parser("write")
    write.add_argument("--repo", default=".", help="Path inside the target Git repository")
    write.add_argument("--context-dir", help="Repository-local storage root")
    write.add_argument("--branch", help="Branch name. Defaults to the current checked-out branch")
    write.add_argument("--kind", required=True, help="Update kind to classify")
    write.add_argument("--title", help="Section title to append")
    write.add_argument("--content", help="Inline markdown content to append")
    write.add_argument("--content-file", help="Markdown content file to append")
    write.add_argument("--summary", help="Session-derived summary to store")
    write.add_argument("--summary-file", help="File containing a session-derived summary")
    write.add_argument("--user-input", help="Latest user input to store alongside the summary")
    write.add_argument("--user-input-file", help="File containing the latest user input")

    touch = subparsers.add_parser("touch-manifest")
    touch.add_argument("--repo", default=".", help="Path inside the target Git repository")
    touch.add_argument("--context-dir", help="Repository-local storage root")
    touch.add_argument("--branch", help="Branch name. Defaults to the current checked-out branch")

    args = parser.parse_args()
    try:
        if args.command == "show":
            command_show(args)
        elif args.command == "suggest-target":
            command_suggest_target(args)
        elif args.command == "write":
            command_write(args)
        else:
            command_touch_manifest(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
