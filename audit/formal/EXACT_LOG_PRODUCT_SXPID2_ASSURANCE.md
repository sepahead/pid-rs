# Exact multiplicative certificates for empirical categorical SxPID2

## Status and claim boundary

This note adds an exact arithmetic assurance route for the two-source empirical categorical
shared-exclusions PID of Makkeh, Gutknecht, and Wibral. It does not define a new PID and does not
import axioms, atoms, or desired properties from another PID proposal.

The route is representation-agnostic only in a narrow algebraic sense: after the
Makkeh--Gutknecht--Wibral source-event unions, target-restricted events, empirical averaging rule,
and integer Möbius transform are fixed, the same finite log expression can be normalized into one
positive rational product. The route is not representation-agnostic across PID definitions. If
the event logic, lattice, or cumulative is changed, it certifies a different object.

The result removes transcendental approximation from exact **zero and sign** decisions for the
fixed empirical count table. It does not by itself enclose the nonzero logarithmic magnitude. The
existing directed-rounding certifier supplies that separate value enclosure.

Artifact set: [this Markdown note](EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md),
[self-contained LaTeX](latex/exact-log-product-sxpid2-assurance.tex), and
[rendered PDF](../../output/pdf/exact-log-product-sxpid2-assurance.pdf). The deterministic PDF
checker rejects build warnings, layout diagnostics, stale bytes, changed extracted text or page
geometry, and non-embedded fonts.

## Definitions and hypotheses

Let $Z_+$ be the finite set of distinct observed complete states
$z=(s_1,s_2,t)$. Each state has an integer count $c_z>0$, and

$$
 n=\sum_{z\in Z_+}c_z>0.
$$

For a fixed SxPID lattice node $\alpha$ and keyed state $z$, define integer counts

$$
 a_{z,\alpha}=\#A_{z,\alpha},\qquad
 b_{z,\alpha}=\#(A_{z,\alpha}\cap\{T=t_z\}),\qquad
 t_z=\#\{T=t_z\}.
$$

Here $A_{z,\alpha}$ is exactly the disjunction of source-collection events in the reviewed
repository transcription of the published shared-exclusions construction. Every defining event
contains its keyed observed state. Hence

$$
 0<c_z\le b_{z,\alpha}\le a_{z,\alpha}\le n,
 \qquad b_{z,\alpha}\le t_z\le n.
$$

The three pointwise cumulative components, in nats, are

$$
 i^+_{z,\alpha}=\log\frac{n}{a_{z,\alpha}},
 \qquad
 i^-_{z,\alpha}=\log\frac{t_z}{b_{z,\alpha}},
$$

and

$$
 i^{\mathrm{sx}}_{z,\alpha}
 =i^+_{z,\alpha}-i^-_{z,\alpha}
 =\log\frac{n b_{z,\alpha}}{a_{z,\alpha}t_z}.
$$

The empirical cumulative is the exact count-weighted average

$$
 C^u_\alpha=\sum_{z\in Z_+}\frac{c_z}{n}i^u_{z,\alpha},
 \qquad u\in\{+, -, \mathrm{sx}\}.
$$

The hypotheses are therefore:

1. The complete categorical states are finite and coalesced into unique rows with positive
   integer counts.
2. The event definition is the published keyed SxPID source disjunction, with its keyed target
   intersection.
3. The empirical probabilities are exact count ratios and the average uses $c_z/n$. No
   smoothing, fractional pseudo-count, or alternative weighting rule is silently inserted.
4. The lattice is finite and its atom-from-cumulative Möbius coefficients are integers.
5. The logarithm is applied only to positive rational arguments. The implementation reports nats.

The product reduction extends to rational weights after clearing a declared common denominator,
but that extension is not used by the current checker.

## Exact product theorem

Define

$$
 R^+_\alpha
 =\prod_{z\in Z_+}\left(\frac{n}{a_{z,\alpha}}\right)^{c_z},
$$

$$
 R^-_\alpha
 =\prod_{z\in Z_+}\left(\frac{t_z}{b_{z,\alpha}}\right)^{c_z},
$$

and

$$
 R^{\mathrm{sx}}_\alpha
 =\prod_{z\in Z_+}
 \left(\frac{n b_{z,\alpha}}{a_{z,\alpha}t_z}\right)^{c_z}.
$$

All three are positive exact rationals. The logarithm product rule and integer power rule give

$$
 C^u_\alpha=\frac{1}{n}\log R^u_\alpha.
$$

The local identity also gives the exact multiplicative component identity

$$
 R^{\mathrm{sx}}_\alpha=\frac{R^+_\alpha}{R^-_\alpha}.
$$

Let $M_{\gamma\alpha}\in\mathbb Z$ be the fixed Möbius row that constructs atom
$\gamma$. Define

