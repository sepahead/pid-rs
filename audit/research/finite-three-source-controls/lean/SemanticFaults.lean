import Contract
import Candidate
import RawTargets
import JudgeCore
import Fault01
import Fault02
import Fault03
import Fault04
import Fault05
import Fault06
import Fault07
import Fault08
import Fault09
import Fault10
import Fault11
import Fault12

set_option autoImplicit false
set_option warningAsError true

-- Exact full original target types and full mutant-target refutations.
-- Each local witness is finite; original proofs are reused byte-exact.
-- This is development evidence about already-known artifacts, with no blind credit.
namespace PidFin3SemanticTargets

-- empty_family_inclusion: An inserted empty family is not an original valid carrier node.
def original01 : Prop := PidFin3RawTargets.carrier_membership
def rejected01 : Prop := ¬ PidFin3Fault01.carrierMembershipTarget

-- empty_branch_inclusion: A family containing the empty branch must remain outside the carrier, even though it is nonempty.
def original02 : Prop := PidFin3RawTargets.carrier_membership
def rejected02 : Prop := ¬ PidFin3Fault02.carrierMembershipTarget

-- missing_valid_node: The generated carrier must contain the valid singleton family {{0}}; cardinality-only recognition is insufficient.
def original03 : Prop := PidFin3RawTargets.carrier_membership
def rejected03 : Prop := ¬ PidFin3Fault03.carrierMembershipTarget

-- comparable_family_inclusion: The comparable two-branch family is not an antichain.
def original04 : Prop := PidFin3RawTargets.carrier_membership
def rejected04 : Prop := ¬ PidFin3Fault04.carrierMembershipTarget

-- swapped_bit_positions: Coherently swapping encode/decode bit0 and bit1 preserves roundtrips but violates original singleton anchors.
def original05 : Prop := PidFin3RawTargets.codec_anchors
def rejected05 : Prop := ¬ PidFin3Fault05.codecAnchorsTarget

-- unrestricted_mask_roundtrip: Mask8 lies outside the three-bit roundtrip domain and decodes to the empty branch.
def original06 : Prop := PidFin3RawTargets.encode_decode
def rejected06 : Prop := ¬ PidFin3Fault06.encodeDecodeTarget

-- registry_reordering: Transpose registry indices0/1 while retaining registryMasks byte-exact as the external fixed index roster; the original pointwise correspondence fails at index0.
def original07 : Prop := PidFin3RawTargets.registry_pointwise
def rejected07 : Prop := ¬ PidFin3Fault07.registryPointwiseTarget

-- duplicate_registry_member: Distinct fixed indices0 and1 must not decode to the same family.
def original08 : Prop := PidFin3RawTargets.registry_injective
def rejected08 : Prop := ¬ PidFin3Fault08.registryInjectiveTarget

-- reversed_order: The original strict valid-node witness is LE({{0}},{{0,1}}), not its reverse.
def original09 : Prop := PidFin3RawTargets.extremes
def rejected09 : Prop := ¬ PidFin3Fault09.extremesTarget

-- zeta_transpose: Cell(0,2) distinguishes cumulative-row/atom-column orientation from its transpose.
def original10 : Prop := PidFin3RawTargets.zeta_entries
def rejected10 : Prop := ¬ PidFin3Fault10.zetaEntriesTarget

-- one_altered_zeta_cell: One changed diagonal cell contradicts reflexivity, while row width remains18.
def original11 : Prop := PidFin3RawTargets.zeta_entries
def rejected11 : Prop := ¬ PidFin3Fault11.zetaEntriesTarget

-- restricted_boolean_patterns: Restricting the comparison to all-false makes the implication vacuous on both valid nonempty nodes; the missing pattern with bit0 true separates them.
def original12 : Prop := PidFin3RawTargets.reverse_dnf
def rejected12 : Prop := ¬ PidFin3Fault12.reverseDnfTarget

