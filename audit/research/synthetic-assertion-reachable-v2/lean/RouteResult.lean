import RouteLeaves

open SmtW02 ArchivedProjection RouteSpec

namespace RouteResult

theorem ordered (v : Valuation primary) : evaluate primary v = observed (bit v) :=
  (RouteHelpers.evalViaRelay v).trans (congrArg fromValue (RouteHelpers.prefixBit v))

theorem sameOutput (v w : Valuation primary) (h : bit v = bit w) :
    evaluate primary v = evaluate primary w :=
  (ordered v).trans ((congrArg observed h).trans (ordered w).symm)

theorem environmentsDiffer : state sample0 ≠ state sample1 := by
  intro equality
  have h0 : fetch (state sample0) "unused" = some (.integer 0) :=
    (RouteHelpers.prefixTag sample0).trans
      (congrArg (fun i : Int => some (Value.integer i)) RouteHelpers.witnessInputs.2.2.1)
  have h1 : fetch (state sample1) "unused" = some (.integer 1) :=
    (RouteHelpers.prefixTag sample1).trans
      (congrArg (fun i : Int => some (Value.integer i)) RouteHelpers.witnessInputs.2.2.2)
  have bad := h0.symm.trans ((congrArg (fun s => fetch s "unused") equality).trans h1)
  have distinct : (some (Value.integer 0) : Option Value) ≠ some (.integer 1) := by decide
  exact distinct bad

theorem counterexample : bit sample0 = bit sample1 ∧ state sample0 ≠ state sample1 ∧
    evaluate primary sample0 = evaluate primary sample1 := by
  have h : bit sample0 = bit sample1 := RouteHelpers.witnessInputs.1.trans RouteHelpers.witnessInputs.2.1.symm
  exact ⟨h, environmentsDiffer, sameOutput sample0 sample1 h⟩

theorem allRefute (v : Valuation primary) : RefutesTwo (evaluate primary v) := by
  rw [ordered v]
  cases bit v with
  | false => exact RouteHelpers.leafFalse
  | true => exact RouteHelpers.leafTrue

end RouteResult
