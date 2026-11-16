# Finite retained SMT witness qualification

Author: **Sepehr Mahmoudian** (2026).

This project-defined command-line tool rechecks 34 historical satisfiable
witness projections from a fixed 39-case collection. It exposes exact inputs,
checker source, expected outputs and finite hostile controls. The purpose is
to make this narrow, already checked finding inspectable and reproducible.
It adds no PID estimator, UNSAT proof certificate or scientific novelty claim.

Suggested citation: Sepehr Mahmoudian (2026), *Finite retained SMT witness
qualification*. Include the exact repository commit or release. Cite the
software using [CITATION.cff](../../../CITATION.cff). This is a directly consumed
verification tool with a Markdown usage guide; it has no PDF companion.

## Definitions and exact scope

The defining project specification is the exact
[encoder source](fin3_smt.py), SHA-256
`62cd492b20b3d908d26e3838d9d648475d1ea92b9ba5c714bab5844e3a4e6eeb`,
and its 39-case roster. No defining method paper is claimed for this tool.
The source-to-repository MGW question is governed separately by
[decision record 3](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v3.md).
This finite tool does not close that question or change its decision.

The following terms and symbols use the local definitions in
[model_checker.py](model_checker.py) and [encoder source](fin3_smt.py):

| Term or symbol | Meaning and domain |
|---|---|
| SMT | Satisfiability modulo theories; a solver searches for an assignment satisfying a logical formula. |
| SAT / UNSAT | A satisfiable / unsatisfiable response. Here only the extracted SAT projections receive semantic checks; an UNSAT status is not a checked proof. |
| Source indices | Three ordered binary source coordinates indexed by 0, 1 and 2, plus a distinct binary target. |
| Cell, key | An integer from 0 through 15 encoding the four binary coordinates; `k` is the selected key and `r` a comparison cell. |
| Branch, family | A nonempty subset of the three source indices, or a set of branches. There are seven branches; a seven-bit code represents a family. |
| Valid antichain | A nonempty family in which no two branches contain one another. The derived carrier has 18 members. |
| `w_i` | Integer weight at cell `i`, for indices 0 through 15. These are symbolic assignments, not measured observations. |
| `E(a,k)` | Cells matching key `k` on every source in at least one branch of family `a`: AND within a branch, OR across branches. |
| `U`, `V`, `N` | Source-event weight, source-event-and-target weight, and total table weight, defined below. These have count units when weights are counts. |
| Zeta / inverse | The 18 by 18 integer incidence matrix for the declared order and its exact two-sided inverse. These matrices are dimensionless. |

The raw cell encoding is `8*s0 + 4*s1 + 2*s2 + t`; source-subset mask bit
positions use source indices 0, 1 and 2. For a family `a` and key `k`, the
checker recomputes

```text
N = sum of w_i over all 16 cells
U = sum of w_i over cells in E(a,k)
V = sum of w_i over cells in E(a,k) with target equal to key k's target
```

For example, let `a=64` encode the single branch containing all three sources,
let `k=0`, and set `w_0=w_1=1` with all other weights zero. Both occupied
cells have sources `000`; only cell 0 has key 0's target. Then `U=2`, `V=1`
and `N=2`. This is a two-cell synthetic count table, not a population model
or a calibration experiment.

Nonnegative count weights and a positive supported key are premises of W14.
The C01 and M04–M09 SAT fixtures bind equality pattern, target equality and
one or two unit-weight cells. Other cases do not acquire those premises:
negative integer weights remain legal where the original formula allows them.
No logarithm, probability law, information unit or estimated quantity is
computed by these commands. Normalizing a valid count table would be a
separate interpretation; the commands do not fit, train, hold out or resample.

## Finding and evidence boundary

The original capture has 39 cases in each of two solver formats: 78 historical
status observations, comprising 44 UNSAT and 34 SAT. The later qualification
checked each SAT projection's 25 typed declared assignments and 12 get-value
associations against its original case premises and negated predicate. The
25 assignments are `a,b,c`, `q,h,x`, `k,r`, `tau` and the 16 integer weights.

The checker independently enumerates the antichains with sets and derives
their integer inverse by exact rational Gaussian elimination, checking both
inverse products. The encoder uses an incidence recurrence. These are separate
finite algorithms under shared mathematical definitions and a trusted Python
runtime. They do not establish human independence or a formal transport theorem.

The original V2 qualification completed on 15 November 2026 at
14:59:27–14:59:28 UTC. Four Python children exited zero: controls
normal/optimized, then retained qualification normal/optimized. Each control
run observed 454 expected decisions: 85 accepts and 369 refusals. The two
control reports are byte identical; the two qualification reports are also
byte identical. Exact original outputs are included in [reports](reports).
The selected historical facts and private-receipt commitments are recorded in
[RESULT_PROJECTION.json](RESULT_PROJECTION.json).
Its private-candidate and not-executed-during-preparation labels describe the
earlier preparation of that projection and remain unchanged historical bytes.
They do not describe the later portable execution recorded below.

The 44 UNSAT answers remain historical trusted solver observations without
independently checked proof certificates. Known Z3 helper names and sorts are
checked, but their bodies remain opaque. The checked object is the extracted
declared-variable projection and query consistency, not every auxiliary model
interpretation. [Source lineage](SOURCE_LINEAGE.json) distinguishes original
byte copies from the selected metadata and later portable adapter.

