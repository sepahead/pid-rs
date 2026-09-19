import PidPrefixMgwBias.Candidate

/-!
POST-SHARING, UNELABORATED SOURCE PROPOSAL. Definitions and complete Prop targets only.
No new proof term, proof candidate, execution or acceptance is supplied by this file.
The direct import is reconstructed from the exact accepted public thirty-module bias graph.
Existing private helpers are not an interface: the targets below require their own proofs.
Units are nats per declared scalar parameter direction. All alphabets and maps are fixed.
-/
set_option autoImplicit false
set_option warningAsError true
open scoped BigOperators ENNReal Topology
open MeasureTheory
open PidMgwBridgeContract
open PidPrefixProbabilityContract
open PidPrefixMgwBiasSource
universe u v w x

namespace PidPrefixMgwGradientContract

noncomputable local instance propositionDecidable (P : Prop) : Decidable P :=
  Classical.propDecidable P

local instance keySpace {I : Type u} {X : I → Type v} {T : Type w} :
    MeasurableSpace (Key I X T) := ⊤

/-- Common positive support and normalized laws on an actual open neighborhood;
coordinate derivatives and relative-score control are only required at t0. -/
def LocalLawTangent {K : Type u} [Fintype K]
    (p : ℝ → K → ℝ) (dp : K → ℝ) (t0 L : ℝ) : Prop :=
  0 ≤ L ∧
  (∃ U : Set ℝ, IsOpen U ∧ t0 ∈ U ∧
    ∀ t ∈ U, Law (p t) ∧ ∀ z, (0 < p t z ↔ 0 < p t0 z)) ∧
  (∀ z, HasDerivAt (fun t => p t z) (dp z) t0) ∧
  ∀ z, |dp z| ≤ L * p t0 z

/-- A defined likelihood score. Off-support values are zero only for totality. -/
noncomputable def score {K : Type u} (p dp : K → ℝ) (z : K) : ℝ :=
  if 0 < p z then dp z / p z else 0

section Nodes
variable {I : Type u} [Fintype I] [DecidableEq I]
noncomputable local instance rowNodesFinite : Fintype (Node I) := nodeFintype I

/-- The whole inverse row, with no truncated lattice or cumulative substituted for an atom. -/
noncomputable def FullInverseRow (alpha : Node I) (c : Node I → ℝ) : Prop :=
  (∀ beta, ¬ rawLE beta.val alpha.val → c beta = 0) ∧
  ∀ f : Node I → ℝ, (∑ beta, c beta * cumulative f beta) = f alpha

noncomputable def rowL1 (c : Node I → ℝ) : ℝ := ∑ beta, |c beta|

end Nodes

/-- Existence and uniqueness must be proved for the native full redundancy order. -/
abbrev full_inverse_row_target : Prop :=
  ∀ (I : Type u) [Fintype I] [Nonempty I] [DecidableEq I] (alpha : Node I),
    ∃! c : Node I → ℝ, FullInverseRow alpha c

/-- Reconstruct the private scalar argument as a new checked obligation. -/
abbrev scalar_remainder_calculus_target : Prop :=
  (∀ (q : ℝ), 0 < q → ∀ h : ℕ,
    HasDerivAt (fun r : ℝ => logRemainder r h) (-((1 - q) ^ h) / q) q) ∧
  (∀ (q a : ℝ), 0 < q → q ≤ a → a ≤ 1 → ∀ h : ℕ,
    0 ≤ logRemainder q h - logRemainder a h ∧
    logRemainder q h - logRemainder a h ≤
      (1 / q - 1 / a) / ((h : ℝ) + 1)) ∧
  (∀ (q : ℝ), 0 ≤ q → q ≤ 1 → ∀ h : ℕ,
    ((h : ℝ) + 1) * q * (1 - q) ^ h ≤ 1)

