import PidMgwBridge.Contract
import MgwBridgeDepsV1.SxDnf.Proofs
import MgwBridgeDepsV1.JoinLog.Proofs
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators
open PidMgwBridgeContract
universe u v w
namespace PidMgwBridgeCandidate

private lemma raw_refl {I : Type u} (a : Finset (Finset I)) : rawLE a a := by
  intro b hb
  exact ⟨b, hb, Finset.Subset.refl b⟩

private lemma raw_trans {I : Type u} {a b c : Finset (Finset I)}
    (hab : rawLE a b) (hbc : rawLE b c) : rawLE a c := by
  intro x hx
  obtain ⟨y, hy, hyx⟩ := hbc x hx
  obtain ⟨z, hz, hzy⟩ := hab y hy
  exact ⟨z, hz, hzy.trans hyx⟩

private lemma minimal_below {I : Type u} [DecidableEq I]
    (family : Finset (Finset I)) (s : Finset I) (hs : s ∈ family) :
    ∃ m ∈ family, m ⊆ s ∧ ∀ o ∈ family, o ⊆ m → o = m := by
  classical
  obtain ⟨m, hm, hmin⟩ := (family.filter fun x => x ⊆ s).exists_min_image Finset.card
    ⟨s, by simp [hs]⟩
  have hmp := Finset.mem_filter.mp hm
  refine ⟨m, hmp.1, hmp.2, ?_⟩
  intro o ho hom
  apply Finset.eq_of_subset_of_card_le hom
  exact hmin o (Finset.mem_filter.mpr ⟨ho, hom.trans hmp.2⟩)

private lemma raw_join_facts {I : Type u} [DecidableEq I]
    (a b : Finset (Finset I)) (ha : Valid a) (hb : Valid b) :
    Valid (rawJoin a b) ∧ ∀ c, rawLE (rawJoin a b) c ↔ rawLE a c ∧ rawLE b c := by
  classical
  let unions := a.biUnion fun x => b.image fun y => x ∪ y
  have below (s : Finset I) (hs : s ∈ unions) :
      ∃ m ∈ rawJoin a b, m ⊆ s := by
    obtain ⟨m, hm, hms, hmin⟩ := minimal_below unions s hs
    exact ⟨m, Finset.mem_filter.mpr ⟨hm, hmin⟩, hms⟩
  have union_members (s : Finset I) (hs : s ∈ unions) :
      ∃ x ∈ a, ∃ y ∈ b, x ∪ y = s := by
    obtain ⟨x, hx, hs⟩ := Finset.mem_biUnion.mp hs
    obtain ⟨y, hy, hxy⟩ := Finset.mem_image.mp hs
    exact ⟨x, hx, y, hy, hxy⟩
  constructor
  · refine ⟨?_, ?_, ?_⟩
    · obtain ⟨x, hx⟩ := ha.1
      obtain ⟨y, hy⟩ := hb.1
      obtain ⟨m, hm, _⟩ := below (x ∪ y)
        (Finset.mem_biUnion.mpr ⟨x, hx, Finset.mem_image.mpr ⟨y, hy, rfl⟩⟩)
      exact ⟨m, hm⟩
    · intro s hs
      obtain ⟨x, hx, y, _hy, rfl⟩ := union_members s (Finset.mem_filter.mp hs).1
      exact (ha.2.1 x hx).mono Finset.subset_union_left
    · intro x hx y hy hxy
      exact (Finset.mem_filter.mp hy).2 x (Finset.mem_filter.mp hx).1 hxy
  · intro c
    constructor
    · intro h
      constructor <;> intro s hs
      · obtain ⟨m, hm, hms⟩ := h s hs
        obtain ⟨x, hx, y, _hy, hxy⟩ := union_members m (Finset.mem_filter.mp hm).1
        exact ⟨x, hx, Finset.Subset.trans (hxy ▸ Finset.subset_union_left) hms⟩
      · obtain ⟨m, hm, hms⟩ := h s hs
        obtain ⟨x, _hx, y, hy, hxy⟩ := union_members m (Finset.mem_filter.mp hm).1
        exact ⟨y, hy, Finset.Subset.trans (hxy ▸ Finset.subset_union_right) hms⟩
    · rintro ⟨hac, hbc⟩ s hs
      obtain ⟨x, hx, hxs⟩ := hac s hs
      obtain ⟨y, hy, hys⟩ := hbc s hs
      obtain ⟨m, hm, hmu⟩ := below (x ∪ y)
        (Finset.mem_biUnion.mpr ⟨x, hx, Finset.mem_image.mpr ⟨y, hy, rfl⟩⟩)
      exact ⟨m, hm, hmu.trans (Finset.union_subset hxs hys)⟩

