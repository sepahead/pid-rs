import PidFiniteConvergence.Dependence

/-!
# Algebraic core for sharper finite-discrete local-continuity bounds

This module proves exact-real algebraic obligations for a sharper finite-discrete SxPID
local-continuity argument:

* a zero-total signed vector acts on a bounded function through one half of its oscillation;
* the gradients of a negative event log, a nested-event log ratio, and an intersection
  pointwise-mutual-information expression have diameter at most the reciprocal mass of their
  smallest event;
* the four ordinary-diamond gradient coordinates and the five conditioned-nested lifted
  coordinates have the same reciprocal-mass diameter bound;
* the ordinary-diamond ratio lies between one and its floor-dependent algebraic ceiling;
* nonnegative coordinates whose sum is a bounded top value lie in the same bounded interval;
* an arbitrary fixed linear row transfers coordinatewise perturbation bounds through its
  absolute row sum;
* component and signed-net ranges give their respective half-range and full-range weight terms;
* the linear-row and weight bounds compose for finite averages; and
* every event mass along a line segment has a factorized lower bound.

The Boolean arguments below are only event-membership indicators. The module does not formalize
probability laws, event construction, differentiation, a path integral, or the analytic step that
integrates a gradient bound. It does not identify the generic rows or coordinates with the SxPID
redundancy lattice, formalize Makkeh--Gutknecht--Wibral Theorem IV.3, or prove refinement to the
pid-rs Rust implementation or binary64 arithmetic. It also leaves the conditioned-diamond lifted
gradient and its crossed reciprocal cases unformalized. Those boundaries require separate
evidence.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators

namespace PidFiniteConvergence

variable {ι κ : Type*}

/-- A zero-total finite signed vector acts on a function through at most one half of the
function's stated oscillation. The interval endpoints need not be attained. -/
theorem abs_zero_sum_weighted_sum_le_half_oscillation
    (indices : Finset ι) (signedWeight value : ι → ℝ)
    {lower upper l1Bound : ℝ}
    (hzero : ∑ i ∈ indices, signedWeight i = 0)
    (hlowerUpper : lower ≤ upper)
    (_hl1Nonnegative : 0 ≤ l1Bound)
    (hvalueRange : ∀ i ∈ indices, lower ≤ value i ∧ value i ≤ upper)
    (hl1 : ∑ i ∈ indices, |signedWeight i| ≤ l1Bound) :
    |∑ i ∈ indices, signedWeight i * value i| ≤
      l1Bound * (upper - lower) / 2 := by
  have hcenteredValue :
      ∀ i ∈ indices,
        |value i - (lower + upper) / 2| ≤ (upper - lower) / 2 := by
    intro i hi
    rw [abs_le]
    constructor <;> linarith [hvalueRange i hi]
  have hhalfRangeNonnegative : 0 ≤ (upper - lower) / 2 := by
    linarith
  have hcenter :
      (∑ i ∈ indices, signedWeight i * value i) =
        ∑ i ∈ indices,
          signedWeight i * (value i - (lower + upper) / 2) := by
    calc
      (∑ i ∈ indices, signedWeight i * value i) =
          ∑ i ∈ indices,
            (signedWeight i * (value i - (lower + upper) / 2) +
              signedWeight i * ((lower + upper) / 2)) := by
        apply Finset.sum_congr rfl
        intro i _
        ring
      _ =
          (∑ i ∈ indices,
            signedWeight i * (value i - (lower + upper) / 2)) +
          ∑ i ∈ indices, signedWeight i * ((lower + upper) / 2) :=
        Finset.sum_add_distrib
      _ =
          (∑ i ∈ indices,
            signedWeight i * (value i - (lower + upper) / 2)) +
          (∑ i ∈ indices, signedWeight i) * ((lower + upper) / 2) := by
        rw [Finset.sum_mul]
      _ =
          ∑ i ∈ indices,
            signedWeight i * (value i - (lower + upper) / 2) := by
        rw [hzero, zero_mul, add_zero]
  rw [hcenter]
  calc
    |∑ i ∈ indices,
        signedWeight i * (value i - (lower + upper) / 2)|
        ≤ ∑ i ∈ indices,
            |signedWeight i * (value i - (lower + upper) / 2)| :=
          Finset.abs_sum_le_sum_abs
            (f := fun i =>
              signedWeight i * (value i - (lower + upper) / 2)) indices
    _ =
        ∑ i ∈ indices,
          |signedWeight i| * |value i - (lower + upper) / 2| := by
      apply Finset.sum_congr rfl
      intro i _
      exact abs_mul (signedWeight i) (value i - (lower + upper) / 2)
    _ ≤
        ∑ i ∈ indices,
          |signedWeight i| * ((upper - lower) / 2) := by
      apply Finset.sum_le_sum
      intro i hi
      exact mul_le_mul_of_nonneg_left
        (hcenteredValue i hi) (abs_nonneg (signedWeight i))
    _ =
        (∑ i ∈ indices, |signedWeight i|) *
          ((upper - lower) / 2) := by
      rw [Finset.sum_mul]
    _ ≤ l1Bound * ((upper - lower) / 2) :=
      mul_le_mul_of_nonneg_right hl1 hhalfRangeNonnegative
    _ = l1Bound * (upper - lower) / 2 := by ring

/-- The derivative-shaped value for `-log eventMass` at one Boolean membership pattern. -/
noncomputable def negativeLogEventGradient
    (inside : Bool) (eventMass : ℝ) : ℝ :=
  match inside with
  | false => 0
  | true => -(1 / eventMass)

/-- Two negative-event-log gradient values differ by at most the reciprocal event mass. -/
theorem negative_log_event_gradient_diameter_le
    (insideX insideY : Bool) {eventMass : ℝ}
    (hevent : 0 < eventMass) :
    |negativeLogEventGradient insideX eventMass -
        negativeLogEventGradient insideY eventMass| ≤
      1 / eventMass := by
  have hreciprocalPositive : 0 < 1 / eventMass :=
    one_div_pos.mpr hevent
  rw [abs_le]
  constructor <;>
    cases insideX <;> cases insideY <;>
    simp only [negativeLogEventGradient] <;> linarith

/-- The derivative-shaped value for `log (largeMass / smallMass)` at one Boolean membership
pattern. The definition is algebraic and does not assert that the masses come from events. -/
noncomputable def nestedLogRatioGradient
    (inSmall inLarge : Bool) (smallMass largeMass : ℝ) : ℝ :=
  match inSmall, inLarge with
  | false, false => 0
  | false, true => 1 / largeMass
  | true, false => -(1 / smallMass)
  | true, true => 1 / largeMass - 1 / smallMass