section Categorical
variable {I : Type u} {X : I → Type v} {T : Type w}
variable [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
variable [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]

noncomputable local instance categoricalNodesFinite : Fintype (Node I) := nodeFintype I

noncomputable def TargetTangentZero (dp : Key I X T → ℝ) : Prop :=
  ∀ y : T, fiberMass dp (fun z : Key I X T => z.2) y = 0

noncomputable def cumulativeRemainder (p : Key I X T → ℝ)
    (beta : Node I) (h : ℕ) : ℝ :=
  supportedAverage p (fun z =>
    logRemainder (sourceMass p z beta) h -
    logRemainder (restrictedMass p z beta) h + logRemainder (targetMass p z) h)

noncomputable def rowQueryMoment (p : Key I X T → ℝ) (c : Node I → ℝ) : ℝ :=
  ∑ beta, |c beta| * queryMoment p beta

noncomputable def blockScore (p dp : Key I X T → ℝ) (h : ℕ)
    (block : Fin (h + 1) → Key I X T) : ℝ :=
  ∑ r : Fin (h + 1), score p dp (block r)

/-- Includes row zero, the independently drawn anchor. -/
noncomputable def scoreGradient (p dp : Key I X T → ℝ) (alpha : Node I) (h : ℕ)
    (block : Fin (h + 1) → Key I X T) : ℝ :=
  blockStatistic alpha h block * blockScore p dp h block

noncomputable def meanScoreGradient (p dp : Key I X T → ℝ)
    (alpha : Node I) (h : ℕ) : ℝ :=
  ∫ block, scoreGradient p dp alpha h block ∂rowLaw p (h + 1)

end Categorical

/-- Both actual prefix integrals occur; negative rank and arrival gate are native. -/
abbrev native_cumulative_increments_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (z : Key I X T) (alpha : Node I) (n : ℕ),
    Law p → 0 < p z →
      cumulative (fun beta =>
        ∫ rows, positiveOnPrefix z beta (List.ofFn rows) ∂rowLaw p (n + 1)) alpha =
          (1 - sourceMass p z alpha) ^ (n + 1) / ((n : ℝ) + 1) ∧
      cumulative (fun beta =>
        ∫ rows, negativeOnPrefix z beta (List.ofFn rows) ∂rowLaw p (n + 1)) alpha =
          ((1 - restrictedMass p z alpha) ^ (n + 1) -
            (1 - targetMass p z) ^ (n + 1)) / ((n : ℝ) + 1)

/-- Exact finite correspondence, before any derivative or bound is taken. -/
abbrev actual_atom_remainder_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : Key I X T → ℝ) (plus minus : Key I X T → Node I → ℝ)
      (alpha : Node I) (h : ℕ),
    Law p → SupportedInversePair p plus minus →
      cumulative (fun beta =>
        jointAtomMean p plus minus beta - actualBlockMean p beta h) alpha =
          cumulativeRemainder p alpha h ∧
      ∀ c : Node I → ℝ, FullInverseRow alpha c →
        jointAtomMean p plus minus alpha - actualBlockMean p alpha h =
          cumulative (fun beta => c beta * cumulativeRemainder p beta h) alpha

/-- Finite product differentiation and normalization, without target restrictions. -/
abbrev finite_block_score_derivative_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : ℝ → Key I X T → ℝ) (dp : Key I X T → ℝ) (t0 L : ℝ)
      (alpha : Node I) (h : ℕ),
    LocalLawTangent p dp t0 L →
      total dp = 0 ∧
      (∫ z, score (p t0) dp z ∂keyMeasure (p t0)) = 0 ∧
      HasDerivAt (fun t => actualBlockMean (p t) alpha h)
        (meanScoreGradient (p t0) dp alpha h) t0

/-- Main scalar/local theorem: derivative existence and the weighted 2L bound. -/
abbrev actual_atom_score_bias_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : ℝ → Key I X T → ℝ) (dp : Key I X T → ℝ) (t0 L : ℝ)
      (plus minus : ℝ → Key I X T → Node I → ℝ)
      (alpha : Node I) (c : Node I → ℝ) (h : ℕ),
    LocalLawTangent p dp t0 L → TargetTangentZero dp →
    (∀ᶠ t in 𝓝 t0, SupportedInversePair (p t) (plus t) (minus t)) →
    FullInverseRow alpha c →
      ∃ dAtom : ℝ,
        HasDerivAt (fun t => jointAtomMean (p t) (plus t) (minus t) alpha) dAtom t0 ∧
        HasDerivAt (fun t => actualBlockMean (p t) alpha h)
          (meanScoreGradient (p t0) dp alpha h) t0 ∧
        |dAtom - meanScoreGradient (p t0) dp alpha h| ≤
          (2 * L / ((h : ℝ) + 1)) * rowQueryMoment (p t0) c

