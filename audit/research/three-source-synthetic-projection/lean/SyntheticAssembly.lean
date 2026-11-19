import SyntheticUnaryProof
import SyntheticPairProof
import ProjectionReification

set_option maxRecDepth 65536
set_option maxHeartbeats 20000000
open SmtW02 ArchivedProjection

namespace PrepPayloadU
theorem wellFormed : SmtW02.wellFormed syntheticUnary = true := by rfl
theorem inverse : ∀ x : SyntheticUnaryProof.A, SyntheticUnaryProof.pack (SyntheticUnaryProof.restore x) = x := by intro x; rfl
theorem preserved : ∀ rho : Valuation syntheticUnary, evaluate syntheticUnary rho = evaluate syntheticUnary (SyntheticUnaryProof.restore (SyntheticUnaryProof.pack rho)) := by intro rho; rfl
def p : Projection syntheticUnary SyntheticUnaryProof.A := ⟨SyntheticUnaryProof.pack,SyntheticUnaryProof.restore,inverse,preserved⟩
theorem agrees : ∀ x : SyntheticUnaryProof.A, evaluate syntheticUnary (SyntheticUnaryProof.restore x) = SyntheticUnaryProof.observe x := by intro x; rfl
def r : Reification syntheticUnary SyntheticUnaryProof.A p := ⟨SyntheticUnaryProof.observe,agrees⟩
theorem enumeration : (List.finRange 128).all (fun i => decide (RefutesTwo (SyntheticUnaryProof.observe i))) = true := by decide +kernel
theorem successful (rho : Valuation syntheticUnary) : RefutesTwo (evaluate syntheticUnary rho) := by
  apply refutesAll p r _ rho
  intro i
  exact of_decide_eq_true ((List.all_eq_true.mp enumeration) i (List.mem_finRange i))
theorem noModel : ¬ ∃ rho : Valuation syntheticUnary, Satisfies syntheticUnary rho := noModelOfSuccessfulRefutation syntheticUnary successful
theorem inhabited : Nonempty (Valuation syntheticUnary) := valuationsInhabited syntheticUnary
end PrepPayloadU

namespace PrepPayloadP
theorem wellFormed : SmtW02.wellFormed syntheticPair = true := by rfl
theorem inverse : ∀ x : SyntheticPairProof.A, SyntheticPairProof.pack (SyntheticPairProof.restore x) = x := by intro x; rfl
theorem preserved : ∀ rho : Valuation syntheticPair, evaluate syntheticPair rho = evaluate syntheticPair (SyntheticPairProof.restore (SyntheticPairProof.pack rho)) := by intro rho; rfl
def p : Projection syntheticPair SyntheticPairProof.A := ⟨SyntheticPairProof.pack,SyntheticPairProof.restore,inverse,preserved⟩
theorem agrees : ∀ x : SyntheticPairProof.A, evaluate syntheticPair (SyntheticPairProof.restore x) = SyntheticPairProof.observe x := by intro x; rfl
def r : Reification syntheticPair SyntheticPairProof.A p := ⟨SyntheticPairProof.observe,agrees⟩
theorem enumeration : (List.finRange 16).all (fun i => (List.finRange 16).all (fun j => decide (RefutesTwo (SyntheticPairProof.observe (i,j))))) = true := by decide +kernel
theorem successful (rho : Valuation syntheticPair) : RefutesTwo (evaluate syntheticPair rho) := by
  apply refutesAll p r _ rho
  rintro ⟨i,j⟩
  have hi := (List.all_eq_true.mp enumeration) i (List.mem_finRange i)
  exact of_decide_eq_true ((List.all_eq_true.mp hi) j (List.mem_finRange j))
theorem noModel : ¬ ∃ rho : Valuation syntheticPair, Satisfies syntheticPair rho := noModelOfSuccessfulRefutation syntheticPair successful
theorem inhabited : Nonempty (Valuation syntheticPair) := valuationsInhabited syntheticPair
end PrepPayloadP
