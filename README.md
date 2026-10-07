# VeriSCS

VeriSCS is a command-line tool for the shortest common superstring problem. It runs the executable Lean function `OAI.Superstring.answer` from the public repository [openai/math](https://github.com/openai/math) (family 128, commit `adc7f1241b42e322a6451854ab7e4b4c146bf78a`) and checks the result with a separate Python program.

A shortest common superstring of a list of strings is a shortest string that contains each input as a contiguous substring. The upstream development proves, in Lean, that `answer` returns a common superstring whose length is at most twice the optimum, and that the same function has a polynomial-time multi-tape Turing machine implementation. See [TRUST.md](TRUST.md) for what that proof does and does not cover.

## Why this exists

The upstream manuscript states a deterministic polynomial-time factor-2 approximation. Its scope note ([`vendor/comparator/scope-128.md`](vendor/comparator/scope-128.md)) describes the Lean result as one algorithm that works for every finite list of explicitly encoded strings, with the ratio measured in symbols and the time bound measured in input bits. The manuscript presents factor 2 as a guarantee that had been open for this problem since Tarhio and Ukkonen (1988), with the best published guarantee before it below 2.466. VeriSCS does not re-check that historical claim. It packages the Lean function so it can be run and compared with ordinary code.

The machine-checked statement is about the Lean function, not about this repository's text encoding and not about the C code the Lean compiler emits. [TRUST.md](TRUST.md) is the precise account.

## Layout

| Path | Role |
|---|---|
| `OAI/Computability/Superstring/` | Unmodified upstream sources (51 files, 20,361 lines) |
| `VeriSCS/CLI.lean` | `veriscs` executable |
| `VeriSCS/Axioms.lean` | `#print axioms` for the specification and the implementation theorem |
| `tools/checker.py` | Independent substring check |
| `tools/scs.py` | Greedy merge and exact dynamic programming |
| `tools/benchmark.py` | Runtime, memory, and ratio measurements |
| `vendor/comparator/` | Unmodified Comparator challenge and scope note |

`NOTICE` lists the upstream commit and states that those files were not modified. Checksums are in `vendor/SHA256SUMS`.

## Requirements

- Lean `v4.34.1` (`lean-toolchain`), installed by [elan](https://github.com/leanprover/elan)
- mathlib at `d13f23b723b8a846827a245b89c10fc7d3f11612`, the pin in the upstream `lake-manifest.json`
- Python 3.11 or later for the checker and the benchmark (standard library only)

The Lean package does not fetch the rest of openai/math. `OAI.Computability.Superstring.Main` imports only modules under `OAI.Computability.Superstring`, and the root of that chain is `import Mathlib`.

## Build

```sh
lake update          # clones mathlib at the pinned commit; mathlib's hook downloads the olean cache
lake exe cache get   # safe to repeat
lake build veriscs
```

`lake build veriscs` elaborates the proof and produces `.lake/build/bin/veriscs`. Because `Model.lean` imports all of Mathlib, the native executable also compiles the C code of that import closure. The olean cache does not include those object files. Build time and peak memory from the run that produced this revision are in [BUILD.md](BUILD.md).

Axiom listing, after the oleans exist:

```sh
lake env lean VeriSCS/Axioms.lean
```

## Quick start

Input is one string per line. A final newline does not create an extra empty string. Empty lines in the middle are empty strings, which are substrings of every string.

```sh
.lake/build/bin/veriscs tests/instances/ab_bc.txt
```

```text
ab
bc
```

is an instance whose optimum has length 3 (`abc`). The program prints one superstring and a trailing newline.

```sh
printf 'ab\nbc\n' | .lake/build/bin/veriscs --stats
python3 tools/checker.py tests/instances/ab_bc.txt -
```

`--roundtrip` encodes and decodes the input without calling `answer`, which checks the text codec on its own. `--stats` writes `symbols: N` to standard error. `N` is the symbol length of the Lean output, which for this codec equals the number of Unicode scalar values in the printed string.

### Codec

`OAI.Superstring.answer` has type `Instance → Word`, with

```lean
abbrev Symbol := List Bool
abbrev Word := List Symbol
abbrev Instance := List Word
```

The executable maps each Unicode scalar value to one symbol: 21 bits, most significant bit first. It decodes the returned word with the same map. The factor-2 theorem counts symbols, so under this encoding it counts code points. The codec is ordinary Lean code in `VeriSCS/CLI.lean`. It is not part of `answer_spec`.

## Checker and baselines

```sh
python3 tools/test_scs.py
python3 tools/checker.py INPUT SUPERSTRING_FILE
python3 tools/benchmark.py --bin .lake/build/bin/veriscs --timeout 30 --out BENCHMARK.md
```

The checker only tests contiguous containment and reports length. It does not know the optimum.

`tools/scs.py` has two baselines:

- `greedy_superstring` repeatedly merges the pair with the largest prefix-suffix overlap. Ties prefer the smallest left index, then the smallest right index.
- `exact_superstring` drops strings that are already substrings of another input (one copy of a duplicate is kept) and solves the overlap Hamiltonian path by subset dynamic programming. That path is the optimum on a substring-free instance. It refuses more than 20 strings after filtering.

## Measured runs

The numbers below are copied from the benchmark run recorded in [BENCHMARK.md](BENCHMARK.md). They are not extrapolated. If a cell is missing here, that run did not produce it.

<!-- BENCHMARK-TABLE:START -->
Benchmark results are filled in after `tools/benchmark.py` runs against the built executable. Until that file exists, there are no measured times.
<!-- BENCHMARK-TABLE:END -->

## Trust model

Read [TRUST.md](TRUST.md). Short version:

- `answer_spec` is a Lean theorem about `answer`, which is defined as `Executable.solve`.
- The Comparator challenge file states `∃ f, …` and ends in `sorry`. A Comparator run would not, by itself, say that the witness is `Executable.solve`. The `#print axioms` output is what ties the theorems to that definition.
- The vendored sources contain no `sorry`, `axiom`, `unsafe`, `implemented_by`, or `extern`.
- The Lean compiler and the runtime are not verified. A successful `#print axioms` does not make the native binary a verified compiler artifact.
- Whether `IsCommonSuperstring` and `opt` are the problem you care about is a reading of the definitions in `Model.lean`. They are the standard contiguous-substring problem, with length counted in symbols. That reading is not a Lean theorem.

## What this is not

- It is not a fast superstring tool. The Lean function is written with lists and nested scans. Polynomial time is not a claim about practical speed. The benchmark is where that shows up.
- It is not a reimplementation. A port to another language would not inherit the Lean proof.
- The name and URL of the upstream repository identify the source of the vendored files. This project is not a product of that repository's authors and is not endorsed by them.

## Continuous integration

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs the Python tests on every push. A second job installs Lean, restores `.lake` from cache, builds `veriscs`, prints axioms, and runs the checker on `tests/instances/one.txt` and `tests/instances/ab_bc.txt`.

That Lean job compiles the Mathlib import closure to native code on a cold cache. [BUILD.md](BUILD.md) records how long that took here. If a hosted runner cannot finish it, the Python job is the part that still runs. Do not treat a green Python job as a Lean build.

## License

Apache-2.0. Upstream files remain under the license in `LICENSE`. See `NOTICE`.
