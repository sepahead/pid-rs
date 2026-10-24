"""Exact empirical MGW research reference, not a production estimator."""

from collections import Counter
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
from math import gcd

MAX_BITS = 1_048_576
SCALE = 1 << 80


def require(condition, message):
    if not condition:
        raise ValueError(message)


def below(left, right):
    return all(any(a & b == a for a in left) for b in right)


def carrier():
    nodes = []
    for choice in range(1, 128):
        branches = tuple(i + 1 for i in range(7) if choice & (1 << i))
        if all(not (a & b == a or a & b == b)
               for j, a in enumerate(branches) for b in branches[j + 1:]):
            nodes.append(branches)
    predecessor_counts = {a: sum(below(b, a) for b in nodes) for a in nodes}
    nodes.sort(key=lambda a: (predecessor_counts[a], a))
    require(len(nodes) == 18, "carrier size")
    zeta = [[int(below(b, a)) for b in nodes] for a in nodes]
    inverse = [[0] * 18 for _ in nodes]
    for i in range(18):
        require(zeta[i][i] == 1 and not any(zeta[i][i + 1:]), "not triangular")
        for j in range(i + 1):
            inverse[i][j] = int(i == j) - sum(zeta[i][k] * inverse[k][j]
                                            for k in range(i))
    for left, right in ((zeta, inverse), (inverse, zeta)):
        require(all(sum(left[i][k] * right[k][j] for k in range(18)) == int(i == j)
                    for i in range(18) for j in range(18)), "inverse identity")
    require(sum(abs(v) for row in inverse for v in row) == 65, "inverse norm")
    return nodes, zeta, inverse


def matches(anchor, row, node, *, wrong_or=False):
    equal = [anchor[i] == row[i] for i in range(3)]
    if wrong_or:
        return any(any(equal[i] for i in range(3) if b & (1 << i)) for b in node)
    return any(all(equal[i] for i in range(3) if b & (1 << i)) for b in node)


def factors(terms):
    result = Counter()
    for base, power in terms:
        require(isinstance(base, Fraction) and base > 0, "nonpositive log base")
        require(type(power) is int, "noninteger exponent")
        if base != 1:
            result[base] += power
    return tuple(sorted((b, e) for b, e in result.items() if e))


def combine(parts):
    return factors((base, power * weight) for terms, weight in parts
                   for base, power in terms)


def safe_multiply(a, b):
    g1 = gcd(a.numerator, b.denominator)
    g2 = gcd(b.numerator, a.denominator)
    x, y = a.numerator // g1, b.numerator // g2
    u, v = a.denominator // g2, b.denominator // g1
    require(x.bit_length() + y.bit_length() <= MAX_BITS + 1
            and u.bit_length() + v.bit_length() <= MAX_BITS + 1, "product bit preflight")
    result = Fraction(x * y, u * v)
    require(max(result.numerator.bit_length(), result.denominator.bit_length()) <= MAX_BITS,
            "product bit limit")
    return result


@lru_cache(maxsize=4096)
def prime_factors(value):
    require(type(value) is int and 0 < value < 2**32, "small-base factorization limit")
    result = []
    divisor = 2
    remaining = value
    while divisor * divisor <= remaining:
        exponent = 0
        while remaining % divisor == 0:
            remaining //= divisor
            exponent += 1
        if exponent:
            result.append((divisor, exponent))
        divisor = 3 if divisor == 2 else divisor + 2
    if remaining > 1:
        result.append((remaining, 1))
    return tuple(result)


def balanced_integer_product(items):
    if not items:
        return 1
    while len(items) > 1:
        next_level = []
        for i in range(0, len(items), 2):
            if i + 1 == len(items):
                next_level.append(items[i])
                continue
            left, right = items[i:i+2]
            require(left.bit_length() + right.bit_length() <= MAX_BITS + 1,
                    "balanced product bit preflight")
            result = left * right
            require(result.bit_length() <= MAX_BITS, "balanced product bit limit")
            next_level.append(result)
        items = next_level
    return items[0]


@lru_cache(maxsize=128)
def exact_product(terms):
    exponents = Counter()
    for base, power in terms:
        if power < 0:
            base, power = 1 / base, -power
        # Preserve the original preflight BEFORE factoring or exponentiation.
        require(base.numerator.bit_length() * power <= MAX_BITS
                and base.denominator.bit_length() * power <= MAX_BITS, "power bit preflight")
        for integer, sign in ((base.numerator, 1), (base.denominator, -1)):
            for prime, multiplicity in prime_factors(integer):
                exponents[prime] += sign * power * multiplicity
    numerator_parts, denominator_parts = [], []
    for prime, exponent in sorted(exponents.items()):
        if not exponent:
            continue
        require(prime.bit_length() * abs(exponent) <= MAX_BITS, "prime power bit preflight")
        piece = pow(prime, abs(exponent))
        (numerator_parts if exponent > 0 else denominator_parts).append(piece)
    numerator = balanced_integer_product(numerator_parts)
    denominator = balanced_integer_product(denominator_parts)
    # Opposite prime exponents have already cancelled exactly. Fraction still
    # performs its ordinary normalization; no library or numeric default changes.
    return Fraction(numerator, denominator)

