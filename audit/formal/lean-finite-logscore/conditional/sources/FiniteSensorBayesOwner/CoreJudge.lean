import FiniteSensorBayes.Contract
import FiniteSensorBayes.RawTargets
import FiniteSensorBayes.FiniteLogScoreTarget
import FiniteSensorBayes.Candidate
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum
import FiniteSensorBayesOwner.ModuleInventory
import FiniteSensorBayesOwner.ExactTypeComponent
import FiniteSensorBayes.ConditionalCandidate

/-!
UNCOMPILED CONDITIONAL OWNER JUDGE PROPOSAL. No conditional candidate is supplied.
Exactly thirteen unchanged raw targets; accepted finite-law proofs are dependencies.
No mask or PID theorem, estimator guarantee, learned-improvement guarantee or empirical application claim is added.
The outer runner owns source/import binding, containment, terminal status, and adoption.
-/
set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command

run_cmd liftTermElabM do
  let inventory ← SensorBayesModuleInventory.inspectModule `FiniteSensorBayes.ConditionalCandidate
  let pairs : List ((Name × Name) × Nat) := [
    ((`FiniteSensorBayesConditionalCandidate.observationSemantics, ``FiniteSensorBayes.Raw.ObservationSemanticsTarget), 3),
    ((`FiniteSensorBayesConditionalCandidate.posteriorSemantics, ``FiniteSensorBayes.Raw.PosteriorSemanticsTarget), 3),
    ((`FiniteSensorBayesConditionalCandidate.nullFallbackRisk, ``FiniteSensorBayes.Raw.NullFallbackRiskTarget), 3),
    ((`FiniteSensorBayesConditionalCandidate.admissibilityOnStates, ``FiniteSensorBayes.Raw.AdmissibilityOnStatesTarget), 3),
    ((`FiniteSensorBayesConditionalCandidate.expectedLossSum, ``FiniteSensorBayes.Raw.ExpectedLossSumTarget), 3),
    ((`FiniteSensorBayesConditionalCandidate.predictiveKL, ``FiniteSensorBayes.Raw.PredictiveKLTarget), 3),
    ((`FiniteSensorBayesConditionalCandidate.logScoreDecomposition, ``FiniteSensorBayes.Raw.LogScoreDecompositionTarget), 3),
    ((`FiniteSensorBayesConditionalCandidate.bayesAttainmentMinimality, ``FiniteSensorBayes.Raw.BayesAttainmentMinimalityTarget), 3),
    ((`FiniteSensorBayesConditionalCandidate.noObservationRisk, ``FiniteSensorBayes.Raw.NoObservationRiskTarget), 2),
    ((`FiniteSensorBayesConditionalCandidate.informationDomains, ``FiniteSensorBayes.Raw.InformationDomainsTarget), 4),
    ((`FiniteSensorBayesConditionalCandidate.mutualInformationGain, ``FiniteSensorBayes.Raw.MutualInformationGainTarget), 3),
    ((`FiniteSensorBayesConditionalCandidate.conditionalInformationGain, ``FiniteSensorBayes.Raw.ConditionalInformationGainTarget), 4),
    ((`FiniteSensorBayesConditionalCandidate.learnedLossGap, ``FiniteSensorBayes.Raw.LearnedLossGapTarget), 4)]
  let mut exports : Array Json := #[]
  for ((candidate, raw), arity) in pairs do
    SensorBayesExactType.inspectExport candidate raw
    let actual ← getConstInfo candidate
    let intended ← getConstInfoDefn raw
    unless actual.levelParams.length == arity && intended.levelParams.length == arity do
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
    ("scope", Json.str "finite_conditional_bayes_information_thirteen_targets"),
    ("inventory", inventory),
    ("imports", imports),
    ("exports", Json.arr exports),
    ("status", Json.str "semantic_checks_completed_requires_outer_acceptance")]
  IO.println ("SENSOR_BAYES_CORE_JUDGE " ++ result.compress)
