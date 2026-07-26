; Claim: KSG-INTEGER-HARMONIC-001 revision 4, exact local full-tail bound.
; Scope: exact integer indices and exact real algebra for harmonic values under three explicit
; monotonic-order instances. Lean separately proves universal monotonicity of the rational finite
; harmonic sum. This SMT route does not prove those order premises, the analytic digamma premise,
; neighbor geometry, floating-point behavior, an estimator, support, PID, or Rust refinement.
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
(define-fun h_k () Real (harmonic (- k 1)))
(define-fun h_n () Real (harmonic (- n 1)))
(define-fun h_min () Real (harmonic (- min_xy 1)))
(define-fun h_max () Real (harmonic (- max_xy 1)))

; These are the only harmonic-order premises used by this independent linear route.
(assert (<= h_k h_min))
(assert (<= h_min h_max))
(assert (<= h_max h_n))

(define-fun direct_value () Real
  (- (+ h_k h_n)
     (harmonic (- x 1))
     (harmonic (- y 1))))
(define-fun range_value () Real
  (- (- h_n h_max)
     (- h_min h_k)))
(define-fun full_tail () Real (- h_n h_k))

; Fixed at zero in the checked theorem. The self-test tightens the lower bound.
(define-fun mutation_offset () Real 0.0)

(define-fun theorem_holds () Bool
  (and (= direct_value range_value)
       (<= (+ (- full_tail) mutation_offset) range_value)
       (<= range_value full_tail)))

; No exact-real counterexample exists under the stated index and order premises.
(assert (not theorem_holds))
(check-sat)
(exit)
