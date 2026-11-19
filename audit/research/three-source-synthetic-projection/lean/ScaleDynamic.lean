import ScaleStatic
import SyntheticUnaryProof

set_option maxRecDepth 65536
set_option maxHeartbeats 20000000
namespace ScaleDynamic
open SmtW02 ArchivedProjection ScalePrefix

abbrev A := Fin 128

def slot : Fin (declarations syntheticScale).length := ⟨1, by decide⟩
def pack (rho : Valuation syntheticScale) : A := (rho slot).toFin
def extend (x : A) : Valuation syntheticScale :=
  put syntheticScale slot (BitVec.ofFin x) (zeroValuation syntheticScale)

theorem inverse (x : A) : pack (extend x) = x := by rfl

def runBody (rho : Valuation syntheticScale) : Option (List Bool) := do
  let finish ← commands.foldlM (dynamicStep (valuationLookup (declarations syntheticScale) rho)) {}
  return finish.assertedRev.reverse

theorem checkedBody (rho : Valuation syntheticScale) :
    evaluate syntheticScale rho = runBody rho := by
  unfold SmtW02.evaluate
  rw [ScaleStatic.valid, commandsExact] <;> rfl

theorem bodyExact (rho : Valuation syntheticScale) :
    runBody rho = SyntheticUnaryProof.observe (pack rho) := by rfl

theorem full (rho : Valuation syntheticScale) :
    evaluate syntheticScale rho = SyntheticUnaryProof.observe (pack rho) :=
  (checkedBody rho).trans (bodyExact rho)

theorem preserved (rho : Valuation syntheticScale) :
    evaluate syntheticScale rho = evaluate syntheticScale (extend (pack rho)) :=
  (full rho).trans ((congrArg SyntheticUnaryProof.observe (inverse (pack rho))).symm.trans
    (full (extend (pack rho))).symm)

def projection : Projection syntheticScale A := ⟨pack, extend, inverse, preserved⟩

theorem agrees (x : A) : evaluate syntheticScale (extend x) = SyntheticUnaryProof.observe x :=
  (full (extend x)).trans (congrArg SyntheticUnaryProof.observe (inverse x))

def reification : Reification syntheticScale A projection := ⟨SyntheticUnaryProof.observe, agrees⟩

end ScaleDynamic
