# KSG M1a composite v11 repair and qualification boundary

- Repository: `sepahead/pid-rs`
- Fixed parent C9: `337fe9b7f7cf30a8f00138310ce0398d9e95b9c5`
- Required C11 message: `Repair KSG M1a composite v11 contract\n`
- State of this document: candidate-authoring policy; no L11, hosted-success, receipt, or
  publication evidence has been produced.

## Topology and custody decision

C11 is a fresh direct child of C9. It is a sibling of the rejected, unpushed C10 candidate, not a
descendant. C10 must not be merged, cherry-picked, rebased, or treated as a source of L10, R15,
hosted-success, or qualification credit. Independently reviewed non-evidentiary repairs may be
reapplied as new C11 bytes. This is the same distinction made by the v9 boundary: rejected
candidate history is not admitted, while independently reauthored repair bytes may be reviewed on
a fresh parent.

Durable execution history records the full observed C10 identity
`8a9c52c4871f62cf4165102fa5d1c671f866ae73`, tree
`c33fdfd8340594c8233128034baf1804084abc75`, exact C9 parent, clean unsigned state, and 39-path
delta (22 modified, 17 added). Those recorded identity facts are not custody of the currently
unrecovered Git object or its source bytes. The machine-readable diagnostic record is
`audit/evidence/ksg-rev4-m1a-composite-v10-diagnostic-failure-2026-08-23.json`.

## C10 diagnostic: observed blocker versus latent defects

The first production L10 attempt stopped in `authority_descriptors` at the lexicographically first
oversize authority:

| Classification | Path | Observation | Consequence |
|---|---|---:|---|
| first observed blocker | `audit/evidence/ksg-rev4-m1a-composite-c9-terminal-hosted-capture-v10-2026-08-23.json` | 2,264,350 bytes under a 2,097,152-byte ceiling | L10 failed before command execution |
| latent, not reached | `scripts/check-current-source-state-v1-self-test.py` | Git `100755`, live `0755`, v10 expected `0644` | would have blocked later |
| latent, not reached | `scripts/check-current-source-state-v1.py` | Git `100755`, live `0755`, v10 expected `0644` | would have blocked later |

The two mode defects are not co-causes of the observed rejection. They are counterfactual later
blockers discovered by reviewing the complete roster after the first failure. The oversize
artifact itself was not recovered: only metadata about its observed identity, size, and digest was
recovered and retained. Its 2,264,350 bytes are not present in the C9 base and must not be
fabricated. Of the other 38 C10 paths, 35 source-byte sequences were recovered privately, but that
partial recovery is neither custody of the C10 Git object nor C11 evidence. A fresh hosted
observation may reproduce the terminal-C9 artifact later, with no inherited C10 credit.

## One authority specification, four independent bindings

Every authority is declared once as an `AuthoritySpec` with:

1. repository-relative path and unique semantic role;
2. expected Git tree mode (`100644` or `100755`);
3. expected live POSIX mode (`0644` or `0755`);
4. byte-limit class.

The local recorder performs component-wise descriptor-relative opens from a canonical repository
root descriptor. Each component and leaf is opened without following symbolic links. A leaf must
be a single-linked regular file in its declared live mode. The recorder binds pre-open, opened,
post-read descriptor, and post-read directory-entry identities; it reads the exact advertised size
and then requires EOF.

Git is a separate authority surface. The recorder obtains the exact tree entry, checks its mode and
blob object ID, reads the blob object, and recomputes Git SHA-1 object framing in Python. It also
recomputes the candidate commit and top-level tree object IDs. Equality of live bytes, Git blob
bytes, Python-computed blob ID, declared Git mode, and declared live mode is required for evidence
capture. Neither Git object identity nor SHA-256 authenticates an owner or establishes trusted
time.

The checker brackets its complete bounded probe with exact repository-config, routing, replacement,
graft, alternate, rule-file, HEAD, and worktree-status observations and requires endpoint equality.
This is `pass_not_atomic`: it detects persistent endpoint drift, but it cannot exclude a transient
ABA change or a concurrent same-UID or privileged writer that restores the observed endpoints.
That concurrency exclusion remains an execution premise, not a property proved by the checker.

## Resource classes

