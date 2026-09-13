#!/usr/bin/env python3
"""Portable adapter controls. Requires a new, root-reviewed execution registration.

This program is a source proposal until reviewed and run. It never creates an
adoption receipt. Synthetic fixture results cannot count as Lean acceptance.
"""
from __future__ import annotations
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LANE = HERE.parent
ADAPTER_SHA = '127ffdc88b8174bdf8ab2b1027510faf4dd6516c6c01e6fea988866825e5868b'
MANIFEST_SHA = '6783dffce953c0e6dd812658af049770b2e63889807acb34f11c75eb4d577b10'
INPUT_PINS_SHA = '08615604ff3db35cce59f0c5ed005e153667e17f499f01e84bf9551d3c0651cc'
MODULES = ('PidFiniteConvergence/Deterministic',
 'PidFiniteConvergence/SxEventBridge',
 'MgwBridgeDepsV1/SxDnf/Contract',
 'MgwBridgeDepsV1/JoinLog/Contract',
 'MgwBridgeDepsV1/SxDnf/JudgeCore',
 'MgwBridgeDepsV1/SxDnf/Proofs',
 'MgwBridgeDepsV1/JoinLog/Proofs',
 'PidMgwBridge/Contract',
 'PidMgwBridge/RawTargets',
 'PidMgwBridge/AliasTargets',
 'PidMgwBridge/JudgeCore',
 'PidMgwBridge/Candidate',
 'PidMgwBridge/SemanticJudge',
 'PidPrefixProbability/Contract',
 'PidPrefixProbability/RawTargets',
 'PidPrefixProbability/AliasTargets',
 'PidPrefixProbability/Candidate',
 'PidPrefixProbability/SemanticJudge',
 'PidPrefixMgwMean/Contract',
 'PidPrefixMgwMean/RawTargets',
 'PidPrefixMgwMean/AliasTargets',
 'PidPrefixMgwMean/Candidate',
 'PidPrefixMgwMean/SemanticJudge',
 'PrefixMgwMeanCandidateRoot',
 'PidPrefixMgwBias/Contract',
 'PidPrefixMgwBias/RawTargets',
 'PidPrefixMgwBias/AliasTargets',
 'PidPrefixMgwBias/Candidate',
 'PidPrefixMgwBias/SemanticJudge')

