"""Apply the copied-target support criterion to the recorded LP4 force and torque trends."""
import argparse
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import io
import json
from pathlib import Path
from zipfile import ZipFile


ZIP_HASH = "cdfbe0b260f4a21c5249fe0da4b1baf4041959663a9182253885ee1f41a4568e"
LP4_HASH = "f0c901ead751ff3104d7e1aeb23165efb88270b219c1954c43bfff2344a7bb3c"
SIGNS = (-1, 0, 1)


def require(value, message):
    if not value:
        raise ValueError(message)


def trend_sign(window, column):
    # Pair terms at equal distances on opposite sides of sample seven.
    difference = sum(offset * (window[7 + offset][column] - window[7 - offset][column])
                     for offset in range(1, 8))
    return (difference > 0) - (difference < 0)


def read_counts(raw):
    lines = [line.split() for line in raw.decode("ascii").splitlines() if line.strip()]
    require(len(lines) == 16 * 117, "Expected 117 labels followed by 15 measurements each")
    hist = Counter()
    for start in range(0, len(lines), 16):
        require(lines[start] in (["normal"], ["collision"], ["obstruction"]), "Unknown LP4 label")
        window = [tuple(map(int, line)) for line in lines[start + 1:start + 16]]
        require(all(len(row) == 6 for row in window), "Expected six channels at every time")
        hist[trend_sign(window, 2), trend_sign(window, 5)] += 1
    return hist


def summarize(hist):
    require(hist and all(type(n) is int and n > 0 for n in hist.values()), "Positive integer counts")
    n = sum(hist.values())
    rows = Counter()
    columns = Counter()
    for (x, w), count in hist.items():
        rows[x] += count
        columns[w] += count
    cells = []
    q = Fraction(1)
    for (x, w), count in sorted(hist.items()):
        a, b = rows[x], columns[w]
        factor = Fraction(a*b, count*(a+b-count))
        branching = count < a and count < b
        require(factor >= 1 and (factor > 1) == branching, "Support criterion")
        q *= factor ** count
        cells.append({"force": x, "torque": w, "count": count, "row": a, "column": b,
                      "ratio": str(factor), "shares_both": branching})
    with localcontext() as context:
        context.prec = 70
        magnitude = (Decimal(q.numerator).ln() - Decimal(q.denominator).ln()) / Decimal(n)
        single = format(magnitude, ".15f")
        total = format(2*magnitude, ".15f")
    return {"observations": n, "occupied": len(cells), "cells": cells,
            "count_matrix_negative_zero_positive": [[hist.get((x, w), 0) for w in SIGNS] for x in SIGNS],
            "individual_positive_rational": str(q), "five_signed_products":
            {"04": str(1/q), "05": str(q), "06": "1", "05+06": "1", "07": "1"},
            "five_signed_sum_product": "1", "single_magnitude_nats_rounded": single,
            "sum_of_absolute_means_nats_rounded": total,
            "signed_means_all_zero": q == 1,
            "cells_sharing_row_and_column": sum(cell["shares_both"] for cell in cells)}


def self_test():
    for counts in [{(0, 0): 3}, {(0, 0): 2, (0, 1): 1, (1, 2): 1},
                   {(0, 1): 1, (1, 0): 1, (1, 2): 1, (2, 1): 1}]:
        require(summarize(counts)["signed_means_all_zero"], "Zero by support")
    four = {(0, 0): 1, (1, 1): 1, (1, 2): 1, (2, 1): 1}
    require(summarize(four)["individual_positive_rational"] == "4/3", "Intersecting occupied cell")
    require(summarize({key: 2*n for key,n in four.items()})["individual_positive_rational"] == "16/9",
            "Doubling all counts squares the product")


def main():
    options = argparse.ArgumentParser(description=__doc__)
    options.add_argument("archive", type=Path)
    args = options.parse_args()
    self_test()
    content = args.archive.read_bytes()
    require(sha256(content).hexdigest() == ZIP_HASH, "Expected the original donor archive")
    with ZipFile(io.BytesIO(content)) as archive:
        require(archive.namelist().count("lp4.data") == 1, "Expected one LP4 file")
        raw = archive.read("lp4.data")
    require(len(raw) == 33619 and sha256(raw).hexdigest() == LP4_HASH, "Unexpected LP4 data")
    result = summarize(read_counts(raw))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
