; Scope: exact source-permutation equivariance of Mobius inversion on the
; complete 18-node, three-source redundancy lattice only.
;
; The coordinate suffixes are canonical antichains of nonempty source masks.
; The proof checks swaps S0<->S1 and S1<->S2. These adjacent swaps generate
; all six permutations of three sources.
;
; This proves no estimator symmetry premise, asymptotic, floating-point,
; distributional, support, or four-source property. It is not a Rust
; refinement proof.
(set-info :smt-lib-version 2.6)
(set-info :category "crafted")
(set-logic QF_LRA)

; Arbitrary cumulative redundancy coordinates.
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

; Exact Mobius inversion before a source permutation.
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

; Relabel the cumulative coordinates by swapping sources S0 and S1.
(define-fun cap_01_001 () Real cap_010)
(define-fun cap_01_010 () Real cap_001)
(define-fun cap_01_100 () Real cap_100)
(define-fun cap_01_011 () Real cap_011)
(define-fun cap_01_101 () Real cap_110)
(define-fun cap_01_110 () Real cap_101)
(define-fun cap_01_111 () Real cap_111)
(define-fun cap_01_001_010 () Real cap_001_010)
(define-fun cap_01_001_100 () Real cap_010_100)
(define-fun cap_01_001_110 () Real cap_010_101)
(define-fun cap_01_010_100 () Real cap_001_100)
(define-fun cap_01_010_101 () Real cap_001_110)
(define-fun cap_01_011_100 () Real cap_011_100)
(define-fun cap_01_011_101 () Real cap_011_110)
(define-fun cap_01_011_110 () Real cap_011_101)
(define-fun cap_01_101_110 () Real cap_101_110)
(define-fun cap_01_001_010_100 () Real cap_001_010_100)
(define-fun cap_01_011_101_110 () Real cap_011_101_110)

; Apply the same Mobius formulas after the S0/S1 swap.
(define-fun atom_01_001 () Real (- cap_01_001 cap_01_001_110))
(define-fun atom_01_010 () Real (- cap_01_010 cap_01_010_101))
(define-fun atom_01_100 () Real (- cap_01_100 cap_01_011_100))
(define-fun atom_01_011 () Real
  (+ cap_01_011 (- cap_01_011_101) (- cap_01_011_110)
     cap_01_011_101_110))
(define-fun atom_01_101 () Real
  (+ cap_01_101 (- cap_01_011_101) (- cap_01_101_110)
     cap_01_011_101_110))
(define-fun atom_01_110 () Real
  (+ cap_01_110 (- cap_01_011_110) (- cap_01_101_110)
     cap_01_011_101_110))
(define-fun atom_01_111 () Real
  (+ (- cap_01_011) (- cap_01_101) (- cap_01_110) cap_01_111
     cap_01_011_101 cap_01_011_110 cap_01_101_110
     (- cap_01_011_101_110)))
(define-fun atom_01_001_010 () Real
  (- cap_01_001_010 cap_01_001_010_100))
(define-fun atom_01_001_100 () Real
  (- cap_01_001_100 cap_01_001_010_100))
(define-fun atom_01_001_110 () Real
  (+ (- cap_01_001_010) (- cap_01_001_100) cap_01_001_110
     cap_01_001_010_100))
(define-fun atom_01_010_100 () Real
  (- cap_01_010_100 cap_01_001_010_100))
(define-fun atom_01_010_101 () Real
  (+ (- cap_01_001_010) (- cap_01_010_100) cap_01_010_101
     cap_01_001_010_100))
(define-fun atom_01_011_100 () Real
  (+ (- cap_01_001_100) (- cap_01_010_100) cap_01_011_100
     cap_01_001_010_100))
(define-fun atom_01_011_101 () Real
  (+ (- cap_01_001) cap_01_001_110 cap_01_011_101
     (- cap_01_011_101_110)))
(define-fun atom_01_011_110 () Real
  (+ (- cap_01_010) cap_01_010_101 cap_01_011_110
     (- cap_01_011_101_110)))
(define-fun atom_01_101_110 () Real
  (+ (- cap_01_100) cap_01_011_100 cap_01_101_110
     (- cap_01_011_101_110)))
(define-fun atom_01_001_010_100 () Real cap_01_001_010_100)
(define-fun atom_01_011_101_110 () Real
  (+ cap_01_001_010 cap_01_001_100 (- cap_01_001_110)
     cap_01_010_100 (- cap_01_010_101) (- cap_01_011_100)
     (- cap_01_001_010_100) cap_01_011_101_110))

; Relabel the cumulative coordinates by swapping sources S1 and S2.
(define-fun cap_12_001 () Real cap_001)
(define-fun cap_12_010 () Real cap_100)
(define-fun cap_12_100 () Real cap_010)
(define-fun cap_12_011 () Real cap_101)
(define-fun cap_12_101 () Real cap_011)
(define-fun cap_12_110 () Real cap_110)
(define-fun cap_12_111 () Real cap_111)
(define-fun cap_12_001_010 () Real cap_001_100)
(define-fun cap_12_001_100 () Real cap_001_010)
(define-fun cap_12_001_110 () Real cap_001_110)
(define-fun cap_12_010_100 () Real cap_010_100)
(define-fun cap_12_010_101 () Real cap_011_100)
(define-fun cap_12_011_100 () Real cap_010_101)
(define-fun cap_12_011_101 () Real cap_011_101)
(define-fun cap_12_011_110 () Real cap_101_110)
(define-fun cap_12_101_110 () Real cap_011_110)
(define-fun cap_12_001_010_100 () Real cap_001_010_100)
(define-fun cap_12_011_101_110 () Real cap_011_101_110)

