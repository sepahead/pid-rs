"""Construct named source-dependent proof obligations without evaluating an original assertion."""

import json
import re

CASES = ("W01", "W03", "W15")
NODES = {
    "W01": ("a", "sub", "has", "incomparable", "valid", "canonical"),
    "W03": ("a", "sub", "has", "incomparable", "valid", "leq"),
    "W15": ("k", "r", "has", "raw-branch", "raw-source"),
}
WIDTH = {"W01": 8, "W03": 16, "W15": 16}
DYNAMIC = ("rightInverse", "checkedBody", "bodyAgreement", "fullEvaluation", "preserves", "reifies")
OPEN = "open SmtW02 ArchivedProjection OriginalPrefix OriginalContract ReachSpec"


def require(ok, why):
    if not ok:
        raise ValueError(why)


def occurrences(term):
    kind = term[0]
    if kind == "name":
        yield "name", term[2]
    elif kind == "app":
        yield "operator", term[2]
        for child in term[3]:
            yield from occurrences(child)
    elif kind == "indexed":
        yield from occurrences(term[4])
    else:
        require(kind in {"boolean", "numeral", "bits"}, "unknown term constructor")


def plan(case, ast):
    """Record every prefix installation and the dependency role at each point of use."""
    require(case in CASES and len(ast) == 89, "case and raw command count")
    prefix = ast[2:84]
    names = [c[1] for c in prefix]
    require(len(set(names)) == len(names) == 82, "unique ordered prefix names")
    global_names = set(names)

    def direct(term, locals_, available):
        reached = set()
        for role, name in occurrences(term):
            if role == "name" and name in locals_:
                continue
            if name in global_names:
                require(name in available, "capture sees only previously installed definitions")
                reached.add(name)
            elif role == "name":
                raise ValueError("unbound source name " + name)
        return sorted(reached)

    rows = []
    for i, c in enumerate(prefix):
        require(c[0] in {"constant", "define"}, "prefix can only install")
        local_names = [p[0] for p in c[2]] if c[0] == "define" else []
        require(len(local_names) == len(set(local_names)), "unique parameters")
        children = direct(c[4], local_names, names[:i]) if c[0] == "define" else []
        rows.append({"index": i, "name": c[1], "kind": c[0], "parameters": local_names, "calls": children})
    assertions = ast[-4:-2]
    require([a[0] for a in assertions] == ["assertion", "assertion"], "two ordered assertions")
    outer = assertions[1][1]
    require(outer[:3] == ["app", ["bool"], "not"] and len(outer[3]) == 1, "outer negation")
    if case == "W03":
        operands = [assertions[0][1], outer[3][0]]
    else:
        equality = outer[3][0]
        require(assertions[0][1] == ["boolean", True] and equality[:3] == ["app", ["bool"], "="]
                and len(equality[3]) == 2, "ordered equality operands")
        operands = equality[3]
    head = [direct(t, (), names) for t in operands]
    closure = set().union(*head)
    for row in reversed(rows):
        if row["name"] in closure:
            closure.update(row["calls"])
    selected = [row for row in rows if row["name"] in closure]
    require(tuple(r["name"] for r in selected) == NODES[case], "source-reachable declaration list")
    count = 256 if case == "W15" else 128
    intervals = [[i, i + WIDTH[case]] for i in range(0, count, WIDTH[case])]
    check_intervals(intervals, count)
    return {"case": case, "installations": rows, "selected": selected, "operand_dependencies": head,
            "operand_terms": operands, "count": count, "intervals": intervals}


def check_intervals(intervals, count):
    require(type(count) is int and count > 0, "positive finite cardinality")
    end = 0
    for row in intervals:
        require(type(row) is list and len(row) == 2 and all(type(i) is int for i in row),
                "two integer interval endpoints")
        lo, hi = row
        require(lo == end and lo < hi <= count, "strict contiguous disjoint ordered interval cover")
        end = hi
    require(end == count, "complete interval cover")


def capitalize(name):
    return "".join(s[0].upper() + s[1:] for s in name.split("-"))


