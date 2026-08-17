# KSG revision-4 M1a composite-v4 evidence process

Status: C4 contract definition; active only at an exact validating C4; R4 observation receipt
pending and unissued; project-defined process evidence only

## Decision

The composite-v3 receipt is not issued. Its frozen executable contract requires the four CodeQL
analyses to appear both in the fixed semantic language order
`actions, javascript-typescript, python, rust` and in increasing `analysis_id` order. The exact
successful recovery run has IDs `1617732991, 1617732745, 1617735963, 1617735749` in that language
order. They are positive and unique, but not increasing. Reordering rows would violate the
language contract; reassigning IDs would falsify provider observations.

The v3 direct-child topology has a second, separately sufficient contradiction. It permits exactly
three
added paths: the receipt and two historical index payloads. The repository-wide current-source
gate inventories every repository-visible source path except its own manifest. Adding three paths
therefore requires modifying that manifest. A three-addition child has a stale manifest; a
three-addition-plus-manifest-modification child violates v3's exact delta.

Both contradictions are preserved in
`ksg-rev4-m1a-composite-v3-impossibility-2026-08-15.json`. The v3 checker, self-test, and schema
remain unchanged, and the reserved receipt path remains absent. This is a contract revision, not a
retroactive repair.

## First-principles evidence model

The durable subjects are Git commits, trees, blobs, canonical source-state manifests, provider
responses, and downloaded artifact bytes. A Git index is mutable local implementation state. Its
historical byte image can be useful custody evidence while retained, but it is not needed to
identify the committed tree and must not become a permanent scientific dependency.

The exact correction and recovery index bytes are no longer available to this process. Their recorded sizes and
SHA-256 values remain historical observations, but v4 neither reconstructs nor substitutes a
different index. V4 instead rehashes the Git commit/tree/blob graph and binds the sealed-index
trailers as non-self-authenticating historical metadata. This deliberately narrows the claim to
evidence that can still be reproduced.

Provider identifiers are opaque. V4 uses one canonical semantic order for CodeQL analyses:
`actions, javascript-typescript, python, rust`. It requires exact language/category and job-name
matches and positive, globally unique analysis IDs, but makes no monotonicity or
provider-response-order claim.

GitHub's code-scanning alert endpoints expose repository-level current state, not alerts
foreign-keyed to a workflow run and not a reconstruction of alert state during that run. The
recovery and C4 role labels group when those endpoint bytes were captured; they do not create a
run-to-alert relation. V4 deliberately requires the resulting current-state partition to equal the
retained 191-alert baseline as an operational admission condition. That equality is neither a
causal attribution to either run nor evidence about PID mathematics.

## Two-commit topology

### C4: contract migration

C4 is an unsigned, single-parent direct child of recovery commit
`bc3aa80fb6025e709c2906a08bce25a4fac40578`.
It adds the v4 checker, self-test, schemas, workflow, counterexample, process publication, and path
policy; updates only bounded operational custody gates, schemas, documentation, and the prospective
research-integrity workflow publication; appends a separately scoped current-project Lean
replay/reseal after those operational changes; and regenerates the self-excluding current-source
manifest last. No KSG/PID theorem statement, scientific-object definition, numerical result, or
disposition changes, and composite-v4 derives no KSG/PID credit from that replay. C4 binds the
authored research-method bytes but neither the v4
checker, hosted runs, nor Lean replay adjudicates the external-source observations or proves that
the prospective protocol was adopted. It contains no v4 receipt and claims no hosted success for
itself before the runs exist.

### Rejected local pre-publication replay attempt

Before any C4 push, the first one-shot local `r9` execution and its receipt-finalization predicates
passed. The emitted canonical schema-v2 document has internal `status = passed`; this is bounded
execution-custody evidence only. The containing C4 static check then rejected publication. For the
same 748 sorted entries, the current-source generator hashed 132,893 bytes of newline-free compact
JSON to
`b336e6f54450090693731f2391b1ef3e112095dd9a9c8cbdadddbf2f855fba47`, while the first
composite checker hashed 132,894 bytes including one terminal line feed to
`7d4d4fd6bc478aeb20008cd05d1efe4b92b6ca9fd72a72043e67322e6a722f20`.

