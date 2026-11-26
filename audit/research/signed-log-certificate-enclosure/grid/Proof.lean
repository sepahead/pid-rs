prelude
import Model
namespace GridProof
open SignedGrid

theorem ceiling_le (x b d : Int) (hd : 0 < d) : up x d ≤ b ↔ x ≤ b * d := by
  unfold up
  constructor
  · intro h
    have hdiv : -b ≤ (-x)/d := by omega
    have hmul := (Int.le_ediv_iff_mul_le hd).1 hdiv
    rw [Int.neg_mul] at hmul
    omega
  · intro h
    have hmul : (-b)*d ≤ -x := by
      rw [Int.neg_mul]
      omega
    have hdiv := (Int.le_ediv_iff_mul_le hd).2 hmul
    omega

theorem width_residue (l u d : Int) (hd : 0 < d) :
    width l u d = up (l % d + (u-l)) d := by
  unfold width up
  have base := Int.emod_add_ediv_mul l d
  have ident : -(l%d+(u-l)) = -u+(l/d)*d := by omega
  rw [ident, Int.add_mul_ediv_right _ _ (Int.ne_of_gt hd)]
  omega

theorem sharp_max (d h : Int) (hd : 0 < d) (hh : 0 ≤ h) :
    (∀ l u : Int, l ≤ u → u-l ≤ h → width l u d ≤ up (d-1+h) d) ∧
    (d-1 ≤ d-1+h ∧ width (d-1) (d-1+h) d = up (d-1+h) d) := by
  constructor
  · intro l u horder hg
    rw [width_residue l u d hd]
    unfold up
    have hr := Int.emod_lt_of_pos l hd
    have hneg : -(d-1+h) ≤ -(l%d+(u-l)) := by omega
    have hdiv := Int.ediv_le_ediv hd hneg
    omega
  · constructor
    · omega
    · rw [width_residue (d-1) (d-1+h) d hd]
      have hr : (d-1)%d = d-1 := Int.emod_eq_of_lt (by omega) (by omega)
      have hg : d-1+h-(d-1) = h := by omega
      rw [hr,hg]

theorem two_grid (l u d : Int) (hd : 0 < d) (ho : l ≤ u) (hg : u-l ≤ d+1) :
    0 ≤ width l u d ∧ width l u d ≤ 2 := by
  constructor
  · unfold width
    have hf := Int.ediv_mul_le l (Int.ne_of_gt hd)
    have hu := (ceiling_le u (up u d) d hd).1 (Int.le_refl _)
    have hm : (l/d)*d ≤ (up u d)*d := by omega
    have he := Int.le_of_mul_le_mul_right hm hd
    omega
  · have hm := (sharp_max d (d+1) hd (by omega)).1 l u ho hg
    have hx : up (d-1+(d+1)) d ≤ 2 := by
      apply (ceiling_le _ _ _ hd).2
      rw [Int.two_mul]
      omega
    omega

theorem next_width (d : Int) (hd : 0 < d) : width (d-1) (d-1+(d+2)) d = 3 := by
  have hg := (sharp_max d (d+2) hd (by omega)).2.2
  have hi : up (d-1+(d+2)) d ≤ 3 := by
    apply (ceiling_le _ _ _ hd).2
    omega
  have lo : ¬ up (d-1+(d+2)) d ≤ 2 := by
    intro bad
    have hv := (ceiling_le _ _ _ hd).1 bad
    omega
  omega

theorem both_padded (l u a b d : Int) (hd : 0 < d) (ho : overlap l u a b d)
    (hg : u-l ≤ d) : a-1 ≤ l/d ∧ up u d ≤ b+1 := by
  rcases ho with ⟨horder,hab,hl,hu⟩
  constructor
  · apply (Int.le_ediv_iff_mul_le hd).2
    rw [Int.sub_mul, Int.one_mul]
    omega
  · apply (ceiling_le _ _ _ hd).2
    rw [Int.add_mul, Int.one_mul]
    omega

theorem next_padding (d : Int) (hd : 0 < d) :
    overlap (-d-1) 0 0 0 d ∧ 0-(-d-1) = d+1 ∧ (-d-1)/d < -1 := by
  constructor
  · unfold overlap
    constructor
    · omega
    · constructor
      · exact Int.le_refl _
      · constructor
        · rw [Int.zero_mul]
          omega
        · rw [Int.zero_mul]
          exact Int.le_refl 0
  · constructor
    · omega
    · apply (Int.ediv_lt_iff_lt_mul hd).2
      omega

theorem unit_cell (l u a d : Int) (hd : 0 < d) (ho : l ≤ u) (hg : u-l ≤ d)
    (below : l/d < a) : up u d ≤ a+1 := by
  have span := (two_grid l u d hd ho (by omega)).2
  unfold width at span
  omega

theorem counted_envelope (u l n : Int) (hn : 0 < n) (ho : l ≤ u)
    (bound : u-l ≤ 1385*(1+80*n)) :
    u-l < bitDivisor n ∧ (0 ≤ width l u (bitDivisor n) ∧ width l u (bitDivisor n) ≤ 2) := by
  unfold bitDivisor
  have positive : 0 < n*16777216 := by omega
  have small : u-l < n*16777216 := by omega
  exact ⟨small,two_grid l u (n*16777216) positive ho (by omega)⟩

end GridProof
