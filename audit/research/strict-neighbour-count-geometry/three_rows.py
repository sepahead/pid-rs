"""Exact three-row witnesses and complete sign configurations on three undirected edges."""
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from whole_upper import count, harmonic, require


def main():
    edges = [(0, 1), (0, 2), (1, 2)]
    frequencies = [0] * 4
    for signs in product((-1, 0, 1), repeat=3):
        mixed = 0
        for vertex in range(3):
            incident = {s for edge, s in zip(edges, signs, strict=True) if vertex in edge}
            mixed += incident == {-1, 1}
        frequencies[mixed] += 1
    require(sum(frequencies) == 27 and frequencies[2] > 0 and frequencies[3] == 0, "complete parity panel")
    panels = []
    cases = [([(0, 0, 0), (4, 8, 1), (1, 2, 7)], [4, 4, 6]),
             ([(0, 0, 0), (10, 100, 1), (1, 200, 12)], [10, 10, 11])]
    for triples, radii in cases:
        for dimension in (2, 3):
            rows = triples if dimension == 3 else [(s, t) for s, other, t in triples]
            found = []
            for anchor, row in enumerate(rows):
                scores = []
                for other_row in rows:
                    if other_row != row:
                        delta = [abs(a-b) for a,b in zip(row, other_row, strict=True)]
                        scores.append(max(min(delta[:-1]), delta[-1]))
                radius = min(scores)
                x, y = count(rows, anchor, 1)
                require(radius == radii[anchor], "radius")
                require((x, y) == [(2, 2), (2, 2), (3, 1)][anchor], "counts")
                local = harmonic(2) - harmonic(x-1) - harmonic(y-1)
                found.append(dict(radius=radius, x=x, y=y, local=str(local)))
            mean = sum(Fraction(item["local"]) for item in found) / 3
            require(mean == Fraction(-1, 3), "mean minimum")
            panels.append(dict(dimension=dimension, rows=rows, observations=found, mean=str(mean)))
    print(json.dumps(dict(sign_histogram=frequencies, cases=panels), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
