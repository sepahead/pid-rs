import ProjectionCore

namespace ArchivedProjection
open SmtW02

/-- Assemble one symbolic expression from a family of algebras, indexed by genuine free input. -/
def pointwiseAlgebra {X α : Type} (alg : X → TermAlgebra α) : TermAlgebra (X → α) where
  boolean := fun b x => (alg x).boolean b
  numeral := fun n x => (alg x).numeral n
  bits := fun w n x => (alg x).bits w n
  name := fun ty nm x => (alg x).name ty nm
  app := fun ty op args x => (alg x).app ty op (args.map (fun f => f x))
  indexed := fun ty op idx arg x => (alg x).indexed ty op idx (arg x)

mutual
  /-- The complete algebraic expression, applied at a value, is the ordinary fold at that value. -/
  theorem foldAt {X α : Type} (alg : X → TermAlgebra α) (x : X) (term : Term) :
      (Term.fold (pointwiseAlgebra alg) term) x = Term.fold (alg x) term := by
    cases term with
    | boolean _ => rfl
    | numeral _ => rfl
    | bits _ _ => rfl
    | name _ _ => rfl
    | app ty op args =>
      change (alg x).app ty op ((Term.foldArgs (pointwiseAlgebra alg) args).map (fun f => f x)) = _
      rw [foldArgsAt alg x args]
      rfl
    | indexed ty op idx arg =>
      change (alg x).indexed ty op idx ((Term.fold (pointwiseAlgebra alg) arg) x) = _
      rw [foldAt alg x arg]
      rfl
  termination_by structural term

  theorem foldArgsAt {X α : Type} (alg : X → TermAlgebra α) (x : X) (terms : List Term) :
      (Term.foldArgs (pointwiseAlgebra alg) terms).map (fun f => f x) = Term.foldArgs (alg x) terms := by
    cases terms with
    | nil => rfl
    | cons t ts =>
      change (Term.fold (pointwiseAlgebra alg) t x) ::
        ((Term.foldArgs (pointwiseAlgebra alg) ts).map (fun f => f x)) = _
      rw [foldAt alg x t, foldArgsAt alg x ts]
      rfl
  termination_by structural terms
end

/-- Same algebra that the imported `evaluateTerm` uses. The definitional equality below
checks the entire body, including local-variable shadowing and eager evaluation of all arguments. -/
def modelAlgebra (global : Functions) (locals : Locals) : TermAlgebra (Option Value) where
  boolean := fun v => some (.boolean v)
  numeral := fun n => some (.integer (Int.ofNat n))
  bits := fun w n => some (.bits w n)
  name := fun _ n => match locals.lookup n with
    | some v => some v
    | none => do let g ← global.lookup n; g []
  app := fun _ op children => do
    let args ← children.mapM id
    match global.lookup op with
    | some g => g args
    | none => builtinValue op args
  indexed := fun _ op ix child => do indexedValue op ix (← child)

theorem modelAlgebraMatches (t : Term) (g : Functions) (l : Locals) :
    t.fold (modelAlgebra g l) = evaluateTerm t g l := by rfl

def symbolicTerm {X : Type} (t : Term) (g : X → Functions) (l : X → Locals) : X → Option Value :=
  t.fold (pointwiseAlgebra (fun x => modelAlgebra (g x) (l x)))

theorem symbolicTermExact {X : Type} (t : Term) (g : X → Functions) (l : X → Locals) (x : X) :
    symbolicTerm t g l x = evaluateTerm t (g x) (l x) :=
  (foldAt (fun z => modelAlgebra (g z) (l z)) x t).trans (modelAlgebraMatches t (g x) (l x))

end ArchivedProjection
