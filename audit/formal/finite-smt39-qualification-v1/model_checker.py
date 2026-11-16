#!/usr/bin/env python3
"""Finite, exposed SMT39 assignment checks; not UNSAT certificate verification.

No import of the encoder or its tables. Model helper bodies are bounded opaque
renderings: only the 25 declared assignments and 12 get-values are interpreted.
This module has no solver, subprocess, network, or file-writing capability.
"""
import functools
import hashlib
import itertools
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

ROSTER = (
    ('W01-carrier-complete', 'unsat'), ('W02-exactly-18-distinct', 'unsat'),
    ('W03-reflexivity', 'unsat'), ('W04-antisymmetry', 'unsat'),
    ('W05-transitivity', 'unsat'), ('W06-zeta-all-324', 'unsat'),
    ('W07-MZ-all-324', 'unsat'), ('W08-ZM-all-324', 'unsat'),
    ('W09-branch-event-equivalence', 'unsat'), ('W10-raw-source-equivalence', 'unsat'),
    ('W11-raw-target-restriction', 'unsat'), ('W12-order-event-inclusion', 'unsat'),
    ('W13-key-membership', 'unsat'), ('W14-supported-mass-bounds', 'unsat'),
    ('W15-full-joint-event', 'unsat'), ('W16-singleton-event', 'unsat'),
    ('W17-permutation-012', 'unsat'), ('W18-permutation-021', 'unsat'),
    ('W19-permutation-102', 'unsat'), ('W20-permutation-120', 'unsat'),
    ('W21-permutation-201', 'unsat'), ('W22-permutation-210', 'unsat'),
    ('C01-premise-nonvacuity', 'sat'), ('M01-reverse-order', 'sat'),
    ('M02-transpose-zeta', 'sat'), ('M03-omit-antichain', 'sat'),
    ('M04-padded-zero-branch', 'sat'), ('M05-AND-across-branches', 'sat'),
    ('M06-OR-within-branch', 'sat'), ('M07-omit-target', 'sat'),
    ('M08-target-OR', 'sat'), ('M09-unpaired-source-relabel', 'sat'),
    ('M10-change-inverse-coefficient', 'sat'), ('M11-admit-comparable-family', 'sat'),
    ('M12-admit-duplicate-branch', 'sat'), ('M13-admit-empty-family', 'sat'),
    ('M14-order-quantifier-swap', 'sat'), ('M15-proper-subset-order', 'sat'),
    ('M16-positional-key-swap', 'sat'),
)
SORTS = dict((n, ('BV', w)) for n, w in
             (('a', 7), ('b', 7), ('c', 7), ('q', 3), ('h', 3), ('x', 3), ('k', 4), ('r', 4)))
SORTS.update({'tau': ('Bool', 0)})
SORTS.update((f'w{i}', ('Int', 0)) for i in range(16))
HELPERS = {'fixture': ('Bool', 0), 'positive-table': ('Bool', 0), 'N': ('Int', 0)}
VALUE_KEYS = ('a', 'b', 'c', 'q', 'h', 'x', 'tau', 'k', 'r', ('U', 'a', 'k'), ('V', 'a', 'k'), 'N')
CAP = 1048576


class Reject(ValueError):
    pass


def need(ok, stage, reason):
    if not ok:
        raise Reject(stage + ':' + reason)


def sexprs(data):
    """Bounded ASCII, unquoted atom/list grammar; strings/comments are refused."""
    need(type(data) is bytes and len(data) <= CAP, 'parse', 'byte-cap-or-type')
    need(all(c in (9, 10, 32) or 33 <= c <= 126 for c in data), 'parse', 'ascii-whitespace')
    text = data.decode('ascii')
    tokens = re.findall(r'\(|\)|[^()\s]+', text)
    need(len(tokens) <= 65536, 'parse', 'token-cap')
    out, stack = [], []
    for tok in tokens:
        if tok == '(':
            need(len(stack) < 64, 'parse', 'depth-cap')
            stack.append([])
        elif tok == ')':
            need(bool(stack), 'parse', 'unmatched-close')
            node = tuple(stack.pop())
            (stack[-1] if stack else out).append(node)
        else:
            need(len(tok) <= 256 and re.fullmatch(r'[A-Za-z0-9_!+*/<>=?.:#-]+', tok) is not None,
                 'parse', 'atom-grammar')
            (stack[-1] if stack else out).append(tok)
    need(not stack, 'parse', 'unclosed-list')
    return tuple(out)


