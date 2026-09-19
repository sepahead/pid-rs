import PidPrefixMgwGradient.Contract

/-!
Reviewer-owned closed proposition views for the eleven-family scalar/local contract.
Each quantifier and conclusion is reconstructed here, without any contract target alias.
The local tangent, native atom/block means, inverse rows and score products are exposed.
Retained native definitions and the new finite latent laws/maps have exact source pins.
This source supplies no candidate proof and has not been elaborated or accepted.
-/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal Topology
open MeasureTheory
open PidMgwBridgeContract PidPrefixProbabilityContract PidPrefixMgwBiasSource
universe u v w x

namespace PidPrefixMgwGradientRawTargets

local instance keySpace {I : Type u} {X : I → Type v} {T : Type w} :
    MeasurableSpace (Key I X T) := ⊤
noncomputable local instance propositionDecidable (P : Prop) : Decidable P :=
  Classical.propDecidable P
noncomputable local instance nodesFinite {I : Type u} [Fintype I] :
    Fintype (Node I) := nodeFintype I

def full_inverse_row : Prop :=
  ∀ (I : Type u) [Fintype I] [Nonempty I] [DecidableEq I] (alpha : Node I),
    ∃! c : Node I → ℝ,
      (∀ beta, ¬ rawLE beta.val alpha.val → c beta = 0) ∧
      ∀ f : Node I → ℝ, (∑ beta, c beta * cumulative f beta) = f alpha

def scalar_remainder_calculus : Prop :=
  (∀ (q : ℝ), 0 < q → ∀ h : ℕ,
    HasDerivAt (fun r : ℝ => logRemainder r h) (-((1 - q) ^ h) / q) q) ∧
  (∀ (q a : ℝ), 0 < q → q ≤ a → a ≤ 1 → ∀ h : ℕ,
    0 ≤ logRemainder q h - logRemainder a h ∧
    logRemainder q h - logRemainder a h ≤
      (1 / q - 1 / a) / ((h : ℝ) + 1)) ∧
  (∀ (q : ℝ), 0 ≤ q → q ≤ 1 → ∀ h : ℕ,
    ((h : ℝ) + 1) * q * (1 - q) ^ h ≤ 1)

def native_cumulative_increments : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (n : ℕ),
    ((∀ a, 0 ≤ p a) ∧ (∑ a, p a) = 1) → 0 < p z →
      cumulative (fun beta =>
        ∫ rows, positiveOnPrefix z beta (List.ofFn rows) ∂rowLaw p (n + 1)) alpha =
          (1 - sourceMass p z alpha) ^ (n + 1) / ((n : ℝ) + 1) ∧
      cumulative (fun beta =>
        ∫ rows, negativeOnPrefix z beta (List.ofFn rows) ∂rowLaw p (n + 1)) alpha =
          ((1 - restrictedMass p z alpha) ^ (n + 1) -
            (1 - targetMass p z) ^ (n + 1)) / ((n : ℝ) + 1)

def actual_atom_remainder : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (plus minus : Key I X T → Node I → ℝ)
      (alpha : Node I) (h : ℕ),
    ((∀ z, 0 ≤ p z) ∧ (∑ z, p z) = 1) →
    ((∀ z, p z = 0 → plus z = 0 ∧ minus z = 0) ∧
      (∀ z, 0 < p z →
        (∀ beta, cumulative (plus z) beta = -Real.log (sourceMass p z beta)) ∧
        (∀ beta, cumulative (minus z) beta =
          Real.log (targetMass p z / restrictedMass p z beta)) ∧
        (∀ other : Node I → ℝ,
          (∀ beta, cumulative other beta = -Real.log (sourceMass p z beta)) →
            other = plus z) ∧
        (∀ other : Node I → ℝ,
          (∀ beta, cumulative other beta =
            Real.log (targetMass p z / restrictedMass p z beta)) → other = minus z))) →
      cumulative (fun beta =>
        (∑ z, p z * (plus z beta - minus z beta)) -
          (∫ block, blockStatistic beta h block ∂rowLaw p (h + 1))) alpha =
        supportedAverage p (fun z =>
          logRemainder (sourceMass p z alpha) h -
            logRemainder (restrictedMass p z alpha) h + logRemainder (targetMass p z) h) ∧
      ∀ c : Node I → ℝ,
        ((∀ beta, ¬ rawLE beta.val alpha.val → c beta = 0) ∧
          ∀ f : Node I → ℝ, (∑ beta, c beta * cumulative f beta) = f alpha) →
        (∑ z, p z * (plus z alpha - minus z alpha)) -
          (∫ block, blockStatistic alpha h block ∂rowLaw p (h + 1)) =
        cumulative (fun beta => c beta * supportedAverage p (fun z =>
          logRemainder (sourceMass p z beta) h -
            logRemainder (restrictedMass p z beta) h + logRemainder (targetMass p z) h)) alpha

