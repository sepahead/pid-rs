import CountRaw
import AlphabetCounts
import Lean.Elab.Command
import Lean.Elab.BuiltinEvalCommand
import Lean.Meta.ExprDefEq
import Lean.Meta.WHNF
import Lean.Util.CollectAxioms
import Lean.Util.CollectLevelParams
import Lean.Util.InstantiateLevelParams

set_option autoImplicit false
set_option warningAsError true

-- First-stage predicate on the nine named definitions and 22 named theorems.
-- The stronger October whole-module/IR-custody and zero-trust protocol retains its HOLD.
namespace PidFin3CountConsumers
universe u v z

theorem sourceEvent_antitone : PidFin3CountRaw.sourceEvent_antitone.{u, z} :=
  @PidFin3AlphabetCounts.sourceEvent_antitone

theorem sourceEvent_key_iff : PidFin3CountRaw.sourceEvent_key_iff.{u, z} :=
  @PidFin3AlphabetCounts.sourceEvent_key_iff

theorem sourceEvent_data_congr : PidFin3CountRaw.sourceEvent_data_congr.{u, z} :=
  @PidFin3AlphabetCounts.sourceEvent_data_congr

theorem dnf_eq_sourceEvent : PidFin3CountRaw.dnf_eq_sourceEvent.{u, z} :=
  @PidFin3AlphabetCounts.dnf_eq_sourceEvent

theorem mass_mono : PidFin3CountRaw.mass_mono.{z} :=
  @PidFin3AlphabetCounts.mass_mono

theorem mass_le_total : PidFin3CountRaw.mass_le_total.{z} :=
  @PidFin3AlphabetCounts.mass_le_total

theorem key_weight_le_mass : PidFin3CountRaw.key_weight_le_mass.{z} :=
  @PidFin3AlphabetCounts.key_weight_le_mass

theorem mass_congr : PidFin3CountRaw.mass_congr.{z} :=
  @PidFin3AlphabetCounts.mass_congr

theorem total_congr : PidFin3CountRaw.total_congr.{z} :=
  @PidFin3AlphabetCounts.total_congr

theorem supported_key_source_mem : PidFin3CountRaw.supported_key_source_mem.{u, z} :=
  @PidFin3AlphabetCounts.supported_key_source_mem

theorem supported_key_joint_mem : PidFin3CountRaw.supported_key_joint_mem.{u, v, z} :=
  @PidFin3AlphabetCounts.supported_key_joint_mem

theorem supported_key_target_mem : PidFin3CountRaw.supported_key_target_mem.{v, z} :=
  @PidFin3AlphabetCounts.supported_key_target_mem

theorem V_le_U : PidFin3CountRaw.V_le_U.{u, v, z} :=
  @PidFin3AlphabetCounts.V_le_U

theorem U_le_N : PidFin3CountRaw.U_le_N.{u, z} :=
  @PidFin3AlphabetCounts.U_le_N

theorem V_le_T : PidFin3CountRaw.V_le_T.{u, v, z} :=
  @PidFin3AlphabetCounts.V_le_T

theorem T_le_N : PidFin3CountRaw.T_le_N.{v, z} :=
  @PidFin3AlphabetCounts.T_le_N

theorem key_le_V : PidFin3CountRaw.key_le_V.{u, v, z} :=
  @PidFin3AlphabetCounts.key_le_V

theorem supported_key_bounds : PidFin3CountRaw.supported_key_bounds.{u, v, z} :=
  @PidFin3AlphabetCounts.supported_key_bounds

theorem counts_positive : PidFin3CountRaw.counts_positive.{u, v, z} :=
  @PidFin3AlphabetCounts.counts_positive

theorem U_antitone : PidFin3CountRaw.U_antitone.{u, z} :=
  @PidFin3AlphabetCounts.U_antitone

theorem V_antitone : PidFin3CountRaw.V_antitone.{u, v, z} :=
  @PidFin3AlphabetCounts.V_antitone

theorem counts_congr_on_support : PidFin3CountRaw.counts_congr_on_support.{u, v, z} :=
  @PidFin3AlphabetCounts.counts_congr_on_support

