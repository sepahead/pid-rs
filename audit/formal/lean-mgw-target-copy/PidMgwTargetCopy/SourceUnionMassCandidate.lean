import PidMgwTargetCopy.Interface

set_option autoImplicit false
set_option warningAsError true

open PidFiniteConvergence

namespace PidMgwTargetCopy

universe u v

/-- Source-only L3 candidate; qualification and elaboration remain separate. -/
theorem sourceUnionMassTarget_candidate
    {sourceValue : Fin 2 → Type u} {B : Type v}
    [∀ i, Fintype (sourceValue i)] [Fintype B]
    [∀ i, DecidableEq (sourceValue i)] [DecidableEq B] :
    SourceUnionMassTarget (sourceValue := sourceValue) (B := B) := by
  unfold SourceUnionMassTarget
  intro law anchor
  have h_union :
      finiteEventMass law (sxPid2SourceEvent .redundancy anchor) +
          finiteEventMass law (sourceBranchEvent {0, 1} anchor) =
        finiteEventMass law (sourceBranchEvent {0} anchor) +
          finiteEventMass law (sourceBranchEvent {1} anchor) := by
    rw [sx_pid2_redundancy_source_event_eq_union anchor]
    rw [← source_singleton_branch_inter_eq_joint anchor]
    exact Finset.sum_union_inter
  simpa [sourceMass, sxPid2SourceEvent, sxPid2Collections, sxSourceEvent] using h_union

end PidMgwTargetCopy
