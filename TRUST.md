# Trust model

This file records what was checked in this repository, against which sources, and what remains unchecked. It does not extend the Lean proof.

## Sources

| Item | Value |
|---|---|
| Upstream repository | https://github.com/openai/math |
| Commit | `adc7f1241b42e322a6451854ab7e4b4c146bf78a` (initial commit, 2026-10-06T21:58:50Z) |
| Toolchain | `leanprover/lean4:v4.34.1` |
| mathlib | `d13f23b723b8a846827a245b89c10fc7d3f11612` (from that commit's `lean/lake-manifest.json`) |
| Vendored module | `OAI/Computability/Superstring/`, 51 files, 20,361 lines |
| Checksums | `vendor/SHA256SUMS` |

`diff` against a checkout of that commit reported no changes in the 51 Lean files. `NOTICE` states the same.

The import graph inside the module is a single chain. Every file has one import. The chain ends at `Model.lean`, whose only import is `Mathlib`. Nothing in the module imports another `OAI` library.

## The statement that is actually proved

`OAI.Computability.Superstring.Main` defines

```lean
def answer : Instance → Word := Executable.solve
```

and proves three theorems. The text below is the upstream source, not a paraphrase of a different statement.

`answer_spec` says that for every instance `S`, `answer S` is a common superstring of `S` and its length is at most `2 * opt S`.

`answer_implementation` says `HasPolynomialImplementation answer`: there exists a polynomial-time multi-tape Turing machine for the bit encodings `encodeInstance` and `encodeWord`, and every tape alphabet is finite.

`main` packages those two facts as an existential witness `f := answer`.

`Executable.solve` is defined in `WalkOutput.lean` as

```lean
def solve (S : List (List α)) : List α :=
  WalkCode.output (CollectionCode.tour (context S))
```

with the theorem `solve_spec`. The body is a functional program over lists. It is not a proof that is erased, and it is not an `implemented_by` stand-in.

## Definitions the ratio talks about

From `Model.lean`, which `Hierarchical.lean` imports, so these are the definitions used by `answer_spec`:

```lean
abbrev Symbol := List Bool
abbrev Word := List Symbol
abbrev Instance := List Word

def IsCommonSuperstring (S : Instance) (T : Word) : Prop :=
  ∀ s ∈ S, s <:+: T

noncomputable def opt (S : Instance) : ℕ :=
  sInf {n : ℕ | ∃ T : Word, IsCommonSuperstring S T ∧ T.length = n}
```

`<:+:` is Mathlib's contiguous infix relation (a list is a contiguous sublist). `opt` is the greatest lower bound of the lengths of common superstrings, in symbols, not in bits. The empty word is a contiguous sublist of every word, so empty inputs do not increase the optimum.

That is the standard shortest-common-superstring problem on a finite list of finite words over the alphabet of finite bit-lists. Confirming that this matches a particular applied formulation (for example DNA reads with reverse complements, or a circular superstring) is a human reading of these definitions. There is no separate theorem that says "this is the SCS problem from paper X."

## Comparator challenge

`vendor/comparator/Superstring.json` names:

- challenge module `ComparatorChallenges.Superstring`
- solution module `OAI.Computability.Superstring.Main`
- theorem `OAI.Superstring.main`
- permitted axioms `propext`, `Quot.sound`, `Classical.choice`
- `enable_nanoda: false`

The challenge file `vendor/comparator/Superstring.lean` repeats the definitions from `Model.lean` and then states

```lean
theorem main : ∃ f : Instance → Word,
    HasPolynomialImplementation f ∧
    ∀ S, IsCommonSuperstring S (f S) ∧ (f S).length ≤ 2 * opt S := by
  sorry
```

The witness is existential. A Comparator acceptance of this challenge would show that the solution module proves that same existential statement, under the permitted axioms. It would not, by itself, record that the witness is `Executable.solve`. `answer`, `answer_spec`, and `answer_implementation` are what name the function. `#print axioms` on those theorems is the check that connects them.

Comparator was not run in the build recorded by this revision. The reason is in the section "Comparator" below, filled in after the attempt.

## Axiom check

`VeriSCS/Axioms.lean` elaborates

```lean
#print axioms OAI.Superstring.answer_spec
#print axioms OAI.Superstring.answer_implementation
#print axioms OAI.Superstring.main
#print axioms OAI.Superstring.answer
```

The command and the compiler output from this revision:

<!-- AXIOM-OUTPUT:START -->
Not yet recorded. This section is replaced by the output of `lake env lean VeriSCS/Axioms.lean` after that command succeeds.
<!-- AXIOM-OUTPUT:END -->

The upstream challenge allows `propext`, `Quot.sound`, and `Classical.choice`. Anything else in the output above is outside that list. `sorry` or `Classical.choice` appearing on `answer` itself would mean the executable definition depends on an axiom; that is a different fact from the proofs of `answer_spec` using classical reasoning about `opt`.

## Execution path

Command, run on the vendored tree:

```sh
rg -n "implemented_by|@\[extern|unsafe |^unsafe|sorry|admit|^axiom " OAI --glob '*.lean'
```

Result: no matches.

`noncomputable` occurs on specification helpers (`opt`, finiteness instances, several plan and threading constructions used in proofs). `def answer` and `def Executable.solve` are not marked `noncomputable`. The native executable is produced only if Lean accepts `answer` as computable; that is checked by `lake build veriscs`, not by the text search.

The search does not inspect Mathlib. Mathlib contains `extern` and `implemented_by` on primitives (arrays, integers, I/O). `answer` calls ordinary list and natural-number operations, which on the native backend become the usual Lean runtime primitives. Those primitives are outside the Superstring proof.

## What is not guaranteed

- The Lean compiler, the C backend, the linker, and the runtime are not verified. `answer_spec` is a theorem about Lean's kernel semantics. It is not a theorem about the bytes of `.lake/build/bin/veriscs`.
- The text codec in `VeriSCS/CLI.lean` is unchecked. A bug there can print a string that is not the word `answer` returned, or can feed `answer` a different instance than the file contains. `--roundtrip` checks only that encode and decode are inverses on the input, not that the solver's output was decoded faithfully beyond the decoder's own checks.
- The Python checker tests containment of the printed text. It does not test the factor-2 bound. The benchmark compares lengths with an independent exact solver on small instances. Agreement on those instances is evidence, not a proof.
- `opt` is noncomputable. The factor-2 inequality is proved in Lean; the benchmark's "opt" column is a separate dynamic program.
- No human has produced an independent pen-and-paper review of the 20,361 lines as part of this repository. The kernel check is the machine check. It does not replace reading the specification.
- The upstream manuscript's comparison with earlier approximation ratios is not formalized in the vendored files and is not re-established here.

## Comparator

<!-- COMPARATOR:START -->
Not yet attempted in this revision.
<!-- COMPARATOR:END -->