$$
 R^u_\gamma=\prod_\alpha (R^u_\alpha)^{M_{\gamma\alpha}}.
$$

Negative Möbius coefficients mean exact rational reciprocals. Linearity of logarithms gives

$$
 \Pi^u_\gamma
 =\sum_\alpha M_{\gamma\alpha}C^u_\alpha
 =\frac{1}{n}\log R^u_\gamma.
$$

Because $n>0$ and $R>0$, every cumulative and atom obeys

$$
 \frac{1}{n}\log R=0\iff R=1,
$$

$$
 \frac{1}{n}\log R>0\iff R>1,
 \qquad
 \frac{1}{n}\log R<0\iff R<1.
$$

Thus integer numerator-versus-denominator comparison is a complete exact zero/sign decision for
the fixed empirical coordinate. It does not call `log`.

The same conclusion can be read directly from the certifier's canonical log-linear expression.
Every emitted coefficient $q$ satisfies $nq\in\mathbb Z$, so

$$
 R=\prod_j x_j^{nq_j}.
$$

The implementation-separated, repository-local checker reconstructs $R$ from event counts and
separately reconstructs it from the emitted terms. Equality binds the two representations; shared
repository authorship and specifications prevent this route from claiming independent review.

## Retained counterexample to empty-term-only zero certification

The first implementation treated an empty canonical term map as the only exact-zero witness. That
condition is sufficient but not complete: logarithms with different rational arguments can cancel
multiplicatively even after equal arguments and zero coefficients have been combined.

The smallest binary-table counterexample found by exhaustive total-count search uses canonical
state order

$$
(0,0,0),(0,0,1),(0,1,0),(0,1,1),(1,0,0),(1,0,1),(1,1,0),(1,1,1)
$$

and counts

$$
(0,0,1,1,1,4,1,0),\qquad n=8.
$$

For the net `unique_one` atom, the canonical expression is nonempty:

$$
E=-\frac18\log\frac8{15}
  +\frac18\log\frac45
  +\frac18\log\frac89
  +\frac18\log\frac43
  -\frac18\log\frac{16}{9}.
$$

Nevertheless its denominator-cleared product is exactly

$$
R=\left(\frac8{15}\right)^{-1}
  \left(\frac45\right)
  \left(\frac89\right)
  \left(\frac43\right)
  \left(\frac{16}{9}\right)^{-1}
 =\frac{15}{8}\frac45\frac89\frac43\frac9{16}=1,
$$

so $E=\frac18\log R=0$. At 256 working bits, the directed interval is

$$
[-3\,2^{-258},\;5\,2^{-259}],
$$

which correctly contains zero but does not resolve its sign. The repaired report therefore keeps
the interval-local decision `unresolved_sign` and its interval zero witness empty, while a separate
exact-product record reports `certified_exact_zero` with witness
`exact_multiplicative_product_equals_one`. Claiming that the interval itself resolved zero would
be false; refusing the exact product-one proof would be incomplete.

Exhausting all 12,869 nonzero binary tables with total count at most eight, comprising 308,856
coordinates, finds no such cancellation below total eight and exactly 16 at total eight. All 16
have support size five and are net unique atoms. Thus total eight and support five are minimal only
within this explicitly exhausted binary domain, not universally over other alphabets or PID
definitions.

## Bounded executable exact-product route

The Rust certifier now performs a two-stage operation. It first verifies $nq_j\in\mathbb Z$ and
computes, without exponentiation, the conservative projection

$$
B=\sum_j |nq_j|\left(
  \mathrm{bits}(\mathrm{num}x_j)
 +\mathrm{bits}(\mathrm{den}x_j)
\right).
$$

It admits exact powering only when one expression has at most 256 terms, every absolute cleared
exponent is at most 16,384, $B\le262{,}144$, and the admitted-coordinate aggregate projection is
at most $1{,}048{,}576$. These ceilings are far smaller than permission to exponentiate the
parser's 8,192-bit total count. A failed preflight records an unavailable exact-product decision
and falls back to the still-valid directed interval; it does not allocate a huge power and does not
turn absence of exact comparison into a sign claim. No prime-factorization claim is made.

The separate repository-local report-term checker follows the same plan/evaluate split: it parses bounded
rationals and computes every local projection plus the aggregate admission decision before calling
its rational-power primitive. Two sentinel controls replace that primitive with a function that
fails on any call, then exercise a locally rejected plan and an aggregate-rejected plan. Both
guards reject with zero power calls. This is executable ordering evidence, not a formal time or
space bound for Python or Rust.

## Five-lens audit

### Lens 1: SxPID definitional compatibility

The checker scans the complete-state count table for each of the four two-source nodes:

- $\{S_1\}$,
- $\{S_2\}$,
- $\{S_1,S_2\}$, and
- the redundancy disjunction $\{S_1\}\lor\{S_2\}$.

