This is a portable projection of an initial local review. Source observations and conclusions retain their original time and scope. Private-role references name omitted local evidence, not public retrieval links. [Projection scope](PROJECTION_SCOPE.md) and [manifest](MANIFEST.json) distinguish exact copies from projections.

# Independent critique of the public carrier-digest exception

The proposed raw scanner rule is acceptable within the checks below. I found no defect that
requires a change to its exact digest or two-path scope. The current CI self-test must gain
controls for this exception before the repair is integrated. This review did not inspect the
other reviewer's conclusions or proposed CI changes.

## Exact reviewed inputs

| Input | SHA-256 |
|---|---|
| `.gitleaks.toml`, 3,998 bytes | `fc603d1ad33b42fa772612bcf769ca00d18c685479ba2a497b9c491cdca25750` |
| `candidate.gitleaks.toml`, 4,449 bytes | `2567ed22e90ba46b671688c465628d5824a7bc7cb398cb14eb76c63e0cfd9681` |
| `.github/workflows/ci.yml` | `049ed96393454c64905789c1b2b2613878d9084829cde802cb78d93dd338c896` |
| `reviewed-local-gitleaks-8.30.1` | `f414bc2fb952be6c9072b75cb411e3368614ef4b16d48dbd9ad238034afd2302` |

The candidate starts with every byte of the current configuration, followed by one 451-byte
allowlist. The parsed rule count stays one and the allowlist count changes from ten to eleven.
Default rules remain enabled. The local binary reported version `8.30.1`, which matches the
version pinned in CI at lines 1573–1581. This local macOS binary hash does not attest the Linux
archive used by CI.

## Scope and matching semantics

Candidate lines 88–96 add one rule-level exception to `generic-api-key`. `condition = "AND"`
requires both the content and path checks. The two exact path expressions are alternatives
within the path check. There is no global path exclusion, credential-key exception, wildcard
file suffix, arbitrary 64-hex exception, or change to `.gitleaksignore`.

