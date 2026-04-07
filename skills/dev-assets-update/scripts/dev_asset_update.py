#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[3] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from dev_asset_common import asset_paths, get_branch_paths, list_missing_docs, now_iso, read_json, write_json


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
        else:
            command_touch_manifest(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
