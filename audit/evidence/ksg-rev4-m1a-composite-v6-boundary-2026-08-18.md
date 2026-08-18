# KSG revision-4 M1a composite-v6 portability boundary

- Status: **C5 is published; its attempt-1 hosted qualification failed; R5 is permanently
  unissued; C6 defines one bounded checker correction; R6 remains conditional**
- Observation date: 18 August 2026
- Repository: `sepahead/pid-rs`

## Executive disposition

Published commit `be862b155d710573ec95356fc1cbe9a96a2b83b9` (tree
`37ae61554284a2fabb460d3a20a731b6ade5f8f4`, sole parent
`da253576a5f76e99633fff4de5cf1118f967b90d`) is the exact composite-v5 C5 subject. Its first
hosted attempt did not qualify. CodeQL run `32107469060` completed successfully at attempt 1.
Repository CI run `32107469096` completed with failure at attempt 1 on the exact C5 commit at
`2026-08-18T08:18:19Z`; all 45 jobs were terminal, with 44 successes and one failure. Dedicated composite-v5 run
`32107469077` completed with failure at attempt 1. Its single job `95619716898` passed setup,
checkout normalization, dependency installation, and every bounded C4 failure-surface recheck,
then failed in `Validate the bounded successor publication` with the exact diagnostic
`composite-v5 boundary PDF check: PDF structure embedded Form content differs from standalone figure`.

The sole failed repository CI job, `95619717365`, failed at step 11 on the analogous immutable-v4 lane with
the exact diagnostic `composite-v4 process PDF check: PDF object structure changed: embedded custody Form content differs from the standalone figure`. The v4 and v5 messages are two hosted
observations at the same named Cartesian association-rule failure surface. This is one bounded
repair, not two, and it is not evidence that either immutable publication is defective. The
dedicated-v5 failure remains the decisive false term for R5.

The observed diagnostics reach the same named checker association-rule failure surface; they are
not evidence that either committed publication is visually or structurally invalid. This bounded
reproduction proves neither a unique cause nor the only possible remedy. The versioned cross-toolchain gates constructed
two reports and two standalone figures, then validated their Cartesian product. A report embeds the
committed figure named by its TeX source. A freshly rebuilt standalone figure from another
toolchain may have different PDF content-stream bytes while retaining the gate's bounded text,
page-box, font, and raster properties. Comparing a report's committed embedded Form with that
unreferenced fresh figure is a wrong-lane comparison. One false Cartesian pair therefore failed
before the intended associated pairs could establish the bounded cross-toolchain result.

R5 is permanently unissued because the dedicated-v5 term is false. C6 is an unsigned direct child
of C5 whose only claimed defect repair is this association-rule correction; its exact operational
delta also publishes the separately versioned boundary and qualification machinery.
It does not rewrite C5, reinterpret the failed attempt, issue R5, or transfer any observation to a
new attempt. R6 remains conditional on one fresh exact-C6 local closure observation and fresh
attempt-1 CI, CodeQL, and dedicated-v6 success for that same commit.

This change adds **zero PID theories, zero PID functionals, zero estimators, zero theorem-source
changes, and zero numerical-result changes**. It grants no mathematical, scientific, security,
application, authentication, independence, PDF/UA, or renderer-independence credit.

## C5 attempt-1 disposition

Define

$$
Q_5 = L_5 \land \mathrm{CI}_5 \land \mathrm{CodeQL}_5 \land D_5,
$$

where $L_5$ is one fresh local qualification observation for exact C5, without attempt-number or
first-attempt authority, while the hosted $\mathrm{CI}_5$, $\mathrm{CodeQL}_5$, and $D_5$ terms
require terminal success at attempt 1 for that same commit. The observed dedicated term is

$$
D_5 = \mathrm{false}.
$$

Therefore $Q_5=\mathrm{false}$ regardless of any other term. Under the frozen rule

$$
\mathrm{issue}(R5) \Longleftrightarrow Q_5,
$$

R5 is permanently unissued. A retry would be attempt 2; changing C5 would create another commit.
Neither can retroactively satisfy the C5 attempt-1 predicate.

