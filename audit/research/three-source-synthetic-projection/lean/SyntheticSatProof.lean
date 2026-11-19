import ProjectionCore
import SyntheticSatData

namespace SyntheticSatProof
open SmtW02 ArchivedProjection
abbrev s := syntheticSat
def selected : Fin (declarations s).length := ⟨1,by decide⟩
def witness : Valuation s := put s selected (BitVec.ofNat 7 1) (zeroValuation s)
theorem valid : wellFormed s = true := by rfl
theorem observed : evaluate s witness = some [true,true] := by rfl
theorem hasModel : ∃ ρ : Valuation s, Satisfies s ρ := ⟨witness,observed⟩
theorem noUniversalRefutation : ¬ (∀ ρ : Valuation s, RefutesTwo (evaluate s ρ)) :=
  fun h => noModelOfSuccessfulRefutation s h hasModel
end SyntheticSatProof
