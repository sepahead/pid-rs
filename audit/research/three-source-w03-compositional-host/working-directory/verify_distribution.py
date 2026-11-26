"""Verify and install the working-directory field using the exact preceding sources."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent
FIELD = "a1f23f4805c2de8dcbe8551b7bf0fb2ce606b0eb510582a824c60565c5e54978"
ARCHIVE = "977d4f570ebddc330325665600c77c72a53a911dec7099a0ef2cfb778bd572d1"
ORIGINAL_LOADER = "d653d838724577c435fdd72e848ab587d3297213f5ae71b4470f267602435525"
CHANGED = {"FIELD.md", "FIELD.json", "containment.py", "environment.py", "judge.py", "recipient.py"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ensure(ok, message):
    if not ok:
        raise ValueError(message)


def sources(package):
    original = package.parent / "verify_distribution.py"
    ensure(sha(original.read_bytes()) == ORIGINAL_LOADER, "original distribution reader")
    spec = importlib.util.spec_from_file_location("pinned_original_field", original)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    members = old.load_members(package.parent)
    ensure(len(members) == 28, "original source count")
    changes = package / "overrides"
    entries = list(changes.iterdir())
    ensure({p.name for p in entries} == CHANGED and all(p.is_file() and not p.is_symlink() for p in entries), "fixed source changes")
    members.update({p.name: p.read_bytes() for p in entries})
    ensure(len(members) == 29 and sha(members["FIELD.json"]) == FIELD, "new field identity")
    expected = {name: [len(value), sha(value)] for name, value in members.items() if name != "FIELD.json"}
    ensure(json.loads(members["FIELD.json"]) == expected, "every checked source byte")
    compressed = (package / "w03-working-directory-field.tar.gz").read_bytes()
    ensure(len(compressed) == 53990 and sha(compressed) == ARCHIVE, "new compressed source")
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(compressed), mode="r:gz") as source:
        for member in source:
            key = member.name.removeprefix("field/")
            ensure(member.name == "field/" + key and key in members and key not in seen, "archive member identity")
            ensure(member.isfile() and member.mode == 0o444 and member.size == len(members[key]), "regular read-only member")
            ensure(source.extractfile(member).read() == members[key], "readable and archived member")
            seen.add(key)
    ensure(seen == set(members), "all archived source bytes")
    return old, members


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", type=Path)
    args = parser.parse_args()
    old, members = sources(ROOT)
    if args.install is not None:
        old.install(members, args.install)
    print(json.dumps({"archive": ARCHIVE, "manifest": FIELD, "members": len(members)}, sort_keys=True))


if __name__ == "__main__":
    main()
