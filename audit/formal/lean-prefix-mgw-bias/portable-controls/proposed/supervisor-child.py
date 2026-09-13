#!/usr/bin/env python3
"""Bounded inert supervisor fixture. Never accepts a Lean executable argument."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import ModuleType

HERE = Path(__file__).resolve().parent
RUNTIME_SHA = 'bd8a9f2272a20422863c9902ce2148d2957471bb958d13949fece923cb6a7f5d'


def write(path, value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value, sort_keys=True, indent=2) + '\n').encode())
        stream.flush(); os.fsync(stream.fileno())


def main():
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and sys.flags.optimize in (0, 1)):
        raise RuntimeError('requires isolated Python -I -S -B, optional -O')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', required=True, choices=('success', 'failure', 'worker', 'preflight-delay',
                                                        'runtime-hash-delay', 'runtime-child-delay', 'finalization-delay'))
    parser.add_argument('--stage', required=True, type=Path)
    args = parser.parse_args(); stage = args.stage.resolve(strict=True)
    if args.mode == 'success':
        write(stage / 'FIXTURE_COMPLETED.json', {'status': 'inert_success', 'pid': os.getpid()})
        return 0
    if args.mode == 'failure': return 3
    if args.mode == 'worker':
        write(stage / 'WORKER_PID.json', {'pid': os.getpid(), 'ppid': os.getppid(), 'pgid': os.getpgid(0)})
        time.sleep(15)  # Autonomous bound also limits an unexpectedly orphaned fixture.
        return 0
    command = [sys.executable, '-I', '-S', '-B', str(Path(__file__).resolve()), '--mode', 'worker', '--stage', str(stage)]
    if args.mode == 'preflight-delay':
        # The exact base helper's Git command uses an ordinary subprocess group.
        # This fixture exercises that ownership shape, not Git authenticity.
        child = subprocess.Popen(command, start_new_session=False)
        write(stage / 'PREFLIGHT_CHILD.json', {'pid': child.pid, 'group': os.getpgid(child.pid)})
        return child.wait(timeout=18)
    if args.mode == 'finalization-delay':
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        write(stage / 'FINALIZATION_STARTED.json', {'pid': os.getpid()})
        time.sleep(15)
        write(stage / 'LATE_FIXTURE_COMPLETED.json', {'status': 'deliberately_late'})
        return 0
    runtime_path = HERE.parent / 'inputs/package/replay-support/runtime.py'
    raw = runtime_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != RUNTIME_SHA: raise RuntimeError('runtime fixture pin differs')
    j = ModuleType('unchanged_runtime_supervisor_control'); j.__file__ = str(runtime_path)
    exec(compile(raw, str(runtime_path), 'exec', dont_inherit=True, optimize=sys.flags.optimize), j.__dict__)
    src, output = stage / 'runtime-src', stage / 'runtime-output'
    src.mkdir(); output.mkdir(); (src / 'Inert.lean').write_bytes(b'-- inert hash input; never compiled\n')
    if args.mode == 'runtime-hash-delay':
        original = j.register_child
        def delayed(*values, **keywords):
            record = original(*values, **keywords)
            write(stage / 'ACTUAL_RUNTIME_HASH_COMPLETED.json', {'source_inputs': record['source_inputs']})
            time.sleep(15)
            return record
        j.register_child = delayed
    runner = j.Runner(output, {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}, preparation=False)
    failure = None
    try:
        runner.run(command, src, 'inert-python-worker', timeout=18)
    except BaseException as error:
        failure = repr(error)
    write(stage / 'RUNTIME_CONTROL_RESULT.json', {'failure': failure, 'commands': runner.commands,
                                                'scope': 'unchanged Runtime with inert Python child, zero Lean'})
    return 0 if failure is None else 3


if __name__ == '__main__':
    raise SystemExit(main())
