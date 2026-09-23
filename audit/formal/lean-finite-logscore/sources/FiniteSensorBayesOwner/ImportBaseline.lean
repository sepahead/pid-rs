import FiniteSensorBayes.Contract
import FiniteSensorBayes.RawTargets
import FiniteSensorBayes.FiniteLogScoreTarget
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum
import FiniteSensorBayesOwner.ModuleInventory
import FiniteSensorBayesOwner.ExactTypeComponent

/-! UNCOMPILED owner baseline query. No candidate, no proof, no acceptance. -/
set_option autoImplicit false
set_option warningAsError true
open Lean Meta Elab Command

run_cmd liftTermElabM do
  let observation ← SensorBayesModuleInventory.importsObservation
  IO.println ("SENSOR_BAYES_IMPORT_BASELINE " ++ observation.compress)