section Latent
variable {W : Type x} [Fintype W] [DecidableEq W]
local instance latentSpace : MeasurableSpace W := ⊤

noncomputable def latentMeasure (rho : W → ℝ) : Measure W :=
  ∑ z, ENNReal.ofReal (rho z) • Measure.dirac z

noncomputable def latentRowLaw (rho : W → ℝ) (count : ℕ) : Measure (Fin count → W) :=
  Measure.pi fun _ : Fin count => latentMeasure rho

variable {I : Type u} {X : I → Type v} {T : Type w}
variable [Fintype I] [∀ i, Fintype (X i)] [Fintype T]
variable [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]

/-- Also used for signed coordinate tangents; law preservation is a conclusion. -/
noncomputable def inducedMass (phi : W → Key I X T) (rho : W → ℝ) : Key I X T → ℝ :=
  fun z => ∑ w, if phi w = z then rho w else 0

def mapBlock (phi : W → Key I X T) (count : ℕ) (rows : Fin count → W) :
    Fin count → Key I X T := fun r => phi (rows r)

noncomputable def latentScoreGradient (rho drho : W → ℝ) (phi : W → Key I X T)
    (alpha : Node I) (h : ℕ) (rows : Fin (h + 1) → W) : ℝ :=
  blockStatistic alpha h (mapBlock phi (h + 1) rows) *
    ∑ r : Fin (h + 1), score rho drho (rows r)

noncomputable def meanLatentScoreGradient (rho drho : W → ℝ)
    (phi : W → Key I X T) (alpha : Node I) (h : ℕ) : ℝ :=
  ∫ rows, latentScoreGradient rho drho phi alpha h rows ∂latentRowLaw rho (h + 1)

end Latent

/-- Genuine finite pushforward, coordinate derivatives, product map and conditional score. -/
abbrev finite_latent_pushforward_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w) (W : Type x)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T] [Fintype W]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T] [DecidableEq W]
      (rho : ℝ → W → ℝ) (drho : W → ℝ) (t0 L : ℝ) (phi : W → Key I X T),
    letI : MeasurableSpace W := ⊤;
    LocalLawTangent rho drho t0 L →
      LocalLawTangent (fun t => inducedMass phi (rho t)) (inducedMass phi drho) t0 L ∧
      (latentMeasure (rho t0)).map phi = keyMeasure (inducedMass phi (rho t0)) ∧
      (∀ count : ℕ,
        (latentRowLaw (rho t0) count).map (mapBlock phi count) =
          rowLaw (inducedMass phi (rho t0)) count) ∧
      ∀ z : Key I X T, 0 < inducedMass phi (rho t0) z →
        score (inducedMass phi (rho t0)) (inducedMass phi drho) z =
          (∑ w, if phi w = z then rho t0 w * score (rho t0) drho w else 0) /
            inducedMass phi (rho t0) z

/-- Accessible latent score is unbiased for the derivative of the actual finite-prefix mean. -/
abbrev finite_latent_score_derivative_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w) (W : Type x)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T] [Fintype W]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T] [DecidableEq W]
      (rho : ℝ → W → ℝ) (drho : W → ℝ) (t0 L : ℝ) (phi : W → Key I X T)
      (alpha : Node I) (h : ℕ),
    letI : MeasurableSpace W := ⊤;
    LocalLawTangent rho drho t0 L →
      Integrable (latentScoreGradient (rho t0) drho phi alpha h)
        (latentRowLaw (rho t0) (h + 1)) ∧
      meanLatentScoreGradient (rho t0) drho phi alpha h =
        meanScoreGradient (inducedMass phi (rho t0)) (inducedMass phi drho) alpha h ∧
      HasDerivAt (fun t => actualBlockMean (inducedMass phi (rho t)) alpha h)
        (meanLatentScoreGradient (rho t0) drho phi alpha h) t0