# name, exact expected terminal status (None = bootstrap refusal), diagnostic.
CASES = [
    ('selected-positive', 'fresh_semantic_kernel_pass', None),
    ('cosmetic-positive', 'fresh_semantic_kernel_pass', None),
    ('prepare-positive', 'prepared_no_lean_or_kernel_execution', None),
    ('prepare-without-adoption', 'prepared_no_lean_or_kernel_execution', None),
    ('missing-isolation', None, 'requires Python'),
    ('missing-no-site', None, 'requires Python'),
    ('missing-no-bytecode', None, 'requires Python'),
    ('optimization-two', None, 'requires Python'),
    ('invalid-source-cli', None, 'invalid choice'),
    ('unknown-cli', None, 'unrecognized arguments'),
    ('root-alias', None, 'noncanonical input directory'),
    ('stage-parent', None, 'stage must be one direct child'),
    ('stage-name', None, 'invalid stage name'),
    ('wrong-cosmetic-cli', None, 'wrong-target control requires selected source'),
    ('runtime-drift', None, 'module source identity changed'),
    ('manifest-digest', None, 'package manifest digest changed'),
    ('manifest-duplicate-key', None, 'duplicate JSON key'),
    ('manifest-nonfinite', None, 'nonfinite JSON'),
    ('manifest-schema', None, 'manifest schema differs'),
    ('manifest-module-order', None, 'exact module order changed'),
    ('manifest-traversal', None, 'invalid manifest entry'),
    ('manifest-absolute', None, 'invalid manifest entry'),
    ('manifest-digest-type', None, 'invalid manifest entry'),
    ('manifest-missing-member', None, 'load-bearing package input absent'),
    ('package-member-drift', None, 'package input changed'),
    ('package-member-symlink', None, 'noncanonical or symlink'),
    ('package-member-hardlink', None, 'regular single-link'),
    ('selected-hardcoded-pin', None, 'accepted selected source changed'),
    ('registration-digest', None, 'registration digest changed'),
    ('registration-schema', None, 'registration does not bind'),
    ('registration-manifest', None, 'registration does not bind'),
    ('registration-owner', None, 'stage owner absent'),
    ('clock-future', None, 'invalid registered 120-minute clock'),
    ('clock-short', None, 'invalid registered 120-minute clock'),
    ('clock-naive', None, 'invalid registered 120-minute clock'),
    ('clock-expired', None, 'stage deadline exhausted'),
    ('stop-at-entry', None, 'stage is stopped'),
    ('adoption-pending', None, 'exact adapter controls have not been adopted'),
    ('adoption-adapter', None, 'exact adapter controls have not been adopted'),
    ('adoption-manifest', None, 'exact adapter controls have not been adopted'),
    ('adoption-count-bool', None, 'exact adapter controls have not been adopted'),
    ('adoption-count-float', None, 'exact adapter controls have not been adopted'),
    ('adoption-count-one', None, 'exact adapter controls have not been adopted'),
    ('adoption-digest', None, 'control-adoption bytes changed'),
    ('tool-digest', None, 'registered tool bytes changed'),
    ('tool-roster', None, 'tool byte pins absent'),
    ('ledger-registration', None, 'ledger registration differs'),
    ('ledger-attempt-cap', None, 'full attempt limit exhausted'),
    ('ledger-child-cap', None, 'child cap exhausted'),
    ('ledger-probe-cap', None, 'tool-probe cap exhausted'),
    ('ledger-symlink', None, 'nonregular stage ledger'),
    ('lock-held', None, 'Resource temporarily unavailable'),
    ('lock-hardlink', None, 'nonregular stage lock'),
    ('output-collision', None, 'File exists'),
    ('source-pin-drift', 'failed', 'pinned source changed'),
    ('import-pin-drift', 'failed', 'explicit new Mathlib import source changed'),
    ('preflight-error', 'failed', 'synthetic preflight failure'),
    ('preflight-expiry', 'failed', 'stage deadline exhausted'),
    ('expiry-after-rehash', 'failed', 'stage deadline exhausted'),
    ('stop-after-rehash', 'failed', 'stage is stopped'),
    ('stop-between-children', 'failed', 'stage is stopped'),
    ('child-cap-between-children', 'failed', 'registered child cap exhausted'),
    ('version-malformed', 'failed', 'unexpected Lean version output'),
    ('compiler-operational-failure', 'failed', 'synthetic runner rejection'),
    ('dispatch-six-as-bias', 'failed', 'record count'),
    ('dispatch-eleven-as-prefix', 'failed', 'record count'),
    ('dispatch-three-as-mgw', 'failed', 'record count'),
    ('bias-reordered', 'failed', 'identity differs'),
    ('bias-type-drift', 'failed', 'exact accepted bias records differ'),
    ('runtime-hash-gap', 'failed', 'stage deadline exhausted'),
    ('finalization-expiry', 'failed', 'stage deadline exhausted'),
    ('finalization-stop', 'failed', 'stage is stopped'),
    ('finalization-input-drift', 'failed', 'input changed after capture'),
    ('finalization-artifact-link', 'failed', 'nonregular retained artifact'),
    ('finalization-save-error', 'failed', 'synthetic evidence preservation failure'),
    ('wrong-without-prior', 'failed', 'needs a prior public full pass'),
    ('wrong-prior-prepare', 'failed', 'needs a prior public full pass'),
    ('wrong-prior-cosmetic', 'failed', 'needs a prior public full pass'),
    ('wrong-prior-record-drift', 'failed', 'prior semantic records changed'),
    ('wrong-prior-byte-drift', 'failed', 'needs a prior public full pass'),
    ('wrong-positive', 'expected_target_rejection', None),
    ('wrong-final-operational', 'failed', 'missed the actual last-type rejection'),
    ('wrong-final-stderr', 'failed', 'missed the actual last-type rejection'),
    ('wrong-final-missing-marker', 'failed', 'missed the actual last-type rejection'),
    ('wrong-final-missing-prefix', 'failed', 'retain the first four exact'),
    ('wrong-final-accepted', 'failed', 'incorrect final target accepted'),
]
CASES += [
    ('dispatch-three-as-bias', 'failed', 'record count'),
    ('dispatch-five-as-mean', 'failed', 'record count'),
    ('bias-fiber-universe-three', 'failed', 'semantic universes differ'),
    ('bias-other-universe-two', 'failed', 'semantic universes differ'),
    ('bias-axiom-drift', 'failed', 'semantic axiom policy differs'),
    ('bias-raw-target-drift', 'failed', 'semantic record identity differs'),
    ('bias-alias-target-drift', 'failed', 'semantic record identity differs'),
    ('wrong-prior-mode-bool', 'failed', 'needs a prior public full pass'),
]
for bound in ('max_full_attempts', 'max_concurrent_wrappers', 'max_compiler_kernel_children', 'max_tool_probes'):
    for kind in ('bool', 'float', 'higher'):
        CASES.append(('bound-' + bound + '-' + kind, None, 'fixed stage bound differs: ' + bound))