end PidFin3CountConsumers

open Lean Meta Elab Command
namespace PidFin3CountJudge
abbrev SemanticMap := List (Name × Name)
private def candidateModule : Name := `AlphabetCounts
private def rawModule : Name := `CountRaw
private def judgeModule : Name := `CountEvidence
private def definitionStems : List String :=
  ["Observation", "sourceEvent", "eqPattern", "sourceEventDecidable",
   "mass", "N", "U", "V", "T"]

private def theoremStems : List String :=
  ["sourceEvent_antitone",
   "sourceEvent_key_iff",
   "sourceEvent_data_congr",
   "dnf_eq_sourceEvent",
   "mass_mono",
   "mass_le_total",
   "key_weight_le_mass",
   "mass_congr",
   "total_congr",
   "supported_key_source_mem",
   "supported_key_joint_mem",
   "supported_key_target_mem",
   "V_le_U",
   "U_le_N",
   "V_le_T",
   "T_le_N",
   "key_le_V",
   "supported_key_bounds",
   "counts_positive",
   "U_antitone",
   "V_antitone",
   "counts_congr_on_support"]

private def candidateName (stem : String) : Name :=
  .str `PidFin3AlphabetCounts stem

private def rawName (stem : String) : Name :=
  .str `PidFin3CountRaw stem

private def consumerName (stem : String) : Name :=
  .str `PidFin3CountConsumers stem

private def uniqueNames : List Name → Bool
  | [] => true
  | name :: rest => !rest.contains name && uniqueNames rest

private def ownerOf (env : Environment) (name : Name) : CoreM Name := do
  unless env.contains name do
    throwError "COUNT_MISSING_DECLARATION: {name}"
  match env.getModuleIdxFor? name with
  | none => return env.mainModule
  | some index =>
    match env.header.moduleNames[index.toNat]? with
    | some owner => return owner
    | none => throwError "COUNT_UNKNOWN_OWNER: {name}"

private def requireOwner (name owner : Name) : CoreM Unit := do
  let actual ← ownerOf (← getEnv) name
  unless actual == owner do
    throwError "COUNT_OWNER: {name} belongs to {actual}, expected {owner}"

private def checkClosed (name : Name) (levels : List Name)
    (expression : Expr) : CoreM Unit := do
  unless uniqueNames levels do
    throwError "COUNT_DUPLICATE_UNIVERSE: {name}"
  if expression.hasMVar || expression.hasLevelMVar ||
      expression.hasFVar || expression.hasLooseBVars then
    throwError "COUNT_OPEN_EXPRESSION: {name}"
  let used := (collectLevelParams {} expression).params
  for level in used do
    unless levels.contains level do
      throwError "COUNT_UNDECLARED_UNIVERSE: {name} uses {level}"

-- Erase only inert metadata; every other node/field is retained for comparison.
private def eraseMetadata : Expr → Expr
  | .mdata _ body => eraseMetadata body
  | .app fn arg => .app (eraseMetadata fn) (eraseMetadata arg)
  | .lam name type body info => .lam name (eraseMetadata type) (eraseMetadata body) info
  | .forallE name type body info =>
    .forallE name (eraseMetadata type) (eraseMetadata body) info
  | .letE name type value body nondep =>
    .letE name (eraseMetadata type) (eraseMetadata value) (eraseMetadata body) nondep
  | .proj name index body => .proj name index (eraseMetadata body)
  | expression => expression

private def mappedName : SemanticMap → Name → Name
  | [], name => name
  | (actual, raw) :: rest, name =>
    if name == actual then raw else mappedName rest name

