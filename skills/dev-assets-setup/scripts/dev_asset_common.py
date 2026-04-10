#!/usr/bin/env python3

import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_CONTEXT_DIR = ".dev-assets"
AUTO_START = "<!-- AUTO-GENERATED-START -->"
AUTO_END = "<!-- AUTO-GENERATED-END -->"
PLACEHOLDER_MARKERS = ("待补充", "待刷新", "_尚未同步_")
MANAGED_FILES = (
    "manifest.json",
    "overview.md",
    "development.md",
    "context.md",
    "sources.md",
)
FOCUS_PREFIXES = {"skills", "src", "apps", "packages", "services"}


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_git(args, cwd, check=True):
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result


def git_stdout(args, cwd, check=True):
    return run_git(args, cwd, check=check).stdout.strip()


def git_lines(args, cwd, check=True):
    result = run_git(args, cwd, check=check)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def detect_repo_root(repo):
    return Path(git_stdout(["rev-parse", "--show-toplevel"], cwd=repo))


def detect_branch(repo_root):
    branch = git_stdout(["branch", "--show-current"], cwd=repo_root)
    if not branch:
        raise RuntimeError("current HEAD is detached; pass --branch explicitly")
    return branch


def sanitize_branch_name(branch_name):
    cleaned = branch_name.strip().replace("/", "__")
    cleaned = cleaned.replace(" ", "-")
    if not cleaned:
        raise ValueError("branch name is empty")
    return cleaned


def ensure_local_exclude(repo_root, context_dir):
    exclude_path = Path(repo_root) / ".git" / "info" / "exclude"
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    entry = f"{context_dir}/"
    if entry not in {line.strip() for line in existing.splitlines()}:
        with exclude_path.open("a", encoding="utf-8") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write(f"{entry}\n")


def set_repo_config(repo_root, context_dir):
    run_git(["config", "--local", "dev-assets.dir", context_dir], cwd=repo_root)


def get_context_dir(repo_root, explicit_value=None):
    if explicit_value:
        return explicit_value
    configured = run_git(["config", "--get", "dev-assets.dir"], cwd=repo_root, check=False)
    value = configured.stdout.strip()
    return value or DEFAULT_CONTEXT_DIR


def normalize_context_dir(context_dir, branch_name, branch_key):
    parts = list(Path(context_dir).parts)
    branch_parts = list(Path(branch_name).parts)

    if branch_parts and len(parts) >= len(branch_parts) and parts[-len(branch_parts) :] == branch_parts:
        parts = parts[: -len(branch_parts)]
    if parts and parts[-1] == branch_key:
        parts = parts[:-1]

    if not parts:
        return DEFAULT_CONTEXT_DIR
    return Path(*parts).as_posix()


def resolve_branch_dir(repo_root, raw_context_dir, resolved_context_dir, branch_name, branch_key):
    candidates = [
        repo_root / resolved_context_dir / branch_key,
        repo_root / resolved_context_dir / Path(branch_name),
    ]
    if raw_context_dir != resolved_context_dir:
        candidates.extend(
            [
                repo_root / raw_context_dir / branch_key,
                repo_root / raw_context_dir / Path(branch_name),
            ]
        )

    seen = set()
    for candidate in candidates:
        key = candidate.as_posix()
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return candidate
    return candidates[0]


def get_branch_paths(repo, context_dir=None, branch=None):
    repo_root = detect_repo_root(repo)
    branch_name = branch or detect_branch(repo_root)
    branch_key = sanitize_branch_name(branch_name)
    raw_context_dir = get_context_dir(repo_root, context_dir)
    resolved_context_dir = normalize_context_dir(raw_context_dir, branch_name, branch_key)
    if not context_dir and resolved_context_dir != raw_context_dir:
        set_repo_config(repo_root, resolved_context_dir)
    branch_dir = resolve_branch_dir(repo_root, raw_context_dir, resolved_context_dir, branch_name, branch_key)
    return repo_root, branch_name, branch_key, resolved_context_dir, branch_dir


