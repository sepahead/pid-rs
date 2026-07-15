; Scope: exact linear arithmetic for the four-atom, two-source PID identity only.
; This proves no estimator, floating-point, distributional, or higher-source property.
(set-info :smt-lib-version 2.6)
(set-info :category "crafted")
(set-logic QF_LRA)

(declare-fun redundancy () Real)
(declare-fun mi_s1 () Real)
(declare-fun mi_s2 () Real)
(declare-fun mi_joint () Real)

(define-fun atom_redundancy () Real redundancy)
(define-fun atom_unique_s1 () Real (- mi_s1 redundancy))
(define-fun atom_unique_s2 () Real (- mi_s2 redundancy))
(define-fun atom_synergy () Real
  (+ (- mi_joint mi_s1 mi_s2) redundancy))

; Fixed at zero in the checked proof. The self-test changes only this anchor.
(define-fun mutation_offset () Real 0)

; A counterexample to atom-sum reconstruction cannot exist over exact reals.
(assert
  (not
    (= (+ atom_redundancy atom_unique_s1 atom_unique_s2 atom_synergy)
       (+ mi_joint mutation_offset))))

(check-sat)
(exit)
