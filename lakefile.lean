import Lake
open Lake DSL

/-!
VeriSCS packages the Superstring development from
`https://github.com/openai/math` at commit
`adc7f1241b42e322a6451854ab7e4b4c146bf78a`.

The mathlib pin is the one recorded in that commit's `lean/lake-manifest.json`.
Only `OAI.Computability.Superstring` is built. Its import closure is Mathlib
plus the 51 vendored files; it does not require the rest of that repository.
-/

package veriscs where
  version := v!"0.1.0"
  leanOptions := #[⟨`autoImplicit, false⟩]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "d13f23b723b8a846827a245b89c10fc7d3f11612"

lean_lib OAI where
  globs := #[`OAI.Computability.Superstring.+]

lean_lib VeriSCS where
  globs := #[`VeriSCS.+]

/-- Text interface around `OAI.Superstring.answer`. -/
@[default_target]
lean_exe veriscs where
  root := `VeriSCS.CLI
