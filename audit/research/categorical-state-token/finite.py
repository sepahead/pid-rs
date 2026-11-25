"""Read ten published count tables and recompute concrete exact rational certificate checks."""
import argparse
import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

STUDY = Path(__file__).resolve().parent
ROSTER_SHA = "7e3e0d29112f356e8bb83d29f6d9b24791c40d42ad79816d9e1222696200c179"


def require(ok, label):
    if not ok:
        raise ValueError(label)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(path, expected):
    raw = path.read_bytes()
    require(sha(raw) == expected, "changed input " + path.name)
    return raw


def dyadic(value):
    return Fraction(int(value["coefficient"])) * Fraction(2) ** value["exponent"]


def row(source, target, count):
    return {"count": str(count), "source_states": [[source], [source], [source]], "target_state": [target]}


def refuse(f, reason):
    try:
        f()
    except ValueError as error:
        require(str(error) == reason, "wrong refusal " + str(error))
    else:
        raise ValueError("expected refusal " + reason)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--repository", type=Path, default=STUDY.parents[2],
                     help="pid-rs root containing the earlier six-case reader")
    cli.add_argument("--self-test", action="store_true", help="also reproduce nine malformed input controls")
    args = cli.parse_args()
    old = args.repository / "audit/research/three-source-six-certificate-observations/check.py"
    spec = importlib.util.spec_from_file_location("prior_six", old)
    panel = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(panel)
    roster = json.loads(checked(STUDY / "observations.json", ROSTER_SHA))
    originals, relations = panel.run_panel()
    require(relations == roster["historical_transform_counts"] and len(originals) == 6, "historical controls")
    original_negative = originals["negative"]
    require(original_negative[1] == 3 and original_negative[3][("cumulative", "net", (2,4))] == Fraction(9,16),
            "negative signed observation")
    members = {
        "singleton1": [row("A","fixed",1)], "singleton7": [row("A","fixed",7)],
        "constant-equal": [row("A","fixed",1), row("B","fixed",1)],
        "copy-equal": [row("A","A",1), row("B","B",1)],
    }
    empty_header = dict(definition_revision=panel.IDS["definition_revision"], rows=[],
                        schema=panel.IDS["input_schema"], sources=3, units="nats")

    def encode(rows):
        return panel.canonical(dict(empty_header, rows=rows))

    fixed = {}
    for name, rows in members.items():
        directory = STUDY / "cases" / name
        observed = roster["positive"][name]
        b = checked(directory / "B.json", observed["B"])
        c = checked(directory / "C.json", observed["C"])
        require(encode(rows) == b, "full labeled input " + name)
        table, total, points, products = panel.audit(b, c)
        require(len(table) == len(rows) and total == sum(int(r["count"]) for r in rows)
                and len(points) == len(products) == 108, "original schema and total " + name)
        require(sum(q==1 for q in products.values()) == observed["unit_products"]
                and sum(q>1 for q in products.values()) == observed["nonunit_positive"]
                and sum(q<1 for q in products.values()) == observed["nonunit_negative"], "products " + name)
        if name.startswith("singleton"):
            require(all(q == 1 for q in products.values()), "all singleton factors")
        else:
            for (scope, component, _), q in products.items():
                if scope == "cumulative":
                    expected = 1 if component == ("net" if name == "constant-equal" else "misinformative") else 4
                    require(q == expected, "direct event-mass check " + name + " " + component)
                if name == "constant-equal" and component == "net":
                    require(q == 1, "constant-target signed atom or cumulative value")
        fixed[name] = b, c

    b, c = fixed["copy-equal"]
    for kind in ("false_coordinate", "two_certificates"):
        alt = json.loads(c)
        predicate = next(z for z in alt["payload"]["coordinates"] if z["coordinate"] == "cumulative.net.01")
        require(predicate["product"]["numerator"] == "4" and predicate["product"]["denominator"] == "1", "known base value")
        if kind == "false_coordinate":
            predicate["product"]["numerator"] = "3"
        else:
            interval = predicate["interval"]
            gap = Fraction(1,2**190)
            low, high = dyadic(interval["lower"])-gap, dyadic(interval["upper"])+gap
            require(high-low <= Fraction(1,2**160), "new interval width")
            interval.update(lower=panel.dyadic(low), upper=panel.dyadic(high))
        other = panel.canonical(alt)
        require(sha(other) == roster[kind]["other_C"] and other != c and sha(b) == roster[kind]["B"], "changed C identity")
        if kind == "false_coordinate":
            refuse(lambda: panel.audit(b, other), "exact product")
        else:
            require(len(panel.audit(b, other)[2]) == 108, "distinct accepted interval")
    if args.self_test:
        c = fixed["singleton1"][1]
        controls = {
            "empty-bytes": (b"", "canonical envelope"),
            "empty-rows": (encode([]), "panel row cap"),
            "empty-token": (encode([row("","fixed",1)]), "token"),
            "space-token": (encode([row("A B","fixed",1)]), "token"),
            "overlong-token": (encode([row("A"*129,"fixed",1)]), "token"),
            "zero-count": (encode([row("A","fixed",0)]), "positive-count-bits"),
            "empty-state": (encode([dict(row("A","fixed",1), source_states=[[],["A"],["A"]])]), "state-token-count"),
            "duplicate-row": (encode([row("A","fixed",1),row("A","fixed",1)]), "row-order-or-duplicate"),
            "no-final-lf": (fixed["singleton1"][0][:-1], "canonical envelope"),
        }
        for key, (raw, reason) in controls.items():
            require(sha(raw) == roster["negative"][key]["B"], "unchanged adverse bytes " + key)
            refuse(lambda: panel.audit(raw,c), reason)
    print(json.dumps({"six_prior_pairs":len(originals),"four_new_pairs":len(fixed),"coordinates_per_pair":108,
                      "prior_negative_coordinate":"ln(9/16)/3","copy_cumulative_net_01":"ln(4)/2",
                      "distinct_valid_C_for_one_B":2,"false_rational_rejected":True,
                      "malformed_B_rejections":9 if args.self_test else 0},sort_keys=True,separators=(",",":")))


if __name__ == "__main__":
    main()
