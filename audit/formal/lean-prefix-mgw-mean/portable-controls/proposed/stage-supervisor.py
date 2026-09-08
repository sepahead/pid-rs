#!/usr/bin/env python3
"""Cooperative POSIX stage supervision, usable on macOS and Linux.

This is not a sandbox, atomic process census, or hard real-time deadline.
Only an owned, unreaped wrapper process group is signalled. The unchanged
Runtime handles its separately sessioned compiler group on SIGTERM. Observed
surviving descendants, missing receipts, late closure and cleanup uncertainty
fail closed. A failed cleanup is retained, not relabelled as successful killing.
"""
from __future__ import annotations
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

ADAPTER_SHA = '121068917f2cdc0e3b3098c63869227be9511d7df5f9c011d3d68f980308220a'
MANIFEST_SHA = 'acc59640c0f135063bd58b8827ffc9d058e3d3a82d0e1ab0f980fad881d4b618'
STREAM_CAP = 4 * 1024**2
OBSERVATION_CAP = 8 * 1024**2
PRODUCTION_CLEANUP_RESERVE = 45.0


def require(value, message):
    if not value:
        raise RuntimeError(message)


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def utc():
    return dt.datetime.now(dt.timezone.utc)


def observe(wrapper_pid, known):
    observed = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,lstart=,stat='],
                              env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'},
                              stdin=subprocess.DEVNULL, capture_output=True, timeout=2, check=False)
    require(observed.returncode == 0 and not observed.stderr, 'process observation failed')
    rows = {}
    for line in observed.stdout.decode('ascii').splitlines():
        fields = line.split()
        require(len(fields) == 9, 'unexpected process observation shape')
        pid, ppid, group = map(int, fields[:3])
        rows[pid] = {'pid': pid, 'ppid': ppid, 'pgid': group,
                     'observed_start_label': ' '.join(fields[3:8]), 'state': fields[8]}
    selected = {wrapper_pid}
    # lstart is an observation label, not a cryptographic/PID-generation
    # identity. It is never used to authorize a kill of a non-owned PID.
    for pid, label in known.items():
        if pid in rows and rows[pid]['observed_start_label'] == label:
            selected.add(pid)
    changed = True
    while changed:
        before = len(selected)
        selected.update(pid for pid, row in rows.items() if row['ppid'] in selected)
        changed = len(selected) != before
    groups = {rows[pid]['pgid'] for pid in selected if pid in rows}
    selected.update(pid for pid, row in rows.items() if row['pgid'] in groups)
    found = [rows[pid] for pid in sorted(selected) if pid in rows and not rows[pid]['state'].startswith('Z')]
    for row in found:
        known[row['pid']] = row['observed_start_label']
    return found


