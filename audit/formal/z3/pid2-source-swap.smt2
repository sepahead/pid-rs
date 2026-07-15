; Scope: exact source-label exchange for the four-atom, two-source PID formulas only.
; This proves no estimator, floating-point, distributional, or higher-source property.
(set-info :smt-lib-version 2.6)
(set-info :category "crafted")
(set-logic QF_LRA)

(declare-fun redundancy () Real)
(declare-fun mi_s1 () Real)
(declare-fun mi_s2 () Real)
(declare-fun mi_joint () Real)

(define-fun original_redundancy () Real redundancy)
(define-fun original_unique_s1 () Real (- mi_s1 redundancy))
(define-fun original_unique_s2 () Real (- mi_s2 redundancy))
(define-fun original_synergy () Real
  (+ (- mi_joint mi_s1 mi_s2) redundancy))

; Apply the same formulas after exchanging source labels 1 and 2.
(define-fun swapped_redundancy () Real redundancy)
(define-fun swapped_unique_s1 () Real (- mi_s2 redundancy))
(define-fun swapped_unique_s2 () Real (- mi_s1 redundancy))
(define-fun swapped_synergy () Real
  (+ (- mi_joint mi_s2 mi_s1) redundancy))

; Fixed at zero in the checked proof. The self-test changes only this anchor.
(define-fun mutation_offset () Real 0)

; A counterexample cannot change redundancy or synergy, and must exchange uniques.
(assert
  (not
    (and
      (= swapped_redundancy (+ original_redundancy mutation_offset))
      (= swapped_unique_s1 original_unique_s2)
      (= swapped_unique_s2 original_unique_s1)
      (= swapped_synergy original_synergy))))

(check-sat)
(exit)
