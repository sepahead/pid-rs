import PidFiniteConvergence.SxEventBridge

/-!
Proposed definitions and exact obligation types only. No value of an obligation structure is
supplied. This file does not prove the DNF/order theorem or a boundary example. Its signatures
must be elaborated against the pinned dependency closure before a local task freeze.
-/

set_option autoImplicit false
set_option warningAsError true

namespace PidSxDnfOrderContract

open PidFiniteConvergence

universe u v w

def DNF {sourceIndex : Type u}
    (collections : Finset (Finset sourceIndex)) (pattern : sourceIndex → Bool) : Prop :=
  ∃ collection ∈ collections, ∀ source ∈ collection, pattern source = true

def RedundancyLE {sourceIndex : Type u}
    (alpha beta : Finset (Finset sourceIndex)) : Prop :=
  ∀ b ∈ beta, ∃ a ∈ alpha, a ⊆ b

def IsInclusionAntichain {sourceIndex : Type u}
    (collections : Finset (Finset sourceIndex)) : Prop :=
  ∀ a ∈ collections, ∀ b ∈ collections, a ⊆ b → a = b

def EqualityPattern
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [∀ source, DecidableEq (sourceValue source)]
    (anchor candidate : CategoricalKey sourceIndex sourceValue targetValue) :
    sourceIndex → Bool :=
  fun source => decide (anchor.1 source = candidate.1 source)

def RealizesAllPatterns
    {sourceIndex : Type u} {sourceValue : sourceIndex → Type v} {targetValue : Type w}
    [∀ source, DecidableEq (sourceValue source)]
    (anchor : CategoricalKey sourceIndex sourceValue targetValue)
    (domain : Set (CategoricalKey sourceIndex sourceValue targetValue)) : Prop :=
  ∀ pattern : sourceIndex → Bool,
    ∃ candidate ∈ domain, EqualityPattern anchor candidate = pattern

/-- No antichain, nonempty-family, or nonempty-collection premise is present in G1. -/
structure GenericObligations (sourceIndex : Type u) [DecidableEq sourceIndex] : Prop where
  order_iff_dnf (alpha beta : Finset (Finset sourceIndex)) :
    RedundancyLE alpha beta ↔
      ∀ pattern : sourceIndex → Bool, DNF beta pattern → DNF alpha pattern
  antichain_antisymm (alpha beta : Finset (Finset sourceIndex))
      (hAlpha : IsInclusionAntichain alpha) (hBeta : IsInclusionAntichain beta)
      (hAB : RedundancyLE alpha beta) (hBA : RedundancyLE beta alpha) :
    alpha = beta
  dnf_injective_on_antichains (alpha beta : Finset (Finset sourceIndex))
      (hAlpha : IsInclusionAntichain alpha) (hBeta : IsInclusionAntichain beta)
      (hSemantics : ∀ pattern : sourceIndex → Bool, DNF alpha pattern ↔ DNF beta pattern) :
    alpha = beta

structure CategoricalObligations
    (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] : Prop where
  source_event_iff_dnf (collections : Finset (Finset sourceIndex))
      (anchor candidate : CategoricalKey sourceIndex sourceValue targetValue) :
    candidate ∈ sxSourceEvent collections anchor ↔
      DNF collections (EqualityPattern anchor candidate)
  order_implies_source_event_subset (alpha beta : Finset (Finset sourceIndex))
      (anchor : CategoricalKey sourceIndex sourceValue targetValue)
      (hOrder : RedundancyLE alpha beta) :
    sxSourceEvent beta anchor ⊆ sxSourceEvent alpha anchor
  order_iff_implication_on_realizing_domain (alpha beta : Finset (Finset sourceIndex))
      (anchor : CategoricalKey sourceIndex sourceValue targetValue)
      (domain : Set (CategoricalKey sourceIndex sourceValue targetValue))
      (hRealizes : RealizesAllPatterns anchor domain) :
    RedundancyLE alpha beta ↔
      ∀ candidate ∈ domain,
        candidate ∈ sxSourceEvent beta anchor → candidate ∈ sxSourceEvent alpha anchor
  alternate_values_realize_all_patterns
      (anchor : CategoricalKey sourceIndex sourceValue targetValue)
      (alternate : (source : sourceIndex) → sourceValue source)
      (hAlternate : ∀ source, alternate source ≠ anchor.1 source) :
    RealizesAllPatterns anchor Set.univ
  source_event_injective_on_realizing_domain
      (alpha beta : Finset (Finset sourceIndex))
      (hAlpha : IsInclusionAntichain alpha) (hBeta : IsInclusionAntichain beta)
      (anchor : CategoricalKey sourceIndex sourceValue targetValue)
      (domain : Set (CategoricalKey sourceIndex sourceValue targetValue))
      (hRealizes : RealizesAllPatterns anchor domain)
      (hEvents : ∀ candidate ∈ domain,
        candidate ∈ sxSourceEvent alpha anchor ↔ candidate ∈ sxSourceEvent beta anchor) :
    alpha = beta
  order_implies_target_restricted_subset (alpha beta : Finset (Finset sourceIndex))
      (anchor : CategoricalKey sourceIndex sourceValue targetValue)
      (hOrder : RedundancyLE alpha beta) :
    sxTargetRestrictedEvent beta anchor ⊆ sxTargetRestrictedEvent alpha anchor