def spec(plan_, writer, old):
    case = plan_["case"]
    lookup = ('if name == "a" then some (.bits 7 x.val) else none' if case != "W15" else
              'if name == "k" then some (.bits 4 x.1.val) else\n  '
              'if name == "r" then some (.bits 4 x.2.val) else none')
    selects = ", ".join("("+str(r["index"])+", cmd"+str(r["index"])+")" for r in plan_["selected"])
    left, right = old.reference(case, "x")
    relation = "True" if case == "W03" else "("+left+") = ("+right+")"
    ordered = "[p, !q]" if case == "W03" else "[true, !(p == q)]"
    decode = ("Fin.ofNat 128 i" if case != "W15" else
              "(Fin.ofNat 16 (i / 16), Fin.ofNat 16 (i % 16))")
    return f"""import OriginalContract

{old.OPTIONS}
namespace ReachSpec
open SmtW02 ArchivedProjection OriginalPrefix OriginalContract

abbrev V := Valuation originalScript
def installedName : Cmd → Option String
  | .constant n _ => some n
  | .define n _ _ _ => some n
  | _ => none
def retained : List (Nat × Cmd) := [{selects}]
def retainedAt (i : Nat) : List Cmd :=
  retained.filterMap (fun p => if p.1 < i then some p.2 else none)
def lookupSmall (x : A) (name : String) : Option Value :=
  {lookup}
def large (rho : V) (i : Nat) : Option DynamicState :=
  (commands.take i).foldlM (dynamicStep (valuationLookup (declarations originalScript) rho)) {{}}
def small (x : A) (i : Nat) : Option DynamicState :=
  (retainedAt i).foldlM (dynamicStep (lookupSmall x)) {{}}
def ready (cmds : List Cmd) (env : Option DynamicState) : Prop :=
  ∃ st, env = some st ∧ st.assertedRev = [] ∧
    st.globals.map Prod.fst = (cmds.filterMap installedName).reverse
def prefixReady : Prop :=
  (∀ (rho : V) (i : Fin 83), ready (commands.take i.val) (large rho i.val)) ∧
  (∀ (x : A) (i : Fin 83), ready (retainedAt i.val) (small x i.val))
def call (env : Option DynamicState) (name : String) (args : List Value) : Option Value := do
  let st ← env
  let fn ← st.globals.lookup name
  fn args
def callAgrees (j : Nat) (name : String) : Prop :=
  ∀ (rho : V) (i : Fin 83), j < i.val → ∀ args : List Value,
    call (large rho i.val) name args = call (small (pack rho) i.val) name args
def boolTerm (env : Option DynamicState) (term : Term) : Option Bool := do
  let st ← env
  (← evaluateTerm term st.globals).getBool
def firstOperand : Term := {writer.lean_term(plan_["operand_terms"][0])}
def secondOperand : Term := {writer.lean_term(plan_["operand_terms"][1])}
def firstSmall (x : A) : Option Bool := boolTerm (small x 82) firstOperand
def secondSmall (x : A) : Option Bool := boolTerm (small x 82) secondOperand
def combine (p q : Bool) : List Bool := {ordered}
def orderedTail (rho : V) : Option (List Bool) := do
  let p ← leftAt rho
  let q ← rightAt rho
  return combine p q
def fact (x : A) : Prop :=
  firstSmall x = some ({left}) ∧ secondSmall x = some ({right}) ∧
    ({relation}) ∧ RefutesTwo (observe x)
instance (x : A) : Decidable (fact x) := by
  unfold fact
  infer_instance
def decode (i : Nat) : A := {decode}
def block (lo hi : Nat) : Prop :=
  (List.range' lo (hi - lo)).all (fun i => decide (fact (decode i))) = true
end ReachSpec
"""


def imply(premises, result):
    return " → ".join(["(" + p + ")" for p in premises] + [result])


def isolated_statements(source):
    """One full candidate theorem, with the identical public imports, independently elaborable."""
    lines=source.splitlines()
    first=next(i for i,line in enumerate(lines) if line.startswith("theorem "))
    prelude="\n".join(lines[:first])+"\n"
    result={}
    for i,line in enumerate(lines):
        match=re.fullmatch(r"@@PROOF ([A-Za-z0-9_.]+)@@",line)
        if match:
            name=match[1]
            require(name not in result and lines[i-1].startswith("theorem "+name+" : ")
                    and lines[i-1].endswith(" := by"),"isolated statement and named proof slot")
            result[name]=prelude+lines[i-1]+"\n"+line+"\n\n#print axioms "+name+"\n"
    return result