It repeats each scan with the keyed target restriction. It does not substitute intersection for
the redundancy disjunction. The atom order and integer two-source Möbius matrix are fixed to the
shared-exclusions lattice. The first three net cumulatives are also reconstructed separately as
ordinary empirical mutual-information products to challenge the self-redundancy identity.

This lens establishes compatibility with the encoded Makkeh--Gutknecht--Wibral definition. It does
not prove that shared exclusions is the unique or universally preferred PID measure. In
particular, exact arithmetic does not resolve known differences between SxPID and desiderata such
as the identity axiom on the independent two-bit copy, nor does it settle general multivariate
lattice-consistency questions.

### Lens 2: proof assumptions and formal algebra

The proof needs finiteness, positive exact arguments, positive integer $n$, empirical integer
multiplicities, and integer Möbius coefficients. Support outside the observed empirical table is
irrelevant to this arithmetic identity but remains essential for population inference.

`audit/formal/lean-exact-log-product/PidExactLogProduct.lean` kernel-checks the generic reduction,
sign equivalences, cross-argument cancellation, and the retained witness product:

1. `log` of a finite signed-power product is the corresponding integer log sum;
2. scaling gives the $\log R/n$ representation;
3. exact positivity is equivalent to $R>1$;
4. exact negativity is equivalent to $R<1$; and
5. exact zero is equivalent to $R=1$; and
6. $\log x+\log(x^{-1})=0$ for positive $x$, exhibiting a nonempty cancellation; and
7. the five rational factors in the retained total-count-eight witness multiply exactly to one.

The permitted Lean axiom basis is only `propext`, `Classical.choice`, and `Quot.sound`. The Lean
file intentionally does not formalize concrete SxPID events or the concrete Möbius matrix. The
five-factor theorem checks exact witness arithmetic, while implementation-separated exact-rational
and Rust routes bind those factors to the SxPID2 unique-one net atom. That concrete binding is not a
consequence of the generic theorem.

The current kernel-check receipt is the versioned
[`sxpid2-exact-product-lean-check-4.33.0.json`](../evidence/sxpid2-exact-product-lean-check-4.33.0.json),
which binds the portable Lean 4.33.0 release identity, current manifest, checker, source, theorem
count, and axiom boundary. The unversioned
[`sxpid2-exact-product-lean-check.json`](../evidence/sxpid2-exact-product-lean-check.json) is retained
byte-for-byte as historical Lean 4.32 evidence. It is not regenerated, compared to the current
checker as if contemporary, or credited as the current execution route.

#### Checker qualification, terms, and provenance

Here, the **production checker** is the fixed Python program
`scripts/check-lean-exact-log-product.py`, SHA-256
`52510a18ac5fa8b94113bfeba84f61cb28bdbe56be278fc76fb4d55407cb2dcd`. It first requires the
exact 5,357-byte Lean source at SHA-256
`f0727ea3061d561ba89ba49edebece971ce03bdecf03e0c32774a1c080dc07bf`. It rejects the raw word
tokens `sorry`, `admit`, `axiom`, and `unsafe`. It then invokes the pinned Lean 4.33.0 release,
compiles the source plus seven `#print axioms` queries, and requires the exact permitted-axiom line
for every named theorem. A **hostile mutation** is one deliberate change to a temporary copy. A
**test-only digest rebind** replaces the checker's expected source digest inside the self-test
process so that a changed file can reach the later policy or kernel check. Production CI never
rebinds that digest. A **negative control** is a deliberately bad input that must be rejected. A
**positive control** is a deliberately valid input that must be accepted. A **scope probe** is an
accepted input used to show what the named audit does not inspect. An accepted **known limitation**
receives no positive-proof or mutation-kill credit.

#### Exact objects and threat model

The qualification keeps the following objects separate:

1. The **Lean theorem source** states the seven generic results. It is the mathematical object sent
   to Lean; it does not contain the concrete SxPID event extractor.
2. The **production checker** is the unchanged Python gate. It binds the theorem-source digest,
   pinned project files, seven qualified theorem names, and permitted axiom list, then runs Lean.
3. The **pinned Lean project** consists of `lean-toolchain`, `lakefile.toml`, and
   `lake-manifest.json`. Together they select Lean 4.33.0 and the reviewed package closure; their
   hashes do not prove that an executable was built from reviewed source.
4. The **query file** is a temporary concatenation of the theorem source and seven
   `#print axioms` commands. Lean compiles it; it is not retained as a new theorem source.
5. The **production receipt** is the canonical JSON output of one successful checker run. It
   records exact identities and the proof boundary, but it is evidence of that execution rather
   than an authenticity certificate.
6. A **mutant** is one temporary source copy with one declared change. Each mutant has its own
   digest. A mutant result applies only to that change and does not represent all possible faults.
