# C3 post-correction hosted receipt

- **Receipt date:** 6 August 2026
- **Exact subject:** `dbd3984adab1547dccd87690f2e5582b65fbd206`
- **Exact-subject CI:** 45/45 jobs completed successfully
- **Exact-subject CodeQL:** 4/4 jobs completed successfully
- **Disposition:** **bounded C3 engineering chain closed, with security follow-up explicitly open**
- **Scientific credit:** none
- **Machine companion:**
  `audit/evidence/c3-post-correction-hosted-receipt-2026-08-06.json`, 27,880 bytes,
  SHA-256 `412bd80d1908cb61bc9ce6af9a5be499c69fd04b18c21ddea38999fd82518932`

The machine companion is the typed authority for the values summarized here. It does not hash
itself or this Markdown. It leaves the future receipt commit, tree, and receipt-blob identities
null and requires that future commit to have `dbd3984…` as its direct parent. This is intentional:
hosted observations about a pre-existing subject cannot authenticate receipt bytes that were not
in that subject. The machine receipt also cannot establish custody of its own future commit; that
identity requires a later strict descendant or a separately retained external observation.

The JSON serialization contract is UTF-8, LF line endings, two-space indentation, one final
newline, unique keys, and no non-finite numeric constants. Field order is repository-defined rather
than lexicographically sorted, so no general canonical-JSON claim is made.

## Result and exact boundary

The bounded engineering conjunction is now true:

1. `dbd3984…` is the unsigned, single-parent correction of exact parent `dc50e0a…`, with tree
   `72b35f9…` and exactly three modified paths;
2. its complete CI workflow is the scanner-corrected workflow at SHA-256 `07c6e514…`, and the
   certified-SxPID2 checker binds that complete workflow while retaining the unchanged certified-job
   projection `3a31891c…`;