/-- When the small membership implies the large membership, every nested-log-ratio gradient value
lies in an interval of width exactly `1 / smallMass`. -/
theorem nested_log_ratio_gradient_bounds
    (inSmall inLarge : Bool) {smallMass largeMass : ℝ}
    (hsmall : 0 < smallMass) (hsmallLarge : smallMass ≤ largeMass)
    (hnested : inSmall = true → inLarge = true) :
    1 / largeMass - 1 / smallMass ≤
        nestedLogRatioGradient inSmall inLarge smallMass largeMass ∧
      nestedLogRatioGradient inSmall inLarge smallMass largeMass ≤
        1 / largeMass := by
  have hlarge : 0 < largeMass := hsmall.trans_le hsmallLarge
  have hlargeReciprocalNonnegative : 0 ≤ 1 / largeMass :=
    (one_div_pos.mpr hlarge).le
  have hlargeReciprocalLe :
      1 / largeMass ≤ 1 / smallMass :=
    one_div_le_one_div_of_le hsmall hsmallLarge
  cases inSmall <;> cases inLarge
  · change
      1 / largeMass - 1 / smallMass ≤ 0 ∧
        0 ≤ 1 / largeMass
    constructor <;> linarith
  · change
      1 / largeMass - 1 / smallMass ≤ 1 / largeMass ∧
        1 / largeMass ≤ 1 / largeMass
    constructor <;> linarith
  · cases hnested rfl
  · change
      1 / largeMass - 1 / smallMass ≤
          1 / largeMass - 1 / smallMass ∧
        1 / largeMass - 1 / smallMass ≤ 1 / largeMass
    constructor <;> linarith

/-- Two valid membership patterns for nested events have log-ratio gradient values separated by
at most the reciprocal mass of the smaller event. -/
theorem nested_log_ratio_gradient_diameter_le
    (smallX largeX smallY largeY : Bool) {smallMass largeMass : ℝ}
    (hsmall : 0 < smallMass) (hsmallLarge : smallMass ≤ largeMass)
    (hnestedX : smallX = true → largeX = true)
    (hnestedY : smallY = true → largeY = true) :
    |nestedLogRatioGradient smallX largeX smallMass largeMass -
        nestedLogRatioGradient smallY largeY smallMass largeMass| ≤
      1 / smallMass := by
  have hx := nested_log_ratio_gradient_bounds
    smallX largeX hsmall hsmallLarge hnestedX
  have hy := nested_log_ratio_gradient_bounds
    smallY largeY hsmall hsmallLarge hnestedY
  rw [abs_le]
  constructor <;> linarith

/-- The derivative-shaped value for
`log intersectionMass - log leftMass - log rightMass` at one pair of Boolean memberships. -/
noncomputable def intersectionPmiGradient
    (inLeft inRight : Bool)
    (intersectionMass leftMass rightMass : ℝ) : ℝ :=
  match inLeft, inRight with
  | false, false => 0
  | false, true => -(1 / rightMass)
  | true, false => -(1 / leftMass)
  | true, true =>
      1 / intersectionMass - 1 / leftMass - 1 / rightMass

/-- Any two intersection-PMI gradient values differ by at most the reciprocal intersection mass.
Only positivity and the two marginal-mass order relations are used. -/
theorem intersection_pmi_gradient_diameter_le
    (leftX rightX leftY rightY : Bool)
    {intersectionMass leftMass rightMass : ℝ}
    (hintersection : 0 < intersectionMass)
    (hintersectionLeft : intersectionMass ≤ leftMass)
    (hintersectionRight : intersectionMass ≤ rightMass) :
    |intersectionPmiGradient leftX rightX
          intersectionMass leftMass rightMass -
        intersectionPmiGradient leftY rightY
          intersectionMass leftMass rightMass| ≤
      1 / intersectionMass := by
  have hleft : 0 < leftMass := hintersection.trans_le hintersectionLeft
  have hright : 0 < rightMass := hintersection.trans_le hintersectionRight
  have hintersectionReciprocalPositive : 0 < 1 / intersectionMass :=
    one_div_pos.mpr hintersection
  have hleftReciprocalPositive : 0 < 1 / leftMass :=
    one_div_pos.mpr hleft
  have hrightReciprocalPositive : 0 < 1 / rightMass :=
    one_div_pos.mpr hright
  have hleftReciprocalLe :
      1 / leftMass ≤ 1 / intersectionMass :=
    one_div_le_one_div_of_le hintersection hintersectionLeft
  have hrightReciprocalLe :
      1 / rightMass ≤ 1 / intersectionMass :=
    one_div_le_one_div_of_le hintersection hintersectionRight
  rw [abs_le]
  constructor <;>
    cases leftX <;> cases rightX <;> cases leftY <;> cases rightY <;>
    simp only [intersectionPmiGradient] <;> linarith

/-- The four algebraic coordinate classes of an ordinary two-source diamond. The names do not
encode a probability partition. -/
inductive DiamondCoordinate where
  | common
  | leftExclusive
  | rightExclusive
  | outside

/-- The ordinary-diamond gradient written in terms of four reciprocal masses:
`1/a`, `1/(a+b)`, `1/(a+c)`, and `1/(a+b+c)`. -/
noncomputable def ordinaryDiamondGradientFromReciprocals
    (coordinate : DiamondCoordinate)
    (reciprocalA reciprocalAB reciprocalAC reciprocalABC : ℝ) : ℝ :=
  match coordinate with
  | .common =>
      reciprocalAB + reciprocalAC - reciprocalA - reciprocalABC
  | .leftExclusive => reciprocalAB - reciprocalABC
  | .rightExclusive => reciprocalAC - reciprocalABC
  | .outside => 0

/-- Explicit reciprocal order inequalities force every pair of ordinary-diamond gradient
coordinates to differ by at most `reciprocalA`. -/
theorem ordinary_diamond_gradient_diameter_of_reciprocal_bounds
    (coordinateX coordinateY : DiamondCoordinate)
    {reciprocalA reciprocalAB reciprocalAC reciprocalABC : ℝ}
    (hABCNonnegative : 0 ≤ reciprocalABC)
    (hABCAB : reciprocalABC ≤ reciprocalAB)
    (hABCAC : reciprocalABC ≤ reciprocalAC)
    (hABA : reciprocalAB ≤ reciprocalA)
    (hACA : reciprocalAC ≤ reciprocalA) :
    |ordinaryDiamondGradientFromReciprocals coordinateX
          reciprocalA reciprocalAB reciprocalAC reciprocalABC -
        ordinaryDiamondGradientFromReciprocals coordinateY
          reciprocalA reciprocalAB reciprocalAC reciprocalABC| ≤
      reciprocalA := by
  rw [abs_le]
  constructor <;>
    cases coordinateX <;> cases coordinateY <;>
    simp only [ordinaryDiamondGradientFromReciprocals] <;> linarith

