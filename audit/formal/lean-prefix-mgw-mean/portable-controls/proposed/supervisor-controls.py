#!/usr/bin/env python3
"""Causal macOS/Linux supervisory controls; root review required before use."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
CASES = ('success', 'failure', 'preflight-delay', 'runtime-hash-delay', 'runtime-child-delay', 'finalization-delay')


def require(value, message):
    if not value: raise RuntimeError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.write_bytes((json.dumps(value, sort_keys=True, indent=2) + '\n').encode())


def main():
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and sys.flags.optimize in (0, 1),
            'requires Python -I -S -B, optional -O')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', required=True, type=Path)
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    raw = args.registration.read_bytes(); require(digest(raw) == args.registration_sha256, 'control registration differs')
    registration = json.loads(raw)
    require(registration['schema'] == 'portable-mean-supervisor-controls-execution-v1'
            and registration['status'] == 'root-reviewed-source-ready-for-controls'
            and type(registration['new_mean_theorems_proved']) is int
            and registration['new_mean_theorems_proved'] == 0, 'supervisor controls lack reviewed registration')
    start, deadline = (dt.datetime.fromisoformat(registration[key]) for key in ('registered_utc', 'deadline_utc'))
    now = dt.datetime.now(dt.timezone.utc)
    require(start.tzinfo is not None and deadline.tzinfo is not None and start <= now < deadline
            and deadline - start <= dt.timedelta(minutes=15), 'invalid supervisor control clock')
    cutoff = time.monotonic() + (deadline - now).total_seconds()
    for name in ('supervisor-controls.py', 'stage-supervisor.py', 'supervisor-child.py'):
        require(digest((HERE / name).read_bytes()) == registration['source_sha256'][name], 'supervisor control source differs: ' + name)
    output = args.output.absolute()
    require(output.parent == output.parent.resolve(strict=True) and '.local' in output.parts and not output.exists(),
            'fresh ignored control output required')
    output.mkdir(); write(output / 'EXECUTION_REGISTRATION.json', registration)
    result = {'status': 'failed', 'new_mean_theorems_proved': 0,
              'scope': 'actual supervisor and unchanged Runtime against bounded inert Python processes', 'records': []}
    try:
        for mode in (0, 1):
            for name in CASES:
                require(cutoff - time.monotonic() > 25, 'insufficient remaining time for a bounded causal fixture')
                directory = output / (str(mode) + '-' + name); directory.mkdir()
                stage = directory / 'stage'; stage.mkdir()
                born = dt.datetime.now(dt.timezone.utc)
                task = {'registered_utc': born.isoformat(), 'deadline_utc': (born + dt.timedelta(seconds=8)).isoformat(),
                        'owner': 'synthetic supervisor control'}
                write(stage / 'REGISTRATION.json', task)
                plan = {'schema': 'portable-mean-supervisor-control-plan-v1', 'status': 'root-reviewed-ready-to-execute',
                        'root': str(directory), 'stage': str(stage), 'fixture_mode': name,
                        'fixture_child': str(HERE / 'supervisor-child.py'),
                        'fixture_child_sha256': digest((HERE / 'supervisor-child.py').read_bytes()),
                        'supervisor_sha256': digest((HERE / 'stage-supervisor.py').read_bytes()),
                        'registration_sha256': digest((stage / 'REGISTRATION.json').read_bytes()),
                        'new_mean_theorems_proved': 0}
                write(directory / 'PLAN.json', plan)
                command = [sys.executable, '-I', '-S', '-B', *(['-O'] if mode else []), str(HERE / 'stage-supervisor.py'),
                           '--plan', str(directory / 'PLAN.json'), '--plan-sha256', digest((directory / 'PLAN.json').read_bytes()),
                           '--output', str(directory / 'supervised')]
                write(directory / 'COMMAND.json', {'command': command, 'registered_utc': dt.datetime.now(dt.timezone.utc).isoformat()})
                with (directory / 'stdout.log').open('xb') as stdout, (directory / 'stderr.log').open('xb') as stderr:
                    terminal = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                              timeout=20, check=False, env={'PATH': '/usr/bin:/bin'})
                receipt = json.loads((directory / 'supervised/RESULT.json').read_bytes())
                good = name == 'success'
                require(terminal.returncode == (0 if good else 1), name + ': expected supervisory exit differs')
                require(receipt['status'] == ('observed_expected_completion_not_adopted' if good else 'failed'),
                        name + ': expected supervisory disposition differs')
                require(len(receipt['records']) == 1, name + ': missing per-wrapper retained record')
                wrapper = receipt['records'][0]
                require(not wrapper.get('cleanup_incomplete') and not wrapper.get('observed_survivors'),
                        name + ': expected refusal left incomplete or observed surviving cleanup')
                if name in {'preflight-delay', 'runtime-hash-delay', 'runtime-child-delay'}:
                    require(wrapper['failure'] == 'supervisory cleanup interval reached',
                            name + ': refusal was not caused by the registered cleanup interval')
                if name == 'failure': require(wrapper.get('returncode') == 3, 'nonzero fixture cause differs')
                if name == 'finalization-delay':
                    require('deadline or cleanup failure' in str(wrapper['failure']),
                            'late-finalization refusal missed the original deadline cause')
                if name == 'preflight-delay':
                    child = json.loads((stage / 'PREFLIGHT_CHILD.json').read_bytes())
                    require(child['group'] == wrapper['owned_wrapper_pid'], 'Git-shaped child did not share wrapper group')
                    require(not wrapper.get('observed_survivors'), 'preflight fixture left observed survivors')
                if name == 'runtime-hash-delay':
                    require((stage / 'ACTUAL_RUNTIME_HASH_COMPLETED.json').exists() and not (stage / 'WORKER_PID.json').exists(),
                            'delayed actual Runtime hash did not stop before fixture child execution')
                if name == 'runtime-child-delay':
                    worker = json.loads((stage / 'WORKER_PID.json').read_bytes())
                    require(worker['pgid'] == worker['pid'] and worker['pgid'] != wrapper['owned_wrapper_pid'],
                            'actual Runtime did not establish a separate child session/group')
                    runtime = json.loads((stage / 'RUNTIME_CONTROL_RESULT.json').read_bytes())
                    require(runtime['failure'] and len(runtime['commands']) == 1,
                            'actual Runtime interrupt evidence absent')
                    require(runtime['commands'][0]['remaining_live_group_processes'] == [],
                            'actual Runtime did not observe clean child-group closure')
                    require(not wrapper.get('observed_survivors'), 'outer supervisor observed a surviving runtime child')
                if name == 'finalization-delay':
                    require((stage / 'FINALIZATION_STARTED.json').exists() and not (stage / 'LATE_FIXTURE_COMPLETED.json').exists(),
                            'finalization-delay control was admitted late')
                result['records'].append({'mode': mode, 'case': name, 'status': 'matched_expected_behavior',
                                          'receipt_sha256': digest((directory / 'supervised/RESULT.json').read_bytes())})
        require(dt.datetime.now(dt.timezone.utc) < deadline and time.monotonic() < cutoff, 'late supervisor control closure')
        result['status'] = 'controls_matched_expected_behavior_not_adopted'
    except BaseException as error:
        result['failure'] = repr(error)
    finally:
        result['completed_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        if dt.datetime.now(dt.timezone.utc) >= deadline: result.update(status='failed', finalization_failure='original control deadline reached')
        write(output / 'RESULT.json', result)
        if dt.datetime.now(dt.timezone.utc) >= deadline:
            result.update(status='failed', finalization_failure='original deadline reached during control result write')
            write(output / 'RESULT.json', result)
    return 0 if result['status'] == 'controls_matched_expected_behavior_not_adopted' else 1


if __name__ == '__main__':
    raise SystemExit(main())