7. The **hostile self-test** is a separate Python harness that loads the production checker from
   captured bytes, performs the mutants and probes, restores changed globals, and emits one
   canonical case record. It is not a replacement checker.
8. The **hostile evidence JSON** is the byte-for-byte output of normal and optimized hostile runs.
   It records status, counts, mutant digests, scope probes, and the limitation; it does not add a
   theorem.
9. The **archive adjudication memo** preserves the rejected checker design and counterexample. It
   is negative engineering evidence and has no production authority.

The threat model addresses accidental drift and bounded ordinary-process interference: stale or
changed checker/source bytes, symbolic-link or extra-hard-link leaves, parent replacement during a
captured read, mid-read byte or metadata changes, ambient Python packages and bytecode writes,
optimization-sensitive controls, ambiguous JSON, merged output streams, leaked test mutations,
semantic theorem changes, missing theorem names, and added axiom dependencies. The character-literal
witness specifically challenges the discarded partial lexer. Extra-declaration probes challenge the
scope of the seven-name query.

The threat model does **not** claim protection against a privileged or same-user adversary that can
coordinate changes between bounded observations, forge the Python/Lean operating environment,
subvert the kernel, compiler, dynamic loader, filesystem, SHA-256 implementation, or hardware, or
replace absent history. SHA-256 supplies exact byte equality to a reviewed value, not origin,
authorship, trusted time, or authenticity. The self-created mutant files live in a private temporary
directory and assume no concurrent writer; the stable captured-read protocol applies to the tracked
checker, tracked theorem source, and the hostile harness itself. These are endpoint checks, not an
atomic filesystem snapshot or sandbox.

The replacement hostile suite is project-defined engineering evidence. It was added after review
of the discarded archive commit `6077443`. That draft tried to remove Lean comments and strings
with a handwritten scanner. The scanner did not model character literals. Two quote-valued `Char`
literals around an empty string made a later live, unqueried `axiom` invisible to it. The complete
5,492-byte witness has SHA-256
`891323ef49a0a9e2bf8f4306de1301301aa961886121329dcf9b11847d823e03`. The draft also failed to
inventory an added `lemma` and an added `private theorem`. Therefore, the draft checker was rejected
and the current production checker remains byte-identical. The failure does not change any Lean
theorem.

The hostile result assumes: Python 3.11 or newer with exactly `-I -S -B` and either no optimization
or one `-O`; the named checker and Lean source bytes; the pinned Lake manifest and Lean release;
ordinary stability of the checked filesystem objects during each bounded read; the correctness of
Python, Lean, Mathlib, SHA-256, the operating system, and the hardware; and the exact seven-name
query inventory. The loader rejects symbolic-link or multiply linked checker/source leaves,
double-reads each file through one no-follow descriptor, checks parent and file identities, compiles
the captured checker bytes, separates standard output from standard error, requires canonical JSON,
restores every changed checker global in `finally`, and rechecks the tracked bytes after all cases.
These controls reduce the trusted surface; they do not remove it.

#### Byte and process controls, step by step

| Step | Control | Why it is required and what it does not establish |
|---:|---|---|
| 1 | Require Python 3.11 or newer, `-I -S -B`, and optimization level zero or one. | This excludes ambient site packages, ignores Python environment settings, uses a safe import path, prevents bytecode-cache writes, and makes the normal/optimized routes explicit. It does not authenticate the interpreter. |
| 2 | Resolve the expected checker, theorem-source, and self-test paths from the harness location. | This removes dependence on the caller's working directory. It does not make path resolution atomic. |
| 3 | `lstat` every lexical parent before a captured read and require directories, not symbolic links. | This detects the tested parent substitution and symlink routes. It cannot prevent a coordinated replacement outside the observation window. |
| 4 | `lstat` the leaf and require one regular, non-symbolic, single-linked file. | This rejects leaf symlinks, devices, directories, and multiply linked aliases. One link is not an authenticity claim. |
| 5 | Open the leaf read-only with `O_NOFOLLOW` when the platform supplies it, plus close-on-exec. | This narrows a link-swap route and prevents descriptor inheritance. The operating system remains trusted. |
| 6 | Compare descriptor and path metadata—device, inode, mode, link count, size, modification time, and change time—before, during, and after the read. | This detects the bounded metadata changes represented by those fields. It is not a transaction and cannot observe every storage-layer event. |
| 7 | Read the same descriptor to end twice, seek back between reads, and require equal bytes and declared length. | This catches ordinary mid-read byte drift and truncation. Equal repeated reads do not establish provenance. |
| 8 | Recheck all parent identities after the read. | This closes the bounded parent endpoint comparison. It does not continuously monitor the directory tree. |
| 9 | Compute SHA-256 over the captured bytes and require the reviewed checker/source digest. | This binds exact bytes. It does not authenticate who reviewed or produced them. |
| 10 | Compile and execute the captured checker byte string, not a second path read, under a digest-derived private module name. | This keeps the checked and executed checker representation equal. Python compilation and execution remain trusted. |
| 11 | Run every source mutation in a private temporary directory and rebind only the in-process expected source digest. | This lets a mutant reach the intended later policy, kernel, or axiom check. The rebind is test machinery, is not exposed by production CI, and gives the mutant no production authority. |
| 12 | Capture standard output and standard error separately; require exact status, empty unexpected stream, and expected rejection fragment. | This prevents a crash or unrelated rejection from being counted as the intended result. A matching fragment is bounded diagnostic evidence, not a proof of all internal execution steps. |
| 13 | Parse accepted output with duplicate-key and nonfinite-value rejection, require one final LF, no carriage return, exact compact sorted JSON reserialization, the closed ten-key production inventory, and the expected value/type of every field. | This removes ambiguous evidence encodings, rejects silent field addition or omission, and normalizes parity comparison. It does not prove the values true. |
| 14 | Restore source path, expected digest, and theorem tuple in `finally` after every call, including exceptions. | This prevents one case from contaminating the next. The postcondition checks restoration; it is not concurrency isolation. |
| 15 | Re-read the tracked checker and theorem source, capture the hostile harness's own digest, require the complete canonical run record to equal the stable tracked evidence bytes, remove the private loaded module, and compare normal with optimized output. | This detects tracked-byte drift during replay, binds the harness version and evidence relation, and challenges optimization dependence. It does not supply an independent checker implementation. |

