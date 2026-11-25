prelude
import Proof
open W7
example (n k x y : Nat) (hk : 0 < k) (hn : k < n) :
    (∃ (rows : List Row) (r : Nat), rows.length + 1 = n ∧ Realizes rows r k x y) ↔ Triangle n k x y :=
  attainable_iff n k x y hk hn
example (rows : List Row) (r k x y : Nat) (h : Realizes rows r k x y) :
    Triangle (rows.length + 1) k x y := necessary rows r k x y h
example (h p q d : Nat) (extra : 0 < p+q+d) :
    (witness h p q d).length = h+p+q+d ∧ Realizes (witness h p q d) 2 (h+1) (h+p+1) (h+q+1) :=
  constructed h p q d extra
example : Realizes [⟨2,4,2⟩] 2 1 1 1 := by decide +kernel
example : Realizes [⟨1,4,2⟩] 2 1 2 1 := by decide +kernel
example : Realizes [⟨2,4,1⟩] 2 1 1 2 := by decide +kernel
example : ¬ Realizes [] 2 1 1 1 := by decide +kernel
example : ¬ Realizes [⟨0,0,0⟩] 0 1 1 1 := by decide +kernel
example : ¬ Realizes [⟨1,4,2⟩,⟨2,4,1⟩] 2 1 2 2 := by decide +kernel
example : ¬ Realizes [⟨1,4,2⟩] 2 1 1 1 := by decide +kernel
example : Realizes [⟨2,26,3⟩,⟨33,5,10⟩,⟨19,27,2⟩,⟨41,22,7⟩] 10 2 3 4 := by decide +kernel
#print axioms W7.inner_pair
#print axioms W7.counts
#print axioms W7.necessary
#print axioms W7.constructed
#print axioms W7.attainable_iff
set_option pp.proofs true in
#print W7.inner_pair
set_option pp.proofs true in
#print W7.counts
set_option pp.proofs true in
#print W7.necessary
set_option pp.proofs true in
#print W7.constructed
set_option pp.proofs true in
#print W7.attainable_iff