end PidFin3SemanticTargets

namespace PidFin3SemanticAliases
def original01 : Prop := PidFin3SemanticTargets.original01
def rejected01 : Prop := PidFin3SemanticTargets.rejected01
def original02 : Prop := PidFin3SemanticTargets.original02
def rejected02 : Prop := PidFin3SemanticTargets.rejected02
def original03 : Prop := PidFin3SemanticTargets.original03
def rejected03 : Prop := PidFin3SemanticTargets.rejected03
def original04 : Prop := PidFin3SemanticTargets.original04
def rejected04 : Prop := PidFin3SemanticTargets.rejected04
def original05 : Prop := PidFin3SemanticTargets.original05
def rejected05 : Prop := PidFin3SemanticTargets.rejected05
def original06 : Prop := PidFin3SemanticTargets.original06
def rejected06 : Prop := PidFin3SemanticTargets.rejected06
def original07 : Prop := PidFin3SemanticTargets.original07
def rejected07 : Prop := PidFin3SemanticTargets.rejected07
def original08 : Prop := PidFin3SemanticTargets.original08
def rejected08 : Prop := PidFin3SemanticTargets.rejected08
def original09 : Prop := PidFin3SemanticTargets.original09
def rejected09 : Prop := PidFin3SemanticTargets.rejected09
def original10 : Prop := PidFin3SemanticTargets.original10
def rejected10 : Prop := PidFin3SemanticTargets.rejected10
def original11 : Prop := PidFin3SemanticTargets.original11
def rejected11 : Prop := PidFin3SemanticTargets.rejected11
def original12 : Prop := PidFin3SemanticTargets.original12
def rejected12 : Prop := PidFin3SemanticTargets.rejected12
end PidFin3SemanticAliases

namespace PidFin3SemanticControls

theorem original01 : PidFin3SemanticAliases.original01 :=
  @PidFin3Candidate.carrier_membership

theorem rejected01 : PidFin3SemanticAliases.rejected01 := by
  intro h
  have bad : ¬ ((∅ : PidFin3Fault01.Family) ∈ PidFin3Fault01.carrier ↔ PidFin3Fault01.Valid ∅) := by decide
  exact bad (h ∅)

theorem original02 : PidFin3SemanticAliases.original02 :=
  @PidFin3Candidate.carrier_membership

theorem rejected02 : PidFin3SemanticAliases.rejected02 := by
  intro h
  have bad : ¬ (({∅} : PidFin3Fault02.Family) ∈ PidFin3Fault02.carrier ↔ PidFin3Fault02.Valid {∅}) := by decide
  exact bad (h {∅})

theorem original03 : PidFin3SemanticAliases.original03 :=
  @PidFin3Candidate.carrier_membership

theorem rejected03 : PidFin3SemanticAliases.rejected03 := by
  intro h
  have bad : ¬ (({{0}} : PidFin3Fault03.Family) ∈ PidFin3Fault03.carrier ↔ PidFin3Fault03.Valid {{0}}) := by decide
  exact bad (h {{0}})

theorem original04 : PidFin3SemanticAliases.original04 :=
  @PidFin3Candidate.carrier_membership

theorem rejected04 : PidFin3SemanticAliases.rejected04 := by
  intro h
  have bad : ¬ (({{0}, {0, 1}} : PidFin3Fault04.Family) ∈ PidFin3Fault04.carrier ↔ PidFin3Fault04.Valid {{0}, {0, 1}}) := by decide
  exact bad (h {{0}, {0, 1}})

theorem original05 : PidFin3SemanticAliases.original05 :=
  @PidFin3Candidate.codec_anchors

theorem rejected05 : PidFin3SemanticAliases.rejected05 := by
  intro h
  have bad : PidFin3Fault05.encode {0} ≠ 1 := by decide
  exact bad h.1

theorem original06 : PidFin3SemanticAliases.original06 :=
  @PidFin3Candidate.encode_decode

