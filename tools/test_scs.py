#!/usr/bin/env python3
"""Unit tests for the checker, line splitter, greedy merge, and exact DP."""

from __future__ import annotations

import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from checker import missing_strings
from lines import lines_of
from scs import brute_opt_length, exact_superstring, greedy_superstring, overlap


class LineTests(unittest.TestCase):
    def test_matches_lean_rules(self) -> None:
        self.assertEqual(lines_of(""), [])
        self.assertEqual(lines_of("a\n"), ["a"])
        self.assertEqual(lines_of("a\nb"), ["a", "b"])
        self.assertEqual(lines_of("a\n\n"), ["a", ""])
        self.assertEqual(lines_of("\n"), [""])
        self.assertEqual(lines_of("a\r\nb\r\n"), ["a", "b"])
        self.assertEqual(lines_of("α\nβ\n"), ["α", "β"])


class CheckerTests(unittest.TestCase):
    def test_contains(self) -> None:
        self.assertEqual(missing_strings(["ab", "bc"], "abc"), [])
        self.assertEqual(missing_strings(["ab", "zz"], "abc"), ["zz"])
        self.assertEqual(missing_strings([""], "abc"), [])

    def test_cli_roundtrip_file(self) -> None:
        checker = ROOT / "tools" / "checker.py"
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            inputs = folder / "in.txt"
            output = folder / "out.txt"
            inputs.write_text("ab\nbc\n", encoding="utf-8")
            output.write_text("xabcybc\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(checker), str(inputs), str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("ok: True", proc.stdout)
            self.assertIn("symbol_length: 7", proc.stdout)
            output.write_text("ab\n", encoding="utf-8")
            bad = subprocess.run(
                [sys.executable, str(checker), str(inputs), str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(bad.returncode, 1)
            self.assertIn("ok: False", bad.stdout)


class ScsTests(unittest.TestCase):
    def test_overlap(self) -> None:
        self.assertEqual(overlap("ab", "bc"), 1)
        self.assertEqual(overlap("abc", "bcd"), 2)
        self.assertEqual(overlap("abc", "xyz"), 0)
        self.assertEqual(overlap("abc", "abc"), 3)
        self.assertEqual(overlap("", "a"), 0)

    def test_known_optima(self) -> None:
        cases = [
            ([], 0),
            (["a"], 1),
            (["ab", "bc"], 3),
            (["ab", "ba"], 3),
            (["abc", "bc", "a"], 3),
            (["abc", "bcd", "cde"], 5),
            (["a", "b", "c"], 3),
            (["aa", "aa"], 2),
            (["ab", "bc", "ca"], 4),  # abca, or bcab, or cabc; not length 3
        ]
        for strings, length in cases:
            got = exact_superstring(strings)
            self.assertEqual(got.length, length, strings)
            self.assertEqual(missing_strings(strings, got.superstring), [], strings)
            self.assertLessEqual(len(greedy_superstring(strings)), 2 * length)
            self.assertEqual(missing_strings(strings, greedy_superstring(strings)), [])

    def test_dp_matches_brute(self) -> None:
        rng = random.Random(128)
        for _ in range(30):
            alphabet = "ab"
            count = rng.randint(1, 4)
            strings = [
                "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 4)))
                for _ in range(count)
            ]
            exact = exact_superstring(strings)
            self.assertEqual(missing_strings(strings, exact.superstring), [], strings)
            brute = brute_opt_length(strings)
            if brute is not None:
                self.assertEqual(exact.length, brute, strings)


if __name__ == "__main__":
    unittest.main()
