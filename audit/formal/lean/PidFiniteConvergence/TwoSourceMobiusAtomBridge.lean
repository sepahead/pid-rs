import PidFiniteConvergence.TwoSourceCountEventBridge

/-!
# Exact two-source component and Mobius-atom bridge

This module fixes the complete two-source categorical shared-exclusions coordinate surface: four
cumulative nodes, four Mobius atoms, and the informative, misinformative, and signed-net
components.  It proves the concrete two-source Mobius and zeta transforms are inverse, binds their
orders and integer coefficients, proves coordinate-swap equivariance, and proves that the finite
empirical average commutes with the concrete Mobius transform.  It also fixes the exact 24-item
coordinate order used by the separately reviewed categorical SxPID2 certificate route.

The mathematics here is about the paper-defined finite categorical functional after its keyed
events and empirical law have been supplied.  It does not verify row-to-count extraction, the Rust
`NODES2` or `invert2` implementations, certificate schemas or parsers, binary64 logarithms or
summation, resource behavior, sampling or population claims, component nonnegativity, higher-source
lattices, or scientific priority.  Exact count/log/product normalization is layered below these
algebraic statements rather than inferred from executable agreement.
-/

set_option autoImplicit false
set_option warningAsError true

open scoped BigOperators

namespace PidFiniteConvergence

universe v w

/-- The three paper-defined component kinds carried by every cumulative and atom. -/
inductive SxPid2Component where
  | informative
  | misinformative
  | net
deriving DecidableEq, Fintype

/-- The four two-source Mobius atoms in the certificate and Rust result order. -/
inductive SxPid2Atom where
  | uniqueOne
  | uniqueTwo
  | synergy
  | redundancy
deriving DecidableEq, Fintype

/-- The complete two-source averaged coordinate surface. -/
inductive SxPid2Coordinate where
  | cumulative (component : SxPid2Component) (node : SxPid2Node)
  | atom (component : SxPid2Component) (atom : SxPid2Atom)
deriving DecidableEq, Fintype

/-- Exact cumulative-node order: source one, source two, joint sources, redundancy. -/
def sxPid2NodeOrder : List SxPid2Node :=
  [.sourceOne, .sourceTwo, .jointSources, .redundancy]

/-- Exact atom order: unique one, unique two, synergy, redundancy. -/
def sxPid2AtomOrder : List SxPid2Atom :=
  [.uniqueOne, .uniqueTwo, .synergy, .redundancy]

/-- Exact component order: informative, misinformative, signed net. -/
def sxPid2ComponentOrder : List SxPid2Component :=
  [.informative, .misinformative, .net]

/-- Exact 24-coordinate certificate order: kind, then component, then lattice coordinate. -/
def sxPid2CoordinateOrder : List SxPid2Coordinate :=
  [
    .cumulative .informative .sourceOne,
    .cumulative .informative .sourceTwo,
    .cumulative .informative .jointSources,
    .cumulative .informative .redundancy,
    .cumulative .misinformative .sourceOne,
    .cumulative .misinformative .sourceTwo,
    .cumulative .misinformative .jointSources,
    .cumulative .misinformative .redundancy,
    .cumulative .net .sourceOne,
    .cumulative .net .sourceTwo,
    .cumulative .net .jointSources,
    .cumulative .net .redundancy,
    .atom .informative .uniqueOne,
    .atom .informative .uniqueTwo,
    .atom .informative .synergy,
    .atom .informative .redundancy,
    .atom .misinformative .uniqueOne,
    .atom .misinformative .uniqueTwo,
    .atom .misinformative .synergy,
    .atom .misinformative .redundancy,
    .atom .net .uniqueOne,
    .atom .net .uniqueTwo,
    .atom .net .synergy,
    .atom .net .redundancy
  ]

theorem sx_pid2_node_order_length : sxPid2NodeOrder.length = 4 := by
  rfl

theorem sx_pid2_atom_order_length : sxPid2AtomOrder.length = 4 := by
  rfl

theorem sx_pid2_component_order_length : sxPid2ComponentOrder.length = 3 := by
  rfl

theorem sx_pid2_coordinate_order_length : sxPid2CoordinateOrder.length = 24 := by
  rfl

theorem sx_pid2_coordinate_order_nodup : sxPid2CoordinateOrder.Nodup := by
  decide

theorem sx_pid2_coordinate_order_complete :
    sxPid2CoordinateOrder.toFinset = (Finset.univ : Finset SxPid2Coordinate) := by
  decide

theorem sx_pid2_coordinate_card : Fintype.card SxPid2Coordinate = 24 := by
  decide

