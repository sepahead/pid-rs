import PidFiniteConvergence.FractionalCover

/-!
# Exact two-source count/event bridge for categorical shared exclusions

For two heterogeneous finite source alphabets and one finite target alphabet, this module fixes the
four cumulative two-source shared-exclusions nodes, turns an arbitrary natural-valued count
function with positive total into its exact empirical law, and proves the event-count formula for
each supported averaged signed-net cumulative.

The result is exact supplied-count mathematics over `Nat`, `Rat`, and `Real`. It does not model or
verify histogram extraction, row sorting, the Rust `NODES2` or `invert2` implementations, integer
overflow, binary64 or MPFR arithmetic, Python, the standalone certifier, parsing, JSON, allocation,
or resource behavior. It does not prove a sampling or population theorem, calibration, consumer
validity, a concrete Mobius inversion, atom identities, or any extension beyond two sources.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators

namespace PidFiniteConvergence

universe v w x

/-- The four cumulative nodes used by the two-source categorical SxPID construction. -/
inductive SxPid2Node where
  | sourceOne
  | sourceTwo
  | jointSources
  | redundancy
deriving DecidableEq, Fintype

/-- The source collections defining each fixed two-source cumulative node. -/
def sxPid2Collections : SxPid2Node → Finset (Finset (Fin 2))
  | .sourceOne => {{0}}
  | .sourceTwo => {{1}}
  | .jointSources => {{0, 1}}
  | .redundancy => {{0}, {1}}

theorem sx_pid2_node_collection_semantics :
    sxPid2Collections .sourceOne = {{0}} ∧
      sxPid2Collections .sourceTwo = {{1}} ∧
        sxPid2Collections .jointSources = {{0, 1}} ∧
          sxPid2Collections .redundancy = {{0}, {1}} := by
  simp [sxPid2Collections]

theorem sx_pid2_collections_nonempty (node : SxPid2Node) :
    (sxPid2Collections node).Nonempty := by
  cases node <;> simp [sxPid2Collections]

/-- Sum of an exact count function over the complete finite categorical key space. -/
noncomputable def totalCount
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ) : ℕ :=
  ∑ key, count key

/-- Complete keys with strictly positive exact count. -/
noncomputable def positiveSupport
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ) :
    Finset (CategoricalKey (Fin 2) sourceValue targetValue) :=
  Finset.univ.filter fun key => 0 < count key

/-- Sum of an exact count function over a supplied finite event. -/
def eventCount {key : Type x} (count : key → ℕ) (event : Finset key) : ℕ :=
  ∑ candidate ∈ event, count candidate

/-- Exact real empirical law induced by a natural-valued count function. -/
noncomputable def empiricalLaw
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ) :
    CategoricalKey (Fin 2) sourceValue targetValue → ℝ :=
  fun key => (count key : ℝ) / (totalCount count : ℝ)

theorem empirical_law_nonnegative
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (key : CategoricalKey (Fin 2) sourceValue targetValue) :
    0 ≤ empiricalLaw count key := by
  unfold empiricalLaw
  positivity

theorem sum_empirical_law_eq_one
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (h_total : 0 < totalCount count) :
    ∑ key, empiricalLaw count key = 1 := by
  simp only [empiricalLaw, totalCount, Nat.cast_sum]
  simp only [div_eq_mul_inv]
  rw [← Finset.sum_mul]
  apply mul_inv_cancel₀
  exact_mod_cast h_total.ne'

/-- Source event for a fixed two-source cumulative node and keyed anchor. -/
noncomputable def sxPid2SourceEvent
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    Finset (CategoricalKey (Fin 2) sourceValue targetValue) :=
  sxSourceEvent (sxPid2Collections node) anchor

/-- Target-restricted source event for a fixed cumulative node and keyed anchor. -/
noncomputable def sxPid2TargetRestrictedEvent
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    Finset (CategoricalKey (Fin 2) sourceValue targetValue) :=
  sxTargetRestrictedEvent (sxPid2Collections node) anchor

/-- Probability-domain argument of the supported local signed-net logarithm. -/
noncomputable def probabilityNetArgument
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) : ℝ :=
  finiteEventMass law (sxPid2TargetRestrictedEvent node anchor) /
    (finiteEventMass law (sxPid2SourceEvent node anchor) *
      finiteEventMass law (targetBranchEvent anchor))

