# Certified-SxPID2 post-publication container rebind — 2 September 2026

## Disposition

**Local bounded rebind accepted; containing-commit and hosted closure pending.**

This receipt records one current-container custody update after publication commit
`c499653e4ac89733cb35330bf1a13c93a40ee385`. It does not revise the certified-SxPID2 mathematical
claim, any historical claim revision, or any preserved execution receipt. The only certified-claim
checker values changed are the current reviewed-documentation digest for `scripts/README.md` and
the current support-gate digest for `scripts/check-formal-pdf-set.sh`.

The change was required because the repository added a post-publication custody paper and corrected
the root blueprint's edition chronology. The shared scripts guide and formal-PDF dispatcher therefore
changed bytes. The certified-SxPID2 checker binds their complete current bytes deliberately, so it
failed closed until those two additive container changes were reviewed and rebound.

## Exact transition

| Bound object | Prior reviewed SHA-256 | Replacement SHA-256 | Classification |
|---|---|---|---|
| `scripts/README.md` | `644d7ef7420cbfb5eafaf7416b791ede20643abdb24d279e1f4d9df5124f9fff` | `cc771d89cbd94a536b0d37fa72016054695523a1ee444a6968b193c387323c3b` | Additive process/PDF documentation and corrected exact-only profile wording |
| `scripts/check-formal-pdf-set.sh` | `ae8d8ccbb873fe79dd9ebe2c849da93ac92404702e032632a428045068a287f2` | `089725d8c8c547d1bcc67f194602b33991a8d6faf28c0dac1aa5357b20a3ddc7` | Add one typed custody paper, its record/PDF hostile gates, and two exact-only status-2 branches |
| `scripts/check-certified-sxpid2-claim.py` | `dbd76020268ead8a4a926072940e5a9596d2449a5b49c578910cabf18b6487d0` | `afbc803d8436101e1524fb3bb775f47cd9ee51c88fea18f6a3e62650eaa2ae8d` | Exactly the two current digest literals above |
| `scripts/check-certified-sxpid2-claim-self-test.py` | `f051e54fdf2687b0717d5257f91052ccd2b1a47d9ed37b6c437e4b393744b6c1` | `f051e54fdf2687b0717d5257f91052ccd2b1a47d9ed37b6c437e4b393744b6c1` | Unchanged; the existing coordinated-rebind controls remain authoritative |

These are SHA-256 byte identities, not authenticity, compatibility, or scientific-validity claims.
The replacement values are final source values for this local candidate. A containing commit and
hosted run must be recorded separately after publication.

## Protected surfaces and non-change proof

The candidate was compared with the exact `c499653e…` base. No changed path occurs under any of the
following protected scientific or executable surfaces:

- `claims/SX-CERTIFIED-AVERAGED-PID2-001/`;
- `audit/tools/certified-sxpid/`;
- the certified-SxPID exact-product, independent-verifier, Lean, fixture, and schema artifacts;
- `crates/pid-core/`, `crates/pid-python/`, or `crates/pid-runlog/`;
- `method-catalog.json`, `METHODS.md`, or the certified method projection;
- `.github/workflows/ci.yml`, `justfile`, or the extracted certified-SxPID execution slices; and
- any preserved r14, historical Lean, KSG, or prior certified-SxPID receipt.

Inside `scripts/check-certified-sxpid2-claim.py`, the revision-3 authority maps, evidence maps,
execution-container bindings, catalog projection, theorem/source bindings, and accepted command
roster remain byte-for-byte unchanged. Only
`EXPECTED_REVIEWED_DOCUMENTATION_SHA256["scripts/README.md"]` and
`EXPECTED_SUPPORT_GATE_SHA256["scripts/check-formal-pdf-set.sh"]` changed.

The Lean-freeze checker's immutable `PRESERVED_R14_*` maps and receipts must remain unchanged. A
later step may update existing rows in its *current* operational-wiring map for the final candidate
bytes. That update supplies no Lean execution, replay, theorem, or C12 lifecycle credit.

## Why the support-gate change is acceptable

