#!/usr/bin/env python3
"""Restore all thirteen old reporting calls after a bound complete positive run."""
from pathlib import Path
from types import ModuleType
import argparse
import os
import sys

LANE = Path(__file__).resolve().parent
j = ModuleType('reviewed_local_judge')
j.__file__ = str(LANE / 'judge.py')
exec(compile((LANE / 'judge.py').read_bytes(), j.__file__, 'exec', dont_inherit=True,
             optimize=sys.flags.optimize), j.__dict__)
OLD_SEMANTIC_SHA256 = '0c1cf11598048c39e8fee92384362e15e2c9e3555dd93f4befa4c15f865889ab'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accepted_run', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--accepted-receipt-sha256', required=True)
    parser.add_argument('--freeze-sha256', required=True)
    args = parser.parse_args()
    output = args.output.absolute()
    accepted = args.accepted_run.absolute()
    j.require(output.is_relative_to(LANE / 'runs') and output == output.resolve(),
              'regression output must be inside owned lane runs')
    j.require(accepted == accepted.resolve(strict=True), 'accepted run is not canonical')
    output.mkdir(parents=True, exist_ok=False)
    snapshot = j.Snapshot()
    report = {'status': 'not_accepted', 'scope':
        'Causal reporting regression using the exact compiled imports of a bound complete '
        'candidate pass. This direct compilation is not another full wrapper run.'}
    runner = None
    try:
        freeze = j.check_freeze(snapshot, args.freeze_sha256)
        raw_receipt = snapshot.read(accepted / 'receipt.json')
        j.require(j.digest(raw_receipt) == args.accepted_receipt_sha256,
                  'accepted receipt digest changed')
        prior = j.strict_json(raw_receipt)
        j.require(prior['status'] == 'local_semantic_kernel_pass' and prior['freeze'] == freeze,
                  'complete positive result is absent or belongs to another judge')
        commands = prior['commands']
        j.require(commands[-1]['label'] == 'kernel-semantic-closure'
                  and commands[-1]['returncode'] == 0
                  and commands[-1]['command'][1:] == ['--fresh', 'SemanticJudge'],
                  'positive fresh kernel replay is absent')

        def captured(relative):
            raw = snapshot.read(accepted / relative)
            j.require(j.digest(raw) == prior['artifacts'][relative],
                      'accepted artifact changed: ' + relative)
            return raw

        captured('src/Candidate.lean')
        candidate = captured('captured-Candidate.lean')
        j.require(j.digest(candidate) == j.AMENDMENT_CANDIDATE_SHA256
                  and candidate == captured('src/Candidate.lean'),
                  'regression must use the unchanged candidate at amendment')
        correct = snapshot.read(LANE / 'SemanticJudge.lean')
        j.require(captured('src/SemanticJudge.lean') == correct, 'positive reporting source differs')
        positive = j.strict_axiom_output(captured('08-semantic-judge/stdout.log'))
        j.require(positive == prior['theorems'], 'positive theorem records differ from receipt')
        for relative in sorted(prior['artifacts']):
            if relative.startswith('build/') and relative.endswith('.olean'):
                captured(relative)
        environment_record = j.strict_json(captured('environment.json'))
        lean = Path(commands[-2]['command'][0])
        j.require(j.digest(snapshot.read(lean)) == environment_record['tool_sha256'][str(lean)],
                  'positive compiler identity changed')
        environment = {k: v for k, v in os.environ.items()
                       if k in {'HOME', 'TMPDIR', 'USER', 'LOGNAME', 'SYSTEMROOT'}}
        environment.update({'PATH': str(lean.parent) + os.pathsep + '/usr/bin:/bin',
            'LEAN_PATH': environment_record['lean_search_path'],
            'LEAN_SRC_PATH': str(output / 'src'), 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'})
        j.require(environment['LEAN_PATH'].split(os.pathsep)[0] == str(accepted / 'build'),
                  'positive owned build is not first in the search path')
        new_line = b'  IO.println ("DNF_JUDGE_RESULT " ++ result.compress)'
        old_line = b'  liftIO <| IO.println ("DNF_JUDGE_RESULT " ++ result.compress)'
        j.require(correct.count(new_line) == 13, 'reporting site roster changed')
        restored = correct.replace(new_line, old_line)
        j.require(j.digest(restored) == OLD_SEMANTIC_SHA256,
                  'restoration is not byte-identical to the failed original semantic judge')
        src = output / 'src'; src.mkdir()
        source = src / 'SemanticJudge.lean'; source.write_bytes(restored); snapshot.read(source)
        runner = j.Runner(output, environment)
        try:
            runner.run([str(lean), '-t', '0', '-M', '4096', '-o',
                        str(output / 'RestoredReportingDefect.olean'), str(source)],
                       src, 'restored-thirteen-reporting-sites', allow_stdout=True)
        except j.JudgeError as error:
            j.require('nonzero process status' in str(error), 'wrong operational rejection cause')
        else:
            raise j.JudgeError('original reporting defect was accepted')
        stdout = (output / '00-restored-thirteen-reporting-sites/stdout.log').read_bytes()
        stderr = (output / '00-restored-thirteen-reporting-sites/stderr.log').read_bytes()
        j.require(stdout.count(b'Type mismatch') == 13
                  and stdout.count(b'CommandElabM Unit') == 13
                  and stdout.count(b'TermElabM Unit') == 12
                  and len(j.re.findall(rb'TermElabM \?m\.[0-9]+', stdout)) == 1 and not stderr
                  and not any(line.startswith(b'DNF_JUDGE_RESULT ') for line in stdout.splitlines()),
                  'restored reporting defect did not reproduce all thirteen original causes')
        j.require(runner.commands[-1]['remaining_live_group_processes'] == [],
                  'restored reporting control cleanup incomplete')
        snapshot.verify()
        report.update({'status': 'reporting_regression_pass',
            'accepted_receipt_sha256': args.accepted_receipt_sha256,
            'candidate_sha256': j.digest(candidate), 'freeze_sha256': args.freeze_sha256,
            'complete_positive_records': len(positive),
            'restored_semantic_source_sha256': j.digest(restored),
            'restored_monad_mismatches': 13,
            'expected_concrete_term_unit_mismatches': 12,
            'expected_final_term_result_metavariable_mismatches': 1})
    except (OSError, RuntimeError, ValueError, KeyError, j.subprocess.SubprocessError) as error:
        report['failure'] = str(error)
    finally:
        snapshot.save(output)
        report['inputs'] = snapshot.manifest()
        report['commands'] = [j.strict_json(path.read_bytes())
                              for path in sorted(output.glob('[0-9][0-9]-*/command.json'))]
        report['artifacts'] = {str(path.relative_to(output)): j.digest(path.read_bytes())
            for path in sorted(output.rglob('*')) if path.is_file() and path.name != 'regression-receipt.json'}
        (output / 'regression-receipt.json').write_bytes(j.canonical(report))
    print(j.json.dumps({'status': report['status'], 'receipt': str(output / 'regression-receipt.json')},
                       sort_keys=True))
    return 0 if report['status'] == 'reporting_regression_pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