private lemma proof_actual_join_lub : actual_join_lub_target.{u} := by
  classical
  intro I _ _ _
  have facts (a b : Node I) := raw_join_facts a.val b.val a.property b.property
  constructor
  · intro a b
    exact ⟨(facts a b).1, fun c => (facts a b).2 c.val⟩
  · let join (a b : Node I) : Node I := ⟨rawJoin a.val b.val, (facts a b).1⟩
    let sigma : SemilatticeSup (Node I) := {
      le := fun a b => rawLE a.val b.val
      lt := fun a b => rawLE a.val b.val ∧ ¬rawLE b.val a.val
      lt_iff_le_not_ge := fun _ _ => Iff.rfl
      le_refl := fun a => raw_refl a.val
      le_trans := fun _ _ _ => raw_trans
      le_antisymm := fun a b hab hba => Subtype.ext
        (PidSxDnfOrderCandidate.antichain_antisymm I a.val b.val a.property.2.2
          b.property.2.2 hab hba)
      sup := join
      le_sup_left := fun a b => ((facts a b).2 (join a b).val).1 (raw_refl _) |>.1
      le_sup_right := fun a b => ((facts a b).2 (join a b).val).1 (raw_refl _) |>.2
      sup_le := fun a b c hac hbc => ((facts a b).2 c.val).2 ⟨hac, hbc⟩ }
    exact ⟨sigma, (fun _ _ => Iff.rfl), (fun _ _ => rfl)⟩

private lemma singles_valid {I : Type u} [DecidableEq I] (missing : Finset I)
    (hne : missing.Nonempty) : Valid (singles missing) := by
  classical
  refine ⟨hne.image _, ?_, ?_⟩
  · intro a ha
    obtain ⟨i, _hi, rfl⟩ := Finset.mem_image.mp ha
    exact Finset.singleton_nonempty i
  · intro a ha b hb hab
    obtain ⟨i, _hi, rfl⟩ := Finset.mem_image.mp ha
    obtain ⟨j, _hj, rfl⟩ := Finset.mem_image.mp hb
    exact congrArg (fun x : I => ({x} : Finset I))
      (Finset.mem_singleton.mp (hab (Finset.mem_singleton_self i)))