/-- Reciprocal supermodularity and nesting give the ordinary-diamond gradient sign pattern. -/
theorem ordinary_diamond_gradient_signs_of_reciprocal_bounds
    {reciprocalA reciprocalAB reciprocalAC reciprocalABC : ℝ}
    (hABCAB : reciprocalABC ≤ reciprocalAB)
    (hABCAC : reciprocalABC ≤ reciprocalAC)
    (hsupermodular :
      reciprocalAB + reciprocalAC ≤ reciprocalA + reciprocalABC) :
    ordinaryDiamondGradientFromReciprocals .common
          reciprocalA reciprocalAB reciprocalAC reciprocalABC ≤ 0 ∧
      0 ≤ ordinaryDiamondGradientFromReciprocals .leftExclusive
          reciprocalA reciprocalAB reciprocalAC reciprocalABC ∧
      0 ≤ ordinaryDiamondGradientFromReciprocals .rightExclusive
          reciprocalA reciprocalAB reciprocalAC reciprocalABC ∧
      ordinaryDiamondGradientFromReciprocals .outside
          reciprocalA reciprocalAB reciprocalAC reciprocalABC = 0 := by
  simp only [ordinaryDiamondGradientFromReciprocals]
  constructor
  · linarith
  · constructor
    · linarith
    · constructor
      · linarith
      · trivial

/-- Reciprocal mass is supermodular on the ordinary diamond. The exact difference is a
nonnegative rational expression with numerator `b * c * (2 * a + b + c)`. -/
theorem ordinary_diamond_reciprocal_supermodular
    {a b c : ℝ} (ha : 0 < a) (hb : 0 ≤ b) (hc : 0 ≤ c) :
    1 / (a + b) + 1 / (a + c) ≤
      1 / a + 1 / (a + b + c) := by
  have hab : 0 < a + b := by linarith
  have hac : 0 < a + c := by linarith
  have habc : 0 < a + b + c := by linarith
  have hidentity :
      (1 / a + 1 / (a + b + c)) -
          (1 / (a + b) + 1 / (a + c)) =
        b * c * (2 * a + b + c) /
          (a * (a + b) * (a + c) * (a + b + c)) := by
    field_simp
    ring
  apply sub_nonneg.mp
  rw [hidentity]
  exact div_nonneg
    (mul_nonneg
      (mul_nonneg hb hc)
      (by linarith))
    (mul_nonneg
      (mul_nonneg
        (mul_nonneg ha.le hab.le)
        hac.le)
      habc.le)

/-- The ordinary-diamond gradient evaluated from positive masses. -/
noncomputable def ordinaryDiamondGradient
    (coordinate : DiamondCoordinate) (a b c : ℝ) : ℝ :=
  ordinaryDiamondGradientFromReciprocals coordinate
    (1 / a) (1 / (a + b)) (1 / (a + c)) (1 / (a + b + c))

/-- Every pair of ordinary-diamond gradient coordinates differs by at most `1 / a`. -/
theorem ordinary_diamond_gradient_coordinate_diameter_le
    (coordinateX coordinateY : DiamondCoordinate)
    {a b c : ℝ} (ha : 0 < a) (hb : 0 ≤ b) (hc : 0 ≤ c) :
    |ordinaryDiamondGradient coordinateX a b c -
        ordinaryDiamondGradient coordinateY a b c| ≤
      1 / a := by
  have hab : 0 < a + b := by linarith
  have hac : 0 < a + c := by linarith
  have habc : 0 < a + b + c := by linarith
  apply ordinary_diamond_gradient_diameter_of_reciprocal_bounds
  · exact (one_div_pos.mpr habc).le
  · exact one_div_le_one_div_of_le hab (by linarith)
  · exact one_div_le_one_div_of_le hac (by linarith)
  · exact one_div_le_one_div_of_le ha (by linarith)
  · exact one_div_le_one_div_of_le ha (by linarith)

/-- The positive ratio inside the ordinary-diamond logarithm. -/
noncomputable def ordinaryDiamondRatio (a b c : ℝ) : ℝ :=
  ((a + b) * (a + c)) / (a * (a + b + c))

/-- The ordinary-diamond ratio bounds in denominator-cleared form. The upper inequality is the
algebraic form of the floor-dependent `L - 2h` ceiling after taking logarithms. -/
theorem ordinary_diamond_ratio_cross_multiplication_bounds
    {floorMass a b c : ℝ}
    (hfloor : 0 < floorMass)
    (hfloorA : floorMass ≤ a)
    (hb : 0 ≤ b) (hc : 0 ≤ c)
    (htotal : a + b + c ≤ 1) :
    a * (a + b + c) ≤ (a + b) * (a + c) ∧
      4 * floorMass * ((a + b) * (a + c)) ≤
        (1 + floorMass) ^ 2 * (a * (a + b + c)) := by
  have ha : 0 < a := hfloor.trans_le hfloorA
  have haNonnegative : 0 ≤ a := ha.le
  have hsumPositive : 0 < a + b + c := by linarith
  have haSum : a ≤ a + b + c := by linarith
  have hfloorOne : floorMass ≤ 1 :=
    hfloorA.trans (haSum.trans htotal)
  have hfloorMulALeA : floorMass * a ≤ a := by
    nlinarith [mul_nonneg (sub_nonneg.mpr hfloorOne) haNonnegative]
  have hfloorMulALeSum :
      floorMass * a ≤ a + b + c :=
    hfloorMulALeA.trans haSum
  have hfloorMulSumLeFloor :
      floorMass * (a + b + c) ≤ floorMass := by
    nlinarith [mul_nonneg hfloor.le (sub_nonneg.mpr htotal)]
  have hfloorMulSumLeA :
      floorMass * (a + b + c) ≤ a :=
    hfloorMulSumLeFloor.trans hfloorA
  have hfactorNonnegative :
      0 ≤
        ((a + b + c) - floorMass * a) *
          (a - floorMass * (a + b + c)) :=
    mul_nonneg
      (sub_nonneg.mpr hfloorMulALeSum)
      (sub_nonneg.mpr hfloorMulSumLeA)
  have hmiddle :
      floorMass * (a + (a + b + c)) ^ 2 ≤
        (1 + floorMass) ^ 2 * (a * (a + b + c)) := by
    nlinarith [hfactorNonnegative]
  have hamgm :
      4 * ((a + b) * (a + c)) ≤
        (2 * a + b + c) ^ 2 := by
    nlinarith [sq_nonneg (b - c)]
  constructor
  · nlinarith [mul_nonneg hb hc]
  · calc
      4 * floorMass * ((a + b) * (a + c)) =
          floorMass * (4 * ((a + b) * (a + c))) := by ring
      _ ≤ floorMass * (2 * a + b + c) ^ 2 :=
        mul_le_mul_of_nonneg_left hamgm hfloor.le
      _ = floorMass * (a + (a + b + c)) ^ 2 := by ring
      _ ≤ (1 + floorMass) ^ 2 * (a * (a + b + c)) :=
        hmiddle

