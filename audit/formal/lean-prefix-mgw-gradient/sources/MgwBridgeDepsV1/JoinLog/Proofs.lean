import MgwBridgeDepsV1.JoinLog.Contract
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators
open PidJoinLogContract
universe u
namespace PidJoinLogCandidate

private lemma cumulative_split {L : Type u} [Fintype L] [PartialOrder L]
    [DecidableLE L] [DecidableEq L] (f : L → ℝ) (a : L) :
    cumulative f a = (∑ x ∈ Finset.univ.erase a, if x ≤ a then f x else 0) + f a := by
  classical
  unfold cumulative
  rw [← Finset.sum_erase_add Finset.univ (fun x => if x ≤ a then f x else 0)
    (Finset.mem_univ a)]
  simp only [le_refl, ite_true]

theorem lower_cumulative_unique (L : Type u) [Fintype L] [PartialOrder L]
    [DecidableLE L] : lower_cumulative_unique_target L := by
  classical
  intro left right h
  funext a
  induction a using WellFoundedLT.induction with
  | ind a ih =>
    have rest : (∑ x ∈ Finset.univ.erase a, if x ≤ a then left x else 0) =
        ∑ x ∈ Finset.univ.erase a, if x ≤ a then right x else 0 := by
      apply Finset.sum_congr rfl
      intro x hx
      by_cases hxa : x ≤ a
      · rw [if_pos hxa, if_pos hxa, ih x (lt_of_le_of_ne hxa (Finset.ne_of_mem_erase hx))]
      · simp [hxa]
    have ha := h a
    rw [cumulative_split, cumulative_split, rest] at ha
    exact add_left_cancel ha

private lemma join_convolution_cumulative_proof (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] : join_convolution_cumulative_target L := by
  classical
  intro left right a
  have move (z : L) :
      (if z ≤ a then ∑ x, ∑ y, if x ⊔ y = z then left x * right y else 0 else 0) =
      ∑ x, ∑ y, if x ⊔ y = z ∧ z ≤ a then left x * right y else 0 := by
    by_cases hz : z ≤ a <;> simp [hz]
  unfold cumulative joinConvolution
  simp_rw [move]
  rw [Finset.sum_comm]
  calc
    _ = ∑ x, ∑ y, ∑ z, if x ⊔ y = z ∧ z ≤ a then left x * right y else 0 := by
      apply Finset.sum_congr rfl
      intro x hx
      rw [Finset.sum_comm]
    _ = ∑ x, ∑ y, (if x ≤ a then left x else 0) * (if y ≤ a then right y else 0) := by
      apply Finset.sum_congr rfl
      intro x hx
      apply Finset.sum_congr rfl
      intro y hy
      rw [Finset.sum_eq_single (x ⊔ y)]
      · by_cases hxa : x ≤ a <;> by_cases hya : y ≤ a <;> simp [hxa, hya, sup_le_iff]
      · intro z hz hne
        simp [Ne.symm hne]
      · simp
    _ = _ := by simp_rw [Finset.sum_mul, Finset.mul_sum]

theorem join_convolution_cumulative (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] : join_convolution_cumulative_target L :=
  join_convolution_cumulative_proof L

theorem join_power_nonnegative (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] : join_power_nonnegative_target L := by
  intro weight hw n
  induction n with
  | zero => exact hw
  | succ n ih =>
    intro a
    apply Finset.sum_nonneg
    intro x hx
    apply Finset.sum_nonneg
    intro y hy
    exact ite_nonneg (mul_nonneg (ih x) (hw y)) (le_refl 0)

