import CountEvidence
import Lean.Util.FoldConsts
import Lean.Util.CollectAxioms
open Lean Elab Command

-- A supplementary read-only query over the 86 original names. It declares no theorems.
run_cmd do
  let names : List Name := [
    `PidFin3AlphabetCounts.sourceEventDecidable._aux_1,
    `PidFin3CountRaw.sourceEventDecidable._aux_1,
    `PidFin3AlphabetCounts.Observation,
    `PidFin3CountRaw.Observation,
    `PidFin3AlphabetCounts.sourceEvent,
    `PidFin3CountRaw.sourceEvent,
    `PidFin3AlphabetCounts.eqPattern,
    `PidFin3CountRaw.eqPattern,
    `PidFin3AlphabetCounts.sourceEventDecidable,
    `PidFin3CountRaw.sourceEventDecidable,
    `PidFin3AlphabetCounts.mass,
    `PidFin3CountRaw.mass,
    `PidFin3AlphabetCounts.N,
    `PidFin3CountRaw.N,
    `PidFin3AlphabetCounts.U,
    `PidFin3CountRaw.U,
    `PidFin3AlphabetCounts.V,
    `PidFin3CountRaw.V,
    `PidFin3AlphabetCounts.T,
    `PidFin3CountRaw.T,
    `PidFin3AlphabetCounts.sourceEvent_antitone,
    `PidFin3CountRaw.sourceEvent_antitone,
    `PidFin3CountConsumers.sourceEvent_antitone,
    `PidFin3AlphabetCounts.sourceEvent_key_iff,
    `PidFin3CountRaw.sourceEvent_key_iff,
    `PidFin3CountConsumers.sourceEvent_key_iff,
    `PidFin3AlphabetCounts.sourceEvent_data_congr,
    `PidFin3CountRaw.sourceEvent_data_congr,
    `PidFin3CountConsumers.sourceEvent_data_congr,
    `PidFin3AlphabetCounts.dnf_eq_sourceEvent,
    `PidFin3CountRaw.dnf_eq_sourceEvent,
    `PidFin3CountConsumers.dnf_eq_sourceEvent,
    `PidFin3AlphabetCounts.mass_mono,
    `PidFin3CountRaw.mass_mono,
    `PidFin3CountConsumers.mass_mono,
    `PidFin3AlphabetCounts.mass_le_total,
    `PidFin3CountRaw.mass_le_total,
    `PidFin3CountConsumers.mass_le_total,
    `PidFin3AlphabetCounts.key_weight_le_mass,
    `PidFin3CountRaw.key_weight_le_mass,
    `PidFin3CountConsumers.key_weight_le_mass,
    `PidFin3AlphabetCounts.mass_congr,
    `PidFin3CountRaw.mass_congr,
    `PidFin3CountConsumers.mass_congr,
    `PidFin3AlphabetCounts.total_congr,
    `PidFin3CountRaw.total_congr,
    `PidFin3CountConsumers.total_congr,
    `PidFin3AlphabetCounts.supported_key_source_mem,
    `PidFin3CountRaw.supported_key_source_mem,
    `PidFin3CountConsumers.supported_key_source_mem,
    `PidFin3AlphabetCounts.supported_key_joint_mem,
    `PidFin3CountRaw.supported_key_joint_mem,
    `PidFin3CountConsumers.supported_key_joint_mem,
    `PidFin3AlphabetCounts.supported_key_target_mem,
    `PidFin3CountRaw.supported_key_target_mem,
    `PidFin3CountConsumers.supported_key_target_mem,
    `PidFin3AlphabetCounts.V_le_U,
    `PidFin3CountRaw.V_le_U,
    `PidFin3CountConsumers.V_le_U,
    `PidFin3AlphabetCounts.U_le_N,
    `PidFin3CountRaw.U_le_N,
    `PidFin3CountConsumers.U_le_N,
    `PidFin3AlphabetCounts.V_le_T,
    `PidFin3CountRaw.V_le_T,
    `PidFin3CountConsumers.V_le_T,
    `PidFin3AlphabetCounts.T_le_N,
    `PidFin3CountRaw.T_le_N,
    `PidFin3CountConsumers.T_le_N,
    `PidFin3AlphabetCounts.key_le_V,
    `PidFin3CountRaw.key_le_V,
    `PidFin3CountConsumers.key_le_V,
    `PidFin3AlphabetCounts.supported_key_bounds,
    `PidFin3CountRaw.supported_key_bounds,
    `PidFin3CountConsumers.supported_key_bounds,
    `PidFin3AlphabetCounts.counts_positive,
    `PidFin3CountRaw.counts_positive,
    `PidFin3CountConsumers.counts_positive,
    `PidFin3AlphabetCounts.U_antitone,
    `PidFin3CountRaw.U_antitone,
    `PidFin3CountConsumers.U_antitone,
    `PidFin3AlphabetCounts.V_antitone,
    `PidFin3CountRaw.V_antitone,
    `PidFin3CountConsumers.V_antitone,
    `PidFin3AlphabetCounts.counts_congr_on_support,
    `PidFin3CountRaw.counts_congr_on_support,
    `PidFin3CountConsumers.counts_congr_on_support]
  let env ← getEnv
  let sorted := fun (xs : List Name) =>
    (xs.map Name.toString).mergeSort (· ≤ ·)
  for name in names do
    let ci ← getConstInfo name
    let some owner := env.getModuleIdxFor? name | throwError "missing owner of {name}"
    let some val := ci.value? (allowOpaque := true) | throwError "missing body of {name}"
    let tag ← match ci with
      | .defnInfo value => do
          unless value.safety == .safe do throwError "expected safe definition"
          pure "definition"
      | .thmInfo _ => pure "theorem"
      | _ => throwError "unexpected declaration kind"
    let row := Json.mkObj [
      ("name", toJson name.toString), ("kind", toJson tag),
      ("module", toJson (env.header.moduleNames[owner.toNat]!).toString),
      ("type_constants", toJson (sorted ci.type.getUsedConstantsAsSet.toList)),
      ("value_constants", toJson (sorted val.getUsedConstantsAsSet.toList)),
      ("transitive_axioms", toJson (sorted (← collectAxioms name).toList))]
    IO.println ("COUNT_DEPENDENCIES " ++ row.compress)