-- DO NOT use Expr == here: its BEq also ignores BinderInfo (Expr.lean:804-812).
-- Structural recursion on the left tree; no reductions or isDefEq fallback.
-- Binder labels alone are ignored. Paths identify the first mismatching field.
private def astMismatch (mapping : SemanticMap) (path : String) :
    Expr → Expr → Option String
  | .bvar i, .bvar j => if i == j then none else some (path ++ ".index")
  | .sort u, .sort v => if u == v then none else some (path ++ ".level")
  | .const a us, .const b vs =>
    if mappedName mapping a != b then some (path ++ ".constant")
    else if us != vs then some (path ++ ".levels") else none
  | .app f a, .app g b =>
    astMismatch mapping (path ++ ".function") f g <|>
      astMismatch mapping (path ++ ".argument") a b
  | .lam _ d b i, .lam _ e c k =>
    if i != k then some (path ++ ".lambdaBinderInfo")
    else astMismatch mapping (path ++ ".lambdaDomain") d e <|>
      astMismatch mapping (path ++ ".lambdaBody") b c
  | .forallE _ d b i, .forallE _ e c k =>
    if i != k then some (path ++ ".forallBinderInfo")
    else astMismatch mapping (path ++ ".forallDomain") d e <|>
      astMismatch mapping (path ++ ".forallBody") b c
  | .letE _ t v b nd, .letE _ s w c ne =>
    if nd != ne then some (path ++ ".letNondep")
    else astMismatch mapping (path ++ ".letType") t s <|>
      astMismatch mapping (path ++ ".letValue") v w <|>
      astMismatch mapping (path ++ ".letBody") b c
  | .lit a, .lit b => if a == b then none else some (path ++ ".literal")
  | .proj a i x, .proj b k y =>
    if a != b || i != k then some (path ++ ".projection")
    else astMismatch mapping (path ++ ".projectionBody") x y
  | _, _ => some (path ++ ".constructorOrOpenTerm")

