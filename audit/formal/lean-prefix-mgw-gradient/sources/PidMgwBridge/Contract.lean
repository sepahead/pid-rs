import MgwBridgeDepsV1.SxDnf.Contract
import MgwBridgeDepsV1.JoinLog.Contract
import Mathlib.Data.Fintype.Powerset

/-! Trusted finite categorical MGW objects and eleven intended propositions only.
No value of any MGW target is supplied. The actual redundancy order is explicit. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators

universe u v w
namespace PidMgwBridgeContract

abbrev Key (I : Type u) (X : I → Type v) (T : Type w) :=
  PidFiniteConvergence.CategoricalKey I X T

def Valid {I : Type u} (family : Finset (Finset I)) : Prop :=
  family.Nonempty ∧ (∀ a ∈ family, a.Nonempty) ∧
    PidSxDnfOrderContract.IsInclusionAntichain family

abbrev Node (I : Type u) := {family : Finset (Finset I) // Valid family}

def rawLE {I : Type u} (alpha beta : Finset (Finset I)) : Prop :=
  PidSxDnfOrderContract.RedundancyLE alpha beta

@[instance_reducible]
noncomputable def nodeFintype (I : Type u) [Fintype I] : Fintype (Node I) := by
  classical
  exact inferInstance

def singles {I : Type u} [DecidableEq I] (missing : Finset I) : Finset (Finset I) :=
  missing.image fun i => {i}

noncomputable def rawJoin {I : Type u} [DecidableEq I]
    (alpha beta : Finset (Finset I)) : Finset (Finset I) := by
  classical
  let unions := alpha.biUnion fun a => beta.image fun b => a ∪ b
  exact unions.filter fun candidate =>
    ∀ other ∈ unions, other ⊆ candidate → other = candidate

def ExactOps {I : Type u} [DecidableEq I] (sigma : SemilatticeSup (Node I)) : Prop :=
  (∀ a b : Node I, sigma.le a b ↔ rawLE a.val b.val) ∧
  (∀ a b : Node I, (sigma.sup a b).val = rawJoin a.val b.val)

noncomputable def nodeTotal {I : Type u} [Fintype I] (weight : Node I → ℝ) : ℝ := by
  classical
  letI := nodeFintype I
  exact ∑ a, weight a

noncomputable def cumulative {I : Type u} [Fintype I]
    (atoms : Node I → ℝ) (alpha : Node I) : ℝ := by
  classical
  letI := nodeFintype I
  exact ∑ beta, if rawLE beta.val alpha.val then atoms beta else 0

noncomputable def total {K : Type u} [Fintype K] (mass : K → ℝ) : ℝ :=
  ∑ x, mass x

def Law {K : Type u} [Fintype K] (mass : K → ℝ) : Prop :=
  (∀ x, 0 ≤ mass x) ∧ total mass = 1

section Categorical
variable {I : Type u} {X : I → Type v} {T : Type w}
variable [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
variable [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]

noncomputable def fullSourceMass (mass : Key I X T → ℝ) (anchor : Key I X T) : ℝ :=
  PidFiniteConvergence.finiteEventMass mass
    (PidFiniteConvergence.sourceBranchEvent (Finset.univ : Finset I) anchor)

noncomputable def targetMass (mass : Key I X T → ℝ) (anchor : Key I X T) : ℝ :=
  PidFiniteConvergence.finiteEventMass mass (PidFiniteConvergence.targetBranchEvent anchor)

noncomputable def sourceMass (mass : Key I X T → ℝ) (anchor : Key I X T)
    (alpha : Node I) : ℝ :=
  PidFiniteConvergence.finiteEventMass mass
    (PidFiniteConvergence.sxSourceEvent alpha.val anchor)

noncomputable def restrictedMass (mass : Key I X T → ℝ) (anchor : Key I X T)
    (alpha : Node I) : ℝ :=
  PidFiniteConvergence.finiteEventMass mass
    (PidFiniteConvergence.sxTargetRestrictedEvent alpha.val anchor)

noncomputable def mismatches (anchor candidate : Key I X T) : Finset I := by
  classical
  exact Finset.univ.filter fun i => candidate.1 i ≠ anchor.1 i

noncomputable def weights (mass : Key I X T → ℝ) (anchor : Key I X T)
    (beta : Node I) : ℝ := by
  classical
  exact ∑ x, if (mismatches anchor x).Nonempty ∧
    singles (mismatches anchor x) = beta.val then mass x else 0

noncomputable def conditioned (mass : Key I X T → ℝ) (anchor : Key I X T)
    (candidate : Key I X T) : ℝ := by
  classical
  exact if candidate ∈ PidFiniteConvergence.targetBranchEvent anchor then
    mass candidate / targetMass mass anchor else 0

noncomputable def InfInverse (mass : Key I X T → ℝ) (anchor : Key I X T)
    (atoms : Node I → ℝ) : Prop :=
  ∀ alpha, cumulative atoms alpha = -Real.log (sourceMass mass anchor alpha)

noncomputable def MisInverse (mass : Key I X T → ℝ) (anchor : Key I X T)
    (atoms : Node I → ℝ) : Prop :=
  ∀ alpha, cumulative atoms alpha =
    Real.log (targetMass mass anchor / restrictedMass mass anchor alpha)
end Categorical

noncomputable def Generated {I : Type u} (weight : Node I → ℝ) (alpha : Node I) : Prop :=
  ∃ support : Finset (Node I), support.Nonempty ∧
    (∀ x ∈ support, 0 < weight x) ∧
    (∀ x ∈ support, rawLE x.val alpha.val) ∧
    (∀ upper : Node I, (∀ x ∈ support, rawLE x.val upper.val) →
      rawLE alpha.val upper.val)

noncomputable def LogModel {I : Type u} [Fintype I] [DecidableEq I]
    (weight atoms : Node I → ℝ) : Prop := by
  classical
  exact ∃ sigma : SemilatticeSup (Node I), ExactOps sigma ∧
    atoms = @PidJoinLogContract.logAtoms (Node I) (nodeFintype I) sigma
      (Classical.decEq (Node I)) weight

abbrev actual_join_lub_target : Prop :=
  ∀ (I : Type u) [Fintype I] [Nonempty I] [DecidableEq I],
    (∀ alpha beta : Node I,
      Valid (rawJoin alpha.val beta.val) ∧
      ∀ gamma : Node I, rawLE (rawJoin alpha.val beta.val) gamma.val ↔
        (rawLE alpha.val gamma.val ∧ rawLE beta.val gamma.val)) ∧
    ∃ sigma : SemilatticeSup (Node I), ExactOps sigma

abbrev mismatch_generator_and_exclusion_target : Prop :=
  (∀ (I : Type u) [Fintype I] [Nonempty I] [DecidableEq I]
      (missing : Finset I), missing.Nonempty → Valid (singles missing)) ∧
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (anchor candidate : Key I X T) (alpha : Node I),
    candidate ∉ PidFiniteConvergence.sxSourceEvent alpha.val anchor ↔
      ((mismatches anchor candidate).Nonempty ∧
        rawLE (singles (mismatches anchor candidate)) alpha.val)

abbrev generator_nonnegative_and_total_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (anchor : Key I X T),
    (∀ x, 0 ≤ mass x) →
    (∀ beta, 0 ≤ weights mass anchor beta) ∧
      nodeTotal (weights mass anchor) = total mass - fullSourceMass mass anchor

abbrev generator_lower_cumulative_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (anchor : Key I X T) (alpha : Node I),
    cumulative (weights mass anchor) alpha = total mass - sourceMass mass anchor alpha

abbrev target_conditioning_mass_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (anchor : Key I X T),
    Law mass → 0 < targetMass mass anchor →
    Law (conditioned mass anchor) ∧
      ∀ event : Finset (Key I X T),
        PidFiniteConvergence.finiteEventMass (conditioned mass anchor) event =
          PidFiniteConvergence.finiteEventMass mass
            (event ∩ PidFiniteConvergence.targetBranchEvent anchor) / targetMass mass anchor

abbrev supported_anchor_domains_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (anchor : Key I X T),
    Law mass → 0 < mass anchor →
    0 < fullSourceMass mass anchor ∧ fullSourceMass mass anchor ≤ 1 ∧
    0 < targetMass mass anchor ∧ targetMass mass anchor ≤ 1 ∧
    conditioned mass anchor anchor = mass anchor / targetMass mass anchor ∧
    0 < conditioned mass anchor anchor ∧
    nodeTotal (weights mass anchor) = 1 - fullSourceMass mass anchor ∧
    0 ≤ nodeTotal (weights mass anchor) ∧ nodeTotal (weights mass anchor) < 1 ∧
    nodeTotal (weights (conditioned mass anchor) anchor) =
      1 - mass anchor / targetMass mass anchor ∧
    0 ≤ nodeTotal (weights (conditioned mass anchor) anchor) ∧
    nodeTotal (weights (conditioned mass anchor) anchor) < 1 ∧
    ∀ alpha : Node I,
      0 < sourceMass mass anchor alpha ∧ sourceMass mass anchor alpha ≤ 1 ∧
      0 < restrictedMass mass anchor alpha / targetMass mass anchor ∧
      restrictedMass mass anchor alpha / targetMass mass anchor ≤ 1 ∧
      cumulative (weights mass anchor) alpha = 1 - sourceMass mass anchor alpha ∧
      cumulative (weights (conditioned mass anchor) anchor) alpha =
        1 - restrictedMass mass anchor alpha / targetMass mass anchor

abbrev conditional_generator_support_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (anchor : Key I X T) (beta : Node I),
    Law mass → 0 < targetMass mass anchor →
    0 < weights (conditioned mass anchor) anchor beta → 0 < weights mass anchor beta

abbrev informative_inverse_identification_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (anchor : Key I X T),
    Law mass → 0 < fullSourceMass mass anchor →
    ∃ atoms : Node I → ℝ, InfInverse mass anchor atoms ∧ LogModel (weights mass anchor) atoms ∧
      ∀ other : Node I → ℝ, InfInverse mass anchor other → other = atoms

abbrev misinformative_inverse_identification_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (anchor : Key I X T),
    Law mass → 0 < mass anchor →
    ∃ atoms : Node I → ℝ, MisInverse mass anchor atoms ∧
      LogModel (weights (conditioned mass anchor) anchor) atoms ∧
      ∀ other : Node I → ℝ, MisInverse mass anchor other → other = atoms

abbrev component_nonnegative_strict_support_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (anchor : Key I X T) (plus minus : Node I → ℝ),
    Law mass → 0 < mass anchor → InfInverse mass anchor plus → MisInverse mass anchor minus →
    ∀ alpha : Node I, 0 ≤ plus alpha ∧ 0 ≤ minus alpha ∧
      (0 < plus alpha ↔ Generated (weights mass anchor) alpha) ∧
      (0 < minus alpha ↔ Generated (weights (conditioned mass anchor) anchor) alpha)

abbrev signed_mgw_cumulative_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (mass : Key I X T → ℝ) (anchor : Key I X T) (plus minus : Node I → ℝ),
    Law mass → 0 < mass anchor → InfInverse mass anchor plus → MisInverse mass anchor minus →
    ∀ alpha : Node I, cumulative (plus - minus) alpha =
      Real.log (restrictedMass mass anchor alpha /
        (sourceMass mass anchor alpha * targetMass mass anchor))

end PidMgwBridgeContract
