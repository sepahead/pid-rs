import SyntheticRefusalsProved
open SmtW02 SyntheticRefusals
example (ρ : Valuation syntheticUnary) : evaluate syntheticUnary ρ =
    evaluate syntheticUnary (SyntheticUnaryProof.restore (wrongPack ρ)) := by rfl