def finite_block_score_derivative : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : ℝ → Key I X T → ℝ) (dp : Key I X T → ℝ) (t0 L : ℝ)
      (alpha : Node I) (h : ℕ),
    (0 ≤ L ∧
      (∃ U : Set ℝ, IsOpen U ∧ t0 ∈ U ∧
        ∀ t ∈ U, ((∀ z, 0 ≤ p t z) ∧ (∑ z, p t z) = 1) ∧
          ∀ z, (0 < p t z ↔ 0 < p t0 z)) ∧
      (∀ z, HasDerivAt (fun t => p t z) (dp z) t0) ∧
      ∀ z, |dp z| ≤ L * p t0 z) →
      (∑ z, dp z) = 0 ∧
      (∫ z, (if 0 < p t0 z then dp z / p t0 z else 0) ∂keyMeasure (p t0)) = 0 ∧
      HasDerivAt
        (fun t => ∫ block, blockStatistic alpha h block ∂rowLaw (p t) (h + 1))
        (∫ block,
          blockStatistic alpha h block *
            (∑ r : Fin (h + 1),
              if 0 < p t0 (block r) then dp (block r) / p t0 (block r) else 0)
          ∂rowLaw (p t0) (h + 1)) t0

def actual_atom_score_bias : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : ℝ → Key I X T → ℝ) (dp : Key I X T → ℝ) (t0 L : ℝ)
      (plus minus : ℝ → Key I X T → Node I → ℝ)
      (alpha : Node I) (c : Node I → ℝ) (h : ℕ),
    (0 ≤ L ∧
      (∃ U : Set ℝ, IsOpen U ∧ t0 ∈ U ∧
        ∀ t ∈ U, ((∀ z, 0 ≤ p t z) ∧ (∑ z, p t z) = 1) ∧
          ∀ z, (0 < p t z ↔ 0 < p t0 z)) ∧
      (∀ z, HasDerivAt (fun t => p t z) (dp z) t0) ∧
      ∀ z, |dp z| ≤ L * p t0 z) →
    (∀ y : T, (∑ z : Key I X T, @ite ℝ (z.2 = y) (Classical.propDecidable (z.2 = y)) (dp z) 0) = 0) →
    (∀ᶠ t in 𝓝 t0,
      (∀ z, p t z = 0 → plus t z = 0 ∧ minus t z = 0) ∧
      (∀ z, 0 < p t z →
        (∀ beta, cumulative (plus t z) beta = -Real.log (sourceMass (p t) z beta)) ∧
        (∀ beta, cumulative (minus t z) beta =
          Real.log (targetMass (p t) z / restrictedMass (p t) z beta)) ∧
        (∀ other : Node I → ℝ,
          (∀ beta, cumulative other beta = -Real.log (sourceMass (p t) z beta)) →
            other = plus t z) ∧
        (∀ other : Node I → ℝ,
          (∀ beta, cumulative other beta =
            Real.log (targetMass (p t) z / restrictedMass (p t) z beta)) →
              other = minus t z))) →
    ((∀ beta, ¬ rawLE beta.val alpha.val → c beta = 0) ∧
      ∀ f : Node I → ℝ, (∑ beta, c beta * cumulative f beta) = f alpha) →
      ∃ dAtom : ℝ,
        HasDerivAt (fun t => ∑ z, p t z * (plus t z alpha - minus t z alpha)) dAtom t0 ∧
        HasDerivAt
          (fun t => ∫ block, blockStatistic alpha h block ∂rowLaw (p t) (h + 1))
          (∫ block,
            blockStatistic alpha h block *
              (∑ r : Fin (h + 1),
                if 0 < p t0 (block r) then dp (block r) / p t0 (block r) else 0)
            ∂rowLaw (p t0) (h + 1)) t0 ∧
        |dAtom - (∫ block,
          blockStatistic alpha h block *
            (∑ r : Fin (h + 1),
              if 0 < p t0 (block r) then dp (block r) / p t0 (block r) else 0)
          ∂rowLaw (p t0) (h + 1))| ≤
          (2 * L / ((h : ℝ) + 1)) * (∑ beta, |c beta| * queryMoment (p t0) beta)

