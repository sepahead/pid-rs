import Lean
import Lean.Util.CollectAxioms
import Mathlib.Data.List.Defs

/-!
UNCOMPILED OWNER COMPONENT. No candidate or scientific proof is supplied.
Intended installed module: FiniteSensorBayesOwner.ModuleInventory.
The first packet permits theorem/lemma helpers only. Every kernel declaration
owned by the candidate MODULE is checked, without a namespace-prefix filter.
Compiler-only routed names are inventoried and refused rather than guessed safe.
-/
set_option autoImplicit false
set_option warningAsError true
open Lean Meta

namespace SensorBayesModuleInventory

def fixedImports : List Name := [
  `FiniteSensorBayes.Contract,
  `FiniteSensorBayes.RawTargets,
  `FiniteSensorBayes.FiniteLogScoreTarget,
  `Mathlib.Tactic.Positivity,
  `Mathlib.Tactic.Linarith,
  `Mathlib.Tactic.Ring,
  `Mathlib.Tactic.NormNum]

/-- Version 2: the pinned frontend prepends these two imports to a non-prelude
header; mkModuleData preserves that header. Source imports remain exactly seven. -/
def fixedModuleDataImports : Array Import :=
  #[{ module := `Init, importAll := false, isExported := true, isMeta := false },
    { module := `Init, importAll := false, isExported := true, isMeta := true }] ++
  fixedImports.toArray.map (fun name =>
    { module := name, importAll := false, isExported := true, isMeta := false })

private def closed (e : Expr) : Bool :=
  !(e.hasMVar || e.hasFVar || e.hasLooseBVars)

private def namesJson (names : List Name) : Json :=
  Json.arr ((names.mergeSort (fun a b => a.toString ≤ b.toString)).map
    (Json.str ∘ Name.toString)).toArray

private def importJson (entry : Import) : Json :=
  Json.mkObj [
    ("module", Json.str entry.module.toString),
    ("import_all", Json.bool entry.importAll),
    ("exported", Json.bool entry.isExported),
    ("meta", Json.bool entry.isMeta)]

def importsObservation : MetaM Json := do
  let env := (← getEnv).setExporting false
  let entries := env.header.modules.toList.mergeSort
    (fun a b => a.module.toString ≤ b.module.toString)
  return Json.mkObj [
    ("main_module", Json.str env.mainModule.toString),
    ("legacy_owner", Json.bool (!env.header.isModule)),
    ("trust_level", toJson env.header.trustLevel.toNat),
    ("direct_imports", Json.arr (env.header.imports.map importJson)),
    ("closure", Json.arr (entries.map fun item => Json.mkObj [
      ("import", importJson item.toImport),
      ("has_data", Json.bool item.hasData),
      ("ir_phases", Json.str (reprStr item.irPhases))]).toArray)]

/-- An exact positive inventory is returned only if all candidate-owned declarations
are closed theorem values with allowed axioms. No target proof is assumed here. -/
def inspectModule (candidateModule : Name) : MetaM Json := do
  let env := (← getEnv).setExporting false
  unless !env.header.isModule do
    throwError "BAYES_MODULE_VISIBILITY: owner inspector must load private legacy view"
  unless env.header.moduleData.size == env.header.modules.size do
    throwError "BAYES_MODULE_LAYOUT: header arrays differ"
  let mut positions : List Nat := []
  for index in [:env.header.modules.size] do
    if env.header.modules[index]!.module == candidateModule then
      positions := index :: positions
  let [index] := positions
    | throwError "BAYES_MODULE_UNIQUE: candidate module must occur exactly once"
  let effective := env.header.modules[index]!
  unless effective.importAll && effective.hasData do
    throwError "BAYES_MODULE_VISIBILITY: private candidate data was not loaded"
  let data := env.header.moduleData[index]!
  if data.isModule then
    throwError "BAYES_MODULE_FORMAT: first packet requires the frozen legacy source form"
  unless data.imports.size == fixedModuleDataImports.size do
    throwError "BAYES_MODULE_IMPORTS: direct count differs"
  for actual in data.imports, expected in fixedModuleDataImports do
    unless actual.module == expected.module && actual.importAll == expected.importAll &&
        actual.isExported == expected.isExported && actual.isMeta == expected.isMeta do
      throwError "BAYES_MODULE_IMPORTS: direct import or modifier differs"
  let metadataNames := data.constNames.toList
  let valueNames := data.constants.toList.map (·.name)
  unless metadataNames == valueNames && metadataNames.eraseDups.length == metadataNames.length do
    throwError "BAYES_MODULE_CONSTANTS: duplicate or mismatched metadata names"
  let routedNames := env.const2ModIdx.toList.filterMap fun (name, owner) =>
    if owner.toNat == index then some name else none
  let extraRouted := routedNames.filter fun name => !metadataNames.contains name
  if !extraRouted.isEmpty || !data.extraConstNames.isEmpty then
    throwError "BAYES_MODULE_CODEGEN_ONLY: routed extras={extraRouted}; metadata extras={data.extraConstNames}"
  unless metadataNames.all routedNames.contains && routedNames.all metadataNames.contains do
    throwError "BAYES_MODULE_OWNERSHIP: module data and all routed names disagree"
  let allowed : List Name := [``propext, ``Classical.choice, ``Quot.sound]
  let mut records : Array Json := #[]
  for name in metadataNames.mergeSort (fun a b => a.toString ≤ b.toString) do
    unless env.getModuleIdxFor? name == some index do
      throwError "BAYES_MODULE_OWNERSHIP: {name}"
    let some actual := env.find? name
      | throwError "BAYES_MODULE_KERNEL_ENTRY: {name}"
    if actual.isUnsafe || actual.isPartial then
      throwError "BAYES_MODULE_SAFETY: {name}"
    let .thmInfo proof := actual
      | throwError "BAYES_MODULE_KIND: first packet permits theorems only: {name}"
    unless closed proof.type && closed proof.value do
      throwError "BAYES_MODULE_CLOSED: {name}"
    let axioms ← collectAxioms name
    for assumption in axioms do
      unless allowed.contains assumption do
        throwError "BAYES_MODULE_AXIOM: {name} uses {assumption}"
    records := records.push (Json.mkObj [
      ("name", Json.str name.toString),
      ("owner_module", Json.str candidateModule.toString),
      ("kind", Json.str "theorem"),
      ("private_name", Json.bool (isPrivateName name)),
      ("universe_parameters", Json.arr (proof.levelParams.map (Json.str ∘ Name.toString)).toArray),
      ("axioms", namesJson axioms.toList)])
  return Json.mkObj [
    ("candidate_module", Json.str candidateModule.toString),
    ("direct_imports", Json.arr (data.imports.map importJson)),
    ("metadata_names", namesJson metadataNames),
    ("routed_names", namesJson routedNames),
    ("codegen_only_names", namesJson extraRouted),
    ("metadata_extra_names", namesJson data.extraConstNames.toList),
    ("declarations", Json.arr records),
    ("status", Json.str "all_candidate_module_declarations_checked")]

end SensorBayesModuleInventory
