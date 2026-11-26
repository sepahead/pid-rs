"""Exercise the frozen binary64 comparison on actual LP4 native reports."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

path = Path(__file__).with_name("compare.py")
spec = importlib.util.spec_from_file_location("lp4_comparison", path)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def rejected(fn):
    try:
        fn()
    except ValueError as exc:
        return str(exc)
    raise ValueError("a required contrary input was accepted")


def main():
    actual = c.strict_load(Path(sys.argv[1]).read_bytes())
    rows = c.rows_from_original(Path(sys.argv[2]))
    c.compare(actual)
    results = {}
    def changed(label, change):
        altered = copy.deepcopy(actual)
        change(altered)
        results[label] = rejected(lambda: c.compare(altered))
    def find(z, method, masks):
        return next(x for x in z[method]["atoms"] if x["masks"] == masks)
    def sign(z):
        row = find(z, "mgw", [4])
        row["signed"] = f'{int(row["signed"],16) ^ (1<<63):016x}'
    def exchange_masks(z):
        for method in z.values():
            for atom in method["atoms"]:
                atom["masks"] = sorted(((v & 1)<<2) | (v & 2) | ((v & 4)>>2) for v in atom["masks"])
    changed("reverse_MGW_04_sign", sign)
    changed("exchange_source_1_and_3_masks_on_both_reports", exchange_masks)
    changed("erase_MGW_05", lambda z: find(z, "mgw", [5]).update(signed="0000000000000000"))
    changed("replace_imin_06_by_one", lambda z: find(z, "imin", [6]).update(imin="3ff0000000000000"))
    changed("nonfinite_imin_07", lambda z: find(z, "imin", [7]).update(imin="7ff8000000000000"))
    changed("missing_MGW_05_06", lambda z: z["mgw"]["atoms"].remove(find(z, "mgw", [5,6])))
    for name, wrong in (
        ("archive_force_and_torque_swapped", [[w,0,x,w] for x,_,w,t in rows]),
        ("archive_sign_code_reversed", [[1-x,0,1-w,1-t] for x,_,w,t in rows]),
        ("donor_as_target", [[x,0,w,1-t] for x,_,w,t in rows])):
        results[name] = rejected(lambda: c.validate_rows(wrong,rows))
    print(json.dumps(results, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
