import Lean
import Lean.Util.CollectAxioms
import Mathlib.Data.List.Defs

/-!
UNCOMPILED COMPONENT PROPOSAL, NOT A COMPLETE JUDGE.
Rigid-level comparison follows the inspected DNF JudgeCore.
No candidate is imported and no theorem is proved here.
Outer source/import custody and all candidate-module declaration checks remain mandatory.
-/

set_option autoImplicit false
set_option warningAsError true
open Lean Meta

namespace SensorBayesExactType

private def closed (e : Expr) : Bool :=
  !(e.hasMVar || e.hasFVar || e.hasLooseBVars)

private def rigidLevels (count : Nat) : List Level :=
  (List.range count).map fun index => Level.param (Name.mkSimple s!"sensor_bayes_rigid_{index}")

/-- Universe alpha-renaming/permutation is allowed; specialization, extra levels,
extra premises, and expression/level metavariable instantiation are not. -/
def sameClosedType (actual : Expr) (actualLevels : List Name)
    (expected : Expr) (expectedLevels : List Name) : MetaM Bool := do
  if actualLevels.length != expectedLevels.length then
    return false
  unless closed actual && closed expected do
    return false
  let levels := rigidLevels expectedLevels.length
  let intended := expected.instantiateLevelParams expectedLevels levels
  for renamed in levels.permutations do
    let supplied := actual.instantiateLevelParams actualLevels renamed
    if ← withNewMCtxDepth <| withTransparency .all <| isDefEq supplied intended then
      return true
  return false

/-- A proof-phase component only. The raw source/value must already be owner-frozen.
Its successful return is not standalone acceptance and does not inspect unused helpers. -/
def inspectExport (candidate raw : Name) : MetaM Unit := do
  let actual ← getConstInfo candidate
  let .thmInfo proof := actual
    | throwError "SENSOR_BAYES_EXPORT_KIND: {candidate}"
  unless closed proof.type && closed proof.value do
    throwError "SENSOR_BAYES_EXPORT_CLOSED: {candidate}"
  let intended ← getConstInfoDefn raw
  unless intended.type == mkSort Level.zero do
    throwError "SENSOR_BAYES_RAW_PROP: {raw}"
  unless ← sameClosedType proof.type proof.levelParams intended.value intended.levelParams do
    throwError "SENSOR_BAYES_EXPORT_TYPE: {candidate}"
  let allowed : List Name := [``propext, ``Classical.choice, ``Quot.sound]
  for name in [candidate, raw] do
    for assumption in (← collectAxioms name) do
      unless allowed.contains assumption do
        throwError "SENSOR_BAYES_EXPORT_AXIOM: {name} uses {assumption}"

end SensorBayesExactType
