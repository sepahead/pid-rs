# Decision for SX-COUNT-EVENT-BRIDGE-001 revision 2

## Adjudication

Decision: **complete within the bounded supplied-count formal-semantics scope**.

The accepted result starts from an arbitrary natural-valued count function on the complete finite
heterogeneous two-source key space, requires positive total count, restricts logarithms and
averaging to positive count support, and proves the exact count expression for each of the four
fixed two-source signed-net cumulative averages. Revision 1 is retained and superseded because its
prose incorrectly suggested that every complete key had positive count.

## Formal basis

- `TwoSourceCountEventBridge.lean` contains 38 ordered declarations, including 24 theorems.
- At this count/event revision-2 closure snapshot, the pinned project inventory was 263
  declarations and 201 named source theorems across seven imported modules. The complete
  two-source bridge source is separately SHA-256 bound.
- Every named source theorem is checked through `collectAxioms` against the permitted basis
  `propext`, `Classical.choice`, and `Quot.sound`.
- The SHA-256-bound semantic contract contains 16 compiled examples and fixes nonnegativity, the
  asymmetric counts
  `[1,2,3,4,5,8,6,7]`, event counts, and four distinct rational arguments
  `[24/25,9/10,4/5,108/115]`. These examples are not individually passed through `collectAxioms`.
- Ten static gate mutations, including a same-name valid-theorem weakening, and five baseline-first
  isolated Lean semantic mutations fail under normal and optimized Python.
- Executable Lean source rejects `native_decide`; finite closed examples use kernel `decide`.

The snapshot totals above are not the current aggregate finite-convergence totals. The separately
cataloged categorical-only atom successor now brings that aggregate to 339 declarations, 246 named
source theorems, eight imported modules, and 71 registered changes; see
`SX-COUNT-ATOM-BRIDGE-001` revision 2. That successor does not retroactively widen this decision.

## Repository-wide binding

The bounded result is bound into the method catalog and generated method view, assurance registry,
review-evidence inventory, root and crate documentation, formal and limitations documents,
changelog, and the finite-alphabet, dependency-colored, support-change, and formal-tool-adoption
LaTeX/PDF artifacts. Those documents use the same boundary: supplied exact counts and two-source
signed-net cumulative mathematics only.

## Residual decision

The following remain explicitly open and are not prerequisites silently treated as proved:

- bytes, rows, JSON, or another representation to the exact count function;
- Rust sorting and histogram extraction to counts;
- Rust `NODES2`, `invert2`, concrete atom order, or result-field refinement;
- complete informative/misinformative averaged components or concrete Möbius atoms;
- binary64, MPFR, Python, compiler, runtime, standalone-certifier, parser, overflow, allocation,
  cancellation, or resource semantics;
- canonical exact-expression serialization or rational-product comparison;
- more than two sources; and
- sampling, concentration, population, calibration, priority, release, or consumer validity.

The decision therefore supplies no end-to-end executable-verification, estimator-validation,
scientific-priority, attestation, or downstream-authority claim.

## Replay gates

```text
python3 scripts/check-lean-finite-convergence.py
python3 scripts/check-lean-finite-convergence-self-test.py
python3 -O scripts/check-lean-finite-convergence-self-test.py
python3 scripts/check-method-catalog.py
python3 scripts/check-review-evidence.py
scripts/check-finite-alphabet-convergence-pdf.sh
scripts/check-dependency-colored-sxpid-pdf.sh
scripts/check-support-change-tolerant-sxpid-pdf.sh
scripts/check-formal-tool-adoption-pdf.sh
```

These gates are replayable repository evidence. They are not independent human review.
