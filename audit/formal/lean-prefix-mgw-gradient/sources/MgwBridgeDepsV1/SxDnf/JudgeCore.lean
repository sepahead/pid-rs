import Lean
import Lean.Util.CollectAxioms
import Mathlib.Data.List.Defs

/-! Reviewer-owned inspection code. This module supplies no DNF/order proof. -/
set_option autoImplicit false
set_option warningAsError true

open Lean Meta
namespace PidSxDnfOrderJudge

private def rigidLevels (count : Nat) : List Level :=
  (List.range count).map fun index => Level.param (Name.mkSimple s!"judge_universe_{index}")

/-- Compare complete closed declaration types, allowing only a permutation of universe names.
    An additional implicit or explicit proof receiver remains a Pi binder and fails this check. -/
def hasExactType (actual : Expr) (actualLevels : List Name)
    (expected : Expr) (expectedLevels : List Name) : MetaM Bool := do
  if actualLevels.length != expectedLevels.length then
    return false
  if actual.hasMVar || expected.hasMVar then
    return false
  let levels := rigidLevels expectedLevels.length
  let intended := expected.instantiateLevelParams expectedLevels levels
  for renamed in levels.permutations do
    let supplied := actual.instantiateLevelParams actualLevels renamed
    if ← withNewMCtxDepth <| withTransparency .all <| isDefEq supplied intended then
      return true
  return false

def checkContractView (raw aliasView : Name) : MetaM Unit := do
  let rawInfo ← getConstInfoDefn raw
  let aliasInfo ← getConstInfoDefn aliasView
  unless ← hasExactType aliasInfo.value aliasInfo.levelParams rawInfo.value rawInfo.levelParams do
    throwError "DNF_JUDGE_CONTRACT_VIEW: {raw} and {aliasView} differ"

def checkExport (declaration raw aliasView : Name) : MetaM Json := do
  checkContractView raw aliasView
  let actual ← getConstInfo declaration
  match actual with
  | .thmInfo _ => pure ()
  | _ => throwError "DNF_JUDGE_DECLARATION_KIND: {declaration} is not a theorem"
  let intended ← getConstInfoDefn raw
  unless ← hasExactType actual.type actual.levelParams intended.value intended.levelParams do
    throwError "DNF_JUDGE_TARGET_TYPE: {declaration} does not have the complete receiver-free target"
  let allowed : List Name := [``propext, ``Classical.choice, ``Quot.sound]
  let axioms ← collectAxioms declaration
  for assumption in axioms do
    unless allowed.contains assumption do
      throwError "DNF_JUDGE_AXIOM: {declaration} uses {assumption}"
  let ordered := axioms.toList.mergeSort (fun left right => left.toString ≤ right.toString)
  let rendered ← withOptions (fun options =>
    options.setBool `pp.all true |>.setBool `pp.universes true |>.set `pp.width (160 : Nat)) <|
      ppExpr actual.type
  return Json.mkObj [
    ("theorem", Json.str declaration.toString),
    ("raw_target", Json.str raw.toString),
    ("alias_target", Json.str aliasView.toString),
    ("universes", Json.arr (actual.levelParams.map (Json.str ∘ Name.toString)).toArray),
    ("full_elaborated_type", Json.str rendered.pretty),
    ("axioms", Json.arr (ordered.map (Json.str ∘ Name.toString)).toArray),
    ("status", Json.str "accepted")]

def checkPublicRoster (expected : List Name) : MetaM Unit := do
  let environment ← getEnv
  let observed := environment.constants.toList.filterMap fun (name, _) =>
    if name.toString.startsWith "PidSxDnfOrderCandidate." then some name else none
  unless observed.length == expected.length &&
      observed.all expected.contains && expected.all observed.contains do
    throwError "DNF_JUDGE_EXPORT_ROSTER: expected exactly {expected.length} public declarations"

end PidSxDnfOrderJudge
