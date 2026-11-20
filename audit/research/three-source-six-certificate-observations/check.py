"""Read six fixed B/C pairs. Run as a script with Python 3.10 or newer."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import stat
import sys


ROOT = Path(__file__).resolve().parent
PANEL_SHA = "10df11c608caa228256f78be561b3ead0d6c565070f466192ffcfc6ae39b360c"
PROFILE_SHA = "569fb53f6300505ba595dcd0240a2e01e3f348271dbd2f3997c8696c2635d691"
ARITHMETIC_SHA = "b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2"
INPUT_CAP, REPORT_CAP = 4096, 128 * 1024


class Refusal(ValueError):
    pass


def need(condition, reason):
    if not condition:
        raise Refusal(reason)


def digest(raw):
    return sha256(raw).hexdigest()


def bounded(path, limit, label):
    try:
        info = path.lstat()
        need(stat.S_ISREG(info.st_mode) and 0 < info.st_size <= limit, label + " size/type")
        with path.open("rb") as stream:
            data = stream.read(limit + 1)
        need(len(data) == info.st_size, label + " changed size")
        return data
    except OSError as error:
        raise Refusal(label + " unavailable") from error


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")


def decode(raw, cap):
    need(0 < len(raw) <= cap and raw.isascii() and raw[-1:] == b"\n", "canonical envelope")
    # Every admitted field uses unescaped ASCII. Bound nesting before JSON recursion.
    depth, quoted = 0, False
    for octet in raw[:-1]:
        if octet == 92:
            raise Refusal("escaped field")
        if octet == 34:
            quoted = not quoted
        elif not quoted and octet in (91, 123):
            depth += 1
        elif not quoted and octet in (93, 125):
            depth -= 1
        need(0 <= depth <= 12, "nesting")
    need(not quoted and depth == 0, "incomplete JSON")

    def obj(pairs):
        result = dict(pairs)
        need(len(result) == len(pairs), "duplicate JSON member")
        return result

    def small_integer(value):
        need(len(value) <= 10, "JSON integer size")
        return int(value)

    def forbidden(_):
        raise Refusal("noninteger JSON number")

    value = json.loads(raw, object_pairs_hook=obj, parse_int=small_integer,
                       parse_float=forbidden, parse_constant=forbidden)
    need(canonical(value) == raw, "noncanonical JSON")
    return value


def strict_keys(value, expected, label):
    need(type(value) is dict and set(value) == set(expected), label + " fields")


def pinned(path, cap, expected_sha, label):
    raw = bounded(path, cap, label)
    need(digest(raw) == expected_sha, label + " identity")
    return raw


PANEL = json.loads(pinned(ROOT / "panel.json", 16_384, PANEL_SHA, "panel"))
PROFILE = json.loads(pinned(ROOT / "profile.json", 16_384, PROFILE_SHA, "profile"))
IDS, WIRE = PROFILE["ids"], PROFILE["wire"]
source = pinned(ROOT / "arithmetic.py", 32_768, ARITHMETIC_SHA, "arithmetic")
# Execute the bytes just authenticated, avoiding a cache or a second source read.
A = importlib.util.module_from_spec(importlib.util.spec_from_loader("panel_arithmetic", loader=None))
exec(compile(source, "arithmetic.py", "exec"), A.__dict__)


def event_probe_count():
    probes = 0
    for masks in A.lattice()[0]:
        pending = set(range(8))
        for mask in masks:
            probes += len(pending)
            pending = {x for x in pending if x & mask != mask}
    need(probes == 205, "match-mask probes")
    return probes


def derive(raw_b):
    b = decode(raw_b, INPUT_CAP)
    strict_keys(b, ("definition_revision", "rows", "schema", "sources", "units"), "B")
    need(b["schema"] == IDS["input_schema"] and b["definition_revision"] == IDS["definition_revision"]
         and type(b["sources"]) is int and b["sources"] == 3 and b["units"] == "nats", "B identity")
    rows = b["rows"]
    need(type(rows) is list and 1 <= len(rows) <= 8, "panel row cap")
    for row in rows:
        need(type(row) is dict and type(row.get("count")) is str
             and 1 <= len(row["count"]) <= 3, "panel count cap")
    table, total, lengths = A.typed_rows(rows)
    A.reserve(table, total, lengths)
    plans = A.base_plans(table, total)
    terms, exponent, bits, aggregate = A.preflight(A.projections(plans))
    r, nbits = len(table), total.bit_length()
    resources = {
        "aggregate_projected_product_bits": aggregate, "event_comparisons": event_probe_count() + 4*r*r,
        "maximum_absolute_exponent": exponent, "maximum_coordinate_terms": terms,
        "maximum_projected_coordinate_bits": bits,
        "planned_peak_heap_bytes": 40*(1 << 20) + 24*len(raw_b) + 400*r*(320 + 8*((nbits+7)//8)),
        "positive_rows": r, "total_count_bits": nbits,
    }
    return table, total, plans, resources


def endpoint(value):
    strict_keys(value, ("coefficient", "exponent"), "dyadic")
    text, exp = value["coefficient"], value["exponent"]
    need(type(text) is str and len(text) <= 650 and re.fullmatch(r"0|-?[1-9][0-9]*", text)
         and type(exp) is int and abs(exp) <= 2048, "panel dyadic representation")
    coefficient = int(text)
    need((coefficient == 0 and exp == 0) or coefficient % 2 == 1, "dyadic normalization")
    return Fraction(coefficient << exp) if exp >= 0 else Fraction(coefficient, 1 << -exp)


def dyadic(value):
    denominator = value.denominator
    need(denominator & (denominator - 1) == 0, "independent endpoint base")
    exponent = 1 - denominator.bit_length()
    numerator = value.numerator
    if numerator == 0:
        return {"coefficient": "0", "exponent": 0}
    shift = (abs(numerator) & -abs(numerator)).bit_length() - 1
    return {"coefficient": str(numerator >> shift), "exponent": exponent + shift}


def bindings(raw_b):
    fixed = {k: v["sha256"] for k, v in PROFILE["digest_domains"].items() if type(v) is dict}
    return dict(fixed, input_sha256=digest(raw_b), source_manifest_sha256=PANEL["source_manifest_sha256"])


def audit(raw_b, raw_c):
    table, total, plans, resources = derive(raw_b)
    c = decode(raw_c, REPORT_CAP)
    strict_keys(c, WIRE["C"], "C")
    need(c["schema"] == IDS["producer_schema"], "C schema")
    p = c["payload"]
    strict_keys(p, WIRE["payload"], "payload")
    for field in set(p) - {"resources", "coordinates"}:
        need(type(p[field]) is type(IDS[field]) and p[field] == IDS[field], "payload " + field)
    strict_keys(p["resources"], WIRE["resources"], "resources")
    for field, value in resources.items():
        need(type(p["resources"][field]) is int and p["resources"][field] == value, "resource " + field)
    coords = p["coordinates"]
    need(type(coords) is list and len(coords) == 108, "coordinate count")
    expected_bindings = bindings(raw_b)
    observations, products = [], {}
    for expected_id, (identity, plan), coord in zip(PANEL["coordinate_identities"], A.projections(plans), coords, strict=True):
        scope, component, key, masks = identity
        stable_id = ".".join((scope, component, key))
        strict_keys(coord, WIRE["coordinate"], "coordinate")
        need((coord["scope"], coord["component"], coord["key"], coord["coordinate"], expected_id)
             == (scope, component, key, stable_id, stable_id), "coordinate identity")
        need(type(coord["masks"]) is list and all(type(i) is int for i in coord["masks"])
             and tuple(coord["masks"]) == masks, "coordinate masks")
        need(coord["bindings"] == expected_bindings, "coordinate bindings")
        q = A.exact_product(plan)
        product = coord["product"]
        need(product == {"schema": IDS["product_schema"], "numerator": str(q.numerator),
                         "denominator": str(q.denominator)}, "exact product")
        sign = "zero" if q == 1 else "positive" if q > 1 else "negative"
        need(coord["sign"] == sign, "exact sign")
        interval = coord["interval"]
        strict_keys(interval, WIRE["interval"], "interval")
        need(interval["schema"] == IDS["interval_schema"], "interval schema")
        lo, hi = endpoint(interval["lower"]), endpoint(interval["upper"])
        need(0 <= hi-lo <= A.MAX_WIDTH, "interval width/order")
        for precision in A.SCHEDULE:
            independent_lo, independent_hi = A.log_interval(q, total, precision)
            if lo <= independent_lo <= independent_hi <= hi:
                break
        else:
            raise Refusal("independent interval containment")
        observations.append({"scope": scope, "component": component, "coordinate": stable_id,
                             "key": key, "masks": list(masks), "numerator": str(q.numerator),
                             "denominator": str(q.denominator), "sign": sign, "precision_bits": precision,
                             "independent_lower": dyadic(independent_lo), "independent_upper": dyadic(independent_hi),
                             "producer_lower": interval["lower"], "producer_upper": interval["upper"], "subset": True})
        products[(scope, component, masks)] = q
    return table, total, observations, products


def check_relations(cases):
    tables = {name: dict(case[0]) for name, case in cases.items()}
    negative = tables["negative"]
    relabel = {(tuple("A"+t for t in a), tuple("B"+t for t in b), tuple("C"+t for t in c),
                tuple("T"+t for t in y)): m for (a,b,c,y), m in negative.items()}
    need(tables["relabel_negative"] == relabel, "label transformation of B")
    need(tables["permute_negative"] == {(b,c,a,y): m for (a,b,c,y), m in negative.items()}, "permutation of B")
    need(tables["replicate_unit"] == {k: 2*m for k,m in tables["unit"].items()}, "duplication of B")
    need(len({key[3] for key in tables["weighted"]}) == 1, "constant target in B")
    result = Counter()
    for name, left, right in (("label_replacement","negative","relabel_negative"),
                               ("cyclic_source_permutation","negative","permute_negative"),
                               ("doubling_all_counts","unit","replicate_unit")):
        for (scope, comp, masks), q in cases[left][3].items():
            destination = masks
            if name == "cyclic_source_permutation":
                destination = tuple(sorted((m >> 1) | ((m & 1) << 2) for m in masks))
            expected = q*q if name == "doubling_all_counts" else q
            need(cases[right][3][scope, comp, destination] == expected, name)
            result[name] += 1
    for (_, comp, _), q in cases["weighted"][3].items():
        if comp == "net":
            need(q == 1, "constant target product")
            result["constant_target_signed_zeros"] += 1
    need(sorted(result.values()) == [36,108,108,108], "registered relation coverage")
    return dict(result)


def run_panel():
    given = {}
    for item in PANEL["cases"]:
        name = item["case"]
        folder = ROOT / "cases" / name
        need(not folder.is_symlink() and not folder.parent.is_symlink(), "case directory")
        b = pinned(folder/"B.json", INPUT_CAP, item["B_sha256"], "B")
        c = pinned(folder/"C.json", REPORT_CAP, item["C_sha256"], "C")
        need((len(b), len(c)) == (item["B_bytes"], item["C_bytes"]), "B/C declared lengths")
        result = audit(b, c)
        need(digest(canonical(result[2])) == item["coordinate_readback_sha256"], "registered 108-record readback")
        given[name] = result
    return given, check_relations(given)


if __name__ == "__main__":
    try:
        need(len(sys.argv) == 1 or len(sys.argv) == 3 and sys.argv[1] == "--coordinates", "arguments")
        cases, relations = run_panel()
        if len(sys.argv) == 3:
            need(sys.argv[2] in cases, "unknown case")
            output = cases[sys.argv[2]][2]
        else:
            output = {"case_count":len(cases), "coordinates":sum(len(r[2]) for r in cases.values()),
                      "relations":relations, "result":"six published empirical tables agree with their records"}
        sys.stdout.buffer.write(canonical(output))
    except (ValueError, OSError) as error:
        raise SystemExit("refused: " + str(error)) from None
