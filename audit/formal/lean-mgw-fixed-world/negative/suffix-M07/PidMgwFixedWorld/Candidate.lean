import PidMgwFixedWorld.RawTargets
import PidMgwFixedWorld.NegativeHelper

set_option autoImplicit false
set_option warningAsError true

namespace PidMgwFixedWorld.Candidate

theorem world_normalization : PidMgwFixedWorld.RawTargets.WorldNormalization := by
  classical
  norm_num [PidMgwFixedWorld.RawTargets.WorldNormalization, worldMass, World]

theorem world_marginals : PidMgwFixedWorld.RawTargets.WorldMarginals := by
  classical
  intro b
  fin_cases b <;>
    norm_num [worldAMass, worldBMass, worldUMass, worldMass, World,
      Fintype.sum_prod_type, Fin.sum_univ_two]

theorem world_factorization : PidMgwFixedWorld.RawTargets.WorldFactorization := by
  intro w
  rw [(world_marginals w.1).1, (world_marginals w.2.1).2.1,
    (world_marginals w.2.2).2.2]
  norm_num [worldMass]

theorem observation_identity : PidMgwFixedWorld.RawTargets.ObservationIdentity := by
  intro tag w
  simp [observe]

theorem count_table : PidMgwFixedWorld.RawTargets.CountTable := by
  classical
  intro tag z
  simp only [count, Fintype.sum_prod_type, Fin.sum_univ_two]
  rcases z with ⟨s, a, b⟩
  have bits (i : Fin 2) : i = 0 ∨ i = 1 := by
    fin_cases i <;> simp
  rcases bits (s 0) with h0 | h0 <;>
    rcases bits (s 1) with h1 | h1 <;>
      fin_cases a <;> fin_cases b <;> cases tag <;>
        norm_num [count, expectedCount, observe, addedValue, World,
          Fintype.sum_prod_type, Fin.sum_univ_two, funext_iff,
          Fin.forall_fin_two, h0, h1]

theorem totals : PidMgwFixedWorld.RawTargets.Totals := by
  classical
  intro tag
  change Finset.sum Finset.univ (fun z : Key => count tag z) = 8
  simp only [count]
  rw [Finset.sum_comm]
  simp [eq_comm, World]

theorem nonnegative : PidMgwFixedWorld.RawTargets.Nonnegative := by
  intro tag z
  exact PidFiniteConvergence.empirical_law_nonnegative (count tag) z

theorem normalization : PidMgwFixedWorld.RawTargets.Normalization := by
  intro tag
  apply PidFiniteConvergence.sum_empirical_law_eq_one (count tag)
  rw [totals tag]
  norm_num

