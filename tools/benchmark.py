#!/usr/bin/env python3
"""Compare the verified executable with greedy merge and exact optimum.

Writes a Markdown report. Instances that exceed the time limit are recorded
as timeouts; those rows are measurements, not estimates.

Usage:
  python3 tools/benchmark.py --bin .lake/build/bin/veriscs --out BENCHMARK.md
  python3 tools/benchmark.py --skip-veriscs --out /tmp/baselines.md
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from checker import missing_strings
from lines import lines_of
from scs import exact_superstring, greedy_superstring


@dataclass
class Row:
    name: str
    n: int
    symbols_in: int
    max_len: int
    veriscs_len: str
    veriscs_sec: str
    veriscs_rss_kib: str
    veriscs_ok: str
    greedy_len: int
    greedy_sec: float
    opt_len: str
    exact_sec: str
    ratio: str
    note: str


def write_instance(directory: Path, name: str, lines: list[str]) -> Path:
    path = directory / f"{name}.txt"
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    return path


def generated_instances(directory: Path) -> list[tuple[str, str, Path, list[str]]]:
    """Return (family, name, path, lines). A timeout stops only that family."""
    specs: list[tuple[str, str, list[str]]] = [
        ("named", "empty", []),
        ("named", "one", ["a"]),
        ("named", "ab_bc", ["ab", "bc"]),
        ("named", "ab_ba", ["ab", "ba"]),
        ("named", "contained", ["abc", "bc", "a"]),
        ("named", "chain3", ["abc", "bcd", "cde"]),
        ("named", "three_letters", ["a", "b", "c"]),
        ("named", "overlap_cycle", ["ab", "bc", "ca"]),
        ("named", "duplicates", ["aa", "aa", "a"]),
        ("named", "unicode", ["αβ", "βγ", "γα"]),
    ]
    for length in (1, 2, 3, 4, 5, 6, 8):
        left = ("ab" * ((length + 1) // 2))[:length]
        right = ("ba" * ((length + 1) // 2))[:length]
        specs.append(("pair", f"pair_L{length}", [left, right]))
    for count in (2, 3, 4, 5, 6, 8):
        specs.append(("letters", f"distinct_{count}", [chr(ord("a") + i) for i in range(count)]))
    for count in (2, 3, 4, 5):
        specs.append(
            ("words", f"words_{count}", [f"x{chr(ord('a') + i)}y" for i in range(count)])
        )
    out: list[tuple[str, str, Path, list[str]]] = []
    for family, name, lines in specs:
        out.append((family, name, write_instance(directory, name, lines), lines))
    return out


def _vmhwm_kib(pid: int) -> int | None:
    try:
        status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in status.splitlines():
        if line.startswith("VmHWM:"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1])
    return None


def run_veriscs(binary: Path, path: Path, timeout: float) -> tuple[str, float, int | None, str]:
    """Return (stdout superstring or '', seconds, peak RSS KiB or None, status)."""
    start = time.perf_counter()
    proc = subprocess.Popen(
        [str(binary), "--stats", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    peak = _vmhwm_kib(proc.pid)
    timed_out = False
    try:
        while proc.poll() is None:
            sample = _vmhwm_kib(proc.pid)
            if sample is not None and (peak is None or sample > peak):
                peak = sample
            if time.perf_counter() - start > timeout:
                timed_out = True
                proc.kill()
                break
            time.sleep(0.05)
        stdout, stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        timed_out = True
    elapsed = time.perf_counter() - start
    if timed_out:
        return stdout or "", elapsed, peak, "timeout"
    if proc.returncode != 0:
        err = (stderr or "").strip().splitlines()
        detail = err[-1] if err else f"exit {proc.returncode}"
        return "", elapsed, peak, f"error: {detail}"
    text = stdout or ""
    if text.endswith("\n"):
        text = text[:-1]
    return text, elapsed, peak, "ok"


def fmt_sec(value: float) -> str:
    return f"{value:.4f}"


def ratio(produced: int | None, opt: int | None) -> str:
    if produced is None or opt is None:
        return ""
    if opt == 0:
        return "1" if produced == 0 else "inf"
    return f"{produced / opt:.3f}"


def benchmark(binary: Path | None, timeout: float, out_dir: Path) -> list[Row]:
    rows: list[Row] = []
    stopped: set[str] = set()
    for family, name, path, lines in generated_instances(out_dir):
        if family in stopped:
            rows.append(
                Row(
                    name, len(lines), sum(len(s) for s in lines),
                    max((len(s) for s in lines), default=0),
                    "", "", "", "not-run",
                    len(greedy_superstring(lines)), 0.0, "", "", "",
                    f"skipped after {family} timeout",
                )
            )
            continue
        symbols_in = sum(len(s) for s in lines)
        max_len = max((len(s) for s in lines), default=0)
        g0 = time.perf_counter()
        greedy = greedy_superstring(lines)
        greedy_sec = time.perf_counter() - g0
        opt_len: str
        exact_sec: str
        opt_value: int | None
        try:
            e0 = time.perf_counter()
            exact = exact_superstring(lines)
            exact_sec = fmt_sec(time.perf_counter() - e0)
            if missing_strings(lines, exact.superstring):
                opt_len = "exact-invalid"
                opt_value = None
            else:
                opt_len = str(exact.length)
                opt_value = exact.length
        except ValueError as exc:
            opt_len = "skipped"
            exact_sec = ""
            opt_value = None
            _ = exc
        if binary is None:
            rows.append(
                Row(
                    name, len(lines), symbols_in, max_len,
                    "", "", "", "skipped",
                    len(greedy), greedy_sec, opt_len, exact_sec, "",
                    "verified executable not run",
                )
            )
            continue
        text, elapsed, rss, status = run_veriscs(binary, path, timeout)
        if status == "ok":
            missing = missing_strings(lines, text)
            ok = "yes" if not missing else "NO"
            produced: int | None = len(text)
            note = "" if not missing else "checker failed"
            if opt_value is not None and produced > 2 * opt_value:
                note = (note + "; " if note else "") + "longer than 2*opt"
        else:
            ok = status
            produced = None
            note = status
        rows.append(
            Row(
                name,
                len(lines),
                symbols_in,
                max_len,
                "" if produced is None else str(produced),
                fmt_sec(elapsed),
                "" if rss is None else str(rss),
                ok,
                len(greedy),
                greedy_sec,
                opt_len,
                exact_sec,
                ratio(produced, opt_value),
                note,
            )
        )
        if status == "timeout":
            stopped.add(family)
    return rows


def render(rows: list[Row], timeout: float, binary: str) -> str:
    header = (
        f"Binary: `{binary}`\n\n"
        f"Per-instance time limit for the verified executable: {timeout:.0f}s.\n"
        "A timeout stops only the rest of that family. Later families still run.\n\n"
        "| instance | n | input symbols | max len | veriscs len | sec | RSS KiB | covers? | "
        "greedy len | opt | veriscs/opt | note |\n"
        "|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---|\n"
    )
    body = []
    for row in rows:
        body.append(
            f"| `{row.name}` | {row.n} | {row.symbols_in} | {row.max_len} | "
            f"{row.veriscs_len or '—'} | {row.veriscs_sec or '—'} | {row.veriscs_rss_kib or '—'} | "
            f"{row.veriscs_ok} | {row.greedy_len} | {row.opt_len or '—'} | {row.ratio or '—'} | "
            f"{row.note} |"
        )
    return header + "\n".join(body) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin", default="")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--out", default="BENCHMARK.md")
    parser.add_argument("--instances", default="benchmark-out/instances")
    parser.add_argument("--skip-veriscs", action="store_true")
    args = parser.parse_args(argv)
    binary = None if args.skip_veriscs or not args.bin else Path(args.bin)
    if binary is not None and not binary.exists():
        print(f"binary not found: {binary}", file=sys.stderr)
        return 2
    out_dir = Path(args.instances)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = benchmark(binary, args.timeout, out_dir)
    report = render(rows, args.timeout, "skipped" if binary is None else str(binary))
    Path(args.out).write_text(report, encoding="utf-8")
    sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