def series_bounds(z):
    require(0 <= z <= Fraction(1, 3), "range reduction")
    square, power, total = z * z, z, Fraction(0)
    for i in range(64):
        total += 2 * power / (2 * i + 1)
        power *= square
    return total, total + 2 * power / (129 * (1 - square))


@lru_cache(maxsize=4096)
def logarithm(base):
    require(base > 0, "log domain")
    k = base.numerator.bit_length() - base.denominator.bit_length()
    y = base / (Fraction(2) ** k)
    while y < 1:
        y *= 2
        k -= 1
    while y >= 2:
        y /= 2
        k += 1
    lo, hi = series_bounds((y - 1) / (y + 1))
    two_lo, two_hi = series_bounds(Fraction(1, 3))
    lo, hi = (lo + k * two_lo, hi + k * two_hi) if k >= 0 else (
        lo + k * two_hi, hi + k * two_lo)
    return lo.numerator * SCALE // lo.denominator, -((-hi.numerator * SCALE) // hi.denominator)


def interval(terms, n=1):
    require(type(n) is int and n > 0, "normalization")
    if exact_product(terms) == 1:
        return Fraction(0), Fraction(0)
    low = high = 0
    for base, power in terms:
        a, b = logarithm(base)
        low += power * (a if power >= 0 else b)
        high += power * (b if power >= 0 else a)
    result = Fraction(low, SCALE * n), Fraction(high, SCALE * n)
    require(result[0] <= result[1] and result[1] - result[0] <= Fraction(1, 10**12),
            "unresolved interval width")
    return result


def add_intervals(items):
    return tuple(sum(item[i] for item in items) for i in (0, 1))


def absolute_interval(pair):
    lo, hi = pair
    return max(lo, -hi, 0), max(abs(lo), abs(hi))


