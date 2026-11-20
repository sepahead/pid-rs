import OriginalFinite

set_option maxRecDepth 65536
set_option maxHeartbeats 20000000
namespace OriginalConsumer
open SmtW02 OriginalContract

theorem wellFormed : SmtW02.wellFormed SmtW02.originalScript = Bool.true := OriginalProof.wellFormed

theorem inhabited : Nonempty (SmtW02.Valuation SmtW02.originalScript) := OriginalProof.inhabited

theorem rightInverse (a : A) : pack (extend a) = a := OriginalProof.rightInverse a

theorem checkedBody (v : Valuation originalScript) :
    evaluate originalScript v = dynamicBody v := OriginalProof.checkedBody v

theorem bodyAgreement (v : Valuation originalScript) :
    dynamicBody v = observe (pack v) := OriginalProof.bodyAgreement v

theorem preserves (v : Valuation originalScript) :
    evaluate originalScript v = evaluate originalScript (extend (pack v)) := OriginalProof.preserves v

theorem reifies (a : A) :
    evaluate originalScript (extend a) = observe a := OriginalProof.reifies a

theorem fullEvaluation (v : Valuation originalScript) :
    evaluate originalScript v = observe (pack v) := OriginalProof.fullEvaluation v

theorem leftPredicate (v : Valuation originalScript) :
    leftAt v = some (validMask (pack v)) := OriginalProof.leftPredicate v

theorem rightPredicate (v : Valuation originalScript) :
    rightAt v = some (sourceOrder (pack v) (pack v)) := OriginalProof.rightPredicate v

theorem finiteDecision : (List.finRange 128).all
    (fun a => decide (ArchivedProjection.RefutesTwo (observe a))) = Bool.true := OriginalProof.finiteDecision

theorem namedRelation (v : Valuation originalScript) :
    ∃ p q : Bool, leftAt v = some p ∧ rightAt v = some q ∧
      evaluate originalScript v = Option.some (p :: (!q) :: []) := OriginalProof.namedRelation v

theorem orderedOutput (v : Valuation originalScript) :
    evaluate originalScript v = Option.some
      (validMask (pack v) :: (!(sourceOrder (pack v) (pack v))) :: []) := OriginalProof.orderedOutput v

theorem successful (v : Valuation originalScript) :
    ∃ p q : Bool, evaluate originalScript v = Option.some (p :: q :: []) ∧
      (p = Bool.false ∨ q = Bool.false) := OriginalProof.successful v

theorem noModel : ¬ ∃ v : Valuation originalScript, SmtW02.Satisfies originalScript v :=
  OriginalProof.noModel

end OriginalConsumer

