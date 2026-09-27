import PidStoppedPrefixStageA.Contract

/- Source-only F1/F2 candidate. Not elaborated or kernel checked.
   Exact fixed targets; no F4, cycle law, or normalized masked-law premise. -/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal Classical
open MeasureTheory
open PidMgwBridgeContract (Key Law total)
open PidPrefixProbabilityContract
open PidStoppedPrefixStageAContract
universe u v w
namespace PidStoppedPrefixF1F2Candidate

section Helpers
variable {I : Type u} {X : I → Type v} {T : Type w}
variable [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
variable [DecidableEq I]

private lemma f12_key_finite (r : Key I X T → ℝ) :
    IsFiniteMeasure (keyMeasure r) := by
  classical
  let : MeasurableSpace (Key I X T) := ⊤
  constructor
  simp only [keyMeasure, Measure.finsetSum_apply, Measure.smul_apply,
    Measure.dirac_apply_of_mem (Set.mem_univ _), smul_eq_mul, mul_one]
  exact ENNReal.sum_lt_top.mpr (fun _ _ => ENNReal.ofReal_lt_top)

private lemma f12_key_singleton (r : Key I X T → ℝ) (x : Key I X T) :
    keyMeasure r {x} = ENNReal.ofReal (r x) := by
  classical
  let : MeasurableSpace (Key I X T) := ⊤
  change (∑ a, ENNReal.ofReal (r a) • Measure.dirac a) {x} = ENNReal.ofReal (r x)
  rw [← Measure.sum_fintype]
  exact Measure.sum_smul_dirac_singleton

private lemma f12_key_univ (r : Key I X T → ℝ) (hr : ∀ x, 0 ≤ r x) :
    keyMeasure r Set.univ = ENNReal.ofReal (total r) := by
  classical
  let : MeasurableSpace (Key I X T) := ⊤
  simp only [keyMeasure, Measure.finsetSum_apply, Measure.smul_apply,
    Measure.dirac_apply_of_mem (Set.mem_univ _), smul_eq_mul, mul_one]
  change (∑ x : Key I X T, ENNReal.ofReal (r x)) = ENNReal.ofReal (∑ x : Key I X T, r x)
  exact (ENNReal.ofReal_sum_of_nonneg (s := Finset.univ) (f := r)
    (fun x _ => hr x)).symm

private lemma f12_row_singleton (r : Key I X T → ℝ) (n : ℕ)
    (word : Fin n → Key I X T) :
    rowLaw r n {word} = ∏ i, ENNReal.ofReal (r (word i)) := by
  classical
  let : MeasurableSpace (Key I X T) := ⊤
  let : IsFiniteMeasure (keyMeasure r) := f12_key_finite r
  rw [rowLaw, Measure.pi_singleton]
  simp only [f12_key_singleton]

private lemma f12_row_univ (r : Key I X T → ℝ) (hr : ∀ x, 0 ≤ r x) (n : ℕ) :
    rowLaw r n Set.univ = ENNReal.ofReal ((total r) ^ n) := by
  classical
  let : MeasurableSpace (Key I X T) := ⊤
  let : IsFiniteMeasure (keyMeasure r) := f12_key_finite r
  rw [rowLaw, Measure.pi_univ]
  simp only [f12_key_univ r hr, Finset.prod_const, Finset.card_univ, Fintype.card_fin]
  have ht : 0 ≤ total r := Finset.sum_nonneg (fun x _ => hr x)
  exact (ENNReal.ofReal_pow ht n).symm

omit [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] in
private lemma f12_mask_nonneg (p : Key I X T → ℝ) (hp : ∀ x, 0 ≤ p x)
    (A : Set (Key I X T)) : ∀ x, 0 ≤ maskedMass p A x := by
  classical
  intro x
  by_cases hx : x ∈ A
  · simpa only [maskedMass, if_pos hx] using hp x
  · simp only [maskedMass, if_neg hx, le_refl]

private lemma f12_event_mass_bounds (p : Key I X T → ℝ) (hp : Law p)
    (A : Set (Key I X T)) :
    0 ≤ eventMass p A ∧ eventMass p A ≤ 1 ∧
      total (maskedMass p Aᶜ) = 1 - eventMass p A := by
  classical
  have hhit : 0 ≤ eventMass p A :=
    Finset.sum_nonneg (fun x _ => f12_mask_nonneg p hp.1 A x)
  have hmiss : 0 ≤ total (maskedMass p Aᶜ) :=
    Finset.sum_nonneg (fun x _ => f12_mask_nonneg p hp.1 Aᶜ x)
  have hsplit : total (maskedMass p Aᶜ) + eventMass p A = total p := by
    change (∑ x, maskedMass p Aᶜ x) + (∑ x, maskedMass p A x) = ∑ x, p x
    rw [← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro x _
    by_cases hx : x ∈ A <;> simp [maskedMass, hx]
  have hone : total (maskedMass p Aᶜ) + eventMass p A = 1 := hsplit.trans hp.2
  refine ⟨hhit, ?_, eq_sub_of_add_eq hone⟩
  calc
    eventMass p A ≤ total (maskedMass p Aᶜ) + eventMass p A :=
      le_add_of_nonneg_left hmiss
    _ = 1 := hone

omit [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] in
private lemma f12_miss_product (p : Key I X T → ℝ) (A : Set (Key I X T))
    (n : ℕ) (rows : Fin n → Key I X T) :
    (∏ i, ENNReal.ofReal (maskedMass p Aᶜ (rows i))) =
      if (∀ i, rows i ∉ A) then ∏ i, ENNReal.ofReal (p (rows i)) else 0 := by
  classical
  by_cases h : ∀ i, rows i ∉ A
  · rw [if_pos h]
    apply Finset.prod_congr rfl
    intro i _
    simp [maskedMass, h i]
  · rw [if_neg h]
    obtain ⟨i, hi⟩ := not_forall.mp h
    have hhit : rows i ∈ A := Classical.not_not.mp hi
    apply Finset.prod_eq_zero (Finset.mem_univ i)
    simp [maskedMass, hhit]

omit [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
    [DecidableEq I] in
private lemma f12_split_preimage (n : ℕ) (rows : Fin n → Key I X T)
    (x : Key I X T) :
    (splitLast n) ⁻¹' {(rows, x)} = {Fin.snoc rows x} := by
  ext word
  change splitLast n word = (rows, x) ↔ word = Fin.snoc rows x
  constructor
  · intro hw
    have hprefix : (fun i : Fin n => word i.castSucc) = rows := congrArg Prod.fst hw
    have hlast : word (Fin.last n) = x := congrArg Prod.snd hw
    have hsnoc := Fin.snoc_init_self (q := word)
    change Fin.snoc (fun i : Fin n => word i.castSucc) (word (Fin.last n)) = word at hsnoc
    rw [hprefix, hlast] at hsnoc
    exact hsnoc.symm
  · intro hw
    rw [hw]
    simp [splitLast]

private lemma f12_restricted_singleton (p : Key I X T → ℝ)
    (A : Set (Key I X T)) (n : ℕ) (rows : Fin n → Key I X T) (x : Key I X T) :
    rowLaw p (n + 1) ({Fin.snoc rows x} ∩ firstHitWord A n) =
      if (∀ i, rows i ∉ A) ∧ x ∈ A then
        (∏ i, ENNReal.ofReal (p (rows i))) * ENNReal.ofReal (p x) else 0 := by
  classical
  by_cases h : (∀ i, rows i ∉ A) ∧ x ∈ A
  · have hw : Fin.snoc rows x ∈ firstHitWord A n := by
      simpa only [firstHitWord, Set.mem_ofPred_eq, Fin.snoc_castSucc, Fin.snoc_last] using h
    rw [Set.singleton_inter_of_mem hw, if_pos h, f12_row_singleton,
      Fin.prod_univ_castSucc]
    simp only [Fin.snoc_castSucc, Fin.snoc_last]
  · have hw : Fin.snoc rows x ∉ firstHitWord A n := by
      simpa only [firstHitWord, Set.mem_ofPred_eq, Fin.snoc_castSucc, Fin.snoc_last] using h
    rw [Set.singleton_inter_of_notMem hw, measure_empty, if_neg h]

end Helpers

private lemma proof_first_hit_factorization : first_hit_factorization_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p A n _hp
  classical
  -- A concrete key instance does not replace the explicit pair-space codomain.
  let : MeasurableSpace (Key I X T) := ⊤
  let : IsFiniteMeasure (keyMeasure p) := f12_key_finite p
  let : IsFiniteMeasure (keyMeasure (maskedMass p A)) := f12_key_finite _
  let : IsFiniteMeasure (keyMeasure (maskedMass p Aᶜ)) := f12_key_finite _
  apply Measure.ext_of_singleton
  rintro ⟨rows, x⟩
  rw [Measure.map_apply (measurable_of_finite _) (measurableSet_singleton _),
    f12_split_preimage, Measure.restrict_apply (measurableSet_singleton _),
    ← Set.singleton_prod_singleton, Measure.prod_prod,
    f12_row_singleton, f12_key_singleton]
  rw [f12_restricted_singleton, f12_miss_product]
  have hhit : ENNReal.ofReal (maskedMass p A x) =
      if x ∈ A then ENNReal.ofReal (p x) else 0 := by
    by_cases hx : x ∈ A <;> simp [maskedMass, hx]
  rw [hhit]
  by_cases hmiss : ∀ i, rows i ∉ A
  · by_cases hx : x ∈ A
    · rw [if_pos ⟨hmiss, hx⟩, if_pos hmiss, if_pos hx]
    · have hnot : ¬ ((∀ i, rows i ∉ A) ∧ x ∈ A) := fun h => hx h.2
      rw [if_neg hnot, if_neg hx, mul_zero]
  · have hnot : ¬ ((∀ i, rows i ∉ A) ∧ x ∈ A) := fun h => hmiss h.1
    rw [if_neg hnot, if_neg hmiss, zero_mul]

private lemma proof_first_hit_mass : first_hit_mass_target.{u,v,w} := by
  intro I X T _ _ _ _ _ _ _ p A n hp
  classical
  let : MeasurableSpace (Key I X T) := ⊤
  let : IsFiniteMeasure (keyMeasure p) := f12_key_finite p
  let : IsFiniteMeasure (keyMeasure (maskedMass p A)) := f12_key_finite _
  let : IsFiniteMeasure (keyMeasure (maskedMass p Aᶜ)) := f12_key_finite _
  have hb := f12_event_mass_bounds p hp A
  refine ⟨hb.1, hb.2.1, ?_⟩
  have hmass := congrArg
    (fun μ :
      @Measure ((Fin n → Key I X T) × Key I X T)
        (@Prod.instMeasurableSpace (Fin n → Key I X T) (Key I X T)
          inferInstance inferInstance) => μ Set.univ)
    (proof_first_hit_factorization I X T p A n hp)
  rw [Measure.map_apply (measurable_of_finite _) MeasurableSet.univ,
    Set.preimage_univ, Measure.restrict_apply_univ,
    ← Set.univ_prod_univ, Measure.prod_prod,
    f12_row_univ (maskedMass p Aᶜ) (f12_mask_nonneg p hp.1 Aᶜ) n,
    f12_key_univ (maskedMass p A) (f12_mask_nonneg p hp.1 A)] at hmass
  change rowLaw p (n + 1) (firstHitWord A n) =
    ENNReal.ofReal ((total (maskedMass p Aᶜ)) ^ n) * ENNReal.ofReal (eventMass p A) at hmass
  rw [hb.2.2, ← ENNReal.ofReal_mul (pow_nonneg (sub_nonneg.mpr hb.2.1) n)] at hmass
  exact hmass

/-- Source proposal: the exact unnormalized restricted iid pushforward. -/
theorem first_hit_factorization : first_hit_factorization_target.{u,v,w} :=
  proof_first_hit_factorization

/-- Source proposal: first-hit mass, including the empty prefix and null events. -/
theorem first_hit_mass : first_hit_mass_target.{u,v,w} :=
  proof_first_hit_mass

end PidStoppedPrefixF1F2Candidate