The formal-PDF dispatcher still requires the certified-SxPID2 assurance PDF and exact-log-product
PDF gates. The new custody paper is additive. Its checker has an exact same-toolchain relation and
refuses cross-toolchain mode with status 2 because no reviewed producer-equivalence profile exists.
The root blueprint retains the same refusal boundary. The aggregate now distinguishes papers with
reviewed portability profiles from these two exact-only artifacts, and its hostile self-test binds
both refusal branches and the terminal success wording.

No new paper can satisfy, bypass, weaken, or substitute for a certified-SxPID2 obligation. The
aggregate addition increases the enclosing gate surface; it does not change the accepted
certified-SxPID2 theorem, verifier, fixture, numerical result, or release decision.

## Twenty-lens adjudication

| # | Lens | Result |
|---:|---|---|
| 1 | Mathematical statement | Unchanged; no claim, formula, theorem, premise, or conclusion changed |
| 2 | PID semantics | Unchanged; no Wibral/MGW, Ehrlich, Williams–Beer, or other PID mapping was added |
| 3 | Estimand | Unchanged; the rebind is process custody only |
| 4 | Numerical behavior | Unchanged; no Rust/Python numerical implementation or fixture changed |
| 5 | Formal proof | Unchanged; no Lean source, theorem inventory, axiom inventory, or receipt changed |
| 6 | Independent verifier | Unchanged; verifier source and schema bindings remain fixed |
| 7 | Exact-product route | Unchanged; products, witnesses, and mutation evidence remain fixed |
| 8 | Claim authority | Preserved revision-1 through revision-3 authority maps were not edited |
| 9 | Catalog/provenance | Method catalog and certified projection are unchanged |
| 10 | Execution container | Certified CI job, Just recipe, and release dependency are unchanged |
| 11 | Documentation | Complete scripts-guide bytes changed for additive, explicitly bounded material |
| 12 | Aggregate gating | Existing certified PDF calls remain; custody gates are additive and fail closed |
| 13 | Cross-toolchain semantics | Both exact-only artifacts refuse with exact status 2; no similarity proxy was invented |
| 14 | Hostile testing | Certified 126-mutation suites and formal-PDF 65-control inventory pass locally |
| 15 | Historical preservation | Preserved r14 and historical receipt maps remain untouched |
| 16 | Scope separation | Repository custody is not mathematical, statistical, estimator, or application evidence |
| 17 | Independence | Same-repository review is not independent acquisition, execution, or human review |
| 18 | Durability | This dated receipt preserves old/new identities; final commit and remote identity remain pending |
| 19 | Failure behavior | The stale digest failed closed as intended; no tolerance or bypass was introduced |
| 20 | Publication boundary | Local acceptance is provisional until the exact containing commit is pushed and hosted gates pass |

The council disposition is **accept the narrow current-container rebind with zero scientific
credit**. The strongest objection was that rebinding a complete support-gate digest could hide an
unrelated weakening. It is answered here by the protected-path comparison, the two-literal checker
diff, the aggregate hostile suite, the unchanged certified mutation suite, and the preserved
historical maps. These checks share repository custody and therefore do not constitute independent
review.

## Local replay

The following commands passed in normal and optimized Python on the candidate bytes:

```text
python3 -I -S -B scripts/check-certified-sxpid2-claim.py
python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py
python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
scripts/check-formal-pdf-set-self-test.sh
```

The certified self-test rejected all 126 registered revision mutations. The formal-PDF aggregate
self-test passed 65 controls, including both exact-only refusal branches, the custody record/PDF
gates, and terminal-message distinctions. Exact PDF builds and the complete aggregate remain part
of final candidate validation.

## Remaining closure

Before this rebind can be treated as published current-container custody:

1. finalize all intended candidate bytes;
2. update only the existing current operational-wiring rows in the Lean-freeze checker;
3. pass normal and optimized freeze checkers and hostile self-tests;
4. regenerate the self-excluding current-source manifest last;
5. commit unsigned on a descendant of `c499653e…`, push with an exact expected-old-object lease,
   and verify the remote commit identity; and
6. require the applicable hosted workflows to succeed for that exact commit.

This receipt grants no authenticity, attestation, trusted-time, independent-review, mathematical,
statistical, estimator, application, compatibility, release, or future-cleanup claim.
