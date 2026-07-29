# KSG revision-4 public-CI tooling correction

Date: 2026-07-29  
Status: `integration_no_go` pending a fresh, complete, all-green public CI run  
Scope: M1a-C2 execution-container correction only

## Adjudication

Public CI run `30409192059` is terminal and failed for exactly two observed
tool-provisioning reasons. The run does not supply a mathematical
counterexample, but it also does not settle full CI. The correction below
therefore changes no scientific fact, estimator, theorem, proof statement,
certificate, numerical fixture, claim status, release decision, or publication
acceptance state.

The machine receipt is
`audit/evidence/ksg-rev4-public-ci-run-30409192059-failure.json`, SHA-256
`9aefa3bd484d55747a2d6887f35311e5f39f3b8eeb9408c3f17cf4cc8db2fa87`.

## Frozen ancestry and chronology

| Role | Commit | Tree | Adjudication |
|---|---|---|---|
| M1a scientific integration | `dc7b8de0a87443ef2bcde71b19938642f1af2197` | `88b24c0ba4fcad4bd749b9146486143397b6a6eb` | Scientific bytes and revision-4 bounded arithmetic core retained |
| First corrective parent, M1a-C1 | `af50935be9ecf9a81aeb30c56b45059652468746` | `ada3860eb696c9a5d634728365acdb5958e7c4e6` | Public run failed; not M1c and not integration GO |
| This correction, M1a-C2 | direct child of `af50935be9ecf9a81aeb30c56b45059652468746` | externally pre-pinned before commit | Remains integration NO-GO until the whole hosted rerun succeeds |

The earlier `dc7` phase authority and evidence remain immutable historical
custody. This phase is independently re-anchored at exact `af509`.

## Terminal hosted evidence

- Run: `30409192059`, workflow `CI`, workflow ID `297369773`, run number
  `146`, attempt `1`, event `push`, branch `main`.
- Subject: commit
  `af50935be9ecf9a81aeb30c56b45059652468746`, tree
  `ada3860eb696c9a5d634728365acdb5958e7c4e6`.
- Time envelope: created `2026-07-28T23:49:13Z`; terminal update
  `2026-07-29T00:09:24Z`.
- Jobs: `45` total, `43` successful, `2` failed.
- The KSG job `90441337099`, `KSG integer-harmonic arithmetic and phase
  isolation`, completed successfully. That scoped success does not override the
  full-run failure.
- The existing proof-core job `90441337145`, `Finite-alphabet,
  dependency-color, support-change, and KSG harmonic proof cores`, completed
  successfully after its pinned Elan installation, pinned cache action, and
  Mathlib cache/build steps. This is a same-run tooling-pattern control, not
  evidence that another job inherited its environment.

### Observed failure 1: certified SxPID2 job

- Job `90441337083`, `Exact-count directed-rounding SxPID2 reference`, had
  Actions status `completed` and conclusion `failure`.
- Step 18 failed with exact error
  `Lean exact-log-product check failed: lake is not available`.
- The decoded REST job log is exactly `108775` bytes with SHA-256
  `4c066f81381f873f5b1d8bff6d62ab0afffedbb93fbb52d9b0a185bfddd30f10`.
- Actions steps 19-22 were skipped: the claim checker, its self-test,
  `cargo-deny` installation, and the certified-tool dependency audit. They
  receive no credit.
- Post-run cleanup step 43,
  `Post Run actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1`,
  was also reported skipped. It is retained for complete Actions-step
  inventory, is not a substantive user gate, and receives no credit.

### Observed failure 2: formal-PDF job

- Job `90441337159`, `Formal LaTeX / PDF inventory and cross-toolchain
  structure`, had Actions status `completed` and conclusion `failure`.
- Its composite paper step failed in
  `scripts/check-ecosystem-compatibility-audit-pdf.sh --cross-toolchain` with
  exact error
  `ecosystem compatibility audit PDF check: missing command: chktex`.
- The decoded REST job log is exactly `43692` bytes with SHA-256
  `4889d459eaf1c52f394612a593e4bf27718145169025d314f078f718f5cc932c`.
