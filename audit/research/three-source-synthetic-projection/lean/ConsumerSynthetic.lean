import SyntheticAssembly

set_option maxRecDepth 65536
set_option maxHeartbeats 20000000
open SmtW02

namespace PrepConsumerU
theorem wellFormed : SmtW02.wellFormed syntheticUnary = true := PrepPayloadU.wellFormed
theorem successful : ∀ rho : Valuation syntheticUnary, ∃ p q : Bool, evaluate syntheticUnary rho = some [p,q] ∧ (p = false ∨ q = false) := PrepPayloadU.successful
theorem noModel : ¬ ∃ rho : Valuation syntheticUnary, Satisfies syntheticUnary rho := PrepPayloadU.noModel
theorem inhabited : Nonempty (Valuation syntheticUnary) := PrepPayloadU.inhabited
end PrepConsumerU

namespace PrepConsumerP
theorem wellFormed : SmtW02.wellFormed syntheticPair = true := PrepPayloadP.wellFormed
theorem successful : ∀ rho : Valuation syntheticPair, ∃ p q : Bool, evaluate syntheticPair rho = some [p,q] ∧ (p = false ∨ q = false) := PrepPayloadP.successful
theorem noModel : ¬ ∃ rho : Valuation syntheticPair, Satisfies syntheticPair rho := PrepPayloadP.noModel
theorem inhabited : Nonempty (Valuation syntheticPair) := PrepPayloadP.inhabited
end PrepConsumerP
