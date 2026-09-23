#!/usr/bin/env python3
"""Check author metadata and visible first-page credit in current pid-rs reports."""

from pathlib import Path
import sys

from pypdf import PdfReader


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    reports = sorted((root / "output/pdf").glob("*.pdf"))
    reports.append(root / "PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf")
    if len(reports) < 29:
        print("Current publication inventory is incomplete.", file=sys.stderr)
        return 1
    failures = []
    for path in reports:
        reader = PdfReader(path, strict=True)
        author = reader.metadata.author if reader.metadata else None
        text = " ".join((reader.pages[0].extract_text() or "").split())
        if author != "Sepehr Mahmoudian" or "SepehrMahmoudian" not in "".join(text.split()):
            failures.append(str(path.relative_to(root)))
    if failures:
        print("Missing author metadata or first-page credit:\n" + "\n".join(failures),
              file=sys.stderr)
        return 1
    print(f"Verified Sepehr Mahmoudian metadata and visible credit in {len(reports)} PDFs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
