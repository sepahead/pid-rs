"""Exercise the projection reader with invented tables and deliberately altered records."""
from copy import deepcopy
from fractions import Fraction
import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


spec = importlib.util.spec_from_file_location("six_readback", Path(__file__).with_name("check.py"))
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


def synthetic_pair():
    rows = [
        {"count":"1", "source_states":[["alpha"],["cold"],["a"]], "target_state":["green"]},
        {"count":"3", "source_states":[["beta"], ["warm"],["b"]], "target_state":["yellow"]},
    ]
    b = {"definition_revision":panel.IDS["definition_revision"], "rows":rows,
         "schema":panel.IDS["input_schema"], "sources":3, "units":"nats"}
    raw = panel.canonical(b)
    _, total, plans, resources = panel.derive(raw)
    records = []
    for (scope, component, key, masks), plan in panel.A.projections(plans):
        q = panel.A.exact_product(plan)
        lo, hi = panel.A.log_interval(q, total, 256)
        if q != 1:
            lo -= Fraction(1, 1 << 200)
            hi += Fraction(1, 1 << 200)
        records.append({
            "scope":scope, "component":component, "key":key, "coordinate":".".join((scope,component,key)),
            "masks":list(masks), "bindings":panel.bindings(raw),
            "product":{"schema":panel.IDS["product_schema"],"numerator":str(q.numerator),"denominator":str(q.denominator)},
            "interval":{"schema":panel.IDS["interval_schema"],"lower":panel.dyadic(lo),"upper":panel.dyadic(hi)},
            "sign":"positive" if q > 1 else "negative" if q < 1 else "zero",
        })
    payload = {k:panel.IDS[k] for k in panel.WIRE["payload"] if k not in ("resources","coordinates")}
    payload.update(resources=resources, coordinates=records)
    return b, {"schema":panel.IDS["producer_schema"],"payload":payload}


def run():
    b, c = synthetic_pair()
    raw_b, raw_c = panel.canonical(b), panel.canonical(c)
    _, total, records, _ = panel.audit(raw_b, raw_c)
    results = {}

    def refuse(label, reason, f):
        try:
            f()
        except ValueError as error:
            panel.need(str(error) == reason, label + " unexpected reason " + str(error))
            results[label] = reason
            return
        raise panel.Refusal(label + " unexpectedly accepted")

    with TemporaryDirectory() as tmp:
        for lab, raw, other, cap in (("B",raw_b,raw_c,panel.INPUT_CAP),("C",raw_c,raw_b,panel.REPORT_CAP)):
            path = Path(tmp) / (lab+".json")
            refuse("missing "+lab, lab+" unavailable",
                   lambda: panel.pinned(path,cap,panel.digest(raw),lab))
            # Substitute another complete, valid object of the same class and size.
            material = raw.replace(b"alpha",b"omega") if lab == "B" else raw.replace(b'"positive"',b'"negative"',1)
            panel.need(material != raw and len(material) == len(raw), "synthetic replacement")
            path.write_bytes(material)
            refuse("replaced "+lab, lab+" identity",
                   lambda: panel.pinned(path,cap,panel.digest(raw),lab))
    idx = next(i for i,x in enumerate(records) if x["sign"] == "positive")
    idx0 = next(i for i,x in enumerate(records) if x["sign"] == "zero")
    def changed(label, reason, action, index=idx):
        new = deepcopy(c)
        action(new["payload"], new["payload"]["coordinates"][index])
        refuse(label,reason,lambda:panel.audit(raw_b,panel.canonical(new)))

    changed("well-formed incorrect reduced product","exact product",
            lambda p,x:x.update(product={"schema":panel.IDS["product_schema"],"numerator":"2","denominator":"1"}))
    changed("wrong sign","exact sign",lambda p,x:x.update(sign="negative"))
    changed("too-wide interval","interval width/order",
            lambda p,x:x["interval"].update(lower=panel.dyadic(Fraction(-1)), upper=panel.dyadic(Fraction(1))))
    q = Fraction(int(records[idx]["numerator"]),int(records[idx]["denominator"]))
    lo, hi = panel.A.log_interval(q,total,256)
    panel.need(lo < hi, "nontrivial overlap control")
    # [lo,lo] touches the independently produced enclosure without containing it.
    changed("overlap only","independent interval containment",
            lambda p,x:x["interval"].update(lower=panel.dyadic(lo),upper=panel.dyadic(lo)))
    changed("negative zero coefficient","panel dyadic representation",
            lambda p,x:x["interval"].update(lower={"coefficient":"-0","exponent":0}),idx0)
    changed("nonnormal zero exponent","dyadic normalization",
            lambda p,x:x["interval"].update(lower={"coefficient":"0","exponent":1}),idx0)
    changed("wrong named key","coordinate identity",lambda p,x:x.update(key="07"))
    changed("swapped coordinate records","coordinate identity",
            lambda p,x:p["coordinates"].__setitem__(slice(0,2),reversed(p["coordinates"][:2])))
    changed("missing coordinate","coordinate count",lambda p,x:p["coordinates"].pop())
    changed("duplicated coordinate","coordinate identity",
            lambda p,x:p["coordinates"].__setitem__(0,p["coordinates"][1]))
    changed("changed binding","coordinate bindings",lambda p,x:x["bindings"].update(source_manifest_sha256="0"*64))
    changed("changed planned bound","resource event_comparisons",lambda p,x:p["resources"].update(event_comparisons=1))
    changed("out-of-scope report field","coordinate fields",lambda p,x:x.update(verified=True))
    bad = deepcopy(b)
    bad["rows"].append(bad["rows"][-1])
    refuse("duplicate input row","row-order-or-duplicate",lambda:panel.audit(panel.canonical(bad),raw_c))
    bad = deepcopy(b)
    bad["rows"].pop()
    refuse("missing input row","resource aggregate_projected_product_bits",lambda:panel.audit(panel.canonical(bad),raw_c))
    dup = raw_b.replace(b'"sources":3',b'"sources":3,"sources":3')
    refuse("duplicate JSON member","duplicate JSON member",lambda:panel.audit(dup,raw_c))
    return {"synthetic_positive_coordinates":len(records), "refusals":results, "refusal_count":len(results)}


if __name__ == "__main__":
    try:
        sys.stdout.buffer.write(panel.canonical(run()))
    except (ValueError, OSError) as error:
        raise SystemExit("control failed: " + str(error)) from None