def sort_of(expr):
    if expr == 'Bool':
        return ('Bool', 0)
    if expr == 'Int':
        return ('Int', 0)
    if expr in (('_', 'BitVec', '3'), ('_', 'BitVec', '4'), ('_', 'BitVec', '7')):
        return ('BV', int(expr[2]))
    raise Reject('type:sort')


def literal(expr, sort):
    kind, width = sort
    if kind == 'Bool':
        need(expr in ('true', 'false'), 'type', 'bool-literal')
        return expr == 'true'
    if kind == 'Int':
        if type(expr) is str and re.fullmatch(r'0|[1-9][0-9]{0,255}', expr):
            return int(expr)
        if type(expr) is tuple and len(expr) == 2 and expr[0] == '-':
            need(type(expr[1]) is str and re.fullmatch(r'[1-9][0-9]{0,255}', expr[1]) is not None,
                 'type', 'negative-integer')
            return -int(expr[1])
        raise Reject('type:integer-literal')
    if type(expr) is str and expr.startswith('#b'):
        need(re.fullmatch(r'#b[01]+', expr) is not None and len(expr) == width + 2,
             'type', 'bv-binary-width')
        return int(expr[2:], 2)
    if type(expr) is str and expr.startswith('#x'):
        need(re.fullmatch(r'#x[0-9a-fA-F]+', expr) is not None and 4 * (len(expr) - 2) == width,
             'type', 'bv-hex-width')
        return int(expr[2:], 16)
    if type(expr) is tuple and len(expr) == 3 and expr[0] == '_' and expr[2] == str(width):
        need(type(expr[1]) is str and re.fullmatch(r'bv(0|[1-9][0-9]{0,2})', expr[1]) is not None,
             'type', 'bv-decimal-grammar')
        number = int(expr[1][2:])
        need(0 <= number < 2 ** width, 'type', 'bv-decimal-range')
        return number
    raise Reject('type:bv-literal')


def subset(code):
    return frozenset(i for i in range(3) if code & (1 << i))


def family(code):
    return frozenset(subset(b) for b in range(1, 8) if code & (1 << (b - 1)))


def branch_code(branch):
    return sum(1 << i for i in branch)


def family_code(fam):
    return sum(1 << (branch_code(b) - 1) for b in fam)


def incomparable(fam):
    return all(not (a <= b or b <= a) for a, b in itertools.combinations(fam, 2))


def valid(fam):
    return bool(fam) and incomparable(fam)


def below(alpha, beta):
    return all(any(a <= b for a in alpha) for b in beta)


def event(fam, equality):
    return any(branch <= equality for branch in fam)


def raw_sources(cell):
    return tuple((cell >> (3 - i)) & 1 for i in range(3))


def equality(key, cell):
    return frozenset(i for i, (a, b) in enumerate(zip(raw_sources(key), raw_sources(cell))) if a == b)


def target(key, cell):
    return (key & 1) == (cell & 1)


def raw_event(fam, key, cell):
    return event(fam, equality(key, cell))


def matrix_product(a, b):
    size = len(a)
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(size)) for j in range(size)) for i in range(size))