No fresh solver, generator or Lean proof run is represented. No original
256-family Finset transport, full B–L bridge, original 4.33 specification or
12 pre-candidate semantic-control matrix, H1 custody, Program A–E closure,
probability/logarithm argument, Rust behavior, calibration, application value
or global scientific hold change follows. The original positive Finset replay
remains separate. All five SxPID3 Programs A–E remain open.

## Recheck the exposed collection

Use Python 3.9 or later with its standard library. From this directory run:

```text
python3 -I -S -B controls.py --manifest
python3 -I -S -B controls.py model_checker.py
python3 -O -I -S -B controls.py model_checker.py
python3 -I -S -B qualify.py
python3 -O -I -S -B qualify.py
python3 -I -S -B adapter_self_test.py
python3 -O -I -S -B adapter_self_test.py
```

The first output must equal [PAYLOADS.json](PAYLOADS.json) byte for byte. The
control outputs must equal their saved reports. The reader requires equality
with both original 34-projection reports after calling the unchanged checker.
It rejects duplicate JSON keys and compares acceptance-bearing records by
recursive shape, exact type and value; `false`, `0` and `0.0` are distinct.
The adapter suite has 3 positive and 35 refusal controls, including in-memory
hash-rebound metadata and stream mutations. It never changes package files.

The later portable adapter validation passed on 15 November 2026 at
23:12:36–23:12:41 UTC under CPython 3.15.0 on macOS arm64. All seven commands
exited zero with empty standard error; all normal/optimized output pairs were
byte identical. The manifest, original control and retained-projection outputs
matched the saved bytes. Each adapter run observed all 38 expected decisions.
[PORTABLE_VALIDATION.json](PORTABLE_VALIDATION.json) records the exact commands,
output identities, limits and selected original execution facts. This is a
separate execution from the original qualification.

Rechecking exposed fixtures supplies development/reproduction evidence,
without blind or pre-candidate credit. Any unexpected decision, exception,
type, stream, source or output mismatch is a failure. Preserve it and revise
the task before another attempt; do not loosen predicates or relabel the
historical finding.

## Rust implementation and computational cost

This is offline verification tooling in Python, not a runtime estimator or
learner. It has no public Rust API or feature gate and establishes no
Rust/Python binding, binary64 refinement, real-time behavior or release latency
claim. The production engineering baseline remains
[Rust implementation and cost](../../../RUST_IMPLEMENTATION_AND_COST.md).
No estimator timing is reported here. The original four-child elapsed time in
the result projection is custody information for that fixed run, not a portable
benchmark or an estimator performance measurement.

The input is 39 synthetic logical cases, 234 formula/stdout/stderr streams and
78 solver observations. Each SAT projection has fixed dimension 25 and queries
12 values. There are 16 possible cells and at most 16 occupied count cells;
`N` has no global positive, statistical or sample-size meaning outside a case's
count premises. The geometry considers the 127 nonempty families of seven
branches, retains 18 antichains, inverts an 18 by 18 matrix and checks both
products. Gaussian elimination and the two products require cubic arithmetic
work in that matrix size. Exact rational/integer arithmetic costs also depend
on operand bit lengths. No floating-point approximation is used.

The reader admits at most 65,536 bytes per formula and 1,048,576 bytes per
other file read. The checker permits at most 65,536 tokens, nesting depth 64,
atom length 256 and integer magnitude lexemes of at most 256 decimal digits
inside its 1 MiB model-stream cap. It caches one fixed geometry; parsing and
projection checks retain data in memory. The control harness also constructs
deliberately oversized refusal payloads. These are finite logical guards,
not hard RSS, OS scheduling, denial-of-service or complete-runtime bounds.

The tools write their reports to standard output and invoke no solver,
generator or subprocess. An interrupted or incomplete command supplies no
pass. Their file hashes require stable files while reading; these checks are
neither atomic filesystem snapshots nor signatures or authenticity attestations.
There is no training, inference, resampling or online deployment route to time.

## Review and retained history

[REVIEW.md](REVIEW.md) records the ten-route decision, 50 scientific/publication
lenses, actual advisory roles, shared dependencies and remaining dissent. AI
roles prepared the packaging, challenged it and inspected exact receipts; model
agreement is advisory and does not constitute independent human or institutional
scientific review. One portable campaign was submitted, with no retry. Earlier
source-only preparation and correction versions were retained without execution.
All inputs and saved outputs were already exposed.

[OBSERVATIONS.json](OBSERVATIONS.json) is an explicitly selected projection,
not an original capture receipt. [fin3_smt.py](fin3_smt.py),
[model_checker.py](model_checker.py), [PLAN_V2.json](PLAN_V2.json),
[PAYLOADS.json](PAYLOADS.json), the raw streams and original reports retain their
original bytes. Three storage-adapter lines in [controls.py](controls.py) change
only where public data are read. The original unchecked capture summary label
remains historical. Original private custody records and the prospective
pre-repair adapter remain preserved separately; none is overwritten by this
publication. [MANIFEST.json](MANIFEST.json) binds every other package file under
its stated self-exclusion rule. Hashes provide binding, not recovery of omitted
private records or independent authenticity.
