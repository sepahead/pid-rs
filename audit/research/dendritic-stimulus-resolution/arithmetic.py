"""Finite event arithmetic and directed rational logarithm enclosures for the six-table readback.

Functions are selected from the arithmetic reference frozen before the paired run.
"""
from fractions import Fraction
from functools import lru_cache
import re
COMPONENTS = ("informative", "misinformative", "net")
SCOPES = ("cumulative", "atom")
SCHEDULE = (256, 384, 512, 768, 1024, 1536, 2048)
MAX_ROWS = 1024
MAX_TERMS = 8192
MAX_POWER = 1_048_576
MAX_COORD_BITS = 262_144
MAX_TOTAL_BITS = 8_388_608
MAX_OPERATIONS = 100_000_000
MAX_HEAP = 536_870_912
MAX_INPUT_BYTES = 4_194_304
MAX_COUNT_BITS = 8192
MAX_WIDTH = Fraction(1, 1 << 160)
TOKEN = re.compile(r"[A-Za-z0-9._:-]{1,128}", re.ASCII)
DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)", re.ASCII)


class ArithmeticReject(ValueError):
    """A failed check or exhausted resource. No numerical decision follows."""


def require(ok, message):
    if not ok:
        raise ArithmeticReject(message)


def ceildiv(a, b):
    return -((-a) // b)


def unsigned(text, maximum_digits):
    """Admit the complete string before constructing an integer, including on Python 3.11+."""
    require(type(text) is str and 0 < len(text) <= maximum_digits, "integer-digit-bound")
    require(DECIMAL.fullmatch(text) is not None, "noncanonical-unsigned")
    value = 0
    for start in range(0, len(text), 9):
        piece = text[start:start+9]
        value = value * 10**len(piece) + int(piece)
    return value


def typed_rows(rows):
    require(type(rows) is list and 0 < len(rows) <= MAX_ROWS, "row-count")
    table, total, content_bytes = [], 0, 0
    previous = None
    comparison_lengths = [0, 0, 0, 0]
    for row in rows:
        require(type(row) is dict and set(row) == {"count", "source_states", "target_state"},
                "row-members")
        require(type(row["source_states"]) is list and len(row["source_states"]) == 3, "three-sources")
        count = unsigned(row["count"], 4096)
        require(count > 0 and count.bit_length() <= MAX_COUNT_BITS, "positive-count-bits")
        total += count
        require(total.bit_length() <= MAX_COUNT_BITS, "total-count-bits")
        key = []
        for i, state in enumerate((*row["source_states"], row["target_state"])):
            require(type(state) is list and 0 < len(state) <= 64, "state-token-count")
            for token in state:
                require(type(token) is str and 0 < len(token) <= 128
                        and TOKEN.fullmatch(token) is not None, "token")
            n = sum(1 + len(token) for token in state)
            comparison_lengths[i] = max(comparison_lengths[i], n)
            content_bytes += n
            key.append(tuple(state))
        content_bytes += len(row["count"])
        require(content_bytes <= MAX_INPUT_BYTES, "input-content-bound")
        key = tuple(key)
        require(previous is None or previous < key, "row-order-or-duplicate")
        previous = key
        table.append((key, count))
    return table, total, comparison_lengths


@lru_cache(maxsize=1)
def lattice():
    nodes = []
    for family in range(1, 1 << 7):
        patterns = frozenset(i for i in range(1, 8) if family & (1 << (i - 1)))
        if any((p & q) == p and q not in patterns for p in patterns for q in range(1, 8)):
            continue
        minimal = tuple(p for p in sorted(patterns)
                        if not any(q != p and (q & p) == q for q in patterns))
        nodes.append((minimal, patterns))
    nodes.sort(key=lambda item: (len(item[0]), item[0]))
    keys = tuple(a for a, _ in nodes)
    zeta = tuple(tuple(int(event <= lower_event) for _, lower_event in nodes)
                 for _, event in nodes)
    n = len(keys)
    require(n == 18 and sum(map(sum, zeta)) == 129, "carrier")
    identity = tuple(tuple(int(i == j) for j in range(n)) for i in range(n))
    mu = [None] * n
    for i in sorted(range(n), key=lambda j: sum(zeta[j])):
        row = list(identity[i])
        for j, flag in enumerate(zeta[i]):
            if flag and j != i:
                require(mu[j] is not None, "poset-order")
                row = [v - w for v, w in zip(row, mu[j])]
        mu[i] = tuple(row)
    for left, right in ((zeta, mu), (mu, zeta)):
        require(all(sum(left[i][k]*right[k][j] for k in range(n)) == identity[i][j]
                    for i in range(n) for j in range(n)), "inverse-orientation")
    require(sum(int(v != 0) for line in mu for v in line) == 65, "mobius-sparsity")
    return keys, zeta, tuple(mu)


def reserve(table, total, lengths):
    # At most 4 keyed state comparisons, with at most one length comparison and
    # the admitted bytes per token array. Bound mask intersections, union and
    # target-intersection row membership in separately charged set operations.
    nodes, _, _ = lattice()
    n = len(table)
    state_and_set_units = 4 + sum(lengths) + 16 + sum(len(a) for a in nodes) + 18
    operations = n*n*state_and_set_units
    require(operations <= MAX_OPERATIONS, "event-comparison-preflight")
    integer_bytes = ceildiv(total.bit_length()+4, 8)
    # Base reserves the admitted input model and interpreter-side working buffers.
    # Keep only 36 cumulative factor bags and one <=16*rows coordinate decomposition
    # at a time. 96*rows slots cover dict over-allocation, two-pass transients/sets.
    # Per slot reserves object headers and sixteen times magnitude storage. Eight MiB
    # separately cover current large-int arithmetic, range reduction and stored answers.
    planned_heap = 48*1024**2 + 96*n*(1024 + 16*integer_bytes) + 8*1024**2
    require(planned_heap <= MAX_HEAP, "independent-planned-heap")
    return operations, planned_heap


def record(plan, factor, count):
    if factor == 1 or count == 0:
        return
    new = plan.get(factor, 0) + count
    if new:
        plan[factor] = new
    elif factor in plan:
        del plan[factor]


def base_plans(table, total):
    nodes, _, _ = lattice()
    plans = [[{} for _ in nodes] for _ in range(2)]
    for anchor, multiplicity in table:
        equal = [set() for _ in range(4)]
        for i, (key, _) in enumerate(table):
            for j in range(4):
                if key[j] == anchor[j]:
                    equal[j].add(i)
        target_mass = sum(table[i][1] for i in equal[3])
        at_mask = {}
        for mask in range(1, 8):
            columns = [equal[j] for j in range(3) if mask & (1 << j)]
            at_mask[mask] = set.intersection(*columns)
        for j, node in enumerate(nodes):
            event = set.union(*(at_mask[mask] for mask in node))
            joint = sum(table[i][1] for i in event.intersection(equal[3]))
            mass = sum(table[i][1] for i in event)
            require(0 < multiplicity <= joint <= mass <= total and joint <= target_mass <= total,
                    "event-mass")
            record(plans[0][j], Fraction(total, mass), multiplicity)
            record(plans[1][j], Fraction(target_mass, joint), multiplicity)
    return plans


def projections(base):
    nodes, _, mu = lattice()
    for scope in SCOPES:
        for component in COMPONENTS:
            for i, masks in enumerate(nodes):
                plan = {}
                transform = enumerate(mu[i]) if scope == "atom" else ((i, 1),)
                for j, multiplier in transform:
                    if not multiplier:
                        continue
                    channels = ((0, 1), (1, -1)) if component == "net" else (
                        (0 if component == "informative" else 1, 1),)
                    for channel, sign in channels:
                        for factor, exponent in base[channel][j].items():
                            record(plan, factor, multiplier*sign*exponent)
                key = "+".join(format(mask, "02x") for mask in masks)
                yield (scope, component, key, masks), plan


def preflight(plans):
    max_terms = max_exponent = max_bits = aggregate = counted = 0
    for _, plan in plans:
        counted += 1
        require(len(plan) <= MAX_TERMS, "terms-preflight")
        max_terms = max(max_terms, len(plan))
        size = 2
        for q, exponent in plan.items():
            magnitude = abs(exponent)
            require(magnitude <= MAX_POWER, "exponent-preflight")
            max_exponent = max(max_exponent, magnitude)
            size += magnitude * (q.numerator.bit_length()+q.denominator.bit_length())
            require(size <= MAX_COORD_BITS, "coordinate-bits-preflight")
        max_bits = max(max_bits, size)
        aggregate += size
        require(aggregate <= MAX_TOTAL_BITS, "aggregate-bits-preflight")
    require(counted == 108, "plan-cardinality")
    return max_terms, max_exponent, max_bits, aggregate


def exact_product(plan):
    value = Fraction(1)
    for factor, exponent in plan.items():
        value *= factor**exponent
    return value


def atanh_log_bounds(n, d, bits):
    """Bounds for 2*atanh(n/d) in units of 2^-bits, 0 <= n/d <= 1/3."""
    require(0 <= 3*n <= d and d > 0, "atanh-domain")
    if n == 0:
        return 0, 0
    scale = 1 << bits
    low, high = n*scale//d, ceildiv(n*scale, d)
    step_low, step_high = (low*low)//scale, ceildiv(high*high, scale)
    total_low = total_high = 0
    count = ceildiv(bits, 3) + 1
    for i in range(count):
        odd = 2*i + 1
        total_low += 2*low//odd
        total_high += ceildiv(2*high, odd)
        low = low*step_low//scale
        high = ceildiv(high*step_high, scale)
    # Direct geometric bound <= (3/4) 2^(-3 count)/(2 count+1) <= one ulp.
    return total_low, total_high + 1


@lru_cache(maxsize=len(SCHEDULE))
def log_two(bits):
    return atanh_log_bounds(1, 3, bits)


def log_interval(q, total, bits):
    require(q > 0 and total > 0 and bits in SCHEDULE, "log-domain")
    if q == 1:
        return Fraction(0), Fraction(0)
    a, b = q.numerator, q.denominator
    e = a.bit_length() - b.bit_length()
    below_power = a < (b << e) if e >= 0 else (a << -e) < b
    if below_power:
        e -= 1
    if e >= 0:
        b <<= e
    else:
        a <<= -e
    require(b <= a < 2*b, "range-reduction")
    guard_bits = 24
    low, high = atanh_log_bounds(a-b, a+b, bits+guard_bits)
    l2, u2 = log_two(bits+guard_bits)
    low, high = (low+e*u2, high+e*l2) if e < 0 else (low+e*l2, high+e*u2)
    denominator = total << guard_bits
    return Fraction(low//denominator, 1 << bits), Fraction(ceildiv(high, denominator), 1 << bits)