def require(value, text):
    if not value:
        raise RuntimeError(text)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def keep(path, value):
    path.write_bytes(canonical(value))


def fixture(directory, name):
    root = directory / 'root'; root.mkdir()
    shutil.copytree(LANE / 'inputs/fixture-root', root, dirs_exist_ok=True)
    root.chmod(0o755)  # copytree copied the sealed root mode; this is our new fixture.
    package = root / 'package'; shutil.copytree(LANE / 'inputs/package', package)
    # Retained inputs are sealed read-only. Only newly created fixture copies
    # receive writable owner modes for the named causal mutations.
    for path in root.rglob('*'):
        path.chmod(0o755 if path.is_dir() else 0o644)
    stage = root / '.local/prefix-mgw-bias-public-replay-v1/control-stage'
    stage.mkdir(parents=True)
    prefix = root / 'toolchain'; (prefix / 'bin').mkdir(parents=True)
    for tool in ('lean', 'leanchecker'):
        path = prefix / 'bin' / tool
        path.write_bytes(b'INERT NONEXECUTABLE CONTROL INPUT; NEVER A LEAN BINARY\n')
        path.chmod(0o444)
    now = dt.datetime.now(dt.timezone.utc)
    manifest_path = package / 'replay-proposed-v1.json'
    manifest = json.loads(manifest_path.read_bytes())
    controls = {'schema': 'pid-rs/portable-bias-controls-acceptance-v1',
                'status': 'adopted_completed_portable_bias_controls',
                'manifest_sha256': MANIFEST_SHA, 'adapter_sha256': ADAPTER_SHA,
                'new_bias_theorems_proved': 0,
                'evidence': 'SYNTHETIC CONTROL FIXTURE, NOT ADOPTION'}
    registration = {
        'schema': 'pid-rs/prefix-mgw-bias-packaging-registration-v1',
        'registered_utc': (now - dt.timedelta(minutes=1)).isoformat(),
        'deadline_utc': (now + dt.timedelta(minutes=119)).isoformat(),
        'owner': 'SYNTHETIC ENTRYPOINT CONTROL', 'manifest_sha256': MANIFEST_SHA,
        'max_full_attempts': 6, 'max_concurrent_wrappers': 1,
        'max_compiler_kernel_children': 186, 'max_tool_probes': 6,
        'tool_sha256': {n: digest((prefix / 'bin' / n).read_bytes()) for n in ('lean', 'leanchecker')},
    }
    changed_manifest = False
    if name == 'runtime-drift':
        with (package / 'replay-support/runtime.py').open('ab') as stream: stream.write(b'\n# drift\n')
    elif name == 'manifest-schema': manifest['schema'] = 'other'; changed_manifest = True
    elif name == 'manifest-module-order': manifest['source_modules'].reverse(); changed_manifest = True
    elif name in {'manifest-traversal', 'manifest-absolute'}:
        manifest['files']['../outside' if name.endswith('traversal') else '/outside'] = '0' * 64
        changed_manifest = True
    elif name == 'manifest-digest-type': manifest['files']['SOURCE_GRAPH.json'] = False; changed_manifest = True
    elif name == 'manifest-missing-member':
        del manifest['files']['sources/PidPrefixMgwBias/RawTargets.lean']; changed_manifest = True
    elif name == 'selected-hardcoded-pin':
        path = package / 'sources/PidPrefixMgwBias/Candidate.lean'
        path.write_bytes(path.read_bytes() + b'\n-- synthetic pin drift\n')
        manifest['files']['sources/PidPrefixMgwBias/Candidate.lean'] = digest(path.read_bytes())
        changed_manifest = True
    elif name == 'package-member-drift':
        with (package / 'SOURCE_GRAPH.json').open('ab') as stream: stream.write(b'\nsynthetic drift\n')
    elif name in {'package-member-symlink', 'package-member-hardlink'}:
        path = package / 'SOURCE_GRAPH.json'; target = directory / 'member-target'; path.rename(target)
        if name.endswith('symlink'): path.symlink_to(target)
        else: os.link(target, path)
    if changed_manifest: keep(manifest_path, manifest)
    if name == 'manifest-duplicate-key':
        manifest_path.write_bytes(manifest_path.read_bytes().replace(b'{', b'{"schema":"duplicate",', 1))
    if name == 'manifest-nonfinite':
        manifest_path.write_bytes(manifest_path.read_bytes().replace(b'{', b'{"synthetic":NaN,', 1))
    manifest_sha = digest(manifest_path.read_bytes())
    registration['manifest_sha256'] = controls['manifest_sha256'] = manifest_sha
    if name == 'manifest-digest': manifest_sha = '0' * 64
    if name == 'registration-schema': registration['schema'] = 'other'
    if name == 'registration-manifest': registration['manifest_sha256'] = '0' * 64
    if name == 'registration-owner': registration['owner'] = ' '
    if name.startswith('bound-'):
        field, kind = name[6:].rsplit('-', 1)
        value = registration[field]
        registration[field] = {'bool': True, 'float': float(value), 'higher': value + 1}[kind]
    if name == 'clock-future':
        registration['registered_utc'] = (now + dt.timedelta(minutes=1)).isoformat()
        registration['deadline_utc'] = (now + dt.timedelta(minutes=121)).isoformat()
    if name == 'clock-short': registration['deadline_utc'] = (now + dt.timedelta(minutes=118)).isoformat()
    if name == 'clock-naive':
        registration['registered_utc'] = (now - dt.timedelta(minutes=1)).replace(tzinfo=None).isoformat()
        registration['deadline_utc'] = (now + dt.timedelta(minutes=119)).replace(tzinfo=None).isoformat()
    if name == 'clock-expired':
        registration['registered_utc'] = (now - dt.timedelta(minutes=121)).isoformat()
        registration['deadline_utc'] = (now - dt.timedelta(minutes=1)).isoformat()
    if name == 'adoption-pending': controls['status'] = 'PENDING_NOT_ADOPTED'
    if name == 'adoption-adapter': controls['adapter_sha256'] = '0' * 64
    if name == 'adoption-manifest': controls['manifest_sha256'] = '0' * 64
    if name.startswith('adoption-count-'):
        controls['new_bias_theorems_proved'] = {'bool': False, 'float': 0.0, 'one': 1}[name.rsplit('-', 1)[1]]
    keep(stage / 'CONTROLS_ACCEPTANCE.json', controls)
    registration['controls_acceptance_sha256'] = digest((stage / 'CONTROLS_ACCEPTANCE.json').read_bytes())
    if name == 'adoption-digest': registration['controls_acceptance_sha256'] = '0' * 64
    if name == 'tool-digest': registration['tool_sha256']['lean'] = '0' * 64
    if name == 'tool-roster': registration['tool_sha256']['extra'] = '0' * 64
    if name == 'prepare-without-adoption':
        del registration['controls_acceptance_sha256']; (stage / 'CONTROLS_ACCEPTANCE.json').unlink()
    keep(stage / 'REGISTRATION.json', registration)
    reg_sha = digest((stage / 'REGISTRATION.json').read_bytes())
    if name == 'registration-digest': reg_sha = '0' * 64
    ledger = {'registration_sha256': reg_sha, 'attempts': [], 'children': []}
    if name == 'ledger-registration': ledger['registration_sha256'] = '0' * 64
    if name == 'ledger-attempt-cap': ledger['attempts'] = [{} for _ in range(6)]
    if name in {'ledger-child-cap', 'child-cap-between-children'}:
        ledger['children'] = [{'kind': 'compiler_kernel'} for _ in range(186 if name == 'ledger-child-cap' else 185)]
    if name == 'ledger-probe-cap': ledger['children'] = [{'kind': 'tool_probe'} for _ in range(6)]
    if name.startswith('ledger-') or name == 'child-cap-between-children': keep(stage / 'ATTEMPT_LEDGER.json', ledger)
    if name == 'ledger-symlink':
        path = stage / 'ATTEMPT_LEDGER.json'; target = directory / 'ledger-target'; path.rename(target); path.symlink_to(target)
    if name == 'lock-hardlink':
        path = stage / 'EXECUTION.lock'; path.write_bytes(b''); os.link(path, directory / 'lock-link')
    if name == 'output-collision': (stage / 'attempt-001').mkdir()
    if name == 'stop-at-entry': keep(stage / 'STOP_RECORD.json', {'synthetic': True})
    if name == 'source-pin-drift':
        (root / 'audit/formal/lean/lean-toolchain').write_bytes(b'synthetic drift\n')
    if name == 'import-pin-drift':
        imports = json.loads((package / 'preparation/NEW_IMPORT_SOURCE_PINS.json').read_bytes())
        (root / next(iter(imports))).write_bytes(b'synthetic drift\n')
    root_arg, stage_arg = root, stage
    if name == 'root-alias':
        root_arg = directory / 'root-alias'; root_arg.symlink_to(root, target_is_directory=True)
    if name == 'stage-parent':
        stage_arg = root / 'other-stage'; stage_arg.mkdir()
    if name == 'stage-name':
        stage_arg = stage.parent / 'UPPER'; stage.rename(stage_arg); stage = stage_arg
    source = 'cosmetic' if name in {'cosmetic-positive', 'wrong-cosmetic-cli'} else 'selected'
    action = 'wrong-last-target' if name.startswith('wrong-') else 'check'
    argv = ['--root', str(root_arg), '--stage', str(stage_arg), '--manifest-sha256', manifest_sha,
            '--registration-sha256', reg_sha, '--toolchain-prefix', str(prefix), '--source', source,
            '--action', action]
    if name.startswith('prepare-'): argv.append('--prepare-only')
    if name == 'invalid-source-cli': argv[argv.index('--source') + 1] = 'unlisted'
    if name == 'unknown-cli': argv.append('--unlisted')
    return {'case': name, 'adapter': str(package / 'replay-proposed.py'), 'root': str(root),
            'stage': str(stage), 'now': now.isoformat(), 'argv': argv, 'action': action}


