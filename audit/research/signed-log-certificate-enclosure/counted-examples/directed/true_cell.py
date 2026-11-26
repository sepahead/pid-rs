"""A genuine four-row empirical coordinate and two constructed dyadic reports.

Run with the path of the original check.py. An optional new output directory receives
the complete canonical input and all four constructed reports.
"""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys


READER = "9a6c3746937fa0db7ceaf1fc96a6753ce547948412133690778309781e60d1d6"
TOTAL = 1706
REVEALED = 538
P = 2048
SCALE = 1 << P
KEY = "cumulative.net.01"


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(data):
    return sha256(data).hexdigest()


def log_ratio(d, terms=500):
    """Bound ln((d+1)/(d-1)) with a single independent rational tail."""
    z = Fraction(1, d)
    power = z
    square = z * z
    partial = Fraction(0)
    for j in range(terms):
        partial += 2 * power / (2 * j + 1)
        power *= square
    return partial, partial + 2 * power / ((2 * terms + 1) * (1 - square))


def floor(value):
    return value.numerator // value.denominator


def true_cell():
    # (6/4)*(8/6)=2, using two distinct positive rational series.
    lo5, hi5 = log_ratio(5)
    lo7, hi7 = log_ratio(7)
    weight = Fraction(REVEALED, TOTAL)
    lo, hi = (lo5 + lo7) * weight, (hi5 + hi7) * weight
    lower = floor(SCALE * lo)
    need(lower == floor(SCALE * hi), "unique independently located grid cell")
    need(Fraction(lower, SCALE) < lo < hi < Fraction(lower + 1, SCALE), "strict interior")
    return lower, lo, hi


def four_rows():
    return [{"count": str(n), "source_states": [[a], ["fixed"], ["fixed"]], "target_state":[t]}
            for a, t, n in (("0","0",269), ("0","x",584), ("1","1",269), ("1","x",584))]


def prepare(panel, cell):
    b = {"definition_revision": panel.IDS["definition_revision"], "rows": four_rows(),
         "schema": panel.IDS["input_schema"], "sources": 3, "units": "nats"}
    raw = panel.canonical(b)
    table, total, plans, resources = panel.derive(raw)
    need(len(table) == 4 and total == TOTAL, "genuine occupied table and total")
    bindings = panel.bindings(raw)
    values = []
    for (scope, component, key, masks), plan in panel.A.projections(plans):
        coordinate = ".".join((scope, component, key))
        q = panel.A.exact_product(plan)
        if coordinate == KEY:
            need(masks == (1,) and plan == {Fraction(2):REVEALED} and q == (1 << REVEALED),
                 "original typed singleton net product")
            lo, hi = Fraction(cell, SCALE), Fraction(cell+1, SCALE)
        else:
            lo, hi = panel.A.log_interval(q, total, 256)
        need(hi-lo <= panel.A.MAX_WIDTH, "coordinate report width")
        values.append({"scope": scope, "component": component, "coordinate": coordinate,
            "key": key, "masks": list(masks), "bindings": bindings,
            "product": {"schema": panel.IDS["product_schema"],
                        "numerator": str(q.numerator), "denominator": str(q.denominator)},
            "interval": {"schema": panel.IDS["interval_schema"],
                         "lower": panel.dyadic(lo), "upper": panel.dyadic(hi)},
            "sign": "zero" if q == 1 else "positive" if q > 1 else "negative"})
    need(len(values) == 108, "complete report")
    payload = {k:panel.IDS[k] for k in panel.WIRE["payload"] if k not in ("resources","coordinates")}
    payload.update(resources=resources, coordinates=values)
    return raw, {"schema":panel.IDS["producer_schema"], "payload":payload}


