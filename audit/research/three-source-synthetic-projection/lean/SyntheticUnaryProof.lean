import ProjectionCore
import SyntheticUnaryData

set_option maxRecDepth 65536
set_option maxHeartbeats 20000000
namespace SyntheticUnaryProof
open SmtW02 ArchivedProjection
abbrev s := syntheticUnary
abbrev A := Fin 128

def slot : Fin (declarations s).length := ⟨1, by decide⟩
def pack (ρ : Valuation s) : A := (ρ slot).toFin
def restore (x : A) : Valuation s := put s slot (BitVec.ofFin x) (zeroValuation s)

theorem sourceWellFormed : wellFormed s = true := by rfl
theorem rightInverse (x : A) : pack (restore x) = x := by rfl
theorem valuationPreserved (ρ : Valuation s) : evaluate s ρ = evaluate s (restore (pack ρ)) := by rfl

def projection : Projection s A := ⟨pack,restore,rightInverse,valuationPreserved⟩
def observe (x : A) : Option (List Bool) :=
  do
    let mask ← builtinValue "bvand" [.bits 7 x.val, .bits 7 1]
    let truth ← builtinValue "=" [mask, .bits 7 1]
    let contrary ← builtinValue "not" [truth]
    return [← truth.getBool, ← contrary.getBool]

theorem reified (x : A) : evaluate s (restore x) = observe x := by rfl

def reification : Reification s A projection := ⟨observe,reified⟩
theorem finiteCertificate : (List.finRange 128).all (fun x => decide (RefutesTwo (observe x))) = true := by decide +kernel

theorem successfulAssertions (ρ : Valuation s) : RefutesTwo (evaluate s ρ) := by
  apply refutesAll projection reification _ ρ
  intro x
  exact of_decide_eq_true ((List.all_eq_true.mp finiteCertificate) x (List.mem_finRange x))

theorem noModel : ¬ ∃ ρ : Valuation s, Satisfies s ρ := noModelOfSuccessfulRefutation s successfulAssertions
theorem inhabited : Nonempty (Valuation s) := valuationsInhabited s

theorem positivePremise : evaluate s (restore 1) = some [true,false] := by rfl
theorem negativePremise : evaluate s (restore 0) = some [false,true] := by rfl
end SyntheticUnaryProof
