# Correctness-audit intake, 2026-07-24

## Status

This record evaluates two user-supplied documents as review inputs:

- `MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md` and its PDF rendering;
- `PID_RS_CORRECTNESS_ASSURANCE_AUDIT.md` and its PDF rendering.

The documents are not independent evidence. Each PDF is a rendering of its corresponding Markdown
source. The correctness audit is a cleaned copy of an external AI review. Its conclusions remain
unreplayed until repository artifacts close the applicable obligations.

The intake adds no PID method, theorem, implementation, benchmark result, or release claim.

## Source identities

| Artifact | SHA-256 |
|---|---|
| Mathematical workflow Markdown | `04329fd464bbfe62452453a711d72dd37d02ce150cae7beff3d9603562b380aa` |
| Mathematical workflow PDF | `51591ac1634cf1f94dd189cf1c1e0cfa3dc17f892e55f71040e913561cc5d943` |
| Correctness audit Markdown | `5f19f8c3af1ca9daee357dad5860b17f0542343b7ab9f281eb5c19c92d2b1bde` |
| Correctness audit PDF | `3237141ef9aba475af8afe2284e7eae95a14116d532f5e11de2387733796f6d3` |

The Markdown files were read in full. Poppler rendered all 35 PDF pages to PNG. Contact-sheet review
and full-size review of dense table pages found no visible clipping, overlap, missing glyphs, or
unreadable equations. This visual check validates the conversion layout only. It does not validate
the mathematical content.

## Adopted process controls

The repository workflow now adopts these controls:

- immutable revisions for major claim packets;
- separate proof, counterexample, formal, implementation, numerical, and statistical roles;
- independent route memos before routes exchange conclusions;
- explicit evidence labels for model statements;
- complete semantic-domain checks or a proved reduction;
- retained failed routes and exact counterexamples;
- a separate exceptional-case obligation;
- layered go/no-go gates from claim identity through consumer qualification;
- explicit treatment of model output as exploratory until replayable evidence supports it.

These controls extend the existing workflow. They do not retroactively make earlier model runs
independent or preregistered.

## Recommendations and replay dispositions

| Source recommendation | Intake disposition | Repository evidence or next obligation |
|---|---|---|
| Keep paper definitions, project compositions, and diagnostics separate | Accepted and implemented | `method-catalog.json`, `METHODS.md`, source markers |
| Use claim packets, route records, and retained failures | Accepted for major claims | `MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md`; first new use is the support-change-tolerant averaged SxPID claim |
| Treat Lean and blind benchmarks as different evidence | Accepted | Workflow claim-to-evidence matrix |
| Formalize empirical rows through concrete SxPID events and atoms | Valid open obligation | Existing Lean files explicitly stop before full SxPID semantics and Rust refinement |
| Prove specialized and general categorical paths equivalent | Requires current-state replay | Existing bounded exhaustive tests are evidence only for their declared domains |
| Add rigorous logarithm and atom enclosures | Valid open obligation | Existing high-precision fixtures are not interval certificates |
| Add three-valued sign and tie decisions | Valid only with certified enclosures | No global public certified-numerics path is claimed |
| Make dependence and support assumptions fail closed | Partly implemented; continue | Typed continuous support contracts and dependency-colored evidence have explicit limits |
| Qualify each downstream consumer | Historical gap contract implemented; qualification remains open | `ecosystem-capabilities.json`, `ECOSYSTEM_CAPABILITIES.md` |
| Treat continuous PID2 as generally consistent | Rejected | No general consistency theorem is present |
| Treat continuous PID3 as authoritative | Rejected | Mixed-dimensional full PID3 remains research-only |
| Let PID independently authorize an action | Rejected | Ecosystem contract retains the non-authority boundary |
| Import the source review's pass labels | Rejected | An external AI judgment is not a repository evidence class |
| Count Markdown and PDF copies as corroboration | Rejected | They are two formats of the same source |
| Use model consensus to close a claim | Rejected | Shared training data and shared omitted bridges defeat independence |

## Current mathematical application

The first application of the strengthened workflow is a proposed support-change-tolerant
continuity theorem for averaged finite-alphabet shared-exclusions PID. The claim is distinct from
the existing common-support result:

- it permits support creation and deletion;
- it applies to averaged cumulatives and atoms, not pointwise local values;
- it uses overlap decomposition and finite residual-entropy terms;
- it retains exact counterexamples to an entropy-only bound and to a maximum-residual shortcut;
- it remains an exact-real theorem, not a binary64 or estimator-calibration theorem.

The theorem remains active until its proof, formal theorem map, exact counterexamples, bounded
implementation replay, provenance audit, and claim-to-evidence matrix agree. An AI proof draft or a
high-precision decimal comparison cannot close it.

## Rejected evidence substitutions

- A visually correct PDF is not a mathematical proof.
- A formal lemma about abstract reals is not concrete SxPID-to-Rust refinement.
- A bounded exhaustive test is not a universal theorem outside its declared bound.
- A high-precision decimal is not an outward-rounded interval.
- A concentration theorem under a declared coloring does not validate the coloring from data.
- A one-shot confidence bound is not a repeated-alarm guarantee.
- A downstream capability projection is not current integration or application validity.

This record remains diagnostic. Later evidence must link the exact claim revision and artifact
digest before it can change a claim disposition.