@functools.lru_cache(maxsize=1)
def geometry():
    """Combination enumeration plus exact Gaussian inverse, not incidence recurrence."""
    branches = tuple(subset(b) for b in range(1, 8))
    nodes = []
    for size in range(1, 8):
        nodes.extend(frozenset(c) for c in itertools.combinations(branches, size) if incomparable(frozenset(c)))
    nodes.sort(key=lambda f: (len(f), tuple(sorted(branch_code(b) for b in f))))
    nodes = tuple(nodes)
    need(len(nodes) == 18 and len(set(nodes)) == 18, 'geometry', 'carrier')
    zeta = tuple(tuple(int(below(c, r)) for c in nodes) for r in nodes)
    work = [[Fraction(zeta[i][j]) for j in range(18)] + [Fraction(i == j) for j in range(18)] for i in range(18)]
    for col in range(18):
        pivot = next((r for r in range(col, 18) if work[r][col]), None)
        need(pivot is not None, 'geometry', 'singular')
        work[col], work[pivot] = work[pivot], work[col]
        scale = work[col][col]
        work[col] = [x / scale for x in work[col]]
        for row in range(18):
            if row != col:
                scale = work[row][col]
                work[row] = [x - scale * y for x, y in zip(work[row], work[col])]
    need(all(x.denominator == 1 for row in work for x in row[18:]), 'geometry', 'noninteger-inverse')
    inverse = tuple(tuple(int(x) for x in row[18:]) for row in work)
    identity = tuple(tuple(int(i == j) for j in range(18)) for i in range(18))
    need(matrix_product(inverse, zeta) == identity and matrix_product(zeta, inverse) == identity,
         'geometry', 'two-sided-inverse')
    negative = next(((i, j) for i in range(18) for j in range(18) if inverse[i][j] < 0), None)
    need(negative is not None, 'geometry', 'negative-coefficient')
    bottoms = tuple(f for f in nodes if all(below(f, g) for g in nodes))
    need(len(bottoms) == 1, 'geometry', 'bottom')
    return nodes, zeta, inverse, negative, bottoms[0]


def masses(values):
    fam, key = family(values['a']), values['k']
    weights = tuple(values[f'w{i}'] for i in range(16))
    u = sum(w for cell, w in enumerate(weights) if raw_event(fam, key, cell))
    v = sum(w for cell, w in enumerate(weights) if raw_event(fam, key, cell) and target(key, cell))
    return u, v, sum(weights)


def semantic_check(case, values):
    nodes, zeta, inverse, negative, bottom = geometry()
    a, b, c = (family(values[n]) for n in ('a', 'b', 'c'))
    q, h, x = (subset(values[n]) for n in ('q', 'h', 'x'))
    key, cell = values['k'], values['r']
    ev, raw, tar = event(a, x), raw_event(a, key, cell), target(key, cell)
    fix = (x == equality(key, cell) and values['tau'] is tar
           and all(values[f'w{i}'] == int(i in (key, cell)) for i in range(16)))
    pair = valid(a) and valid(b)
    premise, difference = True, False
    if case == 'C01-premise-nonvacuity':
        premise, difference = pair and valid(c) and fix, True
    elif case == 'M01-reverse-order':
        premise, difference = pair, below(a, b) != below(b, a)
    elif case == 'M02-transpose-zeta':
        premise = pair
        if premise:
            difference = zeta[nodes.index(b)][nodes.index(a)] != int(below(b, a))
    elif case == 'M03-omit-antichain':
        difference = valid(a) != (a in nodes and a != bottom)
    elif case in ('M04-padded-zero-branch', 'M05-AND-across-branches', 'M06-OR-within-branch',
                  'M07-omit-target', 'M08-target-OR', 'M09-unpaired-source-relabel'):
        premise = valid(a) and fix
        if case == 'M04-padded-zero-branch':
            difference = ev != (ev or frozenset() <= x)
        elif case == 'M05-AND-across-branches':
            difference = ev != all(branch <= x for branch in a)
        elif case == 'M06-OR-within-branch':
            difference = ev != any(bool(branch & x) for branch in a)
        elif case == 'M07-omit-target':
            difference = (raw and tar) != raw
        elif case == 'M08-target-OR':
            difference = (raw and tar) != (raw or tar)
        else:
            switched = frozenset((2, 1, 0)[i] for i in x)
            difference = ev != event(a, switched)
    elif case == 'M10-change-inverse-coefficient':
        premise = pair
        if premise:
            row, col = nodes.index(a), nodes.index(b)
            ni, nj = negative
            product = sum((-inverse[row][j] if (row, j) == (ni, nj) else inverse[row][j])
                          * zeta[j][col] for j in range(18))
            difference = product != int(a == b)
    elif case == 'M11-admit-comparable-family':
        difference = valid(a) != bool(a)
    elif case == 'M12-admit-duplicate-branch':
        premise = q == h
        proper = bool(q) and bool(h) and q != h and not (q <= h or h <= q)
        mutant = bool(q) and bool(h) and (q == h or not (q <= h or h <= q))
        difference = proper != mutant
    elif case == 'M13-admit-empty-family':
        premise, difference = not a, valid(a) != incomparable(a)
    elif case == 'M14-order-quantifier-swap':
        premise = pair
        difference = below(a, b) != any(all(branch <= other for other in b) for branch in a)
    elif case == 'M15-proper-subset-order':
        premise = valid(a)
        difference = below(a, a) != all(any(branch < other for branch in a) for other in a)
    elif case == 'M16-positional-key-swap':
        premise = pair
        if premise:
            f3, f4 = frozenset((subset(3),)), frozenset((subset(4),))
            switched = f4 if a == f3 else f3 if a == f4 else a
            difference = zeta[nodes.index(switched)][nodes.index(b)] != int(below(b, a))
    else:
        raise Reject('semantic:unknown-sat-case')
    need(premise is True, 'semantic', 'premise-false')
    need(difference is True, 'semantic', 'no-counterexample')
    return {'premises_checked': True, 'negated_property_checked': True,
            'nonvacuity_only': case == 'C01-premise-nonvacuity'}