def record(terms, n):
    product = exact_product(terms)
    low, high = interval(terms, n)
    numerator = product.numerator.to_bytes((product.numerator.bit_length() + 7) // 8, 'big')
    denominator = product.denominator.to_bytes((product.denominator.bit_length() + 7) // 8, 'big')
    digest = sha256(b'PM1' + len(numerator).to_bytes(8, 'big') + numerator
                    + len(denominator).to_bytes(8, 'big') + denominator).hexdigest()
    return {'factors': [[b.numerator, b.denominator, e] for b, e in terms],
            'sign': (product > 1) - (product < 1), 'product_sha256': digest,
            'interval': [str(low), str(high)], 'display_nats': float((low + high) / 2)}


def evaluate(counts, target_size, *, wrong_or=False):
    require(type(target_size) is int and 1 <= target_size <= 4, "target size")
    require(isinstance(counts, dict) and 0 < len(counts) <= 32, "count table shape")
    for key, value in counts.items():
        require(type(key) is tuple and len(key) == 4
                and all(type(x) is int and 0 <= x <= 1 for x in key[:3])
                and type(key[3]) is int and 0 <= key[3] < target_size, "joint key")
        require(type(value) is int and value > 0, "count must be positive integer")
    n = sum(counts.values())
    require(n <= 32768, "row limit")
    nodes, zeta, inverse = carrier()
    cumulative = {'plus': [], 'minus': [], 'net': []}
    for node in nodes:
        plus, minus = [], []
        for anchor, weight in sorted(counts.items()):
            event = [(key, c) for key, c in counts.items()
                     if matches(anchor, key, node, wrong_or=wrong_or)]
            u = sum(c for _, c in event)
            v = sum(c for key, c in event if key[3] == anchor[3])
            t = sum(c for key, c in counts.items() if key[3] == anchor[3])
            require(0 < v <= u <= n and v <= t <= n, "event count range")
            plus.append((Fraction(n, u), weight))
            minus.append((Fraction(t, v), weight))
        cumulative['plus'].append(factors(plus))
        cumulative['minus'].append(factors(minus))
        cumulative['net'].append(combine([(factors(plus), 1), (factors(minus), -1)]))
    atoms = {component: [combine(zip(cumulative[component], row)) for row in inverse]
             for component in cumulative}
    for component in atoms:
        for i, row in enumerate(zeta):
            recovered = combine(zip(atoms[component], row))
            require(exact_product(recovered) == exact_product(cumulative[component][i]),
                    "product zeta reconstruction")
    return {'n': n, 'nodes': nodes, 'zeta': zeta, 'inverse': inverse,
            'cumulative': cumulative, 'atoms': atoms}


def transformed(counts, heads):
    require(len(heads) == 2 and heads[0] != heads[1]
            and all(type(h) is tuple and len(h) == 2
                    and all(type(v) is int and v in (0, 1) for v in h) for h in heads),
            "two distinct legal heads required")
    result = Counter()
    for (x, y, z, t), c in counts.items():
        a, b = heads
        yy, zz = (y, z) if (y, z) in heads else a
        result[x, yy, zz, t] += c
    return dict(result)


def compare_laws(counts, heads, target_size, reference):
    q = transformed(counts, heads)
    before, after = evaluate(counts, target_size), evaluate(q, target_size)
    n = before['n']
    require(after['n'] == n, "mass loss")
    marginal = lambda c: Counter({k: sum(v for z, v in c.items() if (z[0], z[3]) == k)
                                  for k in {(z[0], z[3]) for z in c}})
    require(marginal(counts) == marginal(q), "retained-target marginal")
    tail = Fraction(sum(c for z, c in counts.items() if z[1:3] not in heads), n)
    tv = Fraction(sum(abs(counts.get(z, 0) - q.get(z, 0)) for z in counts.keys() | q.keys()), 2*n)
    require(tv == tail, "TV must equal tail")
    # The independent adapter is supplied only after this candidate is frozen.
    for raw, value in ((counts, before), (q, after)):
        reference(raw, target_size, value)
    differences = [combine([(a, 1), (b, -1)])
                   for a, b in zip(before['atoms']['net'], after['atoms']['net'])]
    signed = [interval(f, n) for f in differences]
    distances = []
    for f, pair in zip(differences, signed):
        product = exact_product(f)
        distances.append(pair if product > 1 else (-pair[1], -pair[0]) if product < 1 else (Fraction(0), Fraction(0)))
    distance = add_intervals(distances)
    mi_changes = {mask: combine([(before['cumulative']['net'][before['nodes'].index((mask,))], 1),
                                (after['cumulative']['net'][after['nodes'].index((mask,))], -1)])
                  for mask in range(1, 8)}
    lost = interval(mi_changes[7], n)
    require(exact_product(mi_changes[7]) >= 1, "negative known-law information loss")
    require(distance[1] >= lost[0], "inconsistent allocation/loss")
    require(distance[1] - distance[0] <= Fraction(1, 10**12), "allocation width")
    # Equal quantities have overlapping outward intervals. Exact atom signs
    # and the reconstructed full sum instead give D = L + 2*redistribution.
    negative_changes = [(-pair[1], -pair[0]) for f, pair in zip(differences, signed)
                        if exact_product(f) < 1]
    redistribution = add_intervals(negative_changes) if negative_changes else (Fraction(0), Fraction(0))
    source_support = sorted({z[:3] for z in counts})
    mapping = lambda s: s if s[1:] in heads else (s[0], *heads[0])
    partitions = [all((s[i] == u[i]) == (mapping(s)[i] == mapping(u)[i])
                      for s in source_support for u in source_support) for i in range(3)]
    cuts = []
    for mask, f in mi_changes.items():
        complement = combine([(mi_changes[7], 1), (f, -1)])
        cut = add_intervals([absolute_interval(interval(f, n)),
                             absolute_interval(interval(complement, n))])
        cuts.append((mask, cut))
    lower = max(pair[0] for _, pair in cuts)
    require(lower <= distance[1], "MI cut exceeds allocation")
    recover = []
    for condition_x in (False, True):
        fine, coarse = Counter(), Counter()
        for z, c in counts.items():
            x, y, zz, _ = z
            out = (y, zz) if (y, zz) in heads else heads[0]
            fine[((x,) if condition_x else ()) + (y, zz)] += c
            coarse[((x,) if condition_x else ()) + out] += c
        terms = []
        for key, c in fine.items():
            prefix, y = (key[:1], key[1:]) if condition_x else ((), key)
            out = y if y in heads else heads[0]
            terms.append((Fraction(coarse[prefix + out], c), c))
        recover.append(record(factors(terms), n))
    paired = []
    for stage in ('cumulative', 'atoms'):
        for component in ('plus', 'minus', 'net'):
            for i, node in enumerate(before['nodes']):
                paired.append({'stage': stage, 'component': component, 'branches': list(node),
                               'before': record(before[stage][component][i], n),
                               'after': record(after[stage][component][i], n)})
    return {'rows': n, 'counts': [[*z, c] for z, c in sorted(counts.items())],
            'mapped_counts': [[*z, c] for z, c in sorted(q.items())],
            'tail': str(tail), 'tv': str(tv), 'allocation_interval': [str(v) for v in distance],
            'allocation_display_nats': float(sum(distance)/2),
            'redistribution_interval': [str(v) for v in redistribution],
            'lost_information': record(mi_changes[7], n),
            'mi_changes': [{'source_mask': m, 'change': record(f, n)} for m, f in mi_changes.items()],
            'mi_cut_lower_nats': str(lower), 'mi_cut_display_nats': float(lower),
            'source_partition_preserved': partitions,
            'tuple_recovery_entropy': recover[0], 'conditional_tuple_recovery_entropy': recover[1],
            'coordinates': paired}

