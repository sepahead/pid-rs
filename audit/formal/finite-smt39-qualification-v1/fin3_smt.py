#!/usr/bin/env python3
"""Unexecuted P3-B-S v2; unchanged finite semantics; derive all tables.
Shared packet/row exposure; no Lean/owner Python read. Independence is
mathematical encoding, not transcription/custody. W12 forward inclusion;
binary raw cells; no closure. Cooperative bounds are not RSS/deadlines.
"""

import json
import sys


SOURCE_COUNT = 3
BRANCHES = tuple(range(1, 1 << SOURCE_COUNT))
FAMILY_WIDTH = len(BRANCHES)
FAMILY_LIMIT = 1 << FAMILY_WIDTH
EMIT_CAP = 65536

# Frozen literally before any derivation; ROSTER.tsv preserves this same roster.
FROZEN_ROSTER = (
    ("W01-carrier-complete", "unsat"),
    ("W02-exactly-18-distinct", "unsat"),
    ("W03-reflexivity", "unsat"),
    ("W04-antisymmetry", "unsat"),
    ("W05-transitivity", "unsat"),
    ("W06-zeta-all-324", "unsat"),
    ("W07-MZ-all-324", "unsat"),
    ("W08-ZM-all-324", "unsat"),
    ("W09-branch-event-equivalence", "unsat"),
    ("W10-raw-source-equivalence", "unsat"),
    ("W11-raw-target-restriction", "unsat"),
    ("W12-order-event-inclusion", "unsat"),
    ("W13-key-membership", "unsat"),
    ("W14-supported-mass-bounds", "unsat"),
    ("W15-full-joint-event", "unsat"),
    ("W16-singleton-event", "unsat"),
    ("W17-permutation-012", "unsat"),
    ("W18-permutation-021", "unsat"),
    ("W19-permutation-102", "unsat"),
    ("W20-permutation-120", "unsat"),
    ("W21-permutation-201", "unsat"),
    ("W22-permutation-210", "unsat"),
    ("C01-premise-nonvacuity", "sat"),
    ("M01-reverse-order", "sat"),
    ("M02-transpose-zeta", "sat"),
    ("M03-omit-antichain", "sat"),
    ("M04-padded-zero-branch", "sat"),
    ("M05-AND-across-branches", "sat"),
    ("M06-OR-within-branch", "sat"),
    ("M07-omit-target", "sat"),
    ("M08-target-OR", "sat"),
    ("M09-unpaired-source-relabel", "sat"),
    ("M10-change-inverse-coefficient", "sat"),
    ("M11-admit-comparable-family", "sat"),
    ("M12-admit-duplicate-branch", "sat"),
    ("M13-admit-empty-family", "sat"),
    ("M14-order-quantifier-swap", "sat"),
    ("M15-proper-subset-order", "sat"),
    ("M16-positional-key-swap", "sat"),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def members(family):
    return tuple(b for b in BRANCHES if family & (1 << (b - 1)))


def subset(left, right):
    return (left & right) == left


def family_valid(family):
    if family == 0:
        return False
    bs = members(family)
    return all(
        not subset(a, b) and not subset(b, a)
        for i, a in enumerate(bs)
        for b in bs[i + 1 :]
    )


def below(alpha, beta):
    return all(any(subset(a, b) for a in members(alpha)) for b in members(beta))


def permute_mask(mask, permutation):
    # permutation[i] is the NEW source index of OLD source i.
    return sum(1 << permutation[i] for i in range(3) if mask & (1 << i))


def permute_family(family, permutation):
    return sum(1 << (permute_mask(b, permutation) - 1) for b in members(family))


def derive():
    # Exhaust all 128 seven-bit families, not a supplied eighteen-row registry.
    carrier = tuple(
        sorted(
            (f for f in range(FAMILY_LIMIT) if family_valid(f)),
            key=lambda f: (len(members(f)), members(f)),
        )
    )
    require(len(carrier) == 18, "derived carrier cardinality is not eighteen")
    require(len(set(carrier)) == 18, "derived carrier contains a duplicate")
    # A separate linear extension is for the incidence recurrence only; the
    # certificate order remains cardinality then ascending branch tuple.
    remaining = list(carrier)
    linear = []
    while remaining:
        minimal = [
            f for f in remaining
            if all(g == f or not below(g, f) for g in remaining)
        ]
        require(bool(minimal), "the derived order has no minimal remaining node")
        chosen = minimal[0]
        linear.append(chosen)
        remaining.remove(chosen)
    mu = {(a, b): 0 for a in carrier for b in carrier}
    for a in linear:
        mu[a, a] = 1
        for b in linear:
            if a != b and below(a, b):
                # mu(a,b) = -sum_{a<=c<b} mu(a,c).
                mu[a, b] = -sum(
                    mu[a, c] for c in linear
                    if c != b and below(a, c) and below(c, b)
                )
    # Z[row cumulative, column atom] = [column <= row].
    zeta = tuple(tuple(int(below(c, r)) for c in carrier) for r in carrier)
    inverse = tuple(tuple(mu[c, r] for c in carrier) for r in carrier)
    permutations = tuple(
        (i, j, k) for i in range(3) for j in range(3) for k in range(3)
        if len({i, j, k}) == 3
    )
    require(len(permutations) == 6, "source bijection count is not six")
    index = {f: i for i, f in enumerate(carrier)}
    images = tuple(
        tuple(permute_family(f, p) for f in carrier) for p in permutations
    )
    require(
        all(all(f in index for f in row) for row in images),
        "a derived source permutation leaves the carrier",
    )
    negative = [
        (i, j) for i in range(18) for j in range(18) if inverse[i][j] < 0
    ]
    require(bool(negative), "no derived negative inverse coefficient for control")
    bottoms = [a for a in carrier if all(below(a, b) for b in carrier)]
    tops = [b for b in carrier if all(below(a, b) for a in carrier)]
    require(len(bottoms) == len(tops) == 1, "order extrema are not unique")
    return {
        "carrier": carrier, "linear": tuple(linear), "zeta": zeta,
        "inverse": inverse, "permutations": permutations, "images": images,
        "negative": negative[0], "bottom": bottoms[0], "top": tops[0],
    }


def app(operator, *arguments):
    return bounded_join((operator,) + arguments, " ", "(", ")")


def bounded_join(parts, separator, prefix="", suffix=""):
    pieces = []
    size = len(prefix) + len(suffix)
    for part in parts:
        require(type(part) is str, "construction term is not a string")
        size += len(part) + (len(separator) if pieces else 0)
        require(size <= EMIT_CAP and len(pieces) < EMIT_CAP, "construction bound")
        pieces.append(part)
    # Check precedes join/all concatenations; fixed source iterables still have
    # allocations/iteration before checks. No Python allocator or RSS theorem.
    return prefix + separator.join(pieces) + suffix


class Script:
    def __init__(self, initial):
        self.lines = []
        self.size = 0
        self.extend(initial)

    def append(self, line):
        require(type(line) is str and "\n" not in line, "invalid SMT line")
        require(self.size + len(line) + 1 <= EMIT_CAP, "aggregate output bound")
        self.lines.append(line)
        self.size += len(line) + 1

    def extend(self, lines):
        for line in lines:
            self.append(line)

    def render(self):
        return bounded_join(self.lines, "\n", suffix="\n")


def bounded_json(value):
    def cost(v):
        t = type(v)
        if t is str:
            n = 2 + 6 * len(v)  # conservative ensure_ascii escape bound
        elif t is bool:
            n = 5
        elif t is int:
            n = len(str(v))  # integers here are from the fixed finite model
        elif t in (list, tuple):
            n = 2 + max(0, len(v) - 1) + sum(cost(x) for x in v)
        elif t is dict:
            require(all(type(k) is str for k in v), "non-string JSON key")
            n = 2 + max(0, len(v) - 1) + sum(cost(k) + 1 + cost(x) for k, x in v.items())
        else:
            raise ValueError("unsupported JSON type")
        require(n < EMIT_CAP, "JSON construction bound")
        return n
    require(cost(value) + 1 <= EMIT_CAP, "JSON aggregate bound")
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def check_roster(roster):
    expected = dict(FROZEN_ROSTER)
    require(len(FROZEN_ROSTER) == len(expected) == 39, "invalid frozen roster")
    seen = set()
    actual = []
    for case in roster:
        name, status = case["name"], case["expect"]
        require(type(name) is str and type(status) is str, "inexact roster type")
        require(name in expected and name not in seen, "unknown/duplicate case")
        require(status == expected[name], "wrong expected status")
        seen.add(name)
        actual.append((name, status))
    require(tuple(actual) == FROZEN_ROSTER, "missing/reordered frozen case")


def conjunction(arguments):
    args = tuple(arguments)
    return "true" if not args else args[0] if len(args) == 1 else app("and", *args)


def disjunction(arguments):
    args = tuple(arguments)
    return "false" if not args else args[0] if len(args) == 1 else app("or", *args)


def addition(arguments):
    args = tuple(arguments)
    return "0" if not args else args[0] if len(args) == 1 else app("+", *args)


def bit_union(arguments, width):
    # SMT-LIB bvor is binary; do not rely on a solver's n-ary extension.
    result = bv(0, width)
    for argument in reversed(tuple(arguments)):
        result = app("bvor", argument, result)
    return result


def bv(value, width):
    require(type(value) is int and 0 <= value < (1 << width), "invalid bitvector literal")
    return "(_ bv" + str(value) + " " + str(width) + ")"


def integer(value):
    require(type(value) is int, "integer literal has an inexact type")
    return str(value) if value >= 0 else app("-", str(-value))


def bit(term, index, width):
    flag = bv(1 << index, width)
    return app("=", app("bvand", term, flag), flag)


def raw_equal(key, cell, source):
    # cell = 8*s0 + 4*s1 + 2*s2 + target, NOT mask-bit order.
    extract = "(_ extract " + str(3 - source) + " " + str(3 - source) + ")"
    return app("=", app(extract, key), app(extract, cell))


def define(name, parameters, result_sort, body):
    params = bounded_join((app(p, sort) for p, sort in parameters), " ", "(", ")")
    return app("define-fun", name, params, result_sort, body)


FAM = "(_ BitVec 7)"
MASK = "(_ BitVec 3)"
CELL = "(_ BitVec 4)"


def table_lookup(name, matrix, carrier):
    # Omitted serialization branches are exactly ZERO, not unconstrained terms.
    outer = "0"
    for i in reversed(range(len(carrier))):
        inner = "0"
        for j in reversed(range(len(carrier))):
            value = matrix[i][j]
            if value != 0:
                inner = app("ite", app("=", "col", bv(carrier[j], 7)), integer(value), inner)
        outer = app("ite", app("=", "row", bv(carrier[i], 7)), inner, outer)
    return define(name, (("row", FAM), ("col", FAM)), "Int", outer)


def prelude(data):
    carrier = data["carrier"]
    lines = Script([
        "; Independent original-definition finite P3-B-S encoding v2.",
        "; ALL selects mixed BV/Int/Boolean logic; formulas contain no quantifiers.",
        "; No solver-specific kernel, tactic, arithmetic, or proof options.",
        "(set-logic ALL)",
        "(set-option :produce-models true)",
    ])
    for name, sort in (
        ("a", FAM), ("b", FAM), ("c", FAM), ("q", MASK), ("h", MASK),
        ("x", MASK), ("k", CELL), ("r", CELL), ("tau", "Bool"),
    ):
        lines.append(app("declare-const", name, sort))
    lines.extend(app("declare-const", "w" + str(i), "Int") for i in range(16))
    lines.append(define("sub", (("u", MASK), ("v", MASK)), "Bool", app("=", app("bvand", "u", "v"), "u")))
    shift = app("(_ zero_extend 4)", app("bvsub", "u", bv(1, 3)))
    selected = app("bvand", "f", app("bvshl", bv(1, 7), shift))
    lines.append(define("has", (("f", FAM), ("u", MASK)), "Bool", conjunction((
        app("distinct", "u", bv(0, 3)), app("distinct", selected, bv(0, 7)),
    ))))
    incomp = conjunction(
        app("=>", conjunction((app("has", "f", bv(a, 3)), app("has", "f", bv(b, 3)))),
            app("not", disjunction((app("sub", bv(a, 3), bv(b, 3)), app("sub", bv(b, 3), bv(a, 3))))))
        for a in BRANCHES for b in BRANCHES if a < b
    )
    lines.append(define("incomparable", (("f", FAM),), "Bool", incomp))
    lines.append(define("valid", (("f", FAM),), "Bool", conjunction((
        app("distinct", "f", bv(0, 7)), app("incomparable", "f"),
    ))))
    lines.append(define("canonical", (("f", FAM),), "Bool", disjunction(
        app("=", "f", bv(f, 7)) for f in carrier
    )))
    lines.append(define("leq", (("alpha", FAM), ("beta", FAM)), "Bool", conjunction(
        app("=>", app("has", "beta", bv(b, 3)), disjunction(
            conjunction((app("has", "alpha", bv(a, 3)), app("sub", bv(a, 3), bv(b, 3))))
            for a in BRANCHES
        )) for b in BRANCHES
    )))
    lines.append(define("leq-one-for-all", (("alpha", FAM), ("beta", FAM)), "Bool", disjunction(
        conjunction((app("has", "alpha", bv(a, 3)), conjunction(
            app("=>", app("has", "beta", bv(b, 3)), app("sub", bv(a, 3), bv(b, 3)))
            for b in BRANCHES
        ))) for a in BRANCHES
    )))
    lines.append(define("leq-proper", (("alpha", FAM), ("beta", FAM)), "Bool", conjunction(
        app("=>", app("has", "beta", bv(b, 3)), disjunction(
            conjunction((app("has", "alpha", bv(a, 3)), app("sub", bv(a, 3), bv(b, 3)),
                app("distinct", bv(a, 3), bv(b, 3)))) for a in BRANCHES
        )) for b in BRANCHES
    )))
    lines.append(define("singleton", (("u", MASK),), FAM, app("bvshl", bv(1, 7), shift)))
    lines.append(define("branch", (("u", MASK), ("e", MASK)), "Bool", app("=", app("bvand", "u", "e"), "u")))
    lines.append(define("branch-direct", (("u", MASK), ("e", MASK)), "Bool", conjunction(
        app("=>", bit("u", i, 3), bit("e", i, 3)) for i in range(3)
    )))
    for name, branch_name in (("source", "branch"), ("source-direct", "branch-direct")):
        lines.append(define(name, (("f", FAM), ("e", MASK)), "Bool", disjunction(
            conjunction((app("has", "f", bv(b, 3)), app(branch_name, bv(b, 3), "e")))
            for b in BRANCHES
        )))
    lines.append(define("source-outer-and", (("f", FAM), ("e", MASK)), "Bool", conjunction(
        app("=>", app("has", "f", bv(b, 3)), app("branch", bv(b, 3), "e"))
        for b in BRANCHES
    )))
    lines.append(define("source-inner-or", (("f", FAM), ("e", MASK)), "Bool", disjunction(
        conjunction((app("has", "f", bv(b, 3)), app("distinct", app("bvand", bv(b, 3), "e"), bv(0, 3))))
        for b in BRANCHES
    )))
    lines.append(define("restricted", (("f", FAM), ("e", MASK), ("t", "Bool")), "Bool",
        conjunction((app("source", "f", "e"), "t"))))
    lines.append(define("raw-branch", (("u", MASK), ("key", CELL), ("cell", CELL)), "Bool", conjunction(
        app("=>", bit("u", i, 3), raw_equal("key", "cell", i)) for i in range(3)
    )))
    lines.append(define("raw-source", (("f", FAM), ("key", CELL), ("cell", CELL)), "Bool", disjunction(
        conjunction((app("has", "f", bv(b, 3)), app("raw-branch", bv(b, 3), "key", "cell")))
        for b in BRANCHES
    )))
    target_eq = app("=", app("(_ extract 0 0)", "key"), app("(_ extract 0 0)", "cell"))
    lines.append(define("raw-target", (("key", CELL), ("cell", CELL)), "Bool", target_eq))
    lines.append(define("raw-restricted", (("f", FAM), ("key", CELL), ("cell", CELL)), "Bool",
        conjunction((app("raw-source", "f", "key", "cell"), app("raw-target", "key", "cell")))))
    lines.append(define("eq-pattern", (("key", CELL), ("cell", CELL)), MASK, bit_union(
        (app("ite", raw_equal("key", "cell", i), bv(1 << i, 3), bv(0, 3)) for i in range(3)), 3
    )))
    # Two-entry raw syntax controls are separate from the set-valued carrier.
    pair_incomp = app("not", disjunction((app("sub", "u", "v"), app("sub", "v", "u"))))
    nonzero_pair = conjunction((app("distinct", "u", bv(0, 3)), app("distinct", "v", bv(0, 3))))
    lines.append(define("valid-pair", (("u", MASK), ("v", MASK)), "Bool", conjunction((
        nonzero_pair, app("distinct", "u", "v"), pair_incomp,
    ))))
    lines.append(define("pair-duplicate-mutant", (("u", MASK), ("v", MASK)), "Bool", conjunction((
        nonzero_pair, app("=>", app("distinct", "u", "v"), pair_incomp),
    ))))
    lines.append(table_lookup("z", data["zeta"], carrier))
    lines.append(table_lookup("m", data["inverse"], carrier))
    ni, nj = data["negative"]
    lines.append(define("m-changed", (("row", FAM), ("col", FAM)), "Int", app("ite",
        conjunction((app("=", "row", bv(carrier[ni], 7)), app("=", "col", bv(carrier[nj], 7)))),
        integer(-data["inverse"][ni][nj]), app("m", "row", "col"))))
    # Count variables denote the complete sixteen-cell binary empirical table.
    weight = "w15"
    for i in reversed(range(15)):
        weight = app("ite", app("=", "cell", bv(i, 4)), "w" + str(i), weight)
    lines.append(define("weight", (("cell", CELL),), "Int", weight))
    lines.append(define("N", (), "Int", addition("w" + str(i) for i in range(16))))
    lines.append(define("positive-table", (), "Bool", conjunction(
        app(">=", "w" + str(i), "0") for i in range(16)
    )))
    for name, predicate in (("U", "raw-source"), ("V", "raw-restricted")):
        lines.append(define(name, (("f", FAM), ("key", CELL)), "Int", addition(
            app("ite", app(predicate, "f", "key", bv(i, 4)), "w" + str(i), "0")
            for i in range(16)
        )))
    lines.append(define("Tmass", (("key", CELL),), "Int", addition(
        app("ite", app("raw-target", "key", bv(i, 4)), "w" + str(i), "0")
        for i in range(16)
    )))
    # Event mutants have an actual one/two-cell positive table, not just a
    # pattern unattached to raw cells. Both key and comparison cell have count 1.
    fixture = conjunction((
        app("=", "x", app("eq-pattern", "k", "r")),
        app("=", "tau", app("raw-target", "k", "r")),
        conjunction(app("=", "w" + str(i), app("ite", disjunction((
            app("=", "k", bv(i, 4)), app("=", "r", bv(i, 4)),
        )), "1", "0")) for i in range(16)),
    ))
    lines.append(define("fixture", (), "Bool", fixture))
    for j, permutation in enumerate(data["permutations"]):
        prefix = "p" + str(j)
        lines.append("; " + prefix + " old-to-new sources = " + str(permutation))
        lines.append(define(prefix + "-mask", (("u", MASK),), MASK, bit_union((
            app("ite", bit("u", i, 3), bv(1 << permutation[i], 3), bv(0, 3))
            for i in range(3)
        ), 3)))
        lines.append(define(prefix + "-family", (("f", FAM),), FAM, bit_union((
            app("ite", app("has", "f", bv(b, 3)),
                bv(1 << (permute_mask(b, permutation) - 1), 7), bv(0, 7))
            for b in BRANCHES
        ), 7)))
        lookup = bv(0, 7)
        for f, image in reversed(tuple(zip(carrier, data["images"][j]))):
            lookup = app("ite", app("=", "f", bv(f, 7)), bv(image, 7), lookup)
        lines.append(define(prefix + "-table", (("f", FAM),), FAM, lookup))
        # Preserve target bit zero and move each source cell bit consistently.
        pieces = [app("ite", bit("cell", 0, 4), bv(1, 4), bv(0, 4))]
        pieces.extend(
            app("ite", bit("cell", 3 - i, 4), bv(1 << (3 - permutation[i]), 4), bv(0, 4))
            for i in range(3)
        )
        lines.append(define(prefix + "-cell", (("cell", CELL),), CELL, bit_union(pieces, 4)))
    return lines


def cases(data):
    carrier = data["carrier"]
    result = []

    def add(name, expectation, premises, theorem, meaning):
        require(expectation in ("sat", "unsat"), "invalid expected status")
        result.append({
            "name": name, "expect": expectation,
            "premises": conjunction(premises), "theorem": theorem, "meaning": meaning,
        })

    va = app("valid", "a")
    vb = app("valid", "b")
    vc = app("valid", "c")
    add("W01-carrier-complete", "unsat", (), app("=", va, app("canonical", "a")),
        "all 128 families equal the derived canonical membership predicate")
    count = addition(app("ite", app("valid", bv(f, 7)), "1", "0") for f in range(128))
    add("W02-exactly-18-distinct", "unsat", (), conjunction((
        app("=", count, "18"), app("distinct", *(bv(f, 7) for f in carrier)),
    )), "eighteen valid families, each canonical representation distinct")
    add("W03-reflexivity", "unsat", (va,), app("leq", "a", "a"), "order reflexivity")
    add("W04-antisymmetry", "unsat", (va, vb, app("leq", "a", "b"), app("leq", "b", "a")),
        app("=", "a", "b"), "order antisymmetry on antichains")
    add("W05-transitivity", "unsat", (va, vb, vc, app("leq", "a", "b"), app("leq", "b", "c")),
        app("leq", "a", "c"), "order transitivity")
    add("W06-zeta-all-324", "unsat", (va, vb), app("=", app("z", "a", "b"),
        app("ite", app("leq", "b", "a"), "1", "0")),
        "all 18x18 generated entries have column-below-row orientation")

    def product(left, right):
        # Z is 0/1; ite avoids nonlinear integer arithmetic while calculating
        # the full finite product. Every one of eighteen intermediate nodes is
        # present, including terms whose coefficient is zero.
        if right == "z":
            return addition(app("ite", app("=", app("z", bv(f, 7), "b"), "1"),
                app(left, "a", bv(f, 7)), "0") for f in carrier)
        return addition(app("ite", app("=", app("z", "a", bv(f, 7)), "1"),
            app(right, bv(f, 7), "b"), "0") for f in carrier)

    delta = app("ite", app("=", "a", "b"), "1", "0")
    add("W07-MZ-all-324", "unsat", (va, vb), app("=", product("m", "z"), delta),
        "integer inverse times zeta is identity at all 324 entries")
    add("W08-ZM-all-324", "unsat", (va, vb), app("=", product("z", "m"), delta),
        "zeta times integer inverse is identity at all 324 entries")
    add("W09-branch-event-equivalence", "unsat", (va,),
        app("=", app("source", "a", "x"), app("source-direct", "a", "x")),
        "AND within each branch and OR across selected branches")
    add("W10-raw-source-equivalence", "unsat", (va,), app("=",
        app("raw-source", "a", "k", "r"), app("source", "a", app("eq-pattern", "k", "r"))),
        "18 families times all 256 raw binary key/cell pairs")
    add("W11-raw-target-restriction", "unsat", (va,), app("=",
        app("raw-restricted", "a", "k", "r"),
        app("restricted", "a", app("eq-pattern", "k", "r"), app("raw-target", "k", "r"))),
        "the target equality is conjoined to the DNF source event")
    add("W12-order-event-inclusion", "unsat", (va, vb, app("leq", "a", "b")),
        app("=>", app("source", "b", "x"), app("source", "a", "x")),
        "alpha<=beta implies the beta event is contained in the alpha event")
    add("W13-key-membership", "unsat", (va,), conjunction((
        app("raw-source", "a", "k", "k"), app("raw-restricted", "a", "k", "k"),
        app("not", app("has", "a", bv(0, 3))),
    )), "the key belongs to every valid event and no zero branch is selected")
    add("W14-supported-mass-bounds", "unsat", (va, "positive-table", app(">", app("weight", "k"), "0")),
        conjunction((
            app(">", "N", "0"), app("<=", app("weight", "k"), app("V", "a", "k")),
            app("<=", app("V", "a", "k"), app("U", "a", "k")),
            app("<=", app("U", "a", "k"), "N"),
            app("<=", app("V", "a", "k"), app("Tmass", "k")),
            app("<=", app("Tmass", "k"), "N"),
        )), "arbitrary nonnegative integer counts on the complete binary table")
    add("W15-full-joint-event", "unsat", (), app("=",
        app("raw-source", bv(data["top"], 7), "k", "r"),
        conjunction(raw_equal("k", "r", i) for i in range(3))),
        "the derived top event requires all three source equalities")
    add("W16-singleton-event", "unsat", (app("distinct", "q", bv(0, 3)),), app("=",
        app("raw-source", app("singleton", "q"), "k", "r"), app("raw-branch", "q", "k", "r")),
        "all seven single-branch families denote their source conjunction")
    for j, permutation in enumerate(data["permutations"]):
        prefix = "p" + str(j)
        pa = app(prefix + "-family", "a")
        pb = app(prefix + "-family", "b")
        pk = app(prefix + "-cell", "k")
        pr = app(prefix + "-cell", "r")
        theorem = conjunction((
            app("valid", pa), app("canonical", pa),
            app("=", pa, app(prefix + "-table", "a")),
            app("distinct", *(app(prefix + "-family", bv(f, 7)) for f in carrier)),
            app("=>", app("=", pa, pb), app("=", "a", "b")),
            app("=", app("leq", "a", "b"), app("leq", pa, pb)),
            app("=", app("z", "a", "b"), app("z", pa, pb)),
            app("=", app("m", "a", "b"), app("m", pa, pb)),
            app("=", app("source", "a", "x"), app("source", pa, app(prefix + "-mask", "x"))),
            app("=", app("raw-source", "a", "k", "r"), app("raw-source", pa, pk, pr)),
            app("=", app("raw-restricted", "a", "k", "r"), app("raw-restricted", pa, pk, pr)),
            app("=", app("raw-target", "k", "r"), app("raw-target", pk, pr)),
        ))
        add("W" + str(17 + j).zfill(2) + "-permutation-" + "".join(map(str, permutation)),
            "unsat", (va, vb), theorem,
            "complete carrier/order/incidence/event automorphism for old-to-new " + str(permutation))
    add("C01-premise-nonvacuity", "sat", (va, vb, vc, "fixture"), "false",
        "a supported positive table and three valid carrier nodes exist")
    add("M01-reverse-order", "sat", (va, vb),
        app("=", app("leq", "a", "b"), app("leq", "b", "a")), "reverse the declared order direction")
    add("M02-transpose-zeta", "sat", (va, vb),
        app("=", app("z", "b", "a"), app("ite", app("leq", "b", "a"), "1", "0")),
        "transpose the cumulative-row/atom-column zeta serialization")
    missing = disjunction(app("=", "a", bv(f, 7)) for f in carrier if f != data["bottom"])
    add("M03-omit-antichain", "sat", (), app("=", va, missing), "omit the independently derived bottom carrier node")
    event_premises = (va, "fixture")
    event = app("source", "a", "x")
    add("M04-padded-zero-branch", "sat", event_premises,
        app("=", event, disjunction((event, app("branch", bv(0, 3), "x")))),
        "add an empty conjunction as a source branch")
    add("M05-AND-across-branches", "sat", event_premises,
        app("=", event, app("source-outer-and", "a", "x")), "replace outer OR by AND")
    add("M06-OR-within-branch", "sat", event_premises,
        app("=", event, app("source-inner-or", "a", "x")), "replace within-branch AND by OR")
    restricted = app("raw-restricted", "a", "k", "r")
    raw_event = app("raw-source", "a", "k", "r")
    add("M07-omit-target", "sat", event_premises,
        app("=", restricted, raw_event), "omit the target equality restriction")
    add("M08-target-OR", "sat", event_premises,
        app("=", restricted, disjunction((raw_event, app("raw-target", "k", "r")))),
        "replace conjunction with the target by disjunction")
    swap_index = data["permutations"].index((2, 1, 0))
    add("M09-unpaired-source-relabel", "sat", event_premises,
        app("=", event, app("source", "a", app("p" + str(swap_index) + "-mask", "x"))),
        "swap source-zero/source-two equality bits without mapping the family")
    add("M10-change-inverse-coefficient", "sat", (va, vb),
        app("=", product("m-changed", "z"), delta),
        "flip the first derived negative inverse coefficient")
    add("M11-admit-comparable-family", "sat", (),
        app("=", va, app("distinct", "a", bv(0, 7))), "discard antichain incomparability")
    add("M12-admit-duplicate-branch", "sat", (app("=", "q", "h"),),
        app("=", app("valid-pair", "q", "h"), app("pair-duplicate-mutant", "q", "h")),
        "admit a repeated branch in raw two-entry family syntax")
    add("M13-admit-empty-family", "sat", (app("=", "a", bv(0, 7)),),
        app("=", va, app("incomparable", "a")), "discard nonempty-family requirement")
    add("M14-order-quantifier-swap", "sat", (va, vb),
        app("=", app("leq", "a", "b"), app("leq-one-for-all", "a", "b")),
        "replace for-every-beta-branch/some-alpha-branch by some-alpha/for-every-beta")
    add("M15-proper-subset-order", "sat", (va,),
        app("=", app("leq", "a", "a"), app("leq-proper", "a", "a")),
        "replace subset inclusion by strict subset inclusion")
    # Deliberate POSITIONAL row swap, distinct from a consistently applied source
    # permutation. Derive the two keys from singleton masks rather than a table.
    f3 = 1 << (3 - 1)
    f4 = 1 << (4 - 1)
    swapped = app("ite", app("=", "a", bv(f3, 7)), bv(f4, 7),
        app("ite", app("=", "a", bv(f4, 7)), bv(f3, 7), "a"))
    add("M16-positional-key-swap", "sat", (va, vb),
        app("=", app("z", swapped, "b"), app("ite", app("leq", "b", "a"), "1", "0")),
        "swap singleton source-mask 03/04 row keys while retaining semantic keys")
    require(len({case["name"] for case in result}) == len(result), "duplicate obligation identity")
    return result


def emit(data, selected):
    lines = prelude(data)
    standalone = len(selected) == 1
    for case in selected:
        lines.extend((
            "; " + case["meaning"],
            app("echo", bounded_json(case["name"] + " expect=" + case["expect"])),
        ))
        if not standalone:
            lines.append("(push 1)")
        lines.extend((app("assert", case["premises"]),
            app("assert", app("not", case["theorem"])), "(check-sat)",
        ))
        if case["expect"] == "sat":
            lines.append("(get-model)")
            lines.append("(get-value (a b c q h x tau k r (U a k) (V a k) N))")
        if not standalone:
            lines.append("(pop 1)")
    lines.append("(exit)")
    output = lines.render()
    require(len(output.encode("ascii")) <= EMIT_CAP, "SMT output exceeds fixed 65536-byte cap")
    return output


def table_record(data):
    carrier = data["carrier"]
    index = {f: i for i, f in enumerate(carrier)}
    return {
        "status": "derived-data-only-not-solver-evidence",
        "source_bits": {"0": 1, "1": 2, "2": 4},
        "family_bits": "branch b in 1..7 uses bit b-1 of a seven-bit family",
        "raw_cell": "8*s0+4*s1+2*s2+t",
        "carrier_order": "branch count, then lexicographic ascending branch tuple",
        "keys": ["+".join(format(b, "02x") for b in members(f)) for f in carrier],
        "family_values": list(carrier),
        "branches": [list(members(f)) for f in carrier],
        "topological_families": list(data["linear"]),
        "zeta_orientation": "row cumulative, column atom: Z[i,j]=[C[j]<=C[i]]",
        "zeta": [list(row) for row in data["zeta"]],
        "inverse": [list(row) for row in data["inverse"]],
        "permutations_old_to_new": [list(p) for p in data["permutations"]],
        "permutation_indices": [[index[f] for f in row] for row in data["images"]],
        "mutant_inverse_coordinate": list(data["negative"]),
        "scope": "original finite P3-B-S; no logarithm, intervals, Rust, or closure credit",
    }


def main(arguments):
    # The interface neither reads an artifact nor writes a file nor invokes a
    # solver. Caller-owned custody, solver pins, bounded capture, and transcript
    # rejection are separate obligations; comments/expected statuses are no proof.
    require(arguments != [], "use --emit all|CASE, --tables, or --expectations")
    require(
        (len(arguments) == 1 and arguments[0] in ("--tables", "--expectations"))
        or (len(arguments) == 2 and arguments[0] == "--emit"),
        "unexpected arguments",
    )
    data = derive()
    roster = cases(data)
    check_roster(roster)
    if arguments[0] == "--tables":
        output = bounded_json(table_record(data)) + "\n"
    elif arguments[0] == "--expectations":
        output = bounded_json({
            "encoding": "fin3-independent-original-definition-smt-v2",
            "expected_only": True,
            "wanted": sum(c["expect"] == "unsat" for c in roster),
            "sat_controls": sum(c["expect"] == "sat" for c in roster),
            "obligations": [{k: c[k] for k in ("name", "expect", "meaning")} for c in roster],
            "solver_execution": "not supplied by this generator",
        }) + "\n"
    else:
        requested = arguments[1]
        selected = roster if requested == "all" else [c for c in roster if c["name"] == requested]
        require(bool(selected), "unknown obligation identity")
        output = emit(data, selected)
    require(len(output.encode("ascii")) <= EMIT_CAP, "output exceeds fixed byte cap")
    sys.stdout.write(output)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (ValueError, UnicodeError) as error:
        sys.stderr.write("REFUSED: " + str(error) + "\n")
        raise SystemExit(2)
