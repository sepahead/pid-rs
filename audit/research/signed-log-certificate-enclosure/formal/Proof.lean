prelude
import Model
namespace N2Round
open N2

/-- The bounds are integers in units of 1/B. The exact fraction is p/q. -/
def Encl (B l h p q : Nat) : Prop := l*q ≤ B*p ∧ B*p ≤ h*q

theorem ceil_upper (a b : Nat) (hb : 0 < b) : a ≤ up a b * b := by
  unfold up
  have h := Nat.lt_mul_div_succ (a + (b - 1)) hb
  rw [Nat.mul_add, Nat.mul_one, Nat.mul_comm b ((a + (b - 1)) / b)] at h
  omega

theorem signed_ceiling : DivisionClaim := by
  intro a b hb
  cases b
  case zero => omega
  case succ b =>
    cases a
    case zero =>
      have h : b / (b+1) = 0 := Nat.div_eq_of_lt (Nat.lt_succ_self b)
      simp [up, h]
    case succ a =>
      have ht : a+1+(b+1-1) = (b+1)+a := by omega
      change (( (a+1+(b+1-1)) / (b+1) : Nat) : Int) = -((-((a+1 : Nat) : Int)) / ((b+1 : Nat) : Int))
      rw [ht, Nat.add_div_left a (Nat.succ_pos b)]
      rfl

theorem initial_interval (n d B : Nat) (hd : 0 < d) :
    Encl B (n*B/d) (up (n*B) d) n d := by
  constructor
  · change n*B/d*d ≤ B*n
    rw [Nat.mul_comm B n]
    exact Nat.div_mul_le_self (n*B) d
  · change B*n ≤ up (n*B) d*d
    rw [Nat.mul_comm B n]
    exact ceil_upper (n*B) d hd

theorem product_lower {B l k p q t r : Nat} (hB : 0 < B)
    (h₁ : l*q ≤ B*p) (h₂ : k*r ≤ B*t) :
    l*k/B*(q*r) ≤ B*(p*t) := by
  apply Nat.le_of_mul_le_mul_right _ hB
  calc
    (l*k/B*(q*r))*B = (l*k/B*B)*(q*r) := by simp only [Nat.mul_left_comm, Nat.mul_comm]
    _ ≤ (l*k)*(q*r) := Nat.mul_le_mul_right (q*r) (Nat.div_mul_le_self (l*k) B)
    _ = (l*q)*(k*r) := by simp only [Nat.mul_left_comm, Nat.mul_comm]
    _ ≤ (B*p)*(B*t) := Nat.mul_le_mul h₁ h₂
    _ = B*(p*t)*B := by simp only [Nat.mul_left_comm, Nat.mul_comm]

theorem product_upper {B h k p q t r : Nat} (hB : 0 < B)
    (h₁ : B*p ≤ h*q) (h₂ : B*t ≤ k*r) :
    B*(p*t) ≤ up (h*k) B*(q*r) := by
  apply Nat.le_of_mul_le_mul_right _ hB
  calc
    B*(p*t)*B = (B*p)*(B*t) := by simp only [Nat.mul_left_comm, Nat.mul_comm]
    _ ≤ (h*q)*(k*r) := Nat.mul_le_mul h₁ h₂
    _ = (h*k)*(q*r) := by simp only [Nat.mul_left_comm, Nat.mul_comm]
    _ ≤ (up (h*k) B*B)*(q*r) := Nat.mul_le_mul_right (q*r) (ceil_upper (h*k) B hB)
    _ = (up (h*k) B*(q*r))*B := by simp only [Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm]

theorem product_interval {B l h k j p q t r : Nat} (hB : 0 < B)
    (a : Encl B l h p q) (b : Encl B k j t r) :
    Encl B (l*k/B) (up (h*j) B) (p*t) (q*r) := by
  exact ⟨product_lower hB a.1 b.1, product_upper hB a.2 b.2⟩