; Apply the same Mobius formulas after the S1/S2 swap.
(define-fun atom_12_001 () Real (- cap_12_001 cap_12_001_110))
(define-fun atom_12_010 () Real (- cap_12_010 cap_12_010_101))
(define-fun atom_12_100 () Real (- cap_12_100 cap_12_011_100))
(define-fun atom_12_011 () Real
  (+ cap_12_011 (- cap_12_011_101) (- cap_12_011_110)
     cap_12_011_101_110))
(define-fun atom_12_101 () Real
  (+ cap_12_101 (- cap_12_011_101) (- cap_12_101_110)
     cap_12_011_101_110))
(define-fun atom_12_110 () Real
  (+ cap_12_110 (- cap_12_011_110) (- cap_12_101_110)
     cap_12_011_101_110))
(define-fun atom_12_111 () Real
  (+ (- cap_12_011) (- cap_12_101) (- cap_12_110) cap_12_111
     cap_12_011_101 cap_12_011_110 cap_12_101_110
     (- cap_12_011_101_110)))
(define-fun atom_12_001_010 () Real
  (- cap_12_001_010 cap_12_001_010_100))
(define-fun atom_12_001_100 () Real
  (- cap_12_001_100 cap_12_001_010_100))
(define-fun atom_12_001_110 () Real
  (+ (- cap_12_001_010) (- cap_12_001_100) cap_12_001_110
     cap_12_001_010_100))
(define-fun atom_12_010_100 () Real
  (- cap_12_010_100 cap_12_001_010_100))
(define-fun atom_12_010_101 () Real
  (+ (- cap_12_001_010) (- cap_12_010_100) cap_12_010_101
     cap_12_001_010_100))
(define-fun atom_12_011_100 () Real
  (+ (- cap_12_001_100) (- cap_12_010_100) cap_12_011_100
     cap_12_001_010_100))
(define-fun atom_12_011_101 () Real
  (+ (- cap_12_001) cap_12_001_110 cap_12_011_101
     (- cap_12_011_101_110)))
(define-fun atom_12_011_110 () Real
  (+ (- cap_12_010) cap_12_010_101 cap_12_011_110
     (- cap_12_011_101_110)))
(define-fun atom_12_101_110 () Real
  (+ (- cap_12_100) cap_12_011_100 cap_12_101_110
     (- cap_12_011_101_110)))
(define-fun atom_12_001_010_100 () Real cap_12_001_010_100)
(define-fun atom_12_011_101_110 () Real
  (+ cap_12_001_010 cap_12_001_100 (- cap_12_001_110)
     cap_12_010_100 (- cap_12_010_101) (- cap_12_011_100)
     (- cap_12_001_010_100) cap_12_011_101_110))

; Fixed at zero in the checked proof. The self-test changes only this anchor.
(define-fun mutation_offset () Real 0)

; Each transformed atom must have the transformed antichain coordinate.
(assert
  (not
    (and
      ; S0/S1 swap.
      (= atom_01_001 (+ atom_010 mutation_offset))
      (= atom_01_010 atom_001)
      (= atom_01_100 atom_100)
      (= atom_01_011 atom_011)
      (= atom_01_101 atom_110)
      (= atom_01_110 atom_101)
      (= atom_01_111 atom_111)
      (= atom_01_001_010 atom_001_010)
      (= atom_01_001_100 atom_010_100)
      (= atom_01_001_110 atom_010_101)
      (= atom_01_010_100 atom_001_100)
      (= atom_01_010_101 atom_001_110)
      (= atom_01_011_100 atom_011_100)
      (= atom_01_011_101 atom_011_110)
      (= atom_01_011_110 atom_011_101)
      (= atom_01_101_110 atom_101_110)
      (= atom_01_001_010_100 atom_001_010_100)
      (= atom_01_011_101_110 atom_011_101_110)

      ; S1/S2 swap.
      (= atom_12_001 atom_001)
      (= atom_12_010 atom_100)
      (= atom_12_100 atom_010)
      (= atom_12_011 atom_101)
      (= atom_12_101 atom_011)
      (= atom_12_110 atom_110)
      (= atom_12_111 atom_111)
      (= atom_12_001_010 atom_001_100)
      (= atom_12_001_100 atom_001_010)
      (= atom_12_001_110 atom_001_110)
      (= atom_12_010_100 atom_010_100)
      (= atom_12_010_101 atom_011_100)
      (= atom_12_011_100 atom_010_101)
      (= atom_12_011_101 atom_011_101)
      (= atom_12_011_110 atom_101_110)
      (= atom_12_101_110 atom_011_110)
      (= atom_12_001_010_100 atom_001_010_100)
      (= atom_12_011_101_110 atom_011_101_110))))

(check-sat)
(exit)
