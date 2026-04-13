#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT="."
PACKAGE_SPEC=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      REPO_ROOT="$2"
      shift 2
      ;;
    --package)
      PACKAGE_SPEC="$2"
      shift 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage: install_codex_hooks.sh [--repo PATH] [--package SPEC]

Install the dev-assets CLI into the target repository and merge Codex hooks.
EOF
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: npm is required" >&2
  exit 1
fi

TARGET_REPO=$(cd "$REPO_ROOT" && pwd)

if [ -z "$PACKAGE_SPEC" ]; then
  if [ -f "$SCRIPT_DIR/../package.json" ]; then
    PACKAGE_SPEC="file:$SCRIPT_DIR/.."
  else
    PACKAGE_SPEC="@xluos/dev-assets-cli"
  fi
fi

(
  cd "$TARGET_REPO"
  npm install --save-dev "$PACKAGE_SPEC"
  npx dev-assets install-hooks codex --repo "$TARGET_REPO"
)