theorem term_interval {B l h p q k : Nat} (hk : 0 < k)
    (a : Encl B l h p q) :
    Encl B (2*l/k) (up (2*h) k) (2*p) (q*k) := by
  constructor
  · calc
      2*l/k*(q*k) = (2*l/k*k)*q := by simp only [Nat.mul_assoc, Nat.mul_comm]
      _ ≤ (2*l)*q := Nat.mul_le_mul_right q (Nat.div_mul_le_self (2*l) k)
      _ = 2*(l*q) := by simp only [Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm]
      _ ≤ 2*(B*p) := Nat.mul_le_mul_left 2 a.1
      _ = B*(2*p) := by simp only [Nat.mul_assoc, Nat.mul_comm]
  · calc
      B*(2*p) = 2*(B*p) := by simp only [Nat.mul_assoc, Nat.mul_comm]
      _ ≤ 2*(h*q) := Nat.mul_le_mul_left 2 a.2
      _ = (2*h)*q := by simp only [Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm]
      _ ≤ (up (2*h) k*k)*q := Nat.mul_le_mul_right q (ceil_upper (2*h) k hk)
      _ = up (2*h) k*(q*k) := by simp only [Nat.mul_assoc, Nat.mul_comm]

theorem add_interval {B l h k j p q t r : Nat}
    (a : Encl B l h p q) (b : Encl B k j t r) :
    Encl B (l+k) (h+j) (p*r + t*q) (q*r) := by
  constructor
  · have e : (l+k)*(q*r) ≤ B*(p*r+t*q) := by simpa only [Nat.add_mul, Nat.mul_add, Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm] using Nat.add_le_add (Nat.mul_le_mul_right r a.1) (Nat.mul_le_mul_right q b.1)
    exact e
  · have e : B*(p*r+t*q) ≤ (h+j)*(q*r) := by simpa only [Nat.add_mul, Nat.mul_add, Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm] using Nat.add_le_add (Nat.mul_le_mul_right r a.2) (Nat.mul_le_mul_right q b.2)
    exact e

theorem square_steps (n d s : Nat) (hd : 0 < d) :
    Encl (scale s) (steps n d s).lo (steps n d s).hi (n*n) (d*d) := by
  have init := initial_interval n d (scale s) hd
  exact product_interval (Nat.two_pow_pos s) init init

theorem odd_power_step (a i : Nat) :
    a ^ (2*(i+1)+1) = a ^ (2*i+1) * (a*a) := by
  have h : 2*(i+1)+1 = (2*i+1)+2 := by omega
  rw [h, Nat.pow_add, Nat.pow_two]

theorem all_prefixes (n d s i : Nat) (hd : 0 < d) :
    enclosedPrefix n d s i := by
  induction i
  case zero =>
    have h := initial_interval n d (scale s) hd
    have z : enclosedPrefix n d s 0 := by simpa [enclosedPrefix, partialSum, loopState, start, Encl] using h
    exact z
  case succ i ih =>
    rcases ih with ⟨hp, hl, hh, hsl, hsh⟩
    let v := loopState n d s i
    let t := partialSum n d i
    let k := 2*i+1
    have hk : 0 < k := Nat.succ_pos _
    have power : Encl (scale s) v.lo v.hi (n^k) (d^k) := ⟨hl, hh⟩
    have sums : Encl (scale s) v.sumLo v.sumHi t.1 t.2 := ⟨hsl, hsh⟩
    have next := product_interval (Nat.two_pow_pos s) power (square_steps n d s hd)
    have total := add_interval sums (term_interval hk power)
    have hden : 0 < t.2*(d^k*k) := Nat.mul_pos hp (Nat.mul_pos (Nat.pow_pos hd) hk)
    unfold enclosedPrefix
    simp only [loopState, advance, partialSum, odd_power_step]
    exact ⟨hden, next.1, next.2, total.1, total.2⟩

theorem returned_finite (n d s : Nat) (hd : 0 < d) : returnedClaim n d s := by
  unfold returnedClaim returned
  by_cases hn : n = 0
  · simp [hn]
  · simp only [hn, ite_false]
    obtain ⟨hp, hl, hh, hsl, hsh⟩ := all_prefixes n d s (count s) hd
    constructor
    · exact hsl
    · rw [Nat.add_mul, Nat.one_mul]
      exact Nat.add_le_add_right hsh (partialSum n d (count s)).2

theorem scheduled : Statement := by
  constructor
  · exact signed_ceiling
  · intro n d p hd hdom hp
    constructor
    · intro i hi
      exact all_prefixes n d (internalBits p) i hd
    · exact returned_finite n d (internalBits p) hd

end N2Round