def finite_latent_pushforward : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w) (W : Type x)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T] [Fintype W]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T] [DecidableEq W]
      (rho : ℝ → W → ℝ) (drho : W → ℝ) (t0 L : ℝ) (phi : W → Key I X T),
    letI : MeasurableSpace W := ⊤;
    (0 ≤ L ∧
      (∃ U : Set ℝ, IsOpen U ∧ t0 ∈ U ∧
        ∀ t ∈ U, ((∀ z, 0 ≤ rho t z) ∧ (∑ z, rho t z) = 1) ∧
          ∀ z, (0 < rho t z ↔ 0 < rho t0 z)) ∧
      (∀ z, HasDerivAt (fun t => rho t z) (drho z) t0) ∧
      ∀ z, |drho z| ≤ L * rho t0 z) →
      (0 ≤ L ∧
        (∃ U : Set ℝ, IsOpen U ∧ t0 ∈ U ∧
          ∀ t ∈ U,
            ((∀ z, 0 ≤ PidPrefixMgwGradientContract.inducedMass phi (rho t) z) ∧
              (∑ z, PidPrefixMgwGradientContract.inducedMass phi (rho t) z) = 1) ∧
            ∀ z,
              (0 < PidPrefixMgwGradientContract.inducedMass phi (rho t) z ↔
                0 < PidPrefixMgwGradientContract.inducedMass phi (rho t0) z)) ∧
        (∀ z,
          HasDerivAt (fun t => PidPrefixMgwGradientContract.inducedMass phi (rho t) z)
            (PidPrefixMgwGradientContract.inducedMass phi drho z) t0) ∧
        ∀ z, |PidPrefixMgwGradientContract.inducedMass phi drho z| ≤
          L * PidPrefixMgwGradientContract.inducedMass phi (rho t0) z) ∧
      (PidPrefixMgwGradientContract.latentMeasure (rho t0)).map phi =
        keyMeasure (PidPrefixMgwGradientContract.inducedMass phi (rho t0)) ∧
      (∀ count : ℕ,
        (PidPrefixMgwGradientContract.latentRowLaw (rho t0) count).map
          (fun rows : Fin count → W => fun r => phi (rows r)) =
            rowLaw (PidPrefixMgwGradientContract.inducedMass phi (rho t0)) count) ∧
      ∀ z : Key I X T, 0 < PidPrefixMgwGradientContract.inducedMass phi (rho t0) z →
        (if 0 < PidPrefixMgwGradientContract.inducedMass phi (rho t0) z then
          PidPrefixMgwGradientContract.inducedMass phi drho z /
            PidPrefixMgwGradientContract.inducedMass phi (rho t0) z else 0) =
          (∑ w, if phi w = z then
            rho t0 w * (if 0 < rho t0 w then drho w / rho t0 w else 0) else 0) /
              PidPrefixMgwGradientContract.inducedMass phi (rho t0) z