/-- Exact rational count-domain argument of the supported local signed-net logarithm. -/
noncomputable def countNetArgument
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) : ℚ :=
  ((totalCount count : ℕ) : ℚ) *
      ((eventCount count (sxPid2TargetRestrictedEvent node anchor) : ℕ) : ℚ) /
    (((eventCount count (sxPid2SourceEvent node anchor) : ℕ) : ℚ) *
      ((eventCount count (targetBranchEvent anchor) : ℕ) : ℚ))

/-- Local informative cumulative, in nats. -/
noncomputable def localCumulativeInformative
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) : ℝ :=
  -Real.log (finiteEventMass law (sxPid2SourceEvent node anchor))

/-- Local misinformative cumulative, in nats. -/
noncomputable def localCumulativeMisinformative
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) : ℝ :=
  Real.log
    (finiteEventMass law (targetBranchEvent anchor) /
      finiteEventMass law (sxPid2TargetRestrictedEvent node anchor))

/-- Local signed-net cumulative, informative minus misinformative, in nats. -/
noncomputable def localCumulativeNet
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) : ℝ :=
  localCumulativeInformative law node anchor -
    localCumulativeMisinformative law node anchor

/-- Positive-mass average of one fixed signed-net cumulative, in nats. -/
noncomputable def averagedCumulativeNet
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (node : SxPid2Node) : ℝ :=
  ∑ anchor ∈ positiveMassSupport law,
    law anchor * localCumulativeNet law node anchor

theorem event_mass_empirical_law_eq_count_ratio
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (event : Finset (CategoricalKey (Fin 2) sourceValue targetValue)) :
    finiteEventMass (empiricalLaw count) event =
      (eventCount count event : ℝ) / (totalCount count : ℝ) := by
  simp only [finiteEventMass, empiricalLaw, eventCount, Nat.cast_sum]
  simp [div_eq_mul_inv, Finset.sum_mul]

theorem positive_mass_support_empirical_law
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (h_total : 0 < totalCount count) :
    positiveMassSupport (empiricalLaw count) = positiveSupport count := by
  ext key
  simp [positiveMassSupport, positiveSupport, empiricalLaw, h_total]

