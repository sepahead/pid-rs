# C3 Noble hosted terminal receipt

- Date recorded: 2026-08-03
- Subject commit: `791a39935fdca4cfe4e907829faa240e08520b6e`
- Subject tree: `360c3f4c757ab30ce3cf1969cf7f521d42da3ecf`
- Subject direct parent: `196b3de19d74a097713474a3a811f24d24bf5de5`
- Receipt schema revision: 2
- Disposition: **C3 portability correction closed for this exact subject; KSG G1/M1a, M1c, and
  the wider program remain open**

## Original revision-1 boundary

Revision-1 bytes of this file and its machine-readable companion were introduced by strict
descendant evidence-only commit `413937275abe74a881ff4c177fd80d1c7467ffbd`, tree
`25fd042660ff4d58786c8039abde89249fc71218`, whose direct parent is the subject above. The JSON
blob is `cedc835c6ec51239316b07f619347f6ac7c0e69d` (11,089 bytes; SHA-256
`1e56db515c928e749c98888b14cab2dd473eeaa98f02aefac28e984551733f04`). The Markdown blob is
`9b03ed2c2e16f193ab6f3049ba2409b1a3369c7a` (12,192 bytes; SHA-256
`05770a2b56fbe0a37782cc55c3b528411f2c9bfee8a887e3e6428ff5fc4f7abd`). Both blobs remain
byte-identical at `4139372`, `59e7451`, and `f1863d5`.

Those revision-1 bytes were absent from subject CI run `30771579118` and CodeQL run
`30771578952`. Neither subject run can authenticate the later receipt. The original receipt
commit's own CI run `30791862414` and CodeQL run `30791862144` cannot provide already-existing
custody of their own revision-1 bytes. Revision 2 does not re-adjudicate exact custody of revision
1. Future exact custody of revision 1 requires a strict descendant or external immutable
attestation that names the original receipt commit and exact receipt digest.

## Pre-erratum lineage

The exact lineage from the C3 subject through the required direct parent of this erratum is:

```text
8b792bc143fff2d84f2d8e7817d1de7850741223
  -> 8fa6e992d9124229c7a175c4508bf10df336675a
  -> f6fde520b841c61b7752cdd053af59bda763d3d1
  -> 196b3de19d74a097713474a3a811f24d24bf5de5
  -> 791a39935fdca4cfe4e907829faa240e08520b6e  C3 subject
  -> 413937275abe74a881ff4c177fd80d1c7467ffbd  original revision-1 receipt
  -> 59e7451d40e5a75366fb0213c2c6ddaf0385f226  method-semantics correction
  -> f1863d58ae3cf907f4d8d0eefcd15b6f29b46d55  documentation-custody repair
  -> this revision-2 observational erratum
```

| Commit | Tree | Hosted CI | CodeQL | Revision-1 receipt blobs |
|---|---|---|---|---|
| `4139372` | `25fd042660ff4d58786c8039abde89249fc71218` | `30791862414`: 45/45 success | `30791862144`: 4/4 success | Original |
| `59e7451` | `b6f38a5462629460947630a4e92ab53c250919bf` | `30812385219`: **failure**, 44/45 success | `30812382065`: 4/4 success | Unchanged |
| `f1863d5` | `b9fd8490df6d02789259ced59c6269de8183f58c` | `30840121158`: 45/45 success | `30840119754`: 4/4 success | Unchanged |

The `59e7451` failure remains a failure. Job `91681934915` failed at
`Run python3 scripts/check-certified-sxpid2-claim.py` because the frozen `scripts/README.md`
digest had changed. Commit `f1863d5` restores those exact documentation bytes; it does not
reclassify the failed run. The repaired directed-rounding SxPID2 job `91774842132` and the long KSG
job `91774842025` both succeed in the exact `f1863d5` run.

The original receipt commit changed only the changelog and the two receipt documents. Intervening
commit `59e7451` changed the method authority, generated methods documentation, claim checker,
fixtures, and changelog. Commit `f1863d5` repaired the declared documentation-custody defect. This
erratum changes only the changelog and the two receipt documents; it does not erase or relabel
those intervening changes.

