; Scope: exact Mobius inversion and zeta reconstruction on the four-node,
; two-source redundancy lattice only. Single-source coordinates are the
; self-redundancy coordinates. No estimator or higher-source claim is made.
(set-info :smt-lib-version 2.6)
(set-info :category "crafted")
(set-logic QF_LRA)

; Cumulative redundancy coordinates, ordered bottom, source 1, source 2, joint.
(declare-fun cap_bottom () Real)
(declare-fun cap_s1 () Real)
(declare-fun cap_s2 () Real)
(declare-fun cap_joint () Real)

; Four-node Mobius inversion.
(define-fun atom_redundancy () Real cap_bottom)
(define-fun atom_unique_s1 () Real (- cap_s1 cap_bottom))
(define-fun atom_unique_s2 () Real (- cap_s2 cap_bottom))
(define-fun atom_synergy () Real
  (+ (- cap_joint cap_s1 cap_s2) cap_bottom))

; Zeta reconstruction, including both single-source self-redundancy coordinates.
(define-fun recovered_bottom () Real atom_redundancy)
(define-fun recovered_s1 () Real (+ atom_redundancy atom_unique_s1))
(define-fun recovered_s2 () Real (+ atom_redundancy atom_unique_s2))
(define-fun recovered_joint () Real
  (+ atom_redundancy atom_unique_s1 atom_unique_s2 atom_synergy))

; Fixed at zero in the checked proof. The self-test changes only this anchor.
(define-fun mutation_offset () Real 0)

; No exact-real counterexample exists to inversion followed by reconstruction.
(assert
  (not
    (and
      (= recovered_bottom (+ cap_bottom mutation_offset))
      (= recovered_s1 cap_s1)
      (= recovered_s2 cap_s2)
      (= recovered_joint cap_joint))))

(check-sat)
(exit)
