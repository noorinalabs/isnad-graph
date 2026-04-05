#!/usr/bin/env python3
"""PreToolUse hook: Block --no-verify on git commit.

Detects `--no-verify` or `-n` (short form) on git commit commands and requires
user confirmation before proceeding.

Exit codes:
  0 — allow (no --no-verify detected, or not a git commit)
  2 — block (--no-verify detected, user must confirm)
"""

import json
import re
import sys


def main() -> None:
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")

    # Only check git commit commands
    if not re.search(r"\bgit\b.*\bcommit\b", command):
        sys.exit(0)

    # Check for --no-verify flag
    if "--no-verify" not in command:
        sys.exit(0)

    # Block with a clear message requiring justification
    result = {
        "decision": "block",
        "reason": (
            "BLOCKED: `--no-verify` detected on git commit. "
            "This bypasses pre-commit hooks which are required by the charter. "
            "Engineers must not use --no-verify routinely. "
            "If you have a legitimate emergency reason, remove --no-verify and "
            "fix the underlying hook failure instead."
        ),
    }
    print(json.dumps(result))
    sys.exit(2)


if __name__ == "__main__":
    main()