## Revision-2 acyclic boundary

The required direct parent of this erratum is `f1863d58ae3cf907f4d8d0eefcd15b6f29b46d55`,
tree `b9fd8490df6d02789259ced59c6269de8183f58c`. The revision-2 correction bytes are absent
from the C3 subject, original receipt, intervening commit, and required-parent trees and runs. None
of those runs can authenticate the correction. A run of the erratum-bearing commit also cannot
provide already-existing custody of its own bytes.

Exact custody of revision 2 is **NOT ESTABLISHED**. It requires a later strict descendant or an
external immutable attestation that names the erratum commit and the exact receipt digest. The
erratum commit is required to remain unsigned under repository policy; this document does not
claim the future Git object's observed signature state.

The subject is observed as unsigned. That Git-state observation is not an authorship or
authenticity proof.

## Descendant compact-summary erratum

The content-addressed retained JSON summaries underlying and cited by revision 1 contain two
incorrect CodeQL runtime action-resolution values. Each logical error appears once in each of the
two summaries, for four affected field instances. Revision 2 records the observations without
altering either summary or any other retained artifact.

| Retained summary | Summary SHA-256 | JSON pointer | Incorrect summary value | Exact-subject-run observation |
|---|---|---|---|---|
| `codeql/security-summary.json` | `f4a4532aa28fe4fa1bdafd783bbfbbc1bfce1dc8703027371dbba062b09f1104` | `/tool/runtime_action_resolutions/checkout` | `d23441a48f845ab2bb7d5681375b15d21c7b7d3c` | `d23441a48e516b6c34aea4fa41551a30e30af803` |
| `codeql/security-summary.json` | `f4a4532aa28fe4fa1bdafd783bbfbbc1bfce1dc8703027371dbba062b09f1104` | `/tool/runtime_action_resolutions/codeql_action` | `f205ea1c1a7b4a21b10cf8a6faae31e4a9f67113` | `f205ea1c3313d32999d8d6a48b4f6530d4437b38` |
| `receipt-summary.json` | `6e38d75c3526793048fc1472d4d64842fe9f855015169f3641a89b6fd74ec0fa` | `/gates/codeql/tool/runtime_action_resolutions/checkout` | `d23441a48f845ab2bb7d5681375b15d21c7b7d3c` | `d23441a48e516b6c34aea4fa41551a30e30af803` |
| `receipt-summary.json` | `6e38d75c3526793048fc1472d4d64842fe9f855015169f3641a89b6fd74ec0fa` | `/gates/codeql/tool/runtime_action_resolutions/codeql_action` | `f205ea1c1a7b4a21b10cf8a6faae31e4a9f67113` | `f205ea1c3313d32999d8d6a48b4f6530d4437b38` |

The bounded observations come from these unchanged retained sources:

- `codeql/action-resolutions.txt`, SHA-256
  `05cc784f7fff1a7bacc56f93666d4c4b8566594245a8bb9e9d22fc9683d31f04`;
- `codeql/logs.txt`, SHA-256
  `9e9571878833ca7a2c310cba371f4a8a526452e80fdaba8b21a7ed858b3d3e3c`; and
- `codeql/logs.zip`, SHA-256
  `39220f901face50854b8513324179b9b3f2800aab848bcd7e0754dbdced8845a`.

They belong to subject CodeQL run `30771578952` and jobs `91559529557` (Actions),
`91559529520` (JavaScript/TypeScript; retained job name `Analyze (javascript-typescript)`),
`91559529514` (Python), and `91559529535` (Rust). Each incorrect value appears twice across the
two summaries and zero times in both raw text sources. Each observed value appears zero times in
the summaries, once in `codeql/action-resolutions.txt`, and four times in `codeql/logs.txt`, once
per CodeQL job.

