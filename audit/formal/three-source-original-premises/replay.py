"""Check complete ground assignments for the first assertion of 22 named source files."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from types import ModuleType


HERE = Path(__file__).resolve().parent
BASE = Path("audit/formal/finite-smt39-qualification-v1")
SOURCE_SHA = "31f785efdd845199cb568483dbf608658910c249b9b33509221462481e3d512f"
CAPTURE_SHA = "86fdae96818a54d5da79f726feb274f6773047363c6202c0148868adb7cfbf5b"
WIDTH = {"a": 7, "b": 7, "c": 7, "q": 3, "h": 3, "x": 3, "k": 4, "r": 4}
WEIGHTS = tuple(f"w{i}" for i in range(16))
NAMES = (*WIDTH, "tau", *WEIGHTS)
LITERAL = {"W01", "W02", "W15"}
MASS_TERMS = ("N", ("U", "a", "k"), ("V", "a", "k"), ("Tmass", "k"), ("weight", "k"))


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return sha256(raw).hexdigest()


def registered(raw, expected, name):
    need(digest(raw) == expected, f"SHA-256 mismatch for {name}")
    return raw


def checked_bytes(path, expected):
    return registered(path.read_bytes(), expected, path.name)


def typed_values(values):
    need(set(values) == set(NAMES), "incomplete or extra assignment")
    for name, width in WIDTH.items():
        number = values[name]
        need(type(number) is int and 0 <= number < 2**width, "invalid bit vector " + name)
    need(type(values["tau"]) is bool, "invalid Boolean tau")
    need(all(type(values[key]) is int for key in WEIGHTS), "invalid integer weight")


def read_original(raw, subject, grammar):
    lines = raw.decode("ascii").splitlines(keepends=True)
    indices = [i for i, line in enumerate(lines) if line.startswith("(assert ")]
    need(len(indices) == 2, "expected two original assertions")
    first, second = indices
    need(second == first + 1 and lines[second + 1:] == ["(check-sat)\n", "(exit)\n"],
         "unexpected assertion or command order")
    need(lines[first - 1].startswith('(echo "') and lines[first - 1].endswith('")\n'),
         "missing original echo before assertions")
    prefix = "".join(lines[:first - 1])
    need(digest(prefix.encode("ascii")) == subject["unchanged_prefix_sha256"], "definition prefix")
    need(lines[second].startswith("(assert (not ") and
         digest(lines[second].encode("ascii")) == subject["second_assertion_sha256"],
         "original second assertion")
    declarations = [grammar.sexprs(line.encode("ascii"))[0] for line in lines[:first - 1]
                    if line.startswith("(declare-const ")]
    expected_sorts = {**{n: ("BV", width) for n, width in WIDTH.items()},
                      "tau": ("Bool", 0), **{n: ("Int", 0) for n in WEIGHTS}}
    native_sorts = {name: grammar.sort_of(sort) for _, name, sort in declarations}
    need(len(declarations) == len(NAMES) and native_sorts == expected_sorts, "original declaration sorts")
    assertion, = grammar.sexprs(lines[first].encode("ascii"))
    text = lines[first][len("(assert "):-2]
    need(assertion[0] == "assert" and len(assertion) == 2 and text == subject["background"],
         "original first assertion")
    return prefix, text, assertion[1]


def semantic(term, values, grammar):
    if term == "true":
        return True
    if term == "positive-table":
        return all(values[n] >= 0 for n in WEIGHTS)
    if isinstance(term, str):
        if term == "0":
            return 0
        need(term in values, "unsupported name " + term)
        return values[term]
    op, *arguments = term
    if op == "_":
        return grammar.literal(term, ("BV", 3))
    args = [semantic(arg, values, grammar) for arg in arguments]
    if op == "and" and args and all(type(v) is bool for v in args):
        return all(args)
    if op == "valid" and len(args) == 1:
        return grammar.valid(grammar.family(args[0]))
    if op == "leq" and len(args) == 2:
        return grammar.below(grammar.family(args[0]), grammar.family(args[1]))
    if op == "weight" and len(args) == 1:
        return values[WEIGHTS[args[0]]]
    if op == ">" and len(args) == 2:
        return args[0] > args[1]
    if op == "distinct" and len(args) == 2:
        return args[0] != args[1]
    raise ValueError("unsupported original first-assertion expression")


def counts(values, grammar):
    source, intersection, total = grammar.masses(values)
    key = values["k"]
    target = sum(values[name] for cell, name in enumerate(WEIGHTS) if grammar.target(key, cell))
    return [total, source, intersection, target, values[WEIGHTS[key]]]


def smt_value(name, value):
    if name in WIDTH:
        return f"(_ bv{value} {WIDTH[name]})"
    if name == "tau":
        return "true" if value else "false"
    return f"(- {-value})" if value < 0 else str(value)


def query(prefix, premise, values, get_masses):
    typed_values(values)
    chunks = [prefix, f"(define-fun groundBackground () Bool {premise})\n"]
    for name in NAMES:
        chunks.append(f"(assert (= {name} {smt_value(name, values[name])}))\n")
    chunks.append("(check-sat)\n(get-value (groundBackground))\n")
    if get_masses:
        chunks.append("(get-value (N (U a k) (V a k) (Tmass k) (weight k)))\n")
    chunks.append("(exit)\n")
    return "".join(chunks).encode("ascii")


def checked_reply(raw, expected, measure, grammar):
    parts = grammar.sexprs(raw)
    count = 3 if measure is not None else 2
    need(len(parts) == count and parts[0] == "sat", "missing ground model")
    truth = "true" if expected else "false"
    need(parts[1] == (("groundBackground", truth),), "wrong first-assertion value")
    if measure is not None:
        need(len(parts[2]) == len(MASS_TERMS), "missing W14 result")
        for item, name, number in zip(parts[2], MASS_TERMS, measure, strict=True):
            need(len(item) == 2 and item[0] == name and grammar.literal(item[1], ("Int", 0)) == number,
                 "wrong W14 term or number")


def solver_output(executable, input_data):
    run = subprocess.run([executable, "-T:17", "-smt2", "-in"], input=input_data, capture_output=True, timeout=20)
    need(run.returncode == 0 and not run.stderr, "solver failed or wrote a diagnostic")
    return run.stdout


def read_row(name, record, path, source_sha, grammar, solver):
    raw = checked_bytes(path, source_sha)
    need(record["raw_sha256"] == source_sha and record["assertion_count"] == 2, "captured source identity")
    prefix, text, term = read_original(raw, record, grammar)
    code = name[:3]
    positive = {"dense", "sparse"}
    rejected = set()
    if code not in LITERAL:
        if code in {"W05", "W12"}:
            rejected.add("reversed-order")
        elif code == "W04":
            rejected.add("one-direction-only")
        elif code == "W16":
            rejected.add("empty-source-mask")
        else:
            rejected.add("empty-family")
    if code == "W14":
        rejected.update(("negative-cell", "unsupported-key"))
    cases = record["cases"]
    need((text == "true") == (code in LITERAL), "literal truth in the original")
    need(len(cases) == len(positive | rejected) and {item["case"] for item in cases} == positive | rejected,
         "ground assignment register")
    seen = set()
    subtotal = Counter()
    for item in cases:
        values = item["values"]
        typed_values(values)
        fingerprint = tuple(values[n] for n in NAMES)
        need(fingerprint not in seen, "repeated assignment in one row")
        seen.add(fingerprint)
        accepted = semantic(term, values, grammar)
        need(item["sat"] is True and item["observed"] is accepted and accepted is (item["case"] in positive),
             "original premise and intended outcome")
        measure = counts(values, grammar) if code == "W14" else None
        if measure is not None:
            need(item.get("observed_masses") == measure, "captured W14 counts")
        payload = query(prefix, text, values, measure is not None)
        need(digest(payload) == item["query_sha256"], "complete original ground query")
        if solver:
            reply = solver_output(solver, payload)
            checked_reply(reply, accepted, measure, grammar)
            need(digest(reply) == item["raw_return_sha256"], "full native return digest")
        subtotal[accepted] += 1
    return subtotal, (prefix, text, term)


def supplementary_example(original, grammar, solver):
    prefix, text, term = original
    values = {n: 0 for n in NAMES}
    values.update(a=1, b=1, c=1, q=1, tau=False, w0=2, w1=3, w8=5, w9=7)
    for change, wanted in [({}, True), ({"a": 0}, False), ({"k": 4}, False), ({"w15": -1}, False)]:
        test = {**values, **change}
        typed_values(test)
        need(semantic(term, test, grammar) is wanted, "additional W14 example")
        result = counts(test, grammar)
        if not change:
            need(result == [17, 5, 2, 7, 2], "additional W14 masses")
        if solver:
            checked_reply(solver_output(solver, query(prefix, text, test, True)), wanted, result, grammar)
    return [17, 5, 2, 7, 2]


def self_test(grammar, original, source, example, template):
    _, _, term = original
    controls = []

    def reject(label, operation):
        try:
            operation()
        except ValueError:
            controls.append(label)
            return
        raise ValueError(f"altered input passed: {label}")

    reject("missing weight", lambda: typed_values({k: v for k, v in example.items() if k != "w15"}))
    reject("extra name", lambda: typed_values({**example, "extra": 0}))
    reject("negative family code", lambda: typed_values({**example, "a": -1}))
    reject("large four-bit key", lambda: typed_values({**example, "k": 16}))
    reject("integer Boolean", lambda: typed_values({**example, "tau": 1}))
    reject("Boolean weight", lambda: typed_values({**example, "w2": False}))
    reject("unknown", lambda: checked_reply(b"unknown\n", True, None, grammar))
    reject("unsat", lambda: checked_reply(b"unsat\n", False, None, grammar))
    reject("missing reply", lambda: checked_reply(b"", True, None, grammar))
    reject("false value for required truth", lambda: checked_reply(b"sat\n((groundBackground false))\n", True, None, grammar))
    reject("extra reply", lambda: checked_reply(b"sat\n((groundBackground true)) 0\n", True, None, grammar))
    reject("missing mass terms", lambda: checked_reply(b"sat\n((groundBackground true)) ((N 0))\n", True, [17, 5, 2, 7, 2], grammar))
    reject("missing assertion", lambda: read_original(b"(assert true)\n(check-sat)\n(exit)\n", template, grammar))
    reject("unknown predicate", lambda: semantic(("invalid-fn", "a"), example, grammar))
    reject("false source digest", lambda: registered(source + b" ", template["raw_sha256"], "W14"))
    lines = source.splitlines(keepends=True)
    first, second = (i for i, line in enumerate(lines) if line.startswith(b"(assert "))
    swapped = lines.copy()
    swapped[first], swapped[second] = swapped[second], swapped[first]
    reject("swapped assertions", lambda: read_original(b"".join(swapped), template, grammar))
    replaced = lines.copy()
    replaced[first] = b"(assert true)\n"
    reject("changed first assertion", lambda: read_original(b"".join(replaced), template, grammar))
    another = lines.copy()
    another[second] = b"(assert (not false))\n"
    reject("changed second assertion", lambda: read_original(b"".join(another), template, grammar))
    duplicate = source.replace(b"(declare-const w15 Int)", b"(declare-const w14 Int)")
    need(duplicate != source, "duplicate-declaration test fixture")
    new_prefix = duplicate[:duplicate.index(b'(echo "')]
    changed_registration = {**template, "unchanged_prefix_sha256": digest(new_prefix)}
    reject("duplicate original declaration", lambda: read_original(duplicate, changed_registration, grammar))
    need(semantic(term, {**example, "a": 0}, grammar) is False, "empty antichain refusal")
    need(semantic(term, {**example, "k": 3}, grammar) is False, "unsupported key refusal")
    return sorted(controls + ["empty W14 family", "unsupported W14 key"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=Path, default=HERE.parents[2], help="checkout containing the pinned original files")
    ap.add_argument("--z3", metavar="EXECUTABLE", help="also reproduce all 65 captured native outputs with stock Z3 4.16.0")
    ap.add_argument("--self-test", action="store_true", help="also check malformed inputs and refused outputs")
    args = ap.parse_args()
    cfg = json.loads(checked_bytes(HERE/"SOURCES.json", SOURCE_SHA))
    found = json.loads(checked_bytes(HERE/"observations.json", CAPTURE_SHA))
    need(cfg["schema"] == "pid-rs/three-source-original-premises/source-v1"
         and cfg["commit"] == "ef705d1ed3410fd9fbbf4920cb4643f6a5140a2f"
         and cfg["capture_sha256"] == CAPTURE_SHA, "source registration")
    for relative, expected in cfg["reference_sources"].items():
        checked_bytes(args.source_root/relative, expected)
    model = BASE/"model_checker.py"
    file = args.source_root/model
    model_bytes = checked_bytes(file, cfg["reference_sources"][str(model)])
    grammar = ModuleType("original_finite_model_reader")
    grammar.__file__ = str(file)
    exec(compile(model_bytes, str(file), "exec", dont_inherit=True), grammar.__dict__)
    if args.z3:
        version = subprocess.run([args.z3, "--version"], capture_output=True, timeout=8)
        need(version.returncode == 0 and not version.stderr and version.stdout == b"Z3 version 4.16.0 - 64 bit\n",
             "native solver version")
    subjects = cfg["original_files"]
    need({Path(k).parent.name for k in subjects} == set(found) and len(subjects) == 22,
         "exact 22-source roster")
    need({name[:3] for name in found} == {f"W{i:02d}" for i in range(1, 23)}, "original W01 through W22")
    total = Counter()
    originals = {}
    for relative, bound in sorted(subjects.items()):
        name = Path(relative).parent.name
        result, originals[name] = read_row(name, found[name], args.source_root/relative, bound, grammar, args.z3)
        total.update(result)
    need(total[True] == 44 and total[False] == 21, "finite first-assertion totals")
    w14 = "W14-supported-mass-bounds"
    out = {"source_rows": 22, "satisfying_valuations": 44, "rejecting_valuations": 21,
           "premises_with_rejections": 19, "literal_true": sorted(LITERAL),
           "original_W14_sparse_N_U_V_Tmass_weight": found[w14]["cases"][1]["observed_masses"],
           "additional_W14_N_U_V_Tmass_weight": supplementary_example(originals[w14], grammar, args.z3),
           "original_proofs_added": 0, "native_original_ground_queries": 65 if args.z3 else 0,
           "native_additional_W14_queries": 4 if args.z3 else 0}
    if args.self_test:
        w14_file, = (path for path in subjects if Path(path).parent.name == w14)
        raw = checked_bytes(args.source_root/w14_file, found[w14]["raw_sha256"])
        checks = self_test(grammar, originals[w14], raw, found[w14]["cases"][1]["values"], found[w14])
        out["refusal_control_names"] = checks
        out["refusal_controls"] = len(checks)
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