theorem pushforward : PidMgwFixedWorld.RawTargets.Pushforward := by
  classical
  intro tag z
  unfold jointLaw PidFiniteConvergence.empiricalLaw
  rw [totals tag]
  simp only [count, pushedLaw, Nat.cast_sum, div_eq_mul_inv, Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro w _
  by_cases h : observe tag w = z
  · simp [h, worldMass]
  · simp [h]

theorem source_masses : PidMgwFixedWorld.RawTargets.SourceMasses := by
  classical
  intro tag z
  have h_event (event : Finset Key) :
      PidFiniteConvergence.eventCount (count tag) event =
        Finset.sum Finset.univ
          (fun w : World => if observe tag w ∈ event then 1 else 0) := by
    simp only [PidFiniteConvergence.eventCount, count]
    rw [Finset.sum_comm]
    apply Finset.sum_congr rfl
    intro w _
    simp [eq_comm]
  have hc :
      PidFiniteConvergence.eventCount (count tag) (PidFiniteConvergence.sxPid2SourceEvent .sourceOne z) = 4 ∧
      PidFiniteConvergence.eventCount (count tag) (PidFiniteConvergence.sxPid2SourceEvent .sourceTwo z) = 4 ∧
      PidFiniteConvergence.eventCount (count tag) (PidFiniteConvergence.sxPid2SourceEvent .jointSources z) = 2 := by
    simp only [h_event, World, Fintype.sum_prod_type, Fin.sum_univ_two]
    rcases z with ⟨s, _target⟩
    have bits (i : Fin 2) : i = 0 ∨ i = 1 := by
      fin_cases i <;> simp
    rcases bits (s 0) with h0 | h0 <;>
      rcases bits (s 1) with h1 | h1 <;> cases tag <;>
        norm_num [h_event, World, Fintype.sum_prod_type, Fin.sum_univ_two,
          observe, addedValue, PidFiniteConvergence.sxPid2SourceEvent,
          PidFiniteConvergence.sxPid2TargetRestrictedEvent, PidFiniteConvergence.sxPid2Collections,
          PidFiniteConvergence.sxSourceEvent, PidFiniteConvergence.sxTargetRestrictedEvent,
          PidFiniteConvergence.sourceBranchEvent, PidFiniteConvergence.sourceTargetBranchEvent,
          PidFiniteConvergence.targetBranchEvent, PidFiniteConvergence.sourceCollectionEquivalent,
          PidFiniteConvergence.sourceTargetCollectionEquivalent, PidFiniteConvergence.targetEquivalent,
          expectedSourceCount, expectedRestrictedCount, h0, h1]
  norm_num [jointLaw, PidFiniteConvergence.event_mass_empirical_law_eq_count_ratio,
    totals tag, hc.1, hc.2.1, hc.2.2]

theorem event_counts : PidMgwFixedWorld.RawTargets.EventCounts := by
  have event_count_worlds (tag : AddedSource) (event : Finset Key) :
      PidFiniteConvergence.eventCount (count tag) event =
        Finset.sum Finset.univ (fun w : World => if observe tag w ∈ event then 1 else 0) := by
    classical
    simp only [PidFiniteConvergence.eventCount, count]
    rw [Finset.sum_comm]
    apply Finset.sum_congr rfl
    intro w _
    simp [eq_comm]

  have target_count (tag : AddedSource) (z : Key) :
      PidFiniteConvergence.eventCount (count tag) (PidFiniteConvergence.targetBranchEvent z) = 2 := by
    classical
    have hm (w : World) :
        observe tag w ∈ PidFiniteConvergence.targetBranchEvent z ↔ z.2 = (w.1, w.2.1) := by
      exact (Finset.mem_filter.trans (and_iff_right (Finset.mem_univ (observe tag w))))
    rw [event_count_worlds]
    simp_rw [hm]
    simp only [Fintype.sum_prod_type, Fin.sum_univ_two]
    rcases z with ⟨s, a, b⟩
    fin_cases a <;> fin_cases b <;> norm_num

  have source_counts_all (tag : AddedSource) (z : Key) :
      ∀ node : PidFiniteConvergence.SxPid2Node,
        PidFiniteConvergence.eventCount (count tag)
          (PidFiniteConvergence.sxPid2SourceEvent node z) = expectedSourceCount node := by
    classical
    intro node
    simp only [event_count_worlds, Fintype.sum_prod_type, Fin.sum_univ_two]
    rcases z with ⟨s, target⟩
    have bits (i : Fin 2) : i = 0 ∨ i = 1 := by
      fin_cases i <;> simp
    rcases bits (s 0) with h0 | h0 <;>
      rcases bits (s 1) with h1 | h1 <;> cases tag <;> cases node <;>
        norm_num [observe, addedValue, PidFiniteConvergence.sxPid2SourceEvent,
            PidFiniteConvergence.sxPid2TargetRestrictedEvent, PidFiniteConvergence.sxPid2Collections,
            PidFiniteConvergence.sxSourceEvent, PidFiniteConvergence.sxTargetRestrictedEvent,
            PidFiniteConvergence.sourceBranchEvent, PidFiniteConvergence.sourceTargetBranchEvent,
            PidFiniteConvergence.sourceCollectionEquivalent,
            PidFiniteConvergence.sourceTargetCollectionEquivalent, PidFiniteConvergence.targetEquivalent,
            expectedSourceCount, expectedRestrictedCount, h0, h1]

  have restricted_counts_irrelevant (z : Key) (hz : 0 < count .irrelevant z) :
      ∀ node : PidFiniteConvergence.SxPid2Node,
        PidFiniteConvergence.eventCount (count .irrelevant)
          (PidFiniteConvergence.sxPid2TargetRestrictedEvent node z) = expectedRestrictedCount .irrelevant node := by
    classical
    intro node
    rw [count_table .irrelevant z] at hz
    simp only [event_count_worlds, Fintype.sum_prod_type, Fin.sum_univ_two]
    rcases z with ⟨s, a, b⟩
    have bits (i : Fin 2) : i = 0 ∨ i = 1 := by
      fin_cases i <;> simp
    rcases bits (s 0) with h0 | h0 <;>
      rcases bits (s 1) with h1 | h1 <;>
        fin_cases a <;> fin_cases b <;>
          norm_num [expectedCount, h0, h1] at hz
    all_goals cases node <;> norm_num [observe, addedValue, PidFiniteConvergence.sxPid2SourceEvent,
            PidFiniteConvergence.sxPid2TargetRestrictedEvent, PidFiniteConvergence.sxPid2Collections,
            PidFiniteConvergence.sxSourceEvent, PidFiniteConvergence.sxTargetRestrictedEvent,
            PidFiniteConvergence.sourceBranchEvent, PidFiniteConvergence.sourceTargetBranchEvent,
            PidFiniteConvergence.sourceCollectionEquivalent,
            PidFiniteConvergence.sourceTargetCollectionEquivalent, PidFiniteConvergence.targetEquivalent,
            expectedSourceCount, expectedRestrictedCount, h0, h1]

  have restricted_counts_completing (z : Key) (hz : 0 < count .completing z) :
      ∀ node : PidFiniteConvergence.SxPid2Node,
        PidFiniteConvergence.eventCount (count .completing)
          (PidFiniteConvergence.sxPid2TargetRestrictedEvent node z) = expectedRestrictedCount .completing node := by
    classical
    intro node
    rw [count_table .completing z] at hz
    simp only [event_count_worlds, Fintype.sum_prod_type, Fin.sum_univ_two]
    rcases z with ⟨s, a, b⟩
    have bits (i : Fin 2) : i = 0 ∨ i = 1 := by
      fin_cases i <;> simp
    rcases bits (s 0) with h0 | h0 <;>
      rcases bits (s 1) with h1 | h1 <;>
        fin_cases a <;> fin_cases b <;>
          norm_num [expectedCount, h0, h1] at hz
    all_goals cases node <;> norm_num [observe, addedValue, PidFiniteConvergence.sxPid2SourceEvent,
            PidFiniteConvergence.sxPid2TargetRestrictedEvent, PidFiniteConvergence.sxPid2Collections,
            PidFiniteConvergence.sxSourceEvent, PidFiniteConvergence.sxTargetRestrictedEvent,
            PidFiniteConvergence.sourceBranchEvent, PidFiniteConvergence.sourceTargetBranchEvent,
            PidFiniteConvergence.sourceCollectionEquivalent,
            PidFiniteConvergence.sourceTargetCollectionEquivalent, PidFiniteConvergence.targetEquivalent,
            expectedSourceCount, expectedRestrictedCount, h0, h1]

  intro tag z hz
  constructor
  · exact target_count tag z
  · intro node
    constructor
    · exact source_counts_all tag z node
    · cases tag with
      | irrelevant => exact restricted_counts_irrelevant z hz node
      | completing => exact restricted_counts_completing z hz node

theorem net_arguments : PidMgwFixedWorld.RawTargets.NetArguments := by
  intro tag z hz node
  obtain ⟨ht, hnodes⟩ := event_counts tag z hz
  obtain ⟨hs, hr⟩ := hnodes node
  unfold PidFiniteConvergence.countNetArgument
  rw [totals tag, ht, hs, hr]
  cases tag <;> cases node <;>
    norm_num [expectedSourceCount, expectedRestrictedCount, expectedNetArgument]

theorem irrelevant_averages : PidMgwFixedWorld.RawTargets.IrrelevantAverages := by
  classical
  intro node
  have htotal : 0 < PidFiniteConvergence.totalCount (count .irrelevant) := by
    rw [totals .irrelevant]
    norm_num
  have hlocal : ∀ z ∈ PidFiniteConvergence.positiveMassSupport (jointLaw .irrelevant),
      PidFiniteConvergence.localCumulativeComponent (jointLaw .irrelevant) .net node z =
        expectedAverage .irrelevant node := by
    intro z hz
    have hs : z ∈ PidFiniteConvergence.positiveSupport (count .irrelevant) := by
      simpa only [jointLaw,
        PidFiniteConvergence.positive_mass_support_empirical_law (count .irrelevant) htotal] using hz
    have hc : 0 < count .irrelevant z := (Finset.mem_filter.mp hs).2
    change PidFiniteConvergence.localCumulativeNet
      (PidFiniteConvergence.empiricalLaw (count .irrelevant)) node z =
        expectedAverage .irrelevant node
    rw [PidFiniteConvergence.local_cumulative_net_empirical_eq_log_count_net_argument
      (count .irrelevant) node htotal hs]
    rw [net_arguments .irrelevant z hc node]
    cases node <;> norm_num [expectedNetArgument, expectedAverage]
  have hsum :
      Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .irrelevant))
        (jointLaw .irrelevant) = 1 := by
    calc
      Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .irrelevant))
          (jointLaw .irrelevant) =
          Finset.sum Finset.univ (jointLaw .irrelevant) := by
        rw [PidFiniteConvergence.positiveMassSupport, Finset.sum_filter]
        apply Finset.sum_congr rfl
        intro z _
        by_cases hpos : 0 < jointLaw .irrelevant z
        · simp [hpos]
        · have hzero : jointLaw .irrelevant z = 0 :=
            le_antisymm (not_lt.mp hpos) (nonnegative .irrelevant z)
          simp [hzero]
      _ = 1 := normalization .irrelevant
  change Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .irrelevant))
      (fun z => jointLaw .irrelevant z *
        PidFiniteConvergence.localCumulativeComponent (jointLaw .irrelevant) .net node z) =
      expectedAverage .irrelevant node
  calc
    _ = Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .irrelevant))
        (fun z => jointLaw .irrelevant z * expectedAverage .irrelevant node) := by
      apply Finset.sum_congr rfl
      intro z hz
      rw [hlocal z hz]
    _ = expectedAverage .irrelevant node := by
      rw [← Finset.sum_mul, hsum, one_mul]