All four incorrect summary fields receive **zero credit**. The observed SHAs receive only bounded
exact-subject-run log-observation credit. They are not repository source pins, authenticity
evidence, or custody evidence. No other summary field is newly re-adjudicated. The 87-entry
manifest validates the retained bytes, not the field semantics of those bytes.

This erratum changes none of the original dispositions: exact-subject C3 closure remains bounded
as recorded, `security_clean_claim=false`, KSG remains `integration_no_go` with all 13 integration
gates open, and release status remains unchanged. Exact erratum custody is **NOT ESTABLISHED**.

## Terminal hosted CI

[CI run `30771579118`](https://github.com/sepahead/pid-rs/actions/runs/30771579118), attempt 1,
run 157, was triggered by a push to `main` at exact head `791a39935fdca4cfe4e907829faa240e08520b6e`.
The terminal run object reported status `completed` and conclusion `success`; its API
`updated_at` value is `2026-08-03T00:25:54Z`.

- Exactly 45 of 45 jobs completed successfully; zero jobs had another conclusion.
- Exactly 534 of 534 API-recorded steps completed successfully; zero steps had another
  conclusion.
- Every job reports the exact subject SHA.
- The complete log ZIP was downloaded twice byte-identically at SHA-256
  `3a84cd765befb009027ce184ee8868bdd6fce6ab77203bac56a2b162b619b485` and passed ZIP
  integrity. Its 105 members reconcile to 45 top-level job logs, 45 system logs, and 15 expanded
  KSG step logs.

The exact workflow is 49,305 bytes, Git blob
`d38532042c0168df2b51f2526bc10e465f26ffc7`, and SHA-256
`b8457a955da4560c6c3d296b81ca8c390ba5f908209eee90eaecc86a86c9bf7d`. All seven unique
third-party action references in that source are full 40-hex pins. This binds the repository
workflow bytes. It does not authenticate GitHub's runner, operating system, package mirrors,
compiler, dynamic loader, or hardware.

## Formal PDF job

Job `91559552230`, “Formal LaTeX / PDF inventory and cross-toolchain structure,” completed
successfully on Ubuntu 24.04.4 runner image `20260720.247.2`. The job installed Noble package
`texlive-luatex` version `2023.20240207-1`, exercised all nine then-current formal papers, rejected
six visual mutations and sixteen citation-edge mutations, and recorded nine warning-free
cross-toolchain structural comparisons.

The hosted log reports these rebuilt PDF SHA-256 values:

| Report | Hosted rebuilt SHA-256 |
|---|---|
| Certified SxPID2 executable assurance | `fe8a8af0ddec4904922c3073f45bc7503d7e1b00d34d168b083463d638392142` |
| Dependency-colored SxPID concentration | `88f5f268a533be9fd7a15921870b348d3024dbd010b2d28097cca3d2ce48de4e` |
| Ecosystem compatibility audit | `8d79e4ce11b525c6e3da4216f740200cb133408a7727be739681cb2bbb9960d8` |
| Exact-log-product SxPID2 assurance | `4a85905ea19febd926b07945524a0f4d60ee2d9988511828867147d9b80ad6a4` |
| Finite-alphabet convergence | `b48b90e5bedc00235ca24b75f87c8de73129770683993e1d2f5ce1e06ec867fa` |
| Formal-tool adoption audit | `bdc41860d1a1ebd9ec3f36bd07458f7fd5c9744d2a88fecd0bd79edc33d18b13` |
| Foundational SxPID audit | `b869245819a61c4999c0eaca688db16730fa4a7936eb0a19390cbd887d9491f3` |
| Mathematical workflow | `f438f7fca513c1e6d1ce32f15c150cd788c6b05caf85c403fcbd5cec2b2d3c6c` |
| Support-change-tolerant SxPID | `d03061cdb16d0cad9ea0af86c28f4dee363676545e82fdd0e375c9f0cab9f933` |

The rebuilt PDF bytes were **not uploaded**. These are exact hosted-log observations coupled to a
successful structural gate, not retained-byte reproductions. Warning freedom, embedded-font and
geometry checks, citation-edge mutations, and shared visual-system checks do not prove
mathematical truth, citation correctness, novelty, or application validity.

## KSG/C3 job and the M1c refusal

Job `91559552241`, “KSG integer-harmonic arithmetic and phase isolation,” completed successfully.
The retained log binds the following finite evidence in normal and optimized Python modes:

- 8,198 frozen arithmetic rows and 8,198 directed intervals;
- 6,920 exact-Fraction containments and zero binary64 conversion mismatches;
- 29 exact-enclosure mutations and 28 modular-certificate mutations rejected per mode;
- 141 claim-only and 176 full revision mutations rejected per mode;
- the frozen 351-case phase-isolation hostile-family aggregate per mode, with its nested and
  separately typed controls retained as correlated bookkeeping;
- three debug and three release one-test compiled production witnesses; and
- twelve serial and twelve parallel tests in each debug/release profile.

The exact KSG job log SHA-256 is
`8547a61b355fbdf085739292e8975bc13634e33f32fb2f46aef11acd98661243`.

This result does **not** close KSG M1c. Revision 4 remains exactly
`integration_no_go`, stage `preclosure_core_manifest_must_be_regenerated_at_m1c`. The immutable
C3 checkpoint receipt adjudicates `8fa6e99`; the follow-up receipt adjudicates `f6fde52`; both
explicitly disclaim adjudicating descendant `791a399`. Hosted execution at `791a399` closes the
requested C3 portability run, not the later core-manifest milestone. Frozen arithmetic,
mutations, and compiled witnesses do not prove KSG consistency, population-support eligibility,
continuous-PID validity, statistical calibration, application validity, universal bounds, or
cross-platform numerical identity.

This receipt also does **not** close KSG G1 or establish the canonical M1a implementation anchor.
The active revision-4 packet retains all 13 integration gates as open. Its repository and
publication disposition remains `integration_no_go`; G1/M1a must still be established by its own
unsigned implementation anchor, remote verification, and acyclic receipt before M1c can begin.

## Honest security receipt

[CodeQL run `30771578952`](https://github.com/sepahead/pid-rs/actions/runs/30771578952), attempt 1,
completed successfully with four of four analysis jobs successful at the exact subject SHA.
CodeQL 2.26.2 reported 133 analysis results across the Rust and Python analyses. Successful
analysis execution is not a security-clean result.

The exact-head alert capture contains:

- **87 open alerts:** 21 critical and 66 high; 22 Python and 65 Rust;
- open-rule inventory: 2 `py/code-injection`, 4 `py/command-line-injection`,
  15 `py/path-injection`, 1 `py/redos`, 15 `rust/hard-coded-cryptographic-value`, and
  50 `rust/path-injection`;
- **46 dismissed** `rust/path-injection` alerts: 43 recorded as `used in tests` and 3 as
  `false positive`; this receipt captures rather than independently re-adjudicates those
  dispositions; and
- **0 fixed** alerts.

The repository-global snapshot separately contained one fixed alert whose most recent instance
was commit `8fa6e992d9124229c7a175c4508bf10df336675a`. It is outside the exact-head projection above.
Thus “0 fixed” means zero records whose `most_recent_instance.commit_sha` equals the exact subject,
not zero fixed alerts in repository-global history.

None of the captured alerts has a creation timestamp inside the CI run window. That timing fact
does not adjudicate the alerts, prove that the subject could not affect them, or authorize an
absence-of-vulnerabilities claim. No SARIF artifact was uploaded. The managed CodeQL workflow uses
mutable major tags; logged runtime resolutions are observations for this run rather than immutable
repository pins.

The Gitleaks 8.30.1 job also completed successfully, reported no leaks over its locally fetched
advertised heads/tags, and passed the frozen allowlist control of 8 accepted and 48 rejected cases.
This is a finite scanner result, not a theorem that no secret exists.

## Uploaded artifacts

GitHub exposed exactly two run artifacts:

- `coverage-lcov`, ZIP SHA-256
  `35faf93d543453abdb87db9fc9e652d636c4c9dfe911071b947cfba530e6bed4`; its retained LCOV
  covers 35 source files and records 33,819 hit lines of 39,325 found, giving the derived ratio
  `0.859987285441831`;
- `workspace-sbom`, ZIP SHA-256
  `17c96a4a768e791a0b0b93a7378e13b4efef4df06b1805b65410f7ba34c250a1`; it contains three
  valid-shape CycloneDX 1.3 JSON documents.

No PDF, wheel, package, SARIF, or rebuilt scientific-output bytes were uploaded. Coverage and SBOM
projections are not independent test replays, attestations, completeness proofs, reproducible-build
proofs, or vulnerability-absence results.

## External custody and retained negatives

The source-read-only hosted capture is currently outside the repository at
`/private/tmp/pid-rs-c3-hosted-791.PPelD7`. Its 87-entry manifest has SHA-256
`755efc14321735d56d784c42df6902e67c8f06d4b70ee47ffe988dc447260ba4`. The compact source
receipt is retained with the two logical errata above and has SHA-256
`6e38d75c3526793048fc1472d4d64842fe9f855015169f3641a89b6fd74ec0fa`.
The 3,963,474-byte archive `/private/tmp/pid-rs-c3-hosted-791.PPelD7.tar.gz` has SHA-256
`586344989147f2b25d8d94dc045b01af16acc5dc08c754b1c0898f16c35c6c21`; a fresh extraction
passed all 87 manifest checks. That replay validates retained-byte integrity, not the semantic
correctness of compact-summary fields. These are local custody facts, not remote durability, a
transparency log, or an external attestation.

Negative results remain part of the record:

- the pre-terminal zero-byte `gh` job-log capture receives zero credit; the later terminal API
  capture replaces it;
- a CodeQL request that ended in a TLS handshake timeout and fed an empty downstream stream
  receives zero credit; successful paginated captures replace it;
- the earlier f6 and `196b3de` hosted PDF failures remain failures; passing subjobs from those
  runs are not transferred into this disposition;
- the `59e7451` hosted CI failure remains a failure; the exact `f1863d5` successor repairs only
  its declared frozen-documentation custody defect;
- the hosted rebuilt PDF bytes were not uploaded;
- KSG M1c remains open; and
- repeated downloads, local manifest replay, mechanism-diverse gates, and mutation families are
  not institutionally independent scientific replications or authenticity proofs.

The detailed precursor failures, exact-source and snapshot attacks, package-provider diagnostics,
Lean 4.32.2 bounded replay, and no-credit classifications remain in
[`c3-hosted-followup-correction-2026-08-01.md`](c3-hosted-followup-correction-2026-08-01.md). This
receipt does not erase or rebrand them.

## Scope of closure

The exact correction rooted at `8b792bc` now has a reviewed, unsigned, fast-forward subject and a
terminal all-green hosted run for exact `791a399`. That closes the C3 Noble/Lean-evidence
portability correction at its declared boundary.

Still open are exact custody of this erratum by a later qualifying descendant or external
immutable attestation, repository-wide Python verifier custody, KSG M1c, PID2 revision 4,
categorical MGW SxPID3 Programs A--E and all 108 coordinates, the research/process artifacts, and
the remaining formal, numerical, compiled, statistical, property/fuzz, coverage, security, SBOM,
identity, package, platform, Python, release, and authorized downstream decisions. No result maps
among KSG mutual information, Ehrlich continuous shared exclusions/PID, categorical MGW SxPID,
Williams--Beer `I_min`, fitted quantized PID, heuristics, or wrappers without a premise-explicit
mapping theorem.

KSG G1 remains open: this receipt is not the canonical M1a implementation anchor, its remote
verification, or its acyclic typed receipt. All 13 revision-4 integration gates remain open.

The machine-readable authority for the typed fields in this receipt is
[`c3-noble-hosted-receipt-2026-08-03.json`](c3-noble-hosted-receipt-2026-08-03.json).
