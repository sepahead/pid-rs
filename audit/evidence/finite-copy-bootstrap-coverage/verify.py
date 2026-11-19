"""Recheck one recorded finite study using the original arithmetic and a separate count table."""
import argparse
import hashlib
import importlib.util
import json
import struct
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def require(value, message):
    if not value:
        raise ValueError(message)


def read_exact(path, identity):
    with path.open("rb") as stream:
        data = stream.read(identity["bytes"] + 1)
    require(len(data) == identity["bytes"], f"{path.name}: byte count differs")
    require(hashlib.sha256(data).hexdigest() == identity["sha256"], f"{path.name}: SHA-256 differs")
    return data


def load_original_judge():
    source = ROOT / "judge" / "observation.py"
    spec = importlib.util.spec_from_file_location("copy_observation", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def balance_table(observation):
    # Decode into indicator counts per tuple first; do not reuse the original classifier.
    schedule = []
    for rep in observation["schedule"]["replicates"]:
        encoded = int(struct.unpack(">d", bytes.fromhex(rep["value_bits"]))[0])
        counts = [0] * 4
        for shift in (0, 2, 4, 6):
            counts[(encoded >> shift) & 3] += 1
        schedule.append(counts)
    result = []
    for mask in range(16):
        labels = [(mask >> bit) & 1 for bit in range(4)]
        balanced = sum(sum(count * bit for count, bit in zip(counts, labels)) == 2
                       for counts in schedule)
        result.append({"mask": mask, "weight_numerator": 2 ** (4 - sum(labels)),
                       "balanced_replicates": balanced, "contains_target": 6 <= balanced <= 194})
    return result


def check(path):
    record = json.loads((ROOT / "record.json").read_bytes())
    require(record["schema"] == "pid-rs-finite-copy-bootstrap-public-record-v1", "record schema")
    for name, identity in record["files"].items():
        read_exact(ROOT / name, identity)
    raw = read_exact(path, record["files"]["observation.json"])
    judge = load_original_judge()
    observed = judge.hist.strict(raw)
    expected_schedule = judge.seed.index_codes()
    schedule_digest = hashlib.sha256(bytes(expected_schedule)).hexdigest()
    require(schedule_digest == record["run"]["qualified_schedule_packed_sha256"], "schedule identity")
    judgment = judge.inspect(raw, expected_schedule)
    stored = judge.hist.strict((ROOT / "judgment.json").read_bytes())
    require(stored["raw_sha256"] == hashlib.sha256(raw).hexdigest() and stored["result"] == judgment,
            "original arithmetic judgment differs")
    require(judgment["status"] == "COMPLETE_FIXED_OBSERVATION", "incomplete study")
    rows = balance_table(observed)
    arithmetic = judgment["historical_projection"]["rows"]
    for row, old in zip(rows, arithmetic):
        require((row["mask"], row["weight_numerator"], row["contains_target"])
                == (old["mask"], old["probability_numerator"], old["covered"]),
                f"independent classification differs for mask {row['mask']}")
    total = sum(row["weight_numerator"] for row in rows)
    covered = sum(row["weight_numerator"] for row in rows if row["contains_target"])
    require(total == 81 and Fraction(covered, total) == Fraction(64, 81), "finite coverage differs")
    require(judgment["typed_api_failure_mass"] == {"numerator": 0, "denominator": 81}, "error mass")
    require(record["coverage"] == judgment["coverage"], "recorded coverage")
    return {"coverage": str(Fraction(covered, total)), "noncoverage": str(Fraction(total - covered, total)),
            "failed_api_mass": "0/81", "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation", type=Path, default=ROOT / "observation.json",
                        help="compare an independent build's complete raw output with this recording")
    print(json.dumps(check(parser.parse_args().observation), indent=2))
