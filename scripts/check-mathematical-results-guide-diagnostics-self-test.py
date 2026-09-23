#!/usr/bin/env python3
"""Exercise scoped guide diagnostics with a pinned raw-TeX/manifest fixture.

The synthetic log contains the exact retained warning blocks. These controls test
matching and rejection; they do not replace an actual build-log observation.
Run this script normally and with -O. It never modifies its input fixtures.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

RAW_SHA256 = "1927bb26900eb31f448a41579f11d0779de5acf6d75f059379faf0fedbb3a320"
MANIFEST_SHA256 = "a9589302cad3c5dc69b25aceccd0dee5aaec36cbc9744396d41274aaf6b2eba9"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--helper", type=Path, default=Path(__file__).with_name(
        "check-mathematical-results-guide-diagnostics.py"))
    parser.add_argument("--raw-tex", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("guide_diagnostics", args.helper)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    raw = args.raw_tex.read_bytes()
    manifest_bytes = args.manifest.read_bytes()
    require(digest(raw) == RAW_SHA256, "raw fixture identity changed")
    require(digest(manifest_bytes) == MANIFEST_SHA256, "manifest fixture identity changed")
    caption = b"\\captionsetup[table]{skip=6pt}"
    require(raw.count(caption) == 1, "expected one canonical caption setup")
    tex = (b"\\DocumentMetadata{testphase=phase-II,lang=en-US}\n"
           + raw.replace(caption, b"\\captionsetup*[table]{skip=6pt}"))
    manifest = json.loads(manifest_bytes)
    require(digest(tex) == manifest["tex_sha256"], "normalization identity changed")
    profile = manifest["profile"]
    blocks = [row["message"] for row in manifest["diagnostics"]]
    log = ("\n\n".join(blocks) + "\n\n").encode()
    results = []

    def exercise(name, *, log_bytes=log, tex_bytes=tex,
                 value=None, raw_manifest=None, expected_digest=None,
                 selected_profile=profile, accepted=False):
        data = (manifest_bytes if value is None else encode(value))
        if raw_manifest is not None:
            data = raw_manifest
        pin = digest(data) if expected_digest is None else expected_digest
        try:
            receipt = helper.check(log_bytes, tex_bytes, data, pin, selected_profile)
        except (helper.DiagnosticError, json.JSONDecodeError, UnicodeError):
            require(not accepted, name + ": unexpectedly rejected")
        else:
            require(accepted, name + ": unexpectedly accepted")
            require(receipt["pdf_ua_claim"] is False, "accessibility scope changed")
            require(receipt["visual_acceptance"] is False, "visual scope changed")
            require(receipt["warning_free"] is False, "warning scope changed")
        results.append(name)

    exercise("baseline-exact-warning-blocks", accepted=True)
    for name, warning in [
        ("unknown-package", "Package unknown Warning: new diagnostic"),
        ("overfull-hbox", r"Overfull \hbox (1.0pt too wide)"),
        ("underfull-vbox", r"Underfull \vbox (badness 10000)"),
        ("missing-glyph", "Missing character: There is no X in font"),
        ("undefined-reference", "LaTeX Warning: Reference x undefined"),
        ("fatal-error", "! Undefined control sequence."),
    ]:
        exercise(name, log_bytes=log + warning.encode() + b"\n\n")
    exercise("changed-warning", log_bytes=log.replace(b"Unable to apply", b"Unable now to apply", 1))
    exercise("missing-warning", log_bytes=("\n\n".join(blocks[1:]) + "\n\n").encode())
    exercise("reordered-warning", log_bytes=("\n\n".join([blocks[1], blocks[0], *blocks[2:]]) + "\n\n").encode())
    exercise("extra-warning", log_bytes=log + blocks[0].encode() + b"\n\n")
    exercise("changed-tex", tex_bytes=tex + b"\n")
    exercise("wrong-profile", selected_profile="unreviewed-profile")
    exercise("wrong-manifest-pin", expected_digest="0" * 64)
    for name, field, value in [
        ("schema", "schema", "wrong"),
        ("scope", "scope", "pdf-ua"),
        ("bool-not-zero", "pdf_ua_claim", 0),
        ("digest-type", "tex_sha256", 1),
        ("diagnostics-type", "diagnostics", {}),
    ]:
        changed = copy.deepcopy(manifest)
        changed[field] = value
        exercise(name, value=changed)
    for value in (True, 296.0, "296", 0):
        changed = copy.deepcopy(manifest)
        changed["diagnostics"][0]["anchors"][0]["line"] = value
        exercise("anchor-line-" + repr(value), value=changed)
    changed = copy.deepcopy(manifest)
    changed["diagnostics"][0]["anchors"][0]["text"] += " changed"
    exercise("anchor-text", value=changed)
    for command in (b"\\footnote{x}", b"\\footnotemark", b"\\footnotetext{x}"):
        changed_tex = tex + b"\n" + command + b"\n"
        changed = copy.deepcopy(manifest)
        changed["tex_sha256"] = digest(changed_tex)
        exercise("footnote-" + command.decode(), value=changed, tex_bytes=changed_tex)
    for name, data in [
        ("malformed-json", b"{"),
        ("duplicate-json", b'{"schema":1,"schema":2}'),
        ("nonfinite-json", b'{"schema":NaN}'),
    ]:
        exercise(name, raw_manifest=data)
    require(args.raw_tex.read_bytes() == raw, "raw fixture changed during test")
    require(args.manifest.read_bytes() == manifest_bytes, "manifest changed during test")
    print(json.dumps({"cases": len(results), "passed": results, "scope":
        "synthetic exact-block controls; no build or accessibility acceptance"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
