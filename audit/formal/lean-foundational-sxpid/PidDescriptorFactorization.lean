import Mathlib.Data.Set.Basic

/-!
# Descriptor-factorization firewall for PID impossibility claims

This module isolates the logical premise needed to transfer a descriptor-collision witness into a
universal reconstruction impossibility.  If an atom assignment factors through a descriptor map,
then equal descriptors force equal atom vectors.  If the target quantity nevertheless differs,
no function of those atoms can reconstruct the target quantity on every system.

The converse scope guard is equally important: if two systems have equal descriptors but a
candidate PID assigns different atom vectors, then that PID does not factor through the descriptor
map.  A reconstruction impossibility proved only for descriptor-factorizing assignments therefore
does not apply to that candidate without another mapping theorem.

This is a generic functional theorem.  It does not formalize shared-exclusions events, the
antichain lattice, the Lyu--Clark--Raviv systems, or the pid-rs implementation.  Those concrete
bindings are supplied by the independent exact-rational checker and Rust regression documented in
`FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md`.
-/

set_option autoImplicit false
set_option warningAsError true

namespace PidDescriptorFactorization

/-- An atom assignment that factors through a descriptor map cannot distinguish systems with the
same descriptor. -/
theorem equal_descriptors_and_factorization_force_equal_atoms
    {sys desc atm : Type*}
    (descriptor : sys → desc)
    (atom : sys → atm)
    (factor : desc → atm)
    (hfactor : ∀ system, atom system = factor (descriptor system))
    {left right : sys}
    (hdescriptor : descriptor left = descriptor right) :
    atom left = atom right := by
  calc
    atom left = factor (descriptor left) := hfactor left
    _ = factor (descriptor right) := congrArg factor hdescriptor
    _ = atom right := (hfactor right).symm

/-- If equal descriptors force equal atoms while the decomposed quantity differs, no universal
function of those atoms reconstructs that quantity. -/
theorem descriptor_collision_blocks_universal_reconstruction
    {sys desc atm qty : Type*}
    (descriptor : sys → desc)
    (atom : sys → atm)
    (quantity : sys → qty)
    (factor : desc → atm)
    (hfactor : ∀ system, atom system = factor (descriptor system))
    {left right : sys}
    (hdescriptor : descriptor left = descriptor right)
    (hquantity : quantity left ≠ quantity right) :
    ¬ ∃ reconstruct : atm → qty,
        ∀ system, reconstruct (atom system) = quantity system := by
  intro hexists
  obtain ⟨reconstruct, hreconstruct⟩ := hexists
  have hatom : atom left = atom right :=
    equal_descriptors_and_factorization_force_equal_atoms
      descriptor atom factor hfactor hdescriptor
  apply hquantity
  calc
    quantity left = reconstruct (atom left) := (hreconstruct left).symm
    _ = reconstruct (atom right) := congrArg reconstruct hatom
    _ = quantity right := hreconstruct right

/-- A candidate atom assignment that distinguishes a descriptor-collision pair cannot factor
through that descriptor map. -/
theorem atom_distinction_refutes_descriptor_factorization
    {sys desc atm : Type*}
    (descriptor : sys → desc)
    (atom : sys → atm)
    {left right : sys}
    (hdescriptor : descriptor left = descriptor right)
    (hatom : atom left ≠ atom right) :
    ¬ ∃ factor : desc → atm,
        ∀ system, atom system = factor (descriptor system) := by
  intro hexists
  obtain ⟨factor, hfactor⟩ := hexists
  apply hatom
  exact equal_descriptors_and_factorization_force_equal_atoms
    descriptor atom factor hfactor hdescriptor

end PidDescriptorFactorization