/-- Integer coefficient of one cumulative in one concrete two-source Mobius atom. -/
def sxPid2MobiusCoefficient : SxPid2Atom → SxPid2Node → ℤ
  | .uniqueOne, .sourceOne => 1
  | .uniqueOne, .redundancy => -1
  | .uniqueTwo, .sourceTwo => 1
  | .uniqueTwo, .redundancy => -1
  | .synergy, .sourceOne => -1
  | .synergy, .sourceTwo => -1
  | .synergy, .jointSources => 1
  | .synergy, .redundancy => 1
  | .redundancy, .redundancy => 1
  | _, _ => 0

/-- Integer coefficient of one atom in one concrete two-source zeta cumulative. -/
def sxPid2ZetaCoefficient : SxPid2Node → SxPid2Atom → ℤ
  | .sourceOne, .uniqueOne => 1
  | .sourceOne, .redundancy => 1
  | .sourceTwo, .uniqueTwo => 1
  | .sourceTwo, .redundancy => 1
  | .jointSources, _ => 1
  | .redundancy, .redundancy => 1
  | _, _ => 0

/-- Concrete two-source Mobius inversion in atom order `[U1, U2, S, R]`. -/
def sxPid2MobiusTransform {G : Type*} [AddCommGroup G]
    (cumulative : SxPid2Node → G) : SxPid2Atom → G
  | .uniqueOne => cumulative .sourceOne - cumulative .redundancy
  | .uniqueTwo => cumulative .sourceTwo - cumulative .redundancy
  | .synergy =>
      cumulative .jointSources - cumulative .sourceOne - cumulative .sourceTwo +
        cumulative .redundancy
  | .redundancy => cumulative .redundancy

/-- Concrete two-source zeta reconstruction in node order `[C1, C2, C12, CR]`. -/
def sxPid2ZetaTransform {G : Type*} [AddCommGroup G]
    (atom : SxPid2Atom → G) : SxPid2Node → G
  | .sourceOne => atom .uniqueOne + atom .redundancy
  | .sourceTwo => atom .uniqueTwo + atom .redundancy
  | .jointSources =>
      atom .uniqueOne + atom .uniqueTwo + atom .synergy + atom .redundancy
  | .redundancy => atom .redundancy

theorem sx_pid2_mobius_transform_eq_integer_row_sum
    {G : Type*} [AddCommGroup G]
    (cumulative : SxPid2Node → G) (atom : SxPid2Atom) :
    sxPid2MobiusTransform cumulative atom =
      ∑ node, sxPid2MobiusCoefficient atom node • cumulative node := by
  have hnodes : (Finset.univ : Finset SxPid2Node) = sxPid2NodeOrder.toFinset := by
    decide
  rw [hnodes]
  cases atom <;>
    simp [sxPid2NodeOrder, sxPid2MobiusTransform, sxPid2MobiusCoefficient] <;>
    abel

theorem sx_pid2_zeta_transform_eq_integer_row_sum
    {G : Type*} [AddCommGroup G]
    (atom : SxPid2Atom → G) (node : SxPid2Node) :
    sxPid2ZetaTransform atom node =
      ∑ coordinate, sxPid2ZetaCoefficient node coordinate • atom coordinate := by
  have hatoms : (Finset.univ : Finset SxPid2Atom) = sxPid2AtomOrder.toFinset := by
    decide
  rw [hatoms]
  cases node <;>
    simp [sxPid2AtomOrder, sxPid2ZetaTransform, sxPid2ZetaCoefficient]
  all_goals abel

theorem sx_pid2_zeta_after_mobius
    {G : Type*} [AddCommGroup G]
    (cumulative : SxPid2Node → G) (node : SxPid2Node) :
    sxPid2ZetaTransform (sxPid2MobiusTransform cumulative) node = cumulative node := by
  cases node
  all_goals simp [sxPid2ZetaTransform, sxPid2MobiusTransform] <;> abel

theorem sx_pid2_mobius_after_zeta
    {G : Type*} [AddCommGroup G]
    (atom : SxPid2Atom → G) (coordinate : SxPid2Atom) :
    sxPid2MobiusTransform (sxPid2ZetaTransform atom) coordinate = atom coordinate := by
  cases coordinate
  all_goals simp [sxPid2MobiusTransform, sxPid2ZetaTransform] <;> abel

theorem sx_pid2_joint_cumulative_eq_sum_atoms
    {G : Type*} [AddCommGroup G]
    (cumulative : SxPid2Node → G) :
    cumulative .jointSources =
      sxPid2MobiusTransform cumulative .uniqueOne +
        sxPid2MobiusTransform cumulative .uniqueTwo +
          sxPid2MobiusTransform cumulative .synergy +
            sxPid2MobiusTransform cumulative .redundancy := by
  rw [← sx_pid2_zeta_after_mobius cumulative .jointSources]
  rfl

