# KSG revision-4 M1a composite-v5 successor boundary

Status: **C5 contract definition; C4 is published; R4 is permanently unissued; R5 is pending a
fresh all-success qualification**  
Observation date: 18 August 2026  
Repository: `sepahead/pid-rs`

## Executive disposition

Published commit `da253576a5f76e99633fff4de5cf1118f967b90d` (tree
`916245b95f90bd98b8bd37a72e148fb9328d5c52`) is the exact composite-v4 C4 subject. Its local
closure passed before publication, but its first hosted qualification did not. CodeQL succeeded;
the dedicated composite-v4 workflow failed at the static-validation preflight, before substantive
contract validation completed; and the repository CI run
contained three terminal job failures. Therefore C4 is a published contract migration, **not** a
qualified hosted receipt subject. No R4 capture or receipt is issued, and the two reserved v4 paths
remain absent.

Composite-v5 is an append-only successor. C5 is an unsigned direct child of the published C4. It
retains the predecessor failure, repairs only the observed operational failure surfaces, publishes
a fresh Lean 4.33 replay as `r10`, and defines a new hosted route. A later R5 is permitted only if
the exact C5 commit passes local closure, CI, CodeQL, and the dedicated v5 workflow in fresh
attempt-1 runs. R5 then adds the successor capture and typed receipt and regenerates the
self-excluding source manifest.

This change adds **zero PID theories, zero PID functionals, zero estimators, zero theorem-source
changes, and zero numerical-result changes**. It does not validate KSG, shared-exclusions PID,
Wibral-authored claims, or any downstream application.

## The failed qualification is not a partial receipt

Define the C4 hosted qualification predicate

\[
Q_4 = \mathrm{CI}_4 \land \mathrm{CodeQL}_4 \land D_4,
\]

where each term means terminal success for the exact C4 commit on run attempt 1 and \(D_4\) is the
dedicated composite-v4 workflow. The observed values are

\[
\mathrm{CI}_4=\mathrm{false},\qquad
\mathrm{CodeQL}_4=\mathrm{true},\qquad
D_4=\mathrm{false}.
\]

Hence \(Q_4=\mathrm{false}\). The issuance rule is

\[
\mathrm{issue}(R4) \Longleftrightarrow Q_4.
\]

It follows that R4 is permanently unissued. A passing CodeQL route cannot compensate for failed CI
or a failed dedicated contract route. Rerunning the failed dedicated workflow would retain the same
run identifier with `run_attempt = 2`, which is outside the frozen v4 attempt-1 contract. Rewriting
C4 would destroy the published subject rather than repair it.

## Exact C4 hosted observations

| Role | Run | Observed disposition | Bounded interpretation |
|---|---:|---|---|
| Repository CI | `32079866560` | failed; three terminal job failures | C4 did not satisfy the all-jobs-success predicate |
| CodeQL | `32079865482` | passed for Actions, JavaScript/TypeScript, Python, and Rust | this satisfies only the CodeQL term |
| Dedicated composite-v4 | `32079866461` | failed at static-validation preflight | Substantive contract validation did not complete; the dedicated-v4 term is false |
| Dependency Graph | `32079867694` | passed | context only; neither a term in \(Q_4\) nor a captured qualification role |

The predecessor hosted capture is retained in C5 as failure evidence. Its existence does not grant
C4, C5, or R5 success credit. Provider responses and artifact archives are bounded observations;
they do not authenticate GitHub, prove a complete provider history, or establish scientific
validity.

## Four bounded repairs

### 1. Reviewed checkout residue

The pinned `actions/checkout` sequence disabled sparse checkout and unset
`extensions.worktreeConfig`, but left an inert `.git/config.worktree` byte image. The dedicated v4
checker correctly rejected the file's existence. C5 does not weaken that checker. Instead, a
separate normalizer accepts either absence or the one reviewed regular, single-link, mode-`0644`
byte image, verifies its exact size and SHA-256, unlinks that literal directory entry, and
requires absence afterward. A symlink, directory, hard link, altered bytes, altered permissions, or
route change fails closed.

The reviewed 83-byte image has SHA-256
`443a5f645c23c3d0c0aa09f634b2ad111d46ef61946b598a2fb311678ab47454`. Recognition of this byte
image is a narrow runner-compatibility rule, not a general permission to delete Git configuration.

### 2. Release-state fixture isolation

The C4 release-state self-test failed with an unlabelled `fatal: not a git repository` diagnostic.
The retained hosted log does not establish a unique causal line. C5 therefore does **not** claim a
proved one-line root cause. It removes the unsafe failure class: extracted-source tests are created
as separate `git archive` fixtures rather than moving the live fixture's `.git` directory away and
back. Every success path is phase-labelled. A hostile clean parent repository with the same release
tag demonstrates that an extracted tree cannot inherit an ancestor repository's tag state; local
tag inference is allowed only when the physical Git top level equals the physical source root.

This is a bounded structural repair plus a fresh hosted requalification requirement. A local pass
alone does not prove that the original runner failure is cured.

### 3. Zeta transfer-firewall binding

The bounded mathematical-workflow section changed only the reviewed spelling `un-certified` to
`uncertified`. Its current 37,869-byte section has SHA-256
`d1a1775dc38c04726b0c6f63feeb74e8f0d750e5fde8f3a76cdf041657d4d368`. C5 preserves the wording
and rebinds the exact section hash; it does not revert correct prose to satisfy a stale digest. The
existing otherwise-unreviewed-section mutation remains the causal negative control.

This rebind changes no category-theory result, PID transfer rule, theorem, or numerical result.

### 4. Certified-SxPID execution-container binding

