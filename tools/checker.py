#!/usr/bin/env python3
"""Independent check that a superstring contains every input string.

The checker does not trust the Lean executable. It only looks at the input
lines and the printed superstring.

Usage:
  python3 tools/checker.py INPUT SUPERSTRING_FILE
  python3 tools/checker.py INPUT -          # superstring on stdin
  veriscs INPUT | python3 tools/checker.py INPUT -

Exit status is 0 when every input line occurs as a contiguous substring.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lines import lines_of, read_lines


def read_superstring(source: str) -> str:
    if source == "-":
        text = sys.stdin.read()
    else:
        with Path(source).open("r", encoding="utf-8", newline="") as handle:
            text = handle.read()
    if text.endswith("\n"):
        text = text[:-1]
        if text.endswith("\r"):
            text = text[:-1]
    return text


def missing_strings(inputs: list[str], superstring: str) -> list[str]:
    return [s for s in inputs if s not in superstring]


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(
            "usage: python3 tools/checker.py INPUT SUPERSTRING_FILE\n"
            "       SUPERSTRING_FILE may be '-' to read standard input",
            file=sys.stderr,
        )
        return 2
    inputs = read_lines(argv[1])
    superstring = read_superstring(argv[2])
    missing = missing_strings(inputs, superstring)
    print(f"ok: {not missing}")
    print(f"strings: {len(inputs)}")
    print(f"symbol_length: {len(superstring)}")
    print(f"missing: {len(missing)}")
    for item in missing:
        shown = item if len(item) <= 80 else item[:77] + "..."
        print(f"missing_string: {shown!r}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