- GitHub reported no later Actions step as skipped because the paper set is one
  composite shell step. The log contains completion markers for the style
  checker, its self-test, and the first two paper routes. The six later paper
  routes listed in the machine receipt were not reached and receive no
  execution credit.

The following canonical projection is checked directly against the machine
receipt. The delimiters are part of the human/machine parity contract.

```text
PUBLIC_CI_FAILURE_PARITY_BEGIN
{
  "failed_jobs": [
    {
      "conclusion": "failure",
      "exact_error": "Lean exact-log-product check failed: lake is not available",
      "id": 90441337083,
      "log_sha256": "4c066f81381f873f5b1d8bff6d62ab0afffedbb93fbb52d9b0a185bfddd30f10",
      "log_size_bytes": 108775,
      "scientific_counterexample": false,
      "step_number": 18
    },
    {
      "conclusion": "failure",
      "exact_error": "ecosystem compatibility audit PDF check: missing command: chktex",
      "id": 90441337159,
      "log_sha256": "4889d459eaf1c52f394612a593e4bf27718145169025d314f078f718f5cc932c",
      "log_size_bytes": 43692,
      "scientific_counterexample": false,
      "step_number": 5
    }
  ],
  "formal_pdf_intra_step": {
    "completed_routes": [
      "python3 scripts/check-formal-pdf-style.py",
      "python3 scripts/check-formal-pdf-style-self-test.py",
      "scripts/check-certified-sxpid2-assurance-pdf.sh --cross-toolchain",
      "scripts/check-dependency-colored-sxpid-pdf.sh --cross-toolchain"
    ],
    "failed_route": "scripts/check-ecosystem-compatibility-audit-pdf.sh --cross-toolchain",
    "unreached_routes": [
      "scripts/check-exact-log-product-sxpid2-pdf.sh --cross-toolchain",
      "scripts/check-finite-alphabet-convergence-pdf.sh --cross-toolchain",
      "scripts/check-formal-tool-adoption-pdf.sh --cross-toolchain",
      "scripts/check-foundational-sxpid-audit-pdf.sh --cross-toolchain",
      "scripts/check-mathematical-workflow-pdf.sh --cross-toolchain",
      "scripts/check-support-change-tolerant-sxpid-pdf.sh --cross-toolchain"
    ]
  },
  "head": {
    "commit": "af50935be9ecf9a81aeb30c56b45059652468746",
    "tree": "ada3860eb696c9a5d634728365acdb5958e7c4e6"
  },
  "integration_disposition": "NO-GO pending a fresh complete public rerun",
  "job_counts": {
    "failed": 2,
    "success": 43,
    "total": 45
  },
  "ksg_job": {
    "conclusion": "success",
    "id": 90441337099,
    "status": "completed"
  },
  "latent_dependencies": [
    {
      "classification": "statically discovered latent dependency",
      "missing_tool": "lake",
      "route": "scripts/check-foundational-sxpid-audit-pdf.sh --cross-toolchain"
    }
  ],
  "observed_missing_tools": [
    "lake",
    "chktex"
  ],
  "receipt_path": "audit/evidence/ksg-rev4-public-ci-run-30409192059-failure.json",
  "receipt_sha256": "9aefa3bd484d55747a2d6887f35311e5f39f3b8eeb9408c3f17cf4cc8db2fa87",
  "remediation": {
    "settled_full_ci": false,
    "whole_run_rerun_required": true
  },
  "run": {
    "attempt": 1,
    "conclusion": "failure",
    "id": 30409192059,
    "number": 146,
    "status": "completed"
  },
  "schema": "pid-rs/public-ci-failure-human-parity",
  "schema_revision": 1,
  "skipped_actions_steps": [
    {
      "conclusion": "skipped",
      "name": "Run python3 scripts/check-certified-sxpid2-claim.py",
      "number": 19,
      "status": "completed"
    },
    {
      "conclusion": "skipped",
      "name": "Run python3 scripts/check-certified-sxpid2-claim-self-test.py",
      "number": 20,
      "status": "completed"
    },
    {
      "conclusion": "skipped",
      "name": "Run cargo install cargo-deny --locked --version 0.20.2",
      "number": 21,
      "status": "completed"
    },
    {
      "conclusion": "skipped",
      "name": "Run cargo deny --manifest-path audit/tools/certified-sxpid/Cargo.toml --config audit/tools/certified-sxpid/deny.toml check",
      "number": 22,
      "status": "completed"
    },
    {
      "conclusion": "skipped",
      "name": "Post Run actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
      "number": 43,
      "status": "completed"
    }
  ]
}
PUBLIC_CI_FAILURE_PARITY_END
```

