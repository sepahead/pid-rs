"""Render the fixed Lean statements and proof-only module templates for the three cases."""

from pathlib import Path

OPTIONS = "set_option maxRecDepth 65536\nset_option maxHeartbeats 20000000\n"
CASES = ("W01", "W03", "W15")
SOURCE = "SmtW02.originalScript"
OPEN = "open SmtW02 ArchivedProjection OriginalPrefix OriginalContract\n"
PRELUDE = "import OriginalPrefix\nimport ProjectionReification\n\n" + OPTIONS + "\nnamespace OriginalContract\nopen SmtW02 ArchivedProjection OriginalPrefix\n\n"
NAT_REFERENCE = """def indices : List Nat := [1, 2, 3, 4, 5, 6, 7]
def hasMember (family : Nat) (set : Nat) : Bool := family.testBit (set - 1)
def subsetBits (u v : Nat) : Bool := Nat.land u v == u

def validMask (x : Fin 128) : Bool :=
  x.val != 0 && indices.all (fun u => indices.all (fun v =>
    !(decide (u < v) && hasMember x.val u && hasMember x.val v &&
      (subsetBits u v || subsetBits v u))))
"""
CANONICAL = """def canonicalMask (x : Fin 128) : Bool :=
  ([1, 2, 4, 8, 16, 32, 64, 3, 9, 33, 10, 18, 12, 20, 36, 48, 11, 52] : List Nat).contains x.val
"""
ORDER = """def sourceOrder (a b : Fin 128) : Bool :=
  indices.all (fun v => !(hasMember b.val v) ||
    indices.any (fun u => hasMember a.val u && subsetBits u v))
"""
CELLS = """def sourceBits (x : A) (s : Nat) : Bool :=
  (x.1.val.testBit s == x.2.val.testBit s)
def fullMaskEvent (x : A) : Bool :=
  ([1, 2, 3, 4, 5, 6, 7] : List Nat).any (fun u =>
    (64 : Nat).testBit (u - 1) &&
    ((!(u.testBit 0) || sourceBits x 3) && (!(u.testBit 1) || sourceBits x 2) &&
      (!(u.testBit 2) || sourceBits x 1)))
def explicitAgreement (x : A) : Bool :=
  sourceBits x 3 && sourceBits x 2 && sourceBits x 1
"""
ENVIRONMENT = """def sourceEnvironment (rho : Valuation originalScript) : Option DynamicState :=
  (commands.take 82).foldlM (dynamicStep (valuationLookup (declarations originalScript) rho)) {}

def sourceCall (rho : Valuation originalScript) (name : String) (args : List Value) : Option Bool := do
  let state ← sourceEnvironment rho
  let fn ← state.globals.lookup name
  (← fn args).getBool

def dynamicBody (rho : Valuation originalScript) : Option (List Bool) := do
  let state ← commands.foldlM (dynamicStep (valuationLookup (declarations originalScript) rho)) ({} : DynamicState)
  return state.assertedRev.reverse
"""

def prefix(typed, writer):
    commands = typed[2:-2]
    lines = ["import OriginalLiteral", "", OPTIONS, "namespace OriginalPrefix", "open SmtW02", "",
             "def state0 : StaticState := {}", ""]
    for i, cmd in enumerate(commands):
        lines.append(f"def cmd{i} : Cmd := " + writer.lean_cmd(cmd))
        if cmd[0] in ("constant", "define"):
            name = writer.lean_str(cmd[1])
            args = "[]" if cmd[0] == "constant" else writer.many(writer.lean_sort(t) for _, t in cmd[2])
            result = writer.lean_sort(cmd[2] if cmd[0] == "constant" else cmd[3])
            update = f"globals := ({name}, {args}, {result}) :: state{i}.globals"
        elif cmd[0] == "echo":
            update = "echoSeen := true"
        elif cmd[0] == "assertion":
            update = f"nassert := state{i}.nassert + 1"
        else:
            raise ValueError("unknown active command")
        lines.append(f"def state{i+1} : StaticState := {{state{i} with {update}}}")
    lines += ["", "def commands : List Cmd := [" + ", ".join(f"cmd{i}" for i in range(len(commands))) + "]",
              "", "end OriginalPrefix", ""]
    return "\n".join(lines)

