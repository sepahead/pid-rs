"""Exercise the new guest observations and the independent service-limit reader."""
import copy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def must_refuse(function, *args):
    try:
        function(*args)
    except (ValueError, TypeError, KeyError):
        return 1
    raise ValueError("an invalid observation was accepted")


def main():
    env = load("fixed_environment", HERE / "overrides/environment.py")
    live = load("working_directory_service", HERE / "observe_service.py")
    expected = {
        "HOME": "/tmp", "LC_ALL": "C.UTF-8", "LEAN_NUM_THREADS": "1",
        "LEAN_PATH": "/objects", "PATH": "/stock/bin", "PWD": "/src", "TMPDIR": "/tmp",
    }
    if env.EXPECTED_ENVIRONMENT != expected:
        raise ValueError("the seven published values changed")
    env.require_environment(expected, "/src")
    env_errors = 0
    for name in sorted(expected):
        missing = dict(expected)
        del missing[name]
        env_errors += must_refuse(env.require_environment, missing, "/src")
        changed = dict(expected)
        changed[name] += "_different"
        env_errors += must_refuse(env.require_environment, changed, "/src")
    for values, cwd in (
        ({**expected, "EXTRA": "unexpected"}, "/src"),
        ({**expected, "PWD": True}, "/src"),
        (expected, "/tmp"), (expected, None), (None, "/src"),
    ):
        env_errors += must_refuse(env.require_environment, values, cwd)
    good = {
        "name": "/system.slice/pidrs-w03d-1.service", "pid": 15, "uid": 0, "peak_bytes": 4096,
        "limits": {"cpu.max": "100000 100000", "memory.max": "4294967296",
                   "memory.swap.max": "0", "memory.current": "2048"},
    }
    live.limits(good)
    limit_errors = 0
    for name, value in (("uid", False), ("pid", True), ("peak_bytes", True),
                        ("peak_bytes", 1024), ("peak_bytes", 4294967297)):
        changed = copy.deepcopy(good)
        changed[name] = value
        limit_errors += must_refuse(live.limits, changed)
    for name, value in (("memory.max", "0"), ("memory.max", "4294967297"),
                        ("memory.swap.max", "1"), ("cpu.max", "110000 100000"),
                        ("cpu.max", "0 100000"), ("cpu.max", "50000 100000")):
        changed = copy.deepcopy(good)
        changed["limits"][name] = value
        limit_errors += must_refuse(live.limits, changed)
    print(json.dumps({"observed_keys": 7, "environment_refusals": env_errors,
                      "service_limit_refusals": limit_errors, "scientific_proofs_scored": 0},
                     sort_keys=True))


if __name__ == "__main__":
    main()