/-- The ordinary-diamond ratio lies between one and
`(1 + floorMass)^2 / (4 * floorMass)`. -/
theorem ordinary_diamond_ratio_bounds
    {floorMass a b c : ℝ}
    (hfloor : 0 < floorMass)
    (hfloorA : floorMass ≤ a)
    (hb : 0 ≤ b) (hc : 0 ≤ c)
    (htotal : a + b + c ≤ 1) :
    1 ≤ ordinaryDiamondRatio a b c ∧
      ordinaryDiamondRatio a b c ≤
        (1 + floorMass) ^ 2 / (4 * floorMass) := by
  have ha : 0 < a := hfloor.trans_le hfloorA
  have hsumPositive : 0 < a + b + c := by linarith
  have hdenominator : 0 < a * (a + b + c) :=
    mul_pos ha hsumPositive
  have hfloorDenominator : 0 < 4 * floorMass := by positivity
  have hcross :=
    ordinary_diamond_ratio_cross_multiplication_bounds
      hfloor hfloorA hb hc htotal
  constructor
  · apply (le_div_iff₀ hdenominator).2
    simpa [ordinaryDiamondRatio] using hcross.1
  · change
      ((a + b) * (a + c)) / (a * (a + b + c)) ≤
        (1 + floorMass) ^ 2 / (4 * floorMass)
    apply (div_le_div_iff₀ hdenominator hfloorDenominator).2
    simpa only [mul_assoc, mul_comm, mul_left_comm] using hcross.2

/-- The logarithmic ordinary-diamond value. -/
noncomputable def ordinaryDiamondPhi (a b c : ℝ) : ℝ :=
  Real.log (ordinaryDiamondRatio a b c)

/-- The ordinary-diamond logarithmic value is nonnegative. -/
theorem ordinary_diamond_phi_nonnegative
    {a b c : ℝ} (ha : 0 < a) (hb : 0 ≤ b) (hc : 0 ≤ c) :
    0 ≤ ordinaryDiamondPhi a b c := by
  have hsumPositive : 0 < a + b + c := by linarith
  have hdenominator : 0 < a * (a + b + c) :=
    mul_pos ha hsumPositive
  apply Real.log_nonneg
  change 1 ≤ ((a + b) * (a + c)) / (a * (a + b + c))
  apply (le_div_iff₀ hdenominator).2
  nlinarith [mul_nonneg hb hc]

/-- The ordinary-diamond logarithmic value is at most the logarithm of the algebraic
floor-dependent ceiling. -/
theorem ordinary_diamond_phi_le_floor_log_ceiling
    {floorMass a b c : ℝ}
    (hfloor : 0 < floorMass)
    (hfloorA : floorMass ≤ a)
    (hb : 0 ≤ b) (hc : 0 ≤ c)
    (htotal : a + b + c ≤ 1) :
    ordinaryDiamondPhi a b c ≤
      Real.log ((1 + floorMass) ^ 2 / (4 * floorMass)) := by
  have hratio :=
    ordinary_diamond_ratio_bounds hfloor hfloorA hb hc htotal
  exact Real.log_le_log
    (zero_lt_one.trans_le hratio.1) hratio.2

/-- The logarithm of the algebraic floor ceiling is exactly `L - 2h` when
`L = -log floorMass` and `h = log (2 / (1 + floorMass))`. -/
theorem ordinary_diamond_floor_log_ceiling_eq
    {floorMass : ℝ} (hfloor : 0 < floorMass) :
    Real.log ((1 + floorMass) ^ 2 / (4 * floorMass)) =
      -Real.log floorMass -
        2 * Real.log (2 / (1 + floorMass)) := by
  have honeFloor : 1 + floorMass ≠ 0 := by linarith
  have hfloorNe : floorMass ≠ 0 := hfloor.ne'
  have hfourNe : (4 : ℝ) ≠ 0 := by norm_num
  have htwoNe : (2 : ℝ) ≠ 0 := by norm_num
  have hlogFour :
      Real.log (4 : ℝ) = 2 * Real.log (2 : ℝ) := by
    calc
      Real.log (4 : ℝ) = Real.log ((2 : ℝ) * 2) := by norm_num
      _ = Real.log (2 : ℝ) + Real.log (2 : ℝ) :=
        Real.log_mul htwoNe htwoNe
      _ = 2 * Real.log (2 : ℝ) := by ring
  rw [Real.log_div (pow_ne_zero 2 honeFloor) (mul_ne_zero hfourNe hfloorNe)]
  rw [Real.log_pow]
  rw [Real.log_mul hfourNe hfloorNe]
  rw [Real.log_div htwoNe honeFloor]
  rw [hlogFour]
  norm_num
  ring

/-- The ordinary-diamond value obeys the floor-dependent `L - 2h` upper bound. -/
theorem ordinary_diamond_phi_le_floor_radius_sub_twice_correction
    {floorMass a b c : ℝ}
    (hfloor : 0 < floorMass)
    (hfloorA : floorMass ≤ a)
    (hb : 0 ≤ b) (hc : 0 ≤ c)
    (htotal : a + b + c ≤ 1) :
    ordinaryDiamondPhi a b c ≤
      -Real.log floorMass -
        2 * Real.log (2 / (1 + floorMass)) := by
  rw [← ordinary_diamond_floor_log_ceiling_eq hfloor]
  exact ordinary_diamond_phi_le_floor_log_ceiling
    hfloor hfloorA hb hc htotal

/-- The ordinary-diamond value lies between zero and the floor-dependent `L - 2h` ceiling. -/
theorem ordinary_diamond_phi_floor_bounds
    {floorMass a b c : ℝ}
    (hfloor : 0 < floorMass)
    (hfloorA : floorMass ≤ a)
    (hb : 0 ≤ b) (hc : 0 ≤ c)
    (htotal : a + b + c ≤ 1) :
    0 ≤ ordinaryDiamondPhi a b c ∧
      ordinaryDiamondPhi a b c ≤
        -Real.log floorMass -
          2 * Real.log (2 / (1 + floorMass)) := by
  constructor
  · exact ordinary_diamond_phi_nonnegative
      (hfloor.trans_le hfloorA) hb hc
  · exact ordinary_diamond_phi_le_floor_radius_sub_twice_correction
      hfloor hfloorA hb hc htotal

