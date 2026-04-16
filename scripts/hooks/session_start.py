#!/usr/bin/env python3

import json
import sys

from _common import (
    build_session_start_context,
    build_workspace_start_context,
    is_workspace_mode,
    log,
)


def _resolve_context():
    if is_workspace_mode():
        ctx = build_workspace_start_context()
        if ctx:
            return ctx
        return "dev-assets workspace 模式：当前 workspace 下未发现已初始化的仓库记忆。"
    return build_session_start_context()


def main():
    try:
        additional_context = _resolve_context()
        payload = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": additional_context,
            }
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    except Exception as exc:
        log(f"[dev-assets][SessionStart] skipped: {exc}")
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": "dev-assets SessionStart hook 未能加载上下文，本轮按普通会话继续。",
                    }
                },
                ensure_ascii=False,
            )
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
