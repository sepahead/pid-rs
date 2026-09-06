#!/usr/bin/env python3
"""Stage exact DNF/order judge revision 3 and replay the accepted public source.

Portable routing revision 1. The original judge owns every proof predicate and
process limit. This launcher adds no theorem or historical execution credit.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import sys
from types import ModuleType

HERE = Path(__file__).resolve().parent
JUDGE_SHA256 = '1d80ce12f44e3f602572d5755f059d66b0fdf03fec184f9c0393137b05f8e3e9'
FREEZE_SHA256 = '45a9309d4a8bb764fcd5ec11fbbd08787bf55da24ea1baf34fada3a22d213586'
SELECTED_SHA256 = 'af925aacc56cf765e875ba8bdce41e62139fc9c8be9317a87e5d63df69cf7af2'
COSMETIC_SHA256 = '6ca4bcaf51c3e94db7398c858aaac89d2be72de2ec2ee1b86ae1283db973826a'
COSMETIC_PREFIX = b'/- Cosmetic replay control: unchanged theorem proofs. -/\n'
RUNTIME_RELATIVE = Path('.local/sx-dnf-order-public-replay-v1')


def load_original_judge():
    path = HERE / 'judge-v3/judge.py'
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != JUDGE_SHA256:
        raise RuntimeError('original judge source digest changed')
    module = ModuleType('unchanged_dnf_order_judge_v3')
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec', dont_inherit=True,
                 optimize=sys.flags.optimize), module.__dict__)
    return module, raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run-name', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--action', choices=('check', 'self-test', 'reporting-regression'), default='check')
    parser.add_argument('--source', choices=('selected', 'cosmetic'), default='selected')
    parser.add_argument('--accepted-run', type=Path)
    parser.add_argument('--accepted-receipt-sha256')
    parser.add_argument('--prepare-only', action='store_true',
                        help='write the exact staged inputs and command plan; perform no Lean check')
    args = parser.parse_args()
    j, loaded = load_original_judge()
    snapshot = j.Snapshot()
    j.require(snapshot.read(HERE / 'judge-v3/judge.py') == loaded, 'judge source changed during load')
    raw = snapshot.read(HERE / 'replay-v1.json')
    j.require(j.HEX.fullmatch(args.manifest_sha256) is not None
              and j.digest(raw) == args.manifest_sha256, 'public routing manifest digest changed')
    manifest = j.strict_json(raw)
    j.require(manifest['schema'] == 'pid-rs/dnf-order-portable-replay-v1'
              and manifest['historical_judge_freeze_sha256'] == FREEZE_SHA256,
              'unsupported public routing revision')
    files = manifest['files']
    j.require(type(files) is dict and all(type(name) is str and not Path(name).is_absolute()
              and '..' not in Path(name).parts for name in files), 'invalid public file roster')
    captured = {}
    for name, expected in files.items():
        data = snapshot.read(HERE / name)
        j.require(type(expected) is str and j.digest(data) == expected,
                  'public routing input changed: ' + name)
        captured[name] = data
    j.require(captured.get('replay.py') == snapshot.read(Path(__file__)), 'launcher absent from manifest')
    freeze = j.check_freeze(snapshot, FREEZE_SHA256)
    selected = captured['Candidate.lean']
    j.require(j.digest(selected) == SELECTED_SHA256
              and captured['Contract.lean'] == captured['judge-v3/Contract.lean'],
              'accepted source or contract identity changed')
    root = args.root.absolute()
    j.require(root == root.resolve(strict=True) and root.is_dir(), 'repository root must be canonical')
    j.require(re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', args.run_name) is not None, 'invalid run name')
    j.require(args.action == 'check' or args.source == 'selected', 'source selection applies only to check')
    if args.action == 'reporting-regression':
        j.require(args.accepted_run is not None and args.accepted_receipt_sha256 is not None,
                  'reporting regression requires an accepted run and its exact receipt digest')
    else:
        j.require(args.accepted_run is None and args.accepted_receipt_sha256 is None,
                  'accepted-run arguments apply only to reporting regression')
    runtime_parent = root / RUNTIME_RELATIVE
    j.require(runtime_parent == runtime_parent.resolve(), 'runtime parent contains a symbolic link')
    destination = runtime_parent / args.run_name
    destination.mkdir(parents=True, exist_ok=False)
    stage = destination / 'judge-v3'
    stage.mkdir()
    for name in (*freeze['files'], 'frozen.json'):
        (stage / name).write_bytes(captured['judge-v3/' + name])
    supplement = 'reporting-regression-repaired-candidate.py'
    (stage / supplement).write_bytes(captured['supplemental/' + supplement])
    source = destination / 'Candidate.lean'
    candidate = COSMETIC_PREFIX + selected if args.source == 'cosmetic' else selected
    expected_candidate = COSMETIC_SHA256 if args.source == 'cosmetic' else SELECTED_SHA256
    j.require(j.digest(candidate) == expected_candidate, 'declared source transform changed')
    source.write_bytes(candidate)
    output = stage / 'runs/replay'
    python = str(Path(sys.executable).resolve(strict=True))
    flags = ['-I', '-S', '-B'] + (['-O'] if sys.flags.optimize else [])
    if args.action == 'check':
        command = [python, *flags, str(stage / 'judge.py'), str(root), str(source), str(output),
                   '--candidate-sha256', expected_candidate, '--freeze-sha256', FREEZE_SHA256]
    elif args.action == 'self-test':
        command = [python, *flags, str(stage / 'selftest.py'), str(root), str(output)]
    else:
        command = [python, *flags, str(stage / supplement), str(args.accepted_run.absolute()), str(output),
                   '--accepted-receipt-sha256', args.accepted_receipt_sha256,
                   '--freeze-sha256', FREEZE_SHA256]
    # Verify original captures and staged byte copies before executing the unchanged entry point.
    snapshot.verify()
    for name in (*freeze['files'], 'frozen.json'):
        j.require(snapshot.read(stage / name) == captured['judge-v3/' + name], 'staged judge changed')
    j.require(snapshot.read(stage / supplement) == captured['supplemental/' + supplement], 'staged supplement changed')
    j.require(snapshot.read(source) == candidate, 'staged candidate changed')
    plan = {'schema': 'pid-rs/dnf-order-portable-routing-plan-v1',
            'status': 'prepared_no_lean_execution', 'action': args.action,
            'python_optimized': sys.flags.optimize, 'command': command,
            'manifest_sha256': args.manifest_sha256, 'historical_judge_freeze_sha256': FREEZE_SHA256,
            'candidate_sha256': expected_candidate,
            'scope': 'New routing replay, separate from the completed September 2026 candidate campaign.'}
    (destination / 'routing-plan.json').write_bytes(j.canonical(plan))
    snapshot.save(destination)
    snapshot.verify()
    if args.prepare_only:
        print(j.canonical({'status': plan['status'], 'plan': str(destination / 'routing-plan.json')}).decode(), end='')
        return 0
    os.execv(python, command)
    raise RuntimeError('process replacement unexpectedly returned')


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print('DNF/order public replay refused: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