def contract(case, typed, writer):
    unary = case != "W15"
    lines = [PRELUDE, "abbrev A := " + ("Fin 128" if unary else "Fin 16 × Fin 16")]
    for name, index in ([("slotA",0)] if unary else [("slotK",6),("slotR",7)]):
        lines.append(f"def {name} : Fin (declarations originalScript).length := ⟨{index}, by decide⟩")
    if unary:
        lines += ["def pack (rho : Valuation originalScript) : A := (rho slotA).toFin",
                  "def extend (x : A) : Valuation originalScript := put originalScript slotA (BitVec.ofFin x) (zeroValuation originalScript)",
                  "", NAT_REFERENCE, CANONICAL if case == "W01" else ORDER]
    else:
        lines += ["def pack (rho : Valuation originalScript) : A := ((rho slotK).toFin, (rho slotR).toFin)",
                  "def extend (x : A) : Valuation originalScript := put originalScript slotK (BitVec.ofFin x.1)",
                  "  (put originalScript slotR (BitVec.ofFin x.2) (zeroValuation originalScript))", "", CELLS]
    lines += [ENVIRONMENT, """theorem consStep {c : Cmd} {cs : List Cmd} {a b z : StaticState}
    (h : staticStep a c = some b) (tail : cs.foldlM staticStep b = some z) :
    (c :: cs).foldlM staticStep a = some z := by
  rw [List.foldlM_cons, h]
  exact tail

theorem finishStatic {script cmds : List Cmd} {z : StaticState}
    (shape : currentCommands script = some cmds)
    (steps : cmds.foldlM staticStep {} = some z)
    (ends : (z.echoSeen && z.nassert == 2) = true) : wellFormed script = true := by
  unfold SmtW02.wellFormed
  rw [shape]
  change (match cmds.foldlM staticStep {} with
    | some st => st.echoSeen && st.nassert == 2
    | none => false) = true
  rw [steps] <;> exact ends
"""]
    if case == "W15":
        equality=typed[-3][1][3][0]
        if equality[:3]!=["app",["bool"],"="] or len(equality[3])!=2:
            raise ValueError("W15 must preserve both equality operands")
        raw_right=equality[3][1]
        if raw_right[:3]!=["app",["bool"],"and"] or len(raw_right[3])!=3:
            raise ValueError("W15 must preserve three literal comparisons")
        lines += ['def leftAt (rho : Valuation originalScript) : Option Bool :=',
                  '  sourceCall rho "raw-source" [.bits 7 64, .bits 4 (pack rho).1.val, .bits 4 (pack rho).2.val]',
                  'def sourceRightTerm : Term := '+writer.lean_term(raw_right),
                  'def rightAt (rho : Valuation originalScript) : Option Bool := do',
                  '  let state ← sourceEnvironment rho',
                  '  (← evaluateTerm sourceRightTerm state.globals).getBool']
    else:
        lines += ['def leftAt (rho : Valuation originalScript) : Option Bool :=',
                  '  sourceCall rho "valid" [.bits 7 (pack rho).val]']
        lines += ['def rightAt (rho : Valuation originalScript) : Option Bool :=', (
            '  sourceCall rho "canonical" [.bits 7 (pack rho).val]' if case == "W01" else
            '  sourceCall rho "leq" [.bits 7 (pack rho).val, .bits 7 (pack rho).val]')]
    left, right = reference(case, "x")
    if case == "W03":
        observed = f"some [{left}, !({right})]"
    else:
        observed = f"some [true, !(({left}) == ({right}))]"
    lines += ["def observe (x : A) : Option (List Bool) := " + observed, "", "end OriginalContract", ""]
    return "\n".join(lines)

def reference(case, x):
    if case == "W15":
        return "fullMaskEvent "+x, "explicitAgreement "+x
    return "validMask "+x, ("canonicalMask "+x if case == "W01" else "sourceOrder "+x+" "+x)

def types(case):
    s=SOURCE
    a="OriginalContract.A"
    project,extend,observe="OriginalContract.pack","OriginalContract.extend","OriginalContract.observe"
    ev="SmtW02.evaluate "+s
    val="SmtW02.Valuation "+s
    ref="ArchivedProjection.RefutesTwo"
    left,right=reference(case,"("+project+" rho)")
    outcome=(f"Option.some [OriginalContract.{left}, !(OriginalContract.{right})]" if case=="W03" else
             "Option.some [Bool.true, Bool.false]")
    percase=(f"∃ p q : Bool, OriginalContract.leftAt rho = some p ∧ OriginalContract.rightAt rho = some q ∧ "
             f"{ev} rho = some [p, !q]" if case=="W03" else
             "∃ b : Bool, OriginalContract.leftAt rho = some b ∧ OriginalContract.rightAt rho = some b")
    test=f"decide ({ref} ({observe} x))"
    enumeration=(f"(List.finRange 128).all (fun x => {test}) = true" if case!="W15" else
        f"(List.finRange 16).all (fun k => (List.finRange 16).all (fun r => decide ({ref} ({observe} (k,r))))) = true")
    return {
        "staticFold":"OriginalPrefix.commands.foldlM SmtW02.staticStep OriginalPrefix.state0 = some OriginalPrefix.state85",
        "wellFormed":f"SmtW02.wellFormed {s} = true",
        "inhabited":f"Nonempty ({val})",
        "rightInverse":f"∀ x : {a}, {project} ({extend} x) = x",
        "checkedBody":f"∀ rho : {val}, {ev} rho = OriginalContract.dynamicBody rho",
        "bodyAgreement":f"∀ rho : {val}, OriginalContract.dynamicBody rho = {observe} ({project} rho)",
        "preserves":f"∀ rho : {val}, {ev} rho = {ev} ({extend} ({project} rho))",
        "reifies":f"∀ x : {a}, {ev} ({extend} x) = {observe} x",
        "fullEvaluation":f"∀ rho : {val}, {ev} rho = {observe} ({project} rho)",
        "leftPredicate":f"∀ rho : {val}, OriginalContract.leftAt rho = Option.some (OriginalContract.{left})",
        "rightPredicate":f"∀ rho : {val}, OriginalContract.rightAt rho = Option.some (OriginalContract.{right})",
        "finiteDecision":enumeration,
        "namedRelation":f"∀ rho : {val}, {percase}",
        "orderedOutput":f"∀ rho : {val}, {ev} rho = {outcome}",
        "successful":f"∀ rho : {val}, {ref} ({ev} rho)",
        "noModel":f"¬ ∃ rho : {val}, SmtW02.Satisfies {s} rho",
    }

