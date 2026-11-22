"""Read the pinned three-source count records and replay two finite event calculations."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WEIGHTED = "audit/research/three-source-alphabet-counts/"


def require(matched, message):
    if not matched:
        raise ValueError(message)


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique_keys)


def typed_equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(typed_equal(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(typed_equal(a, b) for a, b in zip(left, right))
    return left == right


def normalized_type(value):
    value = value.replace("PidFin3AlphabetCounts.", "Count.").replace("PidFin3CountRaw.", "Count.")
    return re.sub(r"\b_h(?=[A-Z])", "h", value).split()


def check_stock(pins):
    records = {}
    for path, ref in pins["stock_records"].items():
        data = (ROOT / path).read_bytes()
        require(type(ref["bytes"]) is int and len(data) == ref["bytes"], f"length of {path}")
        require(sha256(data).hexdigest() == ref["sha256"], f"identity of {path}")
        records[path] = data
    def weighted(path):
        return records[WEIGHTED + path]

    original = decode(weighted("observations.json"))
    dependencies = decode(weighted("portable-run/dependencies.json"))
    by_name = {row["name"]: row for row in dependencies}
    require(len(by_name) == len(dependencies) == 86, "direct dependency roster")
    emitted = [line.split(b" ", 1) for line in weighted("declarations.txt").splitlines()]
    tags = [tag for tag, _ in emitted]
    require(tags == [b"COUNT22_HELPER"] + [b"COUNT22_DEFINITION"] * 9 + [b"COUNT22_THEOREM"] * 22,
            "stock declaration sequence")
    with (HERE / "ledger.tsv").open(encoding="utf-8", newline="") as f:
        ledger = list(csv.DictReader(f, delimiter="\t"))
    require([r["id"] for r in ledger] == [str(i) for i in range(1, 23)], "ledger sequence")
    stems = [r["theorem"] for r in ledger]
    require(stems == original["theorem_stems"], "22 theorem names and order")
    raw = weighted("lean/CountRaw.lean").decode()
    prose = (HERE / "LEDGER.md").read_text()
    decision_terms = {"j": "[DecidableEq J]", "s": "[∀ i : Source, DecidableEq (Alpha i)]",
                      "t": "[DecidableEq Beta]", "e": "[DecidablePred E]", "f": "[DecidablePred F]"}
    for ledger_row, (_, stream) in zip(ledger, emitted[10:], strict=True):
        row = decode(stream)
        name = ledger_row["theorem"]
        candidate, target, consumer = (prefix + "." + name for prefix in
                                       ("PidFin3AlphabetCounts", "PidFin3CountRaw", "PidFin3CountConsumers"))
        require([row["theorem"], row["raw_target"], row["consumer"]] == [candidate, target, consumer], name)
        require(row["kind"] == "theorem" and row["status"] == "matched_exact_scoped_type", name)
        require(normalized_type(row["full_type"]) == normalized_type(row["raw_full_target"]), name)
        require(row["raw_universes"] == row["candidate_universes"] == row["consumer_universes"], name)
        require(row["consumer_full_type"] == target + ".{" + ", ".join(row["raw_universes"]) + "}", name)
        require(by_name[consumer]["type_constants"] == [target]
                and by_name[consumer]["value_constants"] == [candidate], name)
        require(row["axioms"] == by_name[candidate]["transitive_axioms"], name)
        raw_target = re.search(r"^def " + re.escape(name) + r" : Prop :=\n(.*?)(?=\n\n)", raw, re.M | re.S)
        require(raw_target is not None, "source type " + name)
        decisions = [key for key, term in decision_terms.items() if term in raw_target[0]]
        require(ledger_row["decisions"] == (",".join(decisions) or "none"), "decision premises " + name)
        line = raw[:raw_target.start()].count("\n") + 1
        marker = f"| {ledger_row['id']}. [{name}]("
        lines = [r for r in prose.splitlines() if r.startswith(marker)]
        require(len(lines) == 1 and f"CountRaw.lean#L{line})" in lines[0], "documentation link " + name)
    print(f"Matched {len(ledger)} theorem records, typed uses and source rows in the 86-name dependency record.")


def main():
    pins = decode((HERE / "sources.json").read_bytes())
    expected_file = HERE / "finite-results.json"
    for path, key in [(expected_file, "finite_results_sha256"), (HERE / "ledger.tsv", "ledger_tsv_sha256"),
                      (HERE / "parity-results.json", "parity_results_sha256")]:
        require(sha256(path.read_bytes()).hexdigest() == pins[key], path.name)
    expected = decode(expected_file.read_bytes())
    check_stock(pins)
    commands = ([sys.executable, "-ISB", "check_sets.py"], [sys.executable, "-OISB", "check_sets.py"],
                ["ruby", "--disable-gems", "check_masks.rb"])
    for command in commands:
        raw = subprocess.check_output(command, cwd=HERE, timeout=60)
        require(typed_equal(decode(raw), expected), "finite result from " + " ".join(command))
    print("Accepted all three finite records: 4,096 truth cases and 147,744 joint counts over 513 tables.", flush=True)
    flags = "-OISB" if sys.flags.optimize else "-ISB"
    subprocess.run([sys.executable, flags, "check_parity.py"], cwd=HERE, check=True, timeout=60)


if __name__ == "__main__":
    main()
