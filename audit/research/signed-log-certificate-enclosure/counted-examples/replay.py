"""Replay the exact two-row experiment and the three constructed reports."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
TRANSPORT = "50b5b631bcbc2da6b1263cbabee3a318ca8d19597005c09cc105c87fc4050b62"


def digest(data):
    return sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="new output directory")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(mode=0o700, exist_ok=False)
    inputs = out/"original-reader"
    shutil.copytree(HERE/"reader-inputs", inputs)
    original = inputs/"arithmetic.py"
    shutil.copyfile(HERE.parent/"formal/fixed/arithmetic.py", original)
    transport = (HERE/"source-transport.json").read_bytes()
    require(digest(transport) == TRANSPORT, "historical scientific script identities")
    for name, spec in json.loads(transport).items():
        published = (HERE/name).read_bytes()
        require(digest(published) == spec["published_sha256"] and spec["append_lf_bytes"]==1, name)
        original_bytes = published+b"\n"
        require(digest(original_bytes)==spec["raw_sha256"], "original "+name)
        (out/name).write_bytes(original_bytes)
    fixtures = out/"constructed"
    fixtures.mkdir()
    launcher = [sys.executable,"-I","-S","-B"]
    if sys.flags.optimize:
        launcher.append("-O")
    runs = [
        ("search.py",[original],"SEARCH.json"),
        ("judge.py",[original,out/"SEARCH.json"],"CHECKED.json"),
        ("true_cell.py",[inputs,"--fixtures",fixtures],"TRUE-CELLS.json"),
    ]
    result = {}
    for name, arguments, expected in runs:
        run = subprocess.run([*launcher,out/name,*arguments],capture_output=True,timeout=180)
        (out/expected).write_bytes(run.stdout)
        (out/(name+".stderr")).write_bytes(run.stderr)
        require(run.returncode == 0 and not run.stderr, name+" execution")
        require(run.stdout == (HERE/expected).read_bytes(), name+" complete original output")
        result[expected] = digest(run.stdout)
    for path in sorted((HERE/"constructed").iterdir()):
        data = (fixtures/path.name).read_bytes()
        require(path.read_bytes()==data,path.name+" regenerated scientific input")
        result[path.name]=digest(data)
    directed = HERE/"directed"
    supplemental = [
        ("true_cell.py", [inputs/"check.py",out/"directed-records"], "TRUE-CELL-REPORTS.json"),
        ("seven_sides.py", [HERE.parent/"numerical/counted.json",original], "SEVEN-GRID-SIDES.json"),
        ("both_grid_sides.py", [inputs/"check.py",out/"both-directed-records"], "BOTH-SIDES-CENSUS.json"),
    ]
    for name, arguments, expected in supplemental:
        run = subprocess.run([*launcher,directed/name,*arguments],capture_output=True,timeout=100)
        (out/expected).write_bytes(run.stdout)
        (out/("directed-"+name+".stderr")).write_bytes(run.stderr)
        require(run.returncode == 0 and not run.stderr, name+" independent full reader")
        require(run.stdout == (directed/expected).read_bytes(), expected+" complete output")
        result[expected] = digest(run.stdout)
    print(json.dumps(result,sort_keys=True,separators=(",",":")))


if __name__ == "__main__":
    main()