theorem sx_pid2_source_one_cumulative_eq_unique_one_add_redundancy
    {G : Type*} [AddCommGroup G]
    (cumulative : SxPid2Node → G) :
    cumulative .sourceOne =
      sxPid2MobiusTransform cumulative .uniqueOne +
        sxPid2MobiusTransform cumulative .redundancy := by
  rw [← sx_pid2_zeta_after_mobius cumulative .sourceOne]
  rfl

theorem sx_pid2_source_two_cumulative_eq_unique_two_add_redundancy
    {G : Type*} [AddCommGroup G]
    (cumulative : SxPid2Node → G) :
    cumulative .sourceTwo =
      sxPid2MobiusTransform cumulative .uniqueTwo +
        sxPid2MobiusTransform cumulative .redundancy := by
  rw [← sx_pid2_zeta_after_mobius cumulative .sourceTwo]
  rfl

theorem sx_pid2_mobius_row_sum
    (atom : SxPid2Atom) :
    ∑ node, sxPid2MobiusCoefficient atom node =
      if atom = .redundancy then 1 else 0 := by
  cases atom <;> decide

/-- Exchange the two source-labelled coordinate positions on cumulative nodes. -/
def sxPid2SwapNode : SxPid2Node → SxPid2Node
  | .sourceOne => .sourceTwo
  | .sourceTwo => .sourceOne
  | .jointSources => .jointSources
  | .redundancy => .redundancy

/-- Exchange the two source-labelled coordinate positions on atoms. -/
def sxPid2SwapAtom : SxPid2Atom → SxPid2Atom
  | .uniqueOne => .uniqueTwo
  | .uniqueTwo => .uniqueOne
  | .synergy => .synergy
  | .redundancy => .redundancy

theorem sx_pid2_swap_node_involution (node : SxPid2Node) :
    sxPid2SwapNode (sxPid2SwapNode node) = node := by
  cases node <;> rfl

theorem sx_pid2_swap_atom_involution (atom : SxPid2Atom) :
    sxPid2SwapAtom (sxPid2SwapAtom atom) = atom := by
  cases atom <;> rfl

theorem sx_pid2_mobius_coordinate_swap_equivariant
    {G : Type*} [AddCommGroup G]
    (cumulative : SxPid2Node → G) (atom : SxPid2Atom) :
    sxPid2MobiusTransform (fun node => cumulative (sxPid2SwapNode node)) atom =
      sxPid2MobiusTransform cumulative (sxPid2SwapAtom atom) := by
  cases atom
  all_goals simp [sxPid2MobiusTransform, sxPid2SwapNode, sxPid2SwapAtom] <;> abel

theorem sx_pid2_mobius_sub
    {G : Type*} [AddCommGroup G]
    (left right : SxPid2Node → G) (atom : SxPid2Atom) :
    sxPid2MobiusTransform (fun node => left node - right node) atom =
      sxPid2MobiusTransform left atom - sxPid2MobiusTransform right atom := by
  cases atom <;> simp [sxPid2MobiusTransform] <;> abel

/-- One local cumulative selected by component kind. -/
noncomputable def localCumulativeComponent
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (component : SxPid2Component) (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) : ℝ :=
  match component with
  | .informative => localCumulativeInformative law node anchor
  | .misinformative => localCumulativeMisinformative law node anchor
  | .net => localCumulativeNet law node anchor

/-- Support-restricted weighted sum of one selected cumulative component.

For a normalized nonnegative `law`, this has the empirical-average interpretation.  The generic
definition itself assumes neither normalization nor nonnegativity. -/
noncomputable def averagedCumulativeComponent
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (component : SxPid2Component) (node : SxPid2Node) : ℝ :=
  ∑ anchor ∈ positiveMassSupport law,
    law anchor * localCumulativeComponent law component node anchor

/-- Local Mobius atom obtained from the four local cumulatives of one component. -/
noncomputable def localAtomComponent
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (component : SxPid2Component) (atom : SxPid2Atom)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) : ℝ :=
  sxPid2MobiusTransform
    (fun node => localCumulativeComponent law component node anchor) atom

/-- Support-restricted weighted sum of pointwise Mobius atoms.

For a normalized nonnegative `law`, this has the empirical-average interpretation.  The generic
definition itself assumes neither normalization nor nonnegativity. -/
noncomputable def averagedPointwiseAtomComponent
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (component : SxPid2Component) (atom : SxPid2Atom) : ℝ :=
  ∑ anchor ∈ positiveMassSupport law,
    law anchor * localAtomComponent law component atom anchor

/-- Concrete Mobius transform of the four support-restricted cumulative weighted sums. -/
noncomputable def averagedAtomComponent
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (component : SxPid2Component) (atom : SxPid2Atom) : ℝ :=
  sxPid2MobiusTransform (averagedCumulativeComponent law component) atom