#### Step-by-step hostile cases

The 19 cases below are disjoint for total accounting. “Kernel rejection” means that the changed
temporary source reached Lean after its test-only digest rebind and did not compile. “Policy
rejection” means that the production raw-token rule rejected the source before Lean. “Digest
rejection” means that the unchanged production digest rejected extra bytes before Lean.

| Class | Case and exact change | Reason for the case | Required and observed result |
|---|---|---|---|
| Baseline positive | Run the exact tracked source and seven-name inventory. | Establish that the real gate is runnable before interpreting failures. | Accepted; seven theorem queries and the exact axiom inventory were reported. |
| Semantic negative 1 | Replace `Real.log_zpow` by `Real.log_pow` in the signed-power normalization. | The exponent is an integer, so the natural-power lemma is not a valid substitute. | Kernel rejection. |
| Semantic negative 2 | Reverse $1<R$ to $R<1$ in the positive-sign equivalence. | A positive scaled logarithm must correspond to a product above one. | Kernel rejection. |
| Semantic negative 3 | Reverse $R<1$ to $1<R$ in the negative-sign equivalence. | A negative scaled logarithm must correspond to a product below one. | Kernel rejection. |
| Semantic negative 4 | Use the impossible $R=-1$ branch where the proof needs $R=1$. | Positivity excludes $-1$; confusing the two destroys the zero proof. | Kernel rejection. |
| Semantic negative 5 | Change reciprocal cancellation from equality to inequality. | For $x>0$, $\log x+\log(x^{-1})=0$ exactly. | Kernel rejection. |
| Semantic negative 6 | Change the retained five-factor rational product from $1$ to $2$. | The witness arithmetic must be exact, not approximate. | Kernel rejection. |
| Semantic negative 7 | Remove the premise $0<R$ from the zero-sign theorem. | The real logarithm zero equivalence needs a positive argument. | Kernel rejection. |
| Semantic negative 8 | Rename one of the seven queried theorems. | The query must fail if a required qualified name disappears. | Kernel rejection. |
| Semantic negative 9 | Make the retained theorem depend on `sorryAx`. | A compiling declaration with an extra axiom must not satisfy the permitted basis. | Compiled, then rejected by the exact axiom-inventory comparison. |
| Raw negative 1 | Replace the retained proof by `sorry`. | A direct proof escape must fail before compilation evidence is credited. | Policy rejection. |
| Raw negative 2 | Change the retained theorem declaration to `axiom`. | A declaration without proof must not be credited. | Policy rejection. |
| Raw negative 3 | Insert two quote-valued `Char` definitions, an empty string, and a live unqueried `axiom`. | This is the concrete counterexample to the discarded handwritten masker. | Policy rejection. |
| Digest negative 1 | Add an unrelated `lemma` without rebinding the source digest. | Extra source must not enter the production gate silently. | Digest rejection. |
| Digest negative 2 | Add an unrelated `private theorem` without rebinding the source digest. | Declaration modifiers must not bypass immutable source custody. | Digest rejection. |
| Raw negative 4 | Put proof-escape words only in a nested comment and a string. | This records the conservative raw policy; it does not pretend those words are live Lean commands. | Policy rejection. |
| Scope positive 1 | Re-run the extra `lemma` after a deliberate test-only digest rebind. | Show that the seven-name axiom query does not enumerate unrelated declarations. | Accepted with seven queried theorems; recorded as scope, not a kill. |
| Scope positive 2 | Re-run the extra `private theorem` after a deliberate test-only digest rebind. | Show the same boundary for a modified declaration form. | Accepted with seven queried theorems; recorded as scope, not a kill. |
| Known limitation | Shorten the in-memory theorem tuple from seven names to six while retaining exact source bytes. | Test whether the checker internally authenticates its mutable query tuple. | Accepted with six queries; recorded as a checker-custody limitation and given zero proof credit. |

