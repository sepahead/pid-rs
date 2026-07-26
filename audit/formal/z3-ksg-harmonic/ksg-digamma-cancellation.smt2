; Claim: KSG-INTEGER-HARMONIC-001 revision 2, typed four-term cancellation seam.
; Scope: exact integer indices and exact real algebra under four explicitly asserted instances of
; the positive-integer digamma premise. This does not prove that analytic premise.
; It proves no neighbor geometry, estimator, floating-point, support, PID, or Rust property.
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
(declare-fun psi (Int) Real)
(declare-const euler_constant Real)

; These are the only special-function premises used by this route.
(assert (= (psi k) (- (harmonic (- k 1)) euler_constant)))
(assert (= (psi n) (- (harmonic (- n 1)) euler_constant)))
(assert (= (psi x) (- (harmonic (- x 1)) euler_constant)))
(assert (= (psi y) (- (harmonic (- y 1)) euler_constant)))

(define-fun direct_harmonic () Real
  (- (+ (harmonic (- k 1)) (harmonic (- n 1)))
     (harmonic (- x 1))
     (harmonic (- y 1))))

; Fixed at zero in the checked theorem. The self-test makes it nonzero.
(define-fun mutation_offset () Real 0.0)

(define-fun theorem_holds () Bool
  (= (- (+ (psi k) (psi n)) (psi x) (psi y))
     (+ direct_harmonic mutation_offset)))

; A counterexample to cancellation under the four typed premises cannot exist.
(assert (not theorem_holds))
(check-sat)
(exit)
