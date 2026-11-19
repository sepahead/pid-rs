import SyntheticUnaryProof
import SyntheticPairProof
import SyntheticSatProof

namespace SyntheticRefusals
open SmtW02 ArchivedProjection

def wrongSlot : Fin (declarations syntheticUnary).length := ⟨2, by decide⟩
def wrongPack (ρ : Valuation syntheticUnary) : Fin 128 := (ρ wrongSlot).toFin

theorem correctAndWrongDiffer :
    evaluate syntheticUnary (SyntheticUnaryProof.restore 1) ≠
      evaluate syntheticUnary (SyntheticUnaryProof.restore (wrongPack (SyntheticUnaryProof.restore 1))) := by decide +kernel

theorem fixedTruthVectorInvalid : ¬ (∀ ρ : Valuation syntheticUnary, evaluate syntheticUnary ρ = some [true,false]) := by
  intro h
  have mismatch := (SyntheticUnaryProof.negativePremise).symm.trans (h (SyntheticUnaryProof.restore 0))
  have unequal : (some [false,true] : Option (List Bool)) ≠ some [true,false] := by decide
  exact unequal mismatch

theorem noRefutationOnFailure : ¬ RefutesTwo none := by decide
theorem noRefutationOnSingleFalse : ¬ RefutesTwo (some [false]) := by decide
theorem noRefutationOnExtraFalse : ¬ RefutesTwo (some [false,false,false]) := by decide
theorem explicitSat : ∃ ρ : Valuation syntheticSat, Satisfies syntheticSat ρ := SyntheticSatProof.hasModel
end SyntheticRefusals
