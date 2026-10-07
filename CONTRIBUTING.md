# Contributing

VeriSCS is an Apache-2.0 reference implementation. Small, measured, and
carefully scoped changes are welcome.

There is no GitHub Actions workflow. Please do not add files under
`.github/workflows/`. Check your change locally:

```sh
make test     # Python unit tests; no Lean binary
make check    # small fixtures through veriscs and tools/checker.py
make axioms   # #print axioms, after a build
```

`make build` compiles the Mathlib import closure and takes about an hour
the first time. See [BUILD.md](BUILD.md).

## Useful work

- A faster implementation that is proved equal to `Executable.solve`, so
  `answer_spec` still applies. An `Array` program with an equivalence proof
  is the example to aim at. A port that is only tested, not proved, must be
  labeled as an unverified baseline.
- More benchmark instances, with the command, the output, and the machine
  written down. Do not replace a timeout with an estimate.
- A reading of `IsCommonSuperstring` and `opt` in
  `OAI/Computability/Superstring/Model.lean` against the classical
  shortest-common-superstring problem. [TRUST.md](TRUST.md) is the place
  those notes belong.

## House rules

- Do not fabricate timings, lengths, or citation details.
- Do not imply that the authors of [openai/math](https://github.com/openai/math)
  endorse this repository. Attribute the vendored files and leave `NOTICE`
  accurate.
- Leave the files under `OAI/Computability/Superstring/` and
  `vendor/comparator/` unmodified. A change to those files belongs in an
  upstream patch, not a silent edit. If a patch is ever required, record it
  in `NOTICE` and refresh `vendor/SHA256SUMS`.
- The Python checker tests containment and length. It does not test the
  factor-2 bound. Say so if you extend it.

Open an issue before a large proof refactor so the claim and the
non-claim stay visible.