def supervise(command, cwd, stage, output, deadline, cutoff, reserve):
    require(not (stage / 'STOP_RECORD.json').exists(), 'stage already stopped')
    require(utc() < deadline - dt.timedelta(seconds=reserve) and time.monotonic() < cutoff - reserve,
            'no supervisory admission window remains')
    record = {'status': 'failed', 'command': command, 'cwd': str(cwd),
              'registered_utc': utc().isoformat(), 'deadline_utc': deadline.isoformat(),
              'cleanup_reserve_seconds': reserve, 'observations_are_atomic': False,
              'deadline_is_hard_real_time': False, 'known_processes': {}}
    output.mkdir()
    (output / 'REGISTERED.json').write_bytes(canonical(record))
    process = None; selector = selectors.DefaultSelector(); known = {}
    stdout, stderr = bytearray(), bytearray()
    failure = None; stop_sent = False; observations = []; previous = None
    observation_bytes = 0; next_observation = time.monotonic()
    old_handlers = {}
    def interrupted(signum, frame):
        raise RuntimeError('supervisor interrupted by signal ' + str(signum))
    def stop(reason):
        nonlocal stop_sent, failure
        failure = failure or reason
        if not stop_sent:
            path = stage / 'STOP_RECORD.json'
            if not path.exists():
                with path.open('xb') as stream:
                    stream.write(canonical({'reason': reason, 'observed_utc': utc().isoformat(),
                                            'owner': 'portable mean stage supervisor'}))
                    stream.flush(); os.fsync(stream.fileno())
            # Popen.returncode is checked without reaping here. A group is never
            # signalled after this supervisor has reaped its owned leader.
            if process is not None and process.returncode is None:
                try: os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError: pass
            stop_sent = True
    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            old_handlers[signum] = signal.signal(signum, interrupted)
        # The source/plan hashes were read before this check. Scheduling can
        # intervene between this observation and Popen; no atomicity is claimed.
        require(utc() < deadline - dt.timedelta(seconds=reserve) and time.monotonic() < cutoff - reserve,
                'deadline before wrapper spawn')
        process = subprocess.Popen(command, cwd=cwd, env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'},
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
        record['owned_wrapper_pid'] = process.pid
        (output / 'PID.json').write_bytes(canonical({'pid': process.pid, 'pgid': process.pid,
                                                   'observed_utc': utc().isoformat(),
                                                   'ownership': 'direct Popen child; leader retained until wait'}))
        for stream, target in ((process.stdout, stdout), (process.stderr, stderr)):
            os.set_blocking(stream.fileno(), False); selector.register(stream, selectors.EVENT_READ, target)
        while selector.get_map() or process.poll() is None:
            now = time.monotonic()
            if now >= cutoff - reserve or utc() >= deadline - dt.timedelta(seconds=reserve):
                stop('supervisory cleanup interval reached')
            if (stage / 'STOP_RECORD.json').exists(): stop('stage stop record observed')
            if now >= next_observation:
                current = observe(process.pid, known)
                if current != previous:
                    entry = {'observed_utc': utc().isoformat(), 'processes': current}
                    observation_bytes += len(canonical(entry))
                    if observation_bytes > OBSERVATION_CAP:
                        stop('supervisor process observation cap exhausted')
                    else:
                        observations.append(entry); previous = current
                next_observation = time.monotonic() + 0.1
            if now >= cutoff or utc() >= deadline:
                stop('original stage deadline reached')
                if process.returncode is None:
                    try: os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                failure = 'deadline or cleanup failure; separate Runtime groups require recorded survivor review'
                break
            for key, _ in selector.select(0.025):
                raw = os.read(key.fileobj.fileno(), 65536)
                if not raw:
                    selector.unregister(key.fileobj); key.fileobj.close(); continue
                available = STREAM_CAP - len(key.data)
                key.data.extend(raw[:available])
                if len(raw) > available: stop('supervisor stream byte cap exhausted')
        # The owned wrapper may already be reaped by poll. No group is signalled
        # past that point. Separate groups are observed, never blindly killed.
        # A failed stage still gets a bounded reap attempt. Cleanup may finish
        # after its original deadline; every such closure remains failed.
        process.wait(timeout=2.0)
        record['returncode'] = process.returncode
        survivors = observe(process.pid, known)
        record['observed_survivors'] = survivors
        if survivors: failure = failure or 'observed descendants survived wrapper termination'
        if process.returncode != 0: failure = failure or 'wrapper returned nonzero'
        if stderr: failure = failure or 'wrapper wrote stderr'
        if utc() >= deadline or time.monotonic() >= cutoff: failure = failure or 'late wrapper closure'
        if failure is None: record['status'] = 'observed_wrapper_completion_pending_receipt_review'
    except BaseException as error:
        failure = failure or repr(error)
        try: stop('supervisor exception')
        except BaseException as stop_error: record['stop_error'] = repr(stop_error)
    finally:
        for key in list(selector.get_map().values()): key.fileobj.close()
        selector.close()
        for signum, handler in old_handlers.items(): signal.signal(signum, handler)
        if process is not None and process.returncode is None:
            # Do not invent successful cleanup if an unresponsive native/OS
            # operation exceeds this observation window.
            record['cleanup_incomplete'] = True
            record['unreaped_owned_wrapper_pid'] = process.pid
        record['failure'] = failure
        record['known_processes'] = {str(k): v for k, v in known.items()}
        record['completed_utc'] = utc().isoformat()
        (output / 'stdout.log').write_bytes(stdout); (output / 'stderr.log').write_bytes(stderr)
        (output / 'PROCESS_OBSERVATIONS.json').write_bytes(canonical(observations))
        if failure is not None: record['status'] = 'failed'
        if utc() >= deadline: record.update(status='failed', finalization_failure='supervisor closure reached original deadline')
        (output / 'RESULT.json').write_bytes(canonical(record))
        if utc() >= deadline:
            record.update(status='failed', finalization_failure='original deadline reached during wrapper result write')
            (output / 'RESULT.json').write_bytes(canonical(record))
    return record


def main():
    require(sys.version_info >= (3, 11) and sys.flags.isolated and sys.flags.no_site and
            sys.dont_write_bytecode and sys.flags.optimize in (0, 1), 'requires Python 3.11+ -I -S -B, optional -O')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    raw = args.plan.read_bytes(); require(digest(raw) == args.plan_sha256, 'supervisor plan digest differs')
    plan = json.loads(raw)
    require(plan['schema'] in {'portable-mean-supervisor-plan-v1', 'portable-mean-supervisor-control-plan-v1'}, 'plan schema differs')
    controls = plan['schema'].endswith('control-plan-v1')
    require(plan['status'] == 'root-reviewed-ready-to-execute', 'supervisor plan is not reviewed')
    require(digest(Path(__file__).read_bytes()) == plan['supervisor_sha256'], 'supervisor source differs')
    stage, root = (Path(plan[key]).absolute() for key in ('stage', 'root'))
    require(stage == stage.resolve(strict=True) and root == root.resolve(strict=True), 'noncanonical supervisor root/stage')
    registration_raw = (stage / 'REGISTRATION.json').read_bytes()
    require(digest(registration_raw) == plan['registration_sha256'], 'supervised registration changed')
    registration = json.loads(registration_raw)
    start, deadline = (dt.datetime.fromisoformat(registration[key]) for key in ('registered_utc', 'deadline_utc'))
    now = utc()
    require(start.tzinfo is not None and deadline.tzinfo is not None and start <= now < deadline, 'invalid supervisor clock')
    reserve = 2.0 if controls else PRODUCTION_CLEANUP_RESERVE
    if controls:
        require(dt.timedelta(seconds=3) <= deadline - start <= dt.timedelta(seconds=120), 'supervisor control interval differs')
        require(type(plan['new_mean_theorems_proved']) is int and plan['new_mean_theorems_proved'] == 0,
                'supervisor controls carry no theorem credit')
        child = Path(plan['fixture_child']).resolve(strict=True)
        require(child.name == 'supervisor-child.py' and digest(child.read_bytes()) == plan['fixture_child_sha256'], 'fixture child differs')
        commands = [[sys.executable, '-I', '-S', '-B', *(['-O'] if sys.flags.optimize else []),
                     str(child), '--mode', plan['fixture_mode'], '--stage', str(stage)]]
    else:
        require(deadline - start == dt.timedelta(minutes=120), 'production stage is not the fixed 120-minute interval')
        adapter = Path(plan['adapter']).resolve(strict=True)
        require(digest(adapter.read_bytes()) == ADAPTER_SHA and digest((adapter.parent / 'replay-proposed-v1.json').read_bytes()) == MANIFEST_SHA,
                'reviewed adapter or manifest differs')
        require(registration['manifest_sha256'] == MANIFEST_SHA, 'registration does not bind manifest')
        prefix = Path(plan['toolchain_prefix']).resolve(strict=True)
        common = [str(adapter), '--root', str(root), '--stage', str(stage), '--manifest-sha256', MANIFEST_SHA,
                  '--registration-sha256', plan['registration_sha256'], '--toolchain-prefix', str(prefix)]
        commands = []
        for source, mode, action in [('selected', 0, 'check'), ('selected', 1, 'check'),
                                     ('cosmetic', 0, 'check'), ('cosmetic', 1, 'check'),
                                     ('selected', 0, 'wrong-last-target')]:
            commands.append([sys.executable, '-I', '-S', '-B', *(['-O'] if mode else []),
                             *common, '--source', source, '--action', action])
    cutoff = time.monotonic() + (deadline - now).total_seconds()
    output = args.output.absolute()
    require(output.parent == output.parent.resolve(strict=True) and '.local' in output.parts and not output.exists(),
            'fresh ignored supervisor output required')
    output.mkdir(); (output / 'PLAN.executed.json').write_bytes(raw)
    lock = (stage / 'SUPERVISOR.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    result = {'status': 'failed', 'scope': 'observed replay execution; root review still required',
              'controls': controls, 'records': []}
    try:
        for index, command in enumerate(commands):
            record = supervise(command, root, stage, output / ('wrapper-' + str(index).zfill(2)), deadline, cutoff, reserve)
            result['records'].append(record)
            require(record['status'] == 'observed_wrapper_completion_pending_receipt_review', 'supervised wrapper failed')
            require(digest((stage / 'REGISTRATION.json').read_bytes()) == plan['registration_sha256'], 'stage registration drifted')
            if not controls:
                transport = json.loads((output / ('wrapper-' + str(index).zfill(2)) / 'stdout.log').read_bytes())
                attempt = Path(transport['output'])
                require(attempt.parent == stage and attempt == attempt.resolve(strict=True), 'adapter receipt path differs')
                receipt = json.loads((attempt / 'RESULT.json').read_bytes())
                expected = 'expected_target_rejection' if index == 4 else 'fresh_semantic_kernel_pass'
                require(receipt['status'] == transport['status'] == expected, 'adapter terminal receipt differs')
                require(dt.datetime.fromisoformat(receipt['completed_utc']) < deadline, 'adapter receipt was late')
                record['adapter_receipt_sha256'] = digest((attempt / 'RESULT.json').read_bytes())
        require(utc() < deadline and time.monotonic() < cutoff and not (stage / 'STOP_RECORD.json').exists(), 'late or stopped supervisor closure')
        result['status'] = 'observed_expected_completion_not_adopted'
    except BaseException as error:
        result['failure'] = repr(error)
    finally:
        result['completed_utc'] = utc().isoformat()
        if utc() >= deadline: result.update(status='failed', finalization_failure='late supervisor closure')
        (output / 'RESULT.json').write_bytes(canonical(result))
        if utc() >= deadline:
            result.update(status='failed', finalization_failure='original deadline reached during supervisor result write')
            (output / 'RESULT.json').write_bytes(canonical(result))
        lock.close()
    return 0 if result['status'] == 'observed_expected_completion_not_adopted' else 1


if __name__ == '__main__':
    raise SystemExit(main())