def validate(case, solver, stdout_bytes, stderr_bytes, native_int):
    """Return an explicit decision; unexpected implementation errors are not hidden."""
    try:
        need(type(case) is str and case in dict(ROSTER), 'protocol', 'case')
        need(solver in ('z3', 'cvc5') and type(solver) is str, 'protocol', 'solver')
        need(type(native_int) is int and native_int == 0, 'transport', 'native')
        need(type(stderr_bytes) is bytes and stderr_bytes == b'', 'transport', 'stderr')
        need(type(stdout_bytes) is bytes and len(stdout_bytes) <= CAP, 'transport', 'stdout-cap-or-type')
        expected = dict(ROSTER)[case]
        echo = case + ' expect=' + expected
        if solver == 'cvc5':
            echo = '"' + echo + '"'
        prefix = (echo + '\n' + expected + '\n').encode('ascii')
        need(stdout_bytes.startswith(prefix), 'protocol', 'echo-status')
        rest = stdout_bytes[len(prefix):]
        if expected == 'unsat':
            need(rest == b'', 'protocol', 'unsat-trailing')
            return {'accepted': True, 'case': case, 'solver': solver, 'status': 'unsat',
                    'semantic_sat_model_checked': False, 'unsat_certificate_checked': False}
        frames = sexprs(rest)
        need(len(frames) == 2 and all(type(f) is tuple for f in frames), 'model', 'two-frames')
        model, getvalues = frames
        required = dict(SORTS)
        if solver == 'z3':
            required.update(HELPERS)
        seen, values = set(), {}
        for declaration in model:
            need(type(declaration) is tuple and len(declaration) == 5 and declaration[0] == 'define-fun'
                 and declaration[2] == (), 'model', 'nullary-define-fun')
            name = declaration[1]
            need(type(name) is str and name in required and name not in seen, 'model', 'name-roster')
            need(sort_of(declaration[3]) == required[name], 'type', 'declared-sort')
            seen.add(name)
            if name in SORTS:
                values[name] = literal(declaration[4], required[name])
            else:
                need(declaration[4] != (), 'model', 'empty-helper-body')
        need(seen == set(required) and set(values) == set(SORTS), 'model', 'complete-roster')
        need(len(getvalues) == len(VALUE_KEYS), 'values', 'association-count')
        u, v, n = masses(values)
        computed = dict(values)
        computed.update({('U', 'a', 'k'): u, ('V', 'a', 'k'): v, 'N': n})
        for association, key in zip(getvalues, VALUE_KEYS):
            need(type(association) is tuple and len(association) == 2 and association[0] == key,
                 'values', 'association-key-order')
            sort = SORTS[key] if type(key) is str and key in SORTS else ('Int', 0)
            found = literal(association[1], sort)
            need(type(found) is type(computed[key]) and found == computed[key], 'values', 'assignment-disagreement')
        sem = semantic_check(case, values)
        return {'accepted': True, 'case': case, 'solver': solver, 'status': 'sat',
                'semantic_sat_model_checked': True, 'unsat_certificate_checked': False,
                'opaque_auxiliary_bodies_not_interpreted': sorted(HELPERS) if solver == 'z3' else [],
                'assignments': values, 'derived_U_V_N': [u, v, n], **sem}
    except Reject as exc:
        stage, reason = str(exc).split(':', 1)
        return {'accepted': False, 'stage': stage, 'reason': reason}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_bound(path, limit):
    need(path.is_file() and not path.is_symlink(), 'custody', 'regular-file')
    need(path.stat().st_size <= limit, 'custody', 'file-cap')
    data = path.read_bytes()
    need(len(data) <= limit, 'custody', 'read-cap')
    return data