### Latent dependency found before rerun

Static reachability review of `scripts/check-formal-pdf-set.sh` showed that the
same formal-PDF job would later invoke
`scripts/check-foundational-sxpid-audit-pdf.sh`, which calls the Lean descriptor
checker. The earlier `chktex` failure stopped execution before this missing
`lake` dependency could be observed in hosted CI. It is therefore classified
as a statically discovered latent provisioning defect, not as a second
observed hosted failure and not as proof that the downstream route would
otherwise pass.

Local negative controls reinforced the dependency boundary but supplied no
formal-proof credit. A cross-toolchain paper-set attempt reached the
foundational route and timed out while `lake` attempted toolchain discovery.
A separate direct exact-log-product invocation also timed out after 60 seconds
at `lake env lean --version`; another silent download attempt was manually
terminated. These are non-credited operator observations rather than archived
execution receipts. No output from those incomplete routes is treated as
settled evidence.

## Exact correction

The correction:

1. installs `chktex` before the unchanged formal-PDF paper-set gate;
2. provisions both the formal-PDF job and the existing certified-SxPID2 job
   with the same checksum-pinned Elan 4.2.3 archive, pinned cache action,
   Lean-toolchain and Mathlib-manifest cache bindings, `lake exe cache get`,
   and `lake build` route already exercised by the successful proof-core job;
3. makes the directly invocable foundational-paper checker preflight `lake`;
4. rebinds only the certified job and whole-workflow SHA-256 constants in the
   certified-SxPID2 claim checker; and
5. adds this human record, the canonical machine receipt, and the re-anchored
   phase policy/checker attacks.

The exact path policy contains nine paths: six modified and three added.
Neither `git add -A` nor ambient dirty-tree content is permitted. The phase
checker reconstructs the prior three-edit `dc7` to `af509` transform, then the
new `af509` tooling transform, and separately preserves the old ecosystem,
package, release, identity, scientific, PID2, PID3, and frontier bytes.

## Failure-diverse review lenses

| Lens | Evidence used | Failure class attacked | Limit |
|---|---|---|---|
| Hosted execution | Terminal run/job/step state from the Actions API | Confusing queued, skipped, failed, and completed states | GitHub execution is not a proof of mathematics |
| Raw-byte provenance | Exact decoded-log sizes and SHA-256 values | Paraphrased or substituted failure logs | The hashes do not authenticate GitHub as a transparency log |
| Static dependency reachability | Workflow plus nested paper-set and foundational scripts | A later missing tool hidden by an earlier failure | Reachability does not prove the later route will pass |
| Reproducible toolchain | Pinned Elan URL and archive digest, pinned cache action, manifest-bound cache keys, explicit build | Version drift, cache substitution, missing setup, and consumer-before-build ordering | Hosted rerun is still required |
| Claim and phase custody | Exact commit/tree ancestry, nine-path A/M policy, full-blob pins, digest-only claim rebind | Scientific contamination, repeated transitions, deletion, unrelated edits, and post-hoc resealing | External tree custody is not authenticity |
| Hostile mutation | Normal and optimized checker attacks over omission, duplication, placement, pin, cache, order, receipt, policy, and call reachability | Superficially green gates whose decisive checks are dead, moved, or weakened | Mutation adequacy is bounded by the enumerated attacks |
| Local negative reproduction | Timed-out Lean discovery routes retained without credit | Mistaking local partial progress for formal verification | Local machine state differs from the fresh hosted runner |

