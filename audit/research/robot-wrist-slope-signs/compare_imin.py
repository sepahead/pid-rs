"""Compare the Williams–Beer minimum with the original five counted robot-wrist tables."""
import argparse
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import itertools
import json
from math import prod
from pathlib import Path

HERE = Path(__file__).resolve().parent
CERTIFICATE = "94ba9611a6fb38c8df5c1e3aa8ff798149649e729bc4b9b02ecd960ba45c219c"
SUMMARY = "0f328136c8acebd081cc3f7254bfc1887ed3c20ec12f741c5eaca2e26826de5e"
FIELDS = ("redundant", "unique_f", "unique_q", "synergy", "mi_f", "mi_q", "mi_joint")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def product(values):
    return prod(values, start=Fraction(1))


def read_original(path, expected):
    data = path.read_bytes()
    require(sha256(data).hexdigest() == expected, "original source changed: " + path.name)
    return json.loads(data)


def ratio_pair(number):
    return [str(number.numerator), str(number.denominator)]


def log_mean(number, total):
    with localcontext() as ctx:
        ctx.prec = 80
        x = Decimal(number.numerator) / Decimal(number.denominator)
        return format(x.ln() / Decimal(total), ".12f")


def minimum_information(counts):
    """Return positive rational exp(N times a mean) for every reported quantity."""
    require(counts and all(type(c) is int and c > 0 for c in counts.values()), "positive multiplicities")
    n = sum(counts.values())
    ny = Counter()
    for (f, q, y), c in counts.items():
        ny[y] += c

    specific = []
    for inputs in ((0,), (1,), (0, 1)):
        marginal = Counter()
        classes = {y: Counter() for y in ny}
        for key, c in counts.items():
            state = tuple(key[i] for i in inputs)
            marginal[state] += c
            classes[key[2]][state] += c
        values = {}
        for y, row in classes.items():
            values[y] = product(
                Fraction(c * n, marginal[state] * ny[y]) ** c
                for state, c in row.items()
            )
        specific.append(values)

    force, torque, both = specific
    minima = {y: min(force[y], torque[y]) for y in ny}
    red = product(minima.values())
    mi_f, mi_q, joint = (product(v.values()) for v in specific)
    quantities = {
        "redundant": red,
        "unique_f": mi_f / red,
        "unique_q": mi_q / red,
        "synergy": joint * red / (mi_f * mi_q),
        "mi_f": mi_f,
        "mi_q": mi_q,
        "mi_joint": joint,
    }
    require(product(quantities[k] for k in FIELDS[:4]) == joint, "four atom products reconstruct joint information")
    require(all(value >= 1 for value in quantities.values()), "nonnegative Williams–Beer quantities")
    choices = {}
    for y in sorted(ny):
        smaller = "tie" if force[y] == torque[y] else ("force" if force[y] < torque[y] else "torque")
        choices[y] = {"count":ny[y], "force":ratio_pair(force[y]), "torque":ratio_pair(torque[y]), "minimum":smaller}
    return quantities, choices


def modal_correct(counts):
    scores = []
    for inputs in ((), (0,), (1,), (0, 1)):
        by_input = {}
        for key, count in counts.items():
            predictors = tuple(key[i] for i in inputs)
            by_input.setdefault(predictors, Counter())[key[2]] += count
        scores.append(sum(max(classes.values()) for classes in by_input.values()))
    return scores


def input_counts(cells, nclasses, total):
    states = itertools.product((-1, 0, 1), (-1, 0, 1), range(nclasses))
    require(len(cells) == 9 * nclasses and all(type(x) is int and x >= 0 for x in cells), "original complete force/torque/class axes")
    counts = {key:c for key,c in zip(states, cells, strict=True) if c}
    require(sum(counts.values()) == total, "original task record count")
    return counts