/-- The floor-dependent `L - 2h` algebraic expression is nonnegative for every positive input. -/
theorem ordinary_diamond_floor_radius_sub_twice_correction_nonnegative
    {floorMass : ℝ} (hfloor : 0 < floorMass) :
    0 ≤ -Real.log floorMass -
      2 * Real.log (2 / (1 + floorMass)) := by
  have hdenominator : 0 < 4 * floorMass := by positivity
  have hratio :
      1 ≤ (1 + floorMass) ^ 2 / (4 * floorMass) := by
    apply (le_div_iff₀ hdenominator).2
    nlinarith [sq_nonneg (1 - floorMass)]
  rw [← ordinary_diamond_floor_log_ceiling_eq hfloor]
  exact Real.log_nonneg hratio

/-- The five coordinate classes in the lifted gradient of a conditioned nested-event
difference. The labels describe algebraic positions only. -/
inductive ConditionedNestedCoordinate where
  | totalSmall
  | totalExclusive
  | conditionedSmall
  | conditionedExclusive
  | outside

/-- The conditioned-nested lifted gradient written in terms of
`1/x_a`, `1/(x_a+x_b)`, `1/(x_a+y_a)`, and
`1/(x_a+x_b+y_a+y_b)`. -/
noncomputable def conditionedNestedLiftedGradientFromReciprocals
    (coordinate : ConditionedNestedCoordinate)
    (reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB : ℝ) : ℝ :=
  match coordinate with
  | .totalSmall => reciprocalTotalAB - reciprocalTotalA
  | .totalExclusive => reciprocalTotalAB
  | .conditionedSmall =>
      reciprocalTotalAB - reciprocalTotalA - reciprocalXAB + reciprocalXA
  | .conditionedExclusive => reciprocalTotalAB - reciprocalXAB
  | .outside => 0

/-- The reciprocal partial order for a conditioned nested-event difference bounds every pair of
lifted gradient coordinates by `reciprocalXA`. -/
theorem conditioned_nested_lifted_gradient_diameter_of_reciprocal_bounds
    (coordinateX coordinateY : ConditionedNestedCoordinate)
    {reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB : ℝ}
    (hTotalABNonnegative : 0 ≤ reciprocalTotalAB)
    (hTotalABTotalA : reciprocalTotalAB ≤ reciprocalTotalA)
    (hTotalAXA : reciprocalTotalA ≤ reciprocalXA)
    (hTotalABXAB : reciprocalTotalAB ≤ reciprocalXAB)
    (hXABXA : reciprocalXAB ≤ reciprocalXA) :
    |conditionedNestedLiftedGradientFromReciprocals coordinateX
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB -
        conditionedNestedLiftedGradientFromReciprocals coordinateY
          reciprocalXA reciprocalXAB reciprocalTotalA reciprocalTotalAB| ≤
      reciprocalXA := by
  rw [abs_le]
  constructor <;>
    cases coordinateX <;> cases coordinateY <;>
    simp only [conditionedNestedLiftedGradientFromReciprocals] <;> linarith

/-- The conditioned-nested lifted gradient evaluated from four nonnegative region masses. -/
noncomputable def conditionedNestedLiftedGradient
    (coordinate : ConditionedNestedCoordinate)
    (xA xB yA yB : ℝ) : ℝ :=
  conditionedNestedLiftedGradientFromReciprocals coordinate
    (1 / xA)
    (1 / (xA + xB))
    (1 / (xA + yA))
    (1 / (xA + xB + yA + yB))

/-- Every pair of conditioned-nested lifted gradient coordinates differs by at most `1 / xA`. -/
theorem conditioned_nested_lifted_gradient_coordinate_diameter_le
    (coordinateX coordinateY : ConditionedNestedCoordinate)
    {xA xB yA yB : ℝ}
    (hxA : 0 < xA) (hxB : 0 ≤ xB) (hyA : 0 ≤ yA) (hyB : 0 ≤ yB) :
    |conditionedNestedLiftedGradient coordinateX xA xB yA yB -
        conditionedNestedLiftedGradient coordinateY xA xB yA yB| ≤
      1 / xA := by
  have hxAB : 0 < xA + xB := by linarith
  have htotalA : 0 < xA + yA := by linarith
  have htotalAB : 0 < xA + xB + yA + yB := by linarith
  apply conditioned_nested_lifted_gradient_diameter_of_reciprocal_bounds
  · exact (one_div_pos.mpr htotalAB).le
  · exact one_div_le_one_div_of_le htotalA (by linarith)
  · exact one_div_le_one_div_of_le hxA (by linarith)
  · exact one_div_le_one_div_of_le hxAB (by linarith)
  · exact one_div_le_one_div_of_le hxA (by linarith)

/-- A nonnegative coordinate is bounded by the stated upper bound on the top sum. The equality
premise records the external identification of that sum with the top cumulative component. -/
theorem component_coordinate_bounds_of_nonnegative_top_sum
    (indices : Finset ι) (component : ι → ℝ) {coordinate : ι}
    {topValue upperBound : ℝ}
    (hcoordinate : coordinate ∈ indices)
    (hnonnegative : ∀ i ∈ indices, 0 ≤ component i)
    (htopSum : ∑ i ∈ indices, component i = topValue)
    (htopBound : topValue ≤ upperBound) :
    0 ≤ component coordinate ∧ component coordinate ≤ upperBound := by
  constructor
  · exact hnonnegative coordinate hcoordinate
  · have hcoordinateLe :
        component coordinate ≤ ∑ i ∈ indices, component i :=
      Finset.single_le_sum
        (fun i hi => hnonnegative i hi) hcoordinate
    linarith

/-- A fixed external linear row transfers uniform coordinatewise changes through its absolute row
sum. The coefficients are arbitrary; no lattice is encoded. -/
theorem abs_mobius_row_change_le_abs_row_sum
    (indices : Finset κ) (coefficient valueP valueQ : κ → ℝ)
    {coordinateBound : ℝ}
    (hchange : ∀ i ∈ indices, |valueQ i - valueP i| ≤ coordinateBound) :
    |(∑ i ∈ indices, coefficient i * valueQ i) -
        ∑ i ∈ indices, coefficient i * valueP i| ≤
      (∑ i ∈ indices, |coefficient i|) * coordinateBound := by
  calc
    |(∑ i ∈ indices, coefficient i * valueQ i) -
        ∑ i ∈ indices, coefficient i * valueP i| =
        |∑ i ∈ indices, coefficient i * (valueQ i - valueP i)| := by
          apply congrArg abs
          rw [← Finset.sum_sub_distrib]
          apply Finset.sum_congr rfl
          intro i _
          ring
    _ ≤ (∑ i ∈ indices, |coefficient i|) * coordinateBound :=
      abs_linear_row_le_abs_row_sum
        indices coefficient (fun i => valueQ i - valueP i) hchange

