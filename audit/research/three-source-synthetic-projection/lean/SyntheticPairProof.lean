import ProjectionCore
import SyntheticPairData

set_option maxRecDepth 65536
set_option maxHeartbeats 20000000
namespace SyntheticPairProof
open SmtW02 ArchivedProjection
abbrev s := syntheticPair
abbrev A := Fin 16 × Fin 16

def leftSlot : Fin (declarations s).length := ⟨1, by decide⟩
def rightSlot : Fin (declarations s).length := ⟨3, by decide⟩
def pack (ρ : Valuation s) : A := ((ρ leftSlot).toFin,(ρ rightSlot).toFin)
def restore (x : A) : Valuation s :=
  put s rightSlot (BitVec.ofFin x.2) (put s leftSlot (BitVec.ofFin x.1) (zeroValuation s))

theorem sourceWellFormed : wellFormed s = true := by rfl
theorem rightInverse (x : A) : pack (restore x) = x := by rfl
theorem valuationPreserved (ρ : Valuation s) : evaluate s ρ = evaluate s (restore (pack ρ)) := by rfl

def projection : Projection s A := ⟨pack,restore,rightInverse,valuationPreserved⟩
def observe (x : A) : Option (List Bool) := do
  let l ← indexedValue "extract" [1,1] (.bits 4 x.1.val)
  let r ← indexedValue "extract" [1,1] (.bits 4 x.2.val)
  let truth ← builtinValue "=" [l,r]
  let contrary ← builtinValue "not" [truth]
  return [← truth.getBool, ← contrary.getBool]

theorem reified (x : A) : evaluate s (restore x) = observe x := by rfl

def reification : Reification s A projection := ⟨observe,reified⟩
theorem finiteCertificate : (List.finRange 16).all (fun i => (List.finRange 16).all
    (fun j => decide (RefutesTwo (observe (i,j))))) = true := by decide +kernel

theorem successfulAssertions (ρ : Valuation s) : RefutesTwo (evaluate s ρ) := by
  apply refutesAll projection reification _ ρ
  rintro ⟨i,j⟩
  have hi := (List.all_eq_true.mp finiteCertificate) i (List.mem_finRange i)
  exact of_decide_eq_true ((List.all_eq_true.mp hi) j (List.mem_finRange j))

theorem noModel : ¬ ∃ ρ : Valuation s, Satisfies s ρ := noModelOfSuccessfulRefutation s successfulAssertions
theorem inhabited : Nonempty (Valuation s) := valuationsInhabited s
theorem positivePremise : evaluate s (restore (0,0)) = some [true,false] := by rfl
theorem leftAffectsPremise : evaluate s (restore (2,0)) = some [false,true] := by rfl
theorem rightAffectsPremise : evaluate s (restore (0,2)) = some [false,true] := by rfl
end SyntheticPairProof
