"""Bounded synthetic checks of the adapter functions; no native execution."""
from pathlib import Path
from types import ModuleType
import ast
import datetime as dt
import hashlib
import json
import os
import stat
import sys
import time


def need(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


need(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
     'requires -I -S -B')
need(len(sys.argv) == 3, 'usage: static-controls.py OUTPUT PLAN_SHA256')
source = Path(__file__).resolve().parent
plan_raw = (source.parent / 'STATIC_CONTROL_PLAN_V2.json').read_bytes()
need(sha(plan_raw) == sys.argv[2], 'control plan binding differs')
plan = json.loads(plan_raw)
for name, digest in plan['files'].items():
    need(sha((source / name).read_bytes()) == digest, 'control source drift')
output = Path(sys.argv[1]).absolute()
need(output.parent.resolve(strict=True) == output.parent, 'noncanonical output parent')
output.mkdir()
caller = (source / 'run-one.py').read_bytes()
tree = ast.parse(caller)
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
function_names = {node.name for node in functions}
need(function_names == {'on_time', 'fingerprint', 'file_record', 'object_records',
                       'verify_fixed', 'disk_bytes'}, 'adapter function selection changed')
code = compile(ast.Module(body=functions, type_ignores=[]), str(source / 'run-one.py'),
               'exec', dont_inherit=True, optimize=sys.flags.optimize)
cases = []
entry_cases = []

# Run the exact entry prefix through its setup and function definitions. The
# scientific/native try block is excluded from this synthetic test object.
prefix_end = next(i for i, node in enumerate(tree.body)
                  if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name)
                  and t.id == 'failure' for t in node.targets))
prefix_code = compile(ast.Module(body=tree.body[:prefix_end], type_ignores=[]),
                      str(source / 'run-one.py'), 'exec', dont_inherit=True,
                      optimize=sys.flags.optimize)


def entry_check(name, mutation, cause=None, ordinal=1):
    stage = output / ('entry-' + name)
    (stage / 'checks').mkdir(parents=True)
    (stage / 'run-one.py').write_bytes(caller)
    dump(stage / 'REGISTRATION.json', dict(max_native_children=10))
    dump(stage / 'EXECUTION_PLAN.json', dict(commands=[dict(ordinal=i) for i in range(1, 11)]))
    dump(stage / 'OBJECT_STATE.json', {})
    admission = dict(native_execution_admitted=True, caller_sha256=sha(caller),
        initial_object_state_sha256=sha((stage / 'OBJECT_STATE.json').read_bytes()),
        fixed_bindings={name: sha((stage / name).read_bytes())
                        for name in ('REGISTRATION.json', 'EXECUTION_PLAN.json')})
    changed_pin = mutation(stage, admission)
    dump(stage / 'ADMISSION.json', admission)
    pin = sha((stage / 'ADMISSION.json').read_bytes()) if changed_pin is None else changed_pin
    previous_argv = sys.argv
    sys.argv = [str(stage / 'run-one.py'), str(ordinal), pin]
    try:
        exec(prefix_code, dict(__file__=str(stage / 'run-one.py'), __name__='synthetic_entry'))
    except (RuntimeError, FileExistsError, FileNotFoundError) as error:
        need(cause is not None and (str(error).startswith(cause) or type(error).__name__ == cause),
             'wrong entry rejection: ' + name + ': ' + str(error))
        entry_cases.append(dict(case=name, outcome='rejected', cause=str(error)))
    else:
        need(cause is None, 'unexpected entry acceptance: ' + name)
        entry_cases.append(dict(case=name, outcome='accepted'))
    finally:
        sys.argv = previous_argv


