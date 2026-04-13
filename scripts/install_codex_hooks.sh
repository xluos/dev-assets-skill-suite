#!/bin/sh

set -eu

DEFAULT_TEMPLATE_URL="https://raw.githubusercontent.com/xluos/dev-asset-skill-suite/main/hooks/codex-hooks.json"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT="."
TEMPLATE_PATH=""
TEMPLATE_URL="$DEFAULT_TEMPLATE_URL"
PRINT_STDOUT="0"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      REPO_ROOT="$2"
      shift 2
      ;;
    --template)
      TEMPLATE_PATH="$2"
      shift 2
      ;;
    --template-url)
      TEMPLATE_URL="$2"
      shift 2
      ;;
    --stdout)
      PRINT_STDOUT="1"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: install_codex_hooks.sh [--repo PATH] [--template FILE] [--template-url URL] [--stdout]

Merge the suite's Codex hook template into the current directory's .codex/hooks.json.
EOF
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required to merge .codex/hooks.json" >&2
  exit 1
fi

export ECC_REPO_ROOT="$REPO_ROOT"
export ECC_TEMPLATE_PATH="$TEMPLATE_PATH"
export ECC_TEMPLATE_URL="$TEMPLATE_URL"
export ECC_PRINT_STDOUT="$PRINT_STDOUT"
export ECC_SCRIPT_DIR="$SCRIPT_DIR"

python3 - <<'PY'
import json
import os
import sys
import urllib.request
from pathlib import Path


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_template(template_path_raw, template_url):
    if template_path_raw:
        return load_json(Path(template_path_raw).expanduser().resolve())

    script_dir = Path(os.environ["ECC_SCRIPT_DIR"]).expanduser().resolve()
    script_path = script_dir / "install_codex_hooks.sh"
    if script_path.exists():
        repo_root = script_dir.parent
        local_template = repo_root / "hooks" / "codex-hooks.json"
        if local_template.exists():
            return load_json(local_template)

    with urllib.request.urlopen(template_url) as response:
        return json.loads(response.read().decode("utf-8"))


def merge_hook_lists(existing_items, incoming_items):
    merged = []
    index_by_key = {}

    for item in existing_items:
        copied = dict(item)
        merged.append(copied)
        key = (copied.get("id"), copied.get("matcher"))
        index_by_key[key] = len(merged) - 1

    for item in incoming_items:
        copied = dict(item)
        key = (copied.get("id"), copied.get("matcher"))
        if key in index_by_key:
            merged[index_by_key[key]] = copied
        else:
            index_by_key[key] = len(merged)
            merged.append(copied)

    return merged


def merge_hooks(existing_config, template_config):
    result = dict(existing_config)
    existing_hooks = existing_config.get("hooks") or {}
    template_hooks = template_config.get("hooks") or {}
    merged_hooks = {}

    for event_name in sorted(set(existing_hooks) | set(template_hooks)):
        existing_items = existing_hooks.get(event_name) or []
        template_items = template_hooks.get(event_name) or []
        merged_hooks[event_name] = merge_hook_lists(existing_items, template_items)

    result["hooks"] = merged_hooks
    return result


repo_root = Path(os.environ["ECC_REPO_ROOT"]).expanduser().resolve()
target_path = repo_root / ".codex" / "hooks.json"
template_config = load_template(os.environ["ECC_TEMPLATE_PATH"], os.environ["ECC_TEMPLATE_URL"])
existing_config = load_json(target_path) if target_path.exists() else {}
merged = merge_hooks(existing_config, template_config)

if os.environ["ECC_PRINT_STDOUT"] == "1":
    print(json.dumps(merged, ensure_ascii=False, indent=2))
    raise SystemExit(0)

target_path.parent.mkdir(parents=True, exist_ok=True)
target_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(
    json.dumps(
        {
            "repo_root": str(repo_root),
            "target": str(target_path),
            "merged_events": sorted((template_config.get("hooks") or {}).keys()),
        },
        ensure_ascii=False,
        indent=2,
    )
)
PY
