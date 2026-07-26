; Claim: KSG-INTEGER-HARMONIC-001 revision 2, exclusive and inclusive count-index maps.
; Scope: exact integer arithmetic plus an arbitrary exact-real harmonic-value function.
; Exclusive KSG counts receive one successor; Ehrlich anchor-inclusive counts receive none.
; This does not prove that any neighbor routine produced the declared counts.
(set-info :smt-lib-version 2.6)
(set-info :category "crafted")
(set-logic QF_UFLIRA)

(declare-const n Int)
(declare-const k Int)
(declare-const nx Int)
(declare-const ny Int)
(declare-const inclusive_x Int)
(declare-const inclusive_y Int)

(assert (>= n 2))
(assert (>= k 1))
(assert (< k n))
(assert (>= nx (- k 1)))
(assert (< nx n))
(assert (>= ny (- k 1)))
(assert (< ny n))
(assert (>= inclusive_x k))
(assert (<= inclusive_x n))
(assert (>= inclusive_y k))
(assert (<= inclusive_y n))

(declare-fun harmonic (Int) Real)

(define-fun exclusive_x () Int (+ nx 1))
(define-fun exclusive_y () Int (+ ny 1))
(define-fun inclusive_argument_x () Int inclusive_x)
(define-fun inclusive_argument_y () Int inclusive_y)

(define-fun exclusive_direct () Real
  (- (+ (harmonic (- k 1)) (harmonic (- n 1)))
     (harmonic (- exclusive_x 1))
     (harmonic (- exclusive_y 1))))
(define-fun exclusive_count_form () Real
  (- (+ (harmonic (- k 1)) (harmonic (- n 1)))
     (harmonic nx)
     (harmonic ny)))

(define-fun inclusive_direct () Real
  (- (+ (harmonic (- k 1)) (harmonic (- n 1)))
     (harmonic (- inclusive_argument_x 1))
     (harmonic (- inclusive_argument_y 1))))
(define-fun inclusive_count_form () Real
  (- (+ (harmonic (- k 1)) (harmonic (- n 1)))
     (harmonic (- inclusive_x 1))
     (harmonic (- inclusive_y 1))))

; Fixed at zero in the checked theorem. The self-test makes one predecessor map false.
(define-fun mutation_offset () Int 0)

(define-fun theorem_holds () Bool
  (and (>= exclusive_x k)
       (<= exclusive_x n)
       (>= exclusive_y k)
       (<= exclusive_y n)
       (= (- exclusive_x 1) (+ nx mutation_offset))
       (= (- exclusive_y 1) ny)
       (= exclusive_direct exclusive_count_form)
       (= inclusive_argument_x inclusive_x)
       (= inclusive_argument_y inclusive_y)
       (= inclusive_direct inclusive_count_form)))

; No counterexample to the two declared index maps can exist in the stated domains.
(assert (not theorem_holds))
(check-sat)
(exit)
