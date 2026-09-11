import PidMgwTargetCopy.Interface
import PidMgwTargetCopyCandidate.L2
import PidMgwTargetCopy.SourceUnionMassCandidate

/-!
One unexecuted candidate for the unchanged L4 proposition.
L2 and L3 are prospective proof imports, not axioms or admitted target predicates.
Their separate elaboration and independent checking, and this candidate's, remain pending.
-/

set_option autoImplicit false
set_option warningAsError true

open PidFiniteConvergence PidMgwTargetCopy

namespace PidMgwTargetCopyCandidate

universe u v

theorem localCumulatives
    {sourceValue : Fin 2 → Type u} {B : Type v}
    [∀ i, Fintype (sourceValue i)] [Fintype B]
    [∀ i, DecidableEq (sourceValue i)] [DecidableEq B] :
    LocalCumulativesTarget (sourceValue := sourceValue) (B := B) := by
  unfold LocalCumulativesTarget
  intro law hlaw hcopy anchor hpositive
  dsimp only
  have hsource (node : SxPid2Node) : 0 < sourceMass law node anchor := by
    simpa only [sourceMass, sxPid2SourceEvent] using
      sx_source_event_mass_positive (sx_pid2_collections_nonempty node)
        law hlaw.1 anchor hpositive
  have htarget : 0 < targetMass law anchor := by
    simpa only [targetMass] using
      sx_target_event_mass_positive law hlaw.1 anchor hpositive
  have hrestricted (node : SxPid2Node) : 0 < restrictedMass law node anchor := by
    simpa only [restrictedMass, sxPid2TargetRestrictedEvent] using
      sx_target_restricted_event_mass_positive (sx_pid2_collections_nonempty node)
        law hlaw.1 anchor hpositive
  have hlog (node : SxPid2Node) :
      localCumulativeNet law node anchor =
        Real.log (restrictedMass law node anchor /
          (sourceMass law node anchor * targetMass law anchor)) := by
    simpa only [probabilityNetArgument, restrictedMass, sourceMass, targetMass] using
      local_cumulative_net_eq_log_probability_argument law node anchor
        (hsource node) htarget (hrestricted node)
  obtain ⟨h_one, h_redundancy, h_two, h_joint⟩ :=
    PidMgwTargetCopyCandidate.copyEventMasses
      (sourceValue := sourceValue) (B := B) law hcopy anchor hpositive
  have h_union :
      sourceMass law .redundancy anchor =
        sourceMass law .sourceOne anchor + sourceMass law .sourceTwo anchor -
          sourceMass law .jointSources anchor := by
    apply (eq_sub_iff_add_eq).2
    exact PidMgwTargetCopy.sourceUnionMassTarget_candidate
      (sourceValue := sourceValue) (B := B) law anchor
  have hcopied (node : SxPid2Node)
      (h_restricted_copy : restrictedMass law node anchor = targetMass law anchor) :
      localCumulativeNet law node anchor = -Real.log (sourceMass law node anchor) := by
    rw [hlog node, h_restricted_copy,
      Real.log_div htarget.ne' (mul_ne_zero (hsource node).ne' htarget.ne'),
      Real.log_mul (hsource node).ne' htarget.ne']
    ring
  refine ⟨hcopied .sourceOne h_one, ?_, ?_, ?_⟩
  · simpa only [h_two] using hlog .sourceTwo
  · simpa only [h_joint] using hlog .jointSources
  · calc
      localCumulativeNet law .redundancy anchor =
          -Real.log (sourceMass law .redundancy anchor) :=
        hcopied .redundancy h_redundancy
      _ = -Real.log
          (sourceMass law .sourceOne anchor + sourceMass law .sourceTwo anchor -
            sourceMass law .jointSources anchor) :=
        congrArg (fun mass : ℝ => -Real.log mass) h_union

end PidMgwTargetCopyCandidate
