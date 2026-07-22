; Scope: exact Mobius inversion and zeta reconstruction on the complete
; 18-node, three-source redundancy lattice only.
;
; The coordinate suffixes are canonical antichains of nonempty source masks.
; For example, 001_110 denotes {{S0}, {S1,S2}}. The lattice order is
; alpha <= beta when each set in beta contains a set in alpha.
;
; This proves no estimator, asymptotic, floating-point, distributional,
; support, or four-source property. It is not a Rust refinement proof.
(set-info :smt-lib-version 2.6)
(set-info :category "crafted")
(set-logic QF_LRA)

; Cumulative redundancy coordinates in the canonical pid-rs order.
(declare-fun cap_001 () Real)
(declare-fun cap_010 () Real)
(declare-fun cap_100 () Real)
(declare-fun cap_011 () Real)
(declare-fun cap_101 () Real)
(declare-fun cap_110 () Real)
(declare-fun cap_111 () Real)
(declare-fun cap_001_010 () Real)
(declare-fun cap_001_100 () Real)
(declare-fun cap_001_110 () Real)
(declare-fun cap_010_100 () Real)
(declare-fun cap_010_101 () Real)
(declare-fun cap_011_100 () Real)
(declare-fun cap_011_101 () Real)
(declare-fun cap_011_110 () Real)
(declare-fun cap_101_110 () Real)
(declare-fun cap_001_010_100 () Real)
(declare-fun cap_011_101_110 () Real)

; Exact Mobius inversion of the 18-by-18 zeta matrix.
(define-fun atom_001 () Real (- cap_001 cap_001_110))
(define-fun atom_010 () Real (- cap_010 cap_010_101))
(define-fun atom_100 () Real (- cap_100 cap_011_100))
(define-fun atom_011 () Real
  (+ cap_011 (- cap_011_101) (- cap_011_110) cap_011_101_110))
(define-fun atom_101 () Real
  (+ cap_101 (- cap_011_101) (- cap_101_110) cap_011_101_110))
(define-fun atom_110 () Real
  (+ cap_110 (- cap_011_110) (- cap_101_110) cap_011_101_110))
(define-fun atom_111 () Real
  (+ (- cap_011) (- cap_101) (- cap_110) cap_111
     cap_011_101 cap_011_110 cap_101_110 (- cap_011_101_110)))
(define-fun atom_001_010 () Real (- cap_001_010 cap_001_010_100))
(define-fun atom_001_100 () Real (- cap_001_100 cap_001_010_100))
(define-fun atom_001_110 () Real
  (+ (- cap_001_010) (- cap_001_100) cap_001_110 cap_001_010_100))
(define-fun atom_010_100 () Real (- cap_010_100 cap_001_010_100))
(define-fun atom_010_101 () Real
  (+ (- cap_001_010) (- cap_010_100) cap_010_101 cap_001_010_100))
(define-fun atom_011_100 () Real
  (+ (- cap_001_100) (- cap_010_100) cap_011_100 cap_001_010_100))
(define-fun atom_011_101 () Real
  (+ (- cap_001) cap_001_110 cap_011_101 (- cap_011_101_110)))
(define-fun atom_011_110 () Real
  (+ (- cap_010) cap_010_101 cap_011_110 (- cap_011_101_110)))
(define-fun atom_101_110 () Real
  (+ (- cap_100) cap_011_100 cap_101_110 (- cap_011_101_110)))
(define-fun atom_001_010_100 () Real cap_001_010_100)
(define-fun atom_011_101_110 () Real
  (+ cap_001_010 cap_001_100 (- cap_001_110) cap_010_100
     (- cap_010_101) (- cap_011_100) (- cap_001_010_100)
     cap_011_101_110))

; Zeta reconstruction from each node's exact down-set.
(define-fun recovered_001 () Real
  (+ atom_001 atom_001_010 atom_001_100 atom_001_110 atom_001_010_100))
(define-fun recovered_010 () Real
  (+ atom_010 atom_001_010 atom_010_100 atom_010_101 atom_001_010_100))