theorem local_cumulative_net_component_eq_sub
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) :
    localCumulativeComponent law .net node anchor =
      localCumulativeComponent law .informative node anchor -
        localCumulativeComponent law .misinformative node anchor := by
  rfl

theorem averaged_cumulative_net_component_eq_sub
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (node : SxPid2Node) :
    averagedCumulativeComponent law .net node =
      averagedCumulativeComponent law .informative node -
        averagedCumulativeComponent law .misinformative node := by
  simp [averagedCumulativeComponent, local_cumulative_net_component_eq_sub,
    mul_sub, Finset.sum_sub_distrib]

theorem averaged_pointwise_atom_eq_mobius_of_averaged_cumulatives
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (component : SxPid2Component) (atom : SxPid2Atom) :
    averagedPointwiseAtomComponent law component atom =
      averagedAtomComponent law component atom := by
  cases atom <;>
    simp [averagedPointwiseAtomComponent, localAtomComponent,
      averagedAtomComponent, sxPid2MobiusTransform, averagedCumulativeComponent,
      mul_add, mul_sub, Finset.sum_add_distrib, Finset.sum_sub_distrib]

theorem averaged_atom_net_component_eq_sub
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ)
    (atom : SxPid2Atom) :
    averagedAtomComponent law .net atom =
      averagedAtomComponent law .informative atom -
        averagedAtomComponent law .misinformative atom := by
  unfold averagedAtomComponent
  rw [← sx_pid2_mobius_sub]
  congr 1
  funext node
  exact averaged_cumulative_net_component_eq_sub law node

/-- One of the exact 24 averaged component coordinates. -/
noncomputable def averagedSxPid2Coordinate
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (law : CategoricalKey (Fin 2) sourceValue targetValue → ℝ) :
    SxPid2Coordinate → ℝ
  | .cumulative component node => averagedCumulativeComponent law component node
  | .atom component atom => averagedAtomComponent law component atom

/-- Exact rational argument of one local informative cumulative. -/
noncomputable def countInformativeArgument
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) : ℚ :=
  (totalCount count : ℚ) /
    (eventCount count (sxPid2SourceEvent node anchor) : ℚ)

/-- Exact rational argument of one local misinformative cumulative. -/
noncomputable def countMisinformativeArgument
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) : ℚ :=
  (eventCount count (targetBranchEvent anchor) : ℚ) /
    (eventCount count (sxPid2TargetRestrictedEvent node anchor) : ℚ)

/-- Exact rational local log argument selected by component kind. -/
noncomputable def countComponentArgument
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (node : SxPid2Node)
    (anchor : CategoricalKey (Fin 2) sourceValue targetValue) : ℚ :=
  match component with
  | .informative => countInformativeArgument count node anchor
  | .misinformative => countMisinformativeArgument count node anchor
  | .net => countNetArgument count node anchor

theorem count_component_argument_positive_on_support
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (node : SxPid2Node)
    {anchor : CategoricalKey (Fin 2) sourceValue targetValue}
    (h_total : 0 < totalCount count)
    (hanchor : anchor ∈ positiveSupport count) :
    0 < countComponentArgument count component node anchor := by
  obtain ⟨hsource, htarget, hrestricted⟩ :=
    sx_pid2_event_counts_positive_on_support count node hanchor
  cases component
  · unfold countComponentArgument countInformativeArgument
    positivity
  · unfold countComponentArgument countMisinformativeArgument
    positivity
  · simpa [countComponentArgument] using
      count_net_argument_positive_on_support count node h_total hanchor

theorem count_net_argument_eq_informative_div_misinformative
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    {anchor : CategoricalKey (Fin 2) sourceValue targetValue}
    (h_total : 0 < totalCount count)
    (hanchor : anchor ∈ positiveSupport count) :
    countComponentArgument count .net node anchor =
      countComponentArgument count .informative node anchor /
        countComponentArgument count .misinformative node anchor := by
  obtain ⟨hsource, htarget, hrestricted⟩ :=
    sx_pid2_event_counts_positive_on_support count node hanchor
  unfold countComponentArgument countInformativeArgument countMisinformativeArgument
    countNetArgument
  field_simp

theorem local_cumulative_informative_empirical_eq_log_count_argument
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    {anchor : CategoricalKey (Fin 2) sourceValue targetValue}
    (h_total : 0 < totalCount count)
    (hanchor : anchor ∈ positiveSupport count) :
    localCumulativeInformative (empiricalLaw count) node anchor =
      Real.log ((countInformativeArgument count node anchor : ℚ) : ℝ) := by
  obtain ⟨hsource, _, _⟩ :=
    sx_pid2_event_counts_positive_on_support count node hanchor
  have htotalReal : (0 : ℝ) < totalCount count := by
    exact_mod_cast h_total
  have hsourceReal : (0 : ℝ) <
      eventCount count (sxPid2SourceEvent node anchor) := by
    exact_mod_cast hsource
  unfold localCumulativeInformative countInformativeArgument
  rw [event_mass_empirical_law_eq_count_ratio]
  simp only [Rat.cast_div, Rat.cast_natCast]
  rw [Real.log_div hsourceReal.ne' htotalReal.ne']
  rw [Real.log_div htotalReal.ne' hsourceReal.ne']
  ring