The directed-rounding job reached its final claim checker after its Rust tests, exhaustive oracle,
independent verifier, exact-product checks, search, and Lean exact-log checks had passed. The claim
checker then rejected stale exact bindings for the release-audit dependency line and related current
execution/documentation containers. C5 rebinds the final reviewed bytes only after the v5 recipe,
documentation, and PDF gate are frozen. A hostile control preserves `certified-sxpid` membership
while changing only the dependency-line byte framing, so exact-line custody remains nonvacuous.

The repair does not upgrade the certificate's mathematical scope. In particular, it does not turn
a finite exact certifier into a population theorem, a Rust refinement proof, or a general validation
of shared-exclusions PID.

## Fresh C5 and R5 topology

C5 must be the exact unsigned, single-parent direct child of C4 with commit message
`Repair KSG M1a composite v5 contract`. R5, if permitted, must be the exact unsigned,
single-parent direct child of C5 with commit message
`Record KSG M1a composite v5 receipt`.

Define

\[
Q_5 = L_5 \land \mathrm{CI}_5 \land \mathrm{CodeQL}_5 \land D_5,
\]

where \(L_5\) is local static, hostile, replay, source-state, and publication closure;
\(\mathrm{CI}_5\) is repository-CI all-jobs success; \(\mathrm{CodeQL}_5\) is success of every
required CodeQL role; and \(D_5\) is success of the dedicated composite-v5 workflow. Every term
must be terminal at attempt 1 for the same exact C5 commit. The issuance rule is

\[
\mathrm{issue}(R5) \Longleftrightarrow Q_5.
\]

If any term is false, missing, nonterminal, attached to another commit, or from another run attempt,
R5 remains unissued and another append-only contract version is required. Passing a subset is not
partial qualification.

When \(Q_5\) is true, R5 has exactly three source changes:

1. add the raw successor-qualification hosted capture;
2. add the typed receipt derived from that capture; and
3. regenerate the self-excluding current-source manifest last.

The receipt hashes both the predecessor-failure capture retained in C5 and the
successor-qualification capture added in R5. The manifest inventories both R5 additions while
excluding itself. The R5 tree and commit are outputs, never checksum inputs.

## Replay and non-conflation boundary

C5 publishes a fresh Lean 4.33 replay as `r10`; the accepted C4 `r9` remains exact-hash-bound prior
execution evidence. The suffix `r10` denotes the tenth receipt in the versioned sequence that began
on 12 August and the eleventh current-project replay receipt overall because the separate 11 August
historical receipt remains outside that sequence. This numbering is custody metadata, not a theorem
revision, proof-strength ranking, or independence claim.

The r10 replay checks the same bounded theorem inventory under the final C5 operational bytes. It
does not adjudicate hosted success, KSG estimator quality, PID validity, source authenticity, or
scientific novelty. C5's Git tree binds the v5 machinery; the v5 checker validates r10. No cyclic
claim that r10 independently authenticates the checker is made.

## Durable publication and recovery

The minimum operational recovery anchor is an exact C5 or R5 commit reachable from reviewed remote
`main`, with its remote URL, ref, commit OID, tree OID, parent, and push observation recorded. Remote
`main` is mutable and depends on provider retention and history-rewrite controls; it is not an
immutable scholarly archive. A publication freeze should additionally retain the exact commit and
load-bearing evidence in a versioned release or recognized content-addressed scholarly archive,
with access, licence, retention, and retrieval checks recorded.

A digest without a retrievable preimage provides commitment or bounded-omission credit only. The
predecessor and successor captures, typed receipt, visual-review receipt, report source, figure
source, rendered PDF, replay receipt, path policy, and current-source manifest are load-bearing C5
or R5 artifacts and must be reachable from the corresponding published commit. Scratch renders,
package caches, and routine rejected intermediates are not promoted merely because they existed.

No branch, worktree, or temporary directory is deleted until exact-byte or semantic supersession is
proved and every unique permitted payload has a remote or otherwise independent durable home.

## Review protocol and nonclaims

The C5 boundary is reviewed through separate lenses for logical implication, Git topology, hosted
semantics, schema closure, adversarial-test causality, Python isolation, shell failure handling,
Lean replay custody, PDF object structure, raster layout, SVG accessibility, numerical scope,
method provenance, PID-family separation, security, privacy, durability, reproducibility,
operator usability, and publication English. Disagreement is retained until adjudicated; a digest
alone does not preserve a minority report.

A separate correlated agent red-team found and corrected the original C4-to-R4-to-C5 topology,
run-status language, permission claim, incomplete \(Q_5\) definitions, dual-capture binding, and
durability-field omissions. This records review provenance but grants no dependency-disjoint,
independent, or human-review credit.

This process can prevent known classes of evidence and publication error. It does not demonstrate a
causal improvement in research quality, replace peer review, or make the research process itself
publishable. A scoped methods report is eligible for publication consideration only when its exact
attempt population, adaptive exposures, stopping and selection rules, deviations, failures,
inconclusive results, resource and AI roles, council dissent, human adjudication, materials, access,
and licences are disclosed. Eligibility is necessary, not sufficient.

Neither this record nor any linked checker implies:

- a new PID or KSG theory, estimator, theorem, or numerical result;
- transfer among categorical MGW, Schick-Poland, Ehrlich continuous shared exclusions, KSG mutual
  information, Williams-Beer `I_min`, PID2, PID3, quantized, or mixed-support routes;
- authentication, attestation, authorship, independence, peer review, or provider completeness;
- reproducibility outside the stated byte, toolchain, cache, platform, and capture boundaries; or
- safety, control authority, application fitness, or evidence for a drone or other ecosystem
  deployment.
