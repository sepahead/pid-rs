"""Check the exact 64-cell example against the generic and specialized product rules."""

from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from itertools import product
from pathlib import Path
import argparse
import json
import runpy


def require(condition, label):
    if not condition:
        raise ValueError(label)


def noisy_bit_rows():
    words = [''.join(bits) for bits in product('01', repeat=3)]
    rows = []
    for finest, target in product(words, repeat=2):
        equal = sum(a == b for a, b in zip(finest, target))
        rows.append({
            'source_states': [[finest[:j]] for j in (1, 2, 3)],
            'target_state': [target],
            'count': str(2 ** equal),
        })
    return rows


def general_products(module, rows):
    table, total, lengths = module['typed_rows'](rows)
    module['reserve'](table, total, lengths)
    plans = list(module['projections'](module['base_plans'](table, total)))
    module['preflight'](plans)
    return {'/'.join((stage, component, key)): module['exact_product'](plan)
            for (stage, component, key, _), plan in plans}


def check_expected(values):
    require(len(values) == 108, 'key count')
    active = {'01+02+04', '02+04', '04'}
    factors = {'informative': Fraction(2**216), 'misinformative': Fraction(3**216, 2**144),
               'net': Fraction(2**360, 3**216)}
    nonunit = 0
    for label, value in values.items():
        stage, component, key = label.split('/')
        if stage == 'atom':
            expected = factors[component] if key in active else Fraction(1)
            require(value == expected, 'attaining keyed atom')
            nonunit += value != 1
    require(nonunit == 9, 'all nine components simultaneously positive')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('oracle', type=Path)
    parser.add_argument('specialized', type=Path)
    args = parser.parse_args()
    require(sha256(args.oracle.read_bytes()).hexdigest() == 'b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2', 'generic source')
    require(sha256(args.specialized.read_bytes()).hexdigest() == 'd507538e5931ce03f5a4c7ea774c0cca70ad0964f5673b9b0ab38d9444453203', 'special source')
    module = runpy.run_path(str(args.oracle))
    special = runpy.run_path(str(args.specialized))['calculate']
    rows = noisy_bit_rows()
    require(len(rows) == 64 and sum(int(row['count']) for row in rows) == 216, 'input size')
    values = general_products(module, rows)
    output = special(rows)['records']
    require(values == {k: Fraction(*v) for k, v in output.items()}, 'general-versus-special calculation')
    check_expected(values)
    changed = deepcopy(rows)
    changed[0]['count'] = str(int(changed[0]['count']) + 1)
    wrong_count = general_products(module, changed)
    wrong_key = values.copy()
    left, right = 'atom/net/04', 'atom/net/01'
    wrong_key[left], wrong_key[right] = wrong_key[right], wrong_key[left]
    controls = []
    for name, data in [('changed-cell-count', wrong_count), ('exchanged-atom-keys', wrong_key)]:
        try:
            check_expected(data)
        except ValueError as error:
            controls.append([name, str(error)])
        else:
            raise ValueError(name + ' was accepted')
    print(json.dumps({'occupied_cells': 64, 'total': 216, 'general_products': len(values),
                      'nonunit_atoms': 9, 'controls': controls}, sort_keys=True))


if __name__ == '__main__':
    main()
