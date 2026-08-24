# KSG M1a composite v12 append-only repair boundary

- Repository: `sepahead/pid-rs`
- Fixed parent C11: `91d954160a7e717ae46b6088175ae52e92570127`
- Fixed C11 tree: `97841c6eda10573ddc3537c9e3b2ca41a93a3fa1`
- Required C12 message: `Repair KSG M1a composite v12 contract\n`
- Conditional R12 message: `Record KSG M1a composite v12 receipt\n`
- State: terminal hosted failure; Q12 is false and R12 is permanently unissued. L12 is not
  adjudicated by the terminal record.

## Why C11 cannot be retried or credited

The sole production L11 launch for exact C11 reached the retained certified-SxPID2 claim gate and
failed closed at:

```text
certified SxPID2 claim check failed: release-audit just dependency line exact digest changed
```

The v11 policy makes every production launch outcome consume the one L11 attempt. Therefore L11
is permanently false, Q11 is false, and R11 is permanently unissued. A later replay of the same
command is diagnostic only. It cannot become L11, repair C11 in place, or transfer qualification
credit to C12.

The root-installed machine record
`audit/evidence/ksg-rev4-m1a-composite-v11-local-closure-failure-v12-2026-08-23.json`
separates the first observed blocker from two downstream stale whole-container bindings found by
independent source diagnosis. The first error is not evidence that the two latent bindings were
reached during L11, and the later diagnosis is not a reconstruction of a missing L11 record.

## Coordinated certified-SxPID repair

The certified checker binds five related surfaces. C11 preserved the exact certified workflow job
and the exact `certified-sxpid` Just recipe, but changed the release-audit dependency line and the
two enclosing files. The v12 source rebinding is atomic at the contract level:

| Surface | C11 observation | v12 rule |
|---|---|---|
| certified CI job cut | unchanged | retain its exact digest |
| certified Just recipe cut | unchanged | retain its exact digest |
| release-audit dependency line | stale binding | bind the final v12 line |
| complete `.github/workflows/ci.yml` bytes | stale binding | bind the final v12 bytes |
| complete `justfile` bytes | stale binding | bind the final v12 bytes |

The source-reconstruction self-test continues to allow only the reviewed digest assignments and
gate-command isolation block to differ from its fixed historical checker anchor. Exact framing,
membership, path-inventory, and malformed-digest mutations remain negative controls. Passing this
finite suite establishes only the named contracts; it is not proof that every semantic bypass is
absent.

## C12 pre-L12 Lean-wiring finding

After the earlier non-production authoring lanes passed, the same C12 authoring run reached the
Lean 4.33 freeze checker and failed closed at this exact later diagnostic:

```text
Lean toolchain freeze check failed: operational wiring digest mismatch: .github/workflows/ci.yml: expected 9a70c744b57ccf5ca222fc9e8d0cd3f159276db8927f454a647d5d2be4bcd219, found 17b252ff25e881b4f1d01af13f88572c54ed6b221e4b5157fcacc7aae7efafc5
```

This is a C12 pre-L12 authoring finding. It is not an observation from the already consumed L11,
does not retroactively enlarge the L11 transcript, and does not consume L12. Sequential source
diagnosis found exactly six live paths whose C12 bytes intentionally differ from the operational
map embedded in the historical Lean `r14` receipt:

| Path | preserved `r14` / exact C9 SHA-256 | current C12 SHA-256 |
|---|---|---|
| `.github/workflows/ci.yml` | `9a70c744b57ccf5ca222fc9e8d0cd3f159276db8927f454a647d5d2be4bcd219` | `17b252ff25e881b4f1d01af13f88572c54ed6b221e4b5157fcacc7aae7efafc5` |
| `.github/workflows/ksg-m1a-composite-v9.yml` | `b8bcc6302c6625562b54a5f989aeeadc36fe631482d1071749a1c23aebf42002` | `714b01deb1a0671332bca638311095dc775ac75b1894c35a5555f951b9cc6aa0` |
| `CHANGELOG.md` | `307a5dad5fd1e8c69ce482ef900d0008ac9b49b819b912ff44f5331f94ba9ef5` | `edb458e4079cd8096797a014cdcb783e91d7cba60d3b0fbebd02056731fd77af` |
| `justfile` | `93399171cfbb743dba93c7be1ec85e446a33193e41ada3977d198b0e4ecc6437` | `e67d265b6b92fadc47f342a5ee399cc3656de537ebc3cc84e59f7fba3feeb885` |
| `scripts/check-certified-sxpid2-claim-self-test.py` | `2b3481e1ff735ddc2055a4979606a16c5032f54fc4cfd4717d227f68b9e9fb82` | `45166f4ed4dfe247e65fd39f4aa1b88a05ad630ffd6654613a758143c171b149` |
| `scripts/check-certified-sxpid2-claim.py` | `ad438e2ad236fe471ba40545799931da3a256cf5dc095178ef8bfb6398590a37` | `0743cbb515ad081b36ac95d1eff7130fb56579c2464cd0d527e83d971baa9c07` |

The two maps have different temporal subjects and therefore cannot soundly be repinned as one.
The repaired Lean gate validates the immutable receipt against the preserved map and validates the
working source against the current map. The v12 gate independently hashes every one of the 158
historical operational paths plus both historical custody programs from exact reachable C9 Git
objects, reconstructs the historical pre-pin checker digest, and separately binds the current
Lean checker and hostile suite. A coordinated rewrite of the receipt to current hashes is a
negative control. These checks protect the temporal distinction; they do not prove Lean kernel
soundness, theorem truth beyond the reviewed formal scope, Git-object authenticity, or which
process bytes the operating system executed.