Gitleaks 8.30.1 evaluates line exceptions against the finding's context string. Its AND branch
combines applicable path and regex checks; an AND allowlist with a regex does not bypass the
file before finding evaluation. The path alternatives are combined with OR. These details were
checked against the pinned [finding implementation](https://raw.githubusercontent.com/gitleaks/gitleaks/v8.30.1/detect/detect.go)
and [allowlist implementation](https://raw.githubusercontent.com/gitleaks/gitleaks/v8.30.1/config/allowlist.go).

The new expression uses multiline anchors because the context string can contain more than one
physical line. It restricts the matched physical line to the exact key, exact digest, optional
comma, and horizontal space or tabs. It does not accept a newline between key and value. A
multiline anchor alone does not prove that another finding is safe from suppression, so I tested
nearby credentials directly.

## Exact public-digest provenance

The allowed value is
`eac2b9ff616cce863e48c78fb0398c8ba81a582771f7d68e619c3262929d14a2`.
The bridge evidence records it at
`audit/evidence/sxpid3-mgw-v5-program-a-semantic-bridge-v4.json:181`.
The checker pins it at `scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py:118` and derives
it from canonical carrier-key JSON at line 911. Its canonical encoding is defined at line 397;
carrier enumeration and stable-key encoding are defined at lines 649–661.

I independently enumerated all nonempty families of the seven nonempty subsets of a three-bit
source set. I retained exactly those families whose distinct masks were mutually incomparable
under inclusion. Ordering by family size and mask tuple gives eighteen families. Serializing
each mask as two lowercase hexadecimal digits, joining each family with `+`, then hashing the
compact JSON key array reproduced the exact allowed digest. The reconstruction used Python's
standard library and did not execute the bridge checker. This establishes the public digest's
provenance. It does not close the bridge's open formal-completeness or custody claims.

The reconstruction was:

```python
keys = []
for n in range(1, 8):
    for family in itertools.combinations(range(1, 8), n):
        if all((a & b) != a and (a & b) != b
               for a, b in itertools.combinations(family, 2)):
            keys.append("+".join(format(x, "02x") for x in family))
raw = json.dumps(keys, separators=(",", ":"), sort_keys=True).encode()
carrier = hashlib.sha256(raw).hexdigest()
```

## Independent scanner controls

I ran 44 fresh directory scans: eleven content/path cases, each at both allowed paths, under
both the baseline and candidate configurations. Every scan used Gitleaks 8.30.1, redaction,
`--gitleaks-ignore-path /dev/null`, JSON output, and a fresh temporary directory. Every nonempty
finding below had rule ID `generic-api-key`. The two paths gave identical results.

Let `P` be the exact line `"carrier_keys_sha256": "<allowed digest>",`. Let `S` be the synthetic
line `api_key = "<fixture>"`, where the fixture was the joined literal
`G7j4P9x2K8m6Q1n3` + `R5t0V9z7Y6w2H4c8`. This is test data, not an account credential.
A final newline was added to each file.

| Case | Baseline findings | Candidate findings | Candidate exit |
|---|---:|---:|---:|
| `P` | 1 | 0 | 0 |
| `"digests": {` followed by `P` | 1 | 0 | 0 |
| `S` before `P` | 2 | 1, on `S` | 1 |
| `S` after `P` | 2 | 1, on `S` | 1 |
| `S`, `P`, `S` on separate lines | 3 | 2, on both `S` lines | 1 |
| `P` and `S` on the same line | 2 | 2 | 1 |
| Change the digest's first character from `e` to `0` | 1 | 1 | 1 |
| Change the key to `nearby_carrier_keys_sha256` | 1 | 1 | 1 |
| Remove the quotes around the key | 1 | 1 | 1 |
| Replace the key/value colon with `=` | 1 | 1 | 1 |
| Append `.nearby` to the allowed path | 1 | 1 | 1 |

The exact scanner argument vector was:

```text
reviewed-local-gitleaks-8.30.1 dir . --config <absolute-config> --gitleaks-ignore-path /dev/null --redact --no-banner --report-format json --report-path <temporary-report.json>
```

The initial hypothesis was that the multiline line expression might suppress an adjacent
credential. The tested before, after, both-sided, and same-line cases did not support that
hypothesis. They remain bounded tests, not a universal noninterference proof for all scanner
contexts. These synthetic temporary trees were removed after scanning; the exact fixtures,
command, input hashes, counts, rule IDs, and result locations are recorded above. This review
did not run a full-history scan or the complete current CI self-test.

## Current CI and preservation dependencies

The current CI self-test at `.github/workflows/ci.yml:1582–1797` has ten intended cases and
sixty-three rejected cases. It has no carrier-digest case. Extend it with both exact paths,
actual preceding-line context, a different 64-hex value, wrong path/key/syntax, and credentials
before, after, and on the same line. Use actual measured result counts and retain the existing
controls. A generic arbitrary digest cannot serve as the new positive fixture: the exception
correctly accepts only the exact reconstructed public value. Keep full-history checkout and the
full-history scan at line 1799, the scanner version/archive pin, and the two historical ignore
fingerprints unchanged.

The applicable current bindings are:

| Change | Current dependency | Required treatment |
|---|---|---|
| CI self-test bytes | `scripts/check-certified-sxpid2-claim.py:58`, `EXPECTED_EXECUTION_CONTAINER_SHA256` | Rebind the complete current CI file hash. |
| CI self-test bytes | `scripts/check-lean-toolchain-freeze.py:666`, `EXPECTED_OPERATIONAL_WIRING_HASHES` | Rebind the current CI entry. |
| Certified checker after that rebind | `scripts/check-lean-toolchain-freeze.py:706` | Rebind this current checker entry after its final bytes are fixed. |
| Scanner, CI, and changed checker bytes | `audit/evidence/current-source-state-v1.json:199`, `:288`, `:5832`, `:6396` | Regenerate the current source-state inventory last. |

A secret-scan-only change must leave the separate certified job-slice digest at
`check-certified-sxpid2-claim.py:47` unchanged. The slice is extracted and checked at lines
759–784. It is distinct from the whole-container digest.

Do not rewrite `PRESERVED_R14_OPERATIONAL_WIRING_HASHES` in the Lean freeze checker. Its prior CI
entry is at line 505 and its prior certified-checker entry is at line 618. Likewise, preserve
`check-ksg-phase-isolation.py:1668`'s `EXPECTED_BOUND_ALLOWED_BLOBS`, including its old scanner
hash at line 1670: this is a recorded corrective-phase map tied to `CORRECTIVE_PARENT` at line 61.
Old composite checker and recorder references to `.gitleaks.toml` do not authorize revising their
historical evidence or reviving a terminal lifecycle. In particular, the v11 repair predicate at
`check-ksg-m1a-composite-v11.py:3385` describes an older concrete scanner shape; it is not a new
current scanner requirement.

The static dependency census found no direct reference to the CI file or these two current
checker paths in the ecosystem-capabilities or mathematical-audit-protocol checkers. This is a
bounded locator result, not an assertion that arbitrary future edits have no additional binding.

No tracked file, proposal file, frozen DNF judge file, commit, or branch was changed by this
review. The only durable write is this ignored critique.
