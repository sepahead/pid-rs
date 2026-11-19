"""Build the W02 study from its Markdown using the shared finite-study publication routine."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILDER = HERE.parent / "three-source-alphabet-counts" / "build_pdf.py"

if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location("finite_study_publication", BUILDER)
    publication = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(publication)
    publication.command_line(HERE, "three-source-w02", "The eighteen families in the original three-source count test", 4)
