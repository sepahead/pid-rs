"""Read back the archived public API reports against the exact represented-input reference."""
from collections import Counter
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1] / "research/normalized-shannon-ratios"
STAGES = {
    "original": ("0f3122a96e48a099581ad4faf3e3d5d9138367f6",
                 "9a7c35edf9748bf45602b02a32dc71fc38b710d878f0f6e9534fc8b961b9dc74",
                 "baseline", 101),
    "corrected": ("03325745f64becf437b9b3042b51a9d925450579",
                  "8d252784872fb8c5b8af9cee363ca924275f8d51317436ec09e69615f0164352",
                  "fixed", 0),
}


def main():
    spec = importlib.util.spec_from_file_location("shannon_ratio_judge", PACKAGE / "judge.py")
    judge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(judge)
    receipt = judge.strict_json((HERE / "receipt.json").read_bytes())
    fixture, identity = judge.checked_fixture()
    if identity != receipt["fixture_sha256"] or set(receipt["observed"]) != set(STAGES):
        raise ValueError("archived fixture or result roster changed")
    for stage, (commit, digest, mode, cargo_exit) in STAGES.items():
        name = stage + ".json"
        raw = (HERE / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(f"archived native output changed for {stage}")
        differences = judge.compare(judge.strict_json(raw), fixture, identity)
        judge.verdict(differences, mode)
        fields = Counter(field for row in differences.values() for field in row)
        measured = {
            "file": name, "source_commit": commit, "observation_sha256": digest,
            "scored_rows": len(fixture["rows"]), "differing_rows": len(differences),
            "differing_fields": dict(fields), "cargo_exit": cargo_exit, "old_regressions": 16,
        }
        if receipt["observed"][stage] != measured:
            raise ValueError(f"native report summary differs for {stage}")
        print(f"{stage}: {len(differences)} differing rows out of {len(fixture['rows'])}")


if __name__ == "__main__":
    main()