/-- Fixed base state and an explicit permitted encoder-input projection. -/
def encoderMass {B : Type u} {D : Type v} {C : Type w}
    (base : B → ℝ) (input : B → D) (q : D → C → ℝ) (z : B × C) : ℝ :=
  base z.1 * q (input z.1) z.2

/-- The base probabilities cancel from supported sampled scores. This is not a
claim that target labels belong among the encoder's inference inputs. -/
abbrev finite_encoder_score_target : Prop :=
  ∀ (B : Type u) (D : Type v) (C : Type w)
      [Fintype B] [Fintype D] [Fintype C]
      (base : B → ℝ) (input : B → D)
      (q : ℝ → D → C → ℝ) (dq : D → C → ℝ) (t0 L : ℝ),
    Law base → (∀ d, LocalLawTangent (fun t => q t d) (dq d) t0 L) →
      LocalLawTangent (fun t => encoderMass base input (q t))
        (encoderMass base input dq) t0 L ∧
      ∀ z : B × C, 0 < encoderMass base input (q t0) z →
        score (encoderMass base input (q t0)) (encoderMass base input dq) z =
          dq (input z.1) z.2 / q t0 (input z.1) z.2

/-- Separate sampling statement; no independence of block value and scores is assumed. -/
abbrev score_second_moment_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T]
      (p : ℝ → Key I X T → ℝ) (dp : Key I X T → ℝ) (t0 L : ℝ)
      (alpha : Node I) (h : ℕ),
    LocalLawTangent p dp t0 L →
      Integrable (fun block => (scoreGradient (p t0) dp alpha h block) ^ 2)
        (rowLaw (p t0) (h + 1)) ∧
      Integrable (fun z => (score (p t0) dp z) ^ 2) (keyMeasure (p t0)) ∧
      (∫ block, (scoreGradient (p t0) dp alpha h block) ^ 2 ∂rowLaw (p t0) (h + 1)) ≤
        ((h : ℝ) + 1) * (harmonic h) ^ 2 *
          (∫ z, (score (p t0) dp z) ^ 2 ∂keyMeasure (p t0)) ∧
      (∫ z, (score (p t0) dp z) ^ 2 ∂keyMeasure (p t0)) ≤ L ^ 2

/-- Same range/zero-mean-score argument on actual IID latent rows; no variance
ordering or calibration is folded into this separate target. -/
abbrev latent_score_second_moment_target : Prop :=
  ∀ (I : Type u) (X : I → Type v) (T : Type w) (W : Type x)
      [Fintype I] [Nonempty I] [∀ i, Fintype (X i)] [Fintype T] [Fintype W]
      [DecidableEq I] [∀ i, DecidableEq (X i)] [DecidableEq T] [DecidableEq W]
      (rho : ℝ → W → ℝ) (drho : W → ℝ) (t0 L : ℝ) (phi : W → Key I X T)
      (alpha : Node I) (h : ℕ),
    letI : MeasurableSpace W := ⊤;
    LocalLawTangent rho drho t0 L →
      Integrable (fun rows => (latentScoreGradient (rho t0) drho phi alpha h rows) ^ 2)
        (latentRowLaw (rho t0) (h + 1)) ∧
      Integrable (fun z => (score (rho t0) drho z) ^ 2) (latentMeasure (rho t0)) ∧
      (∫ rows, (latentScoreGradient (rho t0) drho phi alpha h rows) ^ 2
        ∂latentRowLaw (rho t0) (h + 1)) ≤
          ((h : ℝ) + 1) * (harmonic h) ^ 2 *
            (∫ z, (score (rho t0) drho z) ^ 2 ∂latentMeasure (rho t0)) ∧
      (∫ z, (score (rho t0) drho z) ^ 2 ∂latentMeasure (rho t0)) ≤ L ^ 2

end PidPrefixMgwGradientContract