| Role | Run / attempt | Terminal result | Bounded observation |
|---|---:|---|---|
| Repository CI | `32107469096` / 1 | failure | All 45 jobs were terminal: 44 success, 1 failure; sole failed job `95619717365`, step 11, recorded the analogous immutable-v4 Form mismatch |
| CodeQL | `32107469060` / 1 | success | Four CodeQL jobs passed; this establishes only the CodeQL term |
| Dedicated composite-v5 | `32107469077` / 1 | failure | Job `95619716898` failed only after the publication step began; later dedicated steps were skipped |

Provider identifiers, conclusions, timestamps, logs, and archives are bounded observations. They
do not authenticate GitHub, establish provider completeness or trusted time, or prove that a
particular executable consumed particular bytes atomically.

## The Cartesian association failure surface

Let the v5 checker hold the ordered report lanes

$$
\mathcal R=(R_{\mathrm{fresh}},R_{\mathrm{committed}})
$$

and standalone figure lanes

$$
\mathcal F=(F_{\mathrm{fresh}},F_{\mathrm{committed}}).
$$

The v5 gate evaluated every pair in $\mathcal R\times\mathcal F$ and required each report's unique
embedded Form content to equal the selected standalone figure's content. That rule includes
cross-lane comparisons which the TeX build never referenced. In particular,
$R_{\mathrm{fresh}}$ is built from the TeX-referenced committed figure, not from
$F_{\mathrm{fresh}}$.

The corrected C6 rule separates two relations:

1. each rebuilt or committed report is checked against the exact committed figure referenced by
   the TeX source; and
2. the fresh and committed standalone figures are compared separately under bounded text,
   geometry, font, object-safety, and raster predicates.

This is keyed association, not Cartesian substitution. It does not claim that byte-different PDFs
are semantically identical in general. It permits only the exact bounded differences accepted by
the named predicates and rejects an association to an unreferenced lane.

## Corrected C6 publication gate

The C6 gate preserves the v5 publication and its gate bytes exactly. It validates only the new C6
report family and uses the following closed checks. The separate v6 portability adjudicator
applies the same corrected association to both immutable v4 and v5 lanes without editing them;
that correlated adjudication is not part of this boundary gate.

- exact source, visual-receipt, rendering-receipt, report, figure, and comparator byte bindings;
- well-formed ARIA-labelled SVG with a unique title and description plus a TeX text alternative,
  no scripts, events, animation, external resources, raster images, or text below the declared
  print floor;
- deterministic same-toolchain SVG-to-PDF and LaTeX rebuilds;
- associated report-to-committed-figure Form content, bounding box, resource-category/name
  inventories, canonical non-font resources, bounded font encodings, widths, Unicode maps,
  embedded programs, and on-page placement;
- separate fresh-to-committed figure text, page geometry, font, object-safety, and raster checks;
- four zero-rotation A4 report pages, one zero-rotation standalone figure page, embedded subset
  fonts with Unicode maps, closed catalog/destination/outline/page entry points, and no annotations,
  form fields, embedded files, unsupported actions, inline images, or raster images reachable
  through Forms, patterns, Type 3 fonts, or ExtGState soft masks;
- closed extracted-text headings, body paragraphs, equations, table rows, and page order;
- exact-mode byte reproduction and cross-toolchain text, geometry, font, and same-renderer raster
  bounds; and
- causal hostiles for unsafe or hidden/transformed SVG content; PDF annotations, catalog/outline
  actions, clipping, off-page or zero-scale placement, nonidentity Form matrices, missing or
  altered resources, font encoding/map/program substitution, unsupported object types,
  soft-mask-reachable raster content, wrong-lane association, raster-visible overlays, and
  receipt-body drift.

Same-renderer raster comparison means both operands are rendered by one observed local Poppler.
It is useful differential evidence, not renderer independence, PDF/UA conformance, absolute visual
correctness, or a claim about every PDF consumer.

## Direct C5 to C6 and conditional R6 topology

