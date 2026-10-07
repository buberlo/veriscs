# Build log

Measured on this machine while producing this revision. `nproc` was 4. `MemTotal` was 16 GiB. During the build, `MemAvailable` in sampled readings stayed near 4.1–5.0 GiB.

## mathlib cache

`lake update` from 2026-10-07T03:56:14Z to 2026-10-07T03:57:35Z (81 seconds), exit 0. mathlib's post-update hook downloaded 8908 cache files from `https://cache.mathlib.org/mathlib4-master` and decompressed them. The mathlib commit is `d13f23b723b8a846827a245b89c10fc7d3f11612`.

## `lake build veriscs`

| | |
|---|---|
| Start | 2026-10-07T04:06:49Z |
| End | 2026-10-07T05:08:13Z |
| Wall clock | 61 minutes 24 seconds |
| Exit | 0 |
| Jobs | 17936 |
| Executable | `.lake/build/bin/veriscs`, 170,135,016 bytes |
| `.lake` afterward | 8.6 GiB |

Most of those jobs compile C object files for the Mathlib import closure. The olean cache does not include them. After `Mathlib:c.o` (29 seconds), each Superstring module elaborated in about 30–42 seconds. Examples from the log: `Model` 80 seconds, `Hierarchical` 38 seconds, `Main` 33 seconds, `VeriSCS.CLI` 33 seconds. Linking `veriscs:exe` took 6.3 seconds.

The largest resident set observed for a `lean` process, from occasional samples rather than a continuous profiler, was 3,619,440 KiB (about 3.45 GiB). The true peak may be higher. The running `veriscs` binary later stayed near 64–88 MiB on the benchmark instances; that number is in [BENCHMARK.md](BENCHMARK.md).

## Axiom print and Comparator

`lake env lean VeriSCS/Axioms.lean` exited 0. The text is in [TRUST.md](TRUST.md).

Comparator's own build, after overriding its toolchain to v4.34.1, finished in well under a minute. The challenge module then elaborated in 39 seconds. The run itself is the log in [docs/comparator-superstring.log](docs/comparator-superstring.log). It used `fake-landrun.sh`, so it is not a landlock-sandboxed run.
