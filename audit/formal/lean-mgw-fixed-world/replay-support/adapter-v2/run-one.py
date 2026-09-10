from pathlib import Path
import datetime as dt
import hashlib
from types import ModuleType
import json
import os
import stat
import sys
import time

if not (sys.version_info >= (3, 11) and sys.flags.isolated and sys.flags.no_site
        and sys.flags.ignore_environment and sys.dont_write_bytecode and sys.flags.optimize == 0):
    raise RuntimeError('requires Python 3.11+ -I -S -B without -O')
if len(sys.argv) != 3 or len(sys.argv[2]) != 64:
    raise RuntimeError('usage: run-one.py ORDINAL ADMISSION_SHA256')
stage = Path(__file__).resolve().parent
ordinal = int(sys.argv[1])
admission_raw = (stage / 'ADMISSION.json').read_bytes()
if hashlib.sha256(admission_raw).hexdigest() != sys.argv[2]:
    raise RuntimeError('out-of-band admission binding differs')
admission = json.loads(admission_raw)
if admission['native_execution_admitted'] is not True:
    raise RuntimeError('native execution has not been admitted')
if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != admission['caller_sha256']:
    raise RuntimeError('caller drift')
for name, digest in admission['fixed_bindings'].items():
    if hashlib.sha256((stage / name).read_bytes()).hexdigest() != digest:
        raise RuntimeError('fixed binding drift: ' + name)
reg = json.loads((stage / 'REGISTRATION.json').read_bytes())
plan = json.loads((stage / 'EXECUTION_PLAN.json').read_bytes())
if not 1 <= ordinal <= len(plan['commands']) <= reg['max_native_children']:
    raise RuntimeError('ordinal outside admitted plan')
if (stage / 'STOP.json').exists():
    raise RuntimeError('prior unexpected outcome requires separate review')
if ordinal > 1:
    prior = stage / 'checks' / ('%02d' % (ordinal - 1)) / 'ROOT_ACCEPTED.json'
    prior_record = json.loads(prior.read_bytes())
    if prior_record['ordinal'] != ordinal - 1 or prior_record['accepted_for_next_command'] is not True:
        raise RuntimeError('preceding actual result not accepted by root')
    for name, path in [('object_state_sha256', stage / 'OBJECT_STATE.json'),
                       ('result_sha256', prior.parent / 'RESULT.json')]:
        if hashlib.sha256(path.read_bytes()).hexdigest() != prior_record[name]:
            raise RuntimeError('preceding result or reviewed object state changed')
elif hashlib.sha256((stage / 'OBJECT_STATE.json').read_bytes()).hexdigest() != admission['initial_object_state_sha256']:
    raise RuntimeError('initial object state changed')
row = plan['commands'][ordinal - 1]
out = stage / 'checks' / ('%02d' % ordinal)
out.mkdir()

def on_time():
    return time.monotonic_ns() < reg['execution_end_monotonic_ns'] and dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(reg['execution_end_utc'])

def fingerprint(value):
    return {'device': value.st_dev, 'inode': value.st_ino, 'mode': oct(stat.S_IMODE(value.st_mode)),
            'nlink': value.st_nlink, 'uid': value.st_uid, 'gid': value.st_gid,
            'bytes': value.st_size, 'mtime_ns': value.st_mtime_ns, 'ctime_ns': value.st_ctime_ns}

def file_record(path):
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or path.is_symlink():
        raise RuntimeError('nonregular owned input: ' + str(path))
    h = hashlib.sha256()
    with path.open('rb') as handle:
        if fingerprint(os.fstat(handle.fileno())) != fingerprint(before):
            raise RuntimeError('descriptor changed: ' + str(path))
        remaining = before.st_size
        while remaining:
            block = handle.read(min(1048576, remaining))
            if not block:
                raise RuntimeError('file truncated while hashing')
            h.update(block)
            remaining -= len(block)
        if handle.read(1):
            raise RuntimeError('file grew while hashing')
        after = os.fstat(handle.fileno())
    if fingerprint(before) != fingerprint(after) or fingerprint(before) != fingerprint(path.lstat()):
        raise RuntimeError('input changed while hashing: ' + str(path))
    return {'path': str(path), 'sha256': h.hexdigest(), 'bytes': before.st_size, 'mode': oct(stat.S_IMODE(before.st_mode))}

