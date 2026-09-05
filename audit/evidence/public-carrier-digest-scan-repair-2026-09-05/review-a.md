This is a portable projection of an initial local review. Source observations and conclusions retain their original time and scope. Private-role references name omitted local evidence, not public retrieval links. [Projection scope](PROJECTION_SCOPE.md) and [manifest](MANIFEST.json) distinguish exact copies from projections.

# Independent review of the September 5 secret-scan failure

The four reproduced findings are two copies of the same public carrier digest in two historical lineages. I recommend the exact-digest, exact-key, exact-two-path allowlist in `candidate.gitleaks.toml`, with the bounded inline CI extension in `repository CI after ci.yml.patch`. This is a review result. No tracked file, Git ref, hosted run, or main branch was changed by this reviewer.

The accepted candidate passed the retained policy cases and the new hostile cases. The initial anchoring candidate failed valid contexts and is retained as negative evidence. A passing local scan does not establish that the repository has no secrets. The exact repaired revision still needs the required hosted evidence before main can advance.

## Observation and public-data provenance

Review source: branch `sxpid3-program-a-clean-lineage-20260903`, HEAD `91d5dbb13130ba89a7c8f2c09b2925fe15286fc5`. The tracked checkout was clean at the final source capture. `private role: initial reviewer source observation` records source hashes, modes, and index entries. `private role: initial reviewer source preimages` retains the relevant original bytes.

The parent supplied CI run 33947582367, attempt 1: secret-scan job 101256372387 reported four findings. The separate PDF job 101256372255 failed during the Elan download with curl error 35. This review does not propose a dependency, version, download-pin, or PDF-gate change for that transport failure.

I independently enumerated the nonempty subsets of `{0,1,2}`. I formed nonempty families of pairwise incomparable subsets, encoded each subset by its three-bit mask, and sorted each family and then the carrier. This construction does not import or execute the repository checker. The resulting 18 keys are:

```text
01, 02, 03, 04, 05, 06, 07, 01+02, 01+04, 01+06, 02+04, 02+05,
03+04, 03+05, 03+06, 05+06, 01+02+04, 03+05+06
```

Their compact JSON list, with no trailing newline, has 130 bytes. Its SHA-256 is `eac2b9ff616cce863e48c78fb0398c8ba81a582771f7d68e619c3262929d14a2`. The exact preimage is retained in `carrier-preimage.json`.

At both commits below, I read the exact Git blobs. I parsed the Python source as an AST and read literal `EXPECTED_KEYS` and `EXPECTED_DIGESTS` assignments without executing that source. Both lineages match the independent construction.

| Historical commit | Evidence JSON line | Checker line | Result |
|---|---:|---:|---|
| `ee93b97fc779191306e34efc02c5ff2c78bc4162` | 181 | 118 | Both contain the public digest |
| `8dc3ed23a2b42785a4b8d1ebb61eedb1d1a8805f` | 181 | 118 | Both contain the same public digest |

The exact paths are `audit/evidence/sxpid3-mgw-v5-program-a-semantic-bridge-v4.json` and `scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py`. The JSON blobs are identical across the two commits: Git blob `a14d462ebdea2ed909fa199e1f9fa31727a8fbdf`, SHA-256 `dbc43a78e88d5e35cce5e01ec69f676eef8c68bda2f5eae5994f61d21fe5db24`, 17,458 bytes. The checker blobs are also identical: Git blob `039825ef6cb147e44dca0da2f9cfe0073c4f2a8e`, SHA-256 `394361524372710179aea41f95f4ddf9559700082a80e02ac0d0a34fbe08ce4a`, 41,953 bytes.

All four finding IDs match these commit/path/line tuples under `generic-api-key`. `provenance.json` retains the exact IDs and metadata. This establishes the public-data origin and the use of this digest. It does not prove the semantic-bridge mathematical claims, the correctness of an estimator, or a general absence of credentials.

## Candidate policy and rejected attempt

The candidate extends the existing `generic-api-key` rule with one allowlist. It requires both an exact path and a complete physical line that has the exact key and known public digest. It retains default rules. It leaves `.gitleaksignore` and its two historical prose fingerprints unchanged.

```toml
  [[rules.allowlists]]
  description = "Exact public Fin-3 carrier digest in its frozen semantic bridge"
  condition = "AND"
  regexTarget = "line"
  regexes = ['''(?m)^[ \t]*"carrier_keys_sha256":[ \t]*"eac2b9ff616cce863e48c78fb0398c8ba81a582771f7d68e619c3262929d14a2",?[ \t]*$''']
  paths = [
    '''^audit/evidence/sxpid3-mgw-v5-program-a-semantic-bridge-v4\.json$''',
    '''^scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4\.py$''',
  ]
```