theorem completing_averages : PidMgwFixedWorld.RawTargets.CompletingAverages := by
  classical
  intro node
  have htotal : 0 < PidFiniteConvergence.totalCount (count .completing) := by
    rw [totals .completing]
    norm_num
  have hlocal : ∀ z ∈ PidFiniteConvergence.positiveMassSupport (jointLaw .completing),
      PidFiniteConvergence.localCumulativeComponent (jointLaw .completing) .net node z =
        expectedAverage .completing node := by
    intro z hz
    have hs : z ∈ PidFiniteConvergence.positiveSupport (count .completing) := by
      simpa only [jointLaw,
        PidFiniteConvergence.positive_mass_support_empirical_law (count .completing) htotal] using hz
    have hc : 0 < count .completing z := (Finset.mem_filter.mp hs).2
    change PidFiniteConvergence.localCumulativeNet
      (PidFiniteConvergence.empiricalLaw (count .completing)) node z =
        expectedAverage .completing node
    rw [PidFiniteConvergence.local_cumulative_net_empirical_eq_log_count_net_argument
      (count .completing) node htotal hs]
    rw [net_arguments .completing z hc node]
    cases node <;> norm_num [expectedNetArgument, expectedAverage]
  have hsum :
      Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .completing))
        (jointLaw .completing) = 1 := by
    calc
      Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .completing))
          (jointLaw .completing) =
          Finset.sum Finset.univ (jointLaw .completing) := by
        rw [PidFiniteConvergence.positiveMassSupport, Finset.sum_filter]
        apply Finset.sum_congr rfl
        intro z _
        by_cases hpos : 0 < jointLaw .completing z
        · simp [hpos]
        · have hzero : jointLaw .completing z = 0 :=
            le_antisymm (not_lt.mp hpos) (nonnegative .completing z)
          simp [hzero]
      _ = 1 := normalization .completing
  change Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .completing))
      (fun z => jointLaw .completing z *
        PidFiniteConvergence.localCumulativeComponent (jointLaw .completing) .net node z) =
      expectedAverage .completing node
  calc
    _ = Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .completing))
        (fun z => jointLaw .completing z * expectedAverage .completing node) := by
      apply Finset.sum_congr rfl
      intro z hz
      rw [hlocal z hz]
    _ = expectedAverage .completing node := by
      rw [← Finset.sum_mul, hsum, one_mul]