def invoke(directory, job, mode, cutoff):
    job_path = directory / 'JOB.json'; keep(job_path, job)
    flags = ['-I', '-S', '-B'] + (['-O'] if mode else [])
    name = job['case']
    for control, flag in [('missing-isolation', '-I'), ('missing-no-site', '-S'), ('missing-no-bytecode', '-B')]:
        if name == control: flags.remove(flag)
    if name == 'optimization-two': flags = ['-I', '-S', '-B', '-OO']
    command = [sys.executable, *flags, str(HERE / 'control-child.py'), str(job_path)]
    keep(directory / 'COMMAND.json', {'command': command, 'registered_utc': dt.datetime.now(dt.timezone.utc).isoformat()})
    seconds = min(30.0, cutoff - time.monotonic())
    require(seconds > 0, 'control stage deadline exhausted')
    with (directory / 'stdout.log').open('xb') as stdout, (directory / 'stderr.log').open('xb') as stderr:
        # Driver audit hook prohibits descendants. This timeout is for an inert
        # Python control process, not the production Runner's separate groups.
        result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                timeout=seconds, check=False, env={'PATH': '/usr/bin:/bin'})
    driver = json.loads((directory / 'DRIVER_RESULT.json').read_bytes())
    require(not driver['external_process_attempts'], 'control attempted an external process')
    require('driver_error' not in driver, 'driver itself failed: ' + str(driver.get('driver_error')))
    return result.returncode, driver


