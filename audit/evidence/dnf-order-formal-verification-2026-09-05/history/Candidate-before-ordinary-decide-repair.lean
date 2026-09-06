import Contract
set_option autoImplicit false
set_option warningAsError true
namespace PidSxDnfOrderCandidate

open PidSxDnfOrderContract PidFiniteConvergence

universe u v w

/-- The characteristic pattern of a branch supplies the reverse implication. -/
theorem order_iff_dnf (sourceIndex : Type u) [DecidableEq sourceIndex] :
    order_iff_dnf_target sourceIndex := by
  intro alpha beta
  constructor
  · intro hOrder pattern hBeta
    obtain ⟨b, hb, hPattern⟩ := hBeta
    obtain ⟨a, ha, hab⟩ := hOrder b hb
    exact ⟨a, ha, fun source hsource => hPattern source (hab hsource)⟩
  · intro hImplication b hb
    have hBeta : DNF beta (fun source => decide (source ∈ b)) := by
      refine ⟨b, hb, ?_⟩
      intro source hsource
      exact decide_eq_true hsource
    obtain ⟨a, ha, hPattern⟩ := hImplication _ hBeta
    refine ⟨a, ha, ?_⟩
    intro source hsource
    exact of_decide_eq_true (hPattern source hsource)

/-- Two rounds of the order witnesses identify each minimal branch. -/
theorem antichain_antisymm (sourceIndex : Type u) [DecidableEq sourceIndex] :
    antichain_antisymm_target sourceIndex := by
  intro alpha beta hAlpha hBeta hAB hBA
  apply Finset.Subset.antisymm
  · intro a ha
    obtain ⟨b, hb, hba⟩ := hBA a ha
    obtain ⟨c, hc, hcb⟩ := hAB b hb
    have hca : c = a := hAlpha c hc a ha (Finset.Subset.trans hcb hba)
    have hab : a ⊆ b := hca ▸ hcb
    have habEqual : a = b := Finset.Subset.antisymm hab hba
    rw [habEqual]
    exact hb
  · intro b hb
    obtain ⟨a, ha, hab⟩ := hAB b hb
    obtain ⟨c, hc, hca⟩ := hBA a ha
    have hcb : c = b := hBeta c hc b hb (Finset.Subset.trans hca hab)
    have hba : b ⊆ a := hcb ▸ hca
    have hbaEqual : b = a := Finset.Subset.antisymm hba hab
    rw [hbaEqual]
    exact ha

theorem dnf_injective_on_antichains (sourceIndex : Type u) [DecidableEq sourceIndex] :
    dnf_injective_on_antichains_target sourceIndex := by
  intro alpha beta hAlpha hBeta hSemantics
  apply antichain_antisymm sourceIndex alpha beta hAlpha hBeta
  · exact (order_iff_dnf sourceIndex alpha beta).2
      (fun pattern => (hSemantics pattern).2)
  · exact (order_iff_dnf sourceIndex beta alpha).2
      (fun pattern => (hSemantics pattern).1)

theorem source_event_iff_dnf
    (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] :
    source_event_iff_dnf_target sourceIndex sourceValue targetValue := by
  classical
  intro collections anchor candidate
  constructor
  · intro hEvent
    obtain ⟨collection, hCollection, hBranch⟩ := Finset.mem_biUnion.mp hEvent
    have hMatch : sourceCollectionEquivalent collection anchor candidate :=
      (Finset.mem_filter.mp hBranch).2
    refine ⟨collection, hCollection, ?_⟩
    intro source hSource
    exact decide_eq_true (hMatch source hSource)
  · intro hDNF
    obtain ⟨collection, hCollection, hPattern⟩ := hDNF
    apply Finset.mem_biUnion.mpr
    refine ⟨collection, hCollection, Finset.mem_filter.mpr ⟨Finset.mem_univ _, ?_⟩⟩
    intro source hSource
    exact of_decide_eq_true (hPattern source hSource)

theorem order_implies_source_event_subset
    (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] :
    order_implies_source_event_subset_target sourceIndex sourceValue targetValue := by
  intro alpha beta anchor hOrder candidate hCandidate
  apply (source_event_iff_dnf sourceIndex sourceValue targetValue alpha anchor candidate).2
  exact (order_iff_dnf sourceIndex alpha beta).1 hOrder _
    ((source_event_iff_dnf sourceIndex sourceValue targetValue beta anchor candidate).1 hCandidate)

theorem order_iff_implication_on_realizing_domain
    (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] :
    order_iff_implication_on_realizing_domain_target sourceIndex sourceValue targetValue := by
  intro alpha beta anchor domain hRealizes
  constructor
  · intro hOrder candidate _hDomain hCandidate
    exact order_implies_source_event_subset sourceIndex sourceValue targetValue
      alpha beta anchor hOrder hCandidate
  · intro hImplication
    apply (order_iff_dnf sourceIndex alpha beta).2
    intro pattern hBeta
    obtain ⟨candidate, hDomain, hPattern⟩ := hRealizes pattern
    have hCandidate : candidate ∈ sxSourceEvent beta anchor := by
      apply (source_event_iff_dnf sourceIndex sourceValue targetValue beta anchor candidate).2
      rw [hPattern]
      exact hBeta
    have hAlpha := (source_event_iff_dnf sourceIndex sourceValue targetValue alpha anchor candidate).1
      (hImplication candidate hDomain hCandidate)
    simpa only [hPattern] using hAlpha