theorem irrelevant_synergy : PidMgwFixedWorld.RawTargets.IrrelevantSynergy := by
  change synergy .irrelevant = Real.log (4 / 3)
  unfold synergy
  rw [PidFiniteConvergence.averaged_pointwise_atom_eq_mobius_of_averaged_cumulatives]
  simp only [PidFiniteConvergence.averagedAtomComponent, PidFiniteConvergence.sxPid2MobiusTransform]
  rw [irrelevant_averages .jointSources, irrelevant_averages .sourceOne,
    irrelevant_averages .sourceTwo, irrelevant_averages .redundancy]
  simp [expectedAverage]

theorem completing_synergy : PidMgwFixedWorld.RawTargets.CompletingSynergy := by
  change synergy .completing = Real.log (4 / 3)
  have hlog4 : Real.log (4 : ℝ) = Real.log 2 + Real.log 2 := by
    simpa only [show (2 : ℝ) * 2 = 4 by norm_num] using Real.log_mul (by norm_num : (2 : ℝ) ≠ 0)
      (by norm_num : (2 : ℝ) ≠ 0)
  unfold synergy
  rw [PidFiniteConvergence.averaged_pointwise_atom_eq_mobius_of_averaged_cumulatives]
  simp only [PidFiniteConvergence.averagedAtomComponent, PidFiniteConvergence.sxPid2MobiusTransform]
  rw [completing_averages .jointSources, completing_averages .sourceOne,
    completing_averages .sourceTwo, completing_averages .redundancy]
  simp only [expectedAverage]
  rw [hlog4]
  ring

