#!/usr/bin/env python3
"""Proposed portable mean replay; source-reviewed, not yet execution-adopted.

This is a new packaging adapter, not the closed candidate campaign. It reuses
the exact historical Snapshot, Runner, source policies and semantic judges.
Fresh adapter controls and a separately frozen registration are required.
"""
from __future__ import annotations

import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from types import ModuleType, SimpleNamespace

HERE = Path(__file__).resolve().parent
RUNTIME_SHA = 'bd8a9f2272a20422863c9902ce2148d2957471bb958d13949fece923cb6a7f5d'
SELECTED_SHA = '17fc2d8fce5ad0ba28cc8348e9348911c393e6eb00515c8139fbd27b85331b6a'
COSMETIC_SHA = '4dc776110f0db0a370123c011d8fe05e2a0abcf99a55dd1b76c9ec335ed71409'
MEAN_NAMES = ('word_coefficient_join_power', 'finite_block_expectation',
              'prefix_expectations_to_mgw_mean')
DEPS = ('PidFiniteConvergence/Deterministic', 'PidFiniteConvergence/SxEventBridge',
        'MgwBridgeDepsV1/SxDnf/Contract', 'MgwBridgeDepsV1/JoinLog/Contract',
        'MgwBridgeDepsV1/SxDnf/JudgeCore', 'MgwBridgeDepsV1/SxDnf/Proofs',
        'MgwBridgeDepsV1/JoinLog/Proofs', 'PidMgwBridge/Contract',
        'PidMgwBridge/RawTargets', 'PidMgwBridge/AliasTargets', 'PidMgwBridge/JudgeCore',
        'PidMgwBridge/Candidate', 'PidMgwBridge/SemanticJudge',
        'PidPrefixProbability/Contract', 'PidPrefixProbability/RawTargets',
        'PidPrefixProbability/AliasTargets', 'PidPrefixProbability/Candidate',
        'PidPrefixProbability/SemanticJudge')
