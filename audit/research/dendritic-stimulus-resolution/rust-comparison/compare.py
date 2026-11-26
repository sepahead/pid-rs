"""Check all four named atoms at every registered rule and input resolution."""
from fractions import Fraction
from itertools import combinations
import json
import math
import re
import struct

WIDTHS = ("10", "50", "100")
CHANNELS = ("informative", "misinformative", "signed", "imin")
TOLERANCE = Fraction(1, 10**12)


def need(ok, label):
    if not ok:
        raise ValueError(label)


def unique_object(pairs):
    data = {}
    for key, value in pairs:
        need(key not in data, "duplicate object key")
        data[key] = value
    return data


def load_json(raw):
    return json.loads(raw, object_pairs_hook=unique_object)


def integer_list(items, length):
    return (type(items) is list and len(items) == length
            and all(type(x) is int for x in items))


def expected_rows(raw):
    cells = [line.split() for line in raw.splitlines()]
    need(len(cells) == 31 and all(len(row) == 21 for row in cells), "grid shape")
    output = {key: [] for key in WIDTHS}
    for row, line in enumerate(cells):
        for column, token in enumerate(line):
            need(re.fullmatch(rb'[0-4]\.0000', token), "integral archived response")
            count = token[0] - 48
            target = (0, 1, 1, 2, 2)[count]
            for key in WIDTHS:
                step = int(key) // 10
                output[key].append([row // step, column // step, int(row > column), target])
    return output


def validate_rows(proposal, expected):
    need(type(proposal) is dict and set(proposal) == set(WIDTHS), "proposed resolutions")
    for width in WIDTHS:
        rows = proposal[width]
        need(type(rows) is list and len(rows) == 651, "651 separately weighted cells")
        need(all(integer_list(row, 4) for row in rows), "strict four categorical labels")
        need(rows == expected[width], "original row order, axes, strict flag or thresholds")


def canonical_nodes():
    out = set()
    for length in range(1, 8):
        for masks in combinations(range(1, 8), length):
            if all(a & b not in (a, b) for a, b in combinations(masks, 2)):
                out.add("+".join(f"{m:02x}" for m in masks))
    need(len(out) == 18, "all normalized nonempty three-source antichains")
    return out


def key_of(masks):
    need(type(masks) is list and all(type(x) is int and 1 <= x <= 7 for x in masks),
         "original source masks")
    need(len(masks) == len(set(masks)), "source group repeated")
    return "+".join(f"{value:02x}" for value in sorted(masks))


def binary64(hexword):
    need(type(hexword) is str and re.fullmatch(r'[0-9a-f]{16}', hexword), "binary64 word")
    value, = struct.unpack(">d", bytes.fromhex(hexword))
    need(math.isfinite(value), "nonfinite output")
    return Fraction.from_float(value)


def write_bits(x):
    return struct.pack(">d", x).hex()


def exact_pair(pair):
    need(type(pair) is list and len(pair) == 2 and all(
        type(s) is str and re.fullmatch(r'[1-9a-f][0-9a-f]*', s) for s in pair), "hex product")
    numerator, denominator = (int(s, 16) for s in pair)
    need(math.gcd(numerator, denominator) == 1, "positive reduced coordinate")
    return Fraction(numerator, denominator)


def build_targets(exact, log_interval):
    need(set(exact) == set(WIDTHS), "reference widths")
    result = {}
    nodes = canonical_nodes()
    for width in WIDTHS:
        table = exact[width]
        need(len(table["keys"]) == 18 and set(table["keys"]) == nodes, "reference key identities")
        for channel in CHANNELS:
            values = table[channel]
            need(len(values) == len(nodes), "reference channel count")
            for key, pair in zip(table["keys"], values, strict=True):
                q = exact_pair(pair)
                low, high = log_interval(q, 651, 256)
                need(low <= high and high - low <= Fraction(2, 1 << 256), "enclosure width")
                need((low == high == 0) == (q == 1), "reference unit-product identity")
                result[width, channel, key] = q, low, high
    need(len(result) == 216, "full reference dimension")
    return result


def collect(actual, inputs):
    need(type(actual) is dict and set(actual) == set(WIDTHS), "native widths")
    entries = {}
    order = {}
    for width in WIDTHS:
        need(set(actual[width]) == {"mgw", "imin"}, "both native routes")
        rows = inputs[width]
        support = len({tuple(r) for r in rows})
        cards = [len({r[i] for r in rows}) for i in range(4)]
        need(support == {"10": 651, "50": 59, "100": 27}[width], "occupied input rows")
        for method, channels in (("mgw", CHANNELS[:3]), ("imin", CHANNELS[3:])):
            obj = actual[width][method]
            need(type(obj["sample_count"]) is int and obj["sample_count"] == 651, "native rows")
            need(type(obj["support"]) is int and obj["support"] == support, "native support")
            need(integer_list(obj["cardinalities"], 4) and obj["cardinalities"] == cards,
                 "native marginal cardinalities")
            need(obj["encoding"] == "Categorical", "native categorical encoding")
            if method == "mgw":
                need(obj["pointwise_included"] is False and type(obj["pointwise_len"]) is int
                     and obj["pointwise_len"] == 0, "averaged-only scope")
            atoms = obj["atoms"]
            need(type(atoms) is list and len(atoms) == 18, "native 18 atom records")
            keys = []
            for record in atoms:
                need(set(record) == {"masks", *channels}, "atom field identity")
                key = key_of(record["masks"])
                keys.append(key)
                for channel in channels:
                    name = width, channel, key
                    need(name not in entries, "duplicate coordinate")
                    entries[name] = binary64(record[channel])
            need(set(keys) == canonical_nodes(), "native antichain family")
            order[width, method] = keys
    return entries, order


def ratio_text(value):
    return [str(value.numerator), str(value.denominator)]


def check(actual, inputs, targets):
    entries, order = collect(actual, inputs)
    need(set(entries) == set(targets), "complete common set")
    summary = {}
    for width in WIDTHS:
        summary[width] = {}
        for channel in CHANNELS:
            errors = {}
            units, printed_zeros, negative, resolved = [], [], [], []
            for node in sorted(canonical_nodes()):
                index = width, channel, node
                q, low, high = targets[index]
                observed = entries[index]
                err = max(abs(observed - low), abs(observed - high))
                need(err <= TOLERANCE, "absolute error at " + "/".join(index))
                if low > TOLERANCE or high < -TOLERANCE:
                    need((observed > 0) == (low > 0), "resolved sign")
                    resolved.append(node)
                if q == 1:
                    units.append(node)
                    if observed == 0:
                        printed_zeros.append(node)
                if q < 1:
                    negative.append(node)
                errors[node] = err
            worst = max(errors, key=errors.get)
            summary[width][channel] = {
                "coordinates": len(errors), "max_error_upper_nats": float(errors[worst]),
                "max_error_upper_exact": ratio_text(errors[worst]), "worst_key": worst,
                "unit_products": units, "native_zeros_at_units": printed_zeros,
                "exact_negative_product_logs": negative, "resolved_signs": len(resolved),
            }
    need(sum(x["coordinates"] for row in summary.values() for x in row.values()) == 216,
         "216 measured atoms")
    return {"output_coordinates": 216, "absolute_tolerance_nats": "1/1000000000000",
            "summary": summary, "returned_key_order": {w:{m:order[w,m] for m in ("mgw","imin")}
                                                        for w in WIDTHS}}
