import OAI.Computability.Superstring.Main

/-!
Elaborating this module prints the axioms used by the statements that tie
`OAI.Superstring.answer` (that is, `Executable.solve`) to the factor-2
guarantee and to the polynomial-time machine certificate.

The Comparator challenge is existential (`∃ f, …`), so a successful
Comparator run would not by itself name `Executable.solve`. These prints are
the check that does.
-/

#print axioms OAI.Superstring.answer_spec
#print axioms OAI.Superstring.answer_implementation
#print axioms OAI.Superstring.main
#print axioms OAI.Superstring.answer
