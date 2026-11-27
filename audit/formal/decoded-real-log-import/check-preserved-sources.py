"""Compare the archived Lean input and proof records with their selected original bytes."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parents[3]
STUDY = Path("audit/formal/decoded-real-log-import")
CATALOG = STUDY / "history/selected-source-paths.json"
SOURCE_MAP = STUDY / "history/two-linux-runs/SOURCE-MAP.json"
ORIGINAL_IMPORT = "8c7b04add45b0fa4a4f065e090b9371769c52498"
EXPECTED_CATALOG = "f17dd5c5de306e80a5ff6c1bfbe6b354d4c23523eb8ad6af89567ce9a2938ed3"
IMPORT_WORKFLOW = ".github/workflows/decoded-real-log-import.yml"
ODD_WORKFLOW = ".github/workflows/real-log-odd-tail.yml"
ODD_PREFIX = "audit/formal/real-log-odd-tail/"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def original_blob(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def verify() -> dict[str, int]:
    catalog = (ROOT / CATALOG).read_bytes()
    require(hashlib.sha256(catalog).hexdigest() == EXPECTED_CATALOG, "changed original file map")
    entries = json.loads(catalog)["selected"]
    roles = json.loads((ROOT / SOURCE_MAP).read_bytes())["source_roles"]
    imports = roles[ORIGINAL_IMPORT]["paths"]
    require(len(entries) == 51 and len(imports) == 13, "incomplete preserved input sets")
    for name in (IMPORT_WORKFLOW, ODD_WORKFLOW):
        require(not os.path.lexists(ROOT / name), f"original workflow is active at {name}")

    import_paths = set()
    for original, row in imports.items():
        selected = str(STUDY / "history/import-workflow.source.yml") if original == IMPORT_WORKFLOW else original
        require(selected in entries, f"missing original import input {original}")
        expected = {"mode": row["mode"], "blob": row["git_blob"], "sha256": row["sha256"]}
        require(entries[selected] == expected, f"wrong import source for {original}")
        import_paths.add(selected)
    odd_paths = set(entries) - import_paths
    require(len(odd_paths) == 38 and all(n.startswith(ODD_PREFIX) for n in odd_paths), "wrong proof sources")
    require(ODD_PREFIX + "workflow.source.yml" in odd_paths, "missing archived proof workflow")

    for name, row in entries.items():
        file = ROOT / name
        require(file.resolve() == file and file.is_file(), f"missing original regular file {name}")
        mode = file.stat().st_mode
        require(stat.S_ISREG(mode), f"wrong file kind for {name}")
        git_mode = "100755" if mode & stat.S_IXUSR else "100644"
        data = file.read_bytes()
        require(git_mode == row["mode"], f"wrong original Git mode for {name}")
        require(original_blob(data) == row["blob"], f"wrong original Git object for {name}")
        require(hashlib.sha256(data).hexdigest() == row["sha256"], f"wrong source digest for {name}")
    return {"preserved_import_files": len(import_paths), "preserved_proof_records": len(odd_paths)}


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
