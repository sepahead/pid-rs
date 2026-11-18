import Lean.Util.CollectAxioms
import Mathlib.Data.List.Defs

set_option autoImplicit false
set_option warningAsError true

open Lean Meta
namespace PidFin3Judge

def hasExactType (actual : Expr) (actualLevels : List Name)
    (expected : Expr) (expectedLevels : List Name) : MetaM Bool := do
  if !actualLevels.isEmpty || !expectedLevels.isEmpty || actual.hasMVar || expected.hasMVar then
    return false
  withNewMCtxDepth <| withTransparency .all <| isDefEq actual expected

def checkContractView (raw aliasView : Name) : MetaM Unit := do
  let rawInfo ← getConstInfoDefn raw
  let aliasInfo ← getConstInfoDefn aliasView
  unless ← hasExactType aliasInfo.value aliasInfo.levelParams rawInfo.value rawInfo.levelParams do
    throwError "FIN3_CONTRACT_VIEW: {raw} and {aliasView} differ"

def renderClosed (expression : Expr) : MetaM String := do
  let rendered ← withOptions (fun options =>
    options.setBool `pp.all true |>.setBool `pp.universes true |>.set `pp.width (160 : Nat)) <|
      ppExpr expression
  return rendered.pretty

def describeContractView (raw aliasView : Name) : MetaM Json := do
  checkContractView raw aliasView
  let rawInfo ← getConstInfoDefn raw
  let rendered ← renderClosed rawInfo.value
  return Json.mkObj [
    ("raw_target", Json.str raw.toString),
    ("alias_target", Json.str aliasView.toString),
    ("raw_elaborated_target", Json.str rendered)]

def checkExport (declaration raw aliasView : Name) : MetaM Json := do
  checkContractView raw aliasView
  let actual ← getConstInfo declaration
  match actual with
  | .thmInfo _ => pure ()
  | _ => throwError "FIN3_DECLARATION_KIND: {declaration} is not a theorem"
  let intended ← getConstInfoDefn raw
  unless ← hasExactType actual.type actual.levelParams intended.value intended.levelParams do
    throwError "FIN3_TARGET_TYPE: {declaration} lacks the complete receiver-free target"
  let allowed : List Name := [``propext, ``Classical.choice, ``Quot.sound]
  let axioms ← collectAxioms declaration
  for assumption in axioms do
    unless allowed.contains assumption do
      throwError "FIN3_AXIOM: {declaration} uses {assumption}"
  let ordered := axioms.toList.mergeSort (fun left right => left.toString ≤ right.toString)
  let rendered ← renderClosed actual.type
  let rawRendered ← renderClosed intended.value
  return Json.mkObj [
    ("theorem", Json.str declaration.toString),
    ("raw_target", Json.str raw.toString),
    ("alias_target", Json.str aliasView.toString),
    ("universes", Json.arr #[]),
    ("full_elaborated_type", Json.str rendered),
    ("raw_elaborated_target", Json.str rawRendered),
    ("axioms", Json.arr (ordered.map (Json.str ∘ Name.toString)).toArray),
    ("status", Json.str "accepted")]

def checkPublicRoster (expected : List Name) : MetaM Unit := do
  let environment ← getEnv
  let observed := environment.constants.toList.filterMap fun (name, _) =>
    if name.toString.startsWith "PidFin3Candidate." then some name else none
  unless observed.length == expected.length &&
      observed.all expected.contains && expected.all observed.contains do
    throwError "FIN3_EXPORT_ROSTER: expected exactly {expected.length} public declarations"

end PidFin3Judge
