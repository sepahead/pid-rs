import FiniteSensorBayes.Contract
import FiniteSensorBayes.RawTargets
import FiniteSensorBayes.FiniteLogScoreTarget
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum
import FiniteSensorBayesOwner.ModuleInventory
import FiniteSensorBayesOwner.ExactTypeComponent
import FiniteSensorBayes.Candidate

/-!
UNCOMPILED OWNER JUDGE PROPOSAL. Candidate module deliberately absent from this packet.
Exactly four export/target pairs; no uniqueness or conditional Bayes claim.
The outer runner owns source/import binding, containment, terminal status, and adoption.
-/
set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command

run_cmd liftTermElabM do
  let inventory ← SensorBayesModuleInventory.inspectModule `FiniteSensorBayes.Candidate
  let pairs : List (Name × Name) := [
    (`FiniteSensorBayesCandidate.finiteMass, ``FiniteSensorBayes.Raw.FiniteMassTarget),
    (`FiniteSensorBayesCandidate.finiteExpectation, ``FiniteSensorBayes.Raw.FiniteExpectationTarget),
    (`FiniteSensorBayesCandidate.gibbs, ``FiniteSensorBayes.Raw.GibbsTarget),
    (`FiniteSensorBayesCandidate.logScore, ``FiniteSensorBayes.LogScoreOwner.FiniteLogScoreTarget)]
  let mut exports : Array Json := #[]
  for (candidate, raw) in pairs do
    SensorBayesExactType.inspectExport candidate raw
    let actual ← getConstInfo candidate
    let intended ← getConstInfoDefn raw
    unless actual.levelParams.length == 1 && intended.levelParams.length == 1 do
      throwError "BAYES_CORE_EXPORT_UNIVERSE: {candidate}"
    let (typeText, targetText) ← withOptions (fun opts =>
        opts.setBool `pp.all true |>.setBool `pp.universes true) do
      let a ← ppExpr actual.type
      let t ← ppExpr intended.value
      return (a.pretty, t.pretty)
    let used ← collectAxioms candidate
    let names := used.toList.mergeSort (fun a b => a.toString ≤ b.toString)
    exports := exports.push (Json.mkObj [
      ("theorem", Json.str candidate.toString),
      ("raw_target", Json.str raw.toString),
      ("universe_parameters", Json.arr (actual.levelParams.map (Json.str ∘ Name.toString)).toArray),
      ("full_type", Json.str typeText),
      ("raw_body", Json.str targetText),
      ("axioms", Json.arr (names.map (Json.str ∘ Name.toString)).toArray),
      ("status", Json.str "exact_type_and_axioms_checked")])
  let imports ← SensorBayesModuleInventory.importsObservation
  let result := Json.mkObj [
    ("schema", toJson (1 : Nat)),
    ("scope", Json.str "finite_mass_expectation_gibbs_logscore_only"),
    ("inventory", inventory),
    ("imports", imports),
    ("exports", Json.arr exports),
    ("status", Json.str "semantic_checks_completed_requires_outer_acceptance")]
  IO.println ("SENSOR_BAYES_CORE_JUDGE " ++ result.compress)
