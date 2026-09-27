# Expanded theorem statements

Author: Sepehr Mahmoudian. These are verbatim proposition declarations from the selected [RawTargets source](sources/PidStoppedPrefixStageA/RawTargets.lean). They are explanatory source excerpts, not newly emitted kernel output. Their imports, namespaces, native measures and local instances remain in that source. All three universes `u`, `v`, `w`, all finite/equality binders, `Nonempty I`, the complete `Law p` hypotheses for F1/F2 and both F4 conclusions are retained below.

The [raw exported-type records](evidence/EXPORTED_TYPES.json) preserve the actual abbreviated F1/F2 strings. The semantic judges compare complete types and raw/alias assignments; no expanded output was substituted for those records.

```lean
universe u v w
abbrev first_hit_factorization : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (A : Set (Key I X T)) (n : ℕ),
    Law p →
      @Measure.map _ _
        (inferInstance : MeasurableSpace (Fin (n + 1) → Key I X T))
        (@Prod.instMeasurableSpace (Fin n → Key I X T) (Key I X T)
          inferInstance inferInstance)
        (fun word : Fin (n + 1) → Key I X T =>
          ((fun i : Fin n => word i.castSucc), word (Fin.last n)))
        ((rowLaw p (n + 1)).restrict
          {word | (∀ i : Fin n, word i.castSucc ∉ A) ∧ word (Fin.last n) ∈ A}) =
        (rowLaw (fun x => @ite ℝ (x ∈ Aᶜ) (Classical.propDecidable (x ∈ Aᶜ)) (p x) 0) n).prod
          (keyMeasure (fun x => @ite ℝ (x ∈ A) (Classical.propDecidable (x ∈ A)) (p x) 0))

abbrev first_hit_mass : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (A : Set (Key I X T)) (n : ℕ),
    Law p →
      0 ≤ (∑ x, @ite ℝ (x ∈ A) (Classical.propDecidable (x ∈ A)) (p x) 0) ∧
      (∑ x, @ite ℝ (x ∈ A) (Classical.propDecidable (x ∈ A)) (p x) 0) ≤ 1 ∧
      rowLaw p (n + 1)
        {word | (∀ i : Fin n, word i.castSucc ∉ A) ∧ word (Fin.last n) ∈ A} =
        ENNReal.ofReal
          ((1 - (∑ x, @ite ℝ (x ∈ A) (Classical.propDecidable (x ∈ A)) (p x) 0)) ^ n *
            (∑ x, @ite ℝ (x ∈ A) (Classical.propDecidable (x ∈ A)) (p x) 0))

abbrev native_return_kills : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (z : Key I X T) (alpha : Node I) (rows : List (Key I X T)),
    z ∈ rows →
      positiveOnPrefix z alpha rows = 0 ∧ negativeOnPrefix z alpha rows = 0
```