def build(plan_, writer, old):
    """Produce frozen helper statements, typed adapters, original owners and direct-use edges."""
    case = plan_["case"]
    types = old.types(case)
    fixed = {"ReachSpec": spec(plan_, writer, old)}
    stages = {}
    targets, edges, slots, checkpoints = {}, {}, [], {}
    propositions = {}
    signatures = {}
    parent = "ReachSpec"
    rows = []

    def start(owner):
        nonlocal rows
        rows = ["import "+parent, "", old.OPTIONS, OPEN, ""]
        if owner=="ReachRightInverse":
            rows.insert(1,"import OriginalStatic")
        checkpoints[owner] = []

    def finish(owner):
        nonlocal parent
        stages[owner] = "\n".join(rows) + "\n"
        parent = owner

    def claim(owner, name, prop, needs=(), public=False, mark=False):
        # The implication and the typed application are distinct checked declarations.
        namespace = "OriginalProof" if public else "OriginalReach"
        final = namespace+"."+name
        method = "ReachMethod."+name
        require(final not in propositions and method not in targets, "one helper per binding")
        reqs = [propositions[q] for q in needs]
        if needs:
            rows.extend(["theorem "+method+" : "+imply(reqs, prop)+" := by", "@@PROOF "+method+"@@", "",
                         "theorem "+final+" : "+prop+" :=", "  "+method+" "+" ".join(needs), ""])
            slots.append(method)
            targets[method] = owner
            signatures[method] = imply(reqs, prop)
            edges[final] = [method, *needs]
        else:
            rows.extend(["theorem "+final+" : "+prop+" := by", "@@PROOF "+final+"@@", ""])
            slots.append(final)
        targets[final] = owner
        signatures[final] = prop
        propositions[final] = prop
        if mark:
            rows.extend(["#print axioms "+final, ""])
            checkpoints[owner].append(final)
        return final

    def alias(owner, name, source):
        q = "OriginalProof."+name
        rows.extend(["theorem "+q+" : "+types[name]+" :=", "  "+source, ""])
        targets[q] = owner
        signatures[q] = types[name]
        propositions[q] = types[name]
        edges[q] = [source]

    # Public names defined previously may be used as fixed hypotheses.
    propositions["OriginalProof.wellFormed"] = types["wellFormed"]
    propositions["OriginalSteps.literalCommands"] = "currentCommands originalScript = some commands"
    start("ReachRightInverse")
    ri = claim("ReachRightInverse", "rightInverse", types["rightInverse"])
    finish("ReachRightInverse")
    start("ReachCheckedBody")
    cb = claim("ReachCheckedBody", "checkedBody", types["checkedBody"],
               ["OriginalProof.wellFormed", "OriginalSteps.literalCommands"])
    finish("ReachCheckedBody")
    owner = "ReachCalls"
    start(owner)
    ready = claim(owner, "prefixInstallation", "ReachSpec.prefixReady", mark=True)
    calls = {}
    for r in plan_["selected"]:
        name = r["name"]
        prop = "ReachSpec.callAgrees "+str(r["index"])+" "+json.dumps(name)
        calls[name] = claim(owner, "call"+capitalize(name), prop,
                            [ready, *(calls[ch] for ch in r["calls"])], mark=True)
    ops = []
    for label, original, reduced, dep in zip(("firstOperand", "secondOperand"),
                ("leftAt", "rightAt"), ("firstSmall", "secondSmall"), plan_["operand_dependencies"]):
        prop = "∀ rho : ReachSpec.V, OriginalContract."+original+" rho = ReachSpec."+reduced+" (pack rho)"
        ops.append(claim(owner, label, prop, [ready, *(calls[k] for k in dep)], mark=True))
    tail = claim(owner, "orderedTail", "∀ rho : ReachSpec.V, dynamicBody rho = ReachSpec.orderedTail rho",
                 [ready], mark=True)
    finish(owner)
    owner = "ReachLeaves"
    start(owner)
    leaves = []
    for lo, hi in plan_["intervals"]:
        leaves.append(claim(owner, f"interval{lo:03d}to{hi:03d}", f"ReachSpec.block {lo} {hi}", mark=True))
    covered = claim(owner, "covered", "∀ x : OriginalContract.A, ReachSpec.fact x", leaves, mark=True)
    finish(owner)
    helper = {"rightInverse": ri, "checkedBody": cb}
    for name, needs in (("bodyAgreement", [tail, *ops, covered]), ("fullEvaluation", [cb, "OriginalReach.bodyAgreement"]),
                        ("preserves", ["OriginalReach.fullEvaluation", ri]),
                        ("reifies", ["OriginalReach.fullEvaluation", ri])):
        owner = "Reach"+capitalize(name)
        start(owner)
        helper[name] = claim(owner, name, types[name], needs)
        finish(owner)
    start("OriginalDynamic")
    for k in ("rightInverse", "checkedBody", "preserves", "reifies", "fullEvaluation", "bodyAgreement"):
        alias("OriginalDynamic", k, helper[k])
    finish("OriginalDynamic")
    start("OriginalPredicates")
    predicates = []
    for k, operand in zip(("leftPredicate", "rightPredicate"), ops):
        predicates.append(claim("OriginalPredicates", k, types[k], [operand, covered], public=True))
    finish("OriginalPredicates")
    start("OriginalFinite")
    for k, deps in (("finiteDecision", [covered]), ("namedRelation", [*predicates, covered, "OriginalProof.fullEvaluation"]),
                    ("orderedOutput", ["OriginalProof.fullEvaluation", covered]),
                    ("successful", ["OriginalProof.fullEvaluation", "OriginalProof.finiteDecision"]),
                    ("noModel", ["OriginalProof.successful"])):
        claim("OriginalFinite", k, types[k], deps, public=True)
    finish("OriginalFinite")
    # These definitions name propositions, never proofs or axioms of those propositions.
    # They import the original contract only and can be typed before any scientific payload.
    names={q:"ReachSignatures.statement"+format(i,"03d") for i,q in enumerate(signatures)}
    statements=["",OPEN,"","namespace ReachSignatures",""]
    for q,prop in signatures.items():
        statements.extend(["def "+names[q].split(".")[1]+" : Prop := "+prop,""])
    statements.extend(["end ReachSignatures",""])
    fixed["ReachSpec"]+="\n".join(statements)
    return fixed, stages, targets, edges, slots, checkpoints, names
