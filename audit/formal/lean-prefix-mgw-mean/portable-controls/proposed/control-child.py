#!/usr/bin/env python3
"""Whole unchanged adapter control driver. Synthetic routing, zero proof credit.

The trace hook changes only the loaded Runtime Runner and external helper
preflight operations. Real Snapshot, helper import, source policies and record
parsers execute. An audit hook denies every attempted external process.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

ADAPTER_SHA = '121068917f2cdc0e3b3098c63869227be9511d7df5f9c011d3d68f980308220a'


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def main():
    job_path = Path(sys.argv[1]).resolve(strict=True)
    job = json.loads(job_path.read_bytes())
    adapter = Path(job['adapter']).resolve(strict=True)
    if hashlib.sha256(adapter.read_bytes()).hexdigest() != ADAPTER_SHA:
        raise RuntimeError('control driver adapter identity differs')
    stage = Path(job['stage'])
    case = job['case']
    report = {'scope': 'synthetic whole-entrypoint routing; no Lean process and no proof credit',
              'adapter_sha256': ADAPTER_SHA, 'events': [], 'patched_interfaces': [],
              'mode': sys.flags.optimize, 'external_process_attempts': []}
    state = {'clock': dt.datetime.fromisoformat(job['now']), 'runtime': None,
             'globals': None, 'verify_count': 0, 'save_count': 0}

    def event(kind, **fields):
        report['events'].append(dict(kind=kind, **fields))

    def expired():
        state['clock'] += dt.timedelta(hours=3)

    def audit(name, args):
        if name in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp',
                    'os.exec', 'os.fork', 'os.forkpty', 'pty.spawn'}:
            report['external_process_attempts'].append(name)
            raise RuntimeError('CONTROL DENIES EXTERNAL EXECUTION: ' + name)

    sys.addaudithook(audit)

    def patch_runtime(j):
        state['runtime'] = j
        report['patched_interfaces'] += ['runtime.Runner', 'runtime.load_helpers external-preflight wrapper']
        actual_helpers = j.load_helpers

        def helpers(root, snapshot):
            helper, base = actual_helpers(root, snapshot)
            for name in ('check_toolchain', 'check_lakefile', 'check_manifest',
                         'find_git', 'run_git', 'check_dependency_checkouts'):
                report['patched_interfaces'].append('base.' + name)
            def checked(name):
                def call(*args, **kwargs):
                    event('preflight', operation=name)
                    if case == 'preflight-error' and name == 'check_manifest':
                        raise RuntimeError('synthetic preflight failure')
                    if name == 'check_dependency_checkouts' and case == 'preflight-expiry':
                        expired()
                    if name == 'find_git':
                        return '/inert/git'
                    if name == 'run_git':
                        return str(root) + '\n'
                    return None
                return call
            for name in ('check_toolchain', 'check_lakefile', 'check_manifest',
                         'find_git', 'run_git', 'check_dependency_checkouts'):
                setattr(base, name, checked(name))
            return helper, base
        j.load_helpers = helpers

        actual_verify, actual_save = j.Snapshot.verify, j.Snapshot.save
        def verify(snapshot):
            actual_verify(snapshot)
            state['verify_count'] += 1
            if case == 'expiry-after-rehash' and state['verify_count'] == 1:
                expired()
            if case == 'stop-after-rehash' and state['verify_count'] == 1:
                (stage / 'STOP_RECORD.json').write_bytes(canonical({'synthetic': True}))
        def save(snapshot, output):
            actual_save(snapshot, output)
            state['save_count'] += 1
            if case == 'finalization-expiry':
                expired()
            if case == 'finalization-stop':
                (stage / 'STOP_RECORD.json').write_bytes(canonical({'synthetic': True}))
            if case == 'finalization-input-drift':
                with (stage / 'REGISTRATION.json').open('ab') as stream:
                    stream.write(b' ')
            if case == 'finalization-artifact-link':
                (output / 'synthetic-artifact-link').symlink_to(output / 'Candidate.original.lean')
            if case == 'finalization-save-error':
                raise RuntimeError('synthetic evidence preservation failure')
        if case in {'expiry-after-rehash', 'stop-after-rehash'}:
            j.Snapshot.verify = verify
            report['patched_interfaces'].append('Snapshot.verify: delegate then causal injection')
        if case.startswith('finalization-'):
            j.Snapshot.save = save
            report['patched_interfaces'].append('Snapshot.save: delegate then causal injection')

        package = adapter.parent
        mean = json.loads((package / 'replay-support/EXPECTED_MEAN_RECORDS.json').read_bytes())
        deps = json.loads((package / 'replay-support/ACCEPTED_DEPENDENCY_RECORDS.json').read_bytes())
        def encode(values, prefix):
            return b''.join(prefix.encode() + json.dumps(v, sort_keys=True).encode() + b'\n' for v in values)
        streams = {
            'compile-PidPrefixMgwMean-SemanticJudge': encode(mean, 'PREFIX_MGW_MEAN_JUDGE_RESULT '),
            'compile-PidPrefixProbability-SemanticJudge': encode(deps['accepted_prefix_dependency'], 'PREFIX_PROBABILITY_JUDGE_RESULT '),
            'compile-PidMgwBridge-SemanticJudge': encode(deps['accepted_mgw_dependency'], 'MGW_BRIDGE_JUDGE_RESULT '),
        }
        # Independent literal record transports above are reviewed against each
        # retained parser. The expected arrays are exact accepted input bytes.
        class InertRunner:
            def __init__(self, output, environment, *, preparation=False):
                self.output, self.environment, self.commands = output, environment, []
                event('runner-created', preparation=preparation)

            def run(self, command, cwd, label, *, timeout, allow_stdout=False):
                event('runner-call', command=command, label=label, timeout=timeout,
                      allow_stdout=allow_stdout)
                if not 0 < timeout <= (60 if label == 'tool-version' else 600):
                    raise RuntimeError('control observed invalid caller timeout')
                directory = self.output / (str(len(self.commands)).zfill(2) + '-' + label)
                directory.mkdir()
                raw = streams.get(label, b'')
                if label == 'tool-version':
                    raw = b'Lean (version 4.33.0, aarch64-apple-darwin, commit d8b18978322de05a8f3dba51ef03cf5461676c17, Release)\n'
                if case == 'version-malformed' and label == 'tool-version':
                    raw = b'Lean synthetic wrong version\n'
                if case == 'dispatch-six-as-mean' and label == 'compile-PidPrefixMgwMean-SemanticJudge':
                    raw = streams['compile-PidPrefixProbability-SemanticJudge']
                if case == 'dispatch-eleven-as-prefix' and label == 'compile-PidPrefixProbability-SemanticJudge':
                    raw = streams['compile-PidMgwBridge-SemanticJudge']
                if case == 'dispatch-three-as-mgw' and label == 'compile-PidMgwBridge-SemanticJudge':
                    raw = streams['compile-PidPrefixMgwMean-SemanticJudge']
                if case == 'mean-reordered' and label == 'compile-PidPrefixMgwMean-SemanticJudge':
                    raw = encode(list(reversed(mean)), 'PREFIX_MGW_MEAN_JUDGE_RESULT ')
                if case == 'mean-type-drift' and label == 'compile-PidPrefixMgwMean-SemanticJudge':
                    values = json.loads(json.dumps(mean)); values[0]['full_elaborated_type'] += ' synthetic drift'
                    raw = encode(values, 'PREFIX_MGW_MEAN_JUDGE_RESULT ')
                failure, code, stderr = None, 0, b''
                if case == 'compiler-operational-failure' and label.startswith('compile-'):
                    failure, code = 'synthetic_timeout', None
                wrong = job['action'] == 'wrong-last-target' and label == 'compile-PidPrefixMgwMean-SemanticJudge'
                if wrong and case != 'wrong-final-accepted':
                    raw = encode(mean[:2], 'PREFIX_MGW_MEAN_JUDGE_RESULT ')
                    raw += b'DNF_JUDGE_TARGET_TYPE type mismatch PidPrefixMgwMeanRawTargets.prefix_expectations_to_mgw_mean PidPrefixMgwMeanAliasTargets.prefix_expectations_to_mgw_mean\n'
                    code = 1
                    if case == 'wrong-final-operational': failure = 'synthetic_timeout'
                    if case == 'wrong-final-stderr': stderr = b'synthetic stderr\n'
                    if case == 'wrong-final-missing-marker': raw = raw.replace(b'DNF_JUDGE_TARGET_TYPE', b'OTHER')
                    if case == 'wrong-final-missing-prefix': raw = raw.split(b'\n', 1)[1]
                if code == 0 and '-o' in command:
                    Path(command[command.index('-o') + 1]).write_bytes(b'SYNTHETIC CONTROL, NOT AN OLEAN\n')
                (directory / 'stdout.log').write_bytes(raw)
                (directory / 'stderr.log').write_bytes(stderr)
                record = {'label': label, 'command': command, 'failure': failure,
                          'returncode': code, 'retained_stderr_bytes': len(stderr),
                          'synthetic': True, 'timeout': timeout}
                self.commands.append(record)
                (directory / 'command.json').write_bytes(canonical(record))
                if case == 'stop-between-children' and label == 'tool-version':
                    (stage / 'STOP_RECORD.json').write_bytes(canonical({'synthetic': True}))
                if failure or code != 0 or stderr:
                    raise j.JudgeError('synthetic runner rejection')
                return raw
        j.Runner = InertRunner

        if case == 'runtime-hash-gap':
            # Exercise the unchanged Runtime.run and actual register_child hash
            # phase. Substitute only its OS spawn boundary; no child executes.
            j.Runner = original_runner
            original_registration = j.register_child
            def registered(*args, **kwargs):
                record = original_registration(*args, **kwargs)
                expired()
                event('runtime-hash-phase-completed-after-deadline')
                return record
            def denied_spawn(*args, **kwargs):
                event('runtime-spawn-boundary-reached-after-deadline',
                      observed_utc=state['clock'].isoformat())
                raise RuntimeError('synthetic delayed-hash spawn boundary; no child launched')
            j.register_child = registered
            j.subprocess = SimpleNamespace(Popen=denied_spawn, run=j.subprocess.run,
                                           PIPE=j.subprocess.PIPE, DEVNULL=j.subprocess.DEVNULL)
            report['patched_interfaces'] += ['register_child: delegate then clock injection', 'runtime subprocess.Popen: inert boundary']

    original_runner = None
    def trace(frame, kind, value):
        nonlocal original_runner
        if frame.f_code.co_filename == str(adapter):
            if kind == 'call' and frame.f_code.co_name == 'main':
                state['globals'] = frame.f_globals
                frame.f_globals['utc'] = lambda: state['clock']
                report['patched_interfaces'].append('adapter.utc: fixed/injected fixture clock')
            if kind == 'return' and value is not None and frame.f_code.co_name == 'load_module' and frame.f_locals.get('name') == 'accepted_mean_runtime':
                original_runner = value.Runner
                patch_runtime(value)
        return trace

    sys.argv = [str(adapter)] + job['argv']
    code = 1
    try:
        sys.settrace(trace)
        runpy.run_path(str(adapter), run_name='__main__')
        code = 0
    except SystemExit as error:
        code = error.code if type(error.code) is int else 1
        if not isinstance(error.code, (int, type(None))): report['system_exit'] = str(error.code)
    except BaseException as error:
        report['driver_error'] = repr(error)
    finally:
        sys.settrace(None)
        report['returncode'] = code
        report['completed_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        (job_path.parent / 'DRIVER_RESULT.json').write_bytes(canonical(report))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
