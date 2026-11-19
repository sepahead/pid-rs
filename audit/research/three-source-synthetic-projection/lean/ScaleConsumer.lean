import ScaleFinite

namespace ScaleConsumer
open SmtW02

theorem wellFormed : SmtW02.wellFormed syntheticScale = Bool.true := ScaleStatic.valid

theorem successful (v : Valuation syntheticScale) :
    ∃ a b : Bool, evaluate syntheticScale v = Option.some (a :: b :: []) ∧
      (a = Bool.false ∨ b = Bool.false) := ScaleFinite.successful v

theorem noModel : ¬ ∃ v : Valuation syntheticScale, Satisfies syntheticScale v := ScaleFinite.noModel

theorem inhabited : Nonempty (Valuation syntheticScale) := ScaleFinite.inhabited

end ScaleConsumer