theorem alternate_values_realize_all_patterns
    (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] :
    alternate_values_realize_all_patterns_target sourceIndex sourceValue targetValue := by
  intro anchor alternate hAlternate pattern
  refine ⟨(fun source => if pattern source = true then anchor.1 source else alternate source,
    anchor.2), Set.mem_univ _, ?_⟩
  funext source
  cases hPattern : pattern source with
  | false => simp [EqualityPattern, hPattern, Ne.symm (hAlternate source)]
  | true => simp [EqualityPattern, hPattern]

theorem source_event_injective_on_realizing_domain
    (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] :
    source_event_injective_on_realizing_domain_target sourceIndex sourceValue targetValue := by
  intro alpha beta hAlpha hBeta anchor domain hRealizes hEvents
  apply dnf_injective_on_antichains sourceIndex alpha beta hAlpha hBeta
  intro pattern
  obtain ⟨candidate, hDomain, hPattern⟩ := hRealizes pattern
  rw [← hPattern]
  exact (source_event_iff_dnf sourceIndex sourceValue targetValue alpha anchor candidate).symm.trans
    ((hEvents candidate hDomain).trans
      (source_event_iff_dnf sourceIndex sourceValue targetValue beta anchor candidate))

theorem order_implies_target_restricted_subset
    (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] :
    order_implies_target_restricted_subset_target sourceIndex sourceValue targetValue := by
  intro alpha beta anchor hOrder
  rw [sx_target_restricted_event_eq_inter, sx_target_restricted_event_eq_inter]
  intro candidate hCandidate
  have hParts := Finset.mem_inter.mp hCandidate
  exact Finset.mem_inter.mpr
    ⟨order_implies_source_event_subset sourceIndex sourceValue targetValue
      alpha beta anchor hOrder hParts.1, hParts.2⟩

/-- Singleton alphabets identify distinct antichains at the event level. -/
theorem singleton_event_collision : singleton_event_collision_target := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩
  · simp [IsInclusionAntichain, singletonLeft]
  · simp [IsInclusionAntichain, singletonRight]
  · decide +kernel
  · simp only [RedundancyLE]
    decide +kernel
  · simp only [RedundancyLE]
    decide +kernel
  · ext candidate
    simp [sxSourceEvent, sourceBranchEvent, sourceCollectionEquivalent,
      singletonLeft, singletonRight, singletonAnchor]

theorem singleton_not_all_patterns : singleton_not_all_patterns_target := by
  intro hRealizes
  obtain ⟨candidate, _hDomain, hPattern⟩ := hRealizes (fun _ => false)
  have hAtZero := congrFun hPattern 0
  simp [EqualityPattern, singletonAnchor] at hAtZero

theorem binary_diagonal_collision : binary_diagonal_collision_target := by
  refine ⟨?_, ?_, ?_⟩
  · intro candidate hDiagonal
    have hEqual : candidate.1 0 = candidate.1 1 := hDiagonal.1
    simp [sxSourceEvent, sourceBranchEvent, sourceCollectionEquivalent,
      singletonLeft, singletonRight, binaryAnchor, hEqual]
  · intro hEvents
    let candidate : CategoricalKey (Fin 3) (fun _ => Bool) Unit :=
      (fun source => decide (source ≠ 0), ())
    have hLeft : candidate ∈ sxSourceEvent singletonLeft binaryAnchor := by
      simp [candidate, sxSourceEvent, sourceBranchEvent, sourceCollectionEquivalent,
        singletonLeft, binaryAnchor]
    have hRight : candidate ∉ sxSourceEvent singletonRight binaryAnchor := by
      simp [candidate, sxSourceEvent, sourceBranchEvent, sourceCollectionEquivalent,
        singletonRight, binaryAnchor]
    exact hRight (hEvents ▸ hLeft)
  · intro hRealizes
    obtain ⟨candidate, hDiagonal, hPattern⟩ :=
      hRealizes (fun source => decide (source = 0))
    have hEqual : EqualityPattern binaryAnchor candidate 0 =
        EqualityPattern binaryAnchor candidate 1 := by
      change decide (false = candidate.1 0) = decide (false = candidate.1 1)
      rw [hDiagonal.1]
    rw [hPattern] at hEqual
    simp at hEqual

/-- Absorption preserves the Boolean function but removes a nonminimal branch. -/
theorem antichain_premise_is_load_bearing : antichain_premise_is_load_bearing_target := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · simp only [IsInclusionAntichain]
    decide +kernel
  · decide +kernel
  · simp only [RedundancyLE]
    decide +kernel
  · simp only [RedundancyLE]
    decide +kernel
  · intro pattern
    simp [DNF, absorbedFamily, singletonLeft]
    exact fun h _ => h

end PidSxDnfOrderCandidate
