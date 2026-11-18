#!/usr/bin/env python3
"""Count overlapping three-bit windows for the finite-sample concentration supplement.

Each of the 2**(n+2) strings of independent fair bits is equally likely.
K counts the windows with at least two ones. Their four possible patterns
have combined probability 1/2 in the marginal distribution of one window.
The eight-cell empirical L1 distance is at least 2 * abs(K/n - 1/2).
"""

from fractions import Fraction


def majority_histogram(n: int) -> list[int]:
    """Return the number of length-n+2 strings at each count K = 0, ..., n.

    Each row of the working table is indexed by the last two bits, encoded
    as 2*a + b. Its kth entry counts prefixes with k majority windows.
    Extending a prefix by one bit creates exactly one new complete window.
    This takes O(n**2) integer additions and O(n) integer counters.
    """
    if type(n) is not int or n < 1:
        raise ValueError("n must be a positive integer")

    counts_by_suffix = [[1] for _ in range(4)]  # All two-bit prefixes, K = 0.
    for windows_so_far in range(n):
        next_counts = [[0] * (windows_so_far + 2) for _ in range(4)]
        for suffix, counts in enumerate(counts_by_suffix):
            older_bit, newer_bit = divmod(suffix, 2)
            for bit in (0, 1):
                destination = next_counts[2 * newer_bit + bit]
                increment = int(older_bit + newer_bit + bit >= 2)
                for k, count in enumerate(counts):
                    destination[k + increment] += count
        counts_by_suffix = next_counts
    return [sum(counts) for counts in zip(*counts_by_suffix)]


def iid_expression_bounds() -> tuple[Fraction, Fraction]:
    """Bound the IID expression 254 * exp(-27/2) with exact rationals."""
    x = Fraction(27, 2)
    term = partial_sum = Fraction(1)
    for k in range(1, 33):
        term *= x / k
        partial_sum += term

    # The omitted tail of exp(x) begins with term 33. Subsequent ratios
    # are at most x/34 < 1, so a geometric tail gives an upper bound.
    term_33 = term * x / 33
    upper_exp = partial_sum + term_33 / (1 - x / 34)
    return 254 / upper_exp, 254 / partial_sum


def main() -> None:
    n = 300
    histogram = majority_histogram(n)
    total = 2 ** (n + 2)
    if sum(histogram) != total or histogram != histogram[::-1]:
        raise ArithmeticError("the counts must exhaust all strings and respect bit complementation")

    lower_count = sum(histogram[:106])
    upper_count = sum(histogram[195:])
    probability = Fraction(lower_count + upper_count, total)
    lower_iid, upper_iid = iid_expression_bounds()
    print(f"strings with K <= 105: {lower_count}")
    print(f"strings with K >= 195: {upper_count}")
    print(f"total strings: {total}")
    print(f"exact probability of either tail: {probability}")
    print(f"strict lower bound on 254 exp(-27/2): {lower_iid}")
    print(f"strict upper bound on 254 exp(-27/2): {upper_iid}")
    if probability >= upper_iid:
        print("The majority-event probability exceeds the IID expression.")
    elif probability <= lower_iid:
        print("The majority-event probability is below the IID expression.")
    else:
        print("The rational bounds leave the comparison undecided.")


if __name__ == "__main__":
    main()