Local commit `e02d27bec91f142949336f9f28550c672d22b297` was never pushed or accepted as C4.
The candidate receives no C4-publication, hosted, scientific, accepted-current-replay, or
independence credit. Its exact 132,710 bytes are retained without alteration at
`audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-15-r9-prepublication-closure-rejected-2026-08-17.json`
with SHA-256
`fb162cc40da3059b61eab9024f4aa38cf6daf2d84ef7e1d8a26dc7d345291e70`.
The corrected checker adopts the generator's already-published newline-free compact framing and
requires a fresh one-shot replay. The accepted `r9` slot may be filled only by a subsequent fresh
attempt over the complete corrected static-and-hostile surface, and it must bind the rejected bytes
as retained pre-publication closure evidence outside the accepted replay lineage; the rejected
document is not renumbered or relabelled as the current receipt. This publication preserves the
exact rejected replay and measured framing facts; it does not represent the rejected local C4
object as a published commit.

#### Withdrawn local pre-publication replay after a stale hostile fixture

After the compact-framing repair, a fresh local replay ran from
`2026-08-17T21:20:16.677815Z` through `2026-08-17T21:36:37.989770Z` and emitted a 132,912-byte
canonical schema-v2 document with internal `status = passed` and SHA-256
`6d5068a2ade251b4ea005e847b78be656bb7697b14ae2e6d8a644d521f09e2cb` (local Git blob
`3d83a833401160f8e980690b0f5d11cef5dfca19`). It bound composite checker SHA-256
`8640bbe11fa37011921291c719fd50bb02ac1baaf945219a4e723f46ddc7d106`. The reported local Lean
execution, receipt finalization, 114-mutation suite, and composite static checker in normal and
optimized modes passed. Before any push, the complete
composite self-test stopped publication: its
`3f965f442fa925cd17aa466f5fee3b24207c3d2eaf98b74801c2102d48563642` fixture incorrectly
classified identical ZIP bytes delivered once directly and once through an individually safe
redirect as inconsistent. The schema and capture tool permit either delivery per request; the raw
capture hash retains the route, while repetition equality deliberately compares normalized
provider semantics.

The corrected self-test, SHA-256
`4a40f43396e5b45aa0a5762995eabb908b61d850b1a215aa817c731140a6078b`, uses mixed direct/safe
redirect delivery as a positive and rejects a forbidden redirect host. It also makes the
repetition and duplicate-response mutations reach their named predicates rather than an earlier
workflow-name or malformed-ZIP check. Host-local commit
`f6d76c1d01a040f74ea55277a5ba835b32fdb6ab` with tree
`f5c306ab982d84d84fa47a9b4f38407bc0f843a4` and parent
`bc3aa80fb6025e709c2906a08bce25a4fac40578` was never pushed or accepted as C4; those local object
identities are neither a durable locator nor authentication. The candidate was not promoted or
selected and receives no C4-publication, hosted, scientific, accepted-current-replay, selection,
or independence credit. Reuse or relabelling is forbidden.

C4 retains this exact identity, disposition, and omission record, but deliberately omits the
second raw preimage; its digest alone provides neither recovery nor reproducibility. Unlike the
first retained rejected document, whose byte framing is the decisive closure witness, this second
document neither caused nor diagnosed the failure; the stale fixture and corrected causal negative
are the decisive artifacts. Reopening requires frozen corrected bytes, complete normal/optimized
static and hostile-suite success, a fresh one-shot replay, current-source regeneration last, and a
newly validated exact C4.

### R4: observation receipt

R4 is an unsigned, single-parent direct child of C4. Its scientific delta is empty. Its source
delta is exactly:

1. add the canonical, byte-retaining hosted-capture bundle;
2. add the canonical typed v4 receipt derived from that bundle; and
3. modify the self-excluding current-source manifest so it inventories both additions.

The receipt hashes the capture bundle but does not hash itself, the regenerated manifest, the R4
tree, or the R4 commit. The checker derives those identities from Git. This removes the checksum
cycle without exempting either new evidence object from source-state custody.