def asset_paths(branch_dir):
    return {
        "manifest": branch_dir / "manifest.json",
        "overview": branch_dir / "overview.md",
        "development": branch_dir / "development.md",
        "context": branch_dir / "context.md",
        "sources": branch_dir / "sources.md",
        "artifacts": branch_dir / "artifacts",
        "history": branch_dir / "artifacts" / "history",
    }


def ensure_file(path, content):
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def render_bullets(items, empty_text="- 待补充", wrap_code=False):
    normalized = [str(item).strip() for item in (items or []) if str(item).strip()]
    if not normalized:
        return empty_text
    lines = []
    for item in normalized:
        if wrap_code and not (item.startswith("`") and item.endswith("`")):
            item = f"`{item}`"
        lines.append(f"- {item}")
    return "\n".join(lines)


def render_title_doc(doc_title, sections, intro=None):
    parts = [f"# {doc_title}"]
    if intro:
        parts.extend(["", intro.strip()])
    for title, body in sections:
        parts.extend(["", f"## {title}", "", body.strip()])
    return "\n".join(parts).rstrip() + "\n"


def template_overview(branch_name):
    return render_title_doc(
        "概览",
        [
            ("分支", f"- {branch_name}"),
            ("当前目标", "- 待补充"),
            ("范围边界", "- 待补充"),
            ("当前阶段", "- 待补充"),
            ("关键约束", "- 待补充"),
        ],
    )


def template_development(branch_name):
    return render_title_doc(
        "当前开发状态",
        [
            ("分支", f"- {branch_name}"),
            ("建议优先查看的目录", "- 待刷新"),
            ("当前进展", "- 待补充"),
            ("阻塞与注意点", "- 待补充"),
            ("下一步", "- 待补充"),
            (
                "自动同步区",
                "本区由 `dev-assets-context` 或 `dev-assets-sync` 刷新，请不要手工编辑。\n\n"
                f"{AUTO_START}\n"
                "_尚未同步_\n"
                f"{AUTO_END}",
            ),
        ],
    )


def template_context():
    return render_title_doc(
        "分支上下文",
        [
            ("当前有效上下文", "- 待补充"),
            ("关键决策与原因", "- 待补充"),
            ("后续继续前要注意", "- 待补充"),
        ]
    )


def template_sources():
    return render_title_doc(
        "源资料索引",
        [
            ("优先阅读", "- 待补充"),
            (
                "提交与代码历史",
                "- 需要了解本分支改动时，优先使用 `git log --oneline <base>..HEAD`\n"
                "- 需要查看某次提交细节时，使用 `git show <sha>`",
            ),
        ],
    )


def build_manifest(repo_root, branch_name, branch_key, context_dir):
    return {
        "schema_version": 2,
        "repo_root": str(repo_root),
        "branch": branch_name,
        "branch_key": branch_key,
        "context_dir": context_dir,
        "initialized_at": now_iso(),
        "updated_at": now_iso(),
        "last_seen_head": None,
        "default_base": None,
        "scope_summary": [],
        "focus_areas": [],
    }


def initialize_assets(repo_root, branch_name, branch_key, context_dir, branch_dir):
    branch_dir.mkdir(parents=True, exist_ok=True)
    ensure_local_exclude(repo_root, context_dir)
    set_repo_config(repo_root, context_dir)

    paths = asset_paths(branch_dir)
    paths["artifacts"].mkdir(exist_ok=True)
    paths["history"].mkdir(parents=True, exist_ok=True)

    if not paths["manifest"].exists():
        write_json(paths["manifest"], build_manifest(repo_root, branch_name, branch_key, context_dir))
    ensure_file(paths["overview"], template_overview(branch_name))
    ensure_file(paths["development"], template_development(branch_name))
    ensure_file(paths["context"], template_context())
    ensure_file(paths["sources"], template_sources())
    return paths