theorem rejected06 : PidFin3SemanticAliases.rejected06 := by
  intro h
  have bad : PidFin3Fault06.encode (PidFin3Fault06.decode 8) ≠ 8 := by decide
  exact bad (h 8)

theorem original07 : PidFin3SemanticAliases.original07 :=
  @PidFin3Candidate.registry_pointwise

theorem rejected07 : PidFin3SemanticAliases.rejected07 := by
  intro h
  have bad : ¬ ((PidFin3Fault07.registry (0 : Fin 18)).image PidFin3Fault07.encode =
      (PidFin3Fault07.registryMasks 0).toFinset) := by decide
  exact bad (h 0)

theorem original08 : PidFin3SemanticAliases.original08 :=
  @PidFin3Candidate.registry_injective

theorem rejected08 : PidFin3SemanticAliases.rejected08 := by
  intro h
  have bad : (0 : Fin 18) ≠ 1 := by decide
  exact bad (@h 0 1 (by decide))

theorem original09 : PidFin3SemanticAliases.original09 :=
  @PidFin3Candidate.extremes

theorem rejected09 : PidFin3SemanticAliases.rejected09 := by
  intro h
  have bad : ¬ PidFin3Fault09.LE (PidFin3Fault09.registry 0) (PidFin3Fault09.registry 2) := by
    unfold PidFin3Fault09.LE
    decide
  exact bad h.2.1

theorem original10 : PidFin3SemanticAliases.original10 :=
  @PidFin3Candidate.zeta_entries

theorem rejected10 : PidFin3SemanticAliases.rejected10 := by
  intro h
  have bad : ¬ (PidFin3Fault10.expectedZeta (0 : Fin 18) 2 = true ↔
      PidFin3Fault10.LE (PidFin3Fault10.registry 2) (PidFin3Fault10.registry 0)) := by
    unfold PidFin3Fault10.LE
    decide
  exact bad (h 0 2)

theorem original11 : PidFin3SemanticAliases.original11 :=
  @PidFin3Candidate.zeta_entries

theorem rejected11 : PidFin3SemanticAliases.rejected11 := by
  intro h
  have bad : ¬ (PidFin3Fault11.expectedZeta (0 : Fin 18) 0 = true ↔
      PidFin3Fault11.LE (PidFin3Fault11.registry 0) (PidFin3Fault11.registry 0)) := by
    unfold PidFin3Fault11.LE
    decide
  exact bad (h 0 0)

theorem original12 : PidFin3SemanticAliases.original12 :=
  @PidFin3Candidate.reverse_dnf

theorem rejected12 : PidFin3SemanticAliases.rejected12 := by
  intro h
  have bad : ¬ (PidFin3Fault12.LE (PidFin3Fault12.registry 2) (PidFin3Fault12.registry 0) ↔
      (PidFin3Fault12.DNF (PidFin3Fault12.registry 0) (fun _ => false) →
      PidFin3Fault12.DNF (PidFin3Fault12.registry 2) (fun _ => false))) := by
    unfold PidFin3Fault12.LE PidFin3Fault12.DNF
    decide
  exact bad (h (PidFin3Fault12.registry 2) (PidFin3Fault12.registry 0))

end PidFin3SemanticControls