private lemma convolution_total {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (left right : L → ℝ) :
    (∑ a, joinConvolution left right a) = (∑ a, left a) * (∑ a, right a) := by
  classical
  unfold joinConvolution
  rw [Finset.sum_comm]
  calc
    _ = ∑ x, ∑ y, ∑ a, if x ⊔ y = a then left x * right y else 0 := by
      apply Finset.sum_congr rfl
      intro x hx
      rw [Finset.sum_comm]
    _ = ∑ x, ∑ y, left x * right y := by simp
    _ = _ := by simp_rw [Finset.sum_mul, Finset.mul_sum]

theorem join_power_total (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] : join_power_total_target L := by
  intro weight n
  induction n with
  | zero => simp [joinPower]
  | succ n ih =>
    simp only [joinPower, convolution_total, ih, pow_succ]

private lemma power_cumulative {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] (weight : L → ℝ) (n : ℕ) (a : L) :
    cumulative (joinPower weight n) a = cumulative weight a ^ (n + 1) := by
  induction n with
  | zero => simp [joinPower]
  | succ n ih =>
    rw [joinPower, join_convolution_cumulative L, ih]
    simp only [pow_succ]

private lemma total_nonnegative {L : Type u} [Fintype L] (weight : L → ℝ)
    (hw : ∀ a, 0 ≤ weight a) : 0 ≤ ∑ a, weight a :=
  Finset.sum_nonneg (fun a _ => hw a)

private lemma cumulative_nonnegative {L : Type u} [Fintype L] [LE L]
    [DecidableLE L] (weight : L → ℝ) (hw : ∀ a, 0 ≤ weight a) (a : L) :
    0 ≤ cumulative weight a := by
  apply Finset.sum_nonneg
  intro x hx
  exact ite_nonneg (hw x) (le_refl 0)

private lemma cumulative_le_total {L : Type u} [Fintype L] [LE L]
    [DecidableLE L] (weight : L → ℝ) (hw : ∀ a, 0 ≤ weight a) (a : L) :
    cumulative weight a ≤ ∑ x, weight x := by
  apply Finset.sum_le_sum
  intro x hx
  split_ifs
  · exact le_refl _
  · exact hw x

private lemma power_le_total {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (weight : L → ℝ) (hw : ∀ a, 0 ≤ weight a) (n : ℕ) (a : L) :
    joinPower weight n a ≤ (∑ x, weight x) ^ (n + 1) := by
  rw [← join_power_total L weight n]
  exact Finset.single_le_sum (fun x _ => join_power_nonnegative L weight hw n x) (Finset.mem_univ a)

private lemma atom_series_summable {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (weight : L → ℝ) (hw : ∀ a, 0 ≤ weight a)
    (hr : (∑ a, weight a) < 1) (a : L) :
    Summable (fun n : ℕ => joinPower weight n a / ((n : ℝ) + 1)) := by
  have major := Real.hasSum_pow_div_log_of_abs_lt_one
    (show |∑ x, weight x| < 1 by rwa [abs_of_nonneg (total_nonnegative weight hw)])
  apply Summable.of_nonneg_of_le (fun n => div_nonneg (join_power_nonnegative L weight hw n a) (by positivity))
    (fun n => div_le_div_of_nonneg_right (power_le_total weight hw n a) (by positivity)) major.summable

private lemma log_atom_nonnegative {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (weight : L → ℝ) (hw : ∀ a, 0 ≤ weight a) (a : L) :
    0 ≤ logAtoms weight a := by
  exact tsum_nonneg (fun n => div_nonneg (join_power_nonnegative L weight hw n a) (by positivity))

theorem log_atoms_cumulative (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] : log_atoms_cumulative_target L := by
  classical
  intro weight hw hr a
  have hs (x : L) : HasSum (fun n : ℕ => if x ≤ a then joinPower weight n x / ((n : ℝ) + 1) else 0)
      (if x ≤ a then logAtoms weight x else 0) := by
    by_cases hx : x ≤ a
    · simpa only [hx, ite_true, logAtoms] using (atom_series_summable weight hw hr x).hasSum
    · simp only [hx, ite_false]
      exact hasSum_zero
  have h := hasSum_sum (s := Finset.univ) (fun x _ => hs x)
  have terms (n : ℕ) : (∑ x, if x ≤ a then joinPower weight n x / ((n : ℝ) + 1) else 0) =
      cumulative weight a ^ (n + 1) / ((n : ℝ) + 1) := by
    rw [← power_cumulative weight n a]
    simp only [cumulative, div_eq_mul_inv, Finset.sum_mul]
    apply Finset.sum_congr rfl
    intro x hx
    by_cases hxa : x ≤ a <;> simp [hxa]
  simp_rw [terms] at h
  exact h.unique (Real.hasSum_pow_div_log_of_abs_lt_one
    (show |cumulative weight a| < 1 by
      rw [abs_of_nonneg (cumulative_nonnegative weight hw a)]
      exact lt_of_le_of_lt (cumulative_le_total weight hw a) hr))

theorem supplied_log_inverse_nonnegative (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] [DecidableLE L] : supplied_log_inverse_nonnegative_target L := by
  intro weight atoms hw hr h
  have equality : atoms = logAtoms weight := lower_cumulative_unique L atoms (logAtoms weight)
    (fun a => (h a).trans (log_atoms_cumulative L weight hw hr a).symm)
  rw [equality]
  exact log_atom_nonnegative weight hw

private lemma convolution_positive {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (left right : L → ℝ) (hl : ∀ x, 0 ≤ left x)
    (hr : ∀ y, 0 ≤ right y) (a : L) :
    0 < joinConvolution left right a ↔
      ∃ x y, x ⊔ y = a ∧ 0 < left x ∧ 0 < right y := by
  classical
  have term_nonnegative (x y : L) :
      0 ≤ (if x ⊔ y = a then left x * right y else 0) :=
    ite_nonneg (mul_nonneg (hl x) (hr y)) (le_refl 0)
  unfold joinConvolution
  rw [Finset.sum_pos_iff_of_nonneg (fun x _ => Finset.sum_nonneg (fun y _ => term_nonnegative x y))]
  constructor
  · rintro ⟨x, hx, hp⟩
    obtain ⟨y, hy, hp⟩ := (Finset.sum_pos_iff_of_nonneg (fun y _ => term_nonnegative x y)).mp hp
    by_cases he : x ⊔ y = a
    · rw [if_pos he] at hp
      rcases mul_pos_iff.mp hp with hpos | hneg
      · exact ⟨x, y, he, hpos.1, hpos.2⟩
      · exact False.elim ((not_lt_of_ge (hl x)) hneg.1)
    · simp [he] at hp
  · rintro ⟨x, y, he, hpx, hpy⟩
    refine ⟨x, Finset.mem_univ x, ?_⟩
    apply (Finset.sum_pos_iff_of_nonneg (fun y _ => term_nonnegative x y)).mpr
    refine ⟨y, Finset.mem_univ y, ?_⟩
    rw [if_pos he]
    exact mul_pos hpx hpy

private lemma positive_power_generator {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (weight : L → ℝ) (hw : ∀ a, 0 ≤ weight a)
    (n : ℕ) (a : L) (hp : 0 < joinPower weight n a) : nonemptyGeneratorJoin weight a := by
  classical
  induction n generalizing a with
  | zero =>
    refine ⟨{a}, Finset.singleton_nonempty a, ?_, ?_⟩
    · intro x hx
      have hx' : x = a := Finset.mem_singleton.mp hx
      subst x
      exact hp
    · simp
  | succ n ih =>
    obtain ⟨x, y, hxy, hpx, hpy⟩ :=
      (convolution_positive (joinPower weight n) weight (join_power_nonnegative L weight hw n) hw a).mp hp
    obtain ⟨support, hs, hspos, hsj⟩ := ih x hpx
    refine ⟨insert y support, Finset.insert_nonempty y support, ?_, ?_⟩
    · intro z hz
      rcases Finset.mem_insert.mp hz with hzy | hz
      · subst z
        exact hpy
      · exact hspos z hz
    · rw [Finset.sup'_insert hs, id_eq, hsj, sup_comm, hxy]

private lemma generator_positive_power {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (weight : L → ℝ) (hw : ∀ a, 0 ≤ weight a)
    (a : L) (hg : nonemptyGeneratorJoin weight a) : ∃ n, 0 < joinPower weight n a := by
  classical
  obtain ⟨support, hs, hpos, rfl⟩ := hg
  induction support using Finset.induction_on with
  | empty => exact False.elim (Finset.not_nonempty_empty hs)
  | @insert y support hy ih =>
    by_cases hne : support.Nonempty
    · obtain ⟨n, hn⟩ := ih hne (fun x hx => hpos x (Finset.mem_insert_of_mem hx))
      refine ⟨n + 1, ?_⟩
      rw [joinPower]
      apply (convolution_positive (joinPower weight n) weight (join_power_nonnegative L weight hw n) hw _).mpr
      refine ⟨support.sup' hne id, y, ?_, hn, hpos y (Finset.mem_insert_self y support)⟩
      rw [Finset.sup'_insert hne]
      exact sup_comm _ _
    · have he : support = ∅ := Finset.not_nonempty_iff_eq_empty.mp hne
      subst support
      refine ⟨0, ?_⟩
      simpa only [Finset.insert_empty, Finset.sup'_singleton, id_eq, joinPower] using hpos y (Finset.mem_insert_self y ∅)

theorem log_atoms_strict_support (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] : log_atoms_strict_support_target L := by
  classical
  intro weight hw hr a
  constructor
  · intro hg
    have some_power : ∃ n, 0 < joinPower weight n a := by
      by_contra hnone
      have hz (n : ℕ) : joinPower weight n a = 0 :=
        le_antisymm (le_of_not_gt (fun hp => hnone ⟨n, hp⟩)) (join_power_nonnegative L weight hw n a)
      have hzero : logAtoms weight a = 0 := by simp [logAtoms, hz]
      exact (ne_of_gt hg) hzero
    obtain ⟨n, hn⟩ := some_power
    exact positive_power_generator weight hw n a hn
  · intro hg
    obtain ⟨n, hn⟩ := generator_positive_power weight hw a hg
    exact (atom_series_summable weight hw hr a).tsum_pos
      (fun k => div_nonneg (join_power_nonnegative L weight hw k a) (by positivity)) n
      (div_pos hn (by positivity))

private lemma log_total {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (weight : L → ℝ) (hw : ∀ a, 0 ≤ weight a)
    (hr : (∑ a, weight a) < 1) :
    (∑ a, logAtoms weight a) = -Real.log (1 - ∑ a, weight a) := by
  have hs := hasSum_sum (s := Finset.univ)
    (fun x _ => (atom_series_summable weight hw hr x).hasSum)
  have terms (n : ℕ) : (∑ x, joinPower weight n x / ((n : ℝ) + 1)) =
      (∑ x, weight x) ^ (n + 1) / ((n : ℝ) + 1) := by
    rw [← join_power_total L weight n]
    simp only [div_eq_mul_inv, Finset.sum_mul]
  simp_rw [terms] at hs
  exact hs.unique (Real.hasSum_pow_div_log_of_abs_lt_one
    (show |∑ x, weight x| < 1 by rwa [abs_of_nonneg (total_nonnegative weight hw)]))

private lemma truncated_total {L : Type u} [Fintype L] [SemilatticeSup L]
    [DecidableEq L] (weight : L → ℝ) (count : ℕ) :
    (∑ a, truncatedLogAtoms weight count a) =
      ∑ n ∈ Finset.range count, (∑ x, weight x) ^ (n + 1) / ((n : ℝ) + 1) := by
  unfold truncatedLogAtoms
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro n hn
  rw [← join_power_total L weight n]
  simp only [div_eq_mul_inv, Finset.sum_mul]

private lemma scalar_log_tail (rho : ℝ) (h0 : 0 ≤ rho) (h1 : rho < 1) (count : ℕ) :
    -Real.log (1 - rho) - ∑ n ∈ Finset.range count, rho ^ (n + 1) / ((n : ℝ) + 1) ≤
      rho ^ (count + 1) / (((count : ℝ) + 1) * (1 - rho)) := by
  have hlog := Real.hasSum_pow_div_log_of_abs_lt_one (show |rho| < 1 by rwa [abs_of_nonneg h0])
  have htail := (summable_nat_add_iff count).mpr hlog.summable
  have hsplit := hlog.summable.sum_add_tsum_nat_add count
  rw [hlog.tsum_eq] at hsplit
  have he : -Real.log (1 - rho) - ∑ n ∈ Finset.range count, rho ^ (n + 1) / ((n : ℝ) + 1) =
      ∑' n : ℕ, rho ^ (n + count + 1) / (((n + count : ℕ) : ℝ) + 1) := by
    linarith
  rw [he]
  have hg := (hasSum_geometric_of_lt_one h0 h1).mul_left (rho ^ (count + 1) / ((count : ℝ) + 1))
  calc
    _ ≤ ∑' n : ℕ, (rho ^ (count + 1) / ((count : ℝ) + 1)) * rho ^ n := by
      apply htail.tsum_le_tsum _ hg.summable
      intro n
      calc
        _ ≤ rho ^ (n + count + 1) / ((count : ℝ) + 1) := by
          apply div_le_div_of_nonneg_left (pow_nonneg h0 _) (by positivity)
          push_cast
          linarith [show (0 : ℝ) ≤ n by positivity]
        _ = _ := by
          rw [show n + count + 1 = (count + 1) + n by omega, pow_add]
          ring
    _ = _ := by
      rw [hg.tsum_eq]
      simp only [div_eq_mul_inv, mul_inv_rev]
      ring

theorem log_atoms_truncation (L : Type u) [Fintype L] [SemilatticeSup L]
    [DecidableEq L] : log_atoms_truncation_target L := by
  intro weight hw hr count
  dsimp only
  have hle (a : L) : truncatedLogAtoms weight count a ≤ logAtoms weight a :=
    (atom_series_summable weight hw hr a).sum_le_tsum (Finset.range count)
      (fun n _ => div_nonneg (join_power_nonnegative L weight hw n a) (by positivity))
  have error : (∑ a, |logAtoms weight a - truncatedLogAtoms weight count a|) =
      -Real.log (1 - ∑ a, weight a) -
        ∑ n ∈ Finset.range count, (∑ a, weight a) ^ (n + 1) / ((n : ℝ) + 1) := by
    calc
      _ = ∑ a, (logAtoms weight a - truncatedLogAtoms weight count a) := by
        apply Finset.sum_congr rfl
        intro a ha
        exact abs_of_nonneg (sub_nonneg.mpr (hle a))
      _ = (∑ a, logAtoms weight a) - (∑ a, truncatedLogAtoms weight count a) := Finset.sum_sub_distrib (logAtoms weight) (truncatedLogAtoms weight count)
      _ = _ := by rw [log_total weight hw hr, truncated_total]
  refine ⟨hle, error, ?_⟩
  rw [error]
  exact scalar_log_tail (∑ a, weight a) (total_nonnegative weight hw) hr count

end PidJoinLogCandidate
