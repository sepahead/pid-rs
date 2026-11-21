import IndexConsumer
import Lean.Elab.Command
import Lean.Util.FoldConsts
import Lean.Util.CollectAxioms
open Lean Elab Command

set_option maxRecDepth 65536
set_option maxHeartbeats 20000000

run_cmd do
  let env ← getEnv
  let targets : List Name := [`IndexExample.leaf00, `IndexExample.leaf01, `IndexExample.leaf02, `IndexExample.leaf03, `IndexExample.leaf04, `IndexExample.leaf05, `IndexExample.leaf06, `IndexExample.leaf07, `IndexExample.leaf08, `IndexExample.leaf09, `IndexExample.leaf10, `IndexExample.leaf11, `IndexExample.leaf12, `IndexExample.leaf13, `IndexExample.leaf14, `IndexExample.leaf15, `IndexExample.leaf16, `IndexExample.leaf17, `IndexExample.leaf18, `IndexExample.leaf19, `IndexExample.leaf20, `IndexExample.leaf21, `IndexExample.leaf22, `IndexExample.leaf23, `IndexExample.leaf24, `IndexExample.leaf25, `IndexExample.leaf26, `IndexExample.leaf27, `IndexExample.leaf28, `IndexExample.leaf29, `IndexExample.leaf30, `IndexExample.leaf31, `IndexExample.leaf32, `IndexExample.leaf33, `IndexExample.leaf34, `IndexExample.leaf35, `IndexExample.leaf36, `IndexExample.leaf37, `IndexExample.leaf38, `IndexExample.leaf39, `IndexExample.leaf40, `IndexExample.leaf41, `IndexExample.leaf42, `IndexExample.leaf43, `IndexExample.leaf44, `IndexExample.leaf45, `IndexExample.leaf46, `IndexExample.leaf47, `IndexExample.leaf48, `IndexExample.leaf49, `IndexExample.leaf50, `IndexExample.leaf51, `IndexExample.leaf52, `IndexExample.leaf53, `IndexExample.leaf54, `IndexExample.leaf55, `IndexExample.leaf56, `IndexExample.leaf57, `IndexExample.leaf58, `IndexExample.leaf59, `IndexExample.leaf60, `IndexExample.leaf61, `IndexExample.leaf62, `IndexExample.leaf63, `IndexExample.leaf64, `IndexExample.leaf65, `IndexExample.leaf66, `IndexExample.leaf67, `IndexExample.leaf68, `IndexExample.leaf69, `IndexExample.leaf70, `IndexExample.leaf71, `IndexExample.leaf72, `IndexExample.leaf73, `IndexExample.leaf74, `IndexExample.leaf75, `IndexExample.leaf76, `IndexExample.leaf77, `IndexExample.leaf78, `IndexExample.leaf79, `IndexExample.leaf80, `IndexExample.leaf81, `IndexExample.leaf82, `IndexExample.cover83, `IndexExample.cover82, `IndexExample.cover81, `IndexExample.cover80, `IndexExample.cover79, `IndexExample.cover78, `IndexExample.cover77, `IndexExample.cover76, `IndexExample.cover75, `IndexExample.cover74, `IndexExample.cover73, `IndexExample.cover72, `IndexExample.cover71, `IndexExample.cover70, `IndexExample.cover69, `IndexExample.cover68, `IndexExample.cover67, `IndexExample.cover66, `IndexExample.cover65, `IndexExample.cover64, `IndexExample.cover63, `IndexExample.cover62, `IndexExample.cover61, `IndexExample.cover60, `IndexExample.cover59, `IndexExample.cover58, `IndexExample.cover57, `IndexExample.cover56, `IndexExample.cover55, `IndexExample.cover54, `IndexExample.cover53, `IndexExample.cover52, `IndexExample.cover51, `IndexExample.cover50, `IndexExample.cover49, `IndexExample.cover48, `IndexExample.cover47, `IndexExample.cover46, `IndexExample.cover45, `IndexExample.cover44, `IndexExample.cover43, `IndexExample.cover42, `IndexExample.cover41, `IndexExample.cover40, `IndexExample.cover39, `IndexExample.cover38, `IndexExample.cover37, `IndexExample.cover36, `IndexExample.cover35, `IndexExample.cover34, `IndexExample.cover33, `IndexExample.cover32, `IndexExample.cover31, `IndexExample.cover30, `IndexExample.cover29, `IndexExample.cover28, `IndexExample.cover27, `IndexExample.cover26, `IndexExample.cover25, `IndexExample.cover24, `IndexExample.cover23, `IndexExample.cover22, `IndexExample.cover21, `IndexExample.cover20, `IndexExample.cover19, `IndexExample.cover18, `IndexExample.cover17, `IndexExample.cover16, `IndexExample.cover15, `IndexExample.cover14, `IndexExample.cover13, `IndexExample.cover12, `IndexExample.cover11, `IndexExample.cover10, `IndexExample.cover09, `IndexExample.cover08, `IndexExample.cover07, `IndexExample.cover06, `IndexExample.cover05, `IndexExample.cover04, `IndexExample.cover03, `IndexExample.cover02, `IndexExample.cover01, `IndexExample.cover00, `IndexExample.inlineComplete, `IndexExample.namedResult, `IndexExample.singleSlotResult]
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