## Hosted capture protocol

The receipt retains two separately fetched byte captures for every load-bearing endpoint.
Each logical response records the exact request path, page number, response-byte SHA-256, byte
count, and base64 payload. A validator parses each repetition separately, rejects duplicate
IDs and duplicate or missing terminal pages, and requires equal normalized projections before it
uses a value.

The bounded capture set is:

- recovery CI run, all job/step pages, artifact pages, and every exact artifact ZIP;
- recovery CodeQL run, all job pages, exact-head analyses, and open/dismissed/fixed alert pages;
- C4 CI run, all job/step and artifact pages, and every exact artifact ZIP;
- C4 CodeQL run, all job pages, exact-head analyses, and all three alert states; and
- the dedicated composite-v4 workflow run, all job/step and artifact pages, and its exact static
  validation ZIP.

The complete capture document and every individual decoded response are bounded. Redirects are
followed only from the GitHub API artifact endpoint to a reviewed HTTPS artifact-host suffix; the
authorization header is stripped, ambient proxies are disabled, and only the redirect status,
target host, and SHA-256 of the full target URL are retained. Signed target URLs are never written.

Capture time, authentication, provider identity, and network completeness beyond the named
endpoints remain unclaimed. A failed, partial, terminally rate-limited, or semantically
inconsistent fetch produces no receipt.

### Executable C4-to-R4 capture route

Run this route only from an exact clean C4 after the C4 CI, CodeQL, and dedicated workflow runs are
terminal. The caller opens the GitHub token read-only on descriptor 3; the token never appears in
argv or a retained artifact. `C4`, `C4_TREE`, and the three run variables are exact observed
identifiers, not values inferred by the capture tool. The temporary parent is resolved and rejected
if it lies inside the repository. A nonzero producer exit deletes its partial standard output.

```text
set -eu
repo_root=$(pwd -P)
: "${C4:?set exact C4 commit}"
: "${C4_TREE:?set exact C4 tree}"
: "${MIGRATION_CI_RUN:?set exact C4 CI run}"
: "${MIGRATION_CODEQL_RUN:?set exact C4 CodeQL run}"
: "${MIGRATION_CONTRACT_RUN:?set exact dedicated-workflow run}"
temp_parent=$(cd "${TMPDIR:-/tmp}" && pwd -P)
case "$temp_parent/" in "$repo_root/"*) exit 2 ;; esac
capture_root=$(mktemp -d "$temp_parent/pid-rs-ksg-v4-capture.XXXXXX")
chmod 700 "$capture_root"
umask 077

capture_tmp="$capture_root/capture.json.tmp"
capture="$capture_root/capture.json"
if python3 -I -S -B scripts/capture-ksg-m1a-composite-v4.py \
    --contract-commit "$C4" --contract-tree "$C4_TREE" \
    --migration-ci-run "$MIGRATION_CI_RUN" \
    --migration-codeql-run "$MIGRATION_CODEQL_RUN" \
    --migration-contract-run "$MIGRATION_CONTRACT_RUN" --token-fd 3 \
    >"$capture_tmp"; then
  mv "$capture_tmp" "$capture"
else
  status=$?
  rm -f -- "$capture_tmp"
  exit "$status"
fi
exec 3<&-

receipt_tmp="$capture_root/receipt.json.tmp"
receipt="$capture_root/receipt.json"
if python3 -I -S -B scripts/check-ksg-m1a-composite-v4.py --derive-receipt \
    <"$capture" >"$receipt_tmp"; then
  mv "$receipt_tmp" "$receipt"
else
  status=$?
  rm -f -- "$receipt_tmp"
  exit "$status"
fi

install -m 0644 "$capture" \
  audit/evidence/.ksg-rev4-m1a-composite-hosted-capture-v4-2026-08-15.json.tmp
mv audit/evidence/.ksg-rev4-m1a-composite-hosted-capture-v4-2026-08-15.json.tmp \
  audit/evidence/ksg-rev4-m1a-composite-hosted-capture-v4-2026-08-15.json
install -m 0644 "$receipt" \
  audit/evidence/.ksg-rev4-m1a-composite-receipt-v4-2026-08-15.json.tmp
mv audit/evidence/.ksg-rev4-m1a-composite-receipt-v4-2026-08-15.json.tmp \
  audit/evidence/ksg-rev4-m1a-composite-receipt-v4-2026-08-15.json
source_state_tmp="$capture_root/current-source-state-v1.json.tmp"
if python3 -I -S -B scripts/check-current-source-state-v1.py --emit \
    >"$source_state_tmp"; then
  install -m 0644 "$source_state_tmp" \
    audit/evidence/.current-source-state-v1.json.tmp
else
  status=$?
  rm -f -- "$source_state_tmp"
  exit "$status"
fi
mv audit/evidence/.current-source-state-v1.json.tmp \
  audit/evidence/current-source-state-v1.json
```

