"""Reproduce the observed rational products from a public checkout of pid-rs."""

from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile


STUDY = Path(__file__).resolve().parent
ROOT = STUDY.parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(script, *arguments, success=True):
    flags = ['-I', '-S', '-B'] + (['-O'] if sys.flags.optimize else [])
    result = subprocess.run([sys.executable, *flags, script, *arguments], capture_output=True,
                            timeout=60, cwd=STUDY)
    if success:
        if result.returncode or result.stderr:
            raise RuntimeError(str(script.name) + ': ' + result.stderr.decode(errors='replace')[-1200:])
    else:
        require(result.returncode != 0, 'original directional predicate was incorrectly accepted')
        require(b'ValueError: hostile discriminators' in result.stderr, 'historical rejection reason')
    return result.stdout


def confirm_file(actual, expected):
    require(actual.read_bytes() == expected.read_bytes(), 'record differs: ' + expected.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-root', type=Path, default=ROOT, help='public checkout with the original six-case arithmetic source')
    parser.add_argument('--self-test', action='store_true', help='repeat the retained rejection and the all-nine-positive example')
    args = parser.parse_args()
    oracle = args.assets_root.resolve() / 'audit/research/three-source-six-certificate-observations/arithmetic.py'
    source = STUDY / 'reference/structured.py'
    tables = STUDY / 'reference/criterion.py'
    other = STUDY / 'independent'
    third = STUDY / 'third-calculation'
    with tempfile.TemporaryDirectory(prefix='categorical-nested-products-') as directory:
        temp = Path(directory)
        run(STUDY / 'checks/restore_sources.py', other, temp / 'original')
        other = temp / 'original'
        run(STUDY / 'checks/complete.py', source, oracle, temp / 'complete')
        confirm_file(temp / 'complete/result.json', STUDY / 'records/complete.json')
        run(STUDY / 'checks/margin.py', tables, temp / 'margin.json')
        confirm_file(temp / 'margin.json', STUDY / 'records/margin.json')
        run(other / 'judge.py', other / 'candidate/nested.py', temp / 'elements')
        for name in ('all-products.json', 'RESULT.json'):
            confirm_file(temp / 'elements' / name, other / 'ordinary' / name)
        enumerated = run(other / 'split-gap/enumerate_partitions.py')
        require(enumerated == (other / 'split-gap/ordinary.json').read_bytes(), 'partition enumeration')
        binary = STUDY / 'finite-alphabets'
        require(run(binary / 'enumerate.py') == (binary / 'exhaustive.json').read_bytes(), 'one- and two-label partition census')
        two = binary / 'set-and-cell'
        run(two / 'judge/check.py', two / 'candidate/from_cells.py', temp / 'binary')
        confirm_file(temp / 'binary/RESULT.json', two / 'RESULT.json')
        verify = binary / 'reader'
        require(run(verify / 'binary_fine.py') == (verify / 'BINARY-FINITE-ACTUAL.json').read_bytes(), 'binary reader tables')
        require(run(verify / 'exact_fine_states.py') == (verify / 'EXACT-FINE-CLASSIFICATION.json').read_bytes(), 'all occupied fine-label counts')
        third_record = run(third / 'nested_first.py')
        require(third_record == (third / 'FINITE-ACTUAL.json').read_bytes(), 'third finite calculation')
        result = {'named_products_on_49': 5292, 'named_products_on_13': 1404, 'integer_tables': 12009,
                  'ordered_partitions': 44168, 'third_integer_tables': 12989, 'binary_partitions_through_8': 593521,
                  'binary_partitions_through_7': 63601, 'binary_count_arrays': 55182,
                  'all_fine_counts_partition_pairs': 44168, 'all_fine_counts_constructed_witnesses': 4950}
        if args.self_test:
            rejected = temp / 'should-not-exist.json'
            run(STUDY / 'checks/first-margin.py', tables, rejected, success=False)
            require(not rejected.exists(), 'historical judge produced an accepted record')
            sharp = run(STUDY / 'checks/attaining.py', oracle, source)
            require(sharp == (STUDY / 'records/attaining.json').read_bytes(), 'attaining example record')
            result['all_nine_positive'] = 9
            result['retained_failed_predicate'] = 'hostile discriminators'
        print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