The toolchain pin is intentionally described at its real boundary. The Elan
installer archive and Actions cache implementation are byte/commit pinned.
`ubuntu-latest` and apt-installed `chktex` are not byte-pinned because the PDF
gate is explicitly cross-toolchain. Downloaded Lean binaries and Mathlib cache
artifacts retain the existing identifier/manifest-pinned network trust
boundary. The fallback cache key binds OS, architecture, Lean toolchain, and
Mathlib manifest, but not the lakefile or local sources; `lake build` supplies
the downstream invalidation check. Dependency-only caching or additional
lakefile/source bindings remain a separately reviewable hardening route, not a
claim silently folded into this correction.

## Candidate verification and no-credit rule

The candidate must pass the phase checker and hostile suite in normal and
optimized Python, the unchanged 111-mutation certified-SxPID2 claim suite, the
direct formal-PDF routes with page/render checks, the scoped KSG routes, and an
independently staged-tree replay before commit. Exact command outcomes are
recorded only after every writer has stopped and the candidate bytes are
settled.

### Hostile-review correction before freeze

A final independent custody review rejected an earlier checker contract before
it received settlement credit. The memo required M1a-C2 to be one direct child
of `af50935be9ecf9a81aeb30c56b45059652468746`, but the earlier checker admitted
as many as three monotone descendants, including a split-path history with an
empty middle commit. The accepted candidate instead pins the bound to exactly
one commit in the checker source model, states the same direct-child obligation
in the separately reviewed path policy, and rejects split-path and empty-prefix
histories as distinct negative controls. The same review found that the new
changelog bullet had introduced a duplicate nearby `Fixed` heading; the bullet
was moved under the existing heading. The superseded 178-mutation result is not
credited.

On the corrected precommit bytes, both normal and optimized phase suites reject
181 hostile cases: 31 checker-model, 14 policy-authority, 8 path-custody, 5
external-tree, 16 Git-context, 21 public-CI-evidence, 75 hash-rebased-semantic,
and 11 lifecycle-history cases. Two separate bool/integer JSON controls and the
retained checker-self-reference control also pass. The certified-SxPID2 checker
passes in both modes, and its byte-unchanged
`cac22cb1af20e8b020d67ec1124515179db4cc93ddc4885d43d83a49dd46a24f`
self-test rejects all 111 registered mutations in both modes. These are bounded
checker and custody results, not mathematical or hosted-execution credit.

The nine-paper cross-toolchain route rebuilt and structurally compared all nine
PDFs. Three disjoint raster review partitions then covered all 186 rendered
pages. Full-resolution adjudication withdrew one contact-sheet false positive:
page 22 of the formal-tool-adoption audit does contain both running heads and
the rule. It confirmed two pre-existing publication defects in the unchanged
mathematical-workflow PDF: page 23 breaks the inline token `Epi(g_s)` after
`Epi(`, and page 24 breaks `BLOCKED` after `BLO`. There was no clipping,
overlap, blank or missing page, broken glyph, or additional layout defect
observed. The two line-break defects are outside this exact nine-path
execution-container correction and remain open for the separately scoped M1c
audience-artifact regeneration; therefore no flawless-publication claim is
made here. Raster review does not verify PDF internals, accessibility,
citations, or mathematical content.

Static candidate checks additionally pass duplicate-rejecting YAML parsing for
all 24 workflow jobs, Bash syntax, ShellCheck, Python compilation, Ruff, and
`git diff --check`. An ad hoc strict Mypy probe is retained as a non-credited
negative route: it reports 40 diagnostics across the current two phase
scripts, and Mypy is not a configured repository gate. Those diagnostics were
not relabelled as runtime, mutation, or scientific failures and were not
silently treated as a pass.

No local or scoped success can promote this correction. Only a fresh,
complete, all-green public run for the pushed correction can close the
execution-container defect. M1c remains a later, separately bounded milestone.

## Claim boundary

This record establishes only the exact failed-run facts, the observed versus
latent provisioning distinction, and the bounded correction plan. It does not
establish KSG or PID correctness, estimator validity, support assumptions,
binary64 portability, release readiness, package identity, publication
acceptance, downstream compatibility, or authenticity. It does not convert
bounded evidence into a universal theorem and does not transfer results among
KSG MI, continuous shared exclusions, categorical SxPID, `I_min`, fitted
quantized compositions, PID2, PID3, or project-defined diagnostics.
