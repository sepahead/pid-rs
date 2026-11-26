"""Recompute the recorded support and all exact categorical products from the original UCI ZIP."""

import argparse
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
AUDIT = runpy.run_path(str(HERE / "audit_results.py"))
CHECKED = HERE / "checked"
READERS = (
    ("support", "source_counts.py", "e2ef22b35518fa1b051c4a2b71d506b7321c405c8f0958077e261ad38aa8e229"),
    ("lattice", "check_lattice.py", "c8483911e40c69292258f55c91e0223721db35cf0c939769dbb8fe00a7f61e37"),
)
ZIP_HASH = "cdfbe0b260f4a21c5249fe0da4b1baf4041959663a9182253885ee1f41a4568e"


def run_reader(program, archive):
    flags = ["-I", "-S", "-B"]
    if sys.flags.optimize:
        flags.append("-O")
    return subprocess.run(
        [sys.executable, *flags, str(HERE / program), str(archive)],
        capture_output=True,
        timeout=60,
        check=False,
    )


def reject_changed_field(baseline, side, path, replacement, diagnostic):
    altered = deepcopy(baseline)
    branch = altered[side]
    for key in path[:-1]:
        branch = branch[key]
    branch[path[-1]] = replacement
    try:
        AUDIT["checked_samples"](*altered)
    except ValueError as exc:
        if str(exc) == diagnostic:
            return
        raise ValueError(f"unexpected refusal for {path}: {exc}") from exc
    raise ValueError(f"accepted changed field {path}")


def adverse_cases(support_file, lattice_file, archive, work):
    with support_file.open() as data:
        supported = json.load(data)
    with lattice_file.open() as data:
        checked = json.load(data)
    full = checked["scientific_result"]
    originals = [supported, checked]
    all_zero = dict.fromkeys(supported["five_signed_products"], "1")
    swapped = dict(supported["five_signed_products"])
    swapped["04"], swapped["05"] = swapped["05"], swapped["04"]
    cases = [
        ("replace five with zero", 0, ["five_signed_products"], all_zero,
         "five named products with correct orientations"),
        ("exchange opposite signs", 0, ["five_signed_products"], swapped,
         "five named products with correct orientations"),
        ("change a positive count", 0, ["cells", 1, "count"], 23, "empirical sign table or margins"),
        ("accept a Boolean as a count", 0, ["cells", 1, "count"], True, "empirical sign table or margins"),
        ("remove positive cell", 0, ["cells"], supported["cells"][:-1], "four occupied cells"),
        ("treat a flat trend as observed", 0, ["count_matrix_negative_zero_positive", 1, 1], 1,
         "zero slope rows and columns"),
        ("wrong support decision", 0, ["cells", 0, "shares_both"], False,
         "occupied row and column support factor"),
        ("drop count powers", 0, ["individual_positive_rational"], "231/208", "positive Q"),
        ("use signed sum as absolute mass", 1, ["scientific_result", "absolute_product"], "1",
         "sum versus absolute sum"),
        ("store rounded magnitude as exact", 0, ["single_magnitude_nats_rounded"], "0.244337",
         "reported rounded nats"),
        ("substitute a cumulative for its atom", 1, ["scientific_result", "all108", "05", "signed", "atom"],
         full["all108"]["05"]["signed"]["cumulative"], "positive component quotient"),
        ("drop a component", 1, ["scientific_result", "all108", "07"],
         {"signed": full["all108"]["07"]["signed"]}, "component identities"),
    ]
    for _, side, path, replacement, diagnostic in cases:
        reject_changed_field(originals, side, path, replacement, diagnostic)
    # This change leaves every plotted count, every positive quotient and all five named
    # atoms intact. The complete result binding must still reject the different record.
    extra = deepcopy(checked)
    other = extra["scientific_result"]["all108"]["01"]
    for role in ("cumulative", "atom"):
        for channel in ("informative", "misinformative"):
            other[channel][role] = str(Fraction(other[channel][role]) * 2)
    AUDIT["checked_samples"](supported, extra)
    alternate = work / "different-hidden-output.json"
    alternate.write_text(json.dumps(extra, sort_keys=True))
    try:
        AUDIT["load_checked"](support_file, alternate)
    except ValueError as exc:
        if str(exc) != "complete original checked records":
            raise
    else:
        raise ValueError("accepted altered hidden coordinates")
    changed_donor = work / "changed.zip"
    raw = bytearray(archive.read_bytes())
    raw[0] ^= 1
    changed_donor.write_bytes(raw)
    for _, script, _ in READERS:
        refused = run_reader(script, changed_donor)
        if refused.returncode == 0 or refused.stdout or b"ValueError" not in refused.stderr:
            raise ValueError(f"{script} did not refuse the altered original archive")
    return [record[0] for record in cases] + [
        "change unplotted exact coordinates",
        "alter original donor bytes for the support reader",
        "alter original donor bytes for the full event reader",
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="original Robot Execution Failures ZIP from UCI")
    parser.add_argument("--self-test", action="store_true", help="also exercise value, role and source refusals")
    args = parser.parse_args()
    mode = "optimized" if sys.flags.optimize else "ordinary"
    archive = args.archive.resolve()
    if archive.stat().st_size != 59365 or sha256(archive.read_bytes()).hexdigest() != ZIP_HASH:
        raise ValueError("expected the original 59,365-byte UCI ZIP")
    with tempfile.TemporaryDirectory(prefix="lp4-copied-target-") as tmp:
        work = Path(tmp)
        results = []
        for role, program, expected_program in READERS:
            if sha256((HERE / program).read_bytes()).hexdigest() != expected_program:
                raise ValueError(f"unexpected original {role} reader")
            execution = run_reader(program, archive)
            if execution.returncode or execution.stderr:
                raise ValueError(f"{role} failed: {execution.stderr.decode(errors='replace')}")
            if execution.stdout != (CHECKED / f"{role}-{mode}.json").read_bytes():
                raise ValueError(f"complete {role} output differs")
            output = work / f"{role}.json"
            output.write_bytes(execution.stdout)
            results.append(output)
        summary = AUDIT["load_checked"](*results)
        returned = {
            "source_zip_sha256": ZIP_HASH,
            "support_output_sha256": AUDIT["SUPPORT_HASH"],
            "lattice_output_sha256": AUDIT["LATTICE_HASH"],
            "exact_categorical_coordinates": 108,
            "episode_count": summary["episodes"],
            "nonzero_added_source_signed_means": 2,
            "absolute_mass_nats_per_episode": summary["sum_absolute_signed_means_nats"],
        }
        if args.self_test:
            returned["rejected_controls"] = adverse_cases(*results, archive, work)
        print(json.dumps(returned, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
