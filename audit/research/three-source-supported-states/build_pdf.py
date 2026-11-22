"""Typeset and verify the finite weighted-state study with the common publication code."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILDER = HERE.parent / "three-source-alphabet-counts" / "build_pdf.py"

if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location("finite_study_publication", BUILDER)
    publication = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(publication)
    publication.command_line(HERE, "three-source-supported-states",
                             "When are all 18 local shared-exclusion calculations finite?", 8)