Thus, the suite reports one baseline, nine rejected semantic mutations, six rejected raw/digest
controls, two accepted scope probes, and one accepted limitation: 19 cases in total. The three
positive acceptances are the baseline and the two scope probes. The accepted limitation is counted
separately. It is not silently converted into positive evidence. Two additional controls show that
the reviewed macOS/Arm64 and Ubuntu/x86-64 version strings map to the same validated portable Lean
identity: version 4.33.0, commit `d8b18978322de05a8f3dba51ef03cf5461676c17`, and a `Release`
build. The raw target triple remains in each live checker output and log. It is not stored as proof
identity and does not establish cross-platform kernel equivalence. Normal and optimized runs emit
the same canonical 5,808-byte JSON record, SHA-256
`01e6e00f72a1ae75aa9f31e148b5685d38b2d82b2477aa8bc55ccfa333ebf84c`.

The production checker proves only this conditional statement about the fixed files and toolchain:
Lean accepted the seven named declarations, and each queried declaration reported exactly the three
permitted axioms. The generic mathematics in those declarations can then be read from their stated
premises. The hostile suite adds bounded sensitivity to the named changes and makes two scope
boundaries and one custody limitation observable. Neither artifact proves that the Python checker
is correct, that the raw scan is a complete Lean lexer, that every declaration was queried, or that
all possible proof faults are rejected. They do not formalize concrete SxPID event extraction, the
Möbius lattice, canonical certificate bytes, Rust or binary64 refinement, resource correctness,
sampling, estimation, calibration, population validity, or an application. The exact case record is
[`sxpid2-exact-log-product-hostile-4.33.0.json`](../evidence/sxpid2-exact-log-product-hostile-4.33.0.json),
and the rejected route and alternatives are retained in
[`lean-exact-log-checker-adjudication-v1.md`](../../claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/lean-exact-log-checker-adjudication-v1.md).

#### Verification procedure and interpretation

The verification sequence is ordered so later evidence is not interpreted when an earlier
prerequisite fails:

1. Run the production checker with `python3 -I -S -B`. Acceptance means that the exact tracked
   source and pinned project passed the seven Lean queries. A failure stops the route.
2. Run the same checker with one `-O` and compare the complete canonical output byte for byte. This
   challenges optimization-sensitive behavior; equality does not create an independent
   implementation.
3. Run the hostile suite with `python3 -I -S -B`. Require exactly the 19 declared cases, their
   separate category counts, exact statuses, and the tracked post-replay bytes.
4. Repeat the hostile suite with one `-O` and compare its 5,808-byte canonical output byte for byte.
   Each run itself requires the stable tracked evidence JSON to equal that output; copying an older
   or differently formatted record is also rejected by the source-state and claim gates.
5. Run the certified-SxPID claim checker and its self-test in normal and optimized isolated modes.
   These gates bind the live command container, exact assurance MD/TeX/PDF bytes, method-catalog
   projection, and retained claim authorities. They do not upgrade the generic Lean theorem into a
   concrete end-to-end refinement proof.
6. Rebuild the PDF with the fixed source-date epoch. The exact route requires identical bytes on the
   producing toolchain; the cross-toolchain route requires equal extracted text and page geometry,
   embedded fonts, and no rejected LaTeX diagnostics. Visual inspection of every rendered page is a
   separate human layout check, not mathematical validation.
7. Run method-catalog, software-identity, Lean-freeze, release-scope, and current-source-state gates.
   They check repository consistency and preserve the historical r14 replay without retroactively
   inserting this post-r14 evidence. They do not authenticate Git history or prove the theorem.

Only the baseline and two declared scope probes are positive acceptances. The nine semantic and six
raw/digest cases are negative controls: each is useful only because the declared bad change was
rejected for its intended reason. The shortened theorem inventory is an accepted limitation and has
zero positive or mutation-kill credit. A passing sequence means the bounded contract above held for
these exact bytes and cases; it is not a general completeness result.

### Lens 3: executable refinement