TRUSTED = tuple('PidPrefixMgwMean/' + x for x in ('Contract', 'RawTargets', 'AliasTargets'))
MODULES = DEPS + TRUSTED + ('PidPrefixMgwMean/Candidate', 'PidPrefixMgwMean/SemanticJudge')
ROOT_MODULE = 'PrefixMgwMeanCandidateRoot'
RUNTIME_PARENT = Path('.local/prefix-mgw-mean-public-replay-v1')
HEX = re.compile(r'[0-9a-f]{64}\Z')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc)


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    def nonfinite(value):
        raise RuntimeError('nonfinite JSON: ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def load_module(name, path, raw, expected):
    require(digest(raw) == expected, 'module source identity changed: ' + path.name)
    module = ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec', dont_inherit=True, optimize=sys.flags.optimize), module.__dict__)
    return module


def remaining(stage, deadline):
    require(not (stage / 'STOP_RECORD.json').exists(), 'packaging stage is stopped')
    seconds = (deadline - utc()).total_seconds()
    require(seconds > 0, 'packaging stage deadline exhausted')
    return seconds


def save_ledger(stage, ledger):
    target = stage / 'ATTEMPT_LEDGER.next.json'
    with target.open('xb') as stream:
        stream.write(canonical(ledger))
        stream.flush()
        os.fsync(stream.fileno())
    target.replace(stage / 'ATTEMPT_LEDGER.json')


def main():
    require(sys.version_info >= (3, 11) and sys.flags.isolated and sys.flags.no_site
            and sys.dont_write_bytecode and sys.flags.optimize in (0, 1),
            'requires Python 3.11+ -I -S -B, optionally -O')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--stage', required=True, type=Path)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--toolchain-prefix', required=True, type=Path)
    parser.add_argument('--source', choices=('selected', 'cosmetic'), default='selected')
    parser.add_argument('--action', choices=('check', 'wrong-last-target'), default='check')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    root, stage, prefix = (p.absolute() for p in (args.root, args.stage, args.toolchain_prefix))
    for path in (root, stage, prefix, HERE):
        require(path == path.resolve(strict=True) and path.is_dir(), 'noncanonical input directory')
    runtime_parent = root / RUNTIME_PARENT
    require(runtime_parent == runtime_parent.resolve(strict=True) and stage.parent == runtime_parent,
            'stage must be one direct child of the canonical ignored runtime directory')
    require(re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', stage.name) is not None, 'invalid stage name')
    require(args.action == 'check' or args.source == 'selected', 'wrong-target control requires selected source')
    for value in (args.manifest_sha256, args.registration_sha256):
        require(HEX.fullmatch(value) is not None, 'invalid expected digest')
    # Bootstrap only the byte-pinned, unchanged utility module. Its main is never called.
    runtime_path = HERE / 'replay-support/runtime.py'
    raw_runtime = runtime_path.read_bytes()
    j = load_module('accepted_mean_runtime', runtime_path, raw_runtime, RUNTIME_SHA)
    snapshot = j.Snapshot()
    require(snapshot.read(runtime_path) == raw_runtime, 'runtime changed during bootstrap')
    manifest_raw = snapshot.read(HERE / 'replay-proposed-v1.json')
    require(digest(manifest_raw) == args.manifest_sha256, 'package manifest digest changed')
    manifest = strict_json(manifest_raw)
    require(manifest['schema'] == 'pid-rs/prefix-mgw-mean-portable-replay-proposal-v1', 'manifest schema differs')
    require(manifest['source_modules'] == list(MODULES + (ROOT_MODULE,)), 'exact module order changed')
    files = manifest['files']
    require(type(files) is dict and bool(files), 'empty file roster')
    captured = {}
    for name, expected in files.items():
        require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts
                and type(expected) is str and HEX.fullmatch(expected), 'invalid manifest entry')
        captured[name] = snapshot.read(HERE / name)
        require(digest(captured[name]) == expected, 'package input changed: ' + name)
    required = {'sources/' + x + '.lean' for x in MODULES + (ROOT_MODULE,)} | {
        'replay-proposed.py', 'replay-support/runtime.py', 'replay-support/policy.py',
        'replay-support/prefix-policy.py', 'replay-support/mgw-policy.py',
        'replay-support/ACCEPTED_DEPENDENCY_RECORDS.json', 'replay-support/EXPECTED_MEAN_RECORDS.json',
        'controls/Candidate.cosmetic.lean', 'controls/Candidate.wrong-last.lean.txt',
        'preparation/NEW_IMPORT_SOURCE_PINS.json'}
    require(required <= set(captured), 'load-bearing package input absent')
    require(captured['replay-proposed.py'] == snapshot.read(Path(__file__)), 'adapter absent or changed')
    policies = {}
    for name in ('policy', 'prefix-policy', 'mgw-policy'):
        rel = 'replay-support/' + name + '.py'
        policies[name] = load_module(name.replace('-', '_'), HERE/rel, captured[rel], files[rel])
    policy = policies['policy']
    require(tuple(policy.THEOREMS) == MEAN_NAMES, 'mean theorem names changed')
    expected = strict_json(captured['replay-support/ACCEPTED_DEPENDENCY_RECORDS.json'])
    require(set(expected) == {'accepted_prefix_dependency', 'accepted_mgw_dependency'}, 'dependency family roster differs')
    expected_mean = strict_json(captured['replay-support/EXPECTED_MEAN_RECORDS.json'])
    selected = captured['sources/PidPrefixMgwMean/Candidate.lean']
    require(digest(selected) == SELECTED_SHA, 'accepted selected source changed')
    source = selected if args.source == 'selected' else captured['controls/Candidate.cosmetic.lean']
    require(digest(source) == (SELECTED_SHA if args.source == 'selected' else COSMETIC_SHA), 'candidate variant changed')
    registration_raw = snapshot.read(stage/'REGISTRATION.json')
    require(digest(registration_raw) == args.registration_sha256, 'registration digest changed')
    registration = strict_json(registration_raw)
    require(registration['schema'] == 'pid-rs/prefix-mgw-mean-packaging-registration-v1'
            and registration['manifest_sha256'] == args.manifest_sha256, 'registration does not bind this adapter')
    require(type(registration['owner']) is str and bool(registration['owner'].strip()), 'stage owner absent')
    for field, value in (('max_full_attempts', 6), ('max_concurrent_wrappers', 1),
                         ('max_compiler_kernel_children', 150), ('max_tool_probes', 6)):
        require(type(registration[field]) is int and registration[field] == value, 'fixed stage bound differs: ' + field)
    registered = datetime.datetime.fromisoformat(registration['registered_utc'])
    deadline = datetime.datetime.fromisoformat(registration['deadline_utc'])
    require(registered.tzinfo is not None and deadline.tzinfo is not None
            and deadline - registered == datetime.timedelta(minutes=120)
            and utc() >= registered, 'invalid registered 120-minute clock')
    remaining(stage, deadline)
    if not args.prepare_only:
        controls_sha = registration['controls_acceptance_sha256']
        require(type(controls_sha) is str and HEX.fullmatch(controls_sha),
                'execution requires actual control-adoption digest')
        controls_raw = snapshot.read(stage/'CONTROLS_ACCEPTANCE.json')
        require(digest(controls_raw) == controls_sha, 'control-adoption bytes changed')
        controls = strict_json(controls_raw)
        require(controls['schema'] == 'pid-rs/portable-mean-controls-acceptance-v1'
                and controls['status'] == 'adopted_completed_portable_mean_controls'
                and controls['manifest_sha256'] == args.manifest_sha256
                and controls['adapter_sha256'] == files['replay-proposed.py']
                and type(controls['new_mean_theorems_proved']) is int
                and controls['new_mean_theorems_proved'] == 0,
                'exact adapter controls have not been adopted')
    tools = registration['tool_sha256']
    require(type(tools) is dict and set(tools) == {'lean','leanchecker'}, 'tool byte pins absent')
    lean, checker = prefix/'bin/lean', prefix/'bin/leanchecker'
    for name, path in (('lean',lean),('leanchecker',checker)):
        require(type(tools[name]) is str and HEX.fullmatch(tools[name])
                and digest(snapshot.read(path)) == tools[name], 'registered tool bytes changed: ' + name)
    lock_path = stage/'EXECUTION.lock'
    if lock_path.exists():
        info = lock_path.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'nonregular stage lock')
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    lock = os.fdopen(lock_fd, 'a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    ledger_path = stage/'ATTEMPT_LEDGER.json'
    if ledger_path.exists():
        info = ledger_path.lstat()
        require(ledger_path == ledger_path.resolve(strict=True) and stat.S_ISREG(info.st_mode)
                and info.st_nlink == 1, 'nonregular stage ledger')
    ledger_raw = ledger_path.read_bytes() if ledger_path.exists() else None
    ledger = strict_json(ledger_raw) if ledger_raw else {
        'registration_sha256': args.registration_sha256, 'attempts': [], 'children': []}
    require(ledger['registration_sha256'] == args.registration_sha256, 'ledger registration differs')
    require(type(ledger['attempts']) is list and len(ledger['attempts']) < 6, 'full attempt limit exhausted')
    require(type(ledger['children']) is list, 'child ledger absent')
    require(sum(x['kind']=='compiler_kernel' for x in ledger['children']) < 150, 'child cap exhausted')
    require(sum(x['kind']=='tool_probe' for x in ledger['children']) < 6, 'tool-probe cap exhausted')
    output = stage/('attempt-'+str(len(ledger['attempts'])+1).zfill(3))
    output.mkdir(exist_ok=False)
    if ledger_raw is not None:
        (output/'ATTEMPT_LEDGER.preimage.json').write_bytes(ledger_raw)
    entry = {'registered_utc':utc().isoformat(), 'action':args.action, 'source':args.source,
             'python_optimized':sys.flags.optimize, 'output':output.name,
             'original_sha256':digest(source), 'manifest_sha256':args.manifest_sha256,
             'prepare_only':args.prepare_only}
    (output/'REGISTERED.json').write_bytes(canonical(entry))
    ledger['attempts'].append(entry)
    save_ledger(stage,ledger)
    result = {'schema':'pid-rs/prefix-mgw-mean-packaging-result-v1','status':'failed',
              'registered':entry,'scope':'Packaging replay after exact local acceptance; three mean exports, inherited eleven and six records.'}
    runner = None
    try:
        j.verify_source_pins(root,snapshot)
        for relative, expected_sha in strict_json(captured['preparation/NEW_IMPORT_SOURCE_PINS.json']).items():
            require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,
                    'invalid explicit import source path')
            require(digest(snapshot.read(root/relative)) == expected_sha,
                    'explicit new Mathlib import source changed: '+relative)
        _, base = j.load_helpers(root,snapshot)
        require(base.ROOT == root, 'helper repository root differs')
        policy.candidate_policy(source,base,HERE/'sources/PidPrefixMgwMean/Candidate.lean')
        if args.action == 'wrong-last-target':
            prior = []
            for previous in ledger['attempts'][:-1]:
                if previous['action'] != 'check' or previous['source'] != 'selected' or previous['prepare_only']:
                    continue
                receipt_path = stage/previous['output']/'RESULT.json'
                if receipt_path.exists():
                    raw = snapshot.read(receipt_path)
                    body = strict_json(raw)
                    original = snapshot.read(receipt_path.parent/'Candidate.original.lean')
                    if body['status']=='fresh_semantic_kernel_pass' and body['registered']==previous and original==selected:
                        require(body['semantic_records']==expected_mean, 'prior semantic records changed')
                        prior.append({'receipt':str(receipt_path),'sha256':digest(raw)})
            require(bool(prior), 'wrong-target control needs a prior public full pass of identical selected bytes')
            result['prior_full_passes'] = prior
            marker = 'theorem prefix_expectations_to_mgw_mean'
            text = selected.decode()
            masked = base.mask_lean_comments_and_strings(text,HERE/'sources/PidPrefixMgwMean/Candidate.lean')
            require(masked.count(marker)==1,'wrong-target marker differs')
            source = (text[:masked.index(marker)] + 'theorem prefix_expectations_to_mgw_mean : True := by trivial\n\nend PidPrefixMgwMeanCandidate\n').encode()
            require(source==captured['controls/Candidate.wrong-last.lean.txt'],'wrong-target transform changed')
            policy.candidate_policy(source,base,output/'Candidate.control.lean',final_control=True)
        (output/'Candidate.original.lean').write_bytes(selected if args.action=='wrong-last-target' else source)
        (output/'Candidate.executed.lean').write_bytes(source)
        result['executed_sha256'] = digest(source)
        src, build = output/'src',output/'build'
        src.mkdir(); build.mkdir()
        for module in MODULES+(ROOT_MODULE,):
            raw = source if module=='PidPrefixMgwMean/Candidate' else captured['sources/'+module+'.lean']
            target = src/(module+'.lean')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
            snapshot.read(target)
        packages = [root/j.PROJECT_RELATIVE/'.lake/packages'/name/'.lake/build/lib/lean'
                    for name in base.EXPECTED_PACKAGE_PINS]
        environment = {'PATH':str(prefix/'bin')+os.pathsep+'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8',
                       'LEAN_PATH':os.pathsep.join(map(str,[build,*packages,prefix/'lib/lean'])),
                       'LEAN_SRC_PATH':str(src)}
        commands = [{'module':m,'command':[str(lean),'-t','0','-M','4096','-o',str(build/(m+'.olean')),str(src/(m+'.lean'))]}
                    for m in MODULES]
        if args.action=='check':
            commands += [{'module':ROOT_MODULE,'command':[str(lean),'-t','0','-M','4096','-o',str(build/(ROOT_MODULE+'.olean')),str(src/(ROOT_MODULE+'.lean'))]},
                         {'module':'fresh-kernel','command':[str(checker),'--fresh',ROOT_MODULE]}]
        (output/'environment.json').write_bytes(canonical({'tools':tools,'environment':environment,
            'package_pins':base.EXPECTED_PACKAGE_PINS,'source_to_dependency_olean_authenticity':'not claimed'}))
        (output/'COMMAND_PLAN.json').write_bytes(canonical({'commands':commands,'probe':[str(lean),'--version'],
            'status':'prepared_no_execution','expected_compiler_kernel_children':25 if args.action=='check' else 23}))
        if args.prepare_only:
            result['status']='prepared_no_lean_or_kernel_execution'
        else:
            # Exact pinned helper preflight; no aggregate project build or development cache is used.
            base.check_toolchain(); base.check_lakefile(); base.check_manifest()
            git = base.find_git()
            require(Path(base.run_git(git,root,['rev-parse','--show-toplevel'],'root check').strip())==root,'Git root differs')
            base.check_dependency_checkouts(git)
            remaining(stage,deadline)
            runner = j.Runner(output,environment,preparation=False)
            def run(command,label,*,allow_stdout=False,kind='compiler_kernel'):
                snapshot.verify()
                seconds = remaining(stage,deadline)
                cap = 6 if kind=='tool_probe' else 150
                require(sum(x['kind']==kind for x in ledger['children']) < cap,'registered child cap exhausted')
                child = {'registered_utc':utc().isoformat(),'attempt':output.name,'kind':kind,'label':label,'command':command}
                ledger['children'].append(child)
                save_ledger(stage,ledger)
                # The unchanged Runner also hashes the staged Lean inputs before
                # spawning. External stage supervision and its causal expiry
                # control remain required; this caller check is not an atomic
                # deadline/launch operation.
                seconds = min(seconds, remaining(stage,deadline))
                return runner.run(command,src,label,timeout=min(60 if kind=='tool_probe' else 600,seconds),allow_stdout=allow_stdout)
            version = run([str(lean),'--version'],'tool-version',allow_stdout=True,kind='tool_probe')
            result['portable_lean_version'] = base.parse_lean_version_probe(SimpleNamespace(returncode=0,stdout=version.decode(),stderr=''))
            for planned in commands:
                module,command = planned['module'],planned['command']
                target = build/(module+'.olean')
                if module!='fresh-kernel':
                    target.parent.mkdir(parents=True,exist_ok=True)
                try:
                    stdout = run(command,'fresh-kernel' if module=='fresh-kernel' else 'compile-'+module.replace('/','-'),
                                 allow_stdout=module.endswith('SemanticJudge'))
                except j.JudgeError:
                    if args.action=='wrong-last-target' and module=='PidPrefixMgwMean/SemanticJudge':
                        last=runner.commands[-1]
                        log=output/(str(len(runner.commands)-1).zfill(2)+'-'+last['label'])/'stdout.log'
                        text=log.read_text()
                        require(last['failure'] is None and last['returncode'] != 0
                                and last['retained_stderr_bytes'] == 0
                                and 'PidPrefixMgwMeanRawTargets.prefix_expectations_to_mgw_mean' in text
                                and 'PidPrefixMgwMeanAliasTargets.prefix_expectations_to_mgw_mean' in text
                                and 'DNF_JUDGE_TARGET_TYPE' in text and 'type mismatch' in text.lower(),
                                'wrong-target control missed the actual last-type rejection')
                        prefix_text = 'PREFIX_MGW_MEAN_JUDGE_RESULT '
                        partial = [strict_json(line[len(prefix_text):].encode()) for line in text.splitlines()
                                   if line.startswith(prefix_text)]
                        require(partial == expected_mean[:2],
                                'wrong-target control did not retain the first two exact accepted records')
                        result['status']='expected_target_rejection'
                        break
                    raise
                if module!='fresh-kernel':
                    snapshot.read(target)
                if module=='PidPrefixMgwMean/SemanticJudge':
                    records=policy.semantic_records(stdout,j.strict_json)
                    require(records==expected_mean,'exact accepted mean records differ')
                    result['semantic_records']=records
                elif module=='PidPrefixProbability/SemanticJudge':
                    records=policies['prefix-policy'].semantic_records(stdout,j.strict_json)
                    require(records==expected['accepted_prefix_dependency'],'six inherited records differ')
                    result['accepted_prefix_dependency_records']=records
                elif module=='PidMgwBridge/SemanticJudge':
                    records=policies['mgw-policy'].semantic_records(stdout,j.strict_json)
                    require(records==expected['accepted_mgw_dependency'],'eleven inherited records differ')
                    result['accepted_mgw_dependency_records']=records
            else:
                require(args.action=='check','incorrect final target accepted')
                result['status']='fresh_semantic_kernel_pass'
        snapshot.verify()
        remaining(stage,deadline)
    except BaseException as error:
        result.update(status='failed',failure=str(error))
    finally:
        result['commands']=[] if runner is None else runner.commands
        result['inputs']=snapshot.manifest()
        try:
            snapshot.save(output)
            artifacts={}
            for path in sorted(output.rglob('*')):
                mode=path.lstat().st_mode
                if stat.S_ISDIR(mode):
                    continue
                require(stat.S_ISREG(mode),'nonregular retained artifact')
                raw=path.read_bytes()
                artifacts[str(path.relative_to(output))]={'bytes':len(raw),'sha256':digest(raw)}
            result['artifacts']=artifacts
            snapshot.verify()
            remaining(stage,deadline)
        except BaseException as error:
            result.update(status='failed',preservation_failure=str(error))
        result['completed_utc']=utc().isoformat()
        (output/'RESULT.json').write_bytes(canonical(result))
        print(canonical({'status':result['status'],'output':str(output)}).decode(),end='')
    return 1 if result['status']=='failed' else 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (OSError,RuntimeError,ValueError,KeyError,TypeError) as error:
        print('Mean packaging replay refused: '+str(error),file=sys.stderr)
        raise SystemExit(1)