theorem local_cumulative_net_eq_log_probability_argument
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue)
    (h_source : 0 < finiteEventMass law (sxPid2SourceEvent node anchor))
    (h_target : 0 < finiteEventMass law (targetBranchEvent anchor))
    (h_restricted : 0 < finiteEventMass law (sxPid2TargetRestrictedEvent node anchor)) :
    localCumulativeNet law node anchor =
      Real.log (probabilityNetArgument law node anchor) := by
  unfold localCumulativeNet localCumulativeInformative localCumulativeMisinformative
    probabilityNetArgument
  rw [Real.log_div h_target.ne' h_restricted.ne']
  rw [Real.log_div h_restricted.ne' (mul_ne_zero h_source.ne' h_target.ne')]
  rw [Real.log_mul h_source.ne' h_target.ne']
  ring

theorem sx_pid2_redundancy_source_event_eq_union
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    sxPid2SourceEvent .redundancy anchor =
      sourceBranchEvent {0} anchor ∪ sourceBranchEvent {1} anchor := by
  simp [sxPid2SourceEvent, sxPid2Collections, sxSourceEvent]

theorem sx_pid2_redundancy_target_restricted_event_eq_union
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    sxPid2TargetRestrictedEvent .redundancy anchor =
      sourceTargetBranchEvent {0} anchor ∪ sourceTargetBranchEvent {1} anchor := by
  simp [sxPid2TargetRestrictedEvent, sxPid2Collections, sxTargetRestrictedEvent]

theorem source_singleton_branch_inter_eq_joint
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    sourceBranchEvent {0} anchor ∩ sourceBranchEvent {1} anchor =
      sourceBranchEvent {0, 1} anchor := by
  ext candidate
  simp [sourceBranchEvent, sourceCollectionEquivalent]

theorem source_target_singleton_branch_inter_eq_joint
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    sourceTargetBranchEvent {0} anchor ∩ sourceTargetBranchEvent {1} anchor =
      sourceTargetBranchEvent {0, 1} anchor := by
  ext candidate
  simp [sourceTargetBranchEvent, sourceTargetCollectionEquivalent,
    sourceCollectionEquivalent, targetEquivalent]
  aesop

theorem joint_source_target_branch_eq_singleton
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    sourceTargetBranchEvent {0, 1} anchor = {anchor} := by
  ext candidate
  simp only [sourceTargetBranchEvent, Finset.mem_filter, Finset.mem_univ, true_and,
    sourceTargetCollectionEquivalent, sourceCollectionEquivalent, Finset.mem_insert,
    Finset.mem_singleton, targetEquivalent]
  constructor
  · rintro ⟨hsource, htarget⟩
    apply Prod.ext
    · funext source
      fin_cases source
      · exact (hsource 0 (by simp)).symm
      · exact (hsource 1 (by simp)).symm
    · exact htarget.symm
  · rintro rfl
    exact ⟨fun _ _ => rfl, rfl⟩

theorem redundancy_source_event_count_inclusion_exclusion
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    eventCount count (sxPid2SourceEvent .redundancy anchor) +
        eventCount count (sourceBranchEvent {0, 1} anchor) =
      eventCount count (sourceBranchEvent {0} anchor) +
        eventCount count (sourceBranchEvent {1} anchor) := by
  rw [sx_pid2_redundancy_source_event_eq_union]
  rw [← source_singleton_branch_inter_eq_joint]
  exact Finset.sum_union_inter

theorem redundancy_target_restricted_event_count_inclusion_exclusion
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    eventCount count (sxPid2TargetRestrictedEvent .redundancy anchor) +
        eventCount count (sourceTargetBranchEvent {0, 1} anchor) =
      eventCount count (sourceTargetBranchEvent {0} anchor) +
        eventCount count (sourceTargetBranchEvent {1} anchor) := by
  rw [sx_pid2_redundancy_target_restricted_event_eq_union]
  rw [← source_target_singleton_branch_inter_eq_joint]
  exact Finset.sum_union_inter

theorem redundancy_source_event_count_eq_add_sub_joint
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    eventCount count (sxPid2SourceEvent .redundancy anchor) =
      eventCount count (sourceBranchEvent {0} anchor) +
        eventCount count (sourceBranchEvent {1} anchor) -
          eventCount count (sourceBranchEvent {0, 1} anchor) := by
  have h := redundancy_source_event_count_inclusion_exclusion count anchor
  omega

theorem redundancy_target_restricted_event_count_eq_add_sub_joint
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    eventCount count (sxPid2TargetRestrictedEvent .redundancy anchor) =
      eventCount count (sourceTargetBranchEvent {0} anchor) +
        eventCount count (sourceTargetBranchEvent {1} anchor) -
          eventCount count (sourceTargetBranchEvent {0, 1} anchor) := by
  have h := redundancy_target_restricted_event_count_inclusion_exclusion count anchor
  omega

theorem joint_source_target_restricted_event_count_eq_anchor
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    eventCount count (sxPid2TargetRestrictedEvent .jointSources anchor) = count anchor := by
  rw [show sxPid2TargetRestrictedEvent .jointSources anchor =
      sourceTargetBranchEvent {0, 1} anchor by
    simp [sxPid2TargetRestrictedEvent, sxPid2Collections, sxTargetRestrictedEvent]]
  rw [joint_source_target_branch_eq_singleton]
  simp [eventCount]

theorem event_count_positive_of_mem
    {key : Type x} [DecidableEq key]
    (count : key → ℕ) {event : Finset key} {anchor : key}
    (hanchor : anchor ∈ event) (hcount : 0 < count anchor) :
    0 < eventCount count event := by
  have hle : count anchor ≤ eventCount count event := by
    exact Finset.single_le_sum (fun candidate _ => Nat.zero_le (count candidate)) hanchor
  exact hcount.trans_le hle

theorem sx_pid2_event_counts_positive_on_support
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    {anchor : CategoricalKey (Fin 2) sourceValue targetValue}
    (hanchor : anchor ∈ positiveSupport count) :
    0 < eventCount count (sxPid2SourceEvent node anchor) ∧
      0 < eventCount count (targetBranchEvent anchor) ∧
        0 < eventCount count (sxPid2TargetRestrictedEvent node anchor) := by
  have hcount : 0 < count anchor := (Finset.mem_filter.mp hanchor).2
  exact
    ⟨event_count_positive_of_mem count
        (sx_source_event_anchor_mem (sx_pid2_collections_nonempty node) anchor) hcount,
      event_count_positive_of_mem count (target_branch_anchor_mem anchor) hcount,
      event_count_positive_of_mem count
        (sx_target_restricted_event_anchor_mem
          (sx_pid2_collections_nonempty node) anchor) hcount⟩

theorem count_net_argument_positive_on_support
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    {anchor : CategoricalKey (Fin 2) sourceValue targetValue}
    (h_total : 0 < totalCount count)
    (hanchor : anchor ∈ positiveSupport count) :
    0 < countNetArgument count node anchor := by
  obtain ⟨hsource, htarget, hrestricted⟩ :=
    sx_pid2_event_counts_positive_on_support count node hanchor
  unfold countNetArgument
  positivity

theorem probability_net_argument_empirical_eq_count_net_argument
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue)
    (h_total : 0 < totalCount count)
    (h_source : 0 < eventCount count (sxPid2SourceEvent node anchor))
    (h_target : 0 < eventCount count (targetBranchEvent anchor)) :
    probabilityNetArgument (empiricalLaw count) node anchor =
      ((countNetArgument count node anchor : ℚ) : ℝ) := by
  unfold probabilityNetArgument countNetArgument
  simp only [event_mass_empirical_law_eq_count_ratio, Rat.cast_div, Rat.cast_mul,
    Rat.cast_natCast]
  field_simp

