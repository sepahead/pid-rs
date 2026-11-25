prelude
import Model

namespace D1Token

theorem read_emit (t rest : List UInt8) (h : Admissible t) :
    read (emit t ++ rest) = some (t, rest) := by
  have ht : ∀ x, List.Mem x t → tokenByte x = true := List.all_eq_true.mp h.2.2
  have hq : tokenByte 34 = false := (by decide)
  simp only [emit, List.cons_append, List.append_assoc, read]
  simp [scan, List.takeWhile_append_of_pos ht, List.dropWhile_append_of_pos ht, List.dropWhile, List.takeWhile, hq, h]

theorem read_sound (word t rest : List UInt8) (h : read word = some (t, rest)) :
    Admissible t ∧ word = emit t ++ rest := by
  cases word
  case nil =>
    simp [read] at h
  case cons opener body =>
    by_cases ho : opener = 34
    · subst opener
      simp only [read] at h
      cases hd : body.dropWhile tokenByte
      · simp [scan, hd] at h
      · rename_i c ss
        by_cases he : c = 34 ∧ Admissible (body.takeWhile tokenByte)
        · simp [scan, hd, he] at h
          rcases h with ⟨rfl, rfl⟩
          obtain ⟨hc, ht⟩ := he
          subst c
          have hb := List.takeWhile_append_dropWhile (p := tokenByte) (l := body)
          rw [hd] at hb
          constructor
          · exact ht
          · simp only [emit, List.cons_append, List.append_assoc, List.cons.injEq, true_and]
            exact hb.symm
        · simp [scan, hd, he] at h
    · simp [read, ho] at h

theorem read_iff (word t rest : List UInt8) :
    read word = some (t, rest) ↔ Admissible t ∧ word = emit t ++ rest := by
  constructor
  · exact read_sound word t rest
  · rintro ⟨ht, rfl⟩
    exact read_emit t rest ht

theorem unique (word a b sa sb : List UInt8)
    (ha : read word = some (a, sa)) (hb : read word = some (b, sb)) :
    a = b ∧ sa = sb := by
  rw [ha] at hb
  simpa using hb

end D1Token