def detect_default_base(repo_root):
    symbolic = run_git(["symbolic-ref", "refs/remotes/origin/HEAD"], cwd=repo_root, check=False)
    ref = symbolic.stdout.strip()
    if symbolic.returncode == 0 and ref:
        return ref.replace("refs/remotes/", "", 1)
    for candidate in ("origin/main", "origin/master"):
        probe = run_git(["rev-parse", "--verify", candidate], cwd=repo_root, check=False)
        if probe.returncode == 0:
            return candidate
    return None


def top_level_scope(path_str):
    parts = Path(path_str).parts
    return parts[0] if parts else "."


def focus_area(path_str):
    parts = Path(path_str).parts
    if not parts:
        return "."
    if parts[0] in FOCUS_PREFIXES and len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


def summarize_scopes(paths):
    counter = Counter(top_level_scope(path) for path in paths)
    return [{"scope": scope, "files": count} for scope, count in sorted(counter.items())]


def summarize_focus_areas(paths, limit=5):
    counter = Counter(focus_area(path) for path in paths)
    ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return [scope for scope, _ in ranked[:limit]]


def collect_git_facts(repo_root, branch_name, context_dir):
    context_prefix = f"{context_dir}/"
    working_tree_files = [
        path for path in git_lines(["diff", "--name-only"], cwd=repo_root) if not path.startswith(context_prefix)
    ]
    staged_files = [
        path for path in git_lines(["diff", "--cached", "--name-only"], cwd=repo_root) if not path.startswith(context_prefix)
    ]
    untracked_files = [
        path
        for path in git_lines(["ls-files", "--others", "--exclude-standard"], cwd=repo_root)
        if not path.startswith(context_prefix)
    ]

    default_base = detect_default_base(repo_root)
    since_base_files = []
    if default_base:
        merge_base = git_lines(["merge-base", "HEAD", default_base], cwd=repo_root)
        if merge_base:
            since_base_files = [
                path
                for path in git_lines(["diff", "--name-only", f"{merge_base[0]}...HEAD"], cwd=repo_root)
                if not path.startswith(context_prefix)
            ]

    all_paths = sorted(set(working_tree_files + staged_files + untracked_files + since_base_files))
    return {
        "branch": branch_name,
        "default_base": default_base,
        "last_seen_head": get_head_commit(repo_root),
        "working_tree_files": working_tree_files,
        "staged_files": staged_files,
        "untracked_files": untracked_files,
        "since_base_files": since_base_files,
        "scope_summary": summarize_scopes(all_paths),
        "focus_areas": summarize_focus_areas(all_paths),
        "updated_at": now_iso(),
    }


def build_auto_block(facts):
    base_line = facts["default_base"] or "未检测到 origin/HEAD"
    head_line = facts["last_seen_head"] or "尚未检测到 HEAD"
    focus_lines = render_bullets(facts["focus_areas"], empty_text="- 当前未检测到改动目录", wrap_code=True)
    scope_lines = render_bullets(
        [f"{item['scope']} ({item['files']} files)" for item in facts["scope_summary"]],
        empty_text="- 当前未检测到改动范围",
    )
    history_hint = (
        f"- `git log --oneline {facts['default_base']}..HEAD`"
        if facts["default_base"]
        else "- `git log --oneline --decorate -n 20`"
    )
    return (
        "### 自动生成\n\n"
        f"- 更新时间: {facts['updated_at']}\n"
        f"- 当前分支: {facts['branch']}\n"
        f"- 默认基线分支: {base_line}\n"
        f"- 当前 HEAD: {head_line}\n\n"
        "#### 建议优先查看的目录\n\n"
        f"{focus_lines}\n\n"
        "#### 顶层改动范围\n\n"
        f"{scope_lines}\n\n"
        "#### 按需查看提交历史\n\n"
        f"{history_hint}\n"
        "- `git diff --name-only`\n"
    )


