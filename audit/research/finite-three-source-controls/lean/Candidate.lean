import Contract

namespace PidFin3Candidate
open PidFin3Contract

theorem codec_range : codecRangeTarget := by
  unfold codecRangeTarget
  decide

theorem decode_encode : decodeEncodeTarget := by
  unfold decodeEncodeTarget
  decide

theorem encode_decode : encodeDecodeTarget := by
  unfold encodeDecodeTarget
  decide

theorem codec_nonempty : codecNonemptyTarget := by
  unfold codecNonemptyTarget
  decide

theorem codec_subset : codecSubsetTarget := by
  unfold codecSubsetTarget
  decide

theorem codec_anchors : codecAnchorsTarget := by
  unfold codecAnchorsTarget
  repeat' apply And.intro
  all_goals decide

theorem carrier_membership : carrierMembershipTarget := by
  unfold carrierMembershipTarget
  intro A
  constructor
  · intro hA
    exact (Finset.mem_filter.mp hA).2
  · intro hA
    refine Finset.mem_filter.mpr ⟨?_, hA⟩
    apply Finset.mem_powerset.mpr
    intro a ha
    refine Finset.mem_filter.mpr ⟨?_, hA.2.1 a ha⟩
    exact Finset.mem_powerset.mpr (Finset.subset_univ a)

theorem carrier_cardinality : carrierCardinalityTarget := by
  unfold carrierCardinalityTarget
  decide

theorem registry_pointwise : registryPointwiseTarget := by
  unfold registryPointwiseTarget
  repeat' first
    | refine Fin.forall_fin_succ.mpr ?_
    | apply And.intro
    | exact Fin.forall_fin_zero.mpr True.intro
  all_goals decide

theorem registry_injective : registryInjectiveTarget := by
  unfold registryInjectiveTarget Function.Injective
  have hMasks : ∀ i j : Fin 18,
      (registryMasks i).toFinset = (registryMasks j).toFinset → i = j := by
    repeat' first
      | refine Fin.forall_fin_succ.mpr ?_
      | apply And.intro
      | exact Fin.forall_fin_zero.mpr True.intro
    all_goals decide
  intro i j h
  apply hMasks i j
  calc
    (registryMasks i).toFinset = (registry i).image encode :=
      (registry_pointwise i).symm
    _ = (registry j).image encode :=
      congrArg (fun A : Family => A.image encode) h
    _ = (registryMasks j).toFinset := registry_pointwise j

theorem registry_coverage : registryCoverageTarget := by
  unfold registryCoverageTarget
  have hValid : ∀ i : Fin 18, Valid (registry i) := by
    repeat' first
      | refine Fin.forall_fin_succ.mpr ?_
      | apply And.intro
      | exact Fin.forall_fin_zero.mpr True.intro
    all_goals decide
  have hSubset : ((Finset.univ : Finset (Fin 18)).image registry) ⊆ carrier := by
    intro A hA
    rcases Finset.mem_image.mp hA with ⟨i, _, rfl⟩
    exact (carrier_membership (registry i)).2 (hValid i)
  have hCard : ((Finset.univ : Finset (Fin 18)).image registry).card = 18 := by
    calc
      _ = (Finset.univ : Finset (Fin 18)).card :=
        Finset.card_image_of_injective _ registry_injective
      _ = 18 := by decide
  have hImage : ((Finset.univ : Finset (Fin 18)).image registry) = carrier :=
    Finset.eq_of_subset_of_card_le hSubset
      (le_of_eq (carrier_cardinality.trans hCard.symm))
  intro A
  constructor
  · intro hA
    have hMem : A ∈ carrier := (carrier_membership A).2 hA
    have hMemImage : A ∈ (Finset.univ : Finset (Fin 18)).image registry :=
      hImage.symm ▸ hMem
    rcases Finset.mem_image.mp hMemImage with ⟨i, _, hi⟩
    exact ⟨i, hi⟩
  · rintro ⟨i, hi⟩
    exact hi ▸ hValid i

theorem reflexivity : reflexivityTarget := by
  unfold reflexivityTarget PidFin3Contract.LE
  intro A b hb
  exact ⟨b, hb, fun _ hi => hi⟩

theorem transitivity : transitivityTarget := by
  unfold transitivityTarget PidFin3Contract.LE
  intro A B C hAB hBC c hc
  rcases hBC c hc with ⟨b, hb, hbc⟩
  rcases hAB b hb with ⟨a, ha, hab⟩
  exact ⟨a, ha, fun _ hi => hbc (hab hi)⟩

