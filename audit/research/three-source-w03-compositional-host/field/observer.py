"""Render the protected expression, receiving-owner and transitive-axiom observers."""
from terms import STAGES
from common import HERE,decode
from modules import PRE
def refs(scientific,authority=False):
    return (['W03Scope.'+k for k in STAGES]+['W03Authority.'+k for k in STAGES] if authority else
            ['W03'+k+'.result' for k in STAGES]+['W03Consumer.accept'+k for k in STAGES])
def native(scientific,authority=False):
    module='W03Authority' if authority else 'W03Consumer'
    names=refs(scientific,authority)
    group=(list(PRE) if scientific else ['W03Scope'])+['W03Authority']
    if not authority:group+=['W03'+k for k in STAGES]+['W03Consumer']
    fields='['+', '.join('`'+n for n in names)+']';gr='['+', '.join('`'+n for n in group)+']'
    start='import '+module+'\nimport Lean.Elab.Command\nimport Lean.Util.FoldConsts\nimport Lean.Util.CollectAxioms\nopen Lean Elab Command\n'
    fixed=decode((HERE/'compiler_roster.json').read_bytes())
    permitted='['+', '.join('"'+x+'"' for x in fixed['W02Semantics'])+']'
    code=r'''
set_option maxRecDepth 65536
set_option maxHeartbeats 20000000

def formalDependencyNames (env : Environment) (start : Name) : CommandElabM (List Name × List Name) := do
  let mut todo := [start]
  let mut seen : NameSet := {}
  let mut assumptions : List Name := []
  while !todo.isEmpty do
    let c := todo.head!
    todo := todo.tail!
    if seen.contains c then continue
    seen := seen.insert c
    let some ci := env.checked.get.find? c | throwError "missing formal dependency {c}"
    if ci.isUnsafe || ci.isPartial then throwError "ineligible formal dependency {c}"
    let mut deps := ci.type.getUsedConstants.toList
    if let some e := ci.value? true then deps := e.getUsedConstants.toList ++ deps
    match ci with
    | .axiomInfo _ => assumptions := c :: assumptions
    | .inductInfo i => deps := i.all ++ i.ctors ++ deps
    | .ctorInfo k => deps := k.induct :: deps
    | .recInfo r =>
      deps := r.all ++ deps
      for rule in r.rules do
        deps := rule.ctor :: (rule.rhs.getUsedConstants.toList ++ deps)
    | _ => pure ()
    todo := deps ++ todo
  return (seen.toList, assumptions)

run_cmd do
  let env := (← getEnv).setExporting false
  if env.header.isModule then throwError "expected original import mode"
  for owner in (GROUPS : List Name) do
    let some ix := env.getModuleIdx? owner | throwError "missing owner {owner}"
    let co := env.header.moduleData[ix.toNat]!
    let how := env.header.modules[ix.toNat]!
    unless how.importAll && how.hasData && !co.isModule do throwError "visibility"
    let names := co.constNames.toList
    let sort := fun (ns : List Name) => (ns.map Name.toString).mergeSort (· ≤ ·)
    let routes := env.const2ModIdx.toList.filterMap (fun (k,i) => if i == ix then some k else none)
    unless names == co.constants.toList.map (·.name) && names.eraseDups.length == names.length &&
      sort routes == sort (names ++ co.extraConstNames.toList) do throwError "module roster {owner}"
    let mut auxiliaries : List String := []
    for ci in co.constants do
      if ci.isUnsafe || ci.isPartial then
        unless owner == `W02Semantics && !ci.isUnsafe && ci.isPartial do throwError "undeclared code-generator helper {ci.name}"
        auxiliaries := ci.name.toString :: auxiliaries
      match ci with
      | .axiomInfo _ => throwError "project axiom {ci.name}"
      | _ => pure ()
    let sealed : List String := if owner == `W02Semantics then PERMITTED else []
    unless auxiliaries.mergeSort (· ≤ ·) == sealed do throwError "changed fixed compiler helper inventory"
    IO.println ("W03_OWNER " ++ (Json.mkObj [("owner",toJson owner.toString),("compiler",toJson sealed),("kernel",toJson (sort names)),("extra",toJson (sort co.extraConstNames.toList))]).compress)
  for n in (NAMES : List Name) do
    let ci ← getConstInfo n
    let some owner := env.getModuleIdxFor? n | throwError "missing theorem owner {n}"
    let (val, kind) ← match ci with
      | .defnInfo d => pure (d.value, "definition")
      | .thmInfo d => pure (d.value, "theorem")
      | _ => throwError "unexpected declaration {n}"
    let ty := ci.type
    for x in [ty, val] do
      if x.hasMVar || x.hasLevelMVar || x.hasFVar || x.hasLooseBVars then throwError "open expression {n}"
    let sorted := fun (ns : List Name) => (ns.map Name.toString).mergeSort (· ≤ ·)
    let (reachable,assumptions) ← formalDependencyNames env n
    let fromTerms := sorted assumptions
    let ax := sorted (← collectAxioms n).toList
    unless fromTerms == ax do throwError "formal closure and printed axiom collector disagree at {n}"
    unless ax.all (fun a => ["Classical.choice","Quot.sound","propext"].contains a) do throwError "unapproved transitive axiom {n}"
    IO.println ("W03_EXPR " ++ (Json.mkObj [
      ("name", toJson n.toString), ("owner", toJson (env.header.moduleNames[owner.toNat]!).toString),
      ("trust",toJson env.header.trustLevel.toNat), ("kind",toJson kind),
      ("levels",toJson (ci.levelParams.map Name.toString)),("type",toJson (reprStr ty)),("value",toJson (reprStr val)),
      ("type_deps",toJson (sorted ty.getUsedConstantsAsSet.toList)),("value_deps",toJson (sorted val.getUsedConstantsAsSet.toList)),("axioms",toJson ax),("formal_closure",toJson (sorted reachable))]).compress)
'''
    return start+code.replace('GROUPS',gr).replace('NAMES',fields).replace('PERMITTED',permitted)
def axioms(scientific,authority=False):
    return 'import '+('W03Authority' if authority else 'W03Consumer')+'\n'+'\n'.join('#print axioms '+n for n in refs(scientific,authority))+'\n'
def trace():
    return '''import W03Scope
open W03Scope SmtW02
set_option maxRecDepth 65536
set_option maxHeartbeats 20000000
def traceCode (r : Option (List Bool)) : Nat :=
  match r with
  | some [p, q] => (if p then 2 else 0) + (if q then 1 else 0)
  | _ => 4
'''+'\n'.join('#reduce traceCode (evaluate originalScript (extend (⟨'+str(i)+', by decide⟩ : Family)))' for i in range(128))+'\n'