/-- The difference of two component values in `[0, upperBound]` lies in the corresponding signed
net interval. -/
theorem net_value_bounds_of_component_bounds
    {informative misinformative upperBound : ℝ}
    (hinformative : 0 ≤ informative ∧ informative ≤ upperBound)
    (hmisinformative : 0 ≤ misinformative ∧ misinformative ≤ upperBound) :
    -upperBound ≤ informative - misinformative ∧
      informative - misinformative ≤ upperBound := by
  constructor <;> linarith

/-- A normalized nonnegative average of component values in `[0, upperBound]` remains in that
interval. -/
theorem component_weighted_average_bounds
    (indices : Finset ι) (weight component : ι → ℝ)
    {upperBound : ℝ}
    (hweightNonnegative : ∀ i ∈ indices, 0 ≤ weight i)
    (hweightSum : ∑ i ∈ indices, weight i = 1)
    (hcomponent : ∀ i ∈ indices, 0 ≤ component i ∧ component i ≤ upperBound) :
    0 ≤ ∑ i ∈ indices, weight i * component i ∧
      ∑ i ∈ indices, weight i * component i ≤ upperBound := by
  constructor
  · exact Finset.sum_nonneg fun i hi =>
      mul_nonneg (hweightNonnegative i hi) (hcomponent i hi).1
  · calc
      ∑ i ∈ indices, weight i * component i
          ≤ ∑ i ∈ indices, weight i * upperBound := by
            apply Finset.sum_le_sum
            intro i hi
            exact mul_le_mul_of_nonneg_left
              (hcomponent i hi).2 (hweightNonnegative i hi)
      _ = upperBound := by
        rw [← Finset.sum_mul, hweightSum, one_mul]

/-- A normalized nonnegative average of signed-net values formed from two `[0, upperBound]`
components lies in `[-upperBound, upperBound]`. -/
theorem net_weighted_average_bounds
    (indices : Finset ι)
    (weight informative misinformative : ι → ℝ)
    {upperBound : ℝ}
    (hweightNonnegative : ∀ i ∈ indices, 0 ≤ weight i)
    (hweightSum : ∑ i ∈ indices, weight i = 1)
    (hinformative :
      ∀ i ∈ indices, 0 ≤ informative i ∧ informative i ≤ upperBound)
    (hmisinformative :
      ∀ i ∈ indices, 0 ≤ misinformative i ∧ misinformative i ≤ upperBound) :
    -upperBound ≤
        ∑ i ∈ indices, weight i * (informative i - misinformative i) ∧
      ∑ i ∈ indices, weight i * (informative i - misinformative i) ≤
        upperBound := by
  have hnet :
      ∀ i ∈ indices,
        -upperBound ≤ informative i - misinformative i ∧
          informative i - misinformative i ≤ upperBound := by
    intro i hi
    exact net_value_bounds_of_component_bounds
      (hinformative i hi) (hmisinformative i hi)
  constructor
  · calc
      -upperBound =
          ∑ i ∈ indices, weight i * (-upperBound) := by
            rw [← Finset.sum_mul, hweightSum, one_mul]
      _ ≤ ∑ i ∈ indices,
          weight i * (informative i - misinformative i) := by
            apply Finset.sum_le_sum
            intro i hi
            exact mul_le_mul_of_nonneg_left
              (hnet i hi).1 (hweightNonnegative i hi)
  · calc
      ∑ i ∈ indices, weight i * (informative i - misinformative i)
          ≤ ∑ i ∈ indices, weight i * upperBound := by
            apply Finset.sum_le_sum
            intro i hi
            exact mul_le_mul_of_nonneg_left
              (hnet i hi).2 (hweightNonnegative i hi)
      _ = upperBound := by
        rw [← Finset.sum_mul, hweightSum, one_mul]

/-- For equal-total weights, a reference component in `[0, upperBound]` contributes at most
`L1-change * upperBound / 2`. -/
theorem abs_component_weight_change_le_half_range
    (indices : Finset ι) (pWeight qWeight componentP : ι → ℝ)
    {upperBound l1Bound : ℝ}
    (hpSum : ∑ i ∈ indices, pWeight i = 1)
    (hqSum : ∑ i ∈ indices, qWeight i = 1)
    (hupperNonnegative : 0 ≤ upperBound)
    (hl1Nonnegative : 0 ≤ l1Bound)
    (hcomponent :
      ∀ i ∈ indices, 0 ≤ componentP i ∧ componentP i ≤ upperBound)
    (hweightChange :
      ∑ i ∈ indices, |qWeight i - pWeight i| ≤ l1Bound) :
    |∑ i ∈ indices, (qWeight i - pWeight i) * componentP i| ≤
      l1Bound * upperBound / 2 := by
  simpa using
    abs_weight_change_against_bounded_values_le_half_range
      indices pWeight qWeight componentP hpSum hqSum hupperNonnegative
      hl1Nonnegative hcomponent hweightChange

/-- For equal-total weights, a reference net formed from two components in `[0, upperBound]`
contributes at most `L1-change * upperBound`. -/
theorem abs_net_weight_change_le_range
    (indices : Finset ι)
    (pWeight qWeight informativeP misinformativeP : ι → ℝ)
    {upperBound l1Bound : ℝ}
    (hpSum : ∑ i ∈ indices, pWeight i = 1)
    (hqSum : ∑ i ∈ indices, qWeight i = 1)
    (hupperNonnegative : 0 ≤ upperBound)
    (hl1Nonnegative : 0 ≤ l1Bound)
    (hinformative :
      ∀ i ∈ indices, 0 ≤ informativeP i ∧ informativeP i ≤ upperBound)
    (hmisinformative :
      ∀ i ∈ indices, 0 ≤ misinformativeP i ∧ misinformativeP i ≤ upperBound)
    (hweightChange :
      ∑ i ∈ indices, |qWeight i - pWeight i| ≤ l1Bound) :
    |∑ i ∈ indices,
        (qWeight i - pWeight i) *
          (informativeP i - misinformativeP i)| ≤
      l1Bound * upperBound := by
  have hnet :
      ∀ i ∈ indices,
        -upperBound ≤ informativeP i - misinformativeP i ∧
          informativeP i - misinformativeP i ≤ upperBound := by
    intro i hi
    exact net_value_bounds_of_component_bounds
      (hinformative i hi) (hmisinformative i hi)
  have hbound :=
    abs_weight_change_against_bounded_values_le_half_range
      indices pWeight qWeight
      (fun i => informativeP i - misinformativeP i)
      hpSum hqSum (by linarith) hl1Nonnegative hnet hweightChange
  convert hbound using 1
  ring