The resulting worktree must have exactly the three R4 paths declared above. After an unsigned,
single-parent R4 with exact message `Record KSG M1a composite v4 receipt`, validate the committed
receipt from standard input in both modes:

```text
python3 -I -S -B scripts/check-ksg-m1a-composite-v4.py --validate-receipt \
  <audit/evidence/ksg-rev4-m1a-composite-receipt-v4-2026-08-15.json
python3 -O -I -S -B scripts/check-ksg-m1a-composite-v4.py --validate-receipt \
  <audit/evidence/ksg-rev4-m1a-composite-receipt-v4-2026-08-15.json
```

The temporary directory is not evidence. Remove it only after the committed blobs and validation
receipts have been separately identified; a failed or interrupted route receives no hosted
observation credit.

## Validation layers

1. Strict JSON: the outer capture, receipt, counterexample, policy, and source-state artifacts use
   exact canonical serialization. Retained provider JSON is preserved byte-for-byte and parsed as
   strict UTF-8 with duplicate-key, floating-point, non-finite, depth, and integer-width rejection;
   provider formatting itself is not claimed canonical.
2. Schema: closed key inventories and exact types for the portable receipt surface.
3. Semantics: exact subject chain, run/head/tree/workflow identities, terminal job and step states,
   fixed CodeQL language order, opaque unique IDs, alert partitions, and artifact content joins.
4. Git: in-process SHA-1 rehash of raw commit, tree, and blob objects separate from Git-reported
   object IDs; unsigned single-parent C4/R4 envelopes; exact C4 and R4 deltas; current-source
   reproduction; and exact byte retention, in every checked post-R4 descendant, of the
   v4-authority paths explicitly enumerated by the checker. Other C4 paths remain historically
   bound by the C4 tree and r9 map; a later version must be recorded by a truthfully regenerated
   current-source manifest rather than being mistaken for the original bytes.
5. Mutation controls: executable negatives cover repeated-observation mismatch, missing and
   duplicate pages, decoded-row and aggregate-body bounds, retry misjoins,
   run/repository/attempt drift, exact job and
   dedicated-step rosters, artifact duplication/digest/member substitution, analysis path/body,
   category/job-name joins, within- and cross-role identifier uniqueness, alert overlap,
   post-commit tree binding, raw-capture-to-receipt
   binding, unauthorized outer fields, unsafe artifact redirects, and PID-boundary drift. Mixed
   direct and individually safe redirected delivery of identical ZIP bytes is a positive transport
   variation, not a semantic mismatch. The two v3 contradictions and
   current-source reconstruction are separately exact static predicates, not mislabeled as hosted
   provider mutations.
6. Runtime parity: the dedicated hosted workflow requires byte-identical normal and optimized
   Python 3.11 dispositions. Broader project Python-minor coverage remains a separate CI surface;
   this receipt does not imply that the v4 checker ran on every supported minor. CI success is
   necessary for the process milestone but does not create scientific evidence.

A fully coordinated fabricated capture and matching receipt that satisfy every declared predicate
cannot be detected without a separately authenticated external anchor. The contract therefore
claims deterministic validation of retained observations, not authentication of their origin. The
typed analysis-to-job field is explicitly a language-category and job-name match; GitHub exposes
no provider analysis-to-job foreign key in these responses.