def singletonLeft : Finset (Finset (Fin 3)) := {{0}}
def singletonRight : Finset (Finset (Fin 3)) := {{1}}
def absorbedFamily : Finset (Finset (Fin 3)) := {{0}, {0, 1}}

def singletonAnchor : CategoricalKey (Fin 3) (fun _ => Unit) Unit :=
  (fun _ => (), ())

def binaryAnchor : CategoricalKey (Fin 3) (fun _ => Bool) Unit :=
  (fun _ => false, ())

def binaryDiagonal : Set (CategoricalKey (Fin 3) (fun _ => Bool) Unit) :=
  {candidate | candidate.1 0 = candidate.1 1 ∧ candidate.1 1 = candidate.1 2}

structure BoundaryObligations : Prop where
  singleton_event_collision :
    IsInclusionAntichain singletonLeft ∧ IsInclusionAntichain singletonRight ∧
    singletonLeft ≠ singletonRight ∧
    ¬ RedundancyLE singletonLeft singletonRight ∧
    ¬ RedundancyLE singletonRight singletonLeft ∧
    sxSourceEvent singletonLeft singletonAnchor = sxSourceEvent singletonRight singletonAnchor
  singleton_not_all_patterns :
    ¬ RealizesAllPatterns singletonAnchor Set.univ
  binary_diagonal_collision :
    (∀ candidate ∈ binaryDiagonal,
      candidate ∈ sxSourceEvent singletonLeft binaryAnchor ↔
        candidate ∈ sxSourceEvent singletonRight binaryAnchor) ∧
    sxSourceEvent singletonLeft binaryAnchor ≠ sxSourceEvent singletonRight binaryAnchor ∧
    ¬ RealizesAllPatterns binaryAnchor binaryDiagonal
  antichain_premise_is_load_bearing :
    ¬ IsInclusionAntichain absorbedFamily ∧
    absorbedFamily ≠ singletonLeft ∧
    RedundancyLE absorbedFamily singletonLeft ∧
    RedundancyLE singletonLeft absorbedFamily ∧
    (∀ pattern : Fin 3 → Bool, DNF absorbedFamily pattern ↔ DNF singletonLeft pattern)

/-- Revision 2: these aliases are receiver-free intended propositions. A candidate theorem
must inhabit each alias without an obligation-structure argument or any other added premise.
The structures above remain a readable checklist, not the external theorem-type authority. -/
abbrev order_iff_dnf_target (sourceIndex : Type u) [DecidableEq sourceIndex] : Prop :=
  ∀ (alpha beta : Finset (Finset sourceIndex)),
  RedundancyLE alpha beta ↔
  ∀ pattern : sourceIndex → Bool, DNF beta pattern → DNF alpha pattern

abbrev antichain_antisymm_target (sourceIndex : Type u) [DecidableEq sourceIndex] : Prop :=
  ∀ (alpha beta : Finset (Finset sourceIndex))
      (_hAlpha : IsInclusionAntichain alpha) (_hBeta : IsInclusionAntichain beta)
      (_hAB : RedundancyLE alpha beta) (_hBA : RedundancyLE beta alpha),
  alpha = beta

abbrev dnf_injective_on_antichains_target (sourceIndex : Type u) [DecidableEq sourceIndex] : Prop :=
  ∀ (alpha beta : Finset (Finset sourceIndex))
      (_hAlpha : IsInclusionAntichain alpha) (_hBeta : IsInclusionAntichain beta)
      (_hSemantics : ∀ pattern : sourceIndex → Bool, DNF alpha pattern ↔ DNF beta pattern),
  alpha = beta

