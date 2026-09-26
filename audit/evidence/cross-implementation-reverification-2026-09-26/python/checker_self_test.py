"""Hostile-input self-test of check_discrete.py and check_continuous.py.

Usage: checker_self_test.py <discrete_dump.json> <continuous_dump.json>

Each case writes one mutated copy of a dump to a private temporary directory and runs the
checker on it. Every mutation must make the checker exit with a nonzero status; the unmutated
dumps must pass. The script exits with status 1 if any mutation is accepted.
"""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISCRETE = HERE / "check_discrete.py"
CONTINUOUS = HERE / "check_continuous.py"


def run(checker, work, data=None, raw=None):
    path = work / "input.json"
    path.write_text(raw if raw is not None else json.dumps(data))
    return subprocess.run([sys.executable, str(checker), str(path)],
                          capture_output=True, text=True).returncode


def main():
    d = json.loads(Path(sys.argv[1]).read_text())
    c = json.loads(Path(sys.argv[2]).read_text())
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        assert run(DISCRETE, work, d) == 0, "unmutated discrete dump must pass"
        assert run(CONTINUOUS, work, c) == 0, "unmutated continuous dump must pass"

        def case(name, checker, data=None, raw=None):
            results.append((name, run(checker, work, data, raw)))

        case("discrete: empty list", DISCRETE, [])
        case("discrete: four-source cases removed", DISCRETE,
             [x for x in d if x["n_sources"] != 4])
        m = copy.deepcopy(d); m[0]["imin2"] = []
        case("discrete: imin2 emptied", DISCRETE, m)
        m = copy.deepcopy(d); m[0]["imin2"] = m[0]["imin2"][:1]
        case("discrete: imin2 truncated", DISCRETE, m)
        m = copy.deepcopy(d)
        zero = next(a for x in m for a in x["n"] if a["net"] == 0.0)
        zero["net"] = False
        case("discrete: JSON false for a zero atom", DISCRETE, m)
        m = copy.deepcopy(d); m[0]["n"][0]["plus"] += 1e-9
        case("discrete: atom perturbed by 1e-9", DISCRETE, m)
        m = copy.deepcopy(d); m[0]["n"].append(copy.deepcopy(m[0]["n"][0]))
        case("discrete: duplicate antichain", DISCRETE, m)
        m = copy.deepcopy(d); m[0]["n"][0]["plus"] = "NaN"
        case("discrete: string value", DISCRETE, m)
        m = copy.deepcopy(d); m[0]["n_subset_mis"][0] += 1e-9
        case("discrete: subset MI perturbed by 1e-9", DISCRETE, m)
        raw = json.dumps(d).replace('"n_sources": 2', '"n_sources": 2, "n_sources": 2', 1)
        case("discrete: duplicate JSON key", DISCRETE, raw=raw)
        case("continuous: empty list", CONTINUOUS, [])
        m = copy.deepcopy(c); m[0]["inc_pid3"] = []
        case("continuous: incomplete PID3 emptied", CONTINUOUS, m)
        m = copy.deepcopy(c)
        for entry in m[0]["inc_pid3"]:
            entry["value"] = None
        case("continuous: incomplete PID3 all abstaining", CONTINUOUS, m)
        m = copy.deepcopy(c)
        m[0]["full_pid3"] = [copy.deepcopy(m[0]["full_pid3"][0]) for _ in range(18)]
        case("continuous: 18 copies of one full-PID3 antichain", CONTINUOUS, m)
        m = copy.deepcopy(c); m[0]["full_pid3"] = "error: unavailable"
        case("continuous: full PID3 absent", CONTINUOUS, m)
        m = copy.deepcopy(c); m[0]["isx_s0_s1_t"] += 1e-9
        case("continuous: redundancy perturbed by 1e-9", CONTINUOUS, m)
        m = copy.deepcopy(c); m[0]["pid2"] = m[0]["pid2"][:3]
        case("continuous: PID2 shortened", CONTINUOUS, m)
    for name, code in results:
        print(f"{'rejected' if code else 'ACCEPTED'}: {name}")
    accepted = [name for name, code in results if code == 0]
    print(f"{len(results) - len(accepted)} of {len(results)} hostile inputs rejected")
    return 1 if accepted else 0


if __name__ == "__main__":
    sys.exit(main())
