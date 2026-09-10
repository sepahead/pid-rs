import PidFiniteConvergence.TwoSourceMobiusAtomBridge

/-!
Trusted finite-world definitions only. The target is (A,B), the first source is A,
and the second source is either U or B. No theorem proof is supplied here.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators
open PidFiniteConvergence

namespace PidMgwFixedWorld

abbrev World := Fin 2 × Fin 2 × Fin 2
abbrev Target := Fin 2 × Fin 2
abbrev Key := CategoricalKey (Fin 2) (fun _ => Fin 2) Target

inductive AddedSource where
  | irrelevant
  | completing
deriving DecidableEq

noncomputable def worldMass (_w : World) : ℝ := 1 / 8

noncomputable def worldAMass (a : Fin 2) : ℝ :=
  ∑ w : World, if w.1 = a then worldMass w else 0

noncomputable def worldBMass (b : Fin 2) : ℝ :=
  ∑ w : World, if w.2.1 = b then worldMass w else 0

noncomputable def worldUMass (u : Fin 2) : ℝ :=
  ∑ w : World, if w.2.2 = u then worldMass w else 0

def addedValue : AddedSource → World → Fin 2
  | .irrelevant, w => w.2.2
  | .completing, w => w.2.1

/-- Both observations use the same world, first source A and target (A,B). -/
def observe (tag : AddedSource) (w : World) : Key :=
  ((fun source => if source = 0 then w.1 else addedValue tag w),
    (w.1, w.2.1))

/-- The actual count is the multiplicity of the observation map on the eight worlds. -/
noncomputable def count (tag : AddedSource) (z : Key) : ℕ :=
  letI : DecidableEq Key := Classical.decEq Key
  ∑ w : World, if observe tag w = z then 1 else 0

noncomputable def jointLaw (tag : AddedSource) : Key → ℝ :=
  empiricalLaw (count tag)

/-- Explicit source-map pushforward of the single world law. -/
noncomputable def pushedLaw (tag : AddedSource) (z : Key) : ℝ :=
  letI : DecidableEq Key := Classical.decEq Key
  ∑ w : World, if observe tag w = z then worldMass w else 0

/-- Expected complete 16-key count tables, kept separate from the defining pushforward. -/
def expectedCount : AddedSource → Key → ℕ
  | .irrelevant, z => if z.2.1 = z.1 0 then 1 else 0
  | .completing, z => if z.2 = (z.1 0, z.1 1) then 2 else 0

def expectedSourceCount : SxPid2Node → ℕ
  | .sourceOne => 4
  | .sourceTwo => 4
  | .jointSources => 2
  | .redundancy => 6

def expectedRestrictedCount : AddedSource → SxPid2Node → ℕ
  | .irrelevant, .sourceOne => 2
  | .irrelevant, .sourceTwo => 1
  | .irrelevant, .jointSources => 1
  | .irrelevant, .redundancy => 2
  | .completing, _ => 2

def expectedNetArgument : AddedSource → SxPid2Node → ℚ
  | .irrelevant, .sourceOne => 2
  | .irrelevant, .sourceTwo => 1
  | .irrelevant, .jointSources => 2
  | .irrelevant, .redundancy => 4 / 3
  | .completing, .sourceOne => 2
  | .completing, .sourceTwo => 2
  | .completing, .jointSources => 4
  | .completing, .redundancy => 4 / 3

noncomputable def expectedAverage : AddedSource → SxPid2Node → ℝ
  | .irrelevant, .sourceOne => Real.log 2
  | .irrelevant, .sourceTwo => 0
  | .irrelevant, .jointSources => Real.log 2
  | .irrelevant, .redundancy => Real.log (4 / 3)
  | .completing, .sourceOne => Real.log 2
  | .completing, .sourceTwo => Real.log 2
  | .completing, .jointSources => Real.log 4
  | .completing, .redundancy => Real.log (4 / 3)

/-- The existing joint-law average of the actual local signed-net MGW synergy. -/
noncomputable def synergy (tag : AddedSource) : ℝ :=
  averagedPointwiseAtomComponent (jointLaw tag) .net .synergy

/-- p(y,x2|x1) / (p(y|x1) * p(x2|x1)); used only on positive support. -/
noncomputable def conditionalRatio (tag : AddedSource) (z : Key) : ℝ :=
  let p := jointLaw tag
  let p1 := finiteEventMass p (sxPid2SourceEvent .sourceOne z)
  let p12 := finiteEventMass p (sxPid2SourceEvent .jointSources z)
  let p1t := finiteEventMass p (sxPid2TargetRestrictedEvent .sourceOne z)
  (p z / p1) / ((p1t / p1) * (p12 / p1))

/-- Direct finite conditional mutual information from conditional probabilities, in nats. -/
noncomputable def directCmi (tag : AddedSource) : ℝ :=
  ∑ z ∈ positiveMassSupport (jointLaw tag),
    jointLaw tag z * Real.log (conditionalRatio tag z)

end PidMgwFixedWorld