example : PidFin3SemanticTargets.original01 := @PidFin3SemanticControls.original01
example : PidFin3SemanticAliases.original01 := @PidFin3SemanticControls.original01
example : PidFin3SemanticTargets.rejected01 := @PidFin3SemanticControls.rejected01
example : PidFin3SemanticAliases.rejected01 := @PidFin3SemanticControls.rejected01
example : PidFin3SemanticTargets.original02 := @PidFin3SemanticControls.original02
example : PidFin3SemanticAliases.original02 := @PidFin3SemanticControls.original02
example : PidFin3SemanticTargets.rejected02 := @PidFin3SemanticControls.rejected02
example : PidFin3SemanticAliases.rejected02 := @PidFin3SemanticControls.rejected02
example : PidFin3SemanticTargets.original03 := @PidFin3SemanticControls.original03
example : PidFin3SemanticAliases.original03 := @PidFin3SemanticControls.original03
example : PidFin3SemanticTargets.rejected03 := @PidFin3SemanticControls.rejected03
example : PidFin3SemanticAliases.rejected03 := @PidFin3SemanticControls.rejected03
example : PidFin3SemanticTargets.original04 := @PidFin3SemanticControls.original04
example : PidFin3SemanticAliases.original04 := @PidFin3SemanticControls.original04
example : PidFin3SemanticTargets.rejected04 := @PidFin3SemanticControls.rejected04
example : PidFin3SemanticAliases.rejected04 := @PidFin3SemanticControls.rejected04
example : PidFin3SemanticTargets.original05 := @PidFin3SemanticControls.original05
example : PidFin3SemanticAliases.original05 := @PidFin3SemanticControls.original05
example : PidFin3SemanticTargets.rejected05 := @PidFin3SemanticControls.rejected05
example : PidFin3SemanticAliases.rejected05 := @PidFin3SemanticControls.rejected05
example : PidFin3SemanticTargets.original06 := @PidFin3SemanticControls.original06
example : PidFin3SemanticAliases.original06 := @PidFin3SemanticControls.original06
example : PidFin3SemanticTargets.rejected06 := @PidFin3SemanticControls.rejected06
example : PidFin3SemanticAliases.rejected06 := @PidFin3SemanticControls.rejected06
example : PidFin3SemanticTargets.original07 := @PidFin3SemanticControls.original07
example : PidFin3SemanticAliases.original07 := @PidFin3SemanticControls.original07
example : PidFin3SemanticTargets.rejected07 := @PidFin3SemanticControls.rejected07
example : PidFin3SemanticAliases.rejected07 := @PidFin3SemanticControls.rejected07
example : PidFin3SemanticTargets.original08 := @PidFin3SemanticControls.original08
example : PidFin3SemanticAliases.original08 := @PidFin3SemanticControls.original08
example : PidFin3SemanticTargets.rejected08 := @PidFin3SemanticControls.rejected08
example : PidFin3SemanticAliases.rejected08 := @PidFin3SemanticControls.rejected08
example : PidFin3SemanticTargets.original09 := @PidFin3SemanticControls.original09
example : PidFin3SemanticAliases.original09 := @PidFin3SemanticControls.original09
example : PidFin3SemanticTargets.rejected09 := @PidFin3SemanticControls.rejected09
example : PidFin3SemanticAliases.rejected09 := @PidFin3SemanticControls.rejected09
example : PidFin3SemanticTargets.original10 := @PidFin3SemanticControls.original10
example : PidFin3SemanticAliases.original10 := @PidFin3SemanticControls.original10
example : PidFin3SemanticTargets.rejected10 := @PidFin3SemanticControls.rejected10
example : PidFin3SemanticAliases.rejected10 := @PidFin3SemanticControls.rejected10
example : PidFin3SemanticTargets.original11 := @PidFin3SemanticControls.original11
example : PidFin3SemanticAliases.original11 := @PidFin3SemanticControls.original11
example : PidFin3SemanticTargets.rejected11 := @PidFin3SemanticControls.rejected11
example : PidFin3SemanticAliases.rejected11 := @PidFin3SemanticControls.rejected11
example : PidFin3SemanticTargets.original12 := @PidFin3SemanticControls.original12
example : PidFin3SemanticAliases.original12 := @PidFin3SemanticControls.original12
example : PidFin3SemanticTargets.rejected12 := @PidFin3SemanticControls.rejected12
example : PidFin3SemanticAliases.rejected12 := @PidFin3SemanticControls.rejected12

open Lean Elab Command