def run(original, output):
    need(digest(original.read_bytes()) == READER, "original unchanged report reader")
    spec = importlib.util.spec_from_file_location("original_six_inputs", original)
    panel = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(panel)
    lower, lower_proof, upper_proof = true_cell()
    raw_b, original_report = prepare(panel, lower)
    stages = []
    for p in panel.A.SCHEDULE:
        lo, hi = panel.A.log_interval(Fraction(1 << REVEALED), TOTAL, p)
        width = (hi-lo) * (1 << p)
        need(width.denominator == 1 and width > 0, "strict positive original interval")
        need(hi-lo > Fraction(1,SCALE), "width excludes containment at every original stage")
        stages.append({"p":p, "width_in_its_own_grid":width.numerator})
    lo_fin, hi_fin = panel.A.log_interval(Fraction(1 << REVEALED),TOTAL,P)
    lo_num, hi_num = int(SCALE*lo_fin), int(SCALE*hi_fin)
    need(hi_num - lo_num == 2, "last genuine crossing")
    need((lo_num,hi_num) in ((lower-1,lower+1), (lower,lower+2)), "which side requires a unit")
    require_left = lo_num == lower-1
    results = []
    if output:
        output.mkdir(parents=True,exist_ok=False)
        (output / "B.json").write_bytes(raw_b)
    for label,left,right in (("tight",0,0), ("left",1,0), ("right",0,1), ("both",1,1)):
        side = deepcopy(original_report)
        chosen = next(c for c in side["payload"]["coordinates"] if c["coordinate"] == KEY)
        lower_grid, upper_grid = lower-left, lower+1+right
        lower_value, upper_value = Fraction(lower_grid,SCALE), Fraction(upper_grid,SCALE)
        chosen["interval"].update(lower=panel.dyadic(lower_value), upper=panel.dyadic(upper_value))
        need(panel.endpoint(chosen["interval"]["lower"]) == lower_value and
             panel.endpoint(chosen["interval"]["upper"]) == upper_value, "normal endpoint fields")
        need(upper_value-lower_value <= panel.A.MAX_WIDTH and lower_value < lower_proof and
             upper_proof < upper_value,"genuine outward normalized width and truth")
        raw_c = panel.canonical(side)
        need(len(raw_b) <= panel.INPUT_CAP and len(raw_c) <= panel.REPORT_CAP, "canonical size cap")
        if output:
            (output / ("C-"+label+".json")).write_bytes(raw_c)
        try:
            _, total, records, _ = panel.audit(raw_b, raw_c)
        except panel.Refusal as refusal:
            need(str(refusal) == "independent interval containment", "precise source refusal")
            status = "independent interval containment"
        else:
            selected = next(a for a in records if a["coordinate"] == KEY)
            need(len(records) == 108 and total == TOTAL and selected["precision_bits"] == P,
                 "actual complete qualified constructed report")
            need(all(a["precision_bits"] == 256 for a in records if a["coordinate"] != KEY),
                 "same other 107 intervals")
            status = "108 coordinates; selected coordinate accepted at 2048"
        should_pass = bool(left if require_left else right)
        need(status.startswith("108") == should_pass, "expected side-specific verdict")
        results.append({"report": label, "input_sha256": digest(raw_b), "report_sha256":digest(raw_c),
                        "report_size": len(raw_c), "selected_wire": chosen["interval"],
                        "width_2048_grid_units":upper_grid-lower_grid,"reader_verdict":status})
    # Two general failure modes of an unqualified padding statement.
    g = Fraction(1,1 << 256)
    need(panel.A.MAX_WIDTH + 2*g > panel.A.MAX_WIDTH, "padding can exceed the wire width cap")
    t = Fraction(1,5)
    l,u = Fraction(-7,10),t
    need(l<=t<=u and u-l<1 and floor(l)<t-1, "off-grid true endpoints need another argument")
    print(json.dumps({"scientific_object": "constructed four-row empirical MGW input; complete constructed reports; no original producer or new historical B/C pair",
          "original_checker_sha256": READER, "original_arithmetic_sha256": panel.ARITHMETIC_SHA,
          "input_sha256":digest(raw_b), "input_bytes":len(raw_b), "target_coordinate": KEY,
          "independent_true_cell_lower_2048_numerator":str(lower),
          "independent_true_cell_upper_2048_numerator":str(lower+1),"true_value":"(538/1706) ln 2",
          "proof":"ln 2 = ln(3/2)+ln(4/3); use 500 positive terms each at 1/5 and 1/7 with separate rational strict tails",
          "grid_bridge":{"last_original_lower_minus_proved_cell_lower":lo_num-lower,
                         "last_original_upper_minus_proved_cell_upper":hi_num-lower-1,
                         "only_necessary_padding_here":"left" if require_left else "right"},
          "stages": stages,"reports":results}, indent=2,sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) not in (2,3):
        raise SystemExit("Usage: python true_cell.py /path/to/original/check.py [new-output-directory]")
    run(Path(sys.argv[1]),Path(sys.argv[2]) if len(sys.argv)==3 else None)
