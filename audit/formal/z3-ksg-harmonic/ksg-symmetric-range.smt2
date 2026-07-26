; Claim: KSG-INTEGER-HARMONIC-001 revision 2, exact range and source symmetry.
; Scope: exact integer index order and exact real algebra for an arbitrary harmonic-value function.
; The result therefore does not depend on a floating association or on a solver definition of
; digamma. It proves no count geometry, estimator, support, PID, or implementation property.
(set-info :smt-lib-version 2.6)
(set-info :category "crafted")
(set-logic QF_UFLIRA)

(declare-const n Int)
(declare-const k Int)
(declare-const x Int)
(declare-const y Int)
(assert (>= n 2))
(assert (>= k 1))
(assert (< k n))
(assert (>= x k))
(assert (<= x n))
(assert (>= y k))
(assert (<= y n))

(declare-fun harmonic (Int) Real)

(define-fun min_xy () Int (ite (<= x y) x y))
(define-fun max_xy () Int (ite (<= x y) y x))
(define-fun min_yx () Int (ite (<= y x) y x))
(define-fun max_yx () Int (ite (<= y x) x y))

(define-fun direct_xy () Real
  (- (+ (harmonic (- k 1)) (harmonic (- n 1)))
     (harmonic (- x 1))
     (harmonic (- y 1))))
(define-fun direct_yx () Real
  (- (+ (harmonic (- k 1)) (harmonic (- n 1)))
     (harmonic (- y 1))
     (harmonic (- x 1))))

(define-fun range_xy () Real
  (- (- (harmonic (- n 1)) (harmonic (- max_xy 1)))
     (- (harmonic (- min_xy 1)) (harmonic (- k 1)))))
(define-fun range_yx () Real
  (- (- (harmonic (- n 1)) (harmonic (- max_yx 1)))
     (- (harmonic (- min_yx 1)) (harmonic (- k 1)))))

; Fixed at zero in the checked theorem. The self-test makes it nonzero.
(define-fun mutation_offset () Real 0.0)

(define-fun theorem_holds () Bool
  (and (= direct_xy (+ range_xy mutation_offset))
       (= direct_yx range_yx)
       (= direct_xy direct_yx)
       (= range_xy range_yx)))

; No exact-real counterexample to range reassociation or source exchange can exist.
(assert (not theorem_holds))
(check-sat)
(exit)
