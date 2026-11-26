"""Find and replay two-grid-unit empirical MGW cumulative values in four-row tables.

Run with the path of the original six-table arithmetic.py. Search uses exact integers.
"""
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import runpy
import sys


ORIGINAL = "b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2"
GUARD = 1 << 24


def require(test, message):
    if not test:
        raise ValueError(message)


def four_rows(total, revealed):
    rows = []
    for a in ("0", "1"):
        for target, count in ((a, revealed // 2), ("x", (total - revealed) // 2)):
            rows.append({"count": str(count), "source_states": [[a], ["fixed"], ["fixed"]],
                         "target_state": [target]})
    return rows


def replay(original, p, n, m, lower, upper):
    rows = four_rows(n, m)
    cells, total, lengths = original["typed_rows"](rows)
    require(total == n and len(cells) == 4, "complete occupied joint tuples and total")
    work, memory = original["reserve"](cells, total, lengths)
    base = original["base_plans"](cells, total)
    plans = list(original["projections"](base))
    metrics = list(original["preflight"](plans))
    single = {key[1]: plan for key, plan in plans if key[0] == "cumulative" and
              key[2] == "01" and key[3] == (1,)}
    require(single == {"informative": {Fraction(2): n}, "misinformative": {Fraction(2): n-m},
                       "net": {Fraction(2): m}}, "all three MGW singleton products")
    q = original["exact_product"](single["net"])
    require(q == Fraction(1 << m), "selected net exact positive power")
    output = original["log_interval"](q, n, p)
    grid = [u * (1 << p) for u in output]
    require(all(u.denominator == 1 for u in grid), "exact final output grid")
    nums = [u.numerator for u in grid]
    divisor = n * GUARD
    expected = [m * lower // divisor, -((-m * upper) // divisor)]
    require(nums == expected and nums[1] - nums[0] == 2, "actual crossing of a final grid point")
    return {"rows": rows, "n": n, "m": m, "exact_plan": "2^m",
            "all_108_original_plans": len(plans), "coordinate_preflights": metrics,
            "event_operations_charged": work, "heap_bytes_reserved": memory,
            "output_grid_endpoint_numerators_decimal": [str(a) for a in nums],
            "width_in_grid_units": nums[1] - nums[0]}


def find(original, p):
    lower, upper = original["log_two"](p + 24)
    width = upper - lower
    examined = 0
    rejected = []
    for n in range(4, 24577, 2):
        divisor = n * GUARD
        step = (2 * lower) % divisor
        residue = 0
        for m in range(2, n, 2):
            examined += 1
            residue += step
            if residue >= divisor:
                residue -= divisor
            # m*width < divisor. The endpoints span two precisely across an internal grid line.
            if residue + m * width > divisor:
                try:
                    witness = replay(original, p, n, m, lower, upper)
                except original["ArithmeticReject"] as failure:
                    rejected.append([n, m, str(failure)])
                    continue
                return {"p": p, "examined_pairs_in_fixed_order": examined,
                        "prior_original_resource_rejections": rejected, "witness": witness}
    raise ValueError(("no admitted width-two table in fixed family", p, examined))


def main(path):
    require(sha256(path.read_bytes()).hexdigest() == ORIGINAL, "original arithmetic identity")
    source = runpy.run_path(str(path))
    schedule = (256, 384, 512, 768, 1024, 1536, 2048)
    require(source["SCHEDULE"] == schedule, "frozen seven output fields")
    results = [find(source, p) for p in schedule]
    require(len(results) == 7, "all returned fields")
    print(json.dumps({"original_source_sha256": ORIGINAL, "search_order": "even N=4 through 24576; even m=2 through N-2; first positive original four-row admission per field",
                      "object": "empirical MGW signed cumulative singleton source A with two constant sources, uniform binary A, target reveals or erases A independently",
                      "result": "each scheduled precision has an actual 2-unit finite-count width witness; no claim these are the earlier six observed inputs",
                      "records": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
