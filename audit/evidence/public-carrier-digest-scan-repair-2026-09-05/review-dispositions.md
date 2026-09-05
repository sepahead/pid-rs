# Recorded route and lens dispositions

Exact route and lens sections from the initial first reviewer. These are local review dispositions, not independent proofs.

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

