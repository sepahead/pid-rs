"""Prepare exact MGW replay inputs. This program never starts a native child."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import os
import stat
import sys
import time


GRAPH_SHA256 = '11a229b232d7b605fe5ec5e83b4c5c36d50e7fc7dbd79991cd5e5e45c38fe9f0'
PACKAGE_ORDER = ('mathlib', 'plausible', 'LeanSearchClient', 'importGraph',
                 'proofwidgets', 'aesop', 'Qq', 'batteries', 'Cli')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def metadata(info):
    return dict(device=info.st_dev, inode=info.st_ino,
                mode=oct(stat.S_IMODE(info.st_mode)), nlink=info.st_nlink,
                uid=info.st_uid, gid=info.st_gid, bytes=info.st_size,
                mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns)


def regular(path):
    before = path.lstat()
    require(path.resolve(strict=True) == path and stat.S_ISREG(before.st_mode),
            'noncanonical or nonregular input: ' + str(path))
    with path.open('rb') as stream:
        require(metadata(os.fstat(stream.fileno())) == metadata(before),
                'input descriptor changed')
        raw = stream.read()
        require(metadata(os.fstat(stream.fileno())) == metadata(before),
                'input descriptor changed during read')
    require(metadata(path.lstat()) == metadata(before) and len(raw) == before.st_size,
            'input changed during read')
    return raw, before


def relative(value):
    require(type(value) is str and bool(value), 'relative path must be text')
    path = Path(value)
    require(not path.is_absolute() and '..' not in path.parts
            and path.as_posix() == value, 'invalid relative path')
    return path


def main():
    require(sys.version_info >= (3, 11) and sys.flags.isolated and sys.flags.no_site
            and sys.flags.ignore_environment and sys.dont_write_bytecode,
            'requires Python 3.11+ -I -S -B')
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('export', 'sysroot', 'packages', 'profile', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--profile-sha256', required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    export = args.export.resolve(strict=True)
    roots = {name: getattr(args, name).resolve(strict=True)
             for name in ('sysroot', 'packages')}
    output = args.output.absolute()
    require(output.parent.resolve(strict=True) == output.parent,
            'output parent must be canonical')
    require(not output.exists() and not output.is_symlink(), 'refuse existing output')
    graph_raw, _ = regular(export / 'audit/formal/lean-mgw-fixed-world/SOURCE_GRAPH.json')
    require(sha(graph_raw) == GRAPH_SHA256, 'source graph changed')
    graph = json.loads(graph_raw)
    require(len(graph['modules_in_compile_order']) == 9, 'source count changed')
    profile_raw, _ = regular(args.profile.resolve(strict=True))
    require(sha(profile_raw) == args.profile_sha256, 'installation profile changed')
    profile = json.loads(profile_raw)
    require(profile['schema'] == 'pid-rs-mgw-installed-profile-v1', 'profile schema')
    require(0 < len(profile['files']) <= 160000, 'installation file bound')
    require(sum(row['bytes'] for row in profile['files']) <= 12 * 1024**3,
            'installation logical-byte bound')
    captured = {}
    for row in graph['modules_in_compile_order']:
        raw, _ = regular(export / relative(row['repository_path']))
        require(sha(raw) == row['sha256'] and len(raw) == row['bytes'],
                'source graph member changed')
        captured['work/' + row['module'].replace('.', '/') + '.lean'] = raw
    captured['SOURCE_GRAPH.json'] = graph_raw
    for name in ('run-one.py', 'runtime.py', 'judge_report_validation.py',
                 'observe-installed.py', 'observe-installed-post.py', 'prepare.py'):
        captured[name] = regular(source / name)[0]
    installed = []
    seen = set()
    for row in profile['files']:
        require(row['root'] in roots, 'undeclared installed root')
        path = roots[row['root']] / relative(row['path'])
        require(path not in seen, 'duplicate installed input')
        seen.add(path)
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) and path.resolve(strict=True) == path
                and info.st_size == row['bytes']
                and oct(stat.S_IMODE(info.st_mode)) == row['mode'],
                'installation metadata differs: ' + str(path))
        installed.append(dict(path=str(path), sha256=row['sha256'],
                              bytes=row['bytes'], mode=row['mode'], metadata=metadata(info)))
    load_roots = [roots['sysroot'] / 'lib/lean'] + [
        roots['packages'] / name / '.lake/build/lib/lean' for name in PACKAGE_ORDER]
    memberships = {}
    for folder in load_roots:
        require(folder.resolve(strict=True) == folder and folder.is_dir(),
                'noncanonical load root')
        members = []
        for path in sorted(folder.rglob('*')):
            require(not path.is_symlink(), 'symbolic load member')
            if path.is_file():
                require(path in seen, 'unbound load member: ' + str(path))
                members.append(path.relative_to(folder).as_posix())
            else:
                require(path.is_dir(), 'special load member')
        memberships[str(folder)] = sorted(members)
    output.mkdir(mode=0o755)

    def write(name, raw):
        path = output / relative(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)

    def dump(name, value):
        write(name, (json.dumps(value, indent=2, allow_nan=False) + '\n').encode())

    for name, raw in captured.items():
        write(name, raw)
    for name in ('tmp', 'checks', 'preparation', 'objects/PidFiniteConvergence',
                 'objects/PidMgwFixedWorld'):
        (output / name).mkdir(parents=True, exist_ok=True)
    dump('LOAD_PATH_MEMBERS.json', memberships)
    dump('INSTALLED_BYTE_PINS.json', installed)
    dump('INSTALLED_METADATA_PINS.json', [dict(path=row['path'], metadata=row['metadata'])
                                        for row in installed])
    start = dt.datetime.now(dt.timezone.utc)
    monotonic = time.monotonic_ns()
    dump('REGISTRATION.json', dict(schema='pid-rs-mgw-fixed-source-replay-v1',
         purpose='Development replay of an already exposed, unchanged deterministic predicate',
         registered_utc=start.isoformat(), registered_monotonic_ns=monotonic,
         execution_end_utc=(start + dt.timedelta(minutes=90)).isoformat(),
         execution_end_monotonic_ns=monotonic + 90 * 60 * 10**9,
         custody_end_utc=(start + dt.timedelta(minutes=110)).isoformat(),
         custody_end_monotonic_ns=monotonic + 110 * 60 * 10**9,
         max_native_children=10, max_concurrent_native_children=1, automatic_retries=0,
         stream_bytes_each=8 * 1024**2, sampled_rss_bytes=8 * 1024**3,
         sampled_stage_disk_bytes=2 * 1024**3,
         installed_profile_sha256=args.profile_sha256,
         claim='MGW-FIXED-WORLD-COUNTEREXAMPLE-001/v1',
         no_new_candidate_or_selection_credit=True))
    lean_path = ':'.join(map(str, [output / 'objects'] + load_roots[1:]))
    commands = []
    for index, row in enumerate(graph['modules_in_compile_order'], 1):
        module_path = row['module'].replace('.', '/')
        commands.append(dict(ordinal=index, role='judge' if index == 9 else 'compiler',
            cwd=str(output / 'work'),
            argv=[str(roots['sysroot'] / 'bin/lean'), '-t', '0', '-o',
                  str(output / 'objects' / (module_path + '.olean')), module_path + '.lean'],
            timeout_seconds=60, expected_exit=0,
            stdout_rule='judge-report' if index == 9 else 'empty', LEAN_PATH=lean_path))
    commands.append(dict(ordinal=10, role='fresh-same-kernel', cwd=str(output / 'work'),
        argv=[str(roots['sysroot'] / 'bin/leanchecker'), '--fresh', 'PidMgwFixedWorld.Candidate'],
        timeout_seconds=300, expected_exit=0, stdout_rule='empty', LEAN_PATH=lean_path))
    dump('EXECUTION_PLAN.json', dict(commands=commands, environment={
        'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
        'TMPDIR': str(output / 'tmp'), 'LEAN_SYSROOT': str(roots['sysroot'])}))
    objects = {path.relative_to(output).as_posix(): dict(kind='directory',
               mode=oct(stat.S_IMODE(path.lstat().st_mode)))
               for path in [output / 'objects'] + sorted((output / 'objects').rglob('*'))}
    dump('OBJECT_STATE.json', objects)
    source_pins = []
    for name in captured:
        raw, info = regular(output / name)
        source_pins.append(dict(path=str(output / name), sha256=sha(raw), bytes=len(raw),
                               mode=oct(stat.S_IMODE(info.st_mode))))
    dump('SOURCE_PINS.json', source_pins)
    bindings = {name: sha((output / name).read_bytes()) for name in (
        'REGISTRATION.json', 'EXECUTION_PLAN.json', 'SOURCE_PINS.json',
        'INSTALLED_METADATA_PINS.json', 'INSTALLED_BYTE_PINS.json', 'LOAD_PATH_MEMBERS.json')}
    dump('ADMISSION.json', dict(native_execution_admitted=False,
        caller_sha256=sha(captured['run-one.py']), fixed_bindings=bindings,
        initial_object_state_sha256=sha((output / 'OBJECT_STATE.json').read_bytes()),
        required_root_decision='Read exact caller and plan; bind full INSTALLED_PRE and controls before admission'))
    dump('preparation/PREPARED.json', dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        source_files=9, installed_files=len(installed), native_children=0,
        compiled_objects_copied=0, installed_bytes_freshly_hashed=False,
        profile_sha256=args.profile_sha256, export=str(export),
        scope='Source copies and current metadata only. Native execution remains unadmitted.'))
    print(json.dumps(dict(status='prepared; native execution not admitted', output=str(output),
                          native_children=0, installed_files=len(installed))))


if __name__ == '__main__':
    main()