def finite_latent_score_derivative : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w) (W : Type x)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T] [Fintype W]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T] [DecidableEq W]
      (rho : ℝ → W → ℝ) (drho : W → ℝ) (t0 L : ℝ) (phi : W → Key I X T)
      (alpha : Node I) (h : ℕ),
    letI : MeasurableSpace W := ⊤;
    (0 ≤ L ∧
      (∃ U : Set ℝ, IsOpen U ∧ t0 ∈ U ∧
        ∀ t ∈ U, ((∀ z, 0 ≤ rho t z) ∧ (∑ z, rho t z) = 1) ∧
          ∀ z, (0 < rho t z ↔ 0 < rho t0 z)) ∧
      (∀ z, HasDerivAt (fun t => rho t z) (drho z) t0) ∧
      ∀ z, |drho z| ≤ L * rho t0 z) →
      Integrable (fun rows : Fin (h + 1) → W =>
        blockStatistic alpha h (fun r => phi (rows r)) *
          (∑ r : Fin (h + 1),
            if 0 < rho t0 (rows r) then drho (rows r) / rho t0 (rows r) else 0))
        (PidPrefixMgwGradientContract.latentRowLaw (rho t0) (h + 1)) ∧
      (∫ rows,
        blockStatistic alpha h (fun r => phi (rows r)) *
          (∑ r : Fin (h + 1),
            if 0 < rho t0 (rows r) then drho (rows r) / rho t0 (rows r) else 0)
        ∂PidPrefixMgwGradientContract.latentRowLaw (rho t0) (h + 1)) =
      (∫ block,
        blockStatistic alpha h block *
          (∑ r : Fin (h + 1),
            if 0 < PidPrefixMgwGradientContract.inducedMass phi (rho t0) (block r) then
              PidPrefixMgwGradientContract.inducedMass phi drho (block r) /
                PidPrefixMgwGradientContract.inducedMass phi (rho t0) (block r) else 0)
        ∂rowLaw (PidPrefixMgwGradientContract.inducedMass phi (rho t0)) (h + 1)) ∧
      HasDerivAt
        (fun t => ∫ block, blockStatistic alpha h block
          ∂rowLaw (PidPrefixMgwGradientContract.inducedMass phi (rho t)) (h + 1))
        (∫ rows,
          blockStatistic alpha h (fun r => phi (rows r)) *
            (∑ r : Fin (h + 1),
              if 0 < rho t0 (rows r) then drho (rows r) / rho t0 (rows r) else 0)
          ∂PidPrefixMgwGradientContract.latentRowLaw (rho t0) (h + 1)) t0

def finite_encoder_score : Prop :=
  ∀ (B : Type u) (D : Type v) (C : Type w)
      [Fintype B] [Fintype D] [Fintype C]
      (base : B → ℝ) (input : B → D)
      (q : ℝ → D → C → ℝ) (dq : D → C → ℝ) (t0 L : ℝ),
    ((∀ z, 0 ≤ base z) ∧ (∑ z, base z) = 1) →
    (∀ d,
      0 ≤ L ∧
      (∃ U : Set ℝ, IsOpen U ∧ t0 ∈ U ∧
        ∀ t ∈ U, ((∀ z, 0 ≤ q t d z) ∧ (∑ z, q t d z) = 1) ∧
          ∀ z, (0 < q t d z ↔ 0 < q t0 d z)) ∧
      (∀ z, HasDerivAt (fun t => q t d z) (dq d z) t0) ∧
      ∀ z, |dq d z| ≤ L * q t0 d z) →
      (0 ≤ L ∧
        (∃ U : Set ℝ, IsOpen U ∧ t0 ∈ U ∧
          ∀ t ∈ U,
            ((∀ z : B × C, 0 ≤ base z.1 * q t (input z.1) z.2) ∧
              (∑ z : B × C, base z.1 * q t (input z.1) z.2) = 1) ∧
            ∀ z : B × C,
              (0 < base z.1 * q t (input z.1) z.2 ↔
                0 < base z.1 * q t0 (input z.1) z.2)) ∧
        (∀ z : B × C,
          HasDerivAt (fun t => base z.1 * q t (input z.1) z.2)
            (base z.1 * dq (input z.1) z.2) t0) ∧
        ∀ z : B × C,
          |base z.1 * dq (input z.1) z.2| ≤ L * (base z.1 * q t0 (input z.1) z.2)) ∧
      ∀ z : B × C, 0 < base z.1 * q t0 (input z.1) z.2 →
        (if 0 < base z.1 * q t0 (input z.1) z.2 then
          (base z.1 * dq (input z.1) z.2) / (base z.1 * q t0 (input z.1) z.2) else 0) =
          dq (input z.1) z.2 / q t0 (input z.1) z.2

