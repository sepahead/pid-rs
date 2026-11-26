prelude
import Model

namespace Nested

universe u

theorem branch_reaches (j : Nat) (b : Branch) : b.reaches j ↔ j ≤ b.level := by
  induction b
  case one i => rfl
  case both a b ha hb =>
    change (a.reaches j ∨ b.reaches j) ↔ j ≤ max a.level b.level
    rw [ha, hb]
    omega

theorem suffix_incidence (j : Nat) (a : Node) : a.covers j ↔ j ≤ a.level := by
  induction a
  case branch b => exact branch_reaches j b
  case either a b ha hb =>
    change (a.covers j ∧ b.covers j) ↔ j ≤ min a.level b.level
    rw [ha, hb]
    omega

theorem branch_matches (p : Nat → Prop) (h : Decreases p) (b : Branch) :
    b.holds p ↔ p b.level := by
  induction b
  case one i => rfl
  case both a b ha hb =>
    change (a.holds p ∧ b.holds p) ↔ p (max a.level b.level)
    rw [ha, hb]
    rcases Nat.le_total a.level b.level with hle | hge
    · rw [Nat.max_eq_right hle]
      constructor
      · exact And.right
      · intro v
        exact ⟨h _ _ hle v, v⟩
    · rw [Nat.max_eq_left hge]
      constructor
      · exact And.left
      · intro v
        exact ⟨v, h _ _ hge v⟩

theorem node_matches (p : Nat → Prop) (h : Decreases p) (a : Node) :
    a.holds p ↔ p a.level := by
  induction a
  case branch b => exact branch_matches p h b
  case either a b ha hb =>
    change (a.holds p ∨ b.holds p) ↔ p (min a.level b.level)
    rw [ha, hb]
    rcases Nat.le_total a.level b.level with hle | hge
    · rw [Nat.min_eq_left hle]
      constructor
      · rintro (v | v)
        · exact v
        · exact h _ _ hle v
      · exact Or.inl
    · rw [Nat.min_eq_right hge]
      constructor
      · rintro (v | v)
        · exact h _ _ hge v
        · exact v
      · exact Or.inr

theorem event_extensional {W : Type u} (F : Nat → W → Prop)
    (h : ∀ w : W, Decreases (fun i => F i w)) (a : Node) :
    (fun w => a.holds (fun i => F i w)) = F a.level := by
  funext w
  apply propext
  exact node_matches (fun i => F i w) (h w) a

theorem cumulative_sum (s : Nat → Int) (a : Node) :
    prefixSum s a.level = s a.level - s 0 := by
  generalize a.level = d
  induction d
  case zero => simp [prefixSum]
  case succ n ih =>
    rw [prefixSum, ih]
    omega

end Nested
