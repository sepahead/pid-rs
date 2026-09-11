import PidMgwTargetCopy.Interface

/-!
One unexecuted candidate proof for the existing L2 proposition.
Reference elaboration and independent candidate checking remain pending.
-/

set_option autoImplicit false
set_option warningAsError true

open PidFiniteConvergence PidMgwTargetCopy

namespace PidMgwTargetCopyCandidate

universe u v

theorem copyEventMasses
    {sourceValue : Fin 2 → Type u} {B : Type v}
    [∀ i, Fintype (sourceValue i)] [Fintype B]
    [∀ i, DecidableEq (sourceValue i)] [DecidableEq B] :
    CopyEventMassesTarget (sourceValue := sourceValue) (B := B) := by
  classical
  intro law hcopy anchor hpositive
  have hanchor : anchor.2.1 = anchor.1 0 := hcopy anchor hpositive.ne'
  have target_implies_source (key : Key sourceValue B) (hkey : law key ≠ 0)
      (htarget : anchor.2 = key.2) : anchor.1 0 = key.1 0 := by
    calc
      anchor.1 0 = anchor.2.1 := hanchor.symm
      _ = key.2.1 := congrArg Prod.fst htarget
      _ = key.1 0 := hcopy key hkey
  have mass_congr (s t : Finset (Key sourceValue B))
      (hsupport : ∀ key, law key ≠ 0 → (key ∈ s ↔ key ∈ t)) :
      finiteEventMass law s = finiteEventMass law t := by
    change s.sum law = t.sum law
    calc
      s.sum law = (s ∩ t).sum law := by
        symm
        apply Finset.sum_subset Finset.inter_subset_left
        intro key hkey hnot
        by_contra hnonzero
        exact hnot (Finset.mem_inter.mpr ⟨hkey, (hsupport key hnonzero).mp hkey⟩)
      _ = t.sum law := by
        apply Finset.sum_subset Finset.inter_subset_right
        intro key hkey hnot
        by_contra hnonzero
        exact hnot (Finset.mem_inter.mpr ⟨(hsupport key hnonzero).mpr hkey, hkey⟩)
  have target_mem (key : Key sourceValue B) :
      key ∈ targetBranchEvent anchor ↔ anchor.2 = key.2 := by
    unfold targetBranchEvent
    rw [Finset.mem_filter]
    simp only [Finset.mem_univ, true_and, targetEquivalent]
  have hjoint : restrictedMass law .jointSources anchor = law anchor := by
    simp [restrictedMass, sxPid2TargetRestrictedEvent, sxPid2Collections,
      sxTargetRestrictedEvent, joint_source_target_branch_eq_singleton, finiteEventMass]
  refine ⟨?_, ?_, ?_, hjoint⟩
  · change finiteEventMass law (sxPid2TargetRestrictedEvent .sourceOne anchor) =
      finiteEventMass law (targetBranchEvent anchor)
    apply mass_congr
    intro key hkey
    have hiff : (anchor.1 0 = key.1 0 ∧ anchor.2 = key.2) ↔ anchor.2 = key.2 := by
      constructor
      · exact And.right
      · intro htarget
        exact ⟨target_implies_source key hkey htarget, htarget⟩
    rw [target_mem key]
    simpa [sxPid2TargetRestrictedEvent, sxPid2Collections, sxTargetRestrictedEvent,
      sourceTargetBranchEvent, sourceTargetCollectionEquivalent,
      sourceCollectionEquivalent, targetEquivalent] using hiff
  · change finiteEventMass law (sxPid2TargetRestrictedEvent .redundancy anchor) =
      finiteEventMass law (targetBranchEvent anchor)
    apply mass_congr
    intro key hkey
    have hiff :
        ((anchor.1 0 = key.1 0 ∧ anchor.2 = key.2) ∨
          (anchor.1 1 = key.1 1 ∧ anchor.2 = key.2)) ↔ anchor.2 = key.2 := by
      constructor
      · intro h
        exact h.elim And.right And.right
      · intro htarget
        exact Or.inl ⟨target_implies_source key hkey htarget, htarget⟩
    rw [target_mem key]
    simpa [sxPid2TargetRestrictedEvent, sxPid2Collections, sxTargetRestrictedEvent,
      sourceTargetBranchEvent, sourceTargetCollectionEquivalent,
      sourceCollectionEquivalent, targetEquivalent] using hiff
  · calc
      restrictedMass law .sourceTwo anchor = restrictedMass law .jointSources anchor := by
        change finiteEventMass law (sxPid2TargetRestrictedEvent .sourceTwo anchor) =
          finiteEventMass law (sxPid2TargetRestrictedEvent .jointSources anchor)
        apply mass_congr
        intro key hkey
        have hiff : (anchor.1 1 = key.1 1 ∧ anchor.2 = key.2) ↔
            ((anchor.1 0 = key.1 0 ∧ anchor.1 1 = key.1 1) ∧ anchor.2 = key.2) := by
          constructor
          · rintro ⟨hsecond, htarget⟩
            exact ⟨⟨target_implies_source key hkey htarget, hsecond⟩, htarget⟩
          · rintro ⟨⟨_, hsecond⟩, htarget⟩
            exact ⟨hsecond, htarget⟩
        simpa [sxPid2TargetRestrictedEvent, sxPid2Collections, sxTargetRestrictedEvent,
          sourceTargetBranchEvent, sourceTargetCollectionEquivalent,
          sourceCollectionEquivalent, targetEquivalent] using hiff
      _ = law anchor := hjoint

end PidMgwTargetCopyCandidate
