import PidMgwTargetCopy.Interface
import Lean
import Lean.Util.CollectAxioms
import Mathlib.Data.List.Defs

/-!
UNCOMPILED SOURCE PROPOSAL. Reviewer-owned type/axiom inspection, no target proof.
The rigid-level comparator below is reused verbatim from the existing DNF judge.
The expected proposition is built only from the unchanged Interface declaration.
No candidate theorem is opened to infer or weaken its intended conclusion.
-/

set_option autoImplicit false
set_option warningAsError true

open Lean Meta

namespace PidMgwTargetCopyJudge

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


/-- Universally close exactly the original declaration's alphabet/instance parameters. -/
def closeOriginalTarget (target : Name) : MetaM Expr := do
  let info ← getConstInfoDefn target
  let original := mkConst target (info.levelParams.map Level.param)
  forallTelescope info.type fun parameters codomain => do
    unless codomain == mkSort .zero do
      throwError "MGW_COPY_TARGET_KIND: {target} is not proposition-valued"
    mkForallFVars parameters (mkAppN original parameters) (usedOnly := false)

/-- Require the entire original statement, an actual theorem value, and allowed closure. -/
def checkExport (candidate target : Name) : MetaM Json := do
  let actual ← getConstInfo candidate
  match actual with
  | .thmInfo _ => pure ()
  | _ => throwError "MGW_COPY_DECLARATION_KIND: {candidate} is not a theorem"
  let some proofValue := actual.value? (allowOpaque := true)
    | throwError "MGW_COPY_PROOF_VALUE: {candidate} has no theorem value"
  if proofValue.hasMVar then
    throwError "MGW_COPY_PROOF_VALUE: {candidate} contains a metavariable"
  let intended ← getConstInfoDefn target
  let expected ← closeOriginalTarget target
  unless ← hasExactType actual.type actual.levelParams expected intended.levelParams do
    throwError "MGW_COPY_TARGET_TYPE: {candidate} differs from the complete original target"
  let allowed : List Name := [``propext, ``Classical.choice, ``Quot.sound]
  let candidateAxioms ← collectAxioms candidate
  let targetAxioms ← collectAxioms target
  for (declaration, assumptions) in #[(candidate, candidateAxioms), (target, targetAxioms)] do
    for assumption in assumptions do
      unless allowed.contains assumption do
        throwError "MGW_COPY_AXIOM: {declaration} uses {assumption}"
  let orderedCandidate := candidateAxioms.toList.mergeSort
    (fun left right => left.toString ≤ right.toString)
  let orderedTarget := targetAxioms.toList.mergeSort
    (fun left right => left.toString ≤ right.toString)
  let (actualType, expectedType, originalType, originalValue) ←
    withOptions (fun options =>
      options.setBool `pp.all true |>.setBool `pp.universes true) do
      let a ← ppExpr actual.type
      let e ← ppExpr expected
      let t ← ppExpr intended.type
      let v ← ppExpr intended.value
      return (a.pretty, e.pretty, t.pretty, v.pretty)
  return Json.mkObj [
    ("candidate_fqn", Json.str candidate.toString),
    ("target_fqn", Json.str target.toString),
    ("candidate_kind", Json.str "theorem"),
    ("proof_value_present", Json.bool true),
    ("candidate_universes", Json.arr (actual.levelParams.map (Json.str ∘ Name.toString)).toArray),
    ("target_universes", Json.arr (intended.levelParams.map (Json.str ∘ Name.toString)).toArray),
    ("candidate_full_type", Json.str actualType),
    ("expected_closed_target", Json.str expectedType),
    ("original_target_type", Json.str originalType),
    ("original_target_value", Json.str originalValue),
    ("full_type_defeq", Json.bool true),
    ("candidate_axioms", Json.arr (orderedCandidate.map (Json.str ∘ Name.toString)).toArray),
    ("target_axioms", Json.arr (orderedTarget.map (Json.str ∘ Name.toString)).toArray)]

end PidMgwTargetCopyJudge