theorem local_cumulative_misinformative_empirical_eq_log_count_argument
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    {anchor : CategoricalKey (Fin 2) sourceValue targetValue}
    (h_total : 0 < totalCount count)
    (hanchor : anchor ∈ positiveSupport count) :
    localCumulativeMisinformative (empiricalLaw count) node anchor =
      Real.log ((countMisinformativeArgument count node anchor : ℚ) : ℝ) := by
  obtain ⟨_, htarget, hrestricted⟩ :=
    sx_pid2_event_counts_positive_on_support count node hanchor
  have htotalReal : (totalCount count : ℝ) ≠ 0 := by
    exact_mod_cast h_total.ne'
  have hrestrictedReal :
      (eventCount count (sxPid2TargetRestrictedEvent node anchor) : ℝ) ≠ 0 := by
    exact_mod_cast hrestricted.ne'
  unfold localCumulativeMisinformative countMisinformativeArgument
  simp only [event_mass_empirical_law_eq_count_ratio, Rat.cast_div, Rat.cast_natCast]
  congr 1
  field_simp

theorem local_cumulative_component_empirical_eq_log_count_argument
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (node : SxPid2Node)
    {anchor : CategoricalKey (Fin 2) sourceValue targetValue}
    (h_total : 0 < totalCount count)
    (hanchor : anchor ∈ positiveSupport count) :
    localCumulativeComponent (empiricalLaw count) component node anchor =
      Real.log ((countComponentArgument count component node anchor : ℚ) : ℝ) := by
  cases component
  · exact local_cumulative_informative_empirical_eq_log_count_argument
      count node h_total hanchor
  · exact local_cumulative_misinformative_empirical_eq_log_count_argument
      count node h_total hanchor
  · exact local_cumulative_net_empirical_eq_log_count_net_argument
      count node h_total hanchor

/-- Exact supplied-count log expression for one averaged cumulative component. -/
noncomputable def averagedCumulativeCountExpression
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (node : SxPid2Node) : ℝ :=
  ∑ anchor ∈ positiveSupport count,
    ((count anchor : ℝ) / (totalCount count : ℝ)) *
      Real.log ((countComponentArgument count component node anchor : ℚ) : ℝ)

/-- Exact supplied-count log expression for one averaged atom component. -/
noncomputable def averagedAtomCountExpression
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (atom : SxPid2Atom) : ℝ :=
  sxPid2MobiusTransform (averagedCumulativeCountExpression count component) atom

/-- Exact supplied-count log expression selected from the complete 24-coordinate surface. -/
noncomputable def sxPid2CountCoordinateExpression
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ) :
    SxPid2Coordinate → ℝ
  | .cumulative component node => averagedCumulativeCountExpression count component node
  | .atom component atom => averagedAtomCountExpression count component atom

theorem averaged_cumulative_component_empirical_eq_count_expression
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (node : SxPid2Node)
    (h_total : 0 < totalCount count) :
    averagedCumulativeComponent (empiricalLaw count) component node =
      averagedCumulativeCountExpression count component node := by
  unfold averagedCumulativeComponent averagedCumulativeCountExpression
  rw [positive_mass_support_empirical_law count h_total]
  apply Finset.sum_congr rfl
  intro anchor hanchor
  rw [local_cumulative_component_empirical_eq_log_count_argument
    count component node h_total hanchor]
  rfl

theorem averaged_atom_component_empirical_eq_count_expression
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (atom : SxPid2Atom)
    (h_total : 0 < totalCount count) :
    averagedAtomComponent (empiricalLaw count) component atom =
      averagedAtomCountExpression count component atom := by
  unfold averagedAtomComponent averagedAtomCountExpression
  congr 1
  funext node
  exact averaged_cumulative_component_empirical_eq_count_expression
    count component node h_total

theorem all_24_averaged_coordinates_empirical_eq_count_expression
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (coordinate : SxPid2Coordinate)
    (h_total : 0 < totalCount count) :
    averagedSxPid2Coordinate (empiricalLaw count) coordinate =
      sxPid2CountCoordinateExpression count coordinate := by
  cases coordinate with
  | cumulative component node =>
      exact averaged_cumulative_component_empirical_eq_count_expression
        count component node h_total
  | atom component atom =>
      exact averaged_atom_component_empirical_eq_count_expression
        count component atom h_total