private def rigidLevels (count : Nat) : List Level :=
  (List.range count).map fun index => .param (.num `PidCountRigid index)

private def requireEquivalent (mapping : SemanticMap) (label : String) (name : Name)
    (actual : Expr) (actualLevels : List Name)
    (expected : Expr) (expectedLevels : List Name) : CoreM Unit := do
  checkClosed name actualLevels actual
  checkClosed name expectedLevels expected
  unless actualLevels.length == expectedLevels.length do
    throwError "COUNT_{label}_UNIVERSE_ARITY: {name}"
  let levels := rigidLevels actualLevels.length
  let left := actual.instantiateLevelParams actualLevels levels
  let right := expected.instantiateLevelParams expectedLevels levels
  if let some path := astMismatch mapping "root" (eraseMetadata left) (eraseMetadata right) then
    throwError "COUNT_{label}_AST: {name} differs at {path}"
  -- Additional semantic guard on ORIGINAL operands, not name-rewritten terms.
  let semantic ← MetaM.run' (ctx := {}) (s := {}) do
    withTransparency .all <| isDefEq left right
  unless semantic do
    throwError "COUNT_{label}_DEFEQ: {name}"

private def checkedAxioms (name : Name) : CoreM (Array Name) := do
  let allowed : List Name := [``propext, ``Classical.choice, ``Quot.sound]
  let found ← collectAxioms name
  for assumption in found do
    unless allowed.contains assumption do
      throwError "COUNT_AXIOM: {name} uses {assumption}"
  return (found.toList.mergeSort fun left right =>
    left.toString ≤ right.toString).toArray

private def requireSafeDefinition (name : Name) : CoreM DefinitionVal := do
  let info ← getConstInfo name
  match info with
  | .defnInfo value =>
    unless value.safety == .safe do
      throwError "COUNT_UNSAFE_OR_PARTIAL: {name}"
    checkClosed name value.levelParams value.type
    checkClosed name value.levelParams value.value
    let _ ← checkedAxioms name
    return value
  | _ => throwError "COUNT_DEFINITION_KIND: {name} is not a safe definition"

private def requireTheorem (name : Name) : CoreM TheoremVal := do
  let info ← getConstInfo name
  match info with
  | .thmInfo value =>
    checkClosed name value.levelParams value.type
    checkClosed name value.levelParams value.value
    let _ ← checkedAxioms name
    return value
  | _ => throwError "COUNT_THEOREM_KIND: {name} is not a theorem"

private def rawTarget (name : Name) : CoreM DefinitionVal := do
  requireOwner name rawModule
  let value ← requireSafeDefinition name
  -- No outer data binders on the raw declaration: all binders are in its value.
  unless value.type == Expr.sort Level.zero do
    throwError "COUNT_RAW_NOT_CLOSED_PROP: {name}"
  return value

private def checkDefinition (mapping : SemanticMap) (stem : String) : CoreM SemanticMap := do
  let actualName := candidateName stem
  let independentName := rawName stem
  requireOwner actualName candidateModule
  requireOwner independentName rawModule
  let actual ← requireSafeDefinition actualName
  let independent ← requireSafeDefinition independentName
  -- Only EARLIER independently checked definitions can be mapped here.
  requireEquivalent mapping "DEFINITION_TYPE" actualName
    actual.type actual.levelParams independent.type independent.levelParams
  requireEquivalent mapping "DEFINITION_BODY" actualName
    actual.value actual.levelParams independent.value independent.levelParams
  return mapping ++ [(actualName, independentName)]

private def referencedConstants : Expr → List Name
  | .const name _ => [name]
  | .proj name _ expression => name :: referencedConstants expression
  | .app fn argument => referencedConstants fn ++ referencedConstants argument
  | .lam _ domain body _ => referencedConstants domain ++ referencedConstants body
  | .forallE _ domain body _ => referencedConstants domain ++ referencedConstants body
  | .letE _ type value body _ =>
    referencedConstants type ++ referencedConstants value ++ referencedConstants body
  | .mdata _ body => referencedConstants body
  | _ => []

private def checkRawIndependence : CoreM Unit := do
  let env ← getEnv
  for (name, info) in env.constants.toList do
    if (← ownerOf env name) == rawModule then
      let mut expressions := [info.type]
      if let some value := info.value? (allowOpaque := true) then
        expressions := value :: expressions
      for expression in expressions do
        for referenced in referencedConstants expression do
          if (← ownerOf env referenced) == candidateModule then
            throwError "COUNT_RAW_CANDIDATE_REFERENCE: {name} refers to {referenced}"

private def renderClosed (expression : Expr) : CoreM String :=
  MetaM.run' (ctx := {}) (s := {}) do
    let rendered ← withOptions (fun options =>
      options.setBool `pp.all true |>.setBool `pp.universes true |>.setBool `pp.proofs true
        |>.setBool `pp.deepTerms true |>.set `pp.maxSteps (100000 : Nat) |>.set `pp.width (160 : Nat)) <|
        ppExpr expression
    return rendered.pretty


-- The only extra name correspondence. Its two owners and complete bodies are verified
-- before its pair may occur in a comparison of any ordinary definition or theorem.
private def helperActual : Name := `PidFin3AlphabetCounts.sourceEventDecidable._aux_1
private def helperRaw : Name := `PidFin3CountRaw.sourceEventDecidable._aux_1

private def publicPair (stem : String) : Name × Name := (candidateName stem, rawName stem)

private def helperPredecessors : List String := ["Observation", "sourceEvent", "eqPattern"]

private def checkRegisteredHelper (mapping : SemanticMap) : CoreM (SemanticMap × Json) := do
  unless mapping == helperPredecessors.map publicPair do
    throwError "COUNT_HELPER_PREDECESSORS: exactly three checked prior definitions required"
  requireOwner helperActual candidateModule
  requireOwner helperRaw rawModule
  let actual ← requireSafeDefinition helperActual
  let raw ← requireSafeDefinition helperRaw
  unless actual.levelParams.length == 2 && raw.levelParams.length == 2 do
    throwError "COUNT_HELPER_UNIVERSE_ARITY: required two ordered levels"
  requireEquivalent mapping "HELPER_TYPE" helperActual
    actual.type actual.levelParams raw.type raw.levelParams
  requireEquivalent mapping "HELPER_BODY" helperActual
    actual.value actual.levelParams raw.value raw.levelParams
  let actualParentName := candidateName "sourceEventDecidable"
  let rawParentName := rawName "sourceEventDecidable"
  requireOwner actualParentName candidateModule
  requireOwner rawParentName rawModule
  let actualParent ← requireSafeDefinition actualParentName
  let rawParent ← requireSafeDefinition rawParentName
  unless (referencedConstants actualParent.value).contains helperActual &&
      (referencedConstants rawParent.value).contains helperRaw do
    throwError "COUNT_HELPER_PARENT_REFERENCE: each parent must use its registered helper"
  let row := Json.mkObj [
    ("kind", toJson ("safe_definition_pair" : String)),
    ("candidate_helper", toJson helperActual.toString), ("raw_helper", toJson helperRaw.toString),
    ("candidate_owner", toJson candidateModule.toString), ("raw_owner", toJson rawModule.toString),
    ("candidate_parent", toJson actualParentName.toString), ("raw_parent", toJson rawParentName.toString),
    ("predecessors", toJson helperPredecessors),
    ("candidate_universes", toJson (actual.levelParams.map Name.toString)),
    ("raw_universes", toJson (raw.levelParams.map Name.toString)),
    ("candidate_type", toJson (← renderClosed actual.type)), ("candidate_body", toJson (← renderClosed actual.value)),
    ("raw_type", toJson (← renderClosed raw.type)), ("raw_body", toJson (← renderClosed raw.value)),
    ("axioms", toJson ((← checkedAxioms helperActual).map Name.toString)),
    ("raw_axioms", toJson ((← checkedAxioms helperRaw).map Name.toString))]
  return (mapping ++ [(helperActual, helperRaw)], row)

-- Unfold only the designated raw Prop wrapper, never arbitrary aliases/whnf.
private def consumerTarget (raw : DefinitionVal) (expression : Expr) : CoreM Expr := do
  match expression.consumeMData with
  | .const name levels =>
    unless name == raw.name && levels.length == raw.levelParams.length do
      throwError "COUNT_CONSUMER_RAW_WRAPPER: {name}"
    return raw.value.instantiateLevelParams raw.levelParams levels
  | _ => throwError "COUNT_CONSUMER_NOT_RAW_WRAPPER"

private def describeTheorem (mapping : SemanticMap) (stem : String) : CoreM Json := do
  let declaration := candidateName stem
  let consumer := consumerName stem
  requireOwner declaration candidateModule
  requireOwner consumer judgeModule
  let expected ← rawTarget (rawName stem)
  let actual ← requireTheorem declaration
  let consumed ← requireTheorem consumer
  requireEquivalent mapping "THEOREM_TYPE" declaration actual.type actual.levelParams
    expected.value expected.levelParams
  let expanded ← consumerTarget expected consumed.type
  requireEquivalent [] "CONSUMER_TYPE" consumer expanded consumed.levelParams
    expected.value expected.levelParams
  let actualAxioms ← checkedAxioms declaration
  let consumerAxioms ← checkedAxioms consumer
  return Json.mkObj [
    ("theorem", Json.str declaration.toString),
    ("kind", Json.str "theorem"),
    ("raw_target", Json.str (rawName stem).toString),
    ("consumer", Json.str consumer.toString),
    ("candidate_universes", Json.arr (actual.levelParams.map (Json.str ∘ Name.toString)).toArray),
    ("raw_universes", Json.arr (expected.levelParams.map (Json.str ∘ Name.toString)).toArray),
    ("consumer_universes", Json.arr (consumed.levelParams.map (Json.str ∘ Name.toString)).toArray),
    ("full_type", Json.str (← renderClosed actual.type)),
    ("raw_full_target", Json.str (← renderClosed expected.value)),
    ("consumer_full_type", Json.str (← renderClosed consumed.type)),
    ("axioms", Json.arr (actualAxioms.map (Json.str ∘ Name.toString))),
    ("consumer_axioms", Json.arr (consumerAxioms.map (Json.str ∘ Name.toString))),
    ("status", Json.str "matched_exact_scoped_type")]

private def describeDefinition (stem : String) : CoreM Json := do
  let name := candidateName stem
  let raw := rawName stem
  let actual ← requireSafeDefinition name
  let expected ← requireSafeDefinition raw
  return Json.mkObj [
    ("definition", toJson name.toString), ("raw_definition", toJson raw.toString),
    ("kind", toJson ("definition" : String)),
    ("candidate_universes", toJson (actual.levelParams.map Name.toString)),
    ("raw_universes", toJson (expected.levelParams.map Name.toString)),
    ("candidate_type", toJson (← renderClosed actual.type)),
    ("candidate_body", toJson (← renderClosed actual.value)),
    ("raw_type", toJson (← renderClosed expected.type)),
    ("raw_body", toJson (← renderClosed expected.value)),
    ("axioms", toJson ((← checkedAxioms name).map Name.toString)),
    ("raw_axioms", toJson ((← checkedAxioms raw).map Name.toString))]

def checkNamedEvidence : CoreM Unit := do
  let env ← getEnv
  unless env.mainModule == judgeModule do
    throwError "COUNT_WRONG_MAIN_MODULE: {env.mainModule}"
  unless definitionStems.length == 9 && theoremStems.length == 22 &&
      uniqueNames (definitionStems.map candidateName) &&
      uniqueNames (theoremStems.map candidateName) do
    throwError "COUNT_KNOWN_ROSTER_MALFORMED"
  checkRawIndependence
  let mut checked : SemanticMap := []
  let mut definitions : Array Json := #[]
  let mut helper? : Option Json := none
  for stem in definitionStems do
    if stem == "sourceEventDecidable" then
      let (extended, row) ← checkRegisteredHelper checked
      checked := extended
      helper? := some row
    checked ← checkDefinition checked stem
    definitions := definitions.push (← describeDefinition stem)
  let some helper := helper? | throwError "COUNT_HELPER_ROW_MISSING"
  let expectedMap := helperPredecessors.map publicPair ++ [(helperActual, helperRaw)] ++
    (definitionStems.drop 3).map publicPair
  unless checked == expectedMap do
    throwError "COUNT_INCOMPLETE_DEFINITION_MAP"
  let mut theorems : Array Json := #[]
  for stem in theoremStems do
    theorems := theorems.push (← describeTheorem checked stem)
  IO.println ("COUNT22_HELPER " ++ helper.compress)
  for row in definitions do
    IO.println ("COUNT22_DEFINITION " ++ row.compress)
  for row in theorems do
    IO.println ("COUNT22_THEOREM " ++ row.compress)

end PidFin3CountJudge

run_cmd liftTermElabM do
  PidFin3CountJudge.checkNamedEvidence

run_elab do
  let env ← getEnv
  let modules ← env.header.modules.mapM fun imported => do
    let olean ← _root_.liftM (m := IO) (n := Lean.Elab.Term.TermElabM) <| findOLean imported.module
    pure <| Json.mkObj [
      ("module", toJson imported.module.toString),
      ("olean", toJson olean.toString),
      ("meta", toJson imported.isMeta),
      ("exported", toJson imported.isExported),
      ("all", toJson imported.importAll),
      ("has_data", toJson imported.hasData)]
  let regions := env.header.regions.map fun region => Json.mkObj [
    ("path", toJson region.filePath.toString),
    ("mapped_bytes", toJson region.size.toNat),
    ("memory_mapped", toJson region.isMemoryMapped)]
  let direct := env.header.imports.map fun imported => Json.mkObj [
    ("module", toJson imported.module.toString),
    ("meta", toJson imported.isMeta),
    ("exported", toJson imported.isExported),
    ("all", toJson imported.importAll)]
  let report := Json.mkObj [
    ("schema", toJson "count22-exact-objects-helper-v3"),
    ("lean_version", toJson Lean.versionString),
    ("lean_githash", toJson Lean.githash),
    ("main_module", toJson env.header.mainModule.toString),
    ("header_trust_level", toJson env.header.trustLevel.toNat),
    ("direct_imports", Json.arr direct),
    ("modules", Json.arr modules),
    ("regions", Json.arr regions)]
  _root_.liftM (m := IO) (n := Lean.Elab.Term.TermElabM) <| IO.println ("COUNT22_IMPORTS " ++ report.compress)
