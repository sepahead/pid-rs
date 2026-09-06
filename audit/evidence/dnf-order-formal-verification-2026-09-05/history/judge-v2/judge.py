#!/usr/bin/env python3
"""Local revision-2 DNF/order judge. It adds no claim of external judge custody."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import selectors
import signal
import stat
import subprocess
import sys
import time
from types import ModuleType

if not (sys.version_info >= (3, 11) and sys.flags.isolated and sys.flags.no_site
        and sys.flags.ignore_environment and sys.dont_write_bytecode
        and sys.flags.optimize in (0, 1)):
    raise SystemExit('judge.py requires Python 3.11+ -I -S -B, optionally -O')

LANE = Path(__file__).resolve().parent
PROJECT_RELATIVE = 'audit/formal/lean'
INFORMATIVE_HELPER = 'scripts/check-lean-sxpid3-informative-invariance.py'
INFORMATIVE_SHA256 = '297c92b7d00272167c4be36c33fb17fb57d8f4958f3ce89615e4200bd30205fc'
BASE_HELPER = 'scripts/check-lean-finite-convergence.py'
BASE_SHA256 = '3ea61295232a03b08522a10257f82865038e760fe47eda34b7f470d2f8f268a0'
SOURCE_PINS = {
    'audit/formal/lean/PidFiniteConvergence.lean': '3b99c57000d6bf14077e8caf4de2f86d27f9654a8d984c9fc59d720947de84f8',
    'audit/formal/lean/PidFiniteConvergence/Deterministic.lean': 'e9dbd7c5b4578aabf92b76c0b8b684db4c1c1038dcdb033239b0076685c41610',
    'audit/formal/lean/PidFiniteConvergence/SxEventBridge.lean': 'cfedf974c73e11e56041013a47797462100f4b896235d6c4185c9ca0a232d77e',
    'audit/formal/lean/lake-manifest.json': '6527e482d9bdbcbf48bf47a420df1ccf9b99958ea0152693446816891cc910af',
    'audit/formal/lean/lakefile.toml': 'ec5def1f5f0aa36218f767993c144a1b76ed9b77d6a429028dd5bb8f857354e0',
    'audit/formal/lean/lean-toolchain': '302cd63c54178885b89e669f33b38f12f4dd7ae7e5cac537b3203e3768d8fb2b',
    INFORMATIVE_HELPER: INFORMATIVE_SHA256,
    BASE_HELPER: BASE_SHA256,
}
CONTRACT_SHA256 = '569bf11314d02ff599309bfcfa0d80109bf0f121032d5d665e8519513219a5c0'
THEOREMS = (
    'order_iff_dnf', 'antichain_antisymm', 'dnf_injective_on_antichains',
    'source_event_iff_dnf', 'order_implies_source_event_subset',
    'order_iff_implication_on_realizing_domain', 'alternate_values_realize_all_patterns',
    'source_event_injective_on_realizing_domain', 'order_implies_target_restricted_subset',
    'singleton_event_collision', 'singleton_not_all_patterns', 'binary_diagonal_collision',
    'antichain_premise_is_load_bearing',
)
MODULES = ('Contract', 'JudgeCore', 'JudgeTargets', 'JudgeAliases', 'ContractJudge', 'SemanticJudge')
ALLOWED_AXIOMS = frozenset({'Classical.choice', 'Quot.sound', 'propext'})
TIMEOUT_SECONDS = 600
MEMORY_BYTES = 4 * 1024**3
OUTPUT_BYTES = 4 * 1024**2
HEX = re.compile(r'[0-9a-f]{64}\Z')


class JudgeError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise JudgeError(message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True,
                       allow_nan=False) + '\n').encode()


def strict_json(raw: bytes) -> object:
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(JudgeError('nonfinite JSON')))


def file_identity(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


class Snapshot:
    def __init__(self) -> None:
        self.inputs: dict[str, tuple[tuple[int, ...], bytes]] = {}

    def read(self, path: Path) -> bytes:
        path = path.absolute()
        require(path == path.resolve(strict=True), 'noncanonical or symlink input: ' + str(path))
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
                'input must be a regular single-link file: ' + str(path))
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            opened = os.fstat(descriptor)
            require(file_identity(opened) == file_identity(before), 'input changed before capture')
            with os.fdopen(descriptor, 'rb', closefd=False) as stream:
                raw = stream.read()
            after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        require(file_identity(after) == file_identity(before)
                == file_identity(path.lstat()) and len(raw) == before.st_size,
                'input changed during capture: ' + str(path))
        captured = (file_identity(before), raw)
        previous = self.inputs.get(str(path))
        require(previous is None or previous == captured, 'input changed since prior capture')
        self.inputs[str(path)] = captured
        return raw

    def verify(self) -> None:
        for name, (identity, raw) in list(self.inputs.items()):
            path = Path(name)
            require(file_identity(path.lstat()) == identity and self.read(path) == raw,
                    'input changed after capture: ' + name)

    def save(self, output: Path) -> None:
        directory = output / 'input-bytes'
        directory.mkdir(exist_ok=True)
        for _, raw in self.inputs.values():
            target = directory / digest(raw)
            if target.exists():
                require(target.read_bytes() == raw, 'captured byte archive collision')
            else:
                target.write_bytes(raw)

    def manifest(self) -> dict[str, object]:
        return {name: {'sha256': digest(raw), 'bytes': len(raw), 'identity': list(identity)}
                for name, (identity, raw) in sorted(self.inputs.items())}


def load_helpers(root: Path, snapshot: Snapshot) -> tuple[ModuleType, ModuleType]:
    helper_path = root / INFORMATIVE_HELPER
    raw = snapshot.read(helper_path)
    require(digest(raw) == INFORMATIVE_SHA256, 'informative custody helper digest changed')
    helper = ModuleType('reviewed_informative_helper')
    helper.__file__ = str(helper_path)
    exec(compile(raw, str(helper_path), 'exec', dont_inherit=True, optimize=sys.flags.optimize),
         helper.__dict__)
    base = helper.load_base_checker()
    require(digest(snapshot.read(root / BASE_HELPER)) == BASE_SHA256, 'base helper digest changed')
    return helper, base


def candidate_policy(raw: bytes, base: ModuleType, path: Path) -> None:
    source = raw.decode('utf-8', errors='strict')
    masked = base.mask_lean_comments_and_strings(source, path)
    imports = re.findall(r'(?m)^\s*import\s+([^\n]+)$', masked)
    require(imports == ['Contract'], 'candidate import roster must be exactly Contract')
    require(re.findall(r'(?m)^\s*namespace\s+([^\n]+)$', masked)
            == ['PidSxDnfOrderCandidate'], 'candidate namespace roster changed')
    require(re.findall(r'(?m)^\s*end\s+([^\n]+)$', masked)
            == ['PidSxDnfOrderCandidate'], 'candidate namespace closing changed')
    options = re.findall(r'(?m)^\s*set_option\s+([^\n]+)$', masked)
    require(options == ['autoImplicit false', 'warningAsError true'],
            'candidate must retain exactly the two strict options')
    forbidden = re.search(r'\b(?:sorry|sorryAx|admit|axiom|constant|opaque|native_decide|unsafe|'
                          r'partial|run_cmd|run_tac|run_elab|run_meta|run_io|by_elab|eval_expr|elab|macro|syntax|initialize|'
                          r'builtin_initialize|implemented_by|extern|attribute|export|'
                          r'deriving|instance|include|omit|section|noncomputable|notation|infix|infixl|infixr|prefix|postfix)\b|#|@\[', masked)
    require(forbidden is None, 'candidate source contains prohibited code')
    declarations = base.source_declaration_inventory(source, path)
    public = []
    for line in masked.splitlines():
        matched = re.match(r'^\s*(private\s+)?(theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_]*)\b', line)
        if matched and not matched.group(1):
            require(matched.group(2) == 'theorem', 'public exports must be theorems')
            public.append(matched.group(3))
    require(tuple(public) == THEOREMS, 'candidate public theorem source roster changed')
    require(len(declarations) == len(re.findall(r'(?m)^\s*(?:private\s+)?(?:theorem|lemma)\s+', masked)),
            'candidate has an unsupported top-level declaration')


def strict_axiom_output(raw: bytes) -> list[dict[str, object]]:
    lines = raw.decode('utf-8', errors='strict').splitlines()
    require(len(lines) == len(THEOREMS), 'theorem evidence line count changed')
    records = []
    for theorem, line in zip(THEOREMS, lines, strict=True):
        prefix = 'DNF_JUDGE_RESULT '
        require(line.startswith(prefix), 'unexpected theorem evidence prefix')
        record = strict_json(line[len(prefix):].encode())
        require(type(record) is dict and set(record) == {
            'theorem', 'raw_target', 'alias_target', 'universes', 'full_elaborated_type',
            'axioms', 'status'}, 'theorem evidence fields changed')
        require(record['theorem'] == 'PidSxDnfOrderCandidate.' + theorem
                and record['raw_target'] == 'PidSxDnfOrderJudgeTargets.' + theorem
                and record['alias_target'] == 'PidSxDnfOrderJudgeAliases.' + theorem
                and record['status'] == 'accepted', 'theorem evidence identity changed')
        for name in ('universes', 'axioms'):
            require(type(record[name]) is list and all(type(x) is str for x in record[name])
                    and len(record[name]) == len(set(record[name])), 'invalid name roster: ' + name)
        require(set(record['axioms']) <= ALLOWED_AXIOMS
                and record['axioms'] == sorted(record['axioms']), 'disallowed or unordered axiom roster')
        require(type(record['full_elaborated_type']) is str and bool(record['full_elaborated_type']),
                'missing elaborated theorem type')
        records.append(record)
    return records


def resource_limits() -> None:
    # macOS rejects RLIMIT_AS at this value. Lean also receives -M 4096.
    if sys.platform != 'darwin':
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def group_processes(group: int) -> list[tuple[int, int, str]]:
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,pgid=,rss=,stat='],
        env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}, stdin=subprocess.DEVNULL,
        capture_output=True, timeout=5, check=False)
    require(result.returncode == 0 and result.stderr == b'', 'process-group observation failed')
    found = []
    for line in result.stdout.decode('ascii').splitlines():
        pid, pgid, rss, state = line.split()
        if int(pgid) == group and not state.startswith('Z'):
            found.append((int(pid), int(rss) * 1024, state))
    return found


class Runner:
    def __init__(self, output: Path, environment: dict[str, str]) -> None:
        self.output = output
        self.environment = environment
        self.commands: list[dict[str, object]] = []

    def run(self, command: list[str], cwd: Path, label: str, *, timeout: float = TIMEOUT_SECONDS,
            cap: int = OUTPUT_BYTES, memory: int = MEMORY_BYTES,
            allow_stdout: bool = False) -> bytes:
        directory = self.output / f'{len(self.commands):02d}-{label}'
        directory.mkdir()
        started = time.monotonic()
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        stdout, stderr = bytearray(), bytearray()
        failure, spawn_error, process = None, None, None
        peak_rss = 0
        cleanup_remaining = []
        selector = selectors.DefaultSelector()
        try:
            process = subprocess.Popen(command, cwd=cwd, env=self.environment,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True, preexec_fn=resource_limits)
            for stream, data in ((process.stdout, stdout), (process.stderr, stderr)):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, data)
            next_sample = started
            while selector.get_map() or process.poll() is None:
                now = time.monotonic()
                if now - started >= timeout:
                    failure = 'timeout'
                    break
                if now >= next_sample:
                    observed = sum(rss for _, rss, _ in group_processes(process.pid))
                    peak_rss = max(peak_rss, observed)
                    if observed > memory:
                        failure = 'memory_limit'
                        break
                    next_sample = time.monotonic() + 0.1
                for key, _ in selector.select(0.025):
                    raw = os.read(key.fileobj.fileno(), 65536)
                    if not raw:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        continue
                    remaining = cap - len(key.data)
                    key.data.extend(raw[:remaining])
                    if len(raw) > remaining:
                        failure = 'output_limit'
                        break
                if failure:
                    break
            if failure is None and group_processes(process.pid):
                failure = 'unexpected_live_descendants'
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            failure, spawn_error = 'execution_error', str(error)
        finally:
            if process is not None:
                if failure:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                process.wait(timeout=10)
                for _ in range(20):
                    cleanup_remaining = group_processes(process.pid)
                    if not cleanup_remaining:
                        break
                    time.sleep(0.05)
                if cleanup_remaining:
                    failure = 'process_group_cleanup_failed'
            for key in list(selector.get_map().values()):
                key.fileobj.close()
            selector.close()
        (directory / 'stdout.log').write_bytes(stdout)
        (directory / 'stderr.log').write_bytes(stderr)
        record = {'command': command, 'cwd': str(cwd), 'label': label,
            'started_utc': timestamp, 'elapsed_seconds': time.monotonic() - started,
            'returncode': None if process is None else process.returncode,
            'failure': failure, 'execution_error': spawn_error,
            'limits': {'seconds': timeout, 'observed_group_rss_bytes': memory,
                       'rss_sample_interval_seconds': 0.1,
                       'rss_limit_is_hard_os_cap': False,
                       'stdout_bytes': cap, 'stderr_bytes': cap},
            'peak_observed_group_rss_bytes': peak_rss,
            'remaining_live_group_processes': cleanup_remaining,
            'stdout_sha256': digest(stdout), 'stderr_sha256': digest(stderr),
            'retained_stdout_bytes': len(stdout), 'retained_stderr_bytes': len(stderr)}
        self.commands.append(record)
        (directory / 'command.json').write_bytes(canonical(record))
        require(failure is None, label + ': operational failure: ' + str(failure))
        require(process is not None and process.returncode == 0, label + ': nonzero process status')
        require(not stderr, label + ': unexpected stderr')
        require(allow_stdout or not stdout, label + ': unexpected stdout')
        return bytes(stdout)


def verify_source_pins(root: Path, snapshot: Snapshot) -> None:
    for relative, expected in SOURCE_PINS.items():
        require(digest(snapshot.read(root / relative)) == expected, 'pinned source changed: ' + relative)


def prepare(root: Path, output: Path, snapshot: Snapshot) -> tuple[Runner, Path, Path, object]:
    require(root == root.resolve(strict=True), 'repository root must be canonical')
    verify_source_pins(root, snapshot)
    helper, base = load_helpers(root, snapshot)
    require(digest(snapshot.read(LANE / 'Contract.lean')) == CONTRACT_SHA256, 'adopted contract changed')
    base.check_toolchain()
    base.check_lakefile()
    base.check_manifest()
    lake, git = base.find_lake(), base.find_git()
    require(Path(base.run_git(git, root, ['rev-parse', '--show-toplevel'], 'root check').strip()) == root,
            'Git canonical root differs')
    version = base.check_version(lake)
    git_head = base.run_git(git, root, ['rev-parse', 'HEAD'], 'HEAD observation').strip()
    git_status = base.run_git(git, root, ['status', '--porcelain=v1', '--untracked-files=no'], 'status observation')
    base.check_dependency_checkouts(git)
    cleaned = {k: v for k, v in os.environ.items()
               if k in {'PATH', 'HOME', 'TMPDIR', 'USER', 'LOGNAME', 'SYSTEMROOT'}}
    prefix_result = subprocess.run([str(lake), 'env', 'lean', '--print-prefix'],
        cwd=root / PROJECT_RELATIVE, env=cleaned, capture_output=True, timeout=60, check=False)
    require(prefix_result.returncode == 0 and prefix_result.stderr == b'', 'Lean prefix probe failed')
    prefix = Path(prefix_result.stdout.decode().strip()).resolve(strict=True)
    lean, leanchecker = prefix / 'bin/lean', prefix / 'bin/leanchecker'
    tools = {str(path): digest(snapshot.read(path)) for path in (lean, leanchecker)}
    (output / 'prefix-stdout.log').write_bytes(prefix_result.stdout)
    (output / 'prefix-stderr.log').write_bytes(prefix_result.stderr)
    src, build = output / 'src', output / 'build'
    src.mkdir(); build.mkdir()
    for module in MODULES:
        copied = src / (module + '.lean')
        copied.write_bytes(snapshot.read(LANE / (module + '.lean')))
        snapshot.read(copied)
    for module in ('Deterministic', 'SxEventBridge'):
        target = src / 'PidFiniteConvergence' / (module + '.lean')
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(snapshot.read(root / PROJECT_RELATIVE / 'PidFiniteConvergence' / (module + '.lean')))
        snapshot.read(target)
    packages = [root / PROJECT_RELATIVE / '.lake/packages' / name / '.lake/build/lib/lean'
                for name in base.EXPECTED_PACKAGE_PINS]
    # Lake includes paths for packages that this import closure does not compile.
    # Keep those pinned locations; an unavailable required module fails in Lean.
    cleaned['PATH'] = str(prefix / 'bin') + os.pathsep + '/usr/bin:/bin'
    cleaned.update({'LEAN_PATH': os.pathsep.join(map(str, [build, *packages, prefix / 'lib/lean'])),
                    'LEAN_SRC_PATH': str(src), 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'})
    runner = Runner(output, cleaned)
    (output / 'environment.json').write_bytes(canonical({'lean_identity': helper.portable_identity(base, version),
        'tool_sha256': tools, 'package_pins': base.EXPECTED_PACKAGE_PINS,
        'repository_root': str(root), 'observed_head': git_head, 'observed_tracked_status': git_status,
        'lean_search_path': cleaned['LEAN_PATH'], 'lean_source_path': cleaned['LEAN_SRC_PATH'],
        'dependency_cache_directories': {str(path): path.is_dir() for path in packages},
        'custody_helper_sha256': {INFORMATIVE_HELPER: INFORMATIVE_SHA256, BASE_HELPER: BASE_SHA256},
        'scope': 'Pinned helper preflight; local source-to-olean authenticity is not claimed.'}))
    for module in ('PidFiniteConvergence/Deterministic', 'PidFiniteConvergence/SxEventBridge',
                   'Contract', 'JudgeCore', 'JudgeTargets', 'JudgeAliases', 'ContractJudge'):
        destination = build / (module + '.olean')
        destination.parent.mkdir(exist_ok=True)
        runner.run([str(lean), '-t', '0', '-M', '4096', '-o', str(destination), str(src / (module + '.lean'))],
                   src, 'compile-' + module.replace('/', '-'))
    snapshot.verify()
    return runner, lean, leanchecker, base


def check_freeze(snapshot: Snapshot, expected: str) -> dict[str, object]:
    require(HEX.fullmatch(expected) is not None, 'freeze digest must be SHA-256')
    raw = snapshot.read(LANE / 'frozen.json')
    require(digest(raw) == expected, 'adopted judge freeze digest changed')
    record = strict_json(raw)
    require(type(record) is dict and record.get('status') == 'frozen_before_candidate',
            'judge freeze is not accepted for a candidate')
    files = record.get('files')
    require(type(files) is dict and all(type(k) is str and '/' not in k and k not in {'.', '..'}
                                      for k in files), 'invalid frozen file roster')
    required = {name + '.lean' for name in MODULES} | {'judge.py', 'selftest.py', 'theorem-roster.json'}
    require(required <= files.keys(), 'frozen judge file roster is incomplete')
    for name, expected_sha in files.items():
        require(type(expected_sha) is str and HEX.fullmatch(expected_sha) is not None
                and digest(snapshot.read(LANE / name)) == expected_sha, 'frozen judge input changed: ' + name)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--candidate-sha256', required=True)
    parser.add_argument('--freeze-sha256', required=True)
    args = parser.parse_args()
    output = args.output.absolute()
    require(output.is_relative_to(LANE / 'runs') and output == output.resolve(),
            'attempt output must be inside the owned lane runs directory')
    output.mkdir(parents=True, exist_ok=False)
    snapshot = Snapshot()
    receipt: dict[str, object] = {'status': 'not_accepted', 'candidate_exists': True,
        'scope': 'Local semantic/kernel evidence only; no external custody, priority, estimator or consumer claim.'}
    runner = None
    try:
        receipt['freeze'] = check_freeze(snapshot, args.freeze_sha256)
        candidate_raw = snapshot.read(args.candidate)
        require(HEX.fullmatch(args.candidate_sha256) is not None
                and digest(candidate_raw) == args.candidate_sha256, 'candidate attempt digest mismatch')
        (output / 'captured-Candidate.lean').write_bytes(candidate_raw)
        runner, lean, leanchecker, base = prepare(args.root.absolute(), output, snapshot)
        candidate_policy(candidate_raw, base, args.candidate)
        src, build = output / 'src', output / 'build'
        (src / 'Candidate.lean').write_bytes(candidate_raw)
        snapshot.read(src / 'Candidate.lean')
        snapshot.verify()
        runner.run([str(lean), '-t', '0', '-M', '4096', '-o', str(build / 'Candidate.olean'), str(src / 'Candidate.lean')],
                   src, 'compile-candidate')
        semantic = runner.run([str(lean), '-t', '0', '-M', '4096', '-o', str(build / 'SemanticJudge.olean'),
                               str(src / 'SemanticJudge.lean')], src, 'semantic-judge', allow_stdout=True)
        receipt['theorems'] = strict_axiom_output(semantic)
        runner.run([str(leanchecker), '--fresh', 'SemanticJudge'], src, 'kernel-semantic-closure')
        snapshot.verify()
        receipt['status'] = 'local_semantic_kernel_pass'
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        receipt['failure'] = str(error)
    finally:
        snapshot.save(output)
        receipt['inputs'] = snapshot.manifest()
        receipt['commands'] = [strict_json(path.read_bytes())
                               for path in sorted(output.glob('[0-9][0-9]-*/command.json'))]
        receipt['artifacts'] = {str(path.relative_to(output)): digest(path.read_bytes())
                                for path in sorted(output.rglob('*')) if path.is_file()
                                and path.name != 'receipt.json'}
        (output / 'receipt.json').write_bytes(canonical(receipt))
    print(json.dumps({'status': receipt['status'], 'receipt': str(output / 'receipt.json')}, sort_keys=True))
    return 0 if receipt['status'] == 'local_semantic_kernel_pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
