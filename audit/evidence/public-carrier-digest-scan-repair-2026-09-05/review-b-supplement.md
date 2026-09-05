This is a portable projection of an initial local review. Source observations and conclusions retain their original time and scope. Private-role references name omitted local evidence, not public retrieval links. [Projection scope](PROJECTION_SCOPE.md) and [manifest](MANIFEST.json) distinguish exact copies from projections.

# Supplement: proposed CI scanner controls

The proposed CI extension is acceptable as reviewed. It preserves the old controls, tests the
new exact carrier-digest rule, and adds direct checks against nearby credential suppression.
I found no invalid expected result or unsafe fixture mutation in the proposed patch.

## Exact scope and observations

The reviewed patch is
`ci.yml.patch`, SHA-256
`3e6297f15e361a4014b19e53719c8b395ad3cc0759506f4e9e05b5f900926d07`.
It is one insertion of 133 lines into the existing scanner Python here-document. I applied the
hunk in memory after checking every preimage/context byte. No tracked file was changed.

The resulting complete CI file has SHA-256
`6b0b1c01f0195ebffe188af443706f62fa3c48e0420318d68c7d8b25c6ab3ac9`.
The extracted complete Python block has SHA-256
`97b790a71f34f02a531dd4e493baac12fef759acbcf6e161bd5d830e7a368058`.
The entire original 8,152-byte Python block remains an exact prefix. The original ten intended
cases, sixty-three rejected cases, fingerprint check, and success message therefore remain
unchanged. The separate certified-reference job remains byte-identical, with SHA-256
`57d9da0e34d99723719040fb8e39490841c48db123074785afe71cb8eab0d028`.

I independently ran the complete extracted Python in normal isolated mode. The only execution
adaptation replaced its single `hosted-temporary-gitleaks-8.30.1` executable literal with the installed
`reviewed-local-gitleaks-8.30.1`. A fresh temporary working directory contained the exact proposed
configuration and current ignore file. Gitleaks reported version 8.30.1. The Python process
returned zero and wrote no stderr. Its stdout was exactly:

```text
Gitleaks narrow-allowlist self-test passed: 10 intended, 63 rejected
Gitleaks carrier-policy self-test passed: 10 intended contexts, 38 rejected shapes/paths, 80 retained adjacent credentials, 1 policy-text control
```

The surrounding tool call later returned one because the optional `command -v actionlint` probe
found no local actionlint binary. That is separate from the successful Python replay. I did not
run actionlint or claim a workflow-lint pass. The coordinator separately reported normal and
optimized replays and full-history scans; those are coordinator observations, not results from
this supplementary replay.

## Control quality

The positive digest is computed from the exact eighteen public carrier keys. The first review
independently reconstructed the same digest from subset families. The CI fixture avoids adding
a literal secret-like token to the workflow. The configuration accepts one exact digest rather
than all 64-hex values.

Each of the two paths has five positive contexts: bare JSON-style line, indentation plus comma,
tabs, a JSON object, and a Python dictionary. The five-by-two count is ten. The rejected matrix
has sixteen content cases and three path cases per path, giving thirty-eight. It includes changed
hex values, nonhex, key variants, quote/separator variants, line prefix/suffix changes, malformed
punctuation, and immediate credentials before, after, or on the same line.

The adjacent matrix combines ten credential shapes, two directions, two newline gaps, and two
paths, giving eighty. It includes split key/value forms and a changed digest under the same key.
It requires a nonzero finding status, exactly one finding, the generic rule ID, and a finding
range that reaches a physical line containing the synthetic credential value. Thus a surviving
public-digest false positive cannot substitute for the intended credential finding. The same-line
case separately requires two findings. The complete replay confirmed these expectations with
the pinned scanner version.

The changed-last-hex case replaces the current final `2` with `3`; it is an actual mutation for
this exact public carrier. The key list and positive rule should remain fixed together with the
reviewed public provenance. These tests do not create an independent trust anchor against a
coordinated replacement of the whole policy and test.

Fixture paths are controlled literals with benign prefix/suffix variations. Each scan creates
its own temporary directory, writes plain text, runs the scanner with an argument vector, and
uses `/dev/null` for ignore fingerprints. No shell evaluates fixture content. No fixture modifies
the checkout, Git history, scanner configuration, or ignore file. Operational scanner failure,
missing expected findings, parse errors, and wrong counts prevent the step from passing.

The policy-text case copies the candidate configuration into a fresh scan tree while the active
configuration path remains outside that tree. It checks that the added public policy text does
not create a new finding at a newly scanned location. It is not a full-history replacement.

## Current bindings and bounded gate list

Use the current-only dependency order from the initial critique:

1. Fix final `.gitleaks.toml` and `.github/workflows/ci.yml` bytes.
2. Update only the current whole-CI container hash in
   `check-certified-sxpid2-claim.py:58`. Preserve the separate certified job-slice hash.
3. Update the current CI and resulting current certified-checker hashes in
   `check-lean-toolchain-freeze.py:666` and `:706`.
4. Apply any additional current documentation bindings required by the coordinator's final incident
   record and changelog. Preserve prior replay, prior operational, and historical phase maps.
5. Regenerate current-source-state after all final tracked inputs are fixed. Generate normal and
   optimized outputs separately and require byte equality before installation.

For this security-only change and literal current binding updates, the applicable local gates are:

- Parse the TOML; check the patch's exact scope; compare the certified job bytes and historical maps.
  Use the repository's available workflow lint route if it is already installed.
- Run the entire old and new scanner self-test, preferably in normal and optimized mode as the
  coordinator has already done. Retain its exact input hashes and output.
- Run the pinned scanner against all relevant Git history with redaction and the exact candidate
  configuration. Preserve baseline findings and the candidate result separately. This review's
  temporary directory scans do not establish that full-history result.
- Run the current certified-PID claim checker and the current Lean freeze checker in normal and
  optimized isolated mode after their digest changes. Their documented complete gate recipes also
  include the existing self-tests in both modes; use those when closing the corresponding gate.
- Generate and check current-source-state last, in both modes. Retain the applicable source-state
  self-test evidence. Run `git diff --check` on the final change.

No Rust estimator or theorem source change is proposed, so an extra numerical experiment, a
KSG terminal lifecycle replay, or a new formal proof campaign is not justified by this patch.
The CI archive/version pin, full-history checkout, final `gitleaks git --log-opts="--all"` command,
and historical ignore fingerprints must stay unchanged. Historical v11/phase-isolation scanner
maps describe prior evidence and must not be rewritten to match this current repair.

This supplementary review did not edit tracked files, the proposal, or the adopted DNF judge.
Its sole durable write is this ignored record.
