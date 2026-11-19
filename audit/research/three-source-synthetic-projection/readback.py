"""Check the stock theorem records and diagnose only the four fixed incorrect statements."""

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = "W02_TERM "
AXIOM_ROW = re.compile(r"'([^']+)' (?:depends on axioms: \[([^\]]+)\]|does not depend on any axioms)")
FIELDS = {"name","owner","kind","ordinary_import_trust","universe_parameters",
          "type_constructor_representation","value_constructor_representation",
          "type_constants","value_constants","axioms"}

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result

def read_json(path):
    return json.loads(path.read_bytes(), object_pairs_hook=pairs)

def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()

def verify_negative(module, path, expected):
    with path.open(encoding="utf-8") as source:
        lines = source.read().splitlines()
    require(len(lines) == 1, "expected exactly one compiler diagnostic for " + module)
    row = json.loads(lines[0], object_pairs_hook=pairs)
    require(row["severity"] == "error" and row["isSilent"] is False, "non-error or silent diagnostic")
    require(Path(row["fileName"]).name == module+".lean" and row["pos"]["line"] == expected["line"],
            "diagnostic origin or source line changed")
    msg = row["data"]
    require(type(msg) is str and msg.startswith(expected["prefix"]) and
            all(s in msg for s in expected["contains"]), "unexpected compiler error for " + module)
    return {"module":module,"line":expected["line"],"diagnostic":msg,"stdout_sha256":digest(path)}

def verify_axioms(path, ordered, allowed):
    seen = {}
    with path.open(encoding="utf-8") as source:
        for line in source:
            match = AXIOM_ROW.fullmatch(line.rstrip("\n"))
            require(match is not None, "unexpected compiler diagnostic in axiom stream")
            name, listed = match.groups()
            deps = listed.split(", ") if listed else []
            require(name in ordered and name not in seen and len(deps) == len(set(deps))
                    and set(deps) <= allowed, "unexpected transitive axiom or name")
            seen[name] = sorted(deps)
    require(list(seen) == list(ordered), "incomplete or reordered axiom stream")
    return seen

def verify_terms(label, terms, axioms, plan):
    roster = read_json(HERE/(label.lower()+"-targets.json"))
    expect_use = read_json(HERE/"consumer-uses.json")
    observed_axes = verify_axioms(axioms,roster,set(plan["observer_stock_axioms"]))
    results = {}
    trusts = set()
    with terms.open(encoding="utf-8") as source:
        for line in source:
            require(line.startswith(PREFIX), "unexpected stdout from term observer")
            row = json.loads(line[len(PREFIX):], object_pairs_hook=pairs)
            require(type(row) is dict and set(row) == FIELDS, "missing or extra expression record fields")
            name = row["name"]
            require(name in roster and name not in results and row["kind"] == "theorem" and
                    row["owner"] == roster[name], "wrong theorem, kind or owner")
            require(row["universe_parameters"] == [] and row["axioms"] == observed_axes[name],
                    "universe parameters or transitive axioms differ")
            trust = row["ordinary_import_trust"]
            require(type(trust) is int and trust >= 0, "bad ordinary import trust")
            trusts.add(trust)
            expressions = {}
            for field in ("type_constructor_representation","value_constructor_representation"):
                raw = row[field]
                require(type(raw) is str and "Lean.Expr." in raw and not any(bad in raw for bad in
                        ("<unknown>","<opaque>","...","…","Lean.Expr.fvar","Lean.Expr.mvar","Lean.Level.mvar")),
                        "unobserved, open or incomplete expression")
                expressions[field] = hashlib.sha256(raw.encode()).hexdigest()
            for field in ("type_constants","value_constants"):
                constants = row[field]
                require(type(constants) is list and all(type(item) is str and item for item in constants)
                        and constants == sorted(set(constants)) and "sorryAx" not in constants,
                        "literal constant inventory")
            if name in expect_use:
                require(expect_use[name] in row["value_constants"], "typed consumer lacks required proof constant")
            results[name] = dict(owner=row["owner"], axioms=observed_axes[name], expressions=expressions)
    require(list(results) == list(roster) and len(trusts) == 1, "missing/reordered theorem or trust drift")
    return {"checked":len(results),"ordinary_import_trust":trusts.pop(),"declarations":results,
            "terms_stdout_sha256":digest(terms),"axioms_stdout_sha256":digest(axioms)}
