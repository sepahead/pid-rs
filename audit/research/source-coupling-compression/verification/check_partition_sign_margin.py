"""Check the full-source information margin on the thirty archived categorical laws.

The sign rows describe the historical real-valued optimization model. This program
uses only its two inequalities and the saved rational information enclosures.
"""

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys


REPORT_SHA256 = "ad0f9781265c7bdf3a9eadae04c063428e4507f946644d0cbbc42b240521bc2b"
SIGNED_COORDINATES = ("-5/2", "-1", "-1/3", "0", "1/3", "1", "5/2")
SIGN_CONSTANTS = ("0", "1/2", "2/3", "1", "2", "3", "5")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def enclosure(record):
    endpoints = record["interval"]
    require(isinstance(endpoints, list) and len(endpoints) == 2, "invalid interval")
    require(all(isinstance(value, str) for value in endpoints), "non-string endpoint")
    lower, upper = map(Fraction, endpoints)
    require(lower <= upper, "reversed interval")
    return lower, upper


def law_margin(campaign, pointer):
    relative = Path(pointer["path"])
    require(relative.parent == Path("laws") and relative.suffix == ".json", "invalid law path")
    raw = (campaign / relative).read_bytes()
    digest = sha256(raw).hexdigest()
    require(len(raw) == pointer["bytes"] and digest == pointer["sha256"], "law identity mismatch")
    law = json.loads(raw, parse_float=str)
    top, = (row for row in law["coordinates"]
            if row["branches"] == [7] and row["stage"] == "cumulative" and row["component"] == "net")
    old_lower, old_upper = enclosure(top["before"])
    new_lower, new_upper = enclosure(top["after"])
    lower, upper = old_lower - new_upper, old_upper - new_lower
    direct, = (row for row in law["mi_changes"] if row["source_mask"] == 7)
    direct_lower, direct_upper = enclosure(direct["change"])
    require(max(lower, direct_lower) <= min(upper, direct_upper), "disjoint information intervals")
    max_abs = max(abs(lower), abs(upper))
    require(max_abs <= 1, "one-nat margin not certified")
    return {"path": pointer["path"], "sha256": digest, "lower": str(lower),
            "upper": str(upper), "max_abs": str(max_abs)}


def sign_cases():
    rows = []
    for coordinate in SIGNED_COORDINATES:
        d = Fraction(coordinate)
        t = abs(d)
        for constant in SIGN_CONSTANTS:
            m = Fraction(constant)
            branches = [z for z in (0, 1) if -d + t + m * z <= m and d + t - m * z <= 0]
            rows.append({"d": coordinate, "M": constant, "branches": branches})
    return rows


def main():
    require(len(sys.argv) == 2, "expected one absolute campaign directory")
    campaign = Path(sys.argv[1])
    require(campaign.is_absolute(), "campaign path must be absolute")
    raw = (campaign / "REPORT.json").read_bytes()
    require(sha256(raw).hexdigest() == REPORT_SHA256, "campaign identity mismatch")
    report = json.loads(raw)
    laws = [law_margin(campaign, pointer)
            for recording in report["recordings"] for pointer in recording["laws"]]
    require(len(laws) == len({law["path"] for law in laws}) == 30, "invalid roster")
    print(json.dumps({"laws": laws, "branches": sign_cases()}, separators=(",", ":")))


if __name__ == "__main__":
    main()