def ensure_development_auto_block(path):
    content = path.read_text(encoding="utf-8")
    if AUTO_START in content and AUTO_END in content:
        return content

    marker = "## 自动同步区"
    auto_section = (
        f"\n\n{marker}\n\n"
        "本区由 `dev-assets-context` 或 `dev-assets-sync` 刷新，请不要手工编辑。\n\n"
        f"{AUTO_START}\n"
        "_尚未同步_\n"
        f"{AUTO_END}\n"
    )

    if marker in content:
        before, _ = content.split(marker, 1)
        updated = before.rstrip() + auto_section
    else:
        updated = content.rstrip() + auto_section

    path.write_text(updated + ("" if updated.endswith("\n") else "\n"), encoding="utf-8")
    return path.read_text(encoding="utf-8")


def replace_auto_block(content, replacement):
    if AUTO_START not in content or AUTO_END not in content:
        raise RuntimeError("development.md is missing auto-generated markers")
    before, remainder = content.split(AUTO_START, 1)
    _, after = remainder.split(AUTO_END, 1)
    return f"{before}{AUTO_START}\n{replacement.rstrip()}\n{AUTO_END}{after}"


def split_sections(content):
    positions = list(re.finditer(r"^## (.+?)\n", content, re.M))
    if not positions:
        return content.rstrip(), []

    prefix = content[: positions[0].start()].rstrip()
    sections = []
    for index, match in enumerate(positions):
        start = match.start()
        end = positions[index + 1].start() if index + 1 < len(positions) else len(content)
        title = match.group(1).strip()
        body = content[match.end() : end].strip()
        sections.append((title, body))
    return prefix, sections


def join_sections(prefix, sections):
    parts = []
    prefix = prefix.rstrip()
    if prefix:
        parts.append(prefix)
    for title, body in sections:
        parts.append(f"## {title}\n\n{body.strip()}")
    return "\n\n".join(parts).rstrip() + "\n"


def upsert_markdown_section(path, title, body):
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    prefix, sections = split_sections(content)
    updated = []
    replaced = False
    for existing_title, existing_body in sections:
        if existing_title == title:
            updated.append((title, body))
            replaced = True
        else:
            updated.append((existing_title, existing_body))
    if not replaced:
        updated.append((title, body))
    path.write_text(join_sections(prefix, updated), encoding="utf-8")


def upsert_development_section(path, title, body):
    content = ensure_development_auto_block(path)
    marker = "## 自动同步区"
    if marker not in content:
        raise RuntimeError("development.md is missing the auto-sync section heading")
    before, after = content.split(marker, 1)
    prefix, sections = split_sections(before.rstrip())
    updated = []
    replaced = False
    for existing_title, existing_body in sections:
        if existing_title == title:
            updated.append((title, body))
            replaced = True
        else:
            updated.append((existing_title, existing_body))
    if not replaced:
        updated.append((title, body))
    rewritten = join_sections(prefix, updated).rstrip() + "\n\n" + marker + after
    path.write_text(rewritten, encoding="utf-8")


def sync_development(paths, facts):
    upsert_development_section(
        paths["development"],
        "建议优先查看的目录",
        render_bullets(facts["focus_areas"], empty_text="- 当前未检测到改动目录", wrap_code=True),
    )
    current = ensure_development_auto_block(paths["development"])
    updated = replace_auto_block(current, build_auto_block(facts))
    paths["development"].write_text(updated, encoding="utf-8")


def list_missing_docs(paths):
    missing = []
    for key, path in paths.items():
        if key in {"manifest", "artifacts", "history"}:
            continue
        if not path.exists():
            missing.append(key)
            continue
        content = path.read_text(encoding="utf-8")
        if any(marker in content for marker in PLACEHOLDER_MARKERS):
            missing.append(key)
    return missing


def get_head_commit(repo_root):
    sha = git_stdout(["rev-parse", "HEAD"], cwd=repo_root, check=False)
    return sha or None
