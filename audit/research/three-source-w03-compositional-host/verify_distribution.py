"""Verify the fixed source archive and install its measured bytes for qualification."""

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile


HERE = Path(__file__).resolve().parent
ARCHIVE = "w03-compositional-field-v2.tar.gz"
ARCHIVE_SHA256 = "46fe098e7f1d2e94e29f5b9a88e93d36e156f5b6514ad8b052822933c6e865ef"
MANIFEST_SHA256 = "4773c2363ced0c069cf0bb3cc17baae51ca94f9599be7fbf4656a589a21a8067"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def load_members(package):
    frame = (package / ARCHIVE).read_bytes()
    require(
        len(frame) == 54046 and sha(frame) == ARCHIVE_SHA256, "original field archive"
    )
    members = {}
    with tarfile.open(fileobj=io.BytesIO(frame), mode="r:gz") as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            require(len(path.parts) >= 2 and path.parts[0] == "field", "field root")
            require(
                path.as_posix() == member.name and ".." not in path.parts,
                "canonical path",
            )
            require(member.isfile() and member.mode == 0o444, "regular read-only input")
            key = path.relative_to("field").as_posix()
            require(key not in members, "duplicate archive member")
            members[key] = archive.extractfile(member).read()
    require(
        len(members) == 28 and sha(members["FIELD.json"]) == MANIFEST_SHA256,
        "field manifest",
    )
    declared = json.loads(members["FIELD.json"])
    checked = {
        key: [len(data), sha(data)]
        for key, data in members.items()
        if key != "FIELD.json"
    }
    require(checked == declared, "manifest byte lengths or digests")
    source = package / "field"
    require(not source.is_symlink(), "source root link")
    all_paths = list(source.rglob("*"))
    require(
        all(not p.is_symlink() for p in all_paths), "link among visible source files"
    )
    visible = {
        p.relative_to(source).as_posix(): p.read_bytes()
        for p in all_paths
        if p.is_file()
    }
    require(visible == members, "readable source and archived bytes differ")
    return members


def install(members, root):
    root.mkdir(mode=0o755, exist_ok=False)
    for name, data in members.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
        path.chmod(0o444)
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_dir():
            path.chmod(0o555)
    root.chmod(0o555)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", type=Path)
    args = parser.parse_args()
    result = load_members(HERE)
    if args.install is not None:
        install(result, args.install)
    print(
        json.dumps(
            {
                "archive": ARCHIVE_SHA256,
                "manifest": MANIFEST_SHA256,
                "members": len(result),
            },
            sort_keys=True,
        )
    )