run_cmd liftTermElabM do
  let entries : List (Name × Name × Name) := [
    (``PidFin3SemanticControls.original01, ``PidFin3SemanticTargets.original01, ``PidFin3SemanticAliases.original01),
    (``PidFin3SemanticControls.rejected01, ``PidFin3SemanticTargets.rejected01, ``PidFin3SemanticAliases.rejected01),
    (``PidFin3SemanticControls.original02, ``PidFin3SemanticTargets.original02, ``PidFin3SemanticAliases.original02),
    (``PidFin3SemanticControls.rejected02, ``PidFin3SemanticTargets.rejected02, ``PidFin3SemanticAliases.rejected02),
    (``PidFin3SemanticControls.original03, ``PidFin3SemanticTargets.original03, ``PidFin3SemanticAliases.original03),
    (``PidFin3SemanticControls.rejected03, ``PidFin3SemanticTargets.rejected03, ``PidFin3SemanticAliases.rejected03),
    (``PidFin3SemanticControls.original04, ``PidFin3SemanticTargets.original04, ``PidFin3SemanticAliases.original04),
    (``PidFin3SemanticControls.rejected04, ``PidFin3SemanticTargets.rejected04, ``PidFin3SemanticAliases.rejected04),
    (``PidFin3SemanticControls.original05, ``PidFin3SemanticTargets.original05, ``PidFin3SemanticAliases.original05),
    (``PidFin3SemanticControls.rejected05, ``PidFin3SemanticTargets.rejected05, ``PidFin3SemanticAliases.rejected05),
    (``PidFin3SemanticControls.original06, ``PidFin3SemanticTargets.original06, ``PidFin3SemanticAliases.original06),
    (``PidFin3SemanticControls.rejected06, ``PidFin3SemanticTargets.rejected06, ``PidFin3SemanticAliases.rejected06),
    (``PidFin3SemanticControls.original07, ``PidFin3SemanticTargets.original07, ``PidFin3SemanticAliases.original07),
    (``PidFin3SemanticControls.rejected07, ``PidFin3SemanticTargets.rejected07, ``PidFin3SemanticAliases.rejected07),
    (``PidFin3SemanticControls.original08, ``PidFin3SemanticTargets.original08, ``PidFin3SemanticAliases.original08),
    (``PidFin3SemanticControls.rejected08, ``PidFin3SemanticTargets.rejected08, ``PidFin3SemanticAliases.rejected08),
    (``PidFin3SemanticControls.original09, ``PidFin3SemanticTargets.original09, ``PidFin3SemanticAliases.original09),
    (``PidFin3SemanticControls.rejected09, ``PidFin3SemanticTargets.rejected09, ``PidFin3SemanticAliases.rejected09),
    (``PidFin3SemanticControls.original10, ``PidFin3SemanticTargets.original10, ``PidFin3SemanticAliases.original10),
    (``PidFin3SemanticControls.rejected10, ``PidFin3SemanticTargets.rejected10, ``PidFin3SemanticAliases.rejected10),
    (``PidFin3SemanticControls.original11, ``PidFin3SemanticTargets.original11, ``PidFin3SemanticAliases.original11),
    (``PidFin3SemanticControls.rejected11, ``PidFin3SemanticTargets.rejected11, ``PidFin3SemanticAliases.rejected11),
    (``PidFin3SemanticControls.original12, ``PidFin3SemanticTargets.original12, ``PidFin3SemanticAliases.original12),
    (``PidFin3SemanticControls.rejected12, ``PidFin3SemanticTargets.rejected12, ``PidFin3SemanticAliases.rejected12)]
  for (declaration, raw, aliasView) in entries do
    let result ← PidFin3Judge.checkExport declaration raw aliasView
    IO.println ("FIN3_SEMANTIC12_RESULT " ++ result.compress)
  IO.println "FIN3_SEMANTIC12_DONE 24"