abbrev source_event_iff_dnf_target (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] : Prop :=
  ∀ (collections : Finset (Finset sourceIndex))
      (anchor candidate : CategoricalKey sourceIndex sourceValue targetValue),
  candidate ∈ sxSourceEvent collections anchor ↔
  DNF collections (EqualityPattern anchor candidate)

abbrev order_implies_source_event_subset_target (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] : Prop :=
  ∀ (alpha beta : Finset (Finset sourceIndex))
      (anchor : CategoricalKey sourceIndex sourceValue targetValue)
      (_hOrder : RedundancyLE alpha beta),
  sxSourceEvent beta anchor ⊆ sxSourceEvent alpha anchor

abbrev order_iff_implication_on_realizing_domain_target (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] : Prop :=
  ∀ (alpha beta : Finset (Finset sourceIndex))
      (anchor : CategoricalKey sourceIndex sourceValue targetValue)
      (domain : Set (CategoricalKey sourceIndex sourceValue targetValue))
      (_hRealizes : RealizesAllPatterns anchor domain),
  RedundancyLE alpha beta ↔
  ∀ candidate ∈ domain,
  candidate ∈ sxSourceEvent beta anchor → candidate ∈ sxSourceEvent alpha anchor

abbrev alternate_values_realize_all_patterns_target (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] : Prop :=
  ∀ (anchor : CategoricalKey sourceIndex sourceValue targetValue)
      (alternate : (source : sourceIndex) → sourceValue source)
      (_hAlternate : ∀ source, alternate source ≠ anchor.1 source),
  RealizesAllPatterns anchor Set.univ

abbrev source_event_injective_on_realizing_domain_target (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] : Prop :=
  ∀ (alpha beta : Finset (Finset sourceIndex))
      (_hAlpha : IsInclusionAntichain alpha) (_hBeta : IsInclusionAntichain beta)
      (anchor : CategoricalKey sourceIndex sourceValue targetValue)
      (domain : Set (CategoricalKey sourceIndex sourceValue targetValue))
      (_hRealizes : RealizesAllPatterns anchor domain)
      (_hEvents : ∀ candidate ∈ domain,
        candidate ∈ sxSourceEvent alpha anchor ↔ candidate ∈ sxSourceEvent beta anchor),
  alpha = beta

abbrev order_implies_target_restricted_subset_target (sourceIndex : Type u) (sourceValue : sourceIndex → Type v) (targetValue : Type w)
    [Fintype sourceIndex] [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [DecidableEq sourceIndex] [∀ source, DecidableEq (sourceValue source)]
    [DecidableEq targetValue] : Prop :=
  ∀ (alpha beta : Finset (Finset sourceIndex))
      (anchor : CategoricalKey sourceIndex sourceValue targetValue)
      (_hOrder : RedundancyLE alpha beta),
  sxTargetRestrictedEvent beta anchor ⊆ sxTargetRestrictedEvent alpha anchor

abbrev singleton_event_collision_target : Prop :=
  IsInclusionAntichain singletonLeft ∧ IsInclusionAntichain singletonRight ∧
  singletonLeft ≠ singletonRight ∧
  ¬ RedundancyLE singletonLeft singletonRight ∧
  ¬ RedundancyLE singletonRight singletonLeft ∧
  sxSourceEvent singletonLeft singletonAnchor = sxSourceEvent singletonRight singletonAnchor

abbrev singleton_not_all_patterns_target : Prop :=
  ¬ RealizesAllPatterns singletonAnchor Set.univ

abbrev binary_diagonal_collision_target : Prop :=
  (∀ candidate ∈ binaryDiagonal,
  candidate ∈ sxSourceEvent singletonLeft binaryAnchor ↔
  candidate ∈ sxSourceEvent singletonRight binaryAnchor) ∧
  sxSourceEvent singletonLeft binaryAnchor ≠ sxSourceEvent singletonRight binaryAnchor ∧
  ¬ RealizesAllPatterns binaryAnchor binaryDiagonal

abbrev antichain_premise_is_load_bearing_target : Prop :=
  ¬ IsInclusionAntichain absorbedFamily ∧
  absorbedFamily ≠ singletonLeft ∧
  RedundancyLE absorbedFamily singletonLeft ∧
  RedundancyLE singletonLeft absorbedFamily ∧
  (∀ pattern : Fin 3 → Bool, DNF absorbedFamily pattern ↔ DNF singletonLeft pattern)

end PidSxDnfOrderContract
