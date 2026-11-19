import SyntheticRefusalsProved
open SmtW02
example : ∀ ρ : Valuation syntheticUnary, evaluate syntheticUnary ρ = some [true,false] := by intro ρ; rfl
