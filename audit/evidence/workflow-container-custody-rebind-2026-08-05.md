# Workflow-container custody rebind - 5 August 2026

## Finding

This receipt describes the exact transition committed as
`54714f08d4c234424cab1b6a9b96bf3d4fafe1d8`. Later workflow portability corrections may supersede
the replacement container bytes; they require their own explicit re-adjudication and do not erase
this failed-run record.

Commit `9031230d0ab6e0878fe8b9ba38578a80c9439776` added the verified mathematical-workflow PDF gate.
That intended change altered the complete bytes of `.github/workflows/ci.yml`, `justfile`,
`scripts/README.md`, and the shared `scripts/check-formal-pdf-set.sh` dispatcher. The revision-3
certified-SxPID2 governance checker deliberately binds these enclosing artifacts in addition to
narrower executable slices. Its first hosted replay therefore failed closed at the stale
complete-workflow digest in CI run `31002580047`, job `92294747557`, step 22.

This was a custody integration defect, not a failed SxPID theorem, estimator discrepancy, or
certificate counterexample. The hosted job's preceding Rust, Python, exact-product, mutation,
boundary, evolutionary, and Lean steps passed. A local exact replay on commit `9031230` reproduced
the checker rejection before this rebind.

## Exact transition

| Bound object | Prior reviewed SHA-256 | Replacement SHA-256 |
|---|---|---|
| complete `.github/workflows/ci.yml` | `b8457a955da4560c6c3d296b81ca8c390ba5f908209eee90eaecc86a86c9bf7d` | `95fa772d867a2adfbc9cc127a276c319886079923d6c86c8e12b52900168832e` |
| complete `justfile` | `c0626c6229a9b7ac0ada280e7a838b0d53985270c29bcd4de4fffd410217ac3c` | `39440fdf9d3b9c49b4721771a89ebc759d1e2fcea7f2f6cebb5a45cbae520605` |
| complete `scripts/README.md` | `061cc9b649750ab0ebfc3b2090d0303db5cf245536ca88f76819d5a6b5717ef9` | `45957675b2606eef05215daa969e620898ff72309afc308e1e649997d80fc83c` |
| complete `scripts/check-formal-pdf-set.sh` | `31b829f54d2ec0574597c68c670ae3b87f74537da413d989617ad6315eed8aeb` | `975452402a16665ca9347a5523dc01a160985b0e50ee3a26dea788716c09149f` |

The separately parsed and hashed certified-SxPID2 execution slices did not change:

| Frozen slice | SHA-256 |
|---|---|
| `certified-sxpid-reference` CI job | `3a31891c2ec40575700ad6b9547148566590c3ffd7b81d4d07635577002e6c9b` |
| `certified-sxpid` Just recipe | `d706ca9cdb493933cc35701677a5fcb50c7650c71aa617e6caa644f04c7a5747` |
| `release-audit` Just dependency line | `67873e131920d50e8014ca656a0ebfe8c4eeb0ca1fbbfa4e6d582f15a8e836be` |

The rebind changes only four expected enclosing-artifact digests in
`scripts/check-certified-sxpid2-claim.py`. It does not modify the SxPID definition, theorem source,
certificate, verifier, fixture, executable command slice, claim wording, or scientific conclusion.
It does not prove that the newly added workflow gate is scientifically correct, authenticate GitHub
Actions, or make same-repository custody independent.

## Qualification

The correction requires all of the following before credit:

```text
python3 scripts/check-certified-sxpid2-claim.py
python3 -O scripts/check-certified-sxpid2-claim.py
python3 scripts/check-certified-sxpid2-claim-self-test.py
python3 -O scripts/check-certified-sxpid2-claim-self-test.py
git diff --check
```

Final closure additionally requires a successful hosted CI run for the exact correction commit.