The first version used the same expression without `(?m)`. It passed 45 of 49 fixture cases. It failed four intended JSON/Python contexts because the scanner can retain more than one physical line in its line target. Do not adopt that version. Its config, program, reports, and disposition are retained under `rejected-v1.gitleaks.toml and rejected-v1-cases.json`.

The second version uses multiline anchors. It passed all 49 initial cases and all 80 added adjacency cases. In the adjacency cases, the synthetic credential retained the same rule and source coordinates that the baseline detector reported. The cases cover tokens before and after the allowed line, single and double newline gaps, JSON and Python syntax, a changed value under the same key, nearby keys, unquoted values, and split key/value lines. The same-line control retains both findings because that physical line is not an allowed complete line.

This evidence supports the tested candidate. It is not a universal theorem about scanner context. If a later counterexample suppresses a neighboring credential, withdraw this line-target route and assess the exact-match route or the four exact historical fingerprints. The pinned detector selects either the match or the line as its allowlist target and evaluates configured AND conditions together. These details were checked in the [Gitleaks 8.30.1 detector source](https://raw.githubusercontent.com/gitleaks/gitleaks/v8.30.1/detect/detect.go).

## Executed checks and proposed CI extension

Local executable: `reviewed-local-gitleaks-8.30.1`, version 8.30.1, Darwin executable SHA-256 `f414bc2fb952be6c9072b75cb411e3368614ef4b16d48dbd9ad238034afd2302`. This is not the hosted Linux binary. The proposed workflow keeps the existing Linux archive version and SHA-256 pin unchanged.

| Check | Observed result | Durable evidence |
|---|---|---|
| Independent baseline full-history scan | Exit 1; exact four findings | `history-results.json`, `history-results.json (reviewer baseline metadata)` |
| Independent candidate full-history scan | Exit 0; zero findings | `history-results.json`, `history-results.json (reviewer candidate metadata)` |
| Initial accepted-candidate matrix | 49/49 cases pass | `matrix-results.json (policy cases)` |
| Added adjacency matrix | 80/80 cases pass | `matrix-results.json (adjacency cases)` |
| Existing hosted self-test, local adapter | 10 intended; 63 rejected; exit 0 | `execution-results.json (existing inline output)` |
| Proposed extended hosted self-test, local adapter | Old cases pass; 10 new contexts, 38 rejected shapes/paths, 80 retained adjacent credentials, 1 policy-text case pass; exit 0 | `execution-results.json (extended inline output)` |
| Structural config comparison | Baseline equals candidate after removing one added allowlist | `structure-results.json` |
| Workflow scope comparison | 26 job blocks; only `secrets` changes | `structure-results.json (workflow scope)` |

The history clone has 269 reachable commits. Both independent Gitleaks runs report **268 commits scanned**, with 81,883,959 scanned bytes. This matches the hosted count supplied for the failed run. The Git commit count and scanner count measure different things. The pinned detector explicitly allows its count to omit commits with no additions. See the [Gitleaks 8.30.1 detector source](https://raw.githubusercontent.com/gitleaks/gitleaks/v8.30.1/detect/detect.go). Do not present 269 versus 268 as evidence of a checkout/ref-selection discrepancy.

The CI proposal appends a bounded extension after the unchanged existing self-test. It computes the known public digest from the public 18-key fixture. It does not embed a new credential, change a dependency, or add another executable. It checks exact inventories, exit codes, finding rules, and the source lines containing the synthetic token. The original inline program is an exact prefix of the extended program after the same local-path adapter substitutions. The existing certified-SxPID job bytes and hash remain unchanged.

The local adapter changes only the config path, the unchanged ignore-file path, and the executable path. It runs the extracted inline Python program. It does not execute GitHub Actions itself. `actionlint` is absent in this environment and was not installed for this bounded review. Hosted execution remains an acceptance condition.

Exact proposed files and diffs:

- `candidate.gitleaks.toml`: SHA-256 `2567ed22e90ba46b671688c465628d5824a7bc7cb398cb14eb76c63e0cfd9681`.
- `candidate.gitleaks.toml compared with baseline.gitleaks.toml`: exact policy diff against the captured original.
- `repository CI after ci.yml.patch`: SHA-256 `6b0b1c01f0195ebffe188af443706f62fa3c48e0420318d68c7d8b25c6ab3ac9`.
- `ci.yml.patch`: exact workflow diff against the captured original.
- `private role: separately extracted CI extension` (not copied as a separate public file): SHA-256 `b36e55cc3b7937a4599a2a5163db42f84d776834d6220eece1e7570ea9f18211`.

## Ten route dispositions

| Route | Disposition | Reason and reconsideration condition |
|---:|---|---|
| 1. Retry the unchanged secret job | Reject as repair | Both independent baseline scans reproduce all four findings. A retry is appropriate for the separate Elan transport failure. |
| 2. Exact public digest, complete key/value line, two exact paths | Recommend with tests | It clears the observed false positives and preserves the tested neighboring credentials. The multiline context fix has explicit negative evidence. |
| 3. Exact `regexTarget=match` shape with two exact paths | Reserve | It can avoid unrelated line context, but must use the pinned scanner's actual known-public match bytes and preserve wrong-key/prefix controls. No adjacency counterexample required this route in the present tests. It was not executed. |
| 4. Add the four exact commit/path/rule/line fingerprints | Viable dissent | This is narrower in historical scope and would not exempt later occurrences. It needs an explicit update to the currently exact two-entry ignore policy and CI tuple. Repeated legitimate additions would need new review. It was not executed. |
| 5. Permit any 64-hex value under this key at these paths | Reject | It exempts changed values without a public-preimage justification. The frozen known digest permits a smaller exception. |
| 6. Permit this digest globally across all paths | Reject | It loses the reviewed use-site boundary and can suppress unrelated matches containing the same value. |
| 7. Exclude the two complete files or directories | Reject | It hides unrelated values and future credentials in those files. |
| 8. Disable the generic rule or lower its sensitivity | Reject | It weakens unrelated credential detection and does not address the specific cause. |
| 9. Rename the key or remove current digest fields | Reject as this repair | Historical findings remain. It also adds unnecessary evidence/checker binding changes. Reconsider only for a separate justified schema change. |
| 10. Rewrite history or delete branches to remove findings | Reject | It changes the historical evidence and loses useful lineage information. Cleanup is a separate preservation task. |

## Fifty applicable review lenses

These are review questions with observed dispositions. They are not fifty independent proofs or a claim of complete security coverage.

| No. | Lens | Disposition and evidence |
|---:|---|---|
| 1 | Public origin | Independent finite-carrier preimage regenerates the digest. |
| 2 | Enumeration independence | No repository checker import or execution was used. |
| 3 | Serialization precision | Compact JSON, 130 bytes, no trailing newline retained. |
| 4 | Historical literal table | AST literal extraction matches the 18 independent keys. |
| 5 | Historical digest use | Both exact source lines identify `carrier_keys_sha256`. |
| 6 | Dual-lineage provenance | Both commit trees were read independently. |
| 7 | Raw-byte identity | Git blob and SHA-256 identities agree across lineages. |
| 8 | Finding identity | All four commit/path/rule/line tuples match the reports. |
| 9 | Scientific scope | Public-data origin does not certify the mathematical bridge. |
| 10 | Unknown-secret scope | No unknown unredacted finding is published or assumed harmless. |
| 11 | Rule scope | The new exception belongs only to `generic-api-key`. |
| 12 | Default-rule coverage | Structural comparison preserves `useDefault = true`. |
| 13 | Boolean policy | AND requires both reviewed path and text conditions. |
| 14 | Path precision | Anchored exact paths; suffix, prefix, and renamed paths stay detected. |
| 15 | Key precision | Exact key; nearby and suffixed keys stay detected. |
| 16 | Value precision | Exact public digest; arbitrary 64-hex values are not allowed. |
| 17 | Nonhex mutation | Changed nonhex last character remains detected. |
| 18 | Changed-value mutation | Different digest and changed last hex digit remain detected. |
| 19 | Case mutation | Uppercase key remains detected. |
| 20 | Assignment syntax | Equals in place of the colon remains detected. |
| 21 | Unquoted key | Missing key quotes remain detected. |
| 22 | Single-quoted key | Alternate quote syntax remains detected. |
| 23 | Prefix text | Added prefix prevents the allowlist match. |
| 24 | Trailing text | Added comment prevents the allowlist match. |
| 25 | Punctuation damage | Missing value quote and extra comma remain detected. |
| 26 | Multiline context | Rejected first version retained; accepted version handles four contexts. |
| 27 | Credential before digest | Synthetic credential retains its original location and rule. |
| 28 | Credential after digest | Synthetic credential retains its original location and rule. |
| 29 | Same-line credential | Both generic findings remain present. |
| 30 | JSON credential syntax | API-key and access-token neighbors remain detected. |
| 31 | Python credential syntax | Quoted and unquoted assignment neighbors remain detected. |
| 32 | Same-key changed neighbor | The adjacent changed value remains detected. |
| 33 | Nearby-key neighbor | The adjacent differently named value remains detected. |
| 34 | Split key/value syntax | All tested newline-separated values remain detected. |
| 35 | Blank-line context | One and two newline gaps preserve the credential. |
| 36 | Config self-scan | Policy text produces no new finding in the tested path. |
| 37 | Baseline sensitivity | New hostile cases are detected by the unchanged baseline. |
| 38 | Existing controls | The original 10 intended and 63 rejected controls still pass. |
| 39 | New control inventory | CI asserts 10/38/80 new-case counts plus the policy-text check. |
| 40 | Executable identity | Local 8.30.1 binary hash recorded; hosted pin unchanged. |
| 41 | Platform difference | Darwin results do not substitute for the hosted Linux run. |
| 42 | History scope | Candidate was tested with `git --log-opts=--all`. |
| 43 | Count interpretation | 269 reachable commits, 268 scanned commits are distinguished. |
| 44 | Exit-code meaning | Baseline exits 1; candidate and both adapted suites exit 0. |
| 45 | Output privacy | Scan reports are redacted; unknown matches are not printed. |
| 46 | Existing ignore policy | The exact two historical prose fingerprints remain unchanged. |
| 47 | Immutable evidence | Historical replay maps and receipt projections must not be rebased. |
| 48 | Current bindings | CI, certified checker, and current freeze hashes need ordered updates. |
| 49 | Source-state durability | Regenerate current source state after final tracked changes. |
| 50 | Integration authorization | Local/remote main remains behind the exact required hosted gates. |

## Explicit binding map and adoption order

1. Review and adopt the two exact proposed diffs. `.gitleaks.toml` adds one scoped allowlist. `.github/workflows/ci.yml` adds only the inline secret-policy test extension. `.gitleaksignore` remains byte-for-byte unchanged. No mathematical source or PDF artifact changes are part of this repair.
2. Finish any professional change-log and incident record edits that belong in this milestone. Do not copy private executable or checkout locators into public records. Describe the observed false positives, the rejected anchoring attempt, and the passing checks with their exact scope.
3. In `scripts/check-certified-sxpid2-claim.py`, update only the current `EXPECTED_EXECUTION_CONTAINER_SHA256[".github/workflows/ci.yml"]` to the reviewed final CI bytes. The proposal's hash is `6b0b1c01f0195ebffe188af443706f62fa3c48e0420318d68c7d8b25c6ab3ac9`. Its `EXPECTED_CI_CERTIFIED_SXPID_JOB_SHA256` remains `57d9da0e34d99723719040fb8e39490841c48db123074785afe71cb8eab0d028`: that job has not changed. Preserve revision-3 authority, retained historical packet, and reviewed-documentation hashes.
4. In `scripts/check-lean-toolchain-freeze.py`, update the current `EXPECTED_OPERATIONAL_WIRING_HASHES` CI override and the current hash for `scripts/check-certified-sxpid2-claim.py`. Update its current `CHANGELOG.md` entry if the change log changed. Recompute any other genuinely changed current entry. Do not edit `PRESERVED_R14_OPERATIONAL_WIRING_HASHES`, `PRESERVED_R14_*`, `PRESERVED_PRIOR_REPLAY_*`, or historical receipt projections.
5. Preserve `audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json`. Its `operational_wiring_sha256` is checked against the preserved r14 map, not the current map. No new replay or replacement receipt is justified by a secret-policy fix. Likewise, do not rewrite immutable maps in older composite lanes to make current checks pass.
6. Regenerate `audit/evidence/current-source-state-v1.json` last, after all tracked additions and edits are final. The generator emits to stdout: `python3 -I -B scripts/check-current-source-state-v1.py --emit`. Redirect to an owned temporary file, then replace the manifest after the command succeeds. Its inventory includes `.gitleaks.toml`, CI, both affected checkers, and the change log. The manifest excludes itself from its direct source inventory; do not create a checksum cycle.
7. Replay the proposed secret-policy test with the pinned scanner and run the applicable certified-SxPID, Lean-freeze, source-state, and post-commit checks. The exact isolation flags for the Lean-freeze gate and self-test are `-I -S -B`, with the optimized-mode companions used by CI. Keep unchanged historical claims and self-tests intact. New failures require diagnosis rather than hash replacement by default.
8. Commit and push a small repair milestone under the existing user authorization only after the local checks pass. Preserve the failed hosted attempt as negative evidence. Re-run the required hosted workflows on the exact repaired commit. The separate transient Elan failure can use a clean rerun without a dependency or version change. Main advancement remains contingent on the established hosted policy and fresh ancestry checks.

## Reproduction and private source boundary

Use `ci-inline.py` through the explicit executable-path adapter in `replay.py` for the archived
inline controls. Use `replay.py --decisive` for the four exact rejected-context fixtures. The
initial private replay programs and their machine-specific command block are omitted from this
portable projection. Their raw identities are recorded as comparison metadata in the manifest;
they are not presented as publicly retrievable bytes.

`history-results.json` records the read-only history clone by role. A new ref set or a later scan
is a new observation and must not be described as the same frozen history scan. This review does
not authorize unrelated publication-figure adoption.