def modules(case, typed, writer, observer):
    fixed={"OriginalPrefix":prefix(typed,writer),"OriginalContract":contract(case,typed,writer)}
    stages={}; use={}; slots=[]
    support={
        "W02Semantics":("SmtW02",["valuationsInhabited","noModelOfResults"]),
        "ProjectionCore":("ArchivedProjection",["put_here","put_elsewhere","fullEvaluation","refutesAll",
                          "noModelOfSuccessfulRefutation","enumerateOne","enumeratePair"]),
        "ProjectionReification":("ArchivedProjection",["foldAt","foldArgsAt","modelAlgebraMatches","symbolicTermExact"]),
        "OriginalContract":("OriginalContract",["consStep","finishStatic"]),
    }
    roster={ns+"."+n:owner for owner,(ns,names) in support.items() for n in names}
    def stage(name, parent, namespace, targets):
        items=["import "+parent,"",OPTIONS,OPEN,"namespace "+namespace,""]
        for key, prop in targets.items():
            qname=namespace+"."+key
            slots.append(qname)
            roster[qname]=name
            items+=["theorem "+key+" : "+prop+" := by", "@@PROOF "+qname+"@@", ""]
        items+=["end "+namespace,""]
        stages[name]="\n".join(items)
    previous="OriginalContract"
    for group,start in enumerate(range(0,85,8)):
        name=f"OriginalStaticGroup{group:02d}"
        target=({"literalCommands":"currentCommands originalScript = some commands"} if group==0 else {})
        target.update({f"step{i:02d}":f"staticStep state{i} cmd{i} = some state{i+1}" for i in range(start,min(start+8,85))})
        stage(name,previous,"OriginalSteps",target)
        previous=name
    sts=types(case)
    for name, keys in [("OriginalStatic",["staticFold","wellFormed","inhabited"]),
        ("OriginalDynamic",["rightInverse","checkedBody","preserves","reifies","fullEvaluation","bodyAgreement"]),
        ("OriginalPredicates",["leftPredicate","rightPredicate"]),
        ("OriginalFinite",["finiteDecision","namedRelation","orderedOutput","successful","noModel"])]:
        stage(name,previous,"OriginalProof",{k:sts[k] for k in keys});previous=name
    text=(Path(__file__).resolve().parent/"consumers"/(case+".lean")).read_text()
    for name in sts:
        if name == "staticFold": continue
        q="OriginalConsumer."+name
        roster[q]="OriginalConsumer";use[q]="OriginalProof."+name
    fixed["OriginalConsumer"]=text
    head, marker, remaining=observer.partition("  let targets : List Name := [")
    old, split, body=remaining.partition("  for n in targets do\n")
    if not marker or not split or "W02Readback.hasAssignments]" not in old or not head.startswith("import W02Consumer\n"):
        raise ValueError("unrecognized stock term observer")
    head="import OriginalConsumer\n"+head.removeprefix("import W02Consumer\n")
    spot='("axioms",toJson (sorted (← collectAxioms n).toList))'
    if body.count(spot)!=1: raise ValueError("unrecognized axiom inventory")
    getdirect="fun d => match env.find? d with | some (.axiomInfo _) => true | _ => false"
    extra=[f'("{k}",toJson (sorted ({v}.getUsedConstantsAsSet.toList.filter ({getdirect}))))'
           for k,v in (("direct_type_axioms","ty"),("direct_value_axioms","val"))]
    body=body.replace(spot,",\n      ".join([*extra,spot]))
    fixed["OriginalTerms"]=head+marker+", ".join("\x60"+k for k in roster)+"]\n"+split+body
    fixed["OriginalAxioms"]="import OriginalConsumer\n\n"+"".join("#print axioms "+k+"\n" for k in roster)
    return fixed,stages,roster,use,slots

