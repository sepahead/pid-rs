# Public carrier-digest scanner repair

The full-history scanner classified a public mathematical digest as a credential at four
historical locations. This repair adds one exception for that exact value, key, and pair of
files. It preserves detection of the tested changed values and nearby credentials. It changes
no PID definition, estimator, theorem, or numerical output.

## Observed failure

The source was commit `91d5dbb13130ba89a7c8f2c09b2925fe15286fc5` on the integration branch.
[CI run 33947582367](https://github.com/sepahead/pid-rs/actions/runs/33947582367), attempt 1,
reported four findings in its full-history secret-scan job, `101256372387`. These were actual
failed gate results. A later passing revision does not change that observation.

All four findings concern the `carrier_keys_sha256` field. Two historical commits contain
the same evidence and checker blobs:

| Commit | Evidence JSON line | Checker line |
|---|---:|---:|
| `ee93b97fc779191306e34efc02c5ff2c78bc4162` | 181 | 118 |
| `8dc3ed23a2b42785a4b8d1ebb61eedb1d1a8805f` | 181 | 118 |

The exact files are
[`sxpid3-mgw-v5-program-a-semantic-bridge-v4.json`](sxpid3-mgw-v5-program-a-semantic-bridge-v4.json)
and the [semantic-bridge checker](../../scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py).
The JSON blob is `a14d462ebdea2ed909fa199e1f9fa31727a8fbdf`; the checker blob is
`039825ef6cb147e44dca0da2f9cfe0073c4f2a8e` in both historical trees.

Independent enumeration gives the 18 nonempty antichains of the seven nonempty subsets of
three source labels. Encode each subset as a two-digit hexadecimal mask. Join masks in a family
with `+`, and order families by size and then by their mask tuple. The compact JSON list has
130 bytes, with no trailing newline. Its SHA-256 is
`eac2b9ff616cce863e48c78fb0398c8ba81a582771f7d68e619c3262929d14a2`.
Two reviewers reconstructed this value without executing the repository checker. This establishes
the value's public-data origin. It does not prove the semantic bridge's mathematical claims.

The separate PDF job, `101256372255`, failed while downloading the pinned Elan archive. Its
reported cause was curl error 35, with a connection reset by the peer. This repair changes no
tool version, archive checksum, download step, or PDF gate. The failed observation remains in
the retained evidence; the repaired revision needs its own hosted execution.

## Scope of the repair

The [scanner configuration](../../.gitleaks.toml) adds one rule-level exception under
`generic-api-key`. Both conditions must hold: the path must equal one of the two reviewed paths,
and a complete physical line must contain the exact quoted key and known public digest.
Only horizontal whitespace and one optional trailing comma may surround that field. Default
rules, the full-history scan, and the two existing historical ignore fingerprints remain.

The first proposed expression used single-line anchors. It passed 45 of 49 cases but rejected
four valid JSON and Python contexts because the scanner's context could span physical lines.
That proposal was rejected. The accepted expression uses multiline anchors. Its exact rejected
preimage and decisive cases are retained in the [evidence manifest](public-carrier-digest-scan-repair-2026-09-05/MANIFEST.json).

Multiline anchors do not by themselves prove that adjacent credentials remain detectable.
The tests therefore place synthetic credentials before, after, and on the same line as the
public field. They also test blank lines, split assignments, changed values under the same key,
and nearby keys. The selected rule preserved detection in those cases. If a later counterexample
shows suppression of a different credential, reconsider the line-context route and test an
exact-match or exact-historical-fingerprint alternative. The relevant matching behavior is in
the pinned [Gitleaks 8.30.1 source](https://github.com/gitleaks/gitleaks/blob/v8.30.1/detect/detect.go).

## Review and local evidence

The first two policy critiques were written before the reviewers read each other's conclusions.
A subsequent review examined the proposed CI extension. The coordinating review inspected the
exact patches, provenance, and scanner implementation, then independently extracted and executed
the complete inline test program. These reviews share repository inputs and the pinned scanner.
They do not establish institutional independence or a universal security guarantee.

The evidence packet preserves ten materially different route dispositions and fifty named
review lenses. The alternatives include leaving the failure unchanged, using exact historical
fingerprints, matching the scanner's exact finding, broader value or path exclusions, changing
the schema, and rewriting history. The selected scope addresses the known false positives while
retaining the tested sensitivity and historical bytes. Counts measure review coverage, not proof.

| Local check | Result |
|---|---|
| Existing inline controls, normal and optimized Python | 10 intended cases and 63 rejected cases pass in each mode |
| Added inline controls, normal and optimized Python | 10 valid contexts, 38 rejected shapes or paths, 80 retained adjacent credentials, and one policy-text case pass in each mode |
| Independent initial policy matrix | 49 of 49 cases pass for the accepted proposal |
| Independent expanded adjacency matrix | 80 of 80 cases retain the baseline credential's rule and source coordinates |
| Second independent policy review | 44 scans preserve the tested detections |
| Coordinating full-history baseline | Exit 1; the exact four public-digest findings |
| Coordinating full-history candidate | Exit 0; zero findings in the same scanned history |
| Current certified-PID checker and hostile suite | Both Python modes pass; 126 mutations rejected per mode |
| Current Lean-freeze checker and hostile suite | Both Python modes pass; 145 mutations rejected per mode |

The local full-history runs used Gitleaks 8.30.1 on Darwin. Each reported 268 scanned commits and
81,883,959 scanned bytes. The clone contained 269 reachable commits; the scanner's count can omit
commits with no additions. These counts have different meanings. The local binary and runs do
not substitute for the pinned Linux archive or the required hosted checks. Zero findings is a
result for the stated detector and inputs, not proof that all credentials are absent.

The workflow change appends only the scanner controls. It preserves the existing certified-PID
job bytes. The certified checker updates its current whole-workflow binding; the Lean-freeze
checker updates only the affected current operational bindings. Historical replay maps and
receipts remain unchanged. The current source-state projection is regenerated after final
source edits. These identity updates grant no new formal execution or historical replay credit.

The retained patch ends with a valid space-prefixed context line. The original council table
ends with a blank line. Two exact-path preservation entries in [`.gitattributes`](../../.gitattributes)
keep those manifest-bound bytes and exclude only their archival whitespace from formatting checks.
The ordinary source-formatting rules remain applicable to the implementation and current prose.

## Publication boundary

The [evidence manifest](public-carrier-digest-scan-repair-2026-09-05/MANIFEST.json) identifies the
portable review records, public preimage, rejected approach, and bounded outcome projections.
It states their relation to local originals and any omissions. Local execution, remote branch
publication, accepted mainline integration, and long-term archival storage are separate states.
Resolve this record's containing commit from Git. Require the applicable hosted workflows on
the exact repaired branch commit before advancing main, then verify the exact main-push runs.
This record does not claim those later events have already occurred.
