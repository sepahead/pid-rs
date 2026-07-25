import Mathlib.Data.ZMod.Basic

/-!
# Adjacent-arrow citation-edge countermodel

This file formalizes the finite exact sequence

`0 → 0 → Z/2 →ⁱᵈ Z/2 → 0`

using additive homomorphisms between `ZMod 1` and `ZMod 2`.  It proves that the three internal
image/kernel equalities hold, the right nonzero arrow is bijective (hence also surjective), the
adjacent arrow is not bijective, and the middle group is nontrivial.

This is only a kernel-checked countermodel to transferring an isomorphism or surjectivity
predicate to an adjacent arrow in an exact sequence.  It does not formalize motivic homotopy,
verify either cited source theorem, establish the source-to-formal-arrow correspondence, or prove
any PID result.  The executable Python checker is another implementation of this same witness;
the two artifacts are not independent mathematical counterexamples.
-/

set_option autoImplicit false
set_option warningAsError true

namespace PidCitationEdgeCountermodel

/-- The zero object used in the retained finite sequence. -/
abbrev ZeroGroup := ZMod 1

/-- The nontrivial middle and right-hand group. -/
abbrev C2 := ZMod 2

/-- The unique additive homomorphism whose value is always zero. -/
def zeroHom (source target : Type*) [AddMonoid source] [AddMonoid target] : source →+ target where
  toFun := fun _ => 0
  map_zero' := rfl
  map_add' := by
    intro _ _
    simp

/-- Exactness at the middle object, stated as equality of image and kernel. -/
def ExactAt
    {left middle right : Type*}
    [AddGroup left] [AddGroup middle] [AddGroup right]
    (incoming : left →+ middle) (outgoing : middle →+ right) : Prop :=
  incoming.range = outgoing.ker

def firstArrow : ZeroGroup →+ ZeroGroup := zeroHom ZeroGroup ZeroGroup

def adjacentArrow : ZeroGroup →+ C2 := zeroHom ZeroGroup C2

def rightArrow : C2 →+ C2 := AddMonoidHom.id C2

def lastArrow : C2 →+ ZeroGroup := zeroHom C2 ZeroGroup

/-- The retained sequence is exact at its first internal zero term. -/
theorem exact_at_internal_zero : ExactAt firstArrow adjacentArrow := by
  change firstArrow.range = adjacentArrow.ker
  ext element
  constructor
  · intro _
    simp [adjacentArrow, zeroHom]
  · intro _
    exact ⟨0, Subsingleton.elim _ _⟩

/-- The retained sequence is exact at its nontrivial middle term. -/
theorem exact_at_middle : ExactAt adjacentArrow rightArrow := by
  change adjacentArrow.range = rightArrow.ker
  ext element
  simp [adjacentArrow, rightArrow, zeroHom, eq_comm]

/-- The retained sequence is exact at its nontrivial right-hand term. -/
theorem exact_at_right : ExactAt rightArrow lastArrow := by
  change rightArrow.range = lastArrow.ker
  ext element
  simp [rightArrow, lastArrow, zeroHom]

/-- The right nonzero arrow is bijective. -/
theorem right_arrow_bijective : Function.Bijective rightArrow := by
  constructor
  · intro left right equality
    exact equality
  · intro value
    exact ⟨value, rfl⟩

/-- The right nonzero arrow is surjective. -/
theorem right_arrow_surjective : Function.Surjective rightArrow :=
  right_arrow_bijective.2

/-- The adjacent arrow from the zero group is not surjective. -/
theorem adjacent_arrow_not_surjective : ¬Function.Surjective adjacentArrow := by
  intro surjective
  obtain ⟨preimage, equality⟩ := surjective (1 : C2)
  have zero_eq_one : (0 : C2) = 1 := by
    change (0 : C2) = 1 at equality
    exact equality
  exact zero_ne_one zero_eq_one

/-- Therefore the adjacent arrow is not bijective. -/
theorem adjacent_arrow_not_bijective : ¬Function.Bijective adjacentArrow := by
  intro bijective
  exact adjacent_arrow_not_surjective bijective.2

/-- The middle group is nontrivial. -/
theorem middle_nontrivial : ∃ value : C2, value ≠ 0 := by
  exact ⟨1, one_ne_zero⟩

/--
The complete local countermodel: exactness does not transfer the right arrow's isomorphism or
surjectivity predicate to its adjacent arrow.
-/
theorem retained_adjacent_arrow_countermodel :
    ExactAt firstArrow adjacentArrow ∧
      ExactAt adjacentArrow rightArrow ∧
      ExactAt rightArrow lastArrow ∧
      Function.Bijective rightArrow ∧
      Function.Surjective rightArrow ∧
      ¬Function.Bijective adjacentArrow ∧
      ¬Function.Surjective adjacentArrow ∧
      ∃ value : C2, value ≠ 0 := by
  exact
    ⟨exact_at_internal_zero,
      exact_at_middle,
      exact_at_right,
      right_arrow_bijective,
      right_arrow_surjective,
      adjacent_arrow_not_bijective,
      adjacent_arrow_not_surjective,
      middle_nontrivial⟩

end PidCitationEdgeCountermodel
