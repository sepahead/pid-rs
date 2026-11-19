import ScaleDynamic

namespace ScaleFinite
open SmtW02 ArchivedProjection

theorem cases128 :
    (List.finRange 128).all (fun x => decide (RefutesTwo (SyntheticUnaryProof.observe x))) = true :=
  SyntheticUnaryProof.finiteCertificate

theorem successful (rho : Valuation syntheticScale) : RefutesTwo (evaluate syntheticScale rho) := by
  apply refutesAll ScaleDynamic.projection ScaleDynamic.reification _ rho
  intro a
  exact of_decide_eq_true ((List.all_eq_true.mp cases128) a (List.mem_finRange a))

theorem noModel : ¬ ∃ rho : Valuation syntheticScale, Satisfies syntheticScale rho :=
  noModelOfSuccessfulRefutation syntheticScale successful

theorem inhabited : Nonempty (Valuation syntheticScale) := valuationsInhabited syntheticScale

theorem odd : evaluate syntheticScale (ScaleDynamic.extend 1) = some [true,false] := by
  rw [ScaleDynamic.agrees] <;> rfl

theorem even : evaluate syntheticScale (ScaleDynamic.extend 0) = some [false,true] := by
  rw [ScaleDynamic.agrees] <;> rfl

end ScaleFinite