/-- Positive real product of exact rational local arguments for one cumulative. -/
noncomputable def countCumulativeRealProduct
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (node : SxPid2Node) : ℝ :=
  ∏ anchor ∈ positiveSupport count,
    ((countComponentArgument count component node anchor : ℚ) : ℝ) ^ count anchor

/-- Exact rational counterpart of `countCumulativeRealProduct`. -/
noncomputable def countCumulativeRationalProduct
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (node : SxPid2Node) : ℚ :=
  ∏ anchor ∈ positiveSupport count,
    countComponentArgument count component node anchor ^ count anchor

/-- Multiplicative Mobius transform of the four cumulative products. -/
noncomputable def countAtomRealProduct
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) : SxPid2Atom → ℝ
  | .uniqueOne =>
      countCumulativeRealProduct count component .sourceOne /
        countCumulativeRealProduct count component .redundancy
  | .uniqueTwo =>
      countCumulativeRealProduct count component .sourceTwo /
        countCumulativeRealProduct count component .redundancy
  | .synergy =>
      (countCumulativeRealProduct count component .jointSources *
        countCumulativeRealProduct count component .redundancy) /
          (countCumulativeRealProduct count component .sourceOne *
            countCumulativeRealProduct count component .sourceTwo)
  | .redundancy => countCumulativeRealProduct count component .redundancy

/-- Exact rational counterpart of `countAtomRealProduct`. -/
noncomputable def countAtomRationalProduct
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) : SxPid2Atom → ℚ
  | .uniqueOne =>
      countCumulativeRationalProduct count component .sourceOne /
        countCumulativeRationalProduct count component .redundancy
  | .uniqueTwo =>
      countCumulativeRationalProduct count component .sourceTwo /
        countCumulativeRationalProduct count component .redundancy
  | .synergy =>
      (countCumulativeRationalProduct count component .jointSources *
        countCumulativeRationalProduct count component .redundancy) /
          (countCumulativeRationalProduct count component .sourceOne *
            countCumulativeRationalProduct count component .sourceTwo)
  | .redundancy => countCumulativeRationalProduct count component .redundancy

noncomputable def countCoordinateRealProduct
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ) :
    SxPid2Coordinate → ℝ
  | .cumulative component node => countCumulativeRealProduct count component node
  | .atom component atom => countAtomRealProduct count component atom

noncomputable def countCoordinateRationalProduct
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ) :
    SxPid2Coordinate → ℚ
  | .cumulative component node => countCumulativeRationalProduct count component node
  | .atom component atom => countAtomRationalProduct count component atom

theorem count_cumulative_real_product_positive
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (node : SxPid2Node)
    (h_total : 0 < totalCount count) :
    0 < countCumulativeRealProduct count component node := by
  unfold countCumulativeRealProduct
  apply Finset.prod_pos
  intro anchor hanchor
  exact pow_pos (by
    exact_mod_cast count_component_argument_positive_on_support
      count component node h_total hanchor) _

theorem count_atom_real_product_positive
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (atom : SxPid2Atom)
    (h_total : 0 < totalCount count) :
    0 < countAtomRealProduct count component atom := by
  have hsourceOne := count_cumulative_real_product_positive
    count component .sourceOne h_total
  have hsourceTwo := count_cumulative_real_product_positive
    count component .sourceTwo h_total
  have hjoint := count_cumulative_real_product_positive
    count component .jointSources h_total
  have hreduc := count_cumulative_real_product_positive
    count component .redundancy h_total
  cases atom with
  | uniqueOne =>
      simpa [countAtomRealProduct] using div_pos hsourceOne hreduc
  | uniqueTwo =>
      simpa [countAtomRealProduct] using div_pos hsourceTwo hreduc
  | synergy =>
      simpa [countAtomRealProduct] using
        div_pos (mul_pos hjoint hreduc) (mul_pos hsourceOne hsourceTwo)
  | redundancy =>
      simpa [countAtomRealProduct] using hreduc

theorem count_coordinate_real_product_positive
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (coordinate : SxPid2Coordinate)
    (h_total : 0 < totalCount count) :
    0 < countCoordinateRealProduct count coordinate := by
  cases coordinate with
  | cumulative component node =>
      exact count_cumulative_real_product_positive count component node h_total
  | atom component atom =>
      exact count_atom_real_product_positive count component atom h_total

theorem count_cumulative_real_product_eq_rational_cast
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (node : SxPid2Node) :
    countCumulativeRealProduct count component node =
      ((countCumulativeRationalProduct count component node : ℚ) : ℝ) := by
  simp [countCumulativeRealProduct, countCumulativeRationalProduct]

