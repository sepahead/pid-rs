"""Read the reviewed bytes, author and first page of a public research report."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parent.parent
EDITION = ROOT / "audit/formal/latex/mathematical-results-guide-current/edition.json"
AUTHOR = "Sepehr Mahmoudian"


def check_fields(fields, first_page):
    if fields.get("Author") != AUTHOR or not fields.get("Title", "").strip():
        raise ValueError("missing or unexpected report author or title")
    if not re.fullmatch(r"[1-9][0-9]*", fields.get("Pages", "")):
        raise ValueError("positive page count required")
    if not fields.get("Page size", "").endswith(" (A4)"):
        raise ValueError("expected an A4 report")
    if fields.get("Encrypted") != "no" or fields.get("JavaScript") != "no":
        raise ValueError("unexpected document protection or execution setting")
    if not re.search(r"\bSepehr\s+Mahmoudian\b", first_page):
        raise ValueError("the report requires a first-page byline")


def check(study):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", study):
        raise ValueError("a single research report name is required")
    name = f"output/pdf/{study}.pdf"
    original = ROOT / name
    inputs = json.loads(EDITION.read_text(encoding="utf-8"))["inputs"]
    if original.is_symlink() or not original.is_file():
        raise ValueError(f"the report must be a regular file: {name}")
    digest = hashlib.sha256(original.read_bytes()).hexdigest()
    if inputs.get(name) != digest:
        raise ValueError(f"the report differs from the reviewed edition: {name}")
    env = {**os.environ, "LC_ALL": "C"}
    metadata = subprocess.run(["pdfinfo", original], check=True, capture_output=True,
                              text=True, env=env).stdout
    fields = {}
    for line in metadata.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key] = value.strip()
    page = subprocess.run(["pdftotext", "-f", "1", "-l", "1", "-enc", "UTF-8",
                           original, "-"], check=True, capture_output=True, text=True,
                          env=env).stdout
    check_fields(fields, page)
    print(f"Verified committed bytes, report metadata and first-page byline for {study}.")


def self_test():
    good = {"Author": AUTHOR, "Title": "Example", "Pages": "2", "Page size": "595 x 842 pts (A4)",
            "Encrypted": "no", "JavaScript": "no"}
    check_fields(good, "Example\nSepehr\nMahmoudian")
    for key, value in (("Author", "Unknown"), ("Title", ""), ("Pages", "0"),
                       ("Pages", "two"), ("Page size", "1 x 1"), ("Encrypted", "yes"),
                       ("JavaScript", "yes")):
        try:
            check_fields({**good, key: value}, AUTHOR)
        except ValueError:
            continue
        raise ValueError(f"invalid metadata passed: {key}")
    for text in ("Example", f"Example\n{AUTHOR}son"):
        try:
            check_fields(good, text)
        except ValueError:
            continue
        raise ValueError("an absent or incomplete byline passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--study")
    options.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        check(args.study)