def capture_receipt(root, case, label, stdout, stderr):
    data = read_bound(root / case / (label + '.capture.json'), 65536)
    rec = json.loads(data)
    need(rec['case'] == case and rec['label'] == label, 'custody', 'receipt-identity')
    need(type(rec['native_exit']) is int and rec['native_exit'] == 0 and rec['reason'] is None,
         'custody', 'native-receipt')
    need(rec['transport_complete'] is True and rec['direct_child_reaped'] is True,
         'custody', 'transport-receipt')
    need(rec['input_before'] == rec['input_after'], 'custody', 'historical-input-drift')
    for channel, raw in (('stdout', stdout), ('stderr', stderr)):
        stream = rec['streams'][channel]
        need(stream['eof_observed'] is True and stream['overflow'] is False
             and stream['first_unretained_byte_hex'] == '' and stream['captured_bytes'] == len(raw)
             and stream['observed_bytes'] == len(raw) and stream['sha256_prefix'] == digest(raw),
             'custody', 'stream-receipt')
    return rec


def qualify_retained(root):
    """Read only retained evidence; receipt trust is explicitly historical, not new solver execution."""
    records = []
    for case, expected in ROSTER:
        folder = root / case
        formula = read_bound(folder / 'generator.stdout.smt2', 65536)
        err = read_bound(folder / 'generator.stderr', 65536)
        gen = capture_receipt(root, case, 'generator', formula, err)
        need(err == b'', 'custody', 'generator-stderr')
        pin = next((p for p in gen['input_before'] if p['name'] == 'generator'), None)
        need(pin is not None and pin['bytes'] == 32608 and pin['sha256'] ==
             '62cd492b20b3d908d26e3838d9d648475d1ea92b9ba5c714bab5844e3a4e6eeb',
             'custody', 'generator-source')
        for solver in ('z3', 'cvc5'):
            out = read_bound(folder / (solver + '.stdout'), CAP)
            err = read_bound(folder / (solver + '.stderr'), CAP)
            receipt = capture_receipt(root, case, solver, out, err)
            fp = next((p for p in receipt['input_before'] if p['name'] == 'formula'), None)
            need(fp is not None and fp['bytes'] == len(formula) and fp['sha256'] == digest(formula),
                 'custody', 'formula-input')
            decision = validate(case, solver, out, err, receipt['native_exit'])
            need(decision.get('accepted') is True and decision['status'] == expected,
                 'qualification', case + '-' + solver + '-' + str(decision))
            records.append({**decision, 'stdout_sha256': digest(out), 'stderr_sha256': digest(err),
                            'formula_sha256': digest(formula)})
    need(len(records) == 78 and sum(r['semantic_sat_model_checked'] for r in records) == 34,
         'qualification', 'complete-roster')
    nodes, zeta, inverse, negative, bottom = geometry()
    return {'status': 'retained78_protocol_and34_assignment_semantics_checked',
            'retained_observations_not_fresh': True, 'unsat_certificates_checked': False,
            'scope': 'binary finite SMT39; no original-Finset transport, B-L, old-SPEC or Program closure',
            'model_helper_bodies_semantically_checked': False,
            'carrier': [family_code(f) for f in nodes], 'zeta': zeta, 'gaussian_inverse': inverse,
            'negative_coordinate': negative, 'bottom': family_code(bottom), 'records': records}


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != '--retained':
        raise SystemExit('usage: model_checker.py --retained CAPTURE_ROOT')
    try:
        result = qualify_retained(Path(sys.argv[2]))
        print(json.dumps(result, sort_keys=True, separators=(',', ':')))
    except (Reject, KeyError, ValueError, OSError) as exc:
        print(json.dumps({'status': 'failed_STOP', 'error': type(exc).__name__, 'message': str(exc)}, sort_keys=True))
        raise SystemExit(1)