def object_records():
    records = {}
    for folder in [stage / 'objects']:
        if folder.is_symlink():
            raise RuntimeError('symbolic object root: ' + str(folder))
        if not folder.exists():
            continue
        if not stat.S_ISDIR(folder.lstat().st_mode):
            raise RuntimeError('non-directory object root: ' + str(folder))
        records[folder.relative_to(stage).as_posix()] = {'kind': 'directory', 'mode': oct(stat.S_IMODE(folder.lstat().st_mode))}
        for path in sorted(folder.rglob('*')):
            if path.is_symlink():
                raise RuntimeError('symbolic object path: ' + str(path))
            if path.is_file():
                record = file_record(path)
                records[path.relative_to(stage).as_posix()] = record
            elif path.is_dir():
                records[path.relative_to(stage).as_posix()] = {'kind': 'directory', 'mode': oct(stat.S_IMODE(path.lstat().st_mode))}
            else:
                raise RuntimeError('special object entry: ' + str(path))
    return records

def verify_fixed(label):
    sources = json.loads((stage / 'SOURCE_PINS.json').read_bytes())
    # Exact loader-relevant source trees; runtime output trees have separate custody.
    work_roots = [stage / 'work']
    def walk_error(error):
        raise RuntimeError('source tree walk failed: ' + str(error))
    for work_root in work_roots:
        if work_root.is_symlink() or not work_root.is_dir() or work_root.resolve() != work_root:
            raise RuntimeError('noncanonical source work root: ' + str(work_root))
        expected_files = {Path(pin['path']) for pin in sources if Path(pin['path']).is_relative_to(work_root)}
        expected_dirs = {work_root}
        for path in expected_files:
            expected_dirs.update(parent for parent in path.parents if parent.is_relative_to(work_root))
        seen_files, seen_dirs = set(), {work_root}
        for directory, dirs, files in os.walk(work_root, followlinks=False, onerror=walk_error):
            for name in dirs + files:
                path = Path(directory) / name
                mode = path.lstat().st_mode
                if stat.S_ISREG(mode) and path in expected_files:
                    seen_files.add(path)
                elif stat.S_ISDIR(mode) and path in expected_dirs:
                    seen_dirs.add(path)
                else:
                    raise RuntimeError('extra, symbolic or special source entry: ' + str(path))
        if seen_files != expected_files or seen_dirs != expected_dirs:
            raise RuntimeError('source tree membership differs from frozen pins: ' + str(work_root))
    for pin in sources:
        actual = file_record(Path(pin['path']))
        if any(actual[k] != pin[k] for k in ('sha256', 'bytes', 'mode')):
            raise RuntimeError('source/tool drift: ' + pin['path'])
    installed = json.loads((stage / 'INSTALLED_METADATA_PINS.json').read_bytes())
    for i, pin in enumerate(installed):
        current = Path(pin['path']).lstat()
        if not stat.S_ISREG(current.st_mode) or fingerprint(current) != pin['metadata']:
            raise RuntimeError('installed input metadata changed: ' + pin['path'])
        if i % 20000 == 0 and not on_time():
            raise RuntimeError('registered execution window ended during metadata observation')
    memberships = json.loads((stage / 'LOAD_PATH_MEMBERS.json').read_bytes())
    for name, expected in memberships.items():
        folder = Path(name)
        if expected is None:
            if folder.exists() or folder.is_symlink():
                raise RuntimeError('previously absent installed load root appeared')
            continue
        if folder.resolve(strict=True) != folder or not folder.is_dir():
            raise RuntimeError('noncanonical installed load root')
        actual_members = []
        for directory, dirs, files in os.walk(folder, followlinks=False, onerror=walk_error):
            for entry in dirs + files:
                path = Path(directory) / entry
                info = path.lstat()
                if stat.S_ISREG(info.st_mode):
                    actual_members.append(path.relative_to(folder).as_posix())
                elif not stat.S_ISDIR(info.st_mode):
                    raise RuntimeError('symbolic or special installed load member')
        if sorted(actual_members) != expected:
            raise RuntimeError('installed load-path membership changed')
        if not on_time():
            raise RuntimeError('registered execution window ended during load-path observation')
    record = {'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'sources_hashed': len(sources), 'installed_metadata_observations': len(installed), 'load_roots_observed': len(memberships), 'scope': 'Installed bytes are bound by separate full pre/post hashes; these per-child metadata and file-membership observations are non-atomic and do not trace actual loaded modules.'}
    (out / ('FIXED-' + label + '.json')).write_text(json.dumps(record, indent=2) + '\n')

def disk_bytes():
    total = sum(p.stat().st_size for p in stage.rglob('*') if p.is_file())
    if total > reg['sampled_stage_disk_bytes']:
        raise RuntimeError('sampled stage logical-byte limit exceeded')
    return total

failure = None
runner = None
record = None
before_disk = None
after_disk = None
try:
    if not on_time():
        raise RuntimeError('registered execution window ended')
    verify_fixed('before')
    expected_objects = json.loads((stage / 'OBJECT_STATE.json').read_bytes())
    if object_records() != expected_objects:
        raise RuntimeError('object membership or bytes differ from last reviewed state')
    before_disk = disk_bytes()
    environment = dict(plan['environment'])
    environment['LEAN_PATH'] = row['LEAN_PATH']
    if set(environment) != set(plan['environment']) | {'LEAN_PATH'}:
        raise RuntimeError('unexpected environment key')
    runtime = stage / 'runtime.py'
    runtime_raw = runtime.read_bytes()
    if hashlib.sha256(runtime_raw).hexdigest() != 'bd8a9f2272a20422863c9902ce2148d2957471bb958d13949fece923cb6a7f5d':
        raise RuntimeError('runtime drift')
    module = ModuleType('reviewed_runtime')
    module.__file__ = str(runtime)
    exec(compile(runtime_raw, str(runtime), 'exec', dont_inherit=True, optimize=0), module.__dict__)
    runner = module.Runner(out, environment, preparation=False)
    caught = None
    if not on_time():
        raise RuntimeError('registered execution window ended before native child')
    try:
        runner.run(row['argv'], Path(row['cwd']), 'native',
                   timeout=min(row['timeout_seconds'], (reg['execution_end_monotonic_ns'] - time.monotonic_ns()) / 10**9),
                   cap=reg['stream_bytes_each'], memory=reg['sampled_rss_bytes'], allow_stdout=True)
    except Exception as error:
        caught = str(error)
    if len(runner.commands) != 1:
        raise RuntimeError('missing actual native command record: ' + str(caught))
    record = runner.commands[0]
    expected_exit = row['expected_exit']
    native_status_matches = record['returncode'] == expected_exit if type(expected_exit) is int else (expected_exit == 'nonzero' and type(record['returncode']) is int and record['returncode'] > 0)
    if record['failure'] is not None or record['execution_error'] is not None or record['remaining_live_group_processes'] or not native_status_matches:
        raise RuntimeError('unexpected native outcome: ' + str(caught))
    stdout = (out / '00-native' / 'stdout.log').read_bytes()
    stderr = (out / '00-native' / 'stderr.log').read_bytes()
    for label, raw in [('stdout', stdout), ('stderr', stderr)]:
        if len(raw) != record['retained_' + label + '_bytes'] or hashlib.sha256(raw).hexdigest() != record[label + '_sha256']:
            raise RuntimeError('retained native stream differs from command record')
    if stderr:
        raise RuntimeError('nonempty native stderr requires separate review')
    if row['stdout_rule'] == 'empty' and stdout:
        raise RuntimeError('unexpected native stdout')
    if row['stdout_rule'] == 'judge-report':
        if hashlib.sha256(stdout).hexdigest() != 'f01413ae4f951a39d5df3b493b7438b2ac4e4817f59454bfbef593155c6f6b14':
            raise RuntimeError('judge output differs from the frozen historical report')
        validator = stage / 'judge_report_validation.py'
        validator_raw = validator.read_bytes()
        validation = ModuleType('reviewed_report_validation')
        validation.__file__ = str(validator)
        exec(compile(validator_raw, str(validator), 'exec', dont_inherit=True, optimize=0), validation.__dict__)
        validation.validate_judge_report(stdout)
    if row['stdout_rule'] not in ('empty', 'judge-report'):
        raise RuntimeError('unadmitted stdout rule')
    verify_fixed('after')
    after_objects = object_records()
    (out / 'OBJECTS_AFTER.json').write_text(json.dumps(after_objects, indent=2) + '\n')
    after_disk = disk_bytes()
    if not on_time():
        raise RuntimeError('native result or custody returned after registered execution window')
except BaseException as error:
    failure = repr(error)
finally:
    result = {'ordinal': ordinal, 'row': row, 'completed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'completed_monotonic_ns': time.monotonic_ns(), 'failure': failure,
              'sampled_stage_bytes_before': before_disk, 'sampled_stage_bytes_after': after_disk,
              'commands': [] if runner is None else runner.commands,
              'scope': 'One registered native command. Expected status is insufficient: root must inspect exact compiler/judge diagnostics, raw producer binding and actual outer tool result before ROOT_ACCEPTED. No independent kernel, mutation, provenance or completion credit from this file alone.'}
    (out / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    if failure is not None:
        (stage / 'STOP.json').write_text(json.dumps({'ordinal': ordinal, 'failure': failure, 'utc': result['completed_utc']}, indent=2) + '\n')
if failure is not None:
    raise RuntimeError(failure)
if not on_time():
    raise RuntimeError('receipt returned after registered execution window; root must reject')
print(json.dumps({'ordinal': ordinal, 'actual_native_exit': record['returncode'], 'status': 'expected native status; root raw review pending'}))
