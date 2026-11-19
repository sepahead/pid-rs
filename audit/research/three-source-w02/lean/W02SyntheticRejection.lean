import W02SyntheticChecks

namespace SmtW02

private def fixture (body : List Cmd) : List Cmd :=
  [.logic "ALL", .option ":produce-models" "true", .echo "\"synthetic\""] ++ body ++ [.check, .exit]

private def yes : Cmd := .assertion (.boolean true)
private def bv (w n : Nat) : Term := .bits w n
private def eqBV (u v : Term) : Cmd := .assertion (.app .bool "=" [u, v])

def syntheticRejectedTrees : List (String × List Cmd) := [
  ("non-Boolean assertion", fixture [yes, .assertion (.numeral 0)]),
  ("different widths", fixture [yes, eqBV (bv 3 1) (bv 4 1)]),
  ("oversized indexed literal", fixture [yes, eqBV (bv 3 8) (bv 3 0)]),
  ("invalid extraction", fixture [yes, eqBV (.indexed (.bv 2) "extract" [4,3] (bv 3 0)) (bv 2 0)]),
  ("forward original binding", fixture [.define "f" [] .bool (.name .bool "g"),
    .define "g" [] .bool (.boolean true), yes, yes]),
  ("duplicate original binding", fixture [.constant "f" .bool, .define "f" [] .bool (.boolean true), yes, yes]),
  ("one assertion", fixture [yes]),
  ("three assertions", fixture [yes,yes,yes]),
  ("operator outside the scoped grammar", fixture [yes, .assertion (.app .bool "=" [
    .app .int "*" [.numeral 2,.numeral 2], .numeral 4])]),
  ("command after exit", (fixture [yes,yes]) ++ [yes]),
  ("wrong application result annotation", fixture [yes, .assertion (.app .bool "+" [.numeral 1,.numeral 1])]),
  ("wrong type annotation on bound name", fixture [.constant "x" .int,yes,.assertion (.name .bool "x")]),
  ("wrong indexed result annotation", fixture [yes,eqBV (.indexed (.bv 2) "zero_extend" [4] (bv 3 0)) (bv 2 0)]),
  ("duplicate local parameters", fixture [.define "f" [("x",.bool),("x",.int)] .int (.numeral 0),yes,yes]),
  ("local argument applied as a function", fixture [.define "f" [("x",.bool)] .bool (.app .bool "x" []),yes,yes]),
  ("undefined integer cannot default to zero", fixture [yes,.assertion (.app .bool "=" [.name .int "missing", .numeral 0])]),
  ("a failed assertion does not supply Boolean false", fixture [yes,.assertion (.app .bool "not" [])])]

theorem allSyntheticRankFaults :
    syntheticRejectedTrees.all (fun p => !wellFormed p.2) = true := by decide

theorem evaluationRejectsMalformed {script : List Cmd} (ρ : Valuation script)
    (h : wellFormed script = false) : evaluate script ρ = none := by
  simp [evaluate, h, guard]

theorem firstControlHasNoModel : ¬ ∃ ρ : Valuation t01, Satisfies t01 ρ :=
  noModelOfResults t01 t01Result

theorem thirdControlHasModel : ∃ ρ : Valuation t03, Satisfies t03 ρ :=
  ⟨t03witness, t03Model⟩

theorem zeroAssignmentExists (script : List Cmd) : Nonempty (Valuation script) :=
  valuationsInhabited script

end SmtW02

