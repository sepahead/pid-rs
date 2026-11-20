"""Check the published rounded bounds with rational arithmetic and a log-series remainder."""
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

D = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("support_bound_example", D / "example.py")
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)
read_tables, summary, numbers = example.read_tables, example.summary, example.numbers

F = Fraction

def require(ok, message):
    if not ok:
        raise ValueError(message)

def add(x, y):
    return x[0] + y[0], x[1] + y[1]

def scale(k, x):
    return (k*x[0], k*x[1]) if k >= 0 else (k*x[1], k*x[0])

def log_unit(x):
    """For 1 <= x <= 2 bound ln(x) using 40 terms of the atanh series."""
    require(1 <= x <= 2, "log series domain")
    z = (x - 1) / (x + 1)
    power = z
    partial = F(0)
    for n in range(40):
        partial += 2*power / (2*n+1)
        power *= z*z
    return partial, partial + 2*power / (81*(1-z*z))

def log_interval(x):
    require(x > 0, "positive log argument")
    x, k = F(x), 0
    while x >= 2:
        x /= 2
        k += 1
    while x < 1:
        x *= 2
        k -= 1
    return add(log_unit(x), scale(k, log_unit(F(2))))

def expected_round(interval, digits):
    center = F(digits)
    half_step = F(1, 2*10**9)
    require(center-half_step < interval[0] <= interval[1] < center+half_step, "rounding enclosure " + digits)

def refused(p, q, ks, message):
    try:
        numbers(p, q, ks)
    except ValueError as exc:
        require(message in str(exc), "unexpected rejection")
        return
    raise ValueError("invalid comparison accepted")

def main():
    d = json.loads((D/"counts.json").read_text())
    p, q = read_tables(d)
    cells = ["000", "010", "100", "111"]
    require([r["cell"] for r in d["rows"]] == cells, "cell sequence")
    require([r["reference"] for r in d["rows"]] == [50]*4 and
            [r["changed"] for r in d["rows"]] == [1,99,50,50], "fixed count data")
    require(d["support_bounds"] == [4,16], "two specified upper bounds")
    s, t, p_min, e = summary(p, q)
    require(s == t == set(cells) and p_min == F(1,4) and e == F(49,200), "fixed distances")
    require(all(int(c[2]) == (int(c[0]) & int(c[1])) for c in s), "AND truth table")
    require(all(p[c] == F(1,4) for c in s), "independent reference bits")
    require(min(q[c] for c in t) == F(1,200), "changed minimum")
    local = add(add(log_interval(50), (-e,-e)), scale(2*e, log_interval(4)))
    def global_interval(k):
        return scale(e, add(add((F(12),F(12)), log_interval(k*k//4)),
                            scale(2,log_interval(1/e))))
    b4, b16 = global_interval(4), global_interval(16)
    require(b4[1] < local[0] and local[1] < b16[0], "two strict comparisons")
    expected_round(b4, "3.968825682")
    expected_round(local, "4.346307242")
    expected_round(b16, "4.648109919")
    decimal_local, decimal_global = numbers(p, q, [4, 16])
    for value, interval in ((decimal_global[4], b4), (decimal_local, local), (decimal_global[16], b16)):
        require(interval[0] <= F(value) <= interval[1], "decimal result outside the rational enclosure")
    require(numbers(p,p,[4])[0] == 0, "same-sized repeat has zero movement")
    require(numbers({"000":F(1)},{"000":F(1)},[1]) == (0,{1:0}), "one-cell endpoint")
    refused(p,q,[3], "union support")
    refused(q,p,[4], "common support and TV below p_min")
    refused(p,{"000":F(1)},[4], "common support and TV below p_min")
    print("verified both orderings, three rounded results, the fixed counts and the boundary controls")

if __name__ == "__main__":
    main()