if sys.flags.optimize == 0:
    entry_check('positive-prefix', lambda p, a: None)
    entry_check('wrong-admission-pin', lambda p, a: '0' * 64, 'out-of-band admission binding differs')
    entry_check('false-admission', lambda p, a: a.update(native_execution_admitted=False),
                'native execution has not been admitted')
    entry_check('integer-admission', lambda p, a: a.update(native_execution_admitted=1),
                'native execution has not been admitted')
    entry_check('string-admission', lambda p, a: a.update(native_execution_admitted='true'),
                'native execution has not been admitted')
    entry_check('caller-drift', lambda p, a: a.update(caller_sha256='0' * 64), 'caller drift')
    entry_check('fixed-plan-drift', lambda p, a: dump(p / 'EXECUTION_PLAN.json', {}), 'fixed binding drift')
    entry_check('ordinal-outside-plan', lambda p, a: None, 'ordinal outside admitted plan', ordinal=0)
    entry_check('prior-stop', lambda p, a: dump(p / 'STOP.json', {}), 'prior unexpected outcome')
    entry_check('initial-object-drift', lambda p, a: dump(p / 'OBJECT_STATE.json', {'extra': 1}),
                'initial object state changed')
    entry_check('missing-root-review', lambda p, a: None, 'FileNotFoundError', ordinal=2)
    entry_check('repeat-output', lambda p, a: (p / 'checks/01').mkdir(), 'FileExistsError')
else:
    entry_check('optimized-native-entry-refused', lambda p, a: None,
                'requires Python 3.11+ -I -S -B without -O')


def fixture(name):
    stage = output / name
    for directory in ('work', 'objects', 'load', 'checks'):
        (stage / directory).mkdir(parents=True, exist_ok=True)
    work = stage / 'work/A.lean'
    work.write_bytes(b'-- synthetic source\n')
    installed = stage / 'load/A.olean'
    installed.write_bytes(b'synthetic object; never given to Lean\n')
    namespace = dict(Path=Path, dt=dt, hashlib=hashlib, json=json, os=os,
                     stat=stat, sys=sys, time=time, stage=stage, out=stage / 'checks',
                     reg=dict(execution_end_monotonic_ns=time.monotonic_ns() + 60 * 10**9,
                              execution_end_utc=(dt.datetime.now(dt.timezone.utc)
                                                 + dt.timedelta(seconds=60)).isoformat(),
                              sampled_stage_disk_bytes=1024**2))
    exec(code, namespace)
    dump(stage / 'SOURCE_PINS.json', [namespace['file_record'](work)])
    dump(stage / 'INSTALLED_METADATA_PINS.json', [dict(path=str(installed),
         metadata=namespace['fingerprint'](installed.lstat()))])
    dump(stage / 'LOAD_PATH_MEMBERS.json', {str(stage / 'load'): ['A.olean']})
    return stage, namespace


def check(name, mutation, operation='verify_fixed', cause=None):
    stage, namespace = fixture(name)
    mutation(stage, namespace)
    try:
        value = namespace[operation]('synthetic') if operation == 'verify_fixed' else namespace[operation]()
    except RuntimeError as error:
        need(cause is not None and str(error).startswith(cause),
             'wrong rejection cause: ' + name + ': ' + str(error))
        cases.append(dict(case=name, outcome='rejected', cause=str(error)))
    else:
        need(cause is None, 'unexpected acceptance: ' + name)
        cases.append(dict(case=name, outcome='accepted'))


check('positive-fixed-inputs', lambda p, n: None)
check('positive-empty-object-tree', lambda p, n: None, 'object_records')
check('positive-absent-load-root', lambda p, n: dump(p / 'LOAD_PATH_MEMBERS.json',
      {str(p / 'load'): ['A.olean'], str(p / 'absent'): None}))
check('absent-load-root-appeared', lambda p, n: dump(p / 'LOAD_PATH_MEMBERS.json',
      {str(p / 'load'): None}), cause='previously absent installed load root appeared')
check('missing-source', lambda p, n: (p / 'work/A.lean').unlink(),
      cause='source tree membership differs')
check('extra-source', lambda p, n: (p / 'work/B.lean').write_bytes(b'extra'),
      cause='extra, symbolic or special source entry')
check('changed-source', lambda p, n: (p / 'work/A.lean').write_bytes(b'changed'),
      cause='source/tool drift')