Ordinary authorities remain capped at 2 MiB each. Exactly one manifest path may use the 4 MiB
class: the named terminal-C9 hosted capture above. A path prefix, role string, filename suffix,
nearby path, or another hosted artifact does not inherit that class. All authority bytes together
are capped at 16 MiB. Recorder and checker enforce these rules independently.

Hosted artifact ZIPs are separately capped at 32 MiB encoded and 22 MiB total advertised expansion.
Before opening a member, the checker rejects ZIP64/multi-disk/trailing layouts, more than 10,000
members, unsupported entry types or compression, unsafe names, and an excessive aggregate. Only
non-directory stored/deflated members with a regular or unspecified Unix type then stream in
requests of at most 64 KiB, with exact advertised size, a final one-byte EOF check, and the
standard-library CRC check. These bounds limit parser and decompression work; they do not
authenticate artifact bytes or prove the ZIP implementation sound.

`--preflight-live` is a non-evidence authoring operation. It exercises the actual production
roster, live modes, no-follow reads, size classes, aggregate ceiling, existing Git entries, and
commit/tree object hashing. It may report the one future predecessor-capture artifact as pending
and new or modified C11 source as prospective. Final L11 capture is stricter: every authority must
exist in and byte-match the clean exact C11 tree.

## Workflow transition

The v9 push lifecycle is retired to a manual refusal job that always fails with an explicit
terminal message. It preserves the historical file path without creating another push-triggered
descendant run. The v11 workflow is the only active dedicated push lifecycle. On the exact first
C11 push it runs normal and optimized self-tests, normal and optimized real live preflights, then
the static v11 checker. Descendant executions are preservation checks only and cannot issue or
transfer R11.

The GitHub workflow selected for a push is read from the pushed commit/ref. Therefore a direct
C9-to-C11 push evaluates the v11 tree; it does not require publishing the rejected C10 tree or
installing a v10 lifecycle. No skip directive, conditional job skip, provider disablement, or
expected-red success convention is used.

## Qualification and publication sequence

For one exact C11 commit and tree:

$$
Q_{11}=L_{11}\land CI_{11}^{(1)}\land CodeQL_{11}^{(1)}\land Dedicated_{11}^{(1)}.
$$

Every hosted term is attempt 1, terminal success, and bound to that same exact commit and tree.
L11 is a fresh successful local closure of `just ksg-composite-v11`. If any term is absent,
failed, retried, nonterminal, or attached to another identity, Q11 is false and R11 remains
unissued. The exact R11 message, if and only if Q11 is established, is
`Record KSG M1a composite v11 receipt\n`.

Launching the production L11 recorder is a one-shot lifecycle action for the exact C11 identity:
success, command failure, timeout, signal, recorder failure, or an unusable emitted record all
consume that attempt. `--preflight-live` and offline self-tests are repeatable non-evidence
authoring checks and do not consume L11. The recorder cannot prove operator uniqueness or exclude
an undisclosed parallel launch; that custody obligation remains procedural and must be reviewed
before R11 issuance.

The sequence is intentionally staged:

1. settle and independently review the C11 capture/checker/policy source;
2. obtain the fresh terminal-C9 predecessor capture outside the repository, review it, and add its
   exact bytes at the sole 4 MiB authority path;
3. settle every C11 tree byte, then generate a fresh R16/current-source binding (never reuse R15);
4. commit one unsigned direct C9 child with the exact C11 message; no later source or predecessor
   artifact mutation can earn L11;
5. perform L11 outside the repository against that clean exact committed tree;
6. push only under separate authorization and observe attempt-1 CI, CodeQL, and dedicated-v11;
7. pass the reviewed mode-0600 L11 and successor capture through the checker’s descriptor-only
   `--derive-receipt` route, review its canonical derivation, refresh current-source state, and
   issue R11 only if the exact formula above is true.

This authoring stage performs none of steps 2–7.

## Nonimplications

This is an operational source-custody and workflow contract. It does not validate a PID functional,
KSG estimator, theorem, numerical result, scientific claim, application, security property,
privacy property, or accessibility property. Finite hostile suites can demonstrate rejection of
named mutants but cannot prove absence of bypasses. Formal tools, source hashes, Git objects,
provider responses, and repeated observations each have explicit trust and completeness bounds;
none is a substitute for semantic review or independent scientific reasoning.