## Scientific-object firewall

This process concerns custody for one KSG M1a implementation lineage. It does not establish KSG
estimator correctness, source-to-paper correspondence, statistical calibration, or application
fitness. It establishes nothing about the categorical MGW pointwise functional, Schick-Poland's
general construction, Ehrlich's analytic continuous functional or kNN estimator, PID2/PID3
algebraic compositions, Williams-Beer `I_min`, fitted quantized routes, resampling methods,
infomorphic objectives, or any consumer application.

Every later scientific claim must still name its paper and revision, estimand, support/domain,
sample role, units, implementation route, estimator/evaluator distinction, evidence class, and
open mapping edges. Shared names, shared code, or a green workflow never authorize cross-PID
transfer.

Model/agent suggestions, proof candidates, model-labelled judge outputs, and generated
certificates receive no scientific credit in C4/R4. Research/scientific or claim-adjudicating
attempts opened after this policy revision must satisfy the prospective candidate/judge controls in
`AGENTS.md` through a pre-candidate object-specific task packet and an append-only attempt ledger
covering failed and unselected attempts as well as selected successes. C4/R4 contains no
such scientific packet and makes no claim that earlier proofs or certificates complied with that
protocol.

## Research-queue non-evidence

Deferral is not scientific rejection, but this KSG custody migration does **not** preserve or
validate unrelated dirty-overlay payloads. A separate read-only work-item inventory reported a
PID2 revision-3 exact-binary64/oracle candidate and a categorical SxPID3 Program-A
specification/counterexample candidate. Their bytes are not retained by C4 or R4, so neither the
reported fixture counts nor the proposed obligations are preservation evidence here. They remain
explicit future research items until an append-only, hash-bound intake records the exact payload,
provenance, symbol mapping, open obligations, and an explicit `absent` or `unknown` disposition for
any historical pre-candidate packet, judge, attempt ledger, and selection rule. That intake grants
no retroactive compliance credit. Every new attempt requires a newly frozen task packet, pre-bound
judge/verifier, append-only attempt ledger, and separately scoped validation with declared
independence dimensions. Those bytes are absent from C4/R4. The candidates must never be
merged into KSG evidence or used to transfer a result between PID definitions or estimators.

## Reproduction checklist

- verify exact `bc3aa80...` ancestry and frozen v3 hashes;
- run the v4 static checker and self-test under normal and optimized isolated Python;
- require the dedicated hosted job to contain exactly one static-validation step, one adversarial
  self-test step, and one static-artifact upload step; provider-injected setup steps are not treated
  as substitutes;
- rebuild this PDF from its committed TeX source with shell escape disabled;
- render every PDF page and inspect for clipping, overlap, missing glyphs, and broken links;
- generate the next Lean replay only after all operational bytes settle and the generator proves
  the unique zero projection placeholder, the two identical final composite-checker cuts, and the
  normalized three-placeholder Lean digest before launching any replay command;
- regenerate current-source last and deterministically reconstruct its containing-tree projection;
- build and inspect the exact C4 tree before an unsigned fast-forward push;
- require exact-SHA CI, CodeQL, and dedicated v4 workflow success;
- capture provider bytes twice and build R4 only after those runs are terminal;
- validate R4 in clean detached and attached states, push fast-forward, and monitor exact-SHA
  hosted results; and
- keep KSG revision 4 `integration_no_go` until the distinct M1c scientific packet closes every
  named gate.

## Nonclaims

- No v3 receipt is issued in the checked lineage; the reserved path remains absent from C4/R4.
- No historical index payload has been recovered.
- No provider response authenticates itself.
- No process receipt is a theorem, estimator validation, peer review, release, or novelty claim.
- A separate model call or model-labelled judge is not independent review. Composite-v4 does not
  claim that earlier proofs, certificates, or model runs followed the prospective candidate/judge
  protocol.
- No PID result transfers across categorical, continuous, quantized, mixed-support, two-source,
  three-source, pointwise, averaged, estimator, evaluator, or objective-composition boundaries.
