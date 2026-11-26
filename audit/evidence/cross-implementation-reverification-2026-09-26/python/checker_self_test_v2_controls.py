"""Check that the dated hostile-input harness rejects false success and failure reports.

Run with plain or optimized Python. These synthetic controls exercise the harness.
Use checker_self_test_v2.py to run the two independent numerical programs.
"""
import json
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent
H = runpy.run_path(str(HERE / "checker_self_test_v2.py"))
inspect = H["inspect_result"]
Failure = H["CheckFailure"]


def result(code, stdout="", stderr=""):
    return subprocess.CompletedProcess(["synthetic transcript"], code, stdout, stderr)


def main():
    cases = json.loads((EVIDENCE / "inputs/continuous_dump.json").read_bytes())
    categorical = (EVIDENCE / "results/check_discrete.txt").read_text()
    continuous = (EVIDENCE / "results/check_continuous.txt").read_text()
    inspect(result(0, categorical), "discrete", cases)
    inspect(result(0, continuous), "continuous", cases)
    note = "expected exactly 60 cases"
    inspect(result(1, stderr=note + "\n"), "discrete", cases, message=note)

    refused = 0

    def reject(label, observed, kind, **expected):
        nonlocal refused
        try:
            inspect(observed, kind, cases, **expected)
        except Failure:
            refused += 1
        else:
            raise RuntimeError(f"accepted changed checker response {label}")

    for code in (-9, 2, 127):
        reject(f"unavailable child {code}", result(code, stderr=note + "\n"), "discrete", message=note)
    reject("silent refusal", result(1), "discrete", message=note)
    reject("different input error", result(1, stderr="expected exactly 6 cases\n"),
           "discrete", message=note)
    reject("import failure", result(1, stderr="ModuleNotFoundError: No module named 'numpy'\n"),
           "discrete", message=note)
    reject("extra error", result(1, stderr=note + "\nRuntimeError: second error\n"),
           "discrete", message=note)
    reject("misplaced error", result(1, stdout=note + "\n"), "discrete", message=note)
    reject("silent success", result(0), "discrete")
    reject("numeric success alone", result(0, "tolerance 1e-12 nats: PASS\n"), "discrete")
    reject("missing categorical result", result(0, categorical.replace("n2_subset_mi", "spurious")),
           "discrete")
    reject("unrelated successful error stream", result(0, categorical, "warning\n"), "discrete")
    reject("large residual and success label", result(0, categorical.replace("5.551e-17", "9.999e-04")),
           "discrete")
    reject("nonfinite residual", result(0, categorical.replace("5.551e-17", "NaN")), "discrete")
    reject("wrong number of systems", result(0, categorical.replace("cases: 60", "cases: 20")),
           "discrete")
    reject("unearned failure by status", result(1, categorical), "discrete", metric="n2_plus")
    reject("wrong categorical metric", result(1, categorical.replace("PASS", "FAIL n2_plus")),
           "discrete", metric="n2_plus")
    reject("wrong continuous dimensions", result(0, continuous.replace("d=1 k=1", "d=2 k=1")),
           "continuous")
    reject("wrong target output", result(0, continuous.replace("isx=", "other=")), "continuous")
    reject("missing continuous result", result(0, "\n".join(continuous.splitlines()[1:])),
           "continuous")
    reject("wrong continuous case count", result(0, continuous.replace("cases: 6", "cases: 1")),
           "continuous")
    reject("wrong abstention count", result(0, continuous.replace("entries: 18", "entries: 17")),
           "continuous")
    reject("unmatched largest difference", result(0, continuous.replace("largest difference 8.9e-16",
                                                                          "largest difference 0.0e+00")),
           "continuous")
    reject("wrong scientific disposition", result(1, continuous.replace("PASS", "FAIL")),
           "continuous", metric="isx")
    reject("categorical output from another checker", result(0, continuous), "discrete")
    reject("continuous output from another checker", result(0, categorical), "continuous")

    layout_controls = [
        ("negative categorical zero", categorical, "0.000e+00", "-0.000e+00", "discrete"),
        ("extra categorical precision", categorical, "0.000e+00", "0.000000e+00", "discrete"),
        ("changed categorical column width", categorical, "imin2   ", "imin2  ", "discrete"),
        ("different in-tolerance categorical result", categorical, "5.551e-17", "5.550e-17", "discrete"),
        ("extra overall precision", continuous, "largest difference 8.9e-16",
         "largest difference 8.90000e-16", "continuous"),
        ("extra estimate integer zero", continuous, "I0=+0.7401", "I0=+00.7401", "continuous"),
        ("zero-padded dimension", continuous, "d=1 k=1", "d=01 k=1", "continuous"),
        ("altered indentation", continuous, "n=  60", "n= 60", "continuous"),
        ("different in-tolerance signed scalar", continuous, "ksg_s1_t=-5.6e-17",
         "ksg_s1_t=5.6e-17", "continuous"),
    ]
    for name, original, good, bad, kind in layout_controls:
        if good not in original:
            raise RuntimeError(f"missing original field for {name}")
        reject(name, result(0, original.replace(good, bad, 1)), kind)
    reject("missing terminal newline", result(0, categorical.rstrip("\n")), "discrete")

    tokens = {"ksg_local": "2.2e-16", "pid2": "1.1e-16",
              "inc_pid3": "2.2e-16", "full_pid3": "2.2e-16"}
    for key, value in tokens.items():
        before = f"{key}={value}"
        if before not in continuous:
            raise RuntimeError(f"missing original positive maximum {key}")
        reject(f"negative absolute maximum {key}",
               result(0, continuous.replace(before, f"{key}=-{value}", 1)), "continuous")
    for field, true_value, false_value in (("I0", "+0.7401", "+9.9999"),
                                          ("red", "+0.5141", "+9.9999"),
                                          ("I0", "+0.7401", "+0.7400"),
                                          ("red", "+0.5141", "+0.5140")):
        before = f"{field}={true_value}"
        if before not in continuous:
            raise RuntimeError(f"missing original rounded estimate {field}")
        reject(f"invalid printed estimate {field} {false_value}",
               result(0, continuous.replace(before, f"{field}={false_value}", 1)), "continuous")
    reject("noncanonical residual precision",
           result(0, continuous.replace("ksg_s0_t=0.0e+00", "ksg_s0_t=0.00e+00", 1)),
           "continuous")

    # These two synthetic estimates lie close enough to a rounding boundary
    # that the printed difference must be used with its proper sign and precision.
    round_case = H["check_printed_estimate"]
    round_case("signed", "+0.1249", 0.1247999, "-1.0e-04")
    rejected_rounded_cases = 0
    for label, printed, supplied, residual in (
            ("wrong signed direction", "+0.1247", 0.1247999, "-1.0e-04"),
            ("rounding ambiguity", "+0.0000", 0.00015, "1.0e-04")):
        try:
            round_case(label, printed, supplied, residual)
        except Failure:
            rejected_rounded_cases += 1
        else:
            raise RuntimeError(f"accepted changed estimate {label}")

    with tempfile.TemporaryDirectory() as directory:
        observer = Path(directory) / "show_mode.py"
        observer.write_text("import sys\nprint(sys.flags.optimize)\n", encoding="utf-8")
        genuine = H["run_child"](observer, observer)
        if genuine.returncode != 0 or genuine.stderr or genuine.stdout.strip() != str(sys.flags.optimize):
            raise RuntimeError("the child did not inherit the parent's optimization mode")
    print(f"Verified three expected transcripts and rejected {refused} changed transcripts. "
          f"Verified one signed rounding case and rejected {rejected_rounded_cases} changed cases. "
          "Checked the actual child optimization mode.")


if __name__ == "__main__":
    main()
