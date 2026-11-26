"""Regenerate the chart and refuse changed scientific inputs before writing either vector."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


FIGURE = Path(__file__).resolve().parent
DATA = FIGURE.parent / "checked"


def draw(support, lattice, output):
    flags = ["-I", "-S", "-B"]
    if sys.flags.optimize:
        flags.append("-O")
    return subprocess.run(
        [sys.executable, *flags, str(FIGURE / "draw.py"),
         "--support", str(support), "--lattice", str(lattice), "--output", str(output)],
        capture_output=True,
        timeout=60,
        check=False,
    )


def main():
    with tempfile.TemporaryDirectory(prefix="lp4-figure-check-") as tmp:
        work = Path(tmp)
        support = DATA / "support-ordinary.json"
        lattice = DATA / "lattice-ordinary.json"
        generated = work / "generated"
        good = draw(support, lattice, generated)
        good.check_returncode()
        for ext in ("svg", "pdf"):
            name = "force-copy-atoms." + ext
            if (generated / name).read_bytes() != (FIGURE / name).read_bytes():
                raise ValueError(f"generated {ext} differs")
        actual = json.loads(support.read_bytes())
        sign = deepcopy(actual)
        five = sign["five_signed_products"]
        five["04"], five["05"] = five["05"], five["04"]
        zero = deepcopy(actual)
        zero["cells"][0]["count"] = 0
        invalid_science = [("interchanged-signs", sign), ("missing-occupied-cell", zero)]
        for label, wrong in invalid_science:
            operand = work / (label + ".json")
            operand.write_text(json.dumps(wrong))
            output = work / label
            changed = draw(operand, lattice, output)
            if changed.returncode == 0 or output.exists():
                raise ValueError(f"chart accepted {label}")
        hidden = json.loads(lattice.read_bytes())
        hidden["scientific_result"]["all108"]["01"]["signed"]["atom"] = "9"
        altered = work / "altered.json"
        altered.write_text(json.dumps(hidden))
        last_output = work / "hidden-coordinate"
        changed = draw(support, altered, last_output)
        if changed.returncode == 0 or last_output.exists():
            raise ValueError("chart accepted a changed unplotted result")
    print("Both vector files reproduced. Three altered empirical records refused before rendering.")


if __name__ == "__main__":
    main()
