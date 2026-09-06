#!/usr/bin/env python3
"""Pre-candidate judge controls. This command does not supply a candidate proof."""
from pathlib import Path
from types import ModuleType
import argparse
import json
import os
import sys

LANE = Path(__file__).resolve().parent
module_path = LANE / 'judge.py'
j = ModuleType('reviewed_local_judge')
j.__file__ = str(module_path)
exec(compile(module_path.read_bytes(), str(module_path), 'exec', dont_inherit=True,
             optimize=sys.flags.optimize), j.__dict__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    output = args.output.absolute()
    j.require(output.is_relative_to(LANE / 'runs') and output == output.resolve(), 'output outside lane')
    output.mkdir(parents=True, exist_ok=False)
    results = []
    snapshots = j.Snapshot()
    for path in sorted(LANE.glob('*.lean')):
        snapshots.read(path)
    snapshots.read(module_path)
    snapshots.read(Path(__file__))
    runner = None
    report = {'status': 'not_accepted', 'scope': 'Pre-candidate controls only. No thirteen-export candidate exists.',
              'python_optimized': sys.flags.optimize, 'results': results}

    def passed(name, category, details=''):
        results.append({'name': name, 'category': category, 'status': 'pass', 'details': details})

    def rejection(name, category, function, expected):
        try:
            function()
        except (RuntimeError, OSError, ValueError, UnicodeError) as error:
            j.require(expected in str(error), name + ': wrong rejection cause: ' + str(error))
            passed(name, category, str(error))
            return
        raise j.JudgeError(name + ': control was accepted')

    try:
        ambient_path = os.environ.get('LEAN_PATH')
        poison = str(output / 'untrusted-stale-candidate-cache')
        os.environ['LEAN_PATH'] = poison
        try:
            runner, lean, checker, base = j.prepare(args.root.absolute(), output, snapshots)
        finally:
            if ambient_path is None:
                os.environ.pop('LEAN_PATH', None)
            else:
                os.environ['LEAN_PATH'] = ambient_path
        j.require(poison not in runner.environment['LEAN_PATH'], 'ambient Lean cache entered search path')
        j.require(runner.environment['LEAN_PATH'].split(os.pathsep)[0] == str(output / 'build'), 'owned olean directory is not first')
        passed('ambient_stale_cache_excluded', 'custody')
        passed('contract_raw_alias_preparation', 'positive')
        src, build = output / 'src', output / 'build'

        def compile_module(name, raw, expected_marker=None):
            source = src / (name + '.lean')
            source.write_bytes(raw)
            snapshots.read(source)
            command = [str(lean), '-t', '0', '-M', '4096', '-o', str(build / (name + '.olean')), str(source)]
            if expected_marker is None:
                runner.run(command, src, name)
            else:
                rejection(name, 'semantic_rejection', lambda: runner.run(command, src, name), 'nonzero process status')
                directory = output / f'{len(runner.commands)-1:02d}-{name}'
                stdout = (directory / 'stdout.log').read_bytes()
                stderr = (directory / 'stderr.log').read_bytes()
                j.require(expected_marker.encode() in stdout and not stderr,
                          name + ': expected semantic rejection marker missing')
                results[-1]['details'] = expected_marker

        for name in ('FiniteControls', 'WrongTargets'):
            compile_module(name, (LANE / (name + '.lean')).read_bytes())
            passed(name, 'finite_counterexamples' if name == 'FiniteControls' else 'valid_wrong_target_proofs')

        positive = '''import WrongTargets
import JudgeCore
open Lean Elab Command
namespace PidSxDnfOrderJudgeControlTypes
open PidSxDnfOrderContract
universe u
def RawFin3 : Prop := ∀ alpha beta : Finset (Finset (Fin 3)),
  RedundancyLE alpha beta ↔ ∀ e : Fin 3 → Bool, DNF beta e → DNF alpha e
def AliasFin3 : Prop := order_iff_dnf_target (Fin 3)
def RawRefl : Prop := ∀ (S : Type u) (x : S), x = x
def AliasRefl : Prop := ∀ (A : Type u) (a : A), a = a
theorem reflProof (A : Type u) (a : A) : a = a := rfl
run_cmd liftTermElabM do
  let _ ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderWrongTargets.fin3_only ``RawFin3 ``AliasFin3
  let _ ← PidSxDnfOrderJudge.checkExport ``reflProof ``RawRefl ``AliasRefl
  pure ()
end PidSxDnfOrderJudgeControlTypes
'''
        compile_module('PositiveTypeControls', positive.encode())
        passed('finite_and_universe_positive_types', 'positive')
        for name in ('fin3_only', 'explicit_receiver', 'implicit_receiver', 'assumed_conclusion', 'renamed_premise'):
            raw = '''import WrongTargets
import JudgeCore
import JudgeTargets
import JudgeAliases
open Lean Elab Command
run_cmd liftTermElabM do
  let _ ← PidSxDnfOrderJudge.checkExport ``PidSxDnfOrderWrongTargets.%s
    ``PidSxDnfOrderJudgeTargets.order_iff_dnf ``PidSxDnfOrderJudgeAliases.order_iff_dnf
  pure ()
''' % name
            compile_module('Reject_' + name, raw.encode(), 'DNF_JUDGE_TARGET_TYPE')
        for name, declaration, marker in (
            ('RejectAxiom', 'axiom injected : True\ntheorem test : True := injected', 'DNF_JUDGE_AXIOM'),
            ('RejectDefinition', 'def test : True := True.intro', 'DNF_JUDGE_DECLARATION_KIND')):
            raw = ('import JudgeCore\nopen Lean Elab Command\n'
                   'namespace JudgeControl\ndef Raw : Prop := True\ndef Alias : Prop := True\n' + declaration +
                   '\nrun_cmd liftTermElabM do\n  let _ ← PidSxDnfOrderJudge.checkExport ``test ``Raw ``Alias\n  pure ()\nend JudgeControl\n')
            compile_module(name, raw.encode(), marker)
        compile_module('RejectMissingRoster', b'''import JudgeCore
open Lean Elab Command
run_cmd liftTermElabM do
  PidSxDnfOrderJudge.checkPublicRoster [ `PidSxDnfOrderCandidate.order_iff_dnf ]
''', 'DNF_JUDGE_EXPORT_ROSTER')
        compile_module('RejectExtraRoster', b'''import JudgeCore
open Lean Elab Command
namespace PidSxDnfOrderCandidate
def extra : Nat := 0
end PidSxDnfOrderCandidate
run_cmd liftTermElabM do
  PidSxDnfOrderJudge.checkPublicRoster []
''', 'DNF_JUDGE_EXPORT_ROSTER')

        fixture = ('import Contract\nset_option autoImplicit false\nset_option warningAsError true\n'
                   'namespace PidSxDnfOrderCandidate\n' + ''.join(
                   'theorem '+name+' : True := True.intro\n' for name in j.THEOREMS) +
                   'end PidSxDnfOrderCandidate\n').encode()
        # Syntax-only source fixture: never compiled and never offered as a proof candidate.
        (output / 'policy-syntax-fixture.txt').write_bytes(fixture)
        j.candidate_policy(fixture, base, output / 'policy-syntax-fixture.txt')
        cosmetic = b'/- Cosmetic syntax-only control. -/\n' + fixture
        j.candidate_policy(cosmetic, base, output / 'policy-syntax-fixture.txt')
        j.require(j.digest(fixture) != j.digest(cosmetic), 'cosmetic fixture digest did not change')
        passed('P12_cosmetic_source_fragment', 'source_policy', 'Source syntax only; candidate semantic replay remains pending.')
        mutations = {
            'extra_import': fixture.replace(b'import Contract', b'import Contract\nimport Lean'),
            'unknown_public': fixture.replace(b'end PidSxDnfOrderCandidate', b'theorem unknown : True := True.intro\nend PidSxDnfOrderCandidate'),
            'missing_export': fixture.replace(b'theorem order_iff_dnf : True := True.intro\n', b''),
            'duplicate_export': fixture.replace(b'theorem order_iff_dnf', b'theorem antichain_antisymm'),
            'changed_option': fixture.replace(b'autoImplicit false', b'autoImplicit true'),
        }
        for token in ('sorry', 'axiom', 'native_decide', 'unsafe', 'run_cmd', 'run_tac', 'elab',
                      'macro', 'initialize', 'attribute', 'set_option maxRecDepth 0', 'import Lean'):
            mutations['forbidden_' + token.replace(' ', '_')] = fixture + ('\n' + token + '\n').encode()
        for name, raw in mutations.items():
            rejection(name, 'source_policy', lambda raw=raw: j.candidate_policy(raw, base, output/'policy.txt'), '')

        valid_records = []
        for name in j.THEOREMS:
            valid_records.append({'theorem':'PidSxDnfOrderCandidate.'+name,
                'raw_target':'PidSxDnfOrderJudgeTargets.'+name,
                'alias_target':'PidSxDnfOrderJudgeAliases.'+name, 'universes':[],
                'full_elaborated_type':'synthetic parser control only', 'axioms':[], 'status':'accepted'})
        def encoded(records):
            return b''.join(b'DNF_JUDGE_RESULT '+json.dumps(record,sort_keys=True).encode()+b'\n' for record in records)
        payload = encoded(valid_records)
        j.strict_axiom_output(payload)
        passed('exact_parser_shape', 'parser_control', 'Synthetic parser records are not theorem evidence.')
        bad = {
            'missing_record':encoded(valid_records[:-1]),
            'duplicate_record':encoded([valid_records[0], *valid_records[:-1]]),
            'unknown_axiom':encoded([{**valid_records[0], 'axioms':['sorryAx']}, *valid_records[1:]]),
            'malformed':payload[:-3], 'extra_output':payload+b'noise\n',
            'wrong_field_type':encoded([{**valid_records[0], 'axioms':True}, *valid_records[1:]]),
            'unknown_field':encoded([{**valid_records[0], 'extra':1}, *valid_records[1:]]),
            'duplicate_json_key':payload.replace(b'"status": "accepted"', b'"status": "accepted", "status": "accepted"', 1),
        }
        for name, raw in bad.items():
            rejection(name, 'parser_control', lambda raw=raw:j.strict_axiom_output(raw), '')

        custody = output / 'custody'; custody.mkdir()
        regular = custody / 'regular'; regular.write_bytes(b'input')
        snap = j.Snapshot(); snap.read(regular); snap.verify(); passed('regular_capture', 'custody')
        rejection('missing_file', 'custody', lambda:j.Snapshot().read(custody/'missing'), '')
        link = custody/'symlink'; link.symlink_to(regular)
        rejection('symlink_file', 'custody', lambda:j.Snapshot().read(link), 'noncanonical or symlink')
        hard = custody/'hardlink'; os.link(regular,hard)
        rejection('hardlinked_file', 'custody', lambda:j.Snapshot().read(hard), 'single-link')
        hard.unlink()
        after = j.Snapshot(); after.read(regular); regular.write_bytes(b'other')
        rejection('changed_after_capture', 'custody', after.verify, 'changed after capture')
        regular.write_bytes(b'input'); swapped=j.Snapshot(); swapped.read(regular)
        replacement=custody/'replacement';replacement.write_bytes(b'input');replacement.replace(regular)
        rejection('same_bytes_inode_replacement', 'custody', swapped.verify, 'changed after capture')
        during = custody/'during';during.write_bytes(b'input')
        original_open = j.os.open
        def replacing_open(path, flags):
            descriptor=original_open(path,flags)
            replacement=custody/'during-replacement';replacement.write_bytes(b'input');replacement.replace(during)
            return descriptor
        j.os.open=replacing_open
        try:
            rejection('inode_replaced_at_open', 'custody', lambda:j.Snapshot().read(during), 'changed before capture')
        finally:
            j.os.open=original_open
        original_fdopen = j.os.fdopen
        def changing_fdopen(descriptor, *args, **kwargs):
            during.write_bytes(b'other')
            return original_fdopen(descriptor, *args, **kwargs)
        j.os.fdopen=changing_fdopen
        try:
            rejection('bytes_changed_during_capture', 'custody', lambda:j.Snapshot().read(during), 'changed during capture')
        finally:
            j.os.fdopen=original_fdopen

        pinroot=custody/'pinroot'
        for relative in j.SOURCE_PINS:
            destination=pinroot/relative;destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes((args.root/relative).read_bytes())
        j.verify_source_pins(pinroot,j.Snapshot());passed('exact_source_pins','custody')
        for index,relative in enumerate(j.SOURCE_PINS):
            destination=pinroot/relative;raw=destination.read_bytes();destination.write_bytes(raw+b'\n')
            rejection('pin_'+str(index),'custody',lambda:j.verify_source_pins(pinroot,j.Snapshot()),'pinned source changed: '+relative)
            destination.write_bytes(raw)

        freeze_files={name+'.lean':j.digest((LANE/(name+'.lean')).read_bytes()) for name in j.MODULES}
        freeze_files.update({name:j.digest((LANE/name).read_bytes()) for name in ('judge.py','selftest.py','theorem-roster.json')})
        frozenir=custody/'freeze';frozenir.mkdir()
        for name in freeze_files:(frozenir/name).write_bytes((LANE/name).read_bytes())
        frozen={'status':'frozen_before_candidate','files':freeze_files}
        frozenraw=j.canonical(frozen);(frozenir/'frozen.json').write_bytes(frozenraw)
        oldlane=j.LANE;j.LANE=frozenir
        try:
            j.check_freeze(j.Snapshot(),j.digest(frozenraw));passed('exact_frozen_roster','custody')
            contract=frozenir/'Contract.lean';contract.write_bytes(contract.read_bytes()+b'\n')
            rejection('changed_contract','custody',lambda:j.check_freeze(j.Snapshot(),j.digest(frozenraw)),'frozen judge input changed')
            frozen['files']['Contract.lean']=j.digest(contract.read_bytes())
            (frozenir/'frozen.json').write_bytes(j.canonical(frozen))
            rejection('coordinated_contract_reseal','custody',lambda:j.check_freeze(j.Snapshot(),j.digest(frozenraw)),'adopted judge freeze digest changed')
        finally:j.LANE=oldlane

        python=str(Path(sys.executable).resolve())
        def process_control(name, code, cause, **limits):
            command=[python,'-I','-S','-B','-c',code]
            rejection(name,'process_control',lambda:runner.run(command,src,name,**limits),cause)
            j.require(runner.commands[-1]['remaining_live_group_processes']==[],name+': cleanup incomplete')
        runner.run([python,'-I','-S','-B','-c','pass'],src,'silent_success')
        passed('silent_success','process_control')
        process_control('nonzero_empty','raise SystemExit(3)','nonzero process status')
        process_control('stdout_spoof',"print('DNF_JUDGE_RESULT fake')",'unexpected stdout')
        process_control('stderr_on_success',"import sys;sys.stderr.write('bad')",'unexpected stderr')
        process_control('truncated_exit',"import sys;sys.stdout.write('DNF_');sys.exit(2)",'nonzero process status')
        process_control('output_limit',"import sys;sys.stdout.write('x'*1000000)",'output_limit',cap=4096)
        process_control('timeout_descendant',"import subprocess,time,sys;subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);time.sleep(30)",'timeout',timeout=0.5)
        process_control('memory_limit',"import time;x=bytearray(32*1024*1024);time.sleep(30)",'memory_limit',memory=16*1024*1024,timeout=10)
        compile_module('ControlClosure', b'import ContractJudge\nimport FiniteControls\nimport WrongTargets\nimport PositiveTypeControls\n')
        runner.run([str(checker), '--fresh', 'ControlClosure'], src, 'kernel-all-positive-controls')
        passed('fresh_positive_control_closure', 'kernel')
        snapshots.verify()
        report['status']='pre_candidate_controls_pass'
        report['pending']=['Full thirteen-export candidate positive and cosmetic semantic replay; no candidate existed at freeze.',
            'No claim of external custody or process isolation from a malicious shared-workspace actor.',
            'Pinned dependency source preflight is reused; its complete historical mutation suite is not repeated here.']
    except (OSError, RuntimeError, ValueError, j.subprocess.SubprocessError) as error:
        report['failure']=str(error)
    finally:
        snapshots.save(output)
        report['inputs']=snapshots.manifest()
        report['commands']=[j.strict_json(path.read_bytes()) for path in sorted(output.glob('[0-9][0-9]-*/command.json'))]
        report['artifacts']={str(path.relative_to(output)):j.digest(path.read_bytes()) for path in sorted(output.rglob('*'))
                            if path.is_file() and not path.is_symlink() and path.name!='selftest-receipt.json'}
        (output/'selftest-receipt.json').write_bytes(j.canonical(report))
    print(json.dumps({'status':report['status'],'passed_controls':len(results),'output':str(output)},sort_keys=True))
    return 0 if report['status']=='pre_candidate_controls_pass' else 1

if __name__=='__main__':raise SystemExit(main())