`audit/tools/certified-sxpid/scripts/check-exact-products.py` uses only the Python standard
library for its implementation-separated, repository-local reconstruction. For every bounded
table it:

1. scans all events directly;
2. checks event nesting and the local net ratio;
3. constructs all 24 exact rational products;
4. checks three direct-MI products;
5. checks atom net/component identities;
6. checks all multiplicative zeta reconstructions;
7. runs the live Rust certifier;
8. reconstructs a product from every emitted exact-term list;
9. checks the separate exact-product decision, witness, and bounded preflight evidence; and
10. treats the interval decision as interval-local, requiring exact-product consistency without
    forging an interval sign when the endpoints straddle zero.

The fixture, generator, checker sources, and live executable are SHA-256 bound in the emitted
qualification receipt. This is bounded cross-implementation refinement evidence, not a universal
Rust refinement theorem. Python's interpreter, arbitrary-precision integers, `Fraction`, the
checker sources, the live binary, and their host execution remain in the trusted computing base.

### Lens 4: numerical and statistical meaning

The product route is stronger than a floating-point sign heuristic because it decides sign and
zero without evaluating a transcendental function. It complements rather than replaces directed
rounding: a nonzero magnitude or interval still requires a certified logarithm.

The result is conditional on the supplied empirical table. It does not establish:

- that the table represents the intended variables;
- population support coverage;
- unbiasedness, consistency, or calibrated uncertainty;
- independence, stationarity, dependency-color, or drift premises;
- equality between quantized and original continuous estimands; or
- downstream scientific or operational validity.

A tiny exact empirical sign can still be statistically unstable. Exact arithmetic eliminates one
numerical ambiguity; it does not eliminate sampling uncertainty.

### Lens 5: adversarial falsification

The fail-closed self-test kills six source-semantic/arithmetic mutations:

1. source disjunction changed to intersection;
2. keyed target restriction inverted;
3. empirical row multiplicity discarded;
4. the synergy Möbius sign changed; and
5. net multiplication substituted for division; and
6. the exact rational sign comparator reversed.

It also kills thirteen certificate mutations, including the exact-product decision, zero witness,
projected-bit preflight record, and both strict interval/product endpoint boundaries, and rejects
four malformed structural cases, for 23 adversaries total. The strict consistency conditions are

$$
R>1\Longrightarrow U>0,\qquad
R<1\Longrightarrow L<0,\qquad
R=1\Longrightarrow L\le 0\le U.
$$

Thus an interval ending exactly at zero cannot be consistent with a strict positive product, and
an interval beginning exactly at zero cannot be consistent with a strict negative product.
Two additional sentinel controls prove that the auxiliary checker reaches its per-expression and
aggregate admission guards before its powering primitive; they are controls, not added to the 23
rejected-adversary count.

The exhaustive bounded corpus contains every nonempty binary count table with total count at most
four: 494 tables and 11,856 coordinates. The checker verifies 5,280 event constraints, 5,280 local
net identities, 1,482 direct-MI identities, 3,952 component-net identities, and 5,928 zeta
reconstructions. Exact products classify 5,886 zeros, 5,762 positive coordinates, and 208 negative
coordinates. Every live exact-product decision agrees; interval decisions remain a separate
endpoint-derived field.

The boundary exhaustion through total count eight adds 12,869 tables and 308,856 coordinates. It
retains 16 nonempty product-one cases at the first possible total, validates the live minimized
witness, and kills a self-consistently resealed false exact-product sign.

The deterministic evolutionary falsifier uses seed `0x5358504944322026`, total count 64,
population 96, and 96 generations. It evaluates 5,921 distinct larger tables with exact rational
fitness and post-certifies the final boundary candidate. It searches specifically for a negative
informative or misinformative **SxPID partial atom**. It found none. This is negative bounded
evidence, not a proof of universal partial-atom nonnegativity. If it finds a violation in a future
run, it performs deterministic deletion-one minimization and then exact live post-certification.

## Positive and negative findings

Positive findings:

- The exact product theorem applies separately to informative, misinformative, and net
  cumulatives and to every integer-Möbius atom.
- All 11,856 bounded coordinate products equal the repository-local products reconstructed by the
  separate checker from the live certificate's exact term lists.
- All bounded exact-product signs and zeros agree with products separately reconstructed within
  this repository, and none contradicts its directed interval. The two decision domains are
  intentionally distinct.
- The generic product/sign algebra and retained five-factor product identity are kernel-checked in
  Lean.
- The larger seeded search found no negative informative or misinformative SxPID partial atom.

Negative findings and counterexamples:

- Exact arithmetic does **not** make all SxPID values nonnegative. The exhaustive corpus contains
  208 negative net coordinates. Any blanket nonnegativity claim is false.
- A large number of coordinates are exactly zero (5,886), so tolerance-only zero classification
  would discard available exact information.
