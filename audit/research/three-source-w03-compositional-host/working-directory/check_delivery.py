"""Exercise the delivery checks using harmless source and transport fixtures."""

import copy
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tarfile
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def expect_refusal(test, reasons, expected):
    try:
        test()
    except (ValueError, OSError, KeyError) as err:
        if expected not in str(err):
            raise ValueError(("different refusal", expected, str(err))) from err
        reasons.append(expected)
        return
    raise ValueError("an invalid fixture passed: " + expected)


def make_tar():
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as pack:
        for key, value in (("evidence/terminal.json", b'{"pass":false}\n'),):
            entry = tarfile.TarInfo(key)
            entry.size = len(value)
            pack.addfile(entry, io.BytesIO(value))
    return raw.getvalue()


def make_case(root, serial, replacements=None):
    # This artifact exercises envelope parsing only. Its native terminal explicitly failed.
    commit = "a" * 40
    run = 123
    repo = "sepahead/pid-rs"
    archive = make_tar()
    live = {
        "name": "/system.slice/pidrs-w03d-123.service",
        "pid": 15,
        "uid": 0,
        "peak_bytes": 1024,
        "limits": {
            "memory.max": "4294967296",
            "memory.swap.max": "0",
            "cpu.max": "100000 100000",
            "memory.current": "512",
        },
    }
    files = {
        "event.txt": f"repository={repo}\ncommit={commit}\nevent=workflow_dispatch\nref=refs/heads/main\nrun=123\nattempt=1\n".encode(),
        "distribution.json": json.dumps(
            {
                "manifest": "a1f23f4805c2de8dcbe8551b7bf0fb2ce606b0eb510582a824c60565c5e54978",
                "members": 29,
                "archive": "977d4f570ebddc330325665600c77c72a53a911dec7099a0ef2cfb778bd572d1",
            }
        ).encode(),
        "host-limit-before.json": json.dumps(live).encode(),
        "host-limit-after.json": json.dumps(live).encode(),
        "disk-before.txt": b"fixture",
        "host-tools.txt": b"fixture",
        "service.log": b"fixture",
        "service-state.txt": b"unavailable",
        "evidence.tar": archive,
        "evidence.sha256": (sha(archive) + "  evidence.tar\n").encode(),
    }
    for name, value in (replacements or {}).items():
        if value is None:
            files.pop(name)
        else:
            files[name] = value
    bundle = root / ("fixture-" + str(serial) + ".zip")
    with zipfile.ZipFile(bundle, "x") as z:
        for n, b in files.items():
            z.writestr(zipfile.ZipInfo(n), b)
    h = sha(bundle.read_bytes())
    args = SimpleNamespace(
        repository=repo,
        commit=commit,
        ref="refs/heads/main",
        event="workflow_dispatch",
        native_run=run,
        artifact_id=12345,
        upload_digest=h,
    )
    meta = {
        "name": f"w03-working-directory-{commit}-{run}-1",
        "id": 12345,
        "digest": "sha256:" + h,
        "expired": False,
        "size_in_bytes": bundle.stat().st_size,
        "workflow_run": {
            "id": run,
            "head_sha": commit,
            "head_branch": "main",
            "repository_id": 1271708111,
            "head_repository_id": 1271708111,
        },
    }
    return bundle, meta, args, live


def main():
    sys.path.insert(0, str(HERE))
    from observe_service import limits
    from read_delivery import decode_unique, envelope, unpack

    reasons = []
    expect_refusal(
        lambda: decode_unique(b'{"id":1,"id":2}'), reasons, "duplicate JSON key"
    )
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bundle, meta, args, live = make_case(root, 0)
        result = envelope(bundle, meta, root / "valid-transport", args)
        if result["id"] != 12345:
            raise ValueError("fixture transport")
        unpack(root / "valid-transport/evidence.tar", root / "parsed-fixture")
        # The failed terminal has no authorized field recipient receipt.
        native = json.loads(
            (root / "parsed-fixture/evidence/terminal.json").read_bytes()
        )
        if native != {"pass": False}:
            raise ValueError("fixture scope")
        limits(live)
        for i, (field, value, msg) in enumerate(
            (
                ("id", 54321, "uploaded artifact identity"),
                ("digest", "0" * 64, "uploaded artifact identity"),
                ("expired", True, "uploaded artifact identity"),
                ("name", "different", "uploaded artifact identity"),
                ("size_in_bytes", 5, "actual uploaded byte length"),
            )
        ):
            changed = dict(meta)
            changed[field] = value
            expect_refusal(
                lambda: envelope(bundle, changed, root / f"meta-{i}", args),
                reasons,
                msg,
            )
        for field, value in (
            ("id", 124),
            ("head_sha", "b" * 40),
            ("head_branch", "elsewhere"),
            ("repository_id", 123),
            ("head_repository_id", 124),
        ):
            changed = copy.deepcopy(meta)
            changed["workflow_run"][field] = value
            expect_refusal(
                lambda: envelope(bundle, changed, root / ("run-" + field), args),
                reasons,
                "provider run linkage",
            )
        for i, (name, value, msg) in enumerate(
            (
                ("host-limit-after.json", None, "complete artifact member roster"),
                ("event.txt", b"different", "exact recorded event"),
                ("evidence.sha256", b"different", "evidence stream"),
                ("distribution.json", b"{}", "field distribution"),
            ),
            10,
        ):
            b, m, a, _ = make_case(root, i, {name: value})
            expect_refusal(lambda: envelope(b, m, root / f"file-{i}", a), reasons, msg)
        for i, (key, value) in enumerate(
            (
                ("memory.max", "8589934592"),
                ("memory.swap.max", "1"),
                ("cpu.max", "200000 100000"),
            )
        ):
            changed = copy.deepcopy(live)
            changed["limits"][key] = value
            expect_refusal(lambda: limits(changed), reasons, "live hard limits")
            b, m, a, _ = make_case(
                root, 20 + i, {"host-limit-before.json": json.dumps(changed).encode()}
            )
            expect_refusal(
                lambda: envelope(b, m, root / f"limit-{i}", a),
                reasons,
                "live service limits",
            )
        changed = copy.deepcopy(live)
        changed["pid"] = 30
        b, m, a, _ = make_case(
            root, 29, {"host-limit-after.json": json.dumps(changed).encode()}
        )
        expect_refusal(
            lambda: envelope(b, m, root / "different-service", a),
            reasons,
            "same service and run",
        )
    print(
        json.dumps(
            {
                "rejected": len(reasons),
                "reasons": reasons,
                "scope": "source-free synthetic transport; zero native proof events",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
