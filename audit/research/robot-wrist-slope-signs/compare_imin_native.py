"""Compare the two original stable Rust bindings with the five exact counted robot tables."""
from argparse import ArgumentParser
from decimal import Decimal
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from compare_imin import CERTIFICATE, FIELDS, SUMMARY, input_counts, read_original, reference, require


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--binding-root", type=Path, help="use a particular extracted pid_core_rs wheel")
    args = parser.parse_args()
    if args.binding_root is not None:
        sys.path.insert(0, str(args.binding_root.resolve()))
    import numpy as np
    import pid_core_rs as pid

    if args.binding_root is not None:
        require(Path(pid.__file__).resolve().is_relative_to(args.binding_root.resolve()), "selected wheel")
    panel, _ = reference(HERE)
    supplied = read_original(HERE / "certificate.json", CERTIFICATE)
    original = read_original(HERE / "results.json", SUMMARY)
    require(panel == json.loads((HERE / "imin-comparison.json").read_bytes()), "entire independent product record")
    atoms = ("redundancy", "unique_s1", "unique_s2", "synergy")
    mis = ("mi_s1_t_nats", "mi_s2_t_nats", "mi_s1s2_t_nats")
    compared = 0
    for table, expected, meta in zip(supplied["tasks"], panel["tasks"], original["tasks"], strict=True):
        require(table["id"] == expected["id"] == meta["id"], "task identity")
        counts = input_counts(table["counts"], len(meta["label_order"]), meta["n"])
        rows = [key for key, count in counts.items() for _ in range(count)]
        cols = [np.asarray(col, dtype=np.int64).reshape(-1, 1) for col in zip(*rows)]
        imin = pid.compute_categorical_imin_pid2(*cols)
        mgw = pid.compute_categorical_sxpid2(*cols)
        require(imin.empirical_pmf.sample_count == mgw.empirical_pmf.sample_count == len(rows), "native observations")
        require(imin.empirical_pmf.observed_joint_states == mgw.empirical_pmf.observed_joint_states == len(counts), "native occupied keys")
        calculated = {
            "imin_nats": [getattr(imin, k + "_nats") for k in atoms] + [getattr(imin, k) for k in mis],
            "mgw_nats": [getattr(mgw, k).net_nats for k in atoms] + [getattr(mgw, k) for k in mis],
        }
        for method, values in calculated.items():
            for field, val in zip(FIELDS, values, strict=True):
                require(math.isfinite(val), "nonfinite native result")
                error = abs(Decimal(expected[method][field]) - Decimal.from_float(val))
                require(error <= Decimal("2e-12"), table["id"] + " " + method + " " + field)
                compared += 1
    require(compared == 70, "complete source and atom field count")
    print("PASS 70 empirical atom and mutual information values from two stable Rust functions on all five original robot tasks")


if __name__ == "__main__":
    main()