theorem count_atom_real_product_eq_rational_cast
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (atom : SxPid2Atom) :
    countAtomRealProduct count component atom =
      ((countAtomRationalProduct count component atom : ℚ) : ℝ) := by
  cases atom <;>
    simp [countAtomRealProduct, countAtomRationalProduct,
      count_cumulative_real_product_eq_rational_cast]

theorem count_coordinate_real_product_eq_rational_cast
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (coordinate : SxPid2Coordinate) :
    countCoordinateRealProduct count coordinate =
      ((countCoordinateRationalProduct count coordinate : ℚ) : ℝ) := by
  cases coordinate with
  | cumulative component node =>
      exact count_cumulative_real_product_eq_rational_cast count component node
  | atom component atom =>
      exact count_atom_real_product_eq_rational_cast count component atom

theorem log_count_cumulative_real_product
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (node : SxPid2Node)
    (h_total : 0 < totalCount count) :
    Real.log (countCumulativeRealProduct count component node) =
      ∑ anchor ∈ positiveSupport count,
        (count anchor : ℝ) *
          Real.log ((countComponentArgument count component node anchor : ℚ) : ℝ) := by
  unfold countCumulativeRealProduct
  calc
    Real.log
        (∏ anchor ∈ positiveSupport count,
          ((countComponentArgument count component node anchor : ℚ) : ℝ) ^ count anchor) =
        ∑ anchor ∈ positiveSupport count,
          Real.log
            (((countComponentArgument count component node anchor : ℚ) : ℝ) ^
              count anchor) := by
      apply Real.log_prod
      intro anchor hanchor
      exact pow_ne_zero _ (ne_of_gt (by
        exact_mod_cast count_component_argument_positive_on_support
          count component node h_total hanchor))
    _ = ∑ anchor ∈ positiveSupport count,
        (count anchor : ℝ) *
          Real.log ((countComponentArgument count component node anchor : ℚ) : ℝ) := by
      apply Finset.sum_congr rfl
      intro anchor _
      rw [Real.log_pow]

theorem averaged_cumulative_count_expression_eq_scaled_log_product
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (node : SxPid2Node)
    (h_total : 0 < totalCount count) :
    averagedCumulativeCountExpression count component node =
      (1 / (totalCount count : ℝ)) *
        Real.log (countCumulativeRealProduct count component node) := by
  unfold averagedCumulativeCountExpression
  rw [log_count_cumulative_real_product count component node h_total]
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro anchor _
  ring

theorem averaged_atom_count_expression_eq_scaled_log_product
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (component : SxPid2Component) (atom : SxPid2Atom)
    (h_total : 0 < totalCount count) :
    averagedAtomCountExpression count component atom =
      (1 / (totalCount count : ℝ)) *
        Real.log (countAtomRealProduct count component atom) := by
  have hsourceOne := count_cumulative_real_product_positive
    count component .sourceOne h_total
  have hsourceTwo := count_cumulative_real_product_positive
    count component .sourceTwo h_total
  have hjoint := count_cumulative_real_product_positive
    count component .jointSources h_total
  have hreduc := count_cumulative_real_product_positive
    count component .redundancy h_total
  cases atom
  · unfold averagedAtomCountExpression sxPid2MobiusTransform countAtomRealProduct
    rw [averaged_cumulative_count_expression_eq_scaled_log_product count component .sourceOne]
    rw [averaged_cumulative_count_expression_eq_scaled_log_product count component .redundancy]
    rw [Real.log_div hsourceOne.ne' hreduc.ne']
    · ring
    · exact h_total
    · exact h_total
  · unfold averagedAtomCountExpression sxPid2MobiusTransform countAtomRealProduct
    rw [averaged_cumulative_count_expression_eq_scaled_log_product count component .sourceTwo]
    rw [averaged_cumulative_count_expression_eq_scaled_log_product count component .redundancy]
    rw [Real.log_div hsourceTwo.ne' hreduc.ne']
    · ring
    · exact h_total
    · exact h_total
  · unfold averagedAtomCountExpression sxPid2MobiusTransform countAtomRealProduct
    rw [averaged_cumulative_count_expression_eq_scaled_log_product count component .jointSources]
    rw [averaged_cumulative_count_expression_eq_scaled_log_product count component .sourceOne]
    rw [averaged_cumulative_count_expression_eq_scaled_log_product count component .sourceTwo]
    rw [averaged_cumulative_count_expression_eq_scaled_log_product count component .redundancy]
    rw [Real.log_div (mul_ne_zero hjoint.ne' hreduc.ne')
      (mul_ne_zero hsourceOne.ne' hsourceTwo.ne')]
    rw [Real.log_mul hjoint.ne' hreduc.ne']
    rw [Real.log_mul hsourceOne.ne' hsourceTwo.ne']
    · ring
    · exact h_total
    · exact h_total
    · exact h_total
    · exact h_total
  · unfold averagedAtomCountExpression sxPid2MobiusTransform countAtomRealProduct
    exact averaged_cumulative_count_expression_eq_scaled_log_product
      count component .redundancy h_total