/-- A component-valued finite average combines a pointwise change with the sharper component
half-range weight term. -/
theorem abs_component_average_change_le
    (indices : Finset ι)
    (pWeight qWeight componentP componentQ : ι → ℝ)
    {upperBound pointwiseBound l1Bound : ℝ}
    (hqNonnegative : ∀ i ∈ indices, 0 ≤ qWeight i)
    (hpSum : ∑ i ∈ indices, pWeight i = 1)
    (hqSum : ∑ i ∈ indices, qWeight i = 1)
    (hupperNonnegative : 0 ≤ upperBound)
    (hpointwiseNonnegative : 0 ≤ pointwiseBound)
    (hl1Nonnegative : 0 ≤ l1Bound)
    (hchange :
      ∀ i ∈ indices, |componentQ i - componentP i| ≤ pointwiseBound)
    (hcomponent :
      ∀ i ∈ indices, 0 ≤ componentP i ∧ componentP i ≤ upperBound)
    (hweightChange :
      ∑ i ∈ indices, |qWeight i - pWeight i| ≤ l1Bound) :
    |(∑ i ∈ indices, qWeight i * componentQ i) -
        ∑ i ∈ indices, pWeight i * componentP i| ≤
      pointwiseBound + l1Bound * upperBound / 2 := by
  simpa using
    abs_weighted_average_change_le_pointwise_plus_half_range
      indices pWeight qWeight componentP componentQ
      hqNonnegative hpSum hqSum hupperNonnegative
      hpointwiseNonnegative hl1Nonnegative hchange hcomponent hweightChange

/-- A signed-net finite average combines a pointwise change with the full `L1-change * upperBound`
weight term implied by two bounded components. -/
theorem abs_net_average_change_le
    (indices : Finset ι)
    (pWeight qWeight informativeP misinformativeP netQ : ι → ℝ)
    {upperBound pointwiseBound l1Bound : ℝ}
    (hqNonnegative : ∀ i ∈ indices, 0 ≤ qWeight i)
    (hpSum : ∑ i ∈ indices, pWeight i = 1)
    (hqSum : ∑ i ∈ indices, qWeight i = 1)
    (hupperNonnegative : 0 ≤ upperBound)
    (hpointwiseNonnegative : 0 ≤ pointwiseBound)
    (hl1Nonnegative : 0 ≤ l1Bound)
    (hchange :
      ∀ i ∈ indices,
        |netQ i - (informativeP i - misinformativeP i)| ≤ pointwiseBound)
    (hinformative :
      ∀ i ∈ indices, 0 ≤ informativeP i ∧ informativeP i ≤ upperBound)
    (hmisinformative :
      ∀ i ∈ indices, 0 ≤ misinformativeP i ∧ misinformativeP i ≤ upperBound)
    (hweightChange :
      ∑ i ∈ indices, |qWeight i - pWeight i| ≤ l1Bound) :
    |(∑ i ∈ indices, qWeight i * netQ i) -
        ∑ i ∈ indices,
          pWeight i * (informativeP i - misinformativeP i)| ≤
      pointwiseBound + l1Bound * upperBound := by
  have hnet :
      ∀ i ∈ indices,
        -upperBound ≤ informativeP i - misinformativeP i ∧
          informativeP i - misinformativeP i ≤ upperBound := by
    intro i hi
    exact net_value_bounds_of_component_bounds
      (hinformative i hi) (hmisinformative i hi)
  have hbound :=
    abs_weighted_average_change_le_pointwise_plus_half_range
      indices pWeight qWeight
      (fun i => informativeP i - misinformativeP i) netQ
      hqNonnegative hpSum hqSum (by linarith)
      hpointwiseNonnegative hl1Nonnegative hchange hnet hweightChange
  convert hbound using 1
  ring

/-- A component average of one fixed linear row obeys the row-transferred coordinate bound plus
the component half-range weight term. The component range remains an explicit premise. -/
theorem abs_component_linear_row_average_change_le
    (cells : Finset ι) (coordinates : Finset κ)
    (pWeight qWeight : ι → ℝ) (coefficient : κ → ℝ)
    (valueP valueQ : ι → κ → ℝ)
    {upperBound coordinateBound l1Bound : ℝ}
    (hqNonnegative : ∀ cell ∈ cells, 0 ≤ qWeight cell)
    (hpSum : ∑ cell ∈ cells, pWeight cell = 1)
    (hqSum : ∑ cell ∈ cells, qWeight cell = 1)
    (hupperNonnegative : 0 ≤ upperBound)
    (hcoordinateNonnegative : 0 ≤ coordinateBound)
    (hl1Nonnegative : 0 ≤ l1Bound)
    (hcoordinateChange :
      ∀ cell ∈ cells, ∀ coordinate ∈ coordinates,
        |valueQ cell coordinate - valueP cell coordinate| ≤ coordinateBound)
    (hcomponentRange :
      ∀ cell ∈ cells,
        0 ≤ ∑ coordinate ∈ coordinates,
            coefficient coordinate * valueP cell coordinate ∧
          (∑ coordinate ∈ coordinates,
            coefficient coordinate * valueP cell coordinate) ≤ upperBound)
    (hweightChange :
      ∑ cell ∈ cells, |qWeight cell - pWeight cell| ≤ l1Bound) :
    |(∑ cell ∈ cells, qWeight cell *
          ∑ coordinate ∈ coordinates,
            coefficient coordinate * valueQ cell coordinate) -
        ∑ cell ∈ cells, pWeight cell *
          ∑ coordinate ∈ coordinates,
            coefficient coordinate * valueP cell coordinate| ≤
      (∑ coordinate ∈ coordinates, |coefficient coordinate|) *
          coordinateBound +
        l1Bound * upperBound / 2 := by
  apply abs_component_average_change_le
    cells pWeight qWeight
    (fun cell =>
      ∑ coordinate ∈ coordinates,
        coefficient coordinate * valueP cell coordinate)
    (fun cell =>
      ∑ coordinate ∈ coordinates,
        coefficient coordinate * valueQ cell coordinate)
    hqNonnegative hpSum hqSum hupperNonnegative
    (mul_nonneg
      (Finset.sum_nonneg fun coordinate _ => abs_nonneg (coefficient coordinate))
      hcoordinateNonnegative)
    hl1Nonnegative
  · intro cell hcell
    exact abs_mobius_row_change_le_abs_row_sum
      coordinates coefficient (valueP cell) (valueQ cell)
      (hcoordinateChange cell hcell)
  · exact hcomponentRange
  · exact hweightChange

