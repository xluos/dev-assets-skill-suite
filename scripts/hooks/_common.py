#!/usr/bin/env python3

import json
import os
import re
import subprocess
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(os.environ.get("DEV_ASSETS_HOOK_REPO_ROOT", ".")).expanduser().resolve()
LIB_ROOT = PACKAGE_ROOT / "lib"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from dev_asset_common import AUTO_END, AUTO_START, PLACEHOLDER_MARKERS, asset_paths, get_branch_paths


CONTEXT_SCRIPT = PACKAGE_ROOT / "skills" / "dev-assets-context" / "scripts" / "dev_asset_context.py"
SYNC_SCRIPT = PACKAGE_ROOT / "skills" / "dev-assets-sync" / "scripts" / "dev_asset_sync.py"


def run_python(script_path, *args):
    result = subprocess.run(
        ["python3", str(script_path), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"command failed: {script_path}")
    return result.stdout.strip()


def log(message):
    print(message, file=sys.stderr)


def resolve_assets():
    repo_root, branch_name, branch_key, storage_root, repo_key, repo_dir, branch_dir = get_branch_paths(str(REPO_ROOT))
    return {
        "repo_root": repo_root,
        "branch_name": branch_name,
        "branch_key": branch_key,
        "storage_root": storage_root,
        "repo_key": repo_key,
        "repo_dir": repo_dir,
        "branch_dir": branch_dir,
        "paths": asset_paths(repo_dir, branch_dir),
    }


def strip_managed_markers(text):
    return text.replace(AUTO_START, "").replace(AUTO_END, "").replace("_尚未同步_", "").strip()


def is_placeholder(text):
    stripped = strip_managed_markers(text)
    if not stripped:
        return True
    return any(marker in stripped for marker in PLACEHOLDER_MARKERS)


def extract_section(path, title):
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(title)}\n\n(.*?)(?=^## |\Z)", content, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return None
    body = strip_managed_markers(match.group(1)).strip()
    return None if is_placeholder(body) else body


def compact_body(text, max_lines=8, max_chars=700):
    normalized = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    lines = [line for line in normalized.splitlines() if line.strip()]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if not lines[-1].endswith("..."):
            lines.append("...")
    compacted = "\n".join(lines)
    if len(compacted) > max_chars:
        compacted = compacted[: max_chars - 3].rstrip() + "..."
    return compacted


def maybe_sync_context():
    return json.loads(run_python(CONTEXT_SCRIPT, "sync", "--repo", str(REPO_ROOT)))


def maybe_sync_working_tree():
    return json.loads(run_python(SYNC_SCRIPT, "sync-working-tree", "--repo", str(REPO_ROOT)))


def maybe_record_head():
    return json.loads(run_python(SYNC_SCRIPT, "record-head", "--repo", str(REPO_ROOT)))


def build_session_start_context():
    assets = resolve_assets()
    if not assets["branch_dir"].exists():
        return (
            "当前仓库尚未初始化 dev-assets 分支记忆。\n"
            "如果这是需要跨会话继续的开发线，请先使用 `dev-assets-setup` 建立 repo+branch 存储。"
        )

    try:
        maybe_sync_context()
    except Exception as exc:
        log(f"[dev-assets][SessionStart] refresh skipped: {exc}")

    paths = assets["paths"]
    sections = [
        ("当前目标", extract_section(paths["overview"], "当前目标")),
        ("范围边界", extract_section(paths["overview"], "范围边界")),
        ("当前阶段", extract_section(paths["overview"], "当前阶段")),
        ("关键约束", extract_section(paths["overview"], "关键约束")),
        ("建议优先查看的目录", extract_section(paths["development"], "建议优先查看的目录")),
        ("当前进展", extract_section(paths["development"], "当前进展")),
        ("阻塞与注意点", extract_section(paths["development"], "阻塞与注意点")),
        ("下一步", extract_section(paths["development"], "下一步")),
        ("当前有效上下文", extract_section(paths["context"], "当前有效上下文")),
        ("关键决策与原因", extract_section(paths["context"], "关键决策与原因")),
        ("后续继续前要注意", extract_section(paths["context"], "后续继续前要注意")),
        ("仓库级长期目标与边界", extract_section(paths["repo_overview"], "长期目标与边界")),
        ("仓库级关键约束", extract_section(paths["repo_overview"], "仓库级关键约束")),
        ("共享入口", extract_section(paths["repo_sources"], "共享入口")),
    ]

    parts = [
        f"已加载 dev-assets：repo `{assets['repo_key']}`，branch `{assets['branch_name']}`。",
        f"主存储目录：`{assets['branch_dir']}`",
    ]
    for title, body in sections:
        if body:
            parts.append(f"{title}:\n{compact_body(body)}")
    return "\n\n".join(parts)