C6 must be the exact unsigned, single-parent direct child of C5. There is no R5 commit between
them. C6 retains the terminal C5 failure and has exactly the 43-path delta declared by its path
policy: 21 modifications and 22 additions across bounded operational, replay/pointer,
publication, schema/tool, and policy surfaces. It changes no theorem or scientific source. Any
separately reviewed immutable-v4/v5 portability adjudicator remains a correlated repository-local
check; it receives no independence credit from having another filename or process.

Define

$$
Q_6 = L_6 \land \mathrm{CI}_6 \land \mathrm{CodeQL}_6 \land D_6,
$$

where $L_6$ is local static, hostile, replay, source-state, and publication closure for the exact
C6 commit, and the other three terms are terminal hosted success at attempt 1 for that same commit.
A typed local-closure record at
`audit/evidence/ksg-rev4-m1a-composite-local-closure-v6-2026-08-18.json` may establish $L_6$ only
after the receipt checker validates its v1 schema, exact clean C6 subject, clean pre/post Git
snapshots, fixed `just ksg-composite-v6` invocation, successful exit and absent signal, complete
bounded stdout/stderr bindings, normalized minimal environment and `0077` umask, UTC and relative
monotonic ordering, named authority descriptors, and bounded executable hashes/version output.
Absent or invalid local-closure bytes make $L_6$ false. The issuance policy is

$$
\mathrm{issue}(R6) \Longleftrightarrow Q_6.
$$

Any false, absent, nonterminal, or wrong-commit term, or any wrong-attempt hosted term, leaves R6
unissued and requires another append-only contract version. Passing a subset is not partial
qualification. The local record is not an attempt-number or first-attempt authority.

When and only when $Q_6$ is true, a separately typed R6 may contain exactly four path changes: the
self-excluding current-source manifest, the typed local-closure record, the derived v6 receipt,
and the successor-qualification hosted capture. The receipt derives all four terms only after it
validates the durable local record and the fresh exact-C6 attempt-1 hosted capture. The source
manifest is regenerated last. Derivation accepts no successor-capture/evidentiary stdin route; it
reads two distinct stable mode-`0600` inputs through file descriptors 3 and 4 using
`scripts/check-ksg-m1a-composite-v6.py --derive-receipt --local-closure-fd 3 --successor-capture-fd 4 3<"$local" 4<"$successor"`.
Those future bytes are not created or inferred by this publication.

The local record is an unsigned, correlated operator observation, not authentication or
independent replication. Its wall-clock/monotonic ordering and clean pre/post snapshots are not
trusted time or an atomic snapshot; its bounded executable roster is incomplete. The capture does
not pass ambient variables into the command environment, and its bounded scanner rejects named
secret-like patterns and private-path prefixes. These controls do not prove privacy or the absence
of every sensitive value.

The clean endpoints use ordinary Git status plus selected metadata checks; rejecting
core.excludesFile removes one ignore-routing overlay, but repository-ignored products and
uninspected Git metadata remain outside the observation and may remain side inputs, so this is not
a hermetic closure.

## Publication and nonclaims

The report source, ARIA-labelled SVG with title/description, deterministic standalone figure PDF, four-page report PDF,
120-dpi rendering receipt, and closed 144-dpi visual-review receipt form one versioned C6
publication set. Hash equality binds named bytes only. A digest without a retrievable preimage has
commitment or bounded-omission value, not archival durability.

The boundary is reviewed separately for logical implication, Git topology, hosted semantics,
shell failure handling, Python isolation, PDF objects, text extraction, geometry, fonts, raster
layout, SVG accessibility, checker causality, numerical scope, method provenance, security,
privacy, durability, usability, and publication English. Correlated local agents and checkers do
not become independent merely because they use separate files.

Neither this record nor any linked checker implies:

- a new or validated PID, KSG, information-theoretic, or mathematical result;
- transfer among categorical shared exclusions, continuous shared exclusions, KSG mutual
  information, Williams-Beer `I_min`, PID2, PID3, quantized, or mixed-support routes;
- authentication, attestation, authorship, provider completeness, trusted time, peer review, or
  dependency-disjoint independence;
- PDF/UA accessibility, renderer independence, reproducibility outside the stated byte and
  toolchain bounds, or archival preservation; or
- security certification, safety, control authority, application fitness, or evidence for any
  drone or other ecosystem deployment.
