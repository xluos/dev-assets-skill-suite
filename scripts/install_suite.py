#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


def read_manifest(repo_root):
    manifest_path = repo_root / "suite-manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def ensure_symlink(target, source, force):
    if target.is_symlink() or target.exists():
        if not force:
            raise RuntimeError(f"target already exists: {target}")
        if target.is_dir() and not target.is_symlink():
            raise RuntimeError(f"refuse to replace real directory: {target}")
        target.unlink()
    target.symlink_to(source)


def main():
    parser = argparse.ArgumentParser(description="Install the dev asset skill suite.")
    parser.add_argument("--target", default=str(Path.home() / ".codex" / "skills"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--remove-legacy", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    manifest = read_manifest(repo_root)
    target_root = Path(args.target).expanduser().resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    installed = []
    for skill_name in manifest["skills"]:
        source = repo_root / "skills" / skill_name
        target = target_root / skill_name
        ensure_symlink(target, source, args.force)
        installed.append(str(target))

    if args.remove_legacy:
        for legacy_name in manifest.get("legacy_skills", []):
            legacy_target = target_root / legacy_name
            if legacy_target.is_symlink():
                legacy_target.unlink()

    print(
        json.dumps(
            {
                "target_root": str(target_root),
                "installed": installed,
                "removed_legacy": args.remove_legacy,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