3. [CI run `31112402374`](https://github.com/sepahead/pid-rs/actions/runs/31112402374), attempt 1,
   reached terminal success with 45/45 uniquely named, uniquely identified jobs at exact head
   `dbd3984…`;
4. separate [CodeQL run `31112399699`](https://github.com/sepahead/pid-rs/actions/runs/31112399699)
   reached terminal success with 4/4 jobs at the same exact head;
5. duplicate run, job, and Git-commit API captures were byte-identical and then sealed read-only in
   a private local capture; and
6. both earlier non-green successor runs, every local correction negative, and the credential-
   handling incident remain negative evidence rather than being rewritten as successes.

This closes the exact-subject C3 engineering correction chain descended from
`8b792bc143fff2d84f2d8e7817d1de7850741223`. It does **not** establish security cleanliness.
Credential rotation or revocation was not observed and remains an external follow-up if it has not
already happened. The wider scientific program remains open.

## Local subject and alternate-index custody

A second, untouched audit worktree was created at
`/private/tmp/pid-rs-c3-dbd-clean-audit.cFUQXv/worktree`. Its `HEAD` and tree re-derived
`dbd3984…` and `72b35f9…`, and its porcelain status had zero bytes. This is a sequential local
cleanliness observation, not an atomic snapshot or an authentication claim. The heavily dirty
primary checkout and other worktrees were not modified.

The original alternate index used to construct the `dbd3984…` subject had been reported by the
prior session as 71,800 bytes, mode 0400, one link, and SHA-256 `d5d817b0…`. Its reported path is
now absent, the raw bytes cannot be rehashed, and the value was not committed into the subject
tree. Continuous historical raw-index custody is therefore **not** claimed.

Instead, a new task-specific alternate index was derived from the exact subject before this receipt
was written. Before sealing, `git write-tree` returned `72b35f9…`. The original was then made mode
0400 and never reopened by Git; two copies independently returned the same semantic tree. The
sealed rederived index is 71,800 bytes, one link, SHA-256 `5b5eac62…`. Its 596-entry, 59,815-byte
stage manifest is mode 0400 at SHA-256 `cc8307d2…`. This proves a fresh exact-subject index
rederivation under the stated local process. It does not turn index bytes into a canonical Git-tree
property, restore the missing historical index, provide remote durability, or resist same-UID or
privileged mutation. The future receipt-commit index is deliberately still null at this acyclic
stage.

## Why two correction descendants were necessary

The first receipt commit, `410a347…`, introduced the earlier exact format-custody receipt,
but its full-history secret-scan job failed on two receipt fields containing public API-response
digests. The narrow correction `dc50e0a…` added a path-and-field-shape exception and expanded the
policy self-test. That changed the complete workflow bytes without changing the certified-SxPID2
job slice. The certified checker intentionally hashes both the narrow job slice and the enclosing
workflow, so run `31108555449` failed closed on the stale whole-workflow digest. `dbd3984…` updates
only that enclosing digest plus changelog/resume state.

Those two specific gates failed closed on those exact inputs; the observation is not a general gate
validation result and is not evidence that the failures were flaky. The
final subject changes no estimator, theorem, numerical fixture, PID atom, statistical method, TeX
source, figure, font, or retained PDF. No PDF was rebuilt because there was no PDF input change;
artificial PDF churn would create unrelated bytes without repairing either custody edge.

## Terminal hosted observations

The CI run was created and started at `2026-08-06T14:45:13Z` and reached its terminal API update at
`2026-08-06T16:02:53Z`. The jobs API reports exactly 45 completed/successful jobs, no other
conclusion, and one distinct head SHA: `dbd3984…`. Two 12,104-byte run captures are byte-identical
at SHA-256 `318f378d…`; two 144,755-byte jobs captures are byte-identical at SHA-256
`c0f6366c…`.

The CodeQL run was created and started at `2026-08-06T14:45:11Z` and reached its terminal API
update at `2026-08-06T14:47:45Z`. Its jobs API reports exactly four completed/successful jobs at
the same head. Duplicate run captures are 12,098 bytes at SHA-256 `b1a8b2ab…`; duplicate jobs
captures are 10,032 bytes at SHA-256 `5b4d0e62…`.

The following archive boundary is receipt-wide and sits outside both the CI and CodeQL run records.
No complete valid hosted log ZIP, artifact, SARIF, coverage file, SBOM, or step transcript was
retained or used as evidence for this receipt. N008 separately records the earlier authenticated
attempt that wrote three partial invalid CodeQL ZIPs; that failed attempt is not attributed to
either terminal run. The partial files are absent from the replacement capture and receive no
archive or log-content credit. Accordingly, this receipt makes no log-text, step-count, test-count,
warning-count, coverage-content, SBOM-content, artifact-content, alert-inventory, or extractor-
completeness claim. API success also does not authenticate GitHub, runners, actions, operating
systems, toolchains, hardware, or network services.

## Retained hosted negatives

Run [`31104508451`](https://github.com/sepahead/pid-rs/actions/runs/31104508451) at exact head
`410a347…` is terminal `cancelled`: 43 jobs succeeded, the full-history secret scan failed, and the
long KSG job was cancelled. Its paired CodeQL run succeeded 4/4; that cannot override the CI
failure. Run [`31108555449`](https://github.com/sepahead/pid-rs/actions/runs/31108555449) at exact
head `dc50e0a…` is likewise terminal `cancelled`: 43 jobs succeeded, the directed-rounding SxPID2
job failed closed on the stale enclosing workflow digest, and the KSG job was cancelled. Its paired
CodeQL run also succeeded 4/4 and likewise does not override the CI failure.

The machine companion retains the duplicate API hashes for those four predecessor CI/CodeQL runs.
Neither cancelled KSG job receives partial closure credit, and neither failed run is retrospectively
green.

The local negative ledger also preserves:

- an interrupted all-reference secret scan whose private-ref scope did not match a fresh hosted
  checkout;
- a malformed patch invocation that changed no file;
- a stale detached-worktree ordinary index that was refreshed without changing committed or
  working bytes;
- a malformed zsh refspec rejected before remote mutation, including rejected commit
  `b901ef2…`;
- a JavaScript interpolation error that launched no shell process;
- a zsh tuple-validation loop that failed before predecessor adjudication and was replaced by two
  explicit successful predicates; and
- an interrupted orchestration turn after the new isolated worktree had already been created; a
  later process-name-only check found no Git process and the exact-subject worktree was clean; and
- a redacted pre-commit gitleaks scan that classified eight public predecessor API-digest fields as
  generic API keys. The receipt schema was repaired by nesting those digests under typed capture
  objects; no allowlist was broadened, and the failed scan receives no credit; and
- loss of the original final subject-commit index path. The fresh exact-subject rederivation receives
  only present-time semantic-tree credit and does not retroactively repair continuous raw-index
  custody.

Every failed or missing historical route receives zero positive credit. The N013 repair receives
only bounded present-time semantic-tree rederivation credit; it does not receive historical
raw-index custody credit.

Receipt review itself also produced retained negatives. Requested reviews of the 18,407-byte
`fbf079bc…` / 10,402-byte `68845687…` pair and the 21,446-byte `a8342386…` /
12,474-byte `95a04694…` pair were invalidated by intentional candidate mutation before final
adjudication and receive no exact-byte review credit (`C3-POST-N014`). The first completed frozen-
pair review then returned NO-GO for the 22,113-byte `118e6fd1…` / 13,083-byte `2374679c…` pair
(`C3-POST-N015`). It found the N013 credit contradiction and the overbroad provider authentication-
state nonmutation claim. Those defects, plus three wording generalizations, were repaired; the
rejected pair remains zero credit.

The three precision narrowings were: (1) “correctly described” became the factual “introduced the
earlier exact format-custody receipt”; (2) general “evidence of the gates working” became the
bounded observation that two specific gates failed closed on exact inputs without general gate-
validation credit; and (3) prepublication “the committed receipt preserves” became conditional
“if committed, these receipt bytes preserve.”

The next 22,324-byte `0d391668…` / 13,419-byte `d4521990…` pair received one bounded GO, but a
second reviewer withheld adjudication because those earlier review negatives were not yet retained
inside the candidate (`C3-POST-N016`). N014--N015 now bind them explicitly. The superseded GO does
not transfer to these later bytes.

The subsequent 24,896-byte `9f3f4eae…` / 14,452-byte `23b2e3c0…` pair received exact-byte NO-GO
from two reviewers (`C3-POST-N017`): N015 counted those three narrowings without identifying them,
and the receipt incorrectly said no hosted log ZIP was downloaded despite N008's three partial
invalid ZIP writes. The typed array and this mirror now retain all three narrowings; the log
boundary now says no complete valid archive was retained or used while affirming the failed partial
attempt. The rejected pair remains zero credit.

The next 26,684-byte `c23e115c…` / 15,666-byte `61c3bc4b…` pair received one bounded GO and one
exact-byte NO-GO (`C3-POST-N018`). Receipt-wide facts about the failed partial CodeQL archive
attempt were nested inside the terminal CI object, so object containment could ambiguously
attribute that attempt to CI run `31112402374`. The repair moves those facts into the top-level
`hosted_evidence_capture_boundary`, explicitly outside both hosted run records; each run now carries
only its own scoped nonclaims. The superseded GO does not transfer and the rejected pair remains
zero credit.

## Honest security receipt

During an earlier attempt to acquire a read-only authenticated log archive, a credential was
expanded into the downloader process argument vector. A later process-status check printed that
argument vector into an internal tool transcript. This receipt deliberately stores neither the
secret value nor a digest of it.

The bounded incident audit observed all four known processes terminated or absent. In the private
capture root that then existed, 95 paths were enumerated and a strict scan found zero token-shaped
or populated-authorization credential matches. Nineteen generic `Authorization:` markers appeared
in pre-existing CI logs, but none matched the strict credential shape and no matching bytes were
printed. A primary-worktree scan enumerated 1,109,780 paths before being cancelled as
disproportionate; it is incomplete and receives no credit. Three partial invalid CodeQL ZIPs were
the only files written by that diagnostic sequence, all inside the then-existing private root. No
repository file, Git object, commit, push, or remote repository state was changed. The
contemporaneous audit also reported no credential rotation/revocation or local credential-file or
configuration mutation. It did not inspect provider-side audit, last-used, rate-limit, or other
authentication-related state, which an authenticated GET may affect.

That earlier private incident-capture root was absent when this receipt was constructed. The
95-path scan is therefore retained historical operational evidence, not a current re-inspection or
durable-archive claim. No credential rotation or revocation was performed by the repository work,
and no later authentication-state proof was available. If the affected credential has not already
been rotated or revoked, that action and an independent confirmation remain required outside this
repository.

Consequently:

- `security_clean_claim = false`;
- `credential_noncompromise_claim = false`;
- `incident_complete_containment_claim = false`; and
- green CodeQL and secret-scan job conclusions are recorded only as exact hosted-job observations.

## Current capture custody

The replacement API-only capture contains 26 JSON files totalling 1,075,330 bytes. Every endpoint
was downloaded twice and each pair is byte-identical. The files are mode 0400 under a mode-0500
private directory. Its 2,516-byte manifest is mode 0400, one link, and SHA-256
`1ade57d0d52617b6adb3e197d4d5b5ed8c12deebb8052a482a64c14fda1d8c67`.

A finite four-pattern scan of all 27 capture files found zero strict token-shaped, bearer,
populated-authorization, or URL-credential matches. That result is scoped to those exact files and
patterns and receives no security-clean or credential-containment credit.

Those modes and hashes are sequential local observations. They are not remote durability,
publisher authentication, an atomic snapshot, tamper-proof sealing, a transparency log, or a
defence against privileged or same-UID mutation. If committed, these receipt bytes preserve the
typed values even if the private capture later disappears; they do not preserve the raw API bytes
themselves.

## Scientific and release firewall

Nothing in this receipt transfers to KSG estimation, Ehrlich continuous shared-exclusions PID,
categorical Makkeh--Gutknecht--Wibral SxPID, Williams--Beer `I_min`, fitted quantized PID,
heuristics, or wrappers. There is no mapping theorem here and no scientific result is claimed.

In particular, this receipt does not close fixed-Lean replay after issue 14576, repository-wide
Python verifier custody, KSG M1c, PID2 revision 4, categorical MGW SxPID3 Programs A--E or all 108
coordinates, frontier mathematics, publication artifacts, release readiness, or downstream
authorization. Those remain separately typed obligations.

## Review boundary

At machine-receipt finalization, exact-byte independent review was still pending. A separately
prompted review must bind the final JSON and Markdown hashes and the exact candidate tree. It is
independent only in the bounded prompt/derivation sense, not institutionally independent. Any edit
after that review invalidates automatic review credit.
