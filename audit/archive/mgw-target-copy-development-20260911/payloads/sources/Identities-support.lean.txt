import PidMgwTargetCopy.Interface
import PidMgwTargetCopyCandidate.L1
import PidMgwTargetCopyCandidate.L4
import PidMgwTargetCopyCandidate.L5

/-!
Unexecuted candidate for four unchanged target-copy propositions. The finite law, actual
MGW event masses, positive support and source marginal are the imported objects. Dependency
proofs and these exports must be separately compiled and checked before any proof claim.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators
open PidFiniteConvergence PidMgwTargetCopy

namespace PidMgwTargetCopyCandidate

universe u v

variable {sourceValue : Fin 2 → Type u} {B : Type v}
variable [∀ i, Fintype (sourceValue i)] [Fintype B]
variable [∀ i, DecidableEq (sourceValue i)] [DecidableEq B]

theorem localIdentity : LocalIdentityTarget (sourceValue := sourceValue) (B := B) := by
  unfold LocalIdentityTarget
  intro law hlaw hcopy anchor hpositive
  have hsource (node : SxPid2Node) : 0 < sourceMass law node anchor := by
    simpa only [sourceMass, sxPid2SourceEvent] using
      sx_source_event_mass_positive (sx_pid2_collections_nonempty node)
        law hlaw.1 anchor hpositive
  have htarget : 0 < targetMass law anchor := by
    simpa only [targetMass] using
      sx_target_event_mass_positive law hlaw.1 anchor hpositive
  have hunion : sourceMass law .redundancy anchor =
      sourceMass law .sourceOne anchor + sourceMass law .sourceTwo anchor -
        sourceMass law .jointSources anchor := by
    apply (eq_sub_iff_add_eq).2
    exact PidMgwTargetCopy.sourceUnionMassTarget_candidate law anchor
  have hd : 0 < sourceMass law .sourceOne anchor + sourceMass law .sourceTwo anchor -
      sourceMass law .jointSources anchor := by
    rw [← hunion]
    exact hsource .redundancy
  obtain ⟨hone, htwo, hjoint, hred⟩ := localCumulatives law hlaw hcopy anchor hpositive
  simp only [localAtomComponent, sxPid2MobiusTransform, localCumulativeComponent,
    localFormula]
  rw [hone, htwo, hjoint, hred]
  rw [Real.log_div hpositive.ne' (mul_ne_zero (hsource .jointSources).ne' htarget.ne'),
    Real.log_div hpositive.ne' (mul_ne_zero (hsource .sourceTwo).ne' htarget.ne'),
    Real.log_mul (hsource .jointSources).ne' htarget.ne',
    Real.log_mul (hsource .sourceTwo).ne' htarget.ne',
    Real.log_div (mul_ne_zero (hsource .sourceOne).ne' (hsource .sourceTwo).ne')
      (mul_ne_zero (hsource .jointSources).ne' hd.ne'),
    Real.log_mul (hsource .sourceOne).ne' (hsource .sourceTwo).ne',
    Real.log_mul (hsource .jointSources).ne' hd.ne']
  ring

theorem worldLocalIdentity :
    WorldLocalIdentityTarget (sourceValue := sourceValue) (B := B) := by
  unfold WorldLocalIdentityTarget
  intro law hlaw world hpositive
  obtain ⟨hpush, hcopy, hat, _⟩ := worldBridge law hlaw
  have hanchor : 0 < worldPushforward law (observe world) := by
    rw [hat world]
    exact hpositive
  exact localIdentity (worldPushforward law) hpush hcopy (observe world) hanchor

theorem averagedIdentity : AveragedIdentityTarget (sourceValue := sourceValue) (B := B) := by
  unfold AveragedIdentityTarget
  intro law hlaw hcopy
  obtain ⟨hmasses, hgroup⟩ := sourceProjection law hlaw.1
  calc
    averagedPointwiseAtomComponent law .net .synergy =
        ∑ anchor ∈ positiveMassSupport law,
          law anchor * rowFormula (sourceLaw law) anchor.1 := by
      unfold averagedPointwiseAtomComponent
      apply Finset.sum_congr rfl
      intro anchor hanchor
      have hpositive : 0 < law anchor := by
        simpa only [positiveMassSupport, Finset.mem_filter, Finset.mem_univ, true_and]
          using hanchor
      rw [localIdentity law hlaw hcopy anchor hpositive]
      obtain ⟨hone, htwo, hjoint⟩ := hmasses anchor
      simp only [localFormula, rowFormula, hone, htwo, hjoint]
    _ = ∑ row ∈ positiveMassSupport (sourceLaw law),
        sourceLaw law row * rowFormula (sourceLaw law) row :=
      hgroup (rowFormula (sourceLaw law))

theorem sameSourceLaw : SameSourceLawTarget (sourceValue := sourceValue) (B := B) := by
  unfold SameSourceLawTarget
  intro left right hleft hright hcopyLeft hcopyRight hequal
  rw [averagedIdentity left hleft hcopyLeft, averagedIdentity right hright hcopyRight, hequal]

end PidMgwTargetCopyCandidate