def reference(path):
    from calculation import fractional
    cert = read_original(path / "certificate.json", CERTIFICATE)
    previous = read_original(path / "results.json", SUMMARY)
    require(previous["certificate_sha256"] == CERTIFICATE and previous["correct_order"] == ["prior","force","torque","both"], "source join and decision order")
    out = []
    cases = {}
    for raw, meta in zip(cert["tasks"], previous["tasks"], strict=True):
        task = raw["id"]
        require(task == meta["id"], "task identity")
        n = meta["n"]
        labels = meta["label_order"]
        counts = input_counts(raw["counts"], len(labels), n)
        values, choices = minimum_information(counts)
        old = {k:fractional(raw["log_products"][k]) for k in FIELDS}
        for k in FIELDS[4:]:
            require(values[k] == old[k], "exact Shannon product: " + task + " " + k)
        require(modal_correct(counts) == meta["modal_correct"] == raw["correct"], "four exact decision counts")
        entry = {
            "id": task, "N": n, "occupied_joint_keys": len(counts),
            "specific_information": {labels[y]:rec for y,rec in choices.items()},
            "imin_exp_N_times_mean": {k:ratio_pair(v) for k,v in values.items()},
            "imin_nats": {k:log_mean(v,n) for k,v in values.items()},
            "mgw_nats": {k:log_mean(v,n) for k,v in old.items()},
            "modal_correct": modal_correct(counts),
        }
        out.append(entry)
        cases[task] = (counts, old, values)
    require([x["id"] for x in out] == ["LP1","LP2","LP3","LP4","LP5"], "all five original tasks")
    return {"schema":"robot-wrist-class-specific-minimum-v1","original_certificate":CERTIFICATE,
            "unit":"nat per recorded task episode","modal_order":previous["correct_order"],"tasks":out}, cases


def check_controls(cases):
    pairs = list(itertools.product(range(2), repeat=2))
    toys = {
        "copy": (Counter((a,b,a) for a,b in pairs), [1,16,1,1]),
        "xor": (Counter((a,b,a^b) for a,b in pairs), [1,1,1,16]),
        "two-bit-target": (Counter((a,b,2*a+b) for a,b in pairs), [16,1,1,16]),
        "constant": (Counter((a,b,0) for a,b in pairs), [1,1,1,1]),
    }
    for name,(counts,expected) in toys.items():
        values,choice = minimum_information(counts)
        require([values[k] for k in FIELDS[:4]] == expected, name+" exact four products")
        if name in ("xor","two-bit-target","constant"):
            require(all(d["minimum"] == "tie" for d in choice.values()), name+" actual specific ties")
    after_min = []
    unequal_class_weight = []
    for task,(counts, old, values) in cases.items():
        switched = Counter({(q,f,y):c for (f,q,y),c in counts.items()})
        doubled = Counter({key:2*c for key,c in counts.items()})
        v_swap,_ = minimum_information(switched)
        v_double,_ = minimum_information(doubled)
        permutation = dict(zip(FIELDS,("redundant","unique_q","unique_f","synergy","mi_q","mi_f","mi_joint"),strict=True))
        require(all(v_swap[k] == values[permutation[k]] and v_double[k] == values[k] ** 2 for k in FIELDS), "source exchange and record duplication: "+task)
        require(modal_correct(doubled) == [2*m for m in modal_correct(counts)], "duplicated modal counts")
        after_min.append(values["redundant"] != min(values["mi_f"], values["mi_q"]))
        _, choices = minimum_information(counts)
        nclasses = len(choices)
        # The products each factor into integers no greater than the task total.
        # Rational prime exponents avoid raising large fractions to a common denominator.
        total = sum(counts.values())
        difference = Counter()
        for item in choices.values():
            factor = min(Fraction(*map(int, item["force"])), Fraction(*map(int, item["torque"])))
            coefficient = Fraction(1, nclasses * item["count"]) - Fraction(1, total)
            for sign, integer in [(1, factor.numerator), (-1, factor.denominator)]:
                for prime in range(2, total + 1):
                    while integer % prime == 0:
                        integer //= prime
                        difference[prime] += sign * coefficient
                    if integer == 1:
                        break
                require(integer == 1, "all empirical product primes come from a positive count no larger than N")
        unequal_class_weight.append(any(difference.values()))
    require(any(after_min), "panel distinguishes a minimum taken after class averaging")
    require(any(unequal_class_weight), "panel distinguishes wrong class weights")
    for cells, classes, n in [([0]*9,1,1),([1]*8,1,8),([True]+[0]*8,1,1),([-1]+[1]*8,1,7)]:
        try:
            input_counts(cells, classes, n)
        except ValueError:
            continue
        raise ValueError("invalid counted input accepted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit", action="store_true", help="print the complete calculated record")
    parser.add_argument("--self-test", action="store_true", help="also run the exact counterexamples and transformations")
    opts = parser.parse_args()
    import sys
    sys.path.insert(0, str(HERE))
    result,cases = reference(HERE)
    if opts.self_test:
        check_controls(cases)
    text = json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if opts.emit:
        print(text, end="")
    else:
        require(text.encode() == (HERE / "imin-comparison.json").read_bytes(), "complete separately received record")
        print("PASS five class-specific minima, exact atom and Shannon products, and four modal rules per task")
if __name__ == "__main__":
    main()
