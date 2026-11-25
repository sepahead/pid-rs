"""Exercise the typed observation and rejection rules with constructed text."""

from pathlib import Path
import runpy

checks = runpy.run_path(str(Path(__file__).with_name("observe.py")))
positive = checks["positive"]
negative = checks["false_control"]
domain = "∀ {x : ℝ}, 0 ≤ x → x < 1 → ∀ (n : ℕ), "
sum_terms = "∑ i ∈ Finset.range n, x ^ (2 * i + 1) / (2 * ↑i + 1)"
log_term = "1 / 2 * Real.log ((1 + x) / (1 - x))"
upper_tail = "x ^ (2 * n + 1) / (1 - x ^ 2)"
lower = domain + sum_terms + " ≤ " + log_term
upper = domain + log_term + " ≤ (" + sum_terms + ") + " + upper_tail
names = checks["NAMES"]
types = dict(zip(names, (lower,upper)))
terms = "".join(f"theorem {key} : {types[key]} :=\nfun h => {original} h\n"
                for key,original in names.items())
for key,original in names.items():
    for name in (key,original):
        terms += f"@{name} : {types[key]}\n"
for key in (*names,*names.values()):
    terms += f"'{key}' depends on axioms: [propext, Classical.choice, Quot.sound]\n"
wrong = "False.lean:5:2: error: Type mismatch\n  this\nhas type\n  0 < 1\nbut is expected to have type\n  1 < 0\n"
if len(positive(terms)) != 4:
    raise ValueError("constructed mathematical observations")
negative(wrong)
mutants = [
    (positive, terms.replace("Real.sum_range_le_log_div h\n", "Real.other h\n", 1)),
    (positive, terms.replace("propext","sorryAx",1)),
    (positive, terms+terms),
    (positive, terms.replace("Classical.choice, ","",1)),
    (positive, terms+"⋯\n"),
    (positive, terms.replace(lower,"Type").replace(upper,"Type")),
    (positive, terms.replace("x < 1","x ≤ 1",1)),
    (positive, terms.replace(lower,upper,1)),
    (positive, terms.replace("0 ≤ x → ","",1)),
    (positive, terms.replace("x < 1 → ","x < 1 → 0 < x → ",1)),
    (positive, terms.replace("x < 1","x ≤ 1")),
    (positive, terms.replace(upper_tail,"x ^ (2 * n + 1) / (1 + x ^ 2)")),
    (positive, terms.replace("1 + x","1 - x")),
    (positive, terms.replace("((1 + x) / (1 - x))","(1 + x / (1 - x))")),
    (positive, terms.replace("x ^ (2 * i + 1)","(x ^ 2) * i + 1")),
    (positive, terms.replace(" / (1 - x ^ 2)"," / 1 - x ^ 2")),
    (positive, terms.replace("@Real.sum_range_le_log_div :", "@Real.other :")),
    (negative, wrong.replace("Type mismatch","unknown identifier")),
    (negative, wrong.replace("1 < 0","1 ≤ 0")),
    (negative, wrong.replace("0 < 1","reversed").replace("1 < 0","0 < 1").replace("reversed","1 < 0")),
    (negative, wrong.replace("but is expected to have type", "and also contains")),
    (negative, wrong + wrong),
]
for index,(read,text) in enumerate(mutants):
    try:
        read(text)
    except ValueError:
        continue
    raise ValueError(f"mutated transcript {index+1} passed")
print(f"Two constructed transcript forms and {len(mutants)} rejected mutations. No Lean process ran in this test.")
