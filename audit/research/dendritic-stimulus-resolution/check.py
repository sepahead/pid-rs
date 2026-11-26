"""Recompute the finite study and check results, damaged reports, and recorded Rust output."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import runpy
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RUST = HERE / "rust-comparison"
DATA_SHA = "718e40b0509f077d8d667187c22d3fe7df7746f5489dc40bd983742a4bcbb467"
RAW_URL = ("https://raw.githubusercontent.com/ModelDBRepository/180373/"
           "655ac03999ecb5ce2b15f3b04cee4c250358a2ff/data/spikes_.dat")
EXPECTED = {"products-and-predictions.json":
            "c4cff8933d60c93e52dc501fc2a2bdc48433443da10f3e73875761a53e247ae1",
            "results.json":"274bbc92cb6662b8a033f896566eac3f0e2688b6739be494402165bea699f1d9",
            "analyze.py":"36ddf15ab089149c38aec544c6a872eab924df3226db95dec256b5e255b084b9",
            "arithmetic.py":"b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2"}


def need(ok, name):
    if not ok:
        raise ValueError(name)


def raw_grid(data):
    need(len(data) == 5890 and sha256(data).hexdigest() == DATA_SHA, "original count file")
    return data


def restore_classes(detailed):
    # This recovers the recorded target classes and setting identities only.
    levels = detailed["10"]["withheld"]["basal"]
    need(len(levels) == 651, "number of recorded class labels")
    lines = []
    for i in range(31):
        tokens = []
        for j in range(21):
            row = levels[21*i + j]
            need(type(row) is list and len(row) == 9
                 and all(type(v) is int for v in row) and row[:2] == [10*i, 10*j]
                 and row[2] in (0,1,2), "class location")
            tokens.append(("%d.0000" % (0,1,3)[row[2]]).encode("ascii"))
        lines.append(b" ".join(tokens))
    return b"\n".join(lines) + b"\n"


def compare_records(observed, original):
    # The strict JSON representation preserves integer/boolean distinctions.
    def encode(v):
        return json.dumps(v, sort_keys=True, ensure_ascii=True, allow_nan=False,
                          separators=(",",":"))
    need(encode(observed) == encode(original), "all atom, forecast and count records")


def compare_summaries(observed, original):
    # These summary decimals use platform libm. Exact records receive a separate comparison.
    if type(original) is dict:
        need(type(observed) is dict and set(observed) == set(original), "summary fields")
        for k, v in original.items():
            compare_summaries(observed[k], v)
    elif type(original) is list:
        need(type(observed) is list and len(observed) == len(original), "summary sequence")
        for x, y in zip(observed, original, strict=True):
            compare_summaries(x, y)
    elif type(original) is float:
        need(type(observed) in (int, float) and math.isfinite(observed)
             and abs(observed - original) <= 1e-12, "summary decimal")
    else:
        need(type(observed) is type(original) and observed == original, "summary integer or string")


def adverse(detailed, math_controls, rows, native, targets):
    result = []
    def refusal(name, function):
        try:
            function()
        except (ValueError, TypeError, KeyError):
            result.append(name)
        else:
            raise ValueError("input mutation accepted: " + name)
    def change(name, function):
        manipulated = deepcopy(detailed)
        function(manipulated)
        refusal(name, lambda:compare_records(manipulated, detailed))

    change("unit product replaced by its false value", lambda x:x["10"]["signed"].__setitem__(
        x["10"]["keys"].index("04"),["2","1"]))
    change("nonunit flag singleton inverted", lambda x:x["100"]["signed"][
        x["100"]["keys"].index("04")].reverse())
    change("shift one held basal probability count", lambda x:x["100"]["withheld"]["basal"][0].__setitem__(
        4, x["100"]["withheld"]["basal"][0][4]+1))
    change("boolean substituted for a numerical coordinate",lambda x:x["10"]["withheld"]["tuft"][0].__setitem__(0,False))
    change("omit one saturated range pair",lambda x:x["50"]["groups"].pop())
    change("exchange an I_min and MGW signed term",lambda x:x["100"]["imin"].__setitem__(
        x["100"]["keys"].index("04"),x["100"]["signed"][x["100"]["keys"].index("04")]))
    refusal("modified original donor word",lambda:raw_grid(b"0"))
    wrong_summary = {"gain":0.2}
    refusal("changed summary decimal",lambda:compare_summaries(wrong_summary, {"gain":0.19}))
    rust = runpy.run_path(str(RUST/"controls.py"))["exercise"](math_controls, rows, rows, native, targets)
    return {"exact_and_forecast":result,"recorded_rust":rust}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data",type=Path,help="use the exact published spike-count file")
    parser.add_argument("--self-test",action="store_true",help="exercise adverse reports and data")
    parser.add_argument("--fetch",type=Path,help="write the versioned external data to a new path")
    args = parser.parse_args()
    if args.fetch:
        from urllib.request import urlopen
        with urlopen(RAW_URL, timeout=30) as response:
            data = raw_grid(response.read(5891))
        with args.fetch.open("xb") as output:
            output.write(data)
        print(DATA_SHA)
        return
    for basename, digest in EXPECTED.items():
        need(sha256((HERE/basename).read_bytes()).hexdigest()==digest, "original source or output "+basename)
    c = runpy.run_path(str(RUST/"compare.py"))
    math_module = runpy.run_path(str(HERE/"arithmetic.py"))
    ref = runpy.run_path(str(HERE/"reference.py"))
    detailed = c["load_json"]((HERE/"products-and-predictions.json").read_bytes())
    brief = c["load_json"]((HERE/"results.json").read_bytes())["widths"]
    grid = raw_grid(args.data.read_bytes()) if args.data else restore_classes(detailed)
    readings = ref["parse"](grid)
    argv = [sys.executable,"-I","-S","-B"] + ([] if __debug__ else ["-O"]) + [str(HERE/"analyze.py")]
    out = subprocess.run(argv, input=grid, capture_output=True, timeout=90, check=True)
    need(not out.stderr, "calculation stderr")
    compare_records(c["load_json"](out.stdout), detailed)
    for width in (10,50,100):
        obs, summary = ref["reference"](readings,width,math_module)
        compare_records(obs,detailed[str(width)])
        summary["target_counts"] = {str(k):val for k,val in summary["target_counts"].items()}
        compare_summaries(summary,brief[str(width)])
    rows = c["expected_rows"](grid)
    targets = c["build_targets"](detailed, math_module["log_interval"])
    for name, expected_sha in (("returned-rust.json",
             "3071e5ee948b07d36d2266b943138a96841f232c028dee4fb2021e3ffbea788b"),("result.json",
             "c8d11e3b5b765f09c8fae87d543c3a34e52a4f2954e474da9a576ef0e31425be")):
        need(sha256((RUST/name).read_bytes()).hexdigest() == expected_sha, "original Rust receipt " + name)
    native = c["load_json"]((RUST/"returned-rust.json").read_bytes())
    native_result = c["check"](native, rows, targets)
    original = c["load_json"]((RUST/"result.json").read_bytes())
    for key in ("summary","returned_key_order","output_coordinates","absolute_tolerance_nats"):
        if key == "summary":
            compare_summaries(native_result[key], original[key])
        else:
            compare_records(native_result[key], original[key])
    controls = adverse(detailed,c,rows,native,targets) if args.self_test else {}
    result = {"input": "original published spike counts" if args.data else "stored setting identities and response classes",
              "rows":651,"widths":[10,50,100],"exact_products":216,"stored_Rust_coordinates":216,
              "complete_forecast_records":3906,"native_execution":"use rust-comparison/replay.py for a new native build and execution",
              "exact_and_forecast_mutations_refused":len(controls.get("exact_and_forecast",[])),
              "recorded_Rust_mutations_refused":len(controls.get("recorded_rust",{}).get("rejections",{}))}
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__ == "__main__":
    main()