private lemma mismatch_full {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (z x : Key I X T) : (mismatches z x).Nonempty ↔
      x ∉ PidFiniteConvergence.sourceBranchEvent Finset.univ z := by
  classical
  simp only [mismatches, Finset.filter_nonempty_iff, Finset.mem_univ, true_and,
    PidFiniteConvergence.sourceBranchEvent, Finset.mem_filter,
    PidFiniteConvergence.sourceCollectionEquivalent, true_and]
  push Not
  constructor
  · rintro ⟨i, hi⟩
    exact ⟨i, trivial, Ne.symm hi⟩
  · rintro ⟨i, _hi, hi⟩
    exact ⟨i, Ne.symm hi⟩

private lemma proof_mismatch_generator_and_exclusion : mismatch_generator_and_exclusion_target.{u,v,w} := by
  classical
  constructor
  · intro I _ _ _ missing hm
    exact singles_valid missing hm
  · intro I X T _ _ _ _ _ _ _ z x alpha
    rw [PidSxDnfOrderCandidate.source_event_iff_dnf I X T alpha.val z x]
    simp only [PidSxDnfOrderContract.DNF, PidSxDnfOrderContract.EqualityPattern]
    constructor
    · intro hn
      have each (a : Finset I) (ha : a ∈ alpha.val) : ∃ i ∈ a, x.1 i ≠ z.1 i := by
        by_contra h
        push Not at h
        exact hn ⟨a, ha, fun i hi => decide_eq_true (h i hi).symm⟩
      obtain ⟨a, ha⟩ := alpha.property.1
      obtain ⟨i, _hi, hne⟩ := each a ha
      refine ⟨Finset.filter_nonempty_iff.mpr ⟨i, Finset.mem_univ i, hne⟩, ?_⟩
      intro b hb
      obtain ⟨j, hj, hne⟩ := each b hb
      exact ⟨{j}, Finset.mem_image.mpr ⟨j,
        Finset.mem_filter.mpr ⟨Finset.mem_univ j, hne⟩, rfl⟩,
        Finset.singleton_subset_iff.mpr hj⟩
    · rintro ⟨_hne, hle⟩ ⟨a, ha, hp⟩
      obtain ⟨b, hb, hba⟩ := hle a ha
      obtain ⟨i, hi, rfl⟩ := Finset.mem_image.mp hb
      exact (Finset.mem_filter.mp hi).2
        (of_decide_eq_true (hp i (hba (Finset.mem_singleton_self i)))).symm

private lemma event_complement {K : Type u} [Fintype K] [DecidableEq K] (mass : K → ℝ)
    (event : Finset K) : (∑ x, if x ∉ event then mass x else 0) =
      total mass - PidFiniteConvergence.finiteEventMass mass event := by
  classical
  have he : PidFiniteConvergence.finiteEventMass mass event =
      ∑ x, if x ∈ event then mass x else 0 := by
    rw [← Finset.sum_filter]
    simp [PidFiniteConvergence.finiteEventMass]
  rw [he]
  change _ = (∑ x, mass x) - _
  rw [← Finset.sum_sub_distrib]
  apply Finset.sum_congr rfl
  intro x _hx
  by_cases hx : x ∈ event <;> simp [hx]

private lemma weight_pushforward {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (mass : Key I X T → ℝ) (z : Key I X T) (test : Node I → Prop) [DecidablePred test] :
    (letI := nodeFintype I; ∑ b : Node I, if test b then weights mass z b else 0) =
      ∑ x, if h : (mismatches z x).Nonempty then
        if test ⟨singles (mismatches z x), singles_valid _ h⟩ then mass x else 0 else 0 := by
  classical
  let : Fintype (Node I) := nodeFintype I
  unfold weights
  have move (b : Node I) :
      (if test b then ∑ x, if (mismatches z x).Nonempty ∧ singles (mismatches z x) = b.val
          then mass x else 0 else 0) =
      ∑ x, if test b ∧ (mismatches z x).Nonempty ∧ singles (mismatches z x) = b.val
        then mass x else 0 := by
    by_cases h : test b <;> simp [h]
  simp_rw [move]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro x _hx
  by_cases hn : (mismatches z x).Nonempty
  · let b : Node I := ⟨singles (mismatches z x), singles_valid _ hn⟩
    have he (c : Node I) : singles (mismatches z x) = c.val ↔ c = b := by
      constructor
      · intro h; exact Subtype.ext h.symm
      · intro h; subst c; rfl
    simp_rw [he]
    simp only [hn, true_and, dite_true]
    rw [Finset.sum_eq_single b]
    · simp [b]
    · intro c _hc hcb; simp [hcb]
    · simp
  · simp [hn]

private lemma proof_generator_nonnegative_and_total : generator_nonnegative_and_total_target.{u,v,w} := by
  classical
  intro I X T _ _ _ _ _ _ _ mass z hm
  constructor
  · intro b
    exact Finset.sum_nonneg (fun x _ => ite_nonneg (hm x) (le_refl 0))
  · have h := weight_pushforward mass z (fun _ => True)
    simp only [ite_true] at h
    rw [show nodeTotal (weights mass z) = (letI := nodeFintype I;
      ∑ b : Node I, weights mass z b) by rfl, h]
    calc
      _ = ∑ x, if x ∉ PidFiniteConvergence.sourceBranchEvent Finset.univ z then mass x else 0 := by
        apply Finset.sum_congr rfl
        intro x _hx
        simp [mismatch_full]
      _ = _ := event_complement mass _

private lemma proof_generator_lower_cumulative : generator_lower_cumulative_target.{u,v,w} := by
  classical
  intro I X T _ _ _ _ _ _ _ mass z alpha
  have h := weight_pushforward mass z (fun b => rawLE b.val alpha.val)
  change (letI := nodeFintype I; ∑ b : Node I,
    if rawLE b.val alpha.val then weights mass z b else 0) = _
  rw [h]
  calc
    _ = ∑ x, if x ∉ PidFiniteConvergence.sxSourceEvent alpha.val z then mass x else 0 := by
      apply Finset.sum_congr rfl
      intro x _hx
      simp only [proof_mismatch_generator_and_exclusion.2 I X T z x alpha]
      by_cases hn : (mismatches z x).Nonempty <;> simp [hn]
    _ = _ := event_complement mass _

private lemma event_bounds {K : Type u} [Fintype K] (mass : K → ℝ)
    (hm : Law mass) (event : Finset K) :
    0 ≤ PidFiniteConvergence.finiteEventMass mass event ∧
      PidFiniteConvergence.finiteEventMass mass event ≤ 1 := by
  classical
  constructor
  · exact Finset.sum_nonneg (fun x _ => hm.1 x)
  · change (∑ x ∈ event, mass x) ≤ 1
    rw [← hm.2]
    exact Finset.sum_le_sum_of_subset_of_nonneg (Finset.subset_univ _)
      (fun x _ _ => hm.1 x)

private lemma event_anchor_positive {K : Type u} [Fintype K] (mass : K → ℝ)
    (hm : ∀ x, 0 ≤ mass x) (z : K) (hz : 0 < mass z)
    (event : Finset K) (he : z ∈ event) :
    0 < PidFiniteConvergence.finiteEventMass mass event := by
  exact lt_of_lt_of_le hz (Finset.single_le_sum (fun x _ => hm x) he)

private lemma proof_target_conditioning_mass : target_conditioning_mass_target.{u,v,w} := by
  classical
  intro I X T _ _ _ _ _ _ _ mass z hm ht
  have he (event : Finset (Key I X T)) :
      PidFiniteConvergence.finiteEventMass (conditioned mass z) event =
      PidFiniteConvergence.finiteEventMass mass
        (event ∩ PidFiniteConvergence.targetBranchEvent z) / targetMass mass z := by
    unfold PidFiniteConvergence.finiteEventMass conditioned
    simp only [div_eq_mul_inv, Finset.sum_mul]
    rw [← Finset.filter_mem_eq_inter, Finset.sum_filter]
  refine ⟨⟨?_, ?_⟩, he⟩
  · intro x
    exact ite_nonneg (div_nonneg (hm.1 x) ht.le) (le_refl 0)
  · have h := he Finset.univ
    change (∑ x, conditioned mass z x) = 1
    calc
      _ = targetMass mass z / targetMass mass z := by
        simpa only [PidFiniteConvergence.finiteEventMass, Finset.univ_inter, targetMass] using h
      _ = 1 := div_self (ne_of_gt ht)

private lemma anchor_source_mem {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (z : Key I X T) : z ∈ PidFiniteConvergence.sourceBranchEvent Finset.univ z := by
  simp [PidFiniteConvergence.sourceBranchEvent, PidFiniteConvergence.sourceCollectionEquivalent]

private lemma anchor_target_mem {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (z : Key I X T) : z ∈ PidFiniteConvergence.targetBranchEvent z := by
  exact PidFiniteConvergence.target_branch_anchor_mem z

private lemma conditional_full {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (mass : Key I X T → ℝ) (z : Key I X T) (hm : Law mass)
    (ht : 0 < targetMass mass z) :
    fullSourceMass (conditioned mass z) z = mass z / targetMass mass z := by
  classical
  have he := (proof_target_conditioning_mass I X T mass z hm ht).2
    (PidFiniteConvergence.sourceBranchEvent Finset.univ z)
  have hs : PidFiniteConvergence.sourceBranchEvent Finset.univ z ∩
      PidFiniteConvergence.targetBranchEvent z = {z} := by
    ext x
    rw [Finset.mem_inter, Finset.mem_singleton]
    constructor
    · rintro ⟨hsource, htarget⟩
      have hs := (PidFiniteConvergence.source_branch_is_equivalence_class
        (Finset.univ : Finset I)).2 z x |>.1 hsource
      have ht := PidFiniteConvergence.target_branch_is_equivalence_class.2 z x |>.1 htarget
      exact Prod.ext (funext fun i => (hs i (Finset.mem_univ i)).symm) ht.symm
    · intro h
      subst x
      exact ⟨anchor_source_mem z, anchor_target_mem z⟩
  simpa [fullSourceMass, hs, PidFiniteConvergence.finiteEventMass] using he

private lemma conditional_source {I : Type u} {X : I → Type v} {T : Type w}
    [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
    (mass : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (hm : Law mass)
    (ht : 0 < targetMass mass z) :
    sourceMass (conditioned mass z) z alpha = restrictedMass mass z alpha / targetMass mass z := by
  simpa [sourceMass, restrictedMass, PidFiniteConvergence.sx_target_restricted_event_eq_inter]
    using (proof_target_conditioning_mass I X T mass z hm ht).2
      (PidFiniteConvergence.sxSourceEvent alpha.val z)

private lemma proof_supported_anchor_domains : supported_anchor_domains_target.{u,v,w} := by
  classical
  intro I X T _ _ _ _ _ _ _ mass z hm hz
  have hf : 0 < fullSourceMass mass z := event_anchor_positive mass hm.1 z hz _ (anchor_source_mem z)
  have ht : 0 < targetMass mass z := event_anchor_positive mass hm.1 z hz _ (anchor_target_mem z)
  have hf1 := (event_bounds mass hm (PidFiniteConvergence.sourceBranchEvent Finset.univ z)).2
  have ht1 := (event_bounds mass hm (PidFiniteConvergence.targetBranchEvent z)).2
  have hc : conditioned mass z z = mass z / targetMass mass z := by
    simp [conditioned, anchor_target_mem]
  have hcz : 0 < conditioned mass z z := by rw [hc]; exact div_pos hz ht
  have hq := (proof_target_conditioning_mass I X T mass z hm ht).1
  have hp := proof_generator_nonnegative_and_total I X T mass z hm.1
  have hn := proof_generator_nonnegative_and_total I X T (conditioned mass z) z hq.1
  have htplus : nodeTotal (weights mass z) = 1 - fullSourceMass mass z := by
    rw [hp.2, hm.2]
  have htminus : nodeTotal (weights (conditioned mass z) z) = 1 - mass z / targetMass mass z := by
    rw [hn.2, hq.2, conditional_full mass z hm ht]
  have nonneg (r : Node I → ℝ) (hr : ∀ b, 0 ≤ r b) : 0 ≤ nodeTotal r :=
    Finset.sum_nonneg (fun b _ => hr b)
  refine ⟨hf, hf1, ht, ht1, hc, hcz, htplus, nonneg _ hp.1, ?_, htminus,
    nonneg _ hn.1, ?_, ?_⟩
  · rw [htplus]; linarith
  · rw [htminus]; have h := div_pos hz ht; linarith
  · intro alpha
    have hsp := PidFiniteConvergence.sx_source_event_mass_positive alpha.property.1 mass hm.1 z hz
    have hsn := PidFiniteConvergence.sx_source_event_mass_positive alpha.property.1 (conditioned mass z) hq.1 z hcz
    have bsp := (event_bounds mass hm (PidFiniteConvergence.sxSourceEvent alpha.val z)).2
    have bsn := (event_bounds (conditioned mass z) hq (PidFiniteConvergence.sxSourceEvent alpha.val z)).2
    refine ⟨hsp, bsp, ?_, ?_, ?_, ?_⟩
    · rw [← conditional_source mass z alpha hm ht]; exact hsn
    · rw [← conditional_source mass z alpha hm ht]; exact bsn
    · rw [proof_generator_lower_cumulative I X T mass z alpha, hm.2]
    · rw [proof_generator_lower_cumulative I X T (conditioned mass z) z alpha, hq.2,
        conditional_source mass z alpha hm ht]

private lemma proof_conditional_generator_support : conditional_generator_support_target.{u,v,w} := by
  classical
  intro I X T _ _ _ _ _ _ _ mass z beta hm ht hp
  have hq := (proof_target_conditioning_mass I X T mass z hm ht).1
  obtain ⟨x, _hx, hx⟩ := (Finset.sum_pos_iff_of_nonneg (fun x _ =>
    ite_nonneg (hq.1 x) (le_refl 0))).mp hp
  split_ifs at hx with hgen
  · have hmx : 0 < mass x := by
      change 0 < (if x ∈ PidFiniteConvergence.targetBranchEvent z then
        mass x / targetMass mass z else 0) at hx
      split_ifs at hx with htarget
      · exact (div_pos_iff.mp hx).resolve_right (fun h => (not_lt_of_ge ht.le) h.2) |>.1
      · exact False.elim (lt_irrefl 0 hx)
    exact lt_of_lt_of_le (by simpa [hgen] using hmx)
      (Finset.single_le_sum (fun y _ => ite_nonneg (hm.1 y) (le_refl 0)) (Finset.mem_univ x))
  · exact False.elim (lt_irrefl 0 hx)

private lemma cumulative_model {I : Type u} [Fintype I] [DecidableEq I]
    (sigma : SemilatticeSup (Node I)) (hsigma : ExactOps sigma) (r : Node I → ℝ) (a : Node I) :
    cumulative r a = @PidJoinLogContract.cumulative (Node I) (nodeFintype I)
      sigma.toLE (Classical.decRel sigma.le) r a := by
  classical
  unfold cumulative PidJoinLogContract.cumulative
  apply Finset.sum_congr rfl
  intro x _hx
  simp only [hsigma.1 x a]

private lemma inverse_exists {I : Type u} [Fintype I] [Nonempty I] [DecidableEq I]
    (r : Node I → ℝ) (hr : ∀ a, 0 ≤ r a) (ht : nodeTotal r < 1) :
    ∃ atoms : Node I → ℝ,
      (∀ a, cumulative atoms a = -Real.log (1 - cumulative r a)) ∧ LogModel r atoms ∧
      ∀ other : Node I → ℝ,
        (∀ a, cumulative other a = -Real.log (1 - cumulative r a)) → other = atoms := by
  classical
  obtain ⟨sigma, hsigma⟩ := (proof_actual_join_lub I).2
  let atoms := @PidJoinLogContract.logAtoms (Node I) (nodeFintype I) sigma
    (Classical.decEq (Node I)) r
  have he (a : Node I) := @PidJoinLogCandidate.log_atoms_cumulative (Node I)
    (nodeFintype I) sigma (Classical.decEq (Node I)) (Classical.decRel sigma.le) r hr ht a
  refine ⟨atoms, ?_, ⟨sigma, hsigma, rfl⟩, ?_⟩
  · intro a
    rw [cumulative_model sigma hsigma, cumulative_model sigma hsigma]
    exact he a
  · intro other hother
    apply @PidJoinLogCandidate.lower_cumulative_unique (Node I) (nodeFintype I)
      sigma.toPartialOrder (Classical.decRel sigma.le) other atoms
    intro a
    rw [← cumulative_model sigma hsigma, ← cumulative_model sigma hsigma, hother a]
    rw [cumulative_model sigma hsigma r a, cumulative_model sigma hsigma atoms a]
    exact (he a).symm

private lemma proof_informative_inverse_identification : informative_inverse_identification_target.{u,v,w} := by
  classical
  intro I X T _ _ _ _ _ _ _ mass z hm hz
  have hg := proof_generator_nonnegative_and_total I X T mass z hm.1
  have ht : nodeTotal (weights mass z) < 1 := by rw [hg.2, hm.2]; linarith
  obtain ⟨atoms, ha, hmodel, hu⟩ := inverse_exists (weights mass z) hg.1 ht
  have hc (a : Node I) : 1 - cumulative (weights mass z) a = sourceMass mass z a := by
    rw [proof_generator_lower_cumulative I X T mass z a, hm.2]; ring
  refine ⟨atoms, ?_, hmodel, ?_⟩
  · intro a; rw [ha a, hc a]
  · intro other hother
    apply hu other
    intro a; rw [hc a]; exact hother a

private lemma proof_misinformative_inverse_identification : misinformative_inverse_identification_target.{u,v,w} := by
  classical
  intro I X T _ _ _ _ _ _ _ mass z hm hz
  have hd := proof_supported_anchor_domains I X T mass z hm hz
  have hq := (proof_target_conditioning_mass I X T mass z hm hd.2.2.1).1
  have hfull : 0 < fullSourceMass (conditioned mass z) z := by
    rw [conditional_full mass z hm hd.2.2.1]
    exact div_pos hz hd.2.2.1
  obtain ⟨atoms, ha, hmodel, hu⟩ := proof_informative_inverse_identification I X T
    (conditioned mass z) z hq hfull
  have hc (a : Node I) :
      -Real.log (sourceMass (conditioned mass z) z a) =
        Real.log (targetMass mass z / restrictedMass mass z a) := by
    rw [conditional_source mass z a hm hd.2.2.1, ← Real.log_inv]
    congr 1
    exact inv_div _ _
  refine ⟨atoms, (fun a => (ha a).trans (hc a)), hmodel, ?_⟩
  intro other ho
  apply hu other
  intro a
  rw [hc a]
  exact ho a

private lemma generated_model {I : Type u} [Fintype I] [DecidableEq I]
    (sigma : SemilatticeSup (Node I)) (hsigma : ExactOps sigma)
    (r : Node I → ℝ) (a : Node I) :
    Generated r a ↔ @PidJoinLogContract.nonemptyGeneratorJoin (Node I) sigma
      (Classical.decEq (Node I)) r a := by
  classical
  constructor
  · rintro ⟨s, hs, hpos, hupper, hleast⟩
    refine ⟨s, hs, hpos, sigma.le_antisymm _ _ ?_ ?_⟩
    · exact @Finset.sup'_le (Node I) (Node I) sigma s hs id a
        (fun x hx => (hsigma.1 x a).2 (hupper x hx))
    · apply (hsigma.1 a _).2
      apply hleast
      intro x hx
      exact (hsigma.1 x _).1 (@Finset.le_sup' (Node I) (Node I) sigma s id x hx)
  · rintro ⟨s, hs, hpos, he⟩
    refine ⟨s, hs, hpos, ?_, ?_⟩
    · intro x hx
      apply (hsigma.1 x a).1
      rw [← he]
      exact @Finset.le_sup' (Node I) (Node I) sigma s id x hx
    · intro upper hu
      apply (hsigma.1 a upper).1
      rw [← he]
      exact @Finset.sup'_le (Node I) (Node I) sigma s hs id upper
        (fun x hx => (hsigma.1 x upper).2 (hu x hx))

private lemma model_nonnegative_support {I : Type u} [Fintype I] [DecidableEq I]
    (r atoms : Node I → ℝ) (hr : ∀ a, 0 ≤ r a) (ht : nodeTotal r < 1)
    (hmodel : LogModel r atoms) :
    ∀ a, 0 ≤ atoms a ∧ (0 < atoms a ↔ Generated r a) := by
  classical
  obtain ⟨sigma, hsigma, rfl⟩ := hmodel
  intro a
  constructor
  · exact tsum_nonneg (fun n => div_nonneg
      (@PidJoinLogCandidate.join_power_nonnegative (Node I) (nodeFintype I) sigma
        (Classical.decEq (Node I)) r hr n a) (by positivity))
  · exact (@PidJoinLogCandidate.log_atoms_strict_support (Node I) (nodeFintype I) sigma
      (Classical.decEq (Node I)) r hr ht a).trans
      (generated_model sigma hsigma r a).symm

private lemma proof_component_nonnegative_strict_support : component_nonnegative_strict_support_target.{u,v,w} := by
  classical
  intro I X T _ _ _ _ _ _ _ mass z plus minus hm hz hp hn
  have hd := proof_supported_anchor_domains I X T mass z hm hz
  obtain ⟨plus', _hp', hpm, hpu⟩ := proof_informative_inverse_identification I X T mass z hm hd.1
  obtain ⟨minus', _hn', hnm, hnu⟩ := proof_misinformative_inverse_identification I X T mass z hm hz
  have ep := hpu plus hp
  have en := hnu minus hn
  subst plus'
  subst minus'
  have hg := proof_generator_nonnegative_and_total I X T mass z hm.1
  have hq := (proof_target_conditioning_mass I X T mass z hm hd.2.2.1).1
  have hgn := proof_generator_nonnegative_and_total I X T (conditioned mass z) z hq.1
  have htp : nodeTotal (weights mass z) < 1 := by rw [hg.2, hm.2]; linarith [hd.1]
  have htn : nodeTotal (weights (conditioned mass z) z) < 1 := by
    rw [hgn.2, hq.2, conditional_full mass z hm hd.2.2.1]
    have hv := div_pos hz hd.2.2.1
    linarith
  intro a
  have p := model_nonnegative_support _ plus hg.1 htp hpm a
  have n := model_nonnegative_support _ minus hgn.1 htn hnm a
  exact ⟨p.1, n.1, p.2, n.2⟩

private lemma proof_signed_mgw_cumulative : signed_mgw_cumulative_target.{u,v,w} := by
  classical
  intro I X T _ _ _ _ _ _ _ mass z plus minus hm hz hp hn a
  have hd := proof_supported_anchor_domains I X T mass z hm hz
  have hs := (hd.2.2.2.2.2.2.2.2.2.2.2.2 a).1
  have ht := hd.2.2.1
  have hr : 0 < restrictedMass mass z a := by
    have h := (hd.2.2.2.2.2.2.2.2.2.2.2.2 a).2.2.1
    exact (div_pos_iff.mp h).resolve_right (fun h => (not_lt_of_ge ht.le) h.2) |>.1
  have hsub : cumulative (plus - minus) a = cumulative plus a - cumulative minus a := by
    unfold cumulative
    rw [← Finset.sum_sub_distrib]
    apply Finset.sum_congr rfl
    intro x _hx
    by_cases h : rawLE x.val a.val <;> simp [h]
  rw [hsub, hp a, hn a, Real.log_div (ne_of_gt ht) (ne_of_gt hr),
    Real.log_div (ne_of_gt hr) (mul_ne_zero (ne_of_gt hs) (ne_of_gt ht)),
    Real.log_mul (ne_of_gt hs) (ne_of_gt ht)]
  ring

theorem actual_join_lub : actual_join_lub_target.{u} :=
  proof_actual_join_lub

theorem mismatch_generator_and_exclusion : mismatch_generator_and_exclusion_target.{u,v,w} :=
  proof_mismatch_generator_and_exclusion

theorem generator_nonnegative_and_total : generator_nonnegative_and_total_target.{u,v,w} :=
  proof_generator_nonnegative_and_total

theorem generator_lower_cumulative : generator_lower_cumulative_target.{u,v,w} :=
  proof_generator_lower_cumulative

theorem target_conditioning_mass : target_conditioning_mass_target.{u,v,w} :=
  proof_target_conditioning_mass

theorem supported_anchor_domains : supported_anchor_domains_target.{u,v,w} :=
  proof_supported_anchor_domains

theorem conditional_generator_support : conditional_generator_support_target.{u,v,w} :=
  proof_conditional_generator_support

theorem informative_inverse_identification : informative_inverse_identification_target.{u,v,w} :=
  proof_informative_inverse_identification

theorem misinformative_inverse_identification : misinformative_inverse_identification_target.{u,v,w} :=
  proof_misinformative_inverse_identification

theorem component_nonnegative_strict_support : component_nonnegative_strict_support_target.{u,v,w} :=
  proof_component_nonnegative_strict_support

theorem signed_mgw_cumulative : signed_mgw_cumulative_target.{u,v,w} :=
  proof_signed_mgw_cumulative

end PidMgwBridgeCandidate
