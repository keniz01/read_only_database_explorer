#!/usr/bin/env python3
"""
Run Ruff only on changed lines of staged Python files.

Usage (pre-commit):
    entry: python .pre-commit-scripts/ruff-diff-check.py
"""

import json
import subprocess
import sys


def get_changed_lines(filename: str) -> set[int]:
    """Return a set of changed line numbers for the given file based on the staged diff."""
    try:
        diff = subprocess.check_output(  # noqa: S603 - filename is argv-controlled git input
            ["git", "diff", "--cached", "-U0", "--", filename],  # noqa: S607 - git must come from PATH
            text=True,
        )
    except subprocess.CalledProcessError:
        return set()

    changed = set()
    for line in diff.splitlines():
        # Hunk header example: @@ -10,0 +11,3 @@
        if line.startswith("@@"):
            try:
                hunk = line.split(" ")[2]  # +11,3
                start, length = hunk[1:].split(",")
                start, length = int(start), int(length)
                for i in range(start, start + length):
                    changed.add(i)
            except Exception:  # noqa: S110 - best-effort hunk parsing; skip malformed headers
                pass

    return changed


def main(filenames: list[str]) -> int:
    """Run Ruff on provided filenames and filter results to changed lines only."""
    # Run Ruff and request JSON output for easy filtering
    try:
        ruff_output = subprocess.check_output(  # noqa: S603 - filenames are argv-controlled
            ["ruff", "check", "--output-format=json", "--force-exclude", *filenames],  # noqa: S607 - ruff must come from PATH
            text=True,
        )
    except subprocess.CalledProcessError as e:
        # Ruff exits nonzero on findings — still captures output
        ruff_output = e.output

    if not ruff_output.strip():
        return 0

    try:
        problems = json.loads(ruff_output)
    except json.JSONDecodeError:
        print("Error: Could not parse Ruff JSON output.")  # noqa: T201 - CLI output
        print(ruff_output)  # noqa: T201 - CLI output
        return 1

    # Build map of changed lines per file
    changed_map = {f: get_changed_lines(f) for f in filenames}

    violations = []
    for p in problems:
        filename = p.get("filename")
        line = p.get("location", {}).get("row")

        if filename in changed_map and line in changed_map[filename]:
            violations.append(p)

    # Output violations (if any)
    if violations:
        print("Ruff found issues in changed lines only:")  # noqa: T201 - CLI output
        print(json.dumps(violations, indent=2))  # noqa: T201 - CLI output
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