theorem antisymmetry : antisymmetryTarget := by
  unfold antisymmetryTarget PidFin3Contract.LE
  intro A B hA hB hAB hBA
  apply Finset.ext
  intro x
  constructor
  · intro hx
    rcases hBA x hx with ⟨b, hb, hbx⟩
    rcases hAB b hb with ⟨a, ha, hab⟩
    have hax : a ⊆ x := fun _ hi => hbx (hab hi)
    have hEqA : a = x := hA.2.2 a ha x hx hax
    have hxb : x ⊆ b := hEqA ▸ hab
    have hEq : x = b := Finset.Subset.antisymm hxb hbx
    exact hEq.symm ▸ hb
  · intro hx
    rcases hAB x hx with ⟨a, ha, hax⟩
    rcases hBA a ha with ⟨b, hb, hba⟩
    have hbx : b ⊆ x := fun _ hi => hax (hba hi)
    have hEqB : b = x := hB.2.2 b hb x hx hbx
    have hxa : x ⊆ a := hEqB ▸ hba
    have hEq : x = a := Finset.Subset.antisymm hxa hax
    exact hEq.symm ▸ ha

theorem reverse_dnf : reverseDnfTarget := by
  unfold reverseDnfTarget PidFin3Contract.LE DNF
  intro A B
  constructor
  · intro hAB pattern hB
    rcases hB with ⟨b, hb, hPattern⟩
    rcases hAB b hb with ⟨a, ha, hab⟩
    exact ⟨a, ha, fun i hi => hPattern i (hab hi)⟩
  · intro h b hb
    let pattern : Source → Bool := fun i => if i ∈ b then true else false
    have hB : DNF B pattern := by
      refine ⟨b, hb, ?_⟩
      intro i hi
      change (if i ∈ b then true else false) = true
      exact ite_eq_left hi
    rcases h pattern hB with ⟨a, ha, hPattern⟩
    refine ⟨a, ha, ?_⟩
    intro i hi
    by_cases hib : i ∈ b
    · exact hib
    · have hp : (if i ∈ b then true else false) = true := hPattern i hi
      have bad : (false : Bool) = true := (ite_eq_right hib).symm.trans hp
      cases bad

theorem row_shape : rowShapeTarget := by
  unfold rowShapeTarget
  repeat' first
    | refine Fin.forall_fin_succ.mpr ?_
    | apply And.intro
    | exact Fin.forall_fin_zero.mpr True.intro
  all_goals decide

theorem zeta_entries : zetaEntriesTarget := by
  unfold zetaEntriesTarget
  have hOrder : ∀ i j : Fin 18,
      LE (registry j) (registry i) ↔
        ∀ mb ∈ (registryMasks i).toFinset,
          ∃ ma ∈ (registryMasks j).toFinset, (ma &&& mb) = ma := by
    unfold PidFin3Contract.LE
    intro i j
    constructor
    · intro h mb hmb
      have hmbImage : mb ∈ (registry i).image encode :=
        (registry_pointwise i).symm ▸ hmb
      rcases Finset.mem_image.mp hmbImage with ⟨b, hb, hbm⟩
      rcases h b hb with ⟨a, ha, hab⟩
      refine ⟨encode a, ?_, ?_⟩
      · exact registry_pointwise j ▸ Finset.mem_image_of_mem encode ha
      · have hbit := (codec_subset a b).1 hab
        rw [hbm] at hbit
        exact hbit
    · intro h b hb
      have hbMask : encode b ∈ (registryMasks i).toFinset :=
        registry_pointwise i ▸ Finset.mem_image_of_mem encode hb
      rcases h (encode b) hbMask with ⟨ma, hma, hbit⟩
      have hmaImage : ma ∈ (registry j).image encode :=
        (registry_pointwise j).symm ▸ hma
      rcases Finset.mem_image.mp hmaImage with ⟨a, ha, ham⟩
      have hab : a ⊆ b := (codec_subset a b).2 (by simpa only [ham] using hbit)
      exact ⟨a, ha, hab⟩
  simp only [hOrder]
  repeat' first
    | refine Fin.forall_fin_succ.mpr ?_
    | apply And.intro
    | exact Fin.forall_fin_zero.mpr True.intro
  all_goals decide

theorem zeta_census : zetaCensusTarget := by
  unfold zetaCensusTarget
  let rowCount : Fin 18 → Nat := fun i =>
    ([5, 5, 13, 5, 13, 13, 18, 2, 2, 4, 2, 4, 4, 10, 10, 10, 1, 8] : List Nat)[i.val]!
  have hCounts : ∀ i : Fin 18,
      ((Finset.univ : Finset (Fin 18)).filter fun j => expectedZeta i j = true).card =
        rowCount i := by
    repeat' first
      | refine Fin.forall_fin_succ.mpr ?_
      | apply And.intro
      | exact Fin.forall_fin_zero.mpr True.intro
    all_goals decide
  have hSum : ((Finset.univ : Finset (Fin 18)).sum rowCount) = 129 := by
    decide
  simpa only [hCounts] using hSum

theorem extremes : extremesTarget := by
  unfold extremesTarget PidFin3Contract.LE
  repeat' first
    | refine Fin.forall_fin_succ.mpr ?_
    | apply And.intro
    | exact Fin.forall_fin_zero.mpr True.intro
  all_goals decide

end PidFin3Candidate
