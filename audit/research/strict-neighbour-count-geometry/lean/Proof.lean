prelude
import Model

namespace W7

theorem inner_pair (r : Nat) :
    inner r = fun v => src r v && tgt r v := by
  funext v
  simp [inner, src, tgt, joint, Nat.max_lt]

theorem counts {α : Type} (xs : List α) (f g : α → Bool) :
    xs.countP (fun v => f v && g v) ≤ xs.countP f ∧
    xs.countP (fun v => f v && g v) ≤ xs.countP g ∧
    xs.countP f + xs.countP g ≤ xs.length + xs.countP (fun v => f v && g v) := by
  induction xs
  case nil => simp
  case cons z xs ih =>
    obtain ⟨hi, hj, hu⟩ := ih
    cases hf : f z <;> cases hg : g z <;> simp [hf, hg] <;> omega

theorem necessary (rows : List Row) (r k x y : Nat) (obs : Realizes rows r k x y) :
    Triangle (rows.length + 1) k x y := by
  rcases obs with ⟨hr, hi, he, hx, hy⟩
  rw [inner_pair r] at hi
  obtain ⟨h1, h2, h3⟩ := counts rows (src r) (tgt r)
  have hf : rows.countP (src r) ≤ rows.length := List.countP_le_length
  have hg : rows.countP (tgt r) ≤ rows.length := List.countP_le_length
  unfold Triangle
  omega

theorem constructed (h p q d : Nat) (extra : 0 < p + q + d) :
    (witness h p q d).length = h + p + q + d ∧
    Realizes (witness h p q d) 2 (h + 1) (h + p + 1) (h + q + 1) := by
  cases p <;> cases q <;> cases d <;> simp_all [witness, boundary, outside, Realizes, inner, edge, src, tgt, joint, source, List.countP_replicate] <;> omega

theorem attainable_iff (n k x y : Nat) (hk : 0 < k) (hn : k < n) :
    (∃ (rows : List Row) (r : Nat), rows.length + 1 = n ∧ Realizes rows r k x y) ↔
    Triangle n k x y := by
  constructor
  · rintro ⟨rows, r, hlen, obs⟩
    rw [← hlen]
    exact necessary rows r k x y obs
  · rintro ⟨hkx, hxn, hky, hyn, hs⟩
    have ht : 0 < (x-k)+(y-k)+(n+k-x-y) := (by omega)
    obtain ⟨hlen, hobs⟩ := constructed (k-1) (x-k) (y-k) (n+k-x-y) ht
    have hK : k-1+1=k := (by omega)
    have hX : k-1+(x-k)+1=x := (by omega)
    have hY : k-1+(y-k)+1=y := (by omega)
    rw [hX, hY, hK] at hobs
    exact ⟨witness (k-1) (x-k) (y-k) (n+k-x-y), 2, (by omega), hobs⟩

end W7
