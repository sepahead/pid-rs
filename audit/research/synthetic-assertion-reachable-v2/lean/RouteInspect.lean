import RouteConsumer
import Lean.Elab.Command
import Lean.Util.FoldConsts
import Lean.Util.CollectAxioms
open Lean Elab Command

run_cmd do
  let env ← getEnv
  let targets : List Name := [`RouteHelpers.wellFormedInputs, `RouteHelpers.prefixBit, `RouteHelpers.prefixTag, `RouteHelpers.evalViaRelay, `RouteHelpers.witnessInputs, `RouteHelpers.leafFalse, `RouteHelpers.leafTrue, `RouteHelpers.changedUse, `RouteHelpers.failedSource, `RouteResult.ordered, `RouteResult.sameOutput, `RouteResult.environmentsDiffer, `RouteResult.counterexample, `RouteResult.allRefute, `RouteConsumer.formation, `RouteConsumer.ordered, `RouteConsumer.invariance, `RouteConsumer.difference, `RouteConsumer.counterexample, `RouteConsumer.successful, `RouteConsumer.reachableTag, `RouteConsumer.typedFailure]
  for n in targets do
    let ci ← getConstInfo n
    let .thmInfo thm := ci | throwError "expected named theorem {n}"
    let some owner := env.getModuleIdxFor? n | throwError "missing owner of {n}"
    let ty := thm.type
    let val := thm.value
    for x in [ty,val] do
      if x.hasMVar || x.hasLevelMVar || x.hasFVar || x.hasLooseBVars then
        throwError "open kernel expression at {n}"
    let sorted := fun (s : List Name) => (s.map Name.toString).mergeSort (· ≤ ·)
    let row := Json.mkObj [("name", toJson n.toString), ("owner", toJson (env.header.moduleNames[owner.toNat]!).toString),
      ("ordinary_import_trust",toJson env.header.trustLevel.toNat), ("kind",toJson "theorem"),
      ("universe_parameters",toJson (thm.levelParams.map Name.toString)),
      ("type_constructor_representation",toJson (reprStr ty)), ("value_constructor_representation",toJson (reprStr val)),
      ("type_constants",toJson (sorted ty.getUsedConstantsAsSet.toList)),
      ("value_constants",toJson (sorted val.getUsedConstantsAsSet.toList)),
      ("direct_type_axioms",toJson (sorted (ty.getUsedConstantsAsSet.toList.filter (fun d => match env.find? d with | some (.axiomInfo _) => true | _ => false)))),
      ("direct_value_axioms",toJson (sorted (val.getUsedConstantsAsSet.toList.filter (fun d => match env.find? d with | some (.axiomInfo _) => true | _ => false)))),
      ("axioms",toJson (sorted (← collectAxioms n).toList))]
    IO.println ("W02_TERM " ++ row.compress)