def main():
    require(sys.version_info >= (3, 11) and sys.flags.isolated and sys.flags.no_site and
            sys.dont_write_bytecode and sys.flags.optimize in (0, 1), 'requires Python 3.11+ -I -S -B, optional -O')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', required=True, type=Path)
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    raw = args.registration.read_bytes()
    require(digest(raw) == args.registration_sha256, 'control execution registration changed')
    registration = json.loads(raw)
    require(registration['schema'] == 'portable-bias-adapter-controls-execution-v1' and
            registration['status'] == 'root-reviewed-source-ready-for-controls' and
            registration['adapter_sha256'] == ADAPTER_SHA
            and type(registration['new_bias_theorems_proved']) is int
            and registration['new_bias_theorems_proved'] == 0,
            'requires separate reviewed control execution registration')
    start, deadline = (dt.datetime.fromisoformat(registration[n]) for n in ('registered_utc', 'deadline_utc'))
    now = dt.datetime.now(dt.timezone.utc)
    require(start.tzinfo is not None and deadline.tzinfo is not None and start <= now < deadline and
            deadline - start <= dt.timedelta(minutes=45), 'invalid bounded control execution clock')
    cutoff = time.monotonic() + (deadline - now).total_seconds()
    pins_raw = (LANE / 'INPUT_PINS.json').read_bytes()
    require(digest(pins_raw) == INPUT_PINS_SHA, 'retained input pin registry changed')
    pins = json.loads(pins_raw)['files']
    for rel, expected in pins.items():
        require(digest((LANE / 'inputs' / rel).read_bytes()) == expected, 'retained source drift: ' + rel)
    for name in ('adapter-controls.py', 'control-child.py'):
        require(digest((HERE / name).read_bytes()) == registration['source_sha256'][name], 'control source differs: ' + name)
    output = args.output.absolute()
    require(output.parent == output.parent.resolve(strict=True) and '.local' in output.parts and
            not output.exists(), 'output must be a fresh ignored-path directory')
    output.mkdir(); keep(output / 'EXECUTION_REGISTRATION.json', registration)
    result = {'status': 'failed', 'scope': 'synthetic whole-entrypoint controls; no proof or adoption',
              'adapter_sha256': ADAPTER_SHA, 'manifest_sha256': MANIFEST_SHA,
              'new_bias_theorems_proved': 0, 'records': []}
    try:
        for mode in (0, 1):
            for name, expected_status, diagnostic in CASES:
                require(time.monotonic() < cutoff and dt.datetime.now(dt.timezone.utc) < deadline,
                        'control deadline before next fixture')
                directory = output / (str(len(result['records'])).zfill(3) + '-' + str(mode) + '-' + name)
                directory.mkdir(); job = fixture(directory, name)
                stage = Path(job['stage'])
                if name.startswith('wrong-') and name not in {'wrong-without-prior', 'wrong-cosmetic-cli'}:
                    prior_dir = directory / 'prior-invocation'; prior_dir.mkdir()
                    prior = dict(job, case='selected-positive', action='check', argv=list(job['argv']))
                    prior['argv'][prior['argv'].index('--action') + 1] = 'check'
                    if name == 'wrong-prior-prepare': prior['argv'].append('--prepare-only')
                    if name == 'wrong-prior-cosmetic': prior['argv'][prior['argv'].index('--source') + 1] = 'cosmetic'
                    prior_code, _ = invoke(prior_dir, prior, mode, cutoff)
                    require(prior_code == 0, 'causal prior invocation did not pass')
                    receipt = stage / 'attempt-001/RESULT.json'
                    if name == 'wrong-prior-record-drift':
                        body = json.loads(receipt.read_bytes()); body['semantic_records'] = []; keep(receipt, body)
                    if name == 'wrong-prior-mode-bool':
                        body = json.loads(receipt.read_bytes()); body['registered']['python_optimized'] = bool(mode); keep(receipt, body)
                    if name == 'wrong-prior-byte-drift':
                        (stage / 'attempt-001/Candidate.original.lean').write_bytes(b'synthetic changed prior bytes\n')
                held = None
                try:
                    if name == 'lock-held':
                        held = (stage / 'EXECUTION.lock').open('a+')
                        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    code, driver = invoke(directory, job, mode, cutoff)
                finally:
                    if held is not None: held.close()
                receipts = sorted(stage.glob('attempt-*/RESULT.json'))
                current = receipts[-1] if receipts else None
                body = json.loads(current.read_bytes()) if current else None
                expected_code = 0 if expected_status and expected_status != 'failed' else (2 if name in {'invalid-source-cli', 'unknown-cli'} else 1)
                require(code == expected_code, name + ': exit code differs: ' + str(code))
                if expected_status is None:
                    require(body is None, name + ': unexpected result after bootstrap refusal')
                else:
                    require(body is not None and body['status'] == expected_status, name + ': result status differs')
                    require(body['registered']['python_optimized'] == mode, name + ': optimization ledger differs')
                text = (directory / 'stderr.log').read_text() + (json.dumps(body) if body else '')
                if diagnostic: require(diagnostic in text, name + ': expected causal diagnostic absent: ' + diagnostic)
                calls = [x for x in driver['events'] if x['kind'] == 'runner-call']
                if expected_status == 'fresh_semantic_kernel_pass':
                    labels = ['tool-version'] + ['compile-' + m.replace('/', '-') for m in MODULES]
                    labels += ['compile-BiasCandidateRoot', 'fresh-kernel']
                    require([x['label'] for x in calls] == labels, name + ': exact 32-dispatch order differs')
                    require(len(body['semantic_records']) == 5 and len(body['accepted_prefix_dependency_records']) == 6
                            and len(body['accepted_mgw_dependency_records']) == 11 and len(body['accepted_mean_dependency_records']) == 3, 'rank record dispatch differs')
                    require(calls[-1]['command'][1:] == ['--fresh', 'BiasCandidateRoot'], 'fresh kernel argv differs')
                    for call in calls[1:-1]:
                        require(call['command'][1:6] == ['-t', '0', '-M', '4096', '-o'], 'compiler limits/order differ')
                if expected_status == 'expected_target_rejection':
                    require(len(calls) == 30 and calls[-1]['label'] == 'compile-PidPrefixMgwBias-SemanticJudge',
                            'wrong target dispatch must stop at child 29 plus one probe')
                if name in {'prepare-positive', 'prepare-without-adoption', 'preflight-expiry', 'expiry-after-rehash', 'stop-after-rehash'}:
                    require(not calls, name + ': child routed after causal stop')
                if name in {'stop-between-children', 'child-cap-between-children'}:
                    require(len(calls) == (1 if name.startswith('stop-') else 2), name + ': child budget did not stop routing')
                if name == 'runtime-hash-gap':
                    require(any(x['kind'] == 'runtime-spawn-boundary-reached-after-deadline' for x in driver['events']),
                            'delayed real Runtime hash did not reach the measured late boundary')
                    require(body['status'] == 'failed' and 'preservation_failure' in body, 'late gap was promoted')
                rec = {'name': name, 'mode': mode, 'status': 'matched_expected_behavior', 'returncode': code,
                       'expected_status': expected_status, 'diagnostic': diagnostic,
                       'driver_sha256': digest((directory / 'DRIVER_RESULT.json').read_bytes()),
                       'adapter_result_sha256': digest(current.read_bytes()) if current else None,
                       'synthetic_runner_calls': len(calls)}
                keep(directory / 'CONTROL_RESULT.json', rec); result['records'].append(rec)
        # A real pair of instrumented whole-entrypoint invocations shares one
        # stage/ledger, so mode separation is not inferred from separate cases.
        shared = output / 'shared-normal-optimized-stage'; shared.mkdir()
        shared_job = fixture(shared, 'selected-positive')
        for mode in (0, 1):
            invocation = shared / ('mode-' + str(mode)); invocation.mkdir()
            code, driver = invoke(invocation, shared_job, mode, cutoff)
            require(code == 0, 'shared-stage mode invocation failed')
            result['records'].append({'name': 'shared-stage-mode', 'mode': mode,
                                      'status': 'matched_expected_behavior', 'synthetic_runner_calls': 32})
        shared_ledger = json.loads((Path(shared_job['stage']) / 'ATTEMPT_LEDGER.json').read_bytes())
        require([x['python_optimized'] for x in shared_ledger['attempts']] == [0, 1]
                and len(shared_ledger['children']) == 64, 'shared normal/O ledger routing differs')
        for rel, expected in pins.items():
            require(digest((LANE / 'inputs' / rel).read_bytes()) == expected, 'retained source drift after controls: ' + rel)
        for name in ('adapter-controls.py', 'control-child.py'):
            require(digest((HERE / name).read_bytes()) == registration['source_sha256'][name], 'control source drift after controls: ' + name)
        require(time.monotonic() < cutoff and dt.datetime.now(dt.timezone.utc) < deadline, 'late control closure')
        result['status'] = 'controls_matched_expected_behavior_not_adopted'
    except BaseException as error:
        result['failure'] = repr(error)
    finally:
        result['completed_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        if dt.datetime.now(dt.timezone.utc) >= deadline:
            result.update(status='failed', finalization_failure='control closure reached original deadline')
        keep(output / 'RESULT.json', result)
        if dt.datetime.now(dt.timezone.utc) >= deadline:
            result.update(status='failed', finalization_failure='original deadline reached during result write')
            keep(output / 'RESULT.json', result)
    print(json.dumps({'status': result['status'], 'controls': len(result['records']), 'output': str(output)}))
    return 0 if result['status'] == 'controls_matched_expected_behavior_not_adopted' else 1


if __name__ == '__main__':
    raise SystemExit(main())
