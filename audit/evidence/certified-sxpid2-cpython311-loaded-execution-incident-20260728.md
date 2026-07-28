# Certified-SxPID2 CPython 3.11 loaded-execution incident

- Date recorded: 2026-07-28
- Observed source commit: `dc7b8de0a87443ef2bcde71b19938642f1af2197`
- Observed source tree: `88b24c0ba4fcad4bd749b9146486143397b6a6eb`
- Observed Actions run: `30305288762`
- Observed job: `90107923447`

## Scope and evidence status

This record retains one fail-closed CI observation and the bounded corrective process for the
independent verifier's loaded-execution digest. It is not a green-run receipt, independent review,
external custody, a mathematical counterexample, or evidence that an accepted SxPID coordinate was
wrong.

The public run and job are:

- <https://github.com/sepahead/pid-rs/actions/runs/30305288762>
- <https://github.com/sepahead/pid-rs/actions/runs/30305288762/job/90107923447>

The complete CI run also had failures outside this incident. Correcting this verifier failure
cannot be represented as a successful full run.

## Observed failure

The job `Exact-count directed-rounding SxPID2 reference` used CPython 3.11.15 on
`ubuntu-latest`. Step 12 ran:

```text
python3 audit/tools/certified-sxpid/scripts/check-independent-verifier.py
```

At 2026-07-27T21:06:58Z it exited 1 while checking the first live certificate. The retained
terminal error was:

```text
pid_certified_sxpid_independent_verifier.VerificationError:
independent verifier loaded execution changed after module initialization
```

The normal-mode failure caused the optimized verifier check and the later exact-product,
claim-packet, and cargo-deny steps in that job to be skipped. It did not produce an accepted false
certificate. The guard rejected before the result could be credited.

On 2026-07-28, the SHA-256 of the exact byte stream returned by:

```text
gh run view 30305288762 --repo sepahead/pid-rs \
  --job 90107923447 --log
```

was:

```text
7c9aa8c1c5f08506dc9dacfb54a9826fecf38393fc823e39dd0460bc1d0094db
```

This digest identifies that retrieved command output. GitHub remains the custodian of the
underlying run log; the digest is not an external timestamp, signature, or guarantee that the
service will retain the log indefinitely.

## Bound failing bytes

At the observed commit, the relevant source digests were:

| Artifact | SHA-256 |
|---|---|
| `audit/tools/certified-sxpid/scripts/verify_certificate.py` | `667bb3426a7fc936d90f74d7e1c0547dae7021fa250bb1f06c9c8c3b0d657d02` |
| `audit/tools/certified-sxpid/scripts/check-independent-verifier.py` | `75fccc617b77513f48abaded50d31732f564abbcce2001f95527047d41ed85a9` |

Those values were recomputed from `git show` of the full observed commit. They identify the
failing source bytes, not an executable or Python-runtime image.

## Diagnosis

The verifier's integrity route marshalled normalized live Python code objects twice: once at
module initialization and again during verification. On CPython 3.11.15, lazy string-intern cache
state can alter the marshal byte stream even when no executable code or semantic constant has
changed. The integrity guard therefore treated a nonsemantic interpreter cache transition as
loaded-execution drift and rejected.

The incident is classified as a false rejection in the project-defined integrity measurement. It
does not falsify the paper-defined SxPID functional, the exact count expressions, the producer's
dyadic intervals, the exact-product comparison, or the verifier's fail-closed acceptance
direction.

## Candidate correction and revision boundary

The candidate correction:

1. recursively primes string-intern state for the code-object strings and nested constants that
   enter the digest;
2. changes the loaded-execution digest domain from
   `pid-certified-sxpid-independent-loaded-execution-v1\0` to
   `pid-certified-sxpid-independent-loaded-execution-v3\0`;
3. changes only the independent-verification schema from
   `pid-rs/certified-sxpid-independent-verification/v2` to
   `pid-rs/certified-sxpid-independent-verification/v3`;
4. adds a two-copy cold/warm control requiring the digest to remain stable across the observed
   nonsemantic string-intern transition;
5. adds one control requiring a post-import function-code replacement to fail through the
   loaded-execution integrity guard and to recover after the original code is restored;
6. replaces the manually selected constant projection with a typed, name-keyed inventory of all
   51 declared uppercase semantic/configuration globals and mutates every one after import; and
7. on CPython 3.11, removes the normalization call in an isolated source mutant and requires the
   affected integrity-check route to fail through the intended guard.

The candidate source digests at the time this record was written are:

| Artifact | SHA-256 |
|---|---|
| `audit/tools/certified-sxpid/scripts/verify_certificate.py` | `c90572571eac9b5cd5cd11d526a211dd0dfa7ab45274f6c038c0f8338cd2958e` |
| `audit/tools/certified-sxpid/scripts/check-independent-verifier.py` | `4327afdcce04421544481e0af9abf15dd3709ea75c5df994cb33b3ce3de91c17` |

