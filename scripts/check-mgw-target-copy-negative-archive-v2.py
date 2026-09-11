#!/usr/bin/env python3
"""Validate the inert public projection of failed MGW target-copy routes."""
from pathlib import Path
import hashlib, json, stat

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "audit/archive/mgw-target-copy-development-20260911"
MANIFEST = ARCHIVE / "MANIFEST-v2.json"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    record = json.loads(MANIFEST.read_text())
    assert record["schema"] == "pid-rs-mgw-target-copy-negative-archive-v2"
    assert record["status"] == "inert-retrospective-correction"
    paths = []
    for path in sorted(ARCHIVE.rglob("*")):
        if path.is_symlink(): raise SystemExit(f"symlink in archive: {path}")
        if path.is_file(): paths.append(path)
    payloads = [p for p in paths if p.relative_to(ARCHIVE).parts[:1] == ("payloads",)]
    if len(payloads) != len(record["artifacts"]):
        raise SystemExit(f"payload count mismatch: {len(payloads)} != {len(record['artifacts'])}")
    by_path = {a["path"]: a for a in record["artifacts"]}
    for rel, item in by_path.items():
        path = ARCHIVE / rel
        if not path.is_file() or path.is_symlink(): raise SystemExit(f"missing payload: {rel}")
        if path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            raise SystemExit(f"executable payload: {rel}")
        if path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise SystemExit(f"payload digest mismatch: {rel}")
    if any(p.suffix == ".py" for p in payloads): raise SystemExit("Python payload must remain inert text")
    print(f"OK: v2 inert MGW archive binds {len(record['routes'])} routes and {len(payloads)} redacted payloads")

if __name__ == "__main__": main()
