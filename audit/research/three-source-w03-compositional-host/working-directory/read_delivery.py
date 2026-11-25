"""Read a candidate-free W03 evidence archive using the fixed recipient."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile


HERE = Path(__file__).resolve().parent
GIB = 1 << 30
FIELD = "a1f23f4805c2de8dcbe8551b7bf0fb2ce606b0eb510582a824c60565c5e54978"


def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def unpack(filename, destination):
    require(0 < filename.stat().st_size <= GIB + (32 << 20), "archive extent")
    destination.mkdir(mode=0o700, exist_ok=False)
    seen = set()
    size = 0
    with tarfile.open(filename, "r:") as archive:
        for entry in archive:
            path = PurePosixPath(entry.name)
            require(
                path.parts and path.parts[0] == "evidence" and ".." not in path.parts,
                "entry root",
            )
            require(
                path.as_posix() == entry.name and entry.name not in seen,
                "unique canonical entry",
            )
            require(
                entry.isdir() or entry.isfile(), "only actual files and directories"
            )
            seen.add(entry.name)
            size += entry.size
            require(
                0 <= entry.size and size < GIB and len(seen) <= 8192,
                "native output limits",
            )
            output = destination / path
            if entry.isdir():
                output.mkdir(mode=0o700, parents=True, exist_ok=True)
                continue
            output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with archive.extractfile(entry) as source, output.open("xb") as sink:
                shutil.copyfileobj(source, sink, length=1 << 20)
            require(output.stat().st_size == entry.size, "incomplete native file")
    require("evidence/terminal.json" in seen, "missing native terminal")


def decode_unique(raw):
    def reject_duplicate(pairs):
        record = {}
        for key, value in pairs:
            require(key not in record, "duplicate JSON key")
            record[key] = value
        return record

    return json.loads(raw, object_pairs_hook=reject_duplicate)


def provider_digest(value):
    require(
        isinstance(value, str) and re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", value),
        "provider SHA-256",
    )
    return value.removeprefix("sha256:")


def envelope(bundle, metadata, root, args):
    require(
        args.repository == "sepahead/pid-rs"
        and re.fullmatch(r"[0-9a-f]{40}", args.commit),
        "public source",
    )
    require(
        args.event in ("push", "workflow_dispatch")
        and (
            (
                args.event == "push"
                and re.fullmatch(
                    r"refs/heads/review/w03-working-directory/[0-9a-f]{40}", args.ref
                )
            )
            or (args.event == "workflow_dispatch" and args.ref == "refs/heads/main")
        ),
        "admitted event",
    )
    require(
        type(args.native_run) is int
        and args.native_run > 0
        and type(args.artifact_id) is int
        and args.artifact_id > 0,
        "actual IDs",
    )
    expected_name = f"w03-working-directory-{args.commit}-{args.native_run}-1"
    declared_hash = provider_digest(args.upload_digest)
    require(
        type(metadata["id"]) is int
        and metadata["id"] == args.artifact_id
        and metadata["name"] == expected_name
        and metadata["expired"] is False
        and provider_digest(metadata["digest"]) == declared_hash,
        "uploaded artifact identity",
    )
    run = metadata["workflow_run"]
    require(
        type(run["id"]) is int
        and run["id"] == args.native_run
        and run["repository_id"] == 1271708111
        and run["head_repository_id"] == 1271708111
        and run["head_sha"] == args.commit
        and run["head_branch"] == args.ref.removeprefix("refs/heads/"),
        "provider run linkage",
    )
    require(
        type(metadata["size_in_bytes"]) is int
        and bundle.stat().st_size == metadata["size_in_bytes"]
        and 0 < bundle.stat().st_size <= GIB + (64 << 20),
        "actual uploaded byte length",
    )
    with bundle.open("rb") as stream:
        require(
            hashlib.file_digest(stream, "sha256").hexdigest() == declared_hash,
            "downloaded ZIP bytes",
        )
    names = {
        "event.txt",
        "distribution.json",
        "disk-before.txt",
        "host-tools.txt",
        "service.log",
        "service-state.txt",
        "host-limit-before.json",
        "host-limit-after.json",
        "evidence.tar",
        "evidence.sha256",
    }
    root.mkdir(mode=0o700, exist_ok=False)
    with zipfile.ZipFile(bundle) as archive:
        members = archive.infolist()
        require(
            len(members) == len(names) and {f.filename for f in members} == names,
            "complete artifact member roster",
        )
        require(
            sum(f.file_size for f in members) <= GIB + (40 << 20),
            "returned native artifact extent",
        )
        for member in members:
            require(
                not member.is_dir() and not member.flag_bits & 1,
                "regular public ZIP entry",
            )
            with (
                archive.open(member) as source,
                (root / member.filename).open("xb") as sink,
            ):
                shutil.copyfileobj(source, sink, length=1 << 20)
    expected = (
        f"repository={args.repository}\ncommit={args.commit}\nevent={args.event}\nref={args.ref}\n"
        f"run={args.native_run}\nattempt=1\n"
    )
    require((root / "event.txt").read_text() == expected, "exact recorded event")
    distribution = decode_unique((root / "distribution.json").read_bytes())
    require(
        distribution
        == {
            "manifest": FIELD,
            "members": 29,
            "archive": "977d4f570ebddc330325665600c77c72a53a911dec7099a0ef2cfb778bd572d1",
        },
        "field distribution",
    )
    logs = [
        decode_unique((root / ("host-limit-" + phase + ".json")).read_bytes())
        for phase in ("before", "after")
    ]
    for obs in logs:
        v = obs["limits"]
        quota, period = map(int, v["cpu.max"].split())
        require(
            type(obs["uid"]) is int
            and obs["uid"] == 0
            and type(obs["pid"]) is int
            and obs["pid"] > 0
            and 0 < int(v["memory.max"]) <= 4 * GIB
            and int(v["memory.swap.max"]) == 0
            and quota == period and period > 0
            and type(obs["peak_bytes"]) is int
            and 0 <= int(v["memory.current"]) <= obs["peak_bytes"] <= int(v["memory.max"]),
            "live service limits",
        )
    require(
        logs[0]["name"] == logs[1]["name"]
        and logs[0]["pid"] == logs[1]["pid"]
        and logs[0]["name"].endswith(f"/pidrs-w03d-{args.native_run}.service"),
        "same service and run",
    )
    peaks = [obs["peak_bytes"] for obs in logs]
    if any(peak is not None for peak in peaks):
        require(
            all(type(p) is int and p >= 0 for p in peaks) and peaks[0] <= peaks[1],
            "kernel peak accounting",
        )
    with (root / "evidence.tar").open("rb") as stream:
        retained_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    require(
        (root / "evidence.sha256").read_text() == retained_hash + "  evidence.tar\n",
        "evidence stream",
    )
    return {
        "id": args.artifact_id,
        "name": expected_name,
        "sha256": declared_hash,
        "bytes": bundle.stat().st_size,
        "run_id": args.native_run,
        "attempt": 1,
        "commit": args.commit,
        "ref": args.ref,
        "event": args.event,
        "native_tar_sha256": retained_hash,
        "service": logs[0]["name"],
        "kernel_peak_bytes": peaks[1],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--native-run", type=int, required=True)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--upload-digest", required=True)
    args = parser.parse_args()
    subprocess.run(
        [sys.executable, "-I", "-S", "-B", HERE / "verify_distribution.py"],
        check=True,
        capture_output=True,
        timeout=60,
    )
    bundles = [p for p in args.bundle_dir.rglob("*") if p.is_file()]
    require(
        len(bundles) == 1 and not bundles[0].is_symlink(), "one actual downloaded ZIP"
    )
    meta = decode_unique(args.metadata.read_bytes())
    retained = envelope(bundles[0], meta, args.destination, args)
    verified = args.destination / "received"
    unpack(args.destination / "evidence.tar", verified)
    native_id = f"W03D-{args.native_run}-1"
    native_field = args.destination / "received-field"
    subprocess.run(
        [sys.executable, "-I", "-S", "-B", HERE / "verify_distribution.py", "--install", native_field],
        check=True, capture_output=True, timeout=90,
    )
    command = [
        native_field / "recipient.py",
        "qualify",
        "--root",
        verified / "evidence",
        "--run-id",
        native_id,
        "--field-sha",
        FIELD,
    ]
    observations = []
    for flags in ([], ["-O"]):
        output = subprocess.run(
            [sys.executable, *flags, "-I", "-S", "-B", *command],
            check=True,
            capture_output=True,
            timeout=600,
        )
        observations.append(output.stdout)
    require(
        observations[0] == observations[1], "ordinary and optimized readbacks differ"
    )
    receipt = decode_unique(observations[0])
    require(
        receipt["verified"] is True
        and receipt["field"] == FIELD
        and receipt["mode"] == "qualify"
        and receipt["run"] == native_id,
        "recipient scope",
    )
    print(
        json.dumps(
            {
                "recipient": receipt,
                "provider": retained,
                "modes": ["ordinary", "optimized"],
                "original_proofs_scored": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
