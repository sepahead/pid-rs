"""Compare every parity-table event with a second, literal Boolean calculation."""
import argparse
from hashlib import sha256
from itertools import combinations, permutations, product
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
POSITIONS = (0, 1, 2)
ROWS = (
    (0, 0, 0, 0), (0, 0, 0, 1), (0, 1, 1, 0), (0, 1, 1, 1),
    (1, 0, 1, 0), (1, 0, 1, 1), (1, 1, 0, 0), (1, 1, 0, 1),
)
MESSAGE = ("Matched 1,728 parity-table coordinates across 16 keys and six source orders: "
           "1,680 finite signed terms and 48 undefined full-source terms.")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digits(items):
    return "".join(str(value) for value in items)


def family_name(family):
    return "|".join(sorted(digits(i + 1 for i in sorted(branch)) for branch in family))


def families():
    branches = [frozenset(a) for size in range(1, 4) for a in combinations(POSITIONS, size)]
    return [family for size in range(1, 8) for family in combinations(branches, size)
            if all(not (a < b or b < a) for a, b in combinations(family, 2))]


def relabel(key, order):
    return tuple(key[i] for i in order) + (key[3],)


def event_counts(rows, key, family):
    matching = set()
    for branch in family:
        matching.update(index for index, row in enumerate(rows)
                        if all(row[i] == key[i] for i in branch))
    target = {index for index, row in enumerate(rows) if row[3] == key[3]}
    return len(rows), len(matching), len(matching & target), len(target)


def calculate():
    nodes = families()
    keys = tuple(product((0, 1), repeat=4))
    orders = tuple(permutations(POSITIONS))
    require(len(nodes) == len({family_name(f) for f in nodes}) == 18, "three-source node carrier")
    require(len(set(ROWS)) == 8 and len(keys) == 16 and len(orders) == 6, "fixture domain")
    baseline = {}
    terms = []
    reference = {}
    finite = undefined = 0
    for order in orders:
        table = [relabel(row, order) for row in ROWS]
        for key in keys:
            moved = relabel(key, order)
            point_finite = 0
            for node in nodes:
                label = family_name(node)
                transformed = [frozenset(order.index(i) for i in branch) for branch in node]
                transformed_label = family_name(transformed)
                counts = event_counts(table, moved, transformed)
                n, u, v, t = counts
                if order == POSITIONS:
                    baseline[key, label] = counts
                    if key == (1, 1, 1, 1):
                        reference[label] = [u, v]
                require(counts == baseline[key, label], "source relabeling changed an event count")
                require(n == 8 and t == 4 and u == 2 * v, "parity balance")
                if v > 0:
                    require(u > 0 and n * v == u * t, "finite signed ratio differs from one")
                    point_finite += 1
                    finite += 1
                else:
                    require(u == 0 and key not in ROWS and label == "123", "unexpected null event")
                    undefined += 1
                fields = [digits(i + 1 for i in order), digits(key), label, digits(moved),
                          transformed_label, *(str(value) for value in counts)]
                terms.append("\t".join(fields))
            require(point_finite == (18 if key in ROWS else 17), "wrong support profile for a key")
    require((len(terms), finite, undefined) == (1728, 1680, 48), "coordinate totals")
    examples = {"1": [4, 2], "12": [2, 1], "1|2|3": [6, 3], "123": [0, 0]}
    require(all(reference[name] == counts for name, counts in examples.items()), "printed counts")
    require(baseline[(1, 1, 0, 1), "123"] == (8, 2, 1, 4), "occupied full-source comparison")
    stream = ("\n".join(sorted(terms)) + "\n").encode("ascii")
    receipt = {
        "schema": "three-source-parity-counts-v1",
        "columns": ["source_order", "original_key", "original_node", "transformed_key",
                    "transformed_node", "N", "U", "V", "T"],
        "rows": [digits(row) for row in ROWS],
        "source_orders": [digits(i + 1 for i in order) for order in orders],
        "absent_keys_per_order": len(keys) - len(ROWS),
        "occupied_keys_per_order": len(ROWS),
        "nodes_per_key": len(nodes),
        "coordinates": len(terms),
        "finite_signed_zero_nats": finite,
        "undefined_full_source": undefined,
        "reference_111_target_1_U_V": reference,
        "sorted_coordinate_tsv_sha256": sha256(stream).hexdigest(),
    }
    return stream, receipt


def compare(actual, expected):
    require(actual == expected, "ordered event coordinates differ")


def check_controls(stream):
    rows = stream.splitlines(keepends=True)
    first = rows[0].rstrip(b"\n").split(b"\t")
    for column in (4, 6):
        altered = first.copy()
        altered[column] += b"0"
        invalid = b"\t".join(altered) + b"\n" + b"".join(rows[1:])
        try:
            compare(invalid, stream)
        except ValueError:
            continue
        raise ValueError("accepted an altered node label or count")
    try:
        compare(b"".join(rows[:-1]), stream)
    except ValueError:
        return
    raise ValueError("accepted a missing coordinate")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--emit-record", action="store_true", help="print the reproducible finite receipt")
    args = cli.parse_args()
    expected, receipt = calculate()
    literal = subprocess.check_output(["ruby", "--disable-gems", str(HERE / "parity_rows.rb")],
                                      cwd=HERE, timeout=30)
    compare(literal, expected)
    check_controls(expected)
    encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.emit_record:
        print(encoded, end="")
    else:
        require((HERE / "parity-results.json").read_bytes() == encoded.encode(), "stored parity receipt differs")
        print(MESSAGE)


if __name__ == "__main__":
    main()
