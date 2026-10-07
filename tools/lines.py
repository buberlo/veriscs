"""Line splitting shared by the checker and the benchmark.

This matches `linesOf` in `VeriSCS/CLI.lean`: split on `\\n` only, strip one
trailing `\\r` from each line, and drop a final empty line that exists only
because the file ends with a newline. Empty lines in the middle are kept.
"""

from __future__ import annotations


def lines_of(text: str) -> list[str]:
    raw = text.split("\n")
    raw = [line[:-1] if line.endswith("\r") else line for line in raw]
    if raw and raw[-1] == "":
        raw = raw[:-1]
    return raw


def read_lines(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return lines_of(handle.read())