- Empty canonical terms are sufficient but not necessary for exact zero. The retained $n=8$
  five-term counterexample disproves the former empty-term-only completeness assumption.
- The route does not certify the scientific choice of SxPID, its population interpretation, or
  its fitness for a downstream authority path.
- The current Lean proof checks generic algebra only. Concrete event extraction, lattice binding,
  and code refinement remain separately challenged rather than formally derived end to end.
- Exact rational products can grow very large. The Rust route therefore has explicit term,
  exponent, per-expression projected-bit, and aggregate projected-bit preflights and records an
  unavailable exact-product decision when they fail.
- Evolutionary search is incomplete. Its failure to find a violation cannot replace a theorem.

### Historical-receipt replay boundary

The total-eight boundary record is both scientific evidence and an execution receipt, so those
roles must not be conflated. The former command unconditionally rewrote the tracked JSON. A later
build produced a different executable digest and a different full certificate digest even though
the bounded findings were unchanged; the subsequent claim-custody check correctly rejected the
changed bytes. That failure is retained as a negative process result.

Ordinary replay is now read-only. It validates the fresh certificate, compares the complete
bounded result under an explicit stable projection, emits the full live receipt to standard
output, and leaves the tracked receipt byte-identical. The evidence projection removes exactly
the executable and full-certificate digest bindings. A stable replacement binding hashes the
certificate payload only after the complete outer payload digest and exact outer/tool/build
inventories are validated. It removes exactly one source-manifest leaf and three
build-environment leaves:

1. `payload/tool_binding/runtime_source_manifest_sha256`;
2. `payload/tool_binding/build_context/rustc_verbose_version`;
3. `payload/tool_binding/build_context/build_host`; and
4. `payload/tool_binding/build_context/build_target`.

Every other certificate payload field remains equality-bound, including lockfile, encoding,
profile, cache-policy, distribution-status, arithmetic, coordinate, and claim-boundary content.
The exact-product self-test exercises 51 projection controls: literal inventories, excluded-field
invariance, retained-field sensitivity, semantic-result sensitivity, canonical JSON
normalization, and malformed/missing/extra/digest-mismatch rejection. The explicit
`--update-evidence` mode is a deliberate custody transition, never ordinary qualification.
A second complete recorded-schema sweep mutates every scalar leaf individually: 276 outer-receipt
leaves partition into 274 detected changes and the exact two declared invariances, while 960
certificate-payload leaves partition into 956 detected changes and the exact four declared
invariances. This closes hidden scalar-leaf omissions for these bytes; it does not exhaust
structural transformations, future schemas, parser faults, or cryptographic failure.

The two same-host certificates compared during this correction differed only at the runtime
source-manifest leaf and the resulting outer payload digest; both produced replay projection
`11641347ef83ef7262b54d8be4b112dfef38bd61af22dfa9f89e4930d2b9beba`.
No second platform was executed, so this is a declared variable-field projection contract, not
cross-build or cross-platform validation. The exact machine account is
`audit/evidence/certified-sxpid2-boundary-replay-portability-20260728.json`. The projection does
not establish source/build/executable identity or replace the separate verifier, claim, package,
or release gates.

## Reproduction

```text
python3 audit/tools/certified-sxpid/scripts/check-exact-products.py
python3 audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py
python3 audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py
python3 audit/tools/certified-sxpid/scripts/challenge-exact-products.py \
  --output audit/evidence/sxpid2-exact-product-evolutionary-challenge.json
python3 -I -S -B scripts/check-lean-exact-log-product.py
python3 -O -I -S -B scripts/check-lean-exact-log-product.py
python3 -I -S -B scripts/check-lean-exact-log-product-self-test.py
python3 -O -I -S -B scripts/check-lean-exact-log-product-self-test.py
scripts/check-exact-log-product-sxpid2-pdf.sh --exact
scripts/check-exact-log-product-sxpid2-pdf.sh --cross-toolchain
```

All commands fail closed. The first command builds the locked audit certifier unless
`--no-build` or an explicit `--certifier` path is supplied.
The third command does not update tracked evidence; a reviewed reseal requires the explicit
`--update-evidence` flag.

## References

1. A. Makkeh, A. J. Gutknecht, and M. Wibral, “Introducing a differentiable measure of
   pointwise shared information,” *Physical Review E* 103, 032149 (2021),
   [doi:10.1103/PhysRevE.103.032149](https://doi.org/10.1103/PhysRevE.103.032149). This is the
   published source for the categorical shared-exclusions construction used here.
2. P. L. Williams and R. D. Beer, “Nonnegative decomposition of multivariate information”
   (2010), [arXiv:1004.2515](https://arxiv.org/abs/1004.2515). This supplies historical PID context
   only; its $I_{\min}$ measure is not used by the exact SxPID2 theorem.