(define-fun recovered_100 () Real
  (+ atom_100 atom_001_100 atom_010_100 atom_011_100 atom_001_010_100))
(define-fun recovered_011 () Real
  (+ atom_001 atom_010 atom_011 atom_001_010 atom_001_100
     atom_001_110 atom_010_100 atom_010_101 atom_011_100
     atom_011_101 atom_011_110 atom_001_010_100 atom_011_101_110))
(define-fun recovered_101 () Real
  (+ atom_001 atom_100 atom_101 atom_001_010 atom_001_100
     atom_001_110 atom_010_100 atom_010_101 atom_011_100
     atom_011_101 atom_101_110 atom_001_010_100 atom_011_101_110))
(define-fun recovered_110 () Real
  (+ atom_010 atom_100 atom_110 atom_001_010 atom_001_100
     atom_001_110 atom_010_100 atom_010_101 atom_011_100
     atom_011_110 atom_101_110 atom_001_010_100 atom_011_101_110))
(define-fun recovered_111 () Real
  (+ atom_001 atom_010 atom_100 atom_011 atom_101 atom_110 atom_111
     atom_001_010 atom_001_100 atom_001_110 atom_010_100 atom_010_101
     atom_011_100 atom_011_101 atom_011_110 atom_101_110
     atom_001_010_100 atom_011_101_110))
(define-fun recovered_001_010 () Real
  (+ atom_001_010 atom_001_010_100))
(define-fun recovered_001_100 () Real
  (+ atom_001_100 atom_001_010_100))
(define-fun recovered_001_110 () Real
  (+ atom_001_010 atom_001_100 atom_001_110 atom_001_010_100))
(define-fun recovered_010_100 () Real
  (+ atom_010_100 atom_001_010_100))
(define-fun recovered_010_101 () Real
  (+ atom_001_010 atom_010_100 atom_010_101 atom_001_010_100))
(define-fun recovered_011_100 () Real
  (+ atom_001_100 atom_010_100 atom_011_100 atom_001_010_100))
(define-fun recovered_011_101 () Real
  (+ atom_001 atom_001_010 atom_001_100 atom_001_110 atom_010_100
     atom_010_101 atom_011_100 atom_011_101 atom_001_010_100
     atom_011_101_110))
(define-fun recovered_011_110 () Real
  (+ atom_010 atom_001_010 atom_001_100 atom_001_110 atom_010_100
     atom_010_101 atom_011_100 atom_011_110 atom_001_010_100
     atom_011_101_110))
(define-fun recovered_101_110 () Real
  (+ atom_100 atom_001_010 atom_001_100 atom_001_110 atom_010_100
     atom_010_101 atom_011_100 atom_101_110 atom_001_010_100
     atom_011_101_110))
(define-fun recovered_001_010_100 () Real atom_001_010_100)
(define-fun recovered_011_101_110 () Real
  (+ atom_001_010 atom_001_100 atom_001_110 atom_010_100
     atom_010_101 atom_011_100 atom_001_010_100 atom_011_101_110))

; Fixed at zero in the checked proof. The self-test changes only this anchor.
(define-fun mutation_offset () Real 0)

; No exact-real counterexample exists to inversion followed by reconstruction.
(assert
  (not
    (and
      (= recovered_001 (+ cap_001 mutation_offset))
      (= recovered_010 cap_010)
      (= recovered_100 cap_100)
      (= recovered_011 cap_011)
      (= recovered_101 cap_101)
      (= recovered_110 cap_110)
      (= recovered_111 cap_111)
      (= recovered_001_010 cap_001_010)
      (= recovered_001_100 cap_001_100)
      (= recovered_001_110 cap_001_110)
      (= recovered_010_100 cap_010_100)
      (= recovered_010_101 cap_010_101)
      (= recovered_011_100 cap_011_100)
      (= recovered_011_101 cap_011_101)
      (= recovered_011_110 cap_011_110)
      (= recovered_101_110 cap_101_110)
      (= recovered_001_010_100 cap_001_010_100)
      (= recovered_011_101_110 cap_011_101_110))))

(check-sat)
(exit)