def score_second_moment : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : ℝ → Key I X T → ℝ) (dp : Key I X T → ℝ) (t0 L : ℝ)
      (alpha : Node I) (h : ℕ),
    (0 ≤ L ∧
      (∃ U : Set ℝ, IsOpen U ∧ t0 ∈ U ∧
        ∀ t ∈ U, ((∀ z, 0 ≤ p t z) ∧ (∑ z, p t z) = 1) ∧
          ∀ z, (0 < p t z ↔ 0 < p t0 z)) ∧
      (∀ z, HasDerivAt (fun t => p t z) (dp z) t0) ∧
      ∀ z, |dp z| ≤ L * p t0 z) →
      Integrable (fun block : Fin (h + 1) → Key I X T =>
        (blockStatistic alpha h block *
          (∑ r : Fin (h + 1),
            if 0 < p t0 (block r) then dp (block r) / p t0 (block r) else 0)) ^ 2)
        (rowLaw (p t0) (h + 1)) ∧
      Integrable (fun z => (if 0 < p t0 z then dp z / p t0 z else 0) ^ 2)
        (keyMeasure (p t0)) ∧
      (∫ block,
        (blockStatistic alpha h block *
          (∑ r : Fin (h + 1),
            if 0 < p t0 (block r) then dp (block r) / p t0 (block r) else 0)) ^ 2
        ∂rowLaw (p t0) (h + 1)) ≤
          ((h : ℝ) + 1) * (harmonic h) ^ 2 *
            (∫ z, (if 0 < p t0 z then dp z / p t0 z else 0) ^ 2 ∂keyMeasure (p t0)) ∧
      (∫ z, (if 0 < p t0 z then dp z / p t0 z else 0) ^ 2 ∂keyMeasure (p t0)) ≤ L ^ 2

def latent_score_second_moment : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w) (W : Type x)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T] [Fintype W]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T] [DecidableEq W]
      (rho : ℝ → W → ℝ) (drho : W → ℝ) (t0 L : ℝ) (phi : W → Key I X T)
      (alpha : Node I) (h : ℕ),
    letI : MeasurableSpace W := ⊤;
    (0 ≤ L ∧
      (∃ U : Set ℝ, IsOpen U ∧ t0 ∈ U ∧
        ∀ t ∈ U, ((∀ z, 0 ≤ rho t z) ∧ (∑ z, rho t z) = 1) ∧
          ∀ z, (0 < rho t z ↔ 0 < rho t0 z)) ∧
      (∀ z, HasDerivAt (fun t => rho t z) (drho z) t0) ∧
      ∀ z, |drho z| ≤ L * rho t0 z) →
      Integrable (fun rows : Fin (h + 1) → W =>
        (blockStatistic alpha h (fun r => phi (rows r)) *
          (∑ r : Fin (h + 1),
            if 0 < rho t0 (rows r) then drho (rows r) / rho t0 (rows r) else 0)) ^ 2)
        (PidPrefixMgwGradientContract.latentRowLaw (rho t0) (h + 1)) ∧
      Integrable (fun z => (if 0 < rho t0 z then drho z / rho t0 z else 0) ^ 2)
        (PidPrefixMgwGradientContract.latentMeasure (rho t0)) ∧
      (∫ rows,
        (blockStatistic alpha h (fun r => phi (rows r)) *
          (∑ r : Fin (h + 1),
            if 0 < rho t0 (rows r) then drho (rows r) / rho t0 (rows r) else 0)) ^ 2
        ∂PidPrefixMgwGradientContract.latentRowLaw (rho t0) (h + 1)) ≤
          ((h : ℝ) + 1) * (harmonic h) ^ 2 *
            (∫ z, (if 0 < rho t0 z then drho z / rho t0 z else 0) ^ 2
              ∂PidPrefixMgwGradientContract.latentMeasure (rho t0)) ∧
      (∫ z, (if 0 < rho t0 z then drho z / rho t0 z else 0) ^ 2
        ∂PidPrefixMgwGradientContract.latentMeasure (rho t0)) ≤ L ^ 2

end PidPrefixMgwGradientRawTargets