theorem conditional_ratio : PidMgwFixedWorld.RawTargets.ConditionalRatio := by
  classical
  intro tag z hz
  have hs := source_masses tag z
  have hr :
      PidFiniteConvergence.finiteEventMass (jointLaw tag)
        (PidFiniteConvergence.sxPid2TargetRestrictedEvent .sourceOne z) = (1 / 4 : ℝ) := by
    rw [jointLaw, PidFiniteConvergence.event_mass_empirical_law_eq_count_ratio,
      ((event_counts tag z hz).2 .sourceOne).2, totals tag]
    cases tag <;> norm_num [expectedRestrictedCount]
  have hp : jointLaw tag z =
      (match tag with | .irrelevant => (1 / 8 : ℝ) | .completing => (1 / 4 : ℝ)) := by
    cases tag with
    | irrelevant =>
        have he : z.2.1 = z.1 0 := by
          by_contra hne
          rw [count_table .irrelevant z] at hz
          simp [expectedCount, hne] at hz
        norm_num [jointLaw, PidFiniteConvergence.empiricalLaw, totals .irrelevant,
          count_table .irrelevant z, expectedCount, he]
    | completing =>
        have he : z.2 = (z.1 0, z.1 1) := by
          by_contra hne
          rw [count_table .completing z] at hz
          simp [expectedCount, hne] at hz
        norm_num [jointLaw, PidFiniteConvergence.empiricalLaw, totals .completing,
          count_table .completing z, expectedCount, he]
  constructor
  · rw [hs.1]
    norm_num
  · constructor
    · rw [hs.2.2]
      norm_num
    · constructor
      · rw [hr]
        norm_num
      · simp only [conditionalRatio, hs.1, hs.2.2, hr, hp]
        cases tag <;> norm_num

