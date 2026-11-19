import W02OriginalData
set_option maxRecDepth 65536
set_option maxHeartbeats 20000000
open SmtW02
namespace W02
theorem sourceWellFormed : wellFormed originalScript = true := by
  rfl

theorem assertionsAtAllValuations : ∀ rho : Valuation originalScript, evaluate originalScript rho = some [true, false] := by
  intro rho
  rfl

theorem noSatisfyingValuation : ¬ ∃ rho : Valuation originalScript, Satisfies originalScript rho := by
  exact noModelOfResults originalScript assertionsAtAllValuations

theorem sourceRanksHaveValuation : Nonempty (Valuation originalScript) := by
  exact valuationsInhabited originalScript
end W02