theorem sx_pid2_empirical_event_masses_positive_on_support
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    {anchor : CategoricalKey (Fin 2) sourceValue targetValue}
    (h_total : 0 < totalCount count)
    (hanchor : anchor ∈ positiveSupport count) :
    0 < finiteEventMass (empiricalLaw count) (sxPid2SourceEvent node anchor) ∧
      0 < finiteEventMass (empiricalLaw count) (targetBranchEvent anchor) ∧
        0 < finiteEventMass (empiricalLaw count)
          (sxPid2TargetRestrictedEvent node anchor) := by
  obtain ⟨hsource, htarget, hrestricted⟩ :=
    sx_pid2_event_counts_positive_on_support count node hanchor
  simp only [event_mass_empirical_law_eq_count_ratio]
  exact ⟨by positivity, by positivity, by positivity⟩

theorem local_cumulative_net_empirical_eq_log_count_net_argument
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    {anchor : CategoricalKey (Fin 2) sourceValue targetValue}
    (h_total : 0 < totalCount count)
    (hanchor : anchor ∈ positiveSupport count) :
    localCumulativeNet (empiricalLaw count) node anchor =
      Real.log ((countNetArgument count node anchor : ℚ) : ℝ) := by
  obtain ⟨hsourceMass, htargetMass, hrestrictedMass⟩ :=
    sx_pid2_empirical_event_masses_positive_on_support count node h_total hanchor
  rw [local_cumulative_net_eq_log_probability_argument
    (empiricalLaw count) node anchor hsourceMass htargetMass hrestrictedMass]
  rw [probability_net_argument_empirical_eq_count_net_argument]
  · exact h_total
  · exact (sx_pid2_event_counts_positive_on_support count node hanchor).1
  · exact (sx_pid2_event_counts_positive_on_support count node hanchor).2.1

theorem sxpid2_averaged_cumulative_net_count_expression
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    (h_total : 0 < totalCount count) :
    averagedCumulativeNet (empiricalLaw count) node =
      ∑ anchor ∈ positiveSupport count,
        ((count anchor : ℝ) / (totalCount count : ℝ)) *
          Real.log ((countNetArgument count node anchor : ℚ) : ℝ) := by
  unfold averagedCumulativeNet
  rw [positive_mass_support_empirical_law count h_total]
  apply Finset.sum_congr rfl
  intro anchor hanchor
  rw [local_cumulative_net_empirical_eq_log_count_net_argument
    count node h_total hanchor]
  rfl

end PidFiniteConvergence