check('symbolic-source', lambda p, n: (p / 'work/B.lean').symlink_to(p / 'work/A.lean'),
      cause='extra, symbolic or special source entry')
check('changed-installed-input', lambda p, n: (p / 'load/A.olean').write_bytes(b'changed'),
      cause='installed input metadata changed')
check('extra-installed-input', lambda p, n: (p / 'load/B.olean').write_bytes(b'extra'),
      cause='installed load-path membership changed')
check('symbolic-installed-input', lambda p, n: (p / 'load/B.olean').symlink_to(p / 'load/A.olean'),
      cause='symbolic or special installed load member')
check('symbolic-object', lambda p, n: (p / 'objects/A.olean').symlink_to(p / 'load/A.olean'),
      'object_records', 'symbolic object path')
check('expired-window', lambda p, n: n['reg'].update(execution_end_monotonic_ns=0),
      cause='registered execution window ended during metadata observation')
check('disk-limit', lambda p, n: n['reg'].update(sampled_stage_disk_bytes=0),
      'disk_bytes', 'sampled stage logical-byte limit exceeded')

# Exercise the exact runtime source-loader statements, stopping before Runner
# construction. This is a function/loader test, not a test of native execution.
main_try = next(node for node in tree.body if isinstance(node, ast.Try))
start = next(i for i, node in enumerate(main_try.body)
             if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name)
             and t.id == 'runtime' for t in node.targets))
end = next(i for i, node in enumerate(main_try.body)
           if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name)
           and t.id == 'runner' for t in node.targets))
loader_code = compile(ast.Module(body=main_try.body[start:end], type_ignores=[]),
                      str(source / 'run-one.py'), 'exec', dont_inherit=True,
                      optimize=sys.flags.optimize)
loader_stage = output / 'source-loader'
loader_stage.mkdir()
(loader_stage / 'runtime.py').write_bytes((source / 'runtime.py').read_bytes())
(loader_stage / '__pycache__').mkdir()
(loader_stage / '__pycache__/runtime.cpython-314.pyc').write_bytes(b'invalid cache sentinel')
namespace = dict(stage=loader_stage, hashlib=hashlib, ModuleType=ModuleType)
exec(loader_code, namespace)
need(namespace['module'].__file__ == str(loader_stage / 'runtime.py')
     and callable(namespace['module'].Runner.run), 'exact source loader failed')
cases.append(dict(case='invalid-bytecode-cache-ignored-by-source-loader', outcome='accepted'))
(loader_stage / 'runtime.py').write_bytes(b'raise RuntimeError("must not execute")\n')
try:
    exec(loader_code, dict(stage=loader_stage, hashlib=hashlib, ModuleType=ModuleType))
except RuntimeError as error:
    need(str(error) == 'runtime drift', 'wrong loader rejection')
    cases.append(dict(case='changed-runtime-rejected-before-exec', outcome='rejected'))
else:
    raise RuntimeError('changed runtime accepted')

validator = ModuleType('synthetic_report_validation')
validator.__file__ = str(source / 'judge_report_validation.py')
exec(compile((source / 'judge_report_validation.py').read_bytes(), validator.__file__,
             'exec', dont_inherit=True, optimize=sys.flags.optimize), validator.__dict__)
report = validator.selfcheck()
need(len(cases) == 16 and report['case_count'] == 43
     and len(entry_cases) == (12 if sys.flags.optimize == 0 else 1), 'control count differs')
result = dict(status='synthetic controls completed', optimization=sys.flags.optimize,
              entry_prefix_cases=entry_cases, adapter_cases=cases,
              report_validator=report, native_children=0,
              scope='Exact entry prefix, adapter function bodies, and source-loader statements on synthetic inputs; no complete-entry, process-monitor, native-proof, or independent acceptance credit. Optimized native entry is deliberately refused.')
dump(output / 'RESULT.json', result)
print(json.dumps(dict(status=result['status'], entry_prefix_cases=len(entry_cases),
                      adapter_cases=16, report_cases=43,
                      native_children=0, optimization=sys.flags.optimize)))