## Append-only topology

C12 is exactly one unsigned direct child of C11. Its expected path/mode delta is enumerated by the
v12 checker. Every HEAD-reachable commit is scanned, including merged side branches. The exact C11,
C12, R11, and R12 messages may not be reused. None of the three R11 evidence paths may appear in
any reachable commit. The C11 failure diagnostic must be introduced by C12 and is zero-credit
negative evidence.

The now-unreachable prospective R12 contract required exactly one unsigned direct child of C12
with a four-row delta:

1. modify the self-excluding current-source manifest;
2. add the fresh L12 local closure;
3. add the fresh exact-C12 hosted qualification capture; and
4. add the canonically derived R12 receipt.

Those three added evidence entries must first appear together at R12 and remain byte-and-mode
identical in every R12-to-HEAD ancestry-path descendant. Side-branch introduction, deletion before
merge, split introduction, message reuse, or a near-name provides no credit.

## Qualification cut

For one exact C12 commit and tree,

$$
Q_{12}=L_{12}\land CI_{12}^{(1)}\land CodeQL_{12}^{(1)}\land Dedicated_{12}^{(1)}.
$$

The prospective contract required every hosted term to be attempt 1, terminal success, and bound
to the same C12 identity. The observed exact-C12 cut does not satisfy that requirement. Attempt-1
CodeQL run `32665994793` completed successfully with all four jobs successful. Attempt-1 repository
CI run `32665995643` completed in failure with 41 successful and four failed jobs. Attempt-1
dedicated-v12 run `32665995620` completed in failure with its sole job failed. Therefore Q12 is
false for either Boolean value of L12. The terminal record makes no statement about whether L12
ran or about any L12 outcome; `L12 = not_adjudicated` is not a failure claim.

The canonical machine record is
`audit/evidence/ksg-rev4-m1a-composite-v12-terminal-failure-2026-08-23.json`. It records the exact
run and failed-job identities plus byte counts and SHA-256 values for five retrieved job logs.
Those log bindings are unauthenticated retrieval evidence; the raw logs are not committed. Three
logs contain the bounded marker `ERROR: git exclude mode changed`, but neither the actual hosted
mode nor its cause is adjudicated. The secret-scan finding is likewise not adjudicated here.
The C12-owned `ksg-rev4-m1a-composite-v12-path-policy-v1.json` remains a historical prospective
snapshot and therefore retains its pre-run candidate fields; it is not the current terminal-state
authority and is not silently rewritten as if C12 had contained future observations.

The v11 push workflow and the v11 Just entry point are retired to explicit refusal. The active v12
workflow is now a nonqualifying terminal-preservation lane, and `just ksg-composite-v12` refuses
replay. `just ksg-composite-v12-preservation` checks the terminal record, exact C12 topology,
historical C12 checker/workflow blobs, absence of every R12 message/evidence path, and
record-introduction/preservation history. Later pushes cannot create L12, another hosted
attempt-1 term, qualification credit, or receipt authority.

## Source and evidence ordering

Three independent numbering namespaces are deliberately kept separate. Composite `R12` was the
conditional receipt commit defined above and is now permanently unissued. Lean `r14` is the
preserved fourteenth replay receipt.
`current_source_generation.generation_slot = 17` is only the next current-source generation slot
after the rejected C10 slot 15 and C11 slot 16; it is neither of those receipts and is not
`pid-rs/current-source-state` schema revision 1. The policy records `generated_fresh` because the
self-excluding slot-17 manifest was generated only after the other C12 source and the C11 failure
diagnostic had settled. That status does not claim a containing commit or any qualification term.

The prospective authoring order was:

1. settle and review all v12 source except the C11 failure record and current-source manifest;
2. install and review the canonical C11 failure diagnostic without treating it as L11;
3. generate the fresh self-excluding current-source manifest last;
4. make one unsigned direct C11-to-C12 commit with the exact message;
5. launch L12 once outside the repository;
6. push only under separate authority and observe exact-C12 attempt-1 CI, CodeQL, and dedicated-v12;
7. derive the receipt from mode-0600 local and hosted inputs through descriptor-only inputs; and
8. issue exact R12 only if all four Q12 terms are true.

The failed hosted conjunction permanently prevents steps 7 and 8. This retrospective statement
does not adjudicate step 5 or infer an L12 outcome from the hosted failures.

## Trust and nonimplications

The historical exact-C12 v12 checker checksum-binds and reuses frozen v11 primitives for
descriptor reads, Git object
verification, bounded subprocesses, canonical JSON, ZIP preflight/streaming, and complete-probe
bracketing. Its wrapper supplies the original lifecycle semantics and is separately
mutation-tested. The terminal overlay does not rerun that production route; its narrower checker
instead binds the exact historical checker/workflow blobs and the immutable terminal disposition.
This reduces duplicated implementation, but it does not make the v11 code, Python runtime, Git,
ZIP library, filesystem, provider, or wrapper infallible.

This boundary is operational source and evidence custody. It does not validate a PID functional,
KSG estimator, theorem, numerical result, scientific claim, application, security property,
privacy property, or accessibility property. Digests and unsigned Git objects do not authenticate
an owner or establish trusted time. Complete-probe endpoint equality is `pass_not_atomic`: a
transient ABA mutation or a same-UID or privileged writer that restores endpoints is not excluded.
