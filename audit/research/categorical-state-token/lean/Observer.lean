prelude
import Proof

open D1Token

example (t rest : List UInt8) (h : Admissible t) :
    read (emit t ++ rest) = some (t, rest) := read_emit t rest h
example (word t rest : List UInt8) (h : read word = some (t, rest)) :
    Admissible t ∧ word = emit t ++ rest := read_sound word t rest h
example (word t rest : List UInt8) :
    read word = some (t, rest) ↔ Admissible t ∧ word = emit t ++ rest := read_iff word t rest
example (word t u rest s : List UInt8) (h : read word = some (t, rest))
    (g : read word = some (u, s)) : t = u ∧ rest = s := unique word t u rest s h g
example : read (emit [65] ++ [0,34,255]) = some ([65], [0,34,255]) := by decide +kernel
example : read (emit [97,98,48,46,95,58,45] ++ [44,255]) =
    some ([97,98,48,46,95,58,45], [44,255]) := by decide +kernel
example : read (emit (List.replicate 128 90) ++ [34]) =
    some (List.replicate 128 90, [34]) := by decide +kernel
example : read (emit (List.replicate 129 90)) = none := by decide +kernel
example : read [] = none := by decide +kernel
example : read [34,34] = none := by decide +kernel
example : read [65,34] = none := by decide +kernel
example : read [34,65] = none := by decide +kernel
example : read [34,65,44,34] = none := by decide +kernel
example : read [34,65,92,34,34] = none := by decide +kernel
example : read [34,255,34] = none := by decide +kernel
example : read [34,65,34,97,34] = some ([65],[97,34]) := by decide +kernel

#print axioms D1Token.read_emit
#print axioms D1Token.read_sound
#print axioms D1Token.read_iff
#print axioms D1Token.unique
set_option pp.proofs true in
#print D1Token.read_emit
set_option pp.proofs true in
#print D1Token.read_sound
set_option pp.proofs true in
#print D1Token.read_iff
set_option pp.proofs true in
#print D1Token.unique
