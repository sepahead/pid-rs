"""Reconstruct the four artificial typed scripts and split the large static fold."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / "three-source-w02"
FIXTURES = ("Unary", "Pair", "Sat", "Scale")
GROUP_SIZE = 8
SETTINGS = "set_option maxRecDepth 65536\nset_option maxHeartbeats 20000000\n"
SHARED_FILES = {
    "source_reader.py": "8826c1380b6fd9d6f8945672c0281aa69e7431e75152652c3109650440632302",
    "source_writer.py": "38b91a375ddb237c33f06db48519654cc6d41bd27678b2e1e4a6cabd02710504",
    "lean_literals.py": "73913ccab97e64878c472c52ff8b9fd1cf6f8f861dac584d58f2acd3818aa274",
    "lean/W02Inspect.lean": "30834cf49fd2fd4c40536ad8a70bdf74d3228c15cd80995225d78788f4209768",
    "lean/W02Semantics.lean": "e47fecb9c4221c594c623551fbc018037f827fe1418741a7393fda2027ccc6e3",
}

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encoded(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode() + b"\n"

def source_module(shared, name):
    path = shared / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def read_fixture(name, writer, reader, literals, expected):
    raw = (HERE / "fixtures" / (name + ".smt2")).read_bytes()
    require(len(raw) == expected["raw_bytes"] and digest(raw) == expected["sha256"], "source " + name)
    tree, spans = writer.neutral(raw)
    other_tree, other_spans = reader.read(raw)
    require(encoded(tree) == encoded(other_tree) and encoded(spans) == encoded(other_spans), "source readers")
    require(b"".join(raw[a:b] for _,a,b in spans) == raw, "contiguous source coverage")
    typed = writer.typed_script(tree)
    require(encoded(typed) == encoded(reader.checked_script(other_tree)), "typed reader agreement")
    for parsed, field in [(tree,"tree_sha256"),(spans,"spans_sha256"),(typed,"annotated_sha256")]:
        require(digest(encoded(parsed)) == expected[field], "fixture field " + field)
    prefix = "import W02Semantics\n\nset_option maxRecDepth 8192\nnamespace SmtW02\n\n"
    original_header = "def originalScript : List Cmd :="
    synthetic_header = "def synthetic" + name + " : List Cmd :="
    neutral = (prefix + writer.lean_definition("originalScript", typed) + "\nend SmtW02\n").encode()
    require(literals.matches(neutral, encoded(typed)) == (expected["commands"], expected["annotated_sha256"]),
            "literal constructor reader")
    require(neutral.count(original_header.encode()) == 1, "unique declaration name")
    generated = neutral.replace(original_header.encode(), synthetic_header.encode(), 1)
    require(digest(generated) == expected["lean_sha256"], "whole synthetic Lean source")
    return generated, typed

def scale_sources(typed, writer):
    active = typed[2:-2]
    require(len(active) == 85 and [cmd[0] for cmd in active] ==
            ["constant"] * 25 + ["define"] * 57 + ["echo","assertion","assertion"], "scale command kinds")
    padding = active[26:82]
    rank_args, result_type, body = padding[0][2:]
    require(all(entry[2:] == [rank_args,result_type,body] for entry in padding),
            "the 56 padding function bodies have identical typed syntax")
    arguments = writer.many("(" + writer.lean_str(n) + ", " + writer.lean_sort(t) + ")" for n,t in rank_args)
    prefix = ["import SyntheticScaleData", "", SETTINGS, "namespace ScalePrefix", "open SmtW02", "",
              "def paddingBody : Term := " + writer.lean_term(body),
              "def padded (name : String) : Cmd := .define name " + arguments + " " + writer.lean_sort(result_type) + " paddingBody",
              "def state0 : StaticState := {}", ""]
    for i, cmd in enumerate(active):
        command = "padded " + writer.lean_str(cmd[1]) if 26 <= i < 82 else writer.lean_cmd(cmd)
        prefix.append(f"def cmd{i} : Cmd := {command}")
        if cmd[0] in ("constant","define"):
            n = writer.lean_str(cmd[1])
            ins = "[]" if cmd[0] == "constant" else writer.many(writer.lean_sort(t) for _,t in cmd[2])
            out = writer.lean_sort(cmd[2] if cmd[0] == "constant" else cmd[3])
            update = f"globals := ({n}, {ins}, {out}) :: state{i}.globals"
        elif cmd[0] == "echo":
            update = "echoSeen := true"
        else:
            update = f"nassert := state{i}.nassert + 1"
        prefix.append(f"def state{i+1} : StaticState := {{state{i} with {update}}}")
    cmds = ", ".join(f"cmd{i}" for i in range(len(active)))
    prefix.extend(["",f"def commands : List Cmd := [{cmds}]",
                   "theorem commandsExact : currentCommands syntheticScale = some commands := by rfl",
                   "theorem commandCount : commands.length = 85 := by rfl", "", "end ScalePrefix", ""])
    answer = {"ScalePrefix":"\n".join(prefix)}
    last_module = "ScalePrefix"
    step_names = []
    for batch, start in enumerate(range(0,len(active),GROUP_SIZE)):
        module = f"ScaleStaticGroup{batch:02d}"
        out = ["import "+last_module, "", SETTINGS, "namespace ScaleSteps", "open SmtW02 ScalePrefix", ""]
        for i in range(start,min(start+GROUP_SIZE,len(active))):
            name = f"step{i:02d}"
            out.append(f"theorem {name} : staticStep state{i} cmd{i} = some state{i+1} := by rfl")
            step_names.append(name)
        out.extend(["","end ScaleSteps",""])
        answer[module] = "\n".join(out)
        last_module = module
    proof = ["import "+last_module, "", SETTINGS, "namespace ScaleStatic", "open SmtW02 ScalePrefix ScaleSteps", "",
             "theorem consStep {c : Cmd} {cs : List Cmd} {a b z : StaticState}",
             "    (h : staticStep a c = some b) (tail : cs.foldlM staticStep b = some z) :",
             "    (c :: cs).foldlM staticStep a = some z := by",
             "  rw [List.foldlM_cons, h]", "  exact tail", "",
             "theorem folded : commands.foldlM staticStep state0 = some state85 := by",
             "  unfold commands"]
    proof.extend("  apply consStep "+step for step in step_names)
    proof.extend(["  rfl", "",
                  "theorem finish {script cmds : List Cmd} {z : StaticState}",
                  "    (shape : currentCommands script = some cmds)",
                  "    (steps : cmds.foldlM staticStep {} = some z)",
                  "    (ends : (z.echoSeen && z.nassert == 2) = true) : wellFormed script = true := by",
                  "  unfold SmtW02.wellFormed", "  rw [shape]",
                  "  change (match cmds.foldlM staticStep {} with",
                  "    | some st => st.echoSeen && st.nassert == 2", "    | none => false) = true",
                  "  rw [steps] <;> exact ends", "",
                  "theorem valid : wellFormed syntheticScale = true :=",
                  "  finish commandsExact folded (by rfl)", "", "end ScaleStatic", ""])
    answer["ScaleStatic"] = "\n".join(proof)
    return answer

def write_sources(target, shared=SHARED):
    for name, expected in SHARED_FILES.items():
        require(digest((shared / name).read_bytes()) == expected, "shared source " + name)
    writer, reader, literals = [source_module(shared, name) for name in
                                ("source_writer","source_reader","lean_literals")]
    expected = json.loads((HERE/"fixtures.json").read_bytes())
    shutil.copyfile(shared/"lean/W02Semantics.lean", target/"W02Semantics.lean")
    for name in FIXTURES:
        data, typed = read_fixture(name,writer,reader,literals,expected[name])
        (target/("Synthetic"+name+"Data.lean")).write_bytes(data)
        if name == "Scale":
            for module, text in scale_sources(typed,writer).items():
                (target/(module+".lean")).write_text(text,encoding="utf-8")
    for source in sorted((HERE/"lean").glob("*.lean")):
        require(not (target/source.name).exists(), "duplicate module")
        shutil.copyfile(source,target/source.name)
    for prefix, imports, file in [("Small",["ConsumerSynthetic","SyntheticRefusalsProved"],"small-targets.json"),
                                  ("Scale",["ScaleConsumer"],"scale-targets.json")]:
        roster = json.loads((HERE/file).read_bytes())
        head = "".join("import "+m+"\n" for m in imports)
        template = (shared/"lean/W02Inspect.lean").read_text()
        old_header, marker, code = template.partition("  let targets : List Name := [")
        old_list, end, exact_body = code.partition("  for n in targets do\n")
        require(old_header.startswith("import W02Consumer\n") and marker and end and
                "W02Readback.hasAssignments]" in old_list, "shared observer structure")
        header = head + old_header.removeprefix("import W02Consumer\n")
        observer = header + marker + ", ".join("`"+n for n in roster) + "]\n" + end + exact_body
        (target/(prefix+"Terms.lean")).write_text(observer)
        (target/(prefix+"Axioms.lean")).write_text(head+"\n"+"".join("#print axioms "+n+"\n" for n in roster))
