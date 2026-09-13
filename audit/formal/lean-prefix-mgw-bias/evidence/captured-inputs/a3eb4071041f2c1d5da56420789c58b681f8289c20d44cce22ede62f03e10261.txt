"""MGW source filter and record parser, not a complete Lean grammar or sandbox.

Actual declarations, types and proof axioms require the separate semantic/kernel judge.
"""

from __future__ import annotations

import re


THEOREMS = (
    "actual_join_lub", "mismatch_generator_and_exclusion",
    "generator_nonnegative_and_total", "generator_lower_cumulative",
    "target_conditioning_mass", "supported_anchor_domains",
    "conditional_generator_support", "informative_inverse_identification",
    "misinformative_inverse_identification", "component_nonnegative_strict_support",
    "signed_mgw_cumulative",
)
IMPORTS = (
    "PidMgwBridge.Contract", "MgwBridgeDepsV1.SxDnf.Proofs",
    "MgwBridgeDepsV1.JoinLog.Proofs",
)
AXIOMS = frozenset({"Classical.choice", "Quot.sound", "propext"})


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def candidate_policy(raw, base, path):
    require(len(raw) <= 2 * 1024**2, "candidate exceeds source byte budget")
    source = raw.decode("utf-8", errors="strict")
    masked = base.mask_lean_comments_and_strings(source, path)
    imports = re.findall(r"(?m)^\s*import\s+([^\n]+)$", masked)
    require(tuple(imports) == IMPORTS, "candidate import roster differs")
    require(re.findall(r"(?m)^\s*namespace\s+([^\n]+)$", masked)
            == ["PidMgwBridgeCandidate"], "candidate namespace differs")
    require(re.findall(r"(?m)^\s*end\s+([^\n]+)$", masked)
            == ["PidMgwBridgeCandidate"], "candidate namespace closing differs")
    require(re.findall(r"(?m)^\s*set_option\s+([^\n]+)$", masked)
            == ["autoImplicit false", "warningAsError true"], "strict options differ")
    forbidden = re.search(
        r"\b(?:sorry|sorryAx|admit|axiom|constant|opaque|native_decide|unsafe|partial|"
        r"run_cmd|run_tac|run_elab|run_meta|run_io|by_elab|eval_expr|elab|macro|syntax|"
        r"initialize|builtin_initialize|implemented_by|extern|attribute|export|deriving|"
        r"instance|class|structure|inductive|def|abbrev|mutual|variable|variables|"
        r"include|omit|section|noncomputable|notation|infix|infixl|infixr|"
        r"prefix|postfix)\b|#|@\[", masked)
    require(forbidden is None, "candidate contains prohibited code")
    require(re.findall(r"(?m)^\s*universe\s+([^\n]+)$", masked)
            == ["u v w"], "candidate universes differ")
    openings = re.findall(r"(?m)^\s*open\s+([^\n]+)$", masked)
    require(len(openings) == len(set(openings))
            and set(openings) <= {"scoped BigOperators", "PidMgwBridgeContract"},
            "candidate open commands differ")
    declarations = base.source_declaration_inventory(source, path)
    public = []
    for line in masked.splitlines():
        item = re.match(r"^\s*(private\s+)?(theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_]*)\b", line)
        if item and not item.group(1):
            require(item.group(2) == "theorem", "public export is not a theorem")
            public.append(item.group(3))
    require(tuple(public) == THEOREMS, "public theorem source roster differs")
    require(len(declarations) == len(re.findall(
        r"(?m)^\s*(?:private\s+)?(?:theorem|lemma)\s+", masked)),
        "unsupported top-level declaration")


def semantic_records(raw, strict_json):
    lines = raw.decode("utf-8", errors="strict").splitlines()
    require(len(lines) == len(THEOREMS), "semantic record count differs")
    records = []
    fields = {"theorem", "raw_target", "alias_target", "universes",
              "full_elaborated_type", "axioms", "status"}
    for index, (name, line) in enumerate(zip(THEOREMS, lines, strict=True)):
        prefix = "MGW_BRIDGE_JUDGE_RESULT "
        require(line.startswith(prefix), "semantic record prefix differs")
        record = strict_json(line[len(prefix):].encode())
        require(type(record) is dict and set(record) == fields, "semantic record fields differ")
        require(record["theorem"] == "PidMgwBridgeCandidate." + name
                and record["raw_target"] == "PidMgwBridgeRawTargets." + name
                and record["alias_target"] == "PidMgwBridgeAliasTargets." + name
                and record["status"] == "accepted", "semantic record identity differs")
        levels = record["universes"]
        require(type(levels) is list and len(levels) == (1 if index == 0 else 3)
                and all(type(x) is str and bool(x) for x in levels)
                and len(levels) == len(set(levels)), "semantic universes differ")
        axioms = record["axioms"]
        require(type(axioms) is list and all(type(x) is str for x in axioms)
                and axioms == sorted(set(axioms)) and set(axioms) <= AXIOMS,
                "semantic axiom policy differs")
        require(type(record["full_elaborated_type"]) is str
                and bool(record["full_elaborated_type"].strip()), "elaborated type is absent")
        records.append(record)
    return records