theorem all_24_count_expressions_eq_scaled_log_product
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (coordinate : SxPid2Coordinate)
    (h_total : 0 < totalCount count) :
    sxPid2CountCoordinateExpression count coordinate =
      (1 / (totalCount count : ℝ)) *
        Real.log (countCoordinateRealProduct count coordinate) := by
  cases coordinate with
  | cumulative component node =>
      exact averaged_cumulative_count_expression_eq_scaled_log_product
        count component node h_total
  | atom component atom =>
      exact averaged_atom_count_expression_eq_scaled_log_product
        count component atom h_total

theorem all_24_averaged_coordinates_eq_scaled_log_product
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (coordinate : SxPid2Coordinate)
    (h_total : 0 < totalCount count) :
    averagedSxPid2Coordinate (empiricalLaw count) coordinate =
      (1 / (totalCount count : ℝ)) *
        Real.log (countCoordinateRealProduct count coordinate) := by
  rw [all_24_averaged_coordinates_empirical_eq_count_expression
    count coordinate h_total]
  exact all_24_count_expressions_eq_scaled_log_product count coordinate h_total

theorem all_24_averaged_coordinates_positive_iff_product_gt_one
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (coordinate : SxPid2Coordinate)
    (h_total : 0 < totalCount count) :
    0 < averagedSxPid2Coordinate (empiricalLaw count) coordinate ↔
      1 < countCoordinateRealProduct count coordinate := by
  rw [all_24_averaged_coordinates_eq_scaled_log_product count coordinate h_total]
  have hscale : 0 < (1 / (totalCount count : ℝ)) :=
    one_div_pos.mpr (Nat.cast_pos.mpr h_total)
  rw [mul_pos_iff_of_pos_left hscale]
  exact Real.log_pos_iff
    (count_coordinate_real_product_positive count coordinate h_total).le

theorem all_24_averaged_coordinates_negative_iff_product_lt_one
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (coordinate : SxPid2Coordinate)
    (h_total : 0 < totalCount count) :
    averagedSxPid2Coordinate (empiricalLaw count) coordinate < 0 ↔
      countCoordinateRealProduct count coordinate < 1 := by
  rw [all_24_averaged_coordinates_eq_scaled_log_product count coordinate h_total]
  have hscale : 0 < (1 / (totalCount count : ℝ)) :=
    one_div_pos.mpr (Nat.cast_pos.mpr h_total)
  have hproduct := count_coordinate_real_product_positive count coordinate h_total
  calc
    (1 / (totalCount count : ℝ)) *
          Real.log (countCoordinateRealProduct count coordinate) < 0 ↔
        0 < -((1 / (totalCount count : ℝ)) *
          Real.log (countCoordinateRealProduct count coordinate)) := neg_pos.symm
    _ ↔ 0 < (1 / (totalCount count : ℝ)) *
        (-Real.log (countCoordinateRealProduct count coordinate)) := by ring_nf
    _ ↔ 0 < -Real.log (countCoordinateRealProduct count coordinate) :=
      mul_pos_iff_of_pos_left hscale
    _ ↔ Real.log (countCoordinateRealProduct count coordinate) < 0 := neg_pos
    _ ↔ countCoordinateRealProduct count coordinate < 1 :=
      Real.log_neg_iff hproduct

theorem all_24_averaged_coordinates_zero_iff_product_eq_one
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (coordinate : SxPid2Coordinate)
    (h_total : 0 < totalCount count) :
    averagedSxPid2Coordinate (empiricalLaw count) coordinate = 0 ↔
      countCoordinateRealProduct count coordinate = 1 := by
  rw [all_24_averaged_coordinates_eq_scaled_log_product count coordinate h_total]
  have hscale : (1 / (totalCount count : ℝ)) ≠ 0 :=
    (one_div_pos.mpr (Nat.cast_pos.mpr h_total)).ne'
  constructor
  · intro hzero
    have hlog : Real.log (countCoordinateRealProduct count coordinate) = 0 :=
      (mul_eq_zero.mp hzero).resolve_left hscale
    rcases Real.log_eq_zero.mp hlog with hproductZero | hproductOne | hproductNegOne
    · exact (count_coordinate_real_product_positive
        count coordinate h_total).ne' hproductZero |>.elim
    · exact hproductOne
    · linarith [count_coordinate_real_product_positive count coordinate h_total]
  · intro hproduct
    simp [hproduct]

end PidFiniteConvergence
