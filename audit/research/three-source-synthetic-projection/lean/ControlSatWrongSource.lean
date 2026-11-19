import SyntheticRefusalsProved
open SmtW02
example : ¬ ∃ ρ : Valuation syntheticSat, Satisfies syntheticSat ρ := SyntheticUnaryProof.noModel
