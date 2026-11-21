"""Retain ordered raw theorem observations and check the complete original semantic reader."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("observer_support", HERE/"support.py")
S=importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def fold(root, ordered, sink=None, available=None):
    """Compare all raw records with their assigned names. Preserve every byte and half-open range."""
    h = hashlib.sha256()
    frames = []
    offset = 0
    for module, names in ordered:
        folder = root/"commands"/("inspect-"+module)
        result = S.read(folder/"result.json")
        source = folder/"stdout"
        S.require(result["tag"] == "inspect-"+module and result["exit"] == 0 and result["stop"] is None and
                  result["post_group_absent"] is True and result["residual_after_wait4"] is False and
                  result["stderr_bytes"] == 0 and result["stdout_bytes"] == source.stat().st_size and
                  result["stdout_sha256"] == S.digest(source) and (folder/"stderr").read_bytes() == b"",
                  "incomplete native shard "+module)
        start = offset
        with source.open("rb") as incoming:
            for expected in names:
                # The complete evidence tree bounds each input even when verification has no output sink.
                max_line = S.SAFE_LIMITS["retained_bytes"] - offset
                if available is not None:
                    max_line = min(max_line, available-offset)
                S.require(max_line > 0, "no retained space for next record")
                raw = incoming.readline(max_line+1)
                S.require(0 < len(raw) <= max_line and raw.endswith(b"\n") and raw.startswith(b"W02_TERM "), "whole bounded native row")
                row = json.loads(raw[len(b"W02_TERM "):],object_pairs_hook=S.V1.pairs)
                S.require(row.get("name") == expected, "wrong name, order or shard at "+expected)
                if sink is not None:
                    sink.write(raw)
                h.update(raw)
                offset += len(raw)
            S.require(not incoming.read(1), "surplus raw row "+module)
        frames.append({"module":module, "targets":names, "begin":start, "end":offset, "stdout":S.info(source)})
    return {"schema":1,"frames":frames,"joined":{"bytes":offset,"sha256":h.hexdigest()}}


def verify_derived(root, repo):
    old = S.read(repo/S.V1.PACKAGE/"plan.json")
    frame = fold(root,S.groups(old))
    S.require(frame == S.read(root/"term-shards.json") and frame["joined"] == S.info(root/"joined-terms.stdout"),
              "byte ranges, sources or joined term output differ")
    def stream(tag):
        if tag == "inspect-IndexTerms":
            return root/"joined-terms.stdout"
        return root/"commands"/tag/"stdout"
    return S.V1.inspect(repo, stream)


def write_evidence(root, repo):
    resources = S.load(repo/S.V1.OLD/"native_resources.py")
    limit = S.SAFE_LIMITS["retained_bytes"]
    base = resources.retained_bytes(root.parent)
    available = limit-base
    S.require(available > 0, "retained capacity for join")
    plan = S.read(repo/S.V1.PACKAGE/"plan.json")
    with (root/"joined-terms.stdout").open("xb") as out:
        frames = fold(root,S.groups(plan),out,available)
    S.require(resources.retained_bytes(root.parent) <= limit, "joined bytes exceeded retention")
    def write_new(path, obj):
        content = (json.dumps(obj,indent=2,sort_keys=True)+"\n").encode()
        S.require(resources.retained_bytes(root.parent)+len(content) <= limit, "derived metadata exceeds remaining retention")
        with path.open("xb") as f:
            f.write(content)
    write_new(root/"term-shards.json",frames)
    observed = verify_derived(root,repo)
    write_new(root/"observed.json",observed)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result",required=True,type=Path)
    args=parser.parse_args()
    write_evidence(args.result.resolve(),S.REPOSITORY)
