"""Compute the count-cleared informative difference from a categorical contingency table."""
from collections import Counter
from fractions import Fraction

def from_cells(coarse, fine):
    if len(coarse) != len(fine) or not coarse:
        raise ValueError("aligned nonempty unit observations required")
    coarse_count = Counter(coarse)
    fine_count = Counter(fine)
    cells = Counter(zip(coarse, fine, strict=True))
    value = Fraction(1)
    for (left, right), count in cells.items():
        gained = fine_count[right] - count
        value *= Fraction(coarse_count[left] + gained, coarse_count[left]) ** count
    return value