/-- A net average of one fixed linear row obeys the row-transferred coordinate bound plus the full
net weight term. The two reference-component ranges remain explicit premises. -/
theorem abs_net_linear_row_average_change_le
    (cells : Finset ι) (coordinates : Finset κ)
    (pWeight qWeight : ι → ℝ) (coefficient : κ → ℝ)
    (informativeP misinformativeP : ι → ℝ)
    (netCoordinateP netCoordinateQ : ι → κ → ℝ)
    {upperBound coordinateBound l1Bound : ℝ}
    (hqNonnegative : ∀ cell ∈ cells, 0 ≤ qWeight cell)
    (hpSum : ∑ cell ∈ cells, pWeight cell = 1)
    (hqSum : ∑ cell ∈ cells, qWeight cell = 1)
    (hupperNonnegative : 0 ≤ upperBound)
    (hcoordinateNonnegative : 0 ≤ coordinateBound)
    (hl1Nonnegative : 0 ≤ l1Bound)
    (hcoordinateChange :
      ∀ cell ∈ cells, ∀ coordinate ∈ coordinates,
        |netCoordinateQ cell coordinate - netCoordinateP cell coordinate| ≤
          coordinateBound)
    (hnetRowP :
      ∀ cell ∈ cells,
        (∑ coordinate ∈ coordinates,
          coefficient coordinate * netCoordinateP cell coordinate) =
            informativeP cell - misinformativeP cell)
    (hinformative :
      ∀ cell ∈ cells,
        0 ≤ informativeP cell ∧ informativeP cell ≤ upperBound)
    (hmisinformative :
      ∀ cell ∈ cells,
        0 ≤ misinformativeP cell ∧ misinformativeP cell ≤ upperBound)
    (hweightChange :
      ∑ cell ∈ cells, |qWeight cell - pWeight cell| ≤ l1Bound) :
    |(∑ cell ∈ cells, qWeight cell *
          ∑ coordinate ∈ coordinates,
            coefficient coordinate * netCoordinateQ cell coordinate) -
        ∑ cell ∈ cells, pWeight cell *
          ∑ coordinate ∈ coordinates,
            coefficient coordinate * netCoordinateP cell coordinate| ≤
      (∑ coordinate ∈ coordinates, |coefficient coordinate|) *
          coordinateBound +
        l1Bound * upperBound := by
  have hchange :
      ∀ cell ∈ cells,
        |(∑ coordinate ∈ coordinates,
            coefficient coordinate * netCoordinateQ cell coordinate) -
          (informativeP cell - misinformativeP cell)| ≤
        (∑ coordinate ∈ coordinates, |coefficient coordinate|) *
          coordinateBound := by
    intro cell hcell
    rw [← hnetRowP cell hcell]
    exact abs_mobius_row_change_le_abs_row_sum
      coordinates coefficient (netCoordinateP cell) (netCoordinateQ cell)
      (hcoordinateChange cell hcell)
  have hbound := abs_net_average_change_le
    cells pWeight qWeight informativeP misinformativeP
    (fun cell =>
      ∑ coordinate ∈ coordinates,
        coefficient coordinate * netCoordinateQ cell coordinate)
    hqNonnegative hpSum hqSum hupperNonnegative
    (mul_nonneg
      (Finset.sum_nonneg fun coordinate _ => abs_nonneg (coefficient coordinate))
      hcoordinateNonnegative)
    hl1Nonnegative hchange hinformative hmisinformative hweightChange
  convert hbound using 1
  · apply congrArg abs
    congr 1
    apply Finset.sum_congr rfl
    intro cell hcell
    rw [hnetRowP cell hcell]

/-- An event mass on the segment from `referenceMass` to `nearbyMass` has the factorized floor
`floorMass * (1 - time * error / (2 * floorMass))`. -/
theorem segment_event_mass_lower_bound_factorized
    {referenceMass nearbyMass floorMass error time : ℝ}
    (hfloor : 0 < floorMass)
    (hreference : floorMass ≤ referenceMass)
    (htimeNonnegative : 0 ≤ time)
    (hchange : |nearbyMass - referenceMass| ≤ error / 2) :
    floorMass * (1 - time * (error / (2 * floorMass))) ≤
      (1 - time) * referenceMass + time * nearbyMass := by
  have hlower :
      -(error / 2) ≤ nearbyMass - referenceMass :=
    neg_le_of_abs_le hchange
  have hscaled :
      time * (-(error / 2)) ≤
        time * (nearbyMass - referenceMass) :=
    mul_le_mul_of_nonneg_left hlower htimeNonnegative
  have hfactor :
      floorMass * (1 - time * (error / (2 * floorMass))) =
        floorMass + time * (-(error / 2)) := by
    field_simp
    ring
  rw [hfactor]
  nlinarith

/-- Under the strict support margin, the factorized segment floor is positive for every
`time ∈ [0, 1]`; hence so is the segment mass. -/
theorem segment_event_mass_positive_of_floor
    {referenceMass nearbyMass floorMass error time : ℝ}
    (hfloor : 0 < floorMass)
    (hreference : floorMass ≤ referenceMass)
    (herrorNonnegative : 0 ≤ error)
    (hstrict : error < 2 * floorMass)
    (htimeNonnegative : 0 ≤ time)
    (htimeUpper : time ≤ 1)
    (hchange : |nearbyMass - referenceMass| ≤ error / 2) :
    0 < (1 - time) * referenceMass + time * nearbyMass := by
  have hratioNonnegative : 0 ≤ error / (2 * floorMass) := by positivity
  have hratioLtOne : error / (2 * floorMass) < 1 := by
    exact (div_lt_one (by positivity)).2 hstrict
  have htimeRatioLtOne :
      time * (error / (2 * floorMass)) < 1 := by
    calc
      time * (error / (2 * floorMass))
          ≤ 1 * (error / (2 * floorMass)) :=
            mul_le_mul_of_nonneg_right htimeUpper hratioNonnegative
      _ < 1 := by simpa using hratioLtOne
  have hfactorPositive :
      0 < floorMass *
        (1 - time * (error / (2 * floorMass))) :=
    mul_pos hfloor (sub_pos.mpr htimeRatioLtOne)
  exact hfactorPositive.trans_le
    (segment_event_mass_lower_bound_factorized
      hfloor hreference htimeNonnegative hchange)

end PidFiniteConvergence