The producer report remains v2, the resource policy remains v2, the exact-expression schema
remains v1, and the mathematical/product algorithms and their bounded evidence counts do not
change. Revision 3 is required because revision 2 explicitly made verifier source/runtime
requirements and the independent-verification schema re-adjudication triggers.

## Hostile-review corrections to the first candidate

A read-only independent verifier audit attacked all 51 declared uppercase configuration globals
on CPython 3.11.15 and 3.14.6. It found exactly four active exact-product admission limits whose
post-import mutation changed `_exact_product_plan` behavior but neither changed the initial
candidate's loaded-execution digest nor caused `_assert_verifier_integrity` to reject:

- `MAX_EXACT_PRODUCT_TERMS_PER_EXPRESSION`;
- `MAX_EXACT_PRODUCT_ABSOLUTE_EXPONENT`;
- `MAX_EXACT_PRODUCT_PROJECTED_BITS_PER_EXPRESSION`; and
- `MAX_TOTAL_EXACT_PRODUCT_PROJECTED_BITS`.

Those active globals had been copied into `PRECISION_POLICY_VALUE`, but behavior read the globals
while the digest read only the earlier copied projection. The review also showed that the first
cache-stability control called `_loaded_execution_sha256` before its explicit `sys.intern`; the
digest routine itself performed the transition, making that explicit step a no-op. These were
integrity/evidence defects, not observed SxPID arithmetic counterexamples or accepted false
certificates.

The revised candidate automatically includes all 51 declared uppercase semantic/configuration
globals through a deterministic typed encoding. Its harness requires the exact 51-name inventory,
mutates each value using a type-matched replacement, requires the intended integrity rejection,
restores it, and requires recovery. The cache control now compares two isolated verifier modules:
the cold copy receives a dynamically constructed non-interned probe, its digest intentionally
primes that object, and only then does `sys.intern` return the same object for attachment to the
otherwise isolated warm copy. This makes the cold-to-warm transition observable rather than
vacuous.

The same read-only audit recursively replaced every currently nested value and dictionary key
reachable from the 51-name inventory: 263 replacements on CPython 3.11.15 and 263 on CPython
3.14.6. Every replacement changed the digest, no supported value caused an encoding error, and
integrity recovered after restoration. Injecting a new unsupported uppercase `object()` failed
closed. This is exhaustive only for the declared inventory and typed recursion, not for arbitrary
Python process state.

Later hostile rounds attacked the claim and gate surfaces rather than the SxPID mathematics. They
found accepted Markdown/HTML/entity equivalences, enclosing workflow and Just disablement,
historical-packet rewrites, contradictory catalog/evidence wording, and parent commands whose
unbound children could exit successfully without checking a PDF or static policy. The correction
therefore combines semantic validation with exact raw-byte bindings for executable containers,
versioned authorities, reviewed documentation, leaf gates, policy sources, TeX/Markdown, and
PDFs, plus canonical whole-object projections for the certified method and five machine evidence
records. The registered hostile corpus rejects 94 named mutations in normal and optimized Python
modes, including a CRLF byte mutation. Those bindings are custody and fail-closed change controls;
they do not convert mutation adequacy into formal verification or independent review.

This fault-finding and the retained reproductions are credited as adversarial agent-review input;
the primary agent reproduced each accepted bypass before applying a correction. It is not
independent human custody.

## Local candidate replay

On the source hashes above, the qualification harness passed normally and under `-O` with local
CPython 3.11.15 and CPython 3.14.6:

```text
/opt/homebrew/bin/python3.11 audit/tools/certified-sxpid/scripts/check-independent-verifier.py
/opt/homebrew/bin/python3.11 -O audit/tools/certified-sxpid/scripts/check-independent-verifier.py
python3 audit/tools/certified-sxpid/scripts/check-independent-verifier.py
python3 -O audit/tools/certified-sxpid/scripts/check-independent-verifier.py
```

Each run reported the unchanged 11,856 coordinates, 1,482 direct-MI identities, 5,928 direct event
identities, 72 live containments, 975 exact-Fraction logarithm enclosures, 23 semantic mutations,
one fixed-point source mutation, one event-extraction source mutation, four cross-artifact
adversaries, six structural adversaries, and two transport/invocation controls, plus the two new
loaded-execution cache/code controls and all 51 semantic-constant mutations. The affected CPython
3.11 runs additionally killed one cache-normalization source mutant. The CPython 3.14 runs
reported zero for that explicitly version-conditioned source-mutation lane.

These are local same-worktree replays, not an Actions rerun, cross-platform result, independent
execution, or full repository pass.

## Open process obligations

- Recompute the two candidate source digests after all writers stop.
- Repeat the local normal/optimized qualification if either bound source file changes.
- Run the revision-3 claim checker and mutation self-test after the catalog inventory is updated.
- Obtain a fresh public CI result and record its run and job identifiers.
- Bind the full containing Git commit and tree after the revision-3 packet is committed.

Until those steps exist, this record must say “candidate correction” and “green rerun open.” It
must not be cited as external review, independent custody, formal verification, executable
attestation, or full-CI success.