theorem irrelevant_cmi : PidMgwFixedWorld.RawTargets.IrrelevantCmi := by
  classical
  have htotal : 0 < PidFiniteConvergence.totalCount (count .irrelevant) := by
    rw [totals .irrelevant]
    norm_num
  change Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .irrelevant))
      (fun z => jointLaw .irrelevant z * Real.log (conditionalRatio .irrelevant z)) = 0
  apply Finset.sum_eq_zero
  intro z hz
  have hs : z ∈ PidFiniteConvergence.positiveSupport (count .irrelevant) := by
    simpa only [jointLaw,
      PidFiniteConvergence.positive_mass_support_empirical_law (count .irrelevant) htotal] using hz
  have hc : 0 < count .irrelevant z := (Finset.mem_filter.mp hs).2
  rw [(conditional_ratio .irrelevant z hc).2.2.2]
  simp

theorem completing_cmi : PidMgwFixedWorld.RawTargets.CompletingCmi := by
  classical
  have htotal : 0 < PidFiniteConvergence.totalCount (count .completing) := by
    rw [totals .completing]
    norm_num
  have hsum :
      Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .completing))
        (jointLaw .completing) = 1 := by
    calc
      Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .completing))
          (jointLaw .completing) =
          Finset.sum Finset.univ (jointLaw .completing) := by
        rw [PidFiniteConvergence.positiveMassSupport, Finset.sum_filter]
        apply Finset.sum_congr rfl
        intro z _
        by_cases hpos : 0 < jointLaw .completing z
        · simp [hpos]
        · have hzero : jointLaw .completing z = 0 :=
            le_antisymm (not_lt.mp hpos) (nonnegative .completing z)
          simp [hzero]
      _ = 1 := normalization .completing
  change Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .completing))
      (fun z => jointLaw .completing z * Real.log (conditionalRatio .completing z)) =
      Real.log 2
  calc
    _ = Finset.sum (PidFiniteConvergence.positiveMassSupport (jointLaw .completing))
        (fun z => jointLaw .completing z * Real.log 2) := by
      apply Finset.sum_congr rfl
      intro z hz
      have hs : z ∈ PidFiniteConvergence.positiveSupport (count .completing) := by
        simpa only [jointLaw,
          PidFiniteConvergence.positive_mass_support_empirical_law (count .completing) htotal] using hz
      have hc : 0 < count .completing z := (Finset.mem_filter.mp hs).2
      rw [(conditional_ratio .completing z hc).2.2.2]
    _ = Real.log 2 := by
      rw [← Finset.sum_mul, hsum, one_mul]

theorem synergy_equal : PidMgwFixedWorld.RawTargets.SynergyEqual := by
  exact irrelevant_synergy.trans completing_synergy.symm

theorem cmi_different : PidMgwFixedWorld.RawTargets.CmiDifferent := PidMgwFixedWorld.NegativeHelper.imported_cmi

end PidMgwFixedWorld.Candidate
