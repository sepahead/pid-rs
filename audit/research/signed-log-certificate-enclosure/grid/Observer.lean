prelude
import Proof
open SignedGrid GridProof
example : (width (-5) (-3) 4, (-5:Int)/4, up (-3) 4) = (2,-2,0) := by decide +kernel
example : (width 3 5 4, (3:Int)/4, up 5 4) = (2,0,2) := by decide +kernel
example : (width (-1) 1 4, (-1:Int)/4, up 1 4) = (2,-1,1) := by decide +kernel
example : overlap (-5) (-3) (-1) 0 4 := by
  unfold overlap
  decide +kernel
example : overlap 3 5 0 1 4 := by
  unfold overlap
  decide +kernel
example : overlap (-1) 1 0 0 4 := by
  unfold overlap
  decide +kernel
example : width 3 8 4 = 2 := by decide +kernel
example : width 3 9 4 = 3 := by decide +kernel
example : width (-12) (-12) 4 = 0 := by decide +kernel
example : width (-6) (-6) 4 = 1 := by decide +kernel
example : width (-3) 2 1 = 5 := by decide +kernel
example : ¬ overlap 5 6 0 1 4 := by
  unfold overlap
  decide +kernel
example : ¬ overlap (-7) (-6) 0 1 4 := by
  unfold overlap
  decide +kernel
example (d : Int) (hd : 0 < d) : width (d-1) (d-1+(d+2)) d = 3 := next_width d hd
example (l u n : Int) (hn : 0 < n) (h : l ≤ u) (b : u-l ≤ 1385*(1+80*n)) :
    u-l < bitDivisor n ∧ (0 ≤ width l u (bitDivisor n) ∧ width l u (bitDivisor n) ≤ 2) :=
  counted_envelope u l n hn h b

set_option pp.proofs true
set_option pp.deepTerms true
set_option pp.maxSteps 3000000
#print axioms GridProof.ceiling_le
#print axioms GridProof.width_residue
#print axioms GridProof.sharp_max
#print axioms GridProof.two_grid
#print axioms GridProof.next_width
#print axioms GridProof.both_padded
#print axioms GridProof.next_padding
#print axioms GridProof.unit_cell
#print axioms GridProof.counted_envelope
#print GridProof.ceiling_le
#print GridProof.width_residue
#print GridProof.sharp_max
#print GridProof.two_grid
#print GridProof.next_width
#print GridProof.both_padded
#print GridProof.next_padding
#print GridProof.unit_cell
#print GridProof.counted_envelope
