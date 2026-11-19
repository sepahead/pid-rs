"""Finite observation checker and failure ledger. Production CLI is capture.py, constrained by a root admission."""
import importlib.util
import json
import math
import re
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
def load_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
hist = load_path("copy_historical_arithmetic", HERE / "historical/check.py")
seed = load_path("copy_schedule", HERE / "seed_oracle.py")

CONFIG = {"n":4, "replicates":200, "block_size":1, "seed":7, "alpha_bits":"3fa999999999999a",
          "algorithm_revision":"V1","dependence":"IndependentExchangeableRows","block_length_selection":"FixedAPriori"}
PROVENANCE = {"original_row_count":4,"requested_replicates":200,"block_size":1,"seed":7,
              "algorithm_revision":"V1","dependence":"IndependentExchangeableRows","block_length_selection":"FixedAPriori"}
ERROR_NAMES = frozenset(("ShapeMismatch InvalidConfig RowCountMismatch SourceDimensionMismatch InvalidK NonFiniteInput "
    "SupportContractRequired UnsupportedSupportContract ObservedContinuousSampleIncompatibility NumericalInstability "
    "ResourceLimitExceeded AllocationFailed SizeOverflow QuantizerOutOfRange SampleCountPrecisionExceeded "
    "ParallelExecutionFailed Cancelled AmbiguousKthNeighborShell NotImplemented").split())
def need(condition, message):
    if not condition:
        raise ValueError(message)
def keys(x, names, where):
    need(type(x) is dict and set(x) == set(names), where + ": wrong fields")
def equal_record(x, expected, where):
    keys(x,expected,where)
    for k,v in expected.items():
        need(type(x[k]) is type(v) and x[k] == v, where + ": " + k)
def check_error(error):
    need(type(error) is str and 0 < len(error) <= 4096, "typed error size or primitive")
    m = re.fullmatch(r"([A-Za-z][A-Za-z0-9]*) \{ [^\x00-\x1f]+ \}", error)
    need(m is not None and m.group(1) in ERROR_NAMES, "unknown or malformed Rust PidError debug record")
    return error
def encode(value):
    return struct.pack(">d",value).hex()
def summary_rank(values, summary):
    keys(summary, ("mean_bits","std_bits","lower_bits","upper_bits"),"summary")
    for name in summary: hist.bits(summary[name])
    need(hist.bits(summary["std_bits"])[1] >= 0,"negative reported sample spread")
    ordered = sorted(values,key=hist.total_key)
    need(summary["lower_bits"] == ordered[5] and summary["upper_bits"] == ordered[194],"observed raw percentile ranks")
def unpack_call(call, where):
    need(type(call) is dict,where + ": expected call")
    if call.get("kind") == "error":
        keys(call,("kind","error_debug"),where)
        return None, [check_error(call["error_debug"])]
    keys(call,("kind","provenance","point_bits","summary","replicates"),where)
    need(call["kind"] == "report",where + ": unknown call kind")
    equal_record(call["provenance"], PROVENANCE,where + " provenance")
    hist.bits(call["point_bits"])
    reps = call["replicates"]
    need(type(reps) is list and len(reps)==200, where + ": complete indexed replicate vector")
    values, failures = [], []
    for idx,rep in enumerate(reps):
        need(type(rep) is dict and type(rep.get("index")) is int and rep["index"] == idx,where + ": replicate index")
        if "value_bits" in rep:
            keys(rep,("index","value_bits"),where + " replicate")
            hist.bits(rep["value_bits"]); values.append(rep["value_bits"])
        else:
            keys(rep,("index","error_debug"),where + " failed replicate")
            failures.append(check_error(rep["error_debug"])); values.append(None)
    if failures:
        need(call["summary"] is None,where + ": failed replicate forbids summary")
    else:
        summary_rank(values,call["summary"])
    return values,failures

def balanced_indicator(mask, codes):
    hist.integer(mask)
    need(0<=mask<16,"mask domain")
    need(len(codes)==200,"classifier schedule length")
    balanced=0
    for code in codes:
        one_count=sum((mask >> ((code >> shift) & 3)) & 1 for shift in (6,4,2,0))
        balanced += one_count==2
    return 6 <= balanced <= 194

def inspect(raw, expected_codes, *, synthetic=False):
    need(type(raw) is bytes and len(raw)<=1048576,"observation byte cap")
    need(synthetic or expected_codes==seed.index_codes(),"production expected schedule provenance")
    obs=hist.strict(raw)
    keys(obs,("schema","configuration","schedule","rows"),"observation")
    need(obs["schema"]=="pid-copy-bootstrap-observation-v2","observation schema")
    equal_record(obs["configuration"],CONFIG,"configuration")
    schedule,probe_errors=unpack_call(obs["schedule"],"schedule probe")
    if schedule is not None:
        need(obs["schedule"]["point_bits"]==encode(27),"index observer point identity")
        for i, x in enumerate(schedule):
            if x is not None:
                val=hist.bits(x)[1]
                need(val.is_integer() and 0<=val<=255 and x==encode(int(val)),"schedule probe exact code")
                need(int(val)==expected_codes[i],"seed-7 schedule mismatch at replicate " + str(i))
    rows=obs["rows"]
    need(type(rows) is list and len(rows)==16,"complete ordered outer space")
    old_rows=[];error_masks=[];cancelled_masks=[];replicate_errors=0
    for mask,row in enumerate(rows):
        keys(row,("mask","outcome"),"row")
        hist.integer(row["mask"],mask)
        call=row["outcome"]; vals,errors=unpack_call(call,"outer mask " + str(mask))
        if errors:
            error_masks.append(mask)
            if any(error.startswith("Cancelled {") for error in errors):cancelled_masks.append(mask)
            if vals is not None:replicate_errors+=len(errors)
            continue
        old_rows.append({"mask":mask,"point_bits":call["point_bits"],
            "lower_bits":call["summary"]["lower_bits"],"upper_bits":call["summary"]["upper_bits"],
            "replicate_bits":vals})
    failure_weight=sum(2**(4-m.bit_count()) for m in error_masks)
    outcome={"scope":"synthetic control" if synthetic else "authenticated fixed-seed finite production observation",
        "mask_count":16,"failed_masks":error_masks,"typed_api_failure_mass":{"numerator":failure_weight,"denominator":81},
        "failed_returned_categorical_replicates":replicate_errors,"schedule_probe_error_count":len(probe_errors),
        "masks_with_typed_cancellation":cancelled_masks,"typed_cancellation_mass":{"numerator":sum(2**(4-m.bit_count()) for m in cancelled_masks),"denominator":81},
        "coverage":None,"historical_projection":None}
    if probe_errors or error_masks:
        outcome["status"]="TYPED_FAILURE_NO_POINT_COVERAGE"
        return outcome
    old_config={k:CONFIG[k] for k in ("n","replicates","block_size","seed","algorithm_revision","alpha_bits")}
    projection={"schema":"pid-copy-bootstrap-calibration-v1","configuration":old_config,
                "schedule_codes":expected_codes,"rows":old_rows}
    raw_projection=json.dumps(projection,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    judgment=hist.judge(raw_projection)
    for row in judgment["rows"]:
        need(balanced_indicator(row["mask"],expected_codes)==row["covered"],"independent integer classifier disagreement")
    outcome.update(status="COMPLETE_FIXED_OBSERVATION",coverage=judgment["coverage"],historical_projection=judgment,
                   projection_sha256=judgment["input_sha256"])
    return outcome

