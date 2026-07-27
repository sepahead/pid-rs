# KSG revision-4 recovery ledger

Status: **byte recovery complete; verification and integration NO-GO**

The former candidate at `/private/tmp/pid-rs-ksg-rev4.E11L9g/tree` was observed absent and no
longer appeared in `git worktree list`. This record does not assign a cause. In particular, it
does not turn an observed path loss into an unsupported operating-system or cleanup-mechanism
claim.

The candidate is being reconstructed from the pushed parent, content-addressed Git history,
surviving ambient files where their exact provenance is established, and the preserved Codex
JSONL transcripts containing the original patches and command results. Pre-loss verification
results remain useful historical evidence, but none will be credited as a settled-byte pass for
the recovered tree.

The byte-recovery phase is now complete. This is narrower than scientific closure: the recovered
candidate still requires hostile-review adjudication, phase-checker hardening, final-byte replay,
an isolated staged tree, and a pushed receipt before repository or publication integration can
become GO.

## Durable candidate and first restore point

- Durable worktree:
  `/Users/torusprime/Development/sepahead-github/pid-rs-ksg-rev4-candidate`
- Branch: `codex/ksg-rev4-candidate-20260726`
- Pushed base and `origin/main` at reconstruction start:
  `118e1de6a2d6d2ae33fe7bdc224736257e42a83f`
- Explicit-path checkpoint ref:
  `refs/codex/checkpoints/ksg-rev4-recovery-source-1`
- Checkpoint commit: `94813b96990ae9ec2b9f2db368fe06e2de797dd6`
- Checkpoint tree: `04669a046910c7fa7f4e33cedca31aecd402a03d`
- Verified durable bundle:
  `/Users/torusprime/Development/sepahead-github/pid-rs-recovery-checkpoints/ksg-rev4-recovery-source-1.bundle`
- Bundle SHA-256:
  `7b0bf3c63d82e28b58fd9a0150d2c6878adade08db4ba33a03ef92529ead295a`

The first restore point contains only the explicitly enumerated KSG source, tests, fixture,
serial/parallel bit oracle, and fixture generator. It is not a formal-proof, claim-packet,
catalog, release, or integration closure.

The corresponding machine-readable record
[`ksg-rev4-recovery-ledger-20260727.json`](ksg-rev4-recovery-ledger-20260727.json) carries every
checkpointed path digest.

## Byte-recovery-complete checkpoint

After recovery and advisory adjudication, 109 modified or untracked paths were enumerated
explicitly. There were no deletions, symlinks, gitlinks, or pre-existing staged paths. A separate
index seeded from the exact pushed parent produced:

```text
ref:    refs/codex/checkpoints/ksg-rev4-recovery-complete-2
commit: 7eb959e3e3fd4bc2893cef83e6728b1594f8691b
tree:   423dd61a5284717db41a7dbda5702f7d81bd48f7
parent: 118e1de6a2d6d2ae33fe7bdc224736257e42a83f
paths:  109
```

The verified bundle is
`/Users/torusprime/Development/sepahead-github/pid-rs-recovery-checkpoints/ksg-rev4-recovery-complete-2.bundle`,
SHA-256 `23a1db4ae281c03723094093c4fa9e726867d07fd6406847f29542ec418f8078`.
It was fetched into a new retained bare repository, checked with `git fsck --full --strict`, and
matched the source commit, tree, parent, and Git-archive SHA-256
`ce51bdf938fa1c65ddfa3c48c268d53c1ab8479273ab14156446fb9cbefad354`.

The external receipt is
`/Users/torusprime/Development/sepahead-github/pid-rs-recovery-checkpoints/ksg-rev4-recovery-complete-2-receipt.json`,
SHA-256 `858c429e91418a3883cfd62a755c4da32dbb5be4c1fe7b801cef86930f83f6e2`.
The receipt retains two construction-path corrections: Git rejected a first malformed
`update-ref` invocation before creating a ref or bundle, and the command guard rejected a
recursive temporary-restore cleanup before execution. The successful replay used the correct
reflog-message flag and a durable bare restore. These events are retained rather than rewritten
as a first-try success.

This checkpoint predates the paragraph that records its own object IDs, so its tree is
non-cyclically bound by the external receipt. It is a restore point, not a test pass or release
candidate.

The 21-path recovery/adjudication record was then committed unsigned and fast-forward pushed to
`main`:

```text
ca24ab8ebade81a94ffc001531abaf5a5579d5e9
audit: preserve KSG recovery evidence
parent 118e1de6a2d6d2ae33fe7bdc224736257e42a83f
```

`git ls-remote` matched the pushed commit. The milestone promotes audit custody only; it stages no
scientific source and does not change the repository/publication integration NO-GO disposition.

## Exact replay chronology and source classes

Every recovered path was classified before use:

1. pushed Git objects supplied the delivery/formal anchor and unchanged historical bytes;
2. the first explicit checkpoint supplied the settled source/test/fixture slice;
3. preserved patch events supplied reviewed additions and updates;
4. untruncated command-output chunks supplied three large historical checker/packet files;
5. deterministic generators supplied canonical JSON/Markdown projections only when their output
   matched the recorded target digest; and
6. current ambient bytes were admitted only after a recorded digest and semantic provenance
   matched. No directory was copied wholesale.

The original preclosure Fable context was reconstructed offline from 31 individually hash-gated
artifacts. The exact recovered records are:

```text
21a08acd99bfc5c5881a6d267382bc808075fb69bca9ae6f76b103775c5f3ee3  context, 662079 bytes
cfdf84ba5ca1e51c215b7785d577c7378e4836d213de12230caf5449f33e010b  receipt, 7831 bytes
b4cac94ca6b636d8f5433bc3e2112f5cee7c118aa60cff9a321ea1fdcaf7dd9a  response, 15681 bytes
```

[`recover-fable5-ksg-rev4-preclosure-20260727.py`](recover-fable5-ksg-rev4-preclosure-20260727.py)
is the offline recovery program and
[`fable5-ksg-rev4-preclosure-recovery-manifest-20260727.json`](fable5-ksg-rev4-preclosure-recovery-manifest-20260727.json)
records the transcript call IDs, patch timestamps, 31 artifact digests, toolchain detail, and final
byte gates. The recovery did not read `.env`, did not use the network, and passed a secret-pattern
scan. These are recovered historical bytes, not a rerun and not evidence for later integration.

## Recovery incident retained

One generated relative-path patch was accidentally applied from the ambient checkout and created
the new file `claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json` there. The file was immediately
removed with an explicit patch. No pre-existing ambient byte was changed. Subsequent edits use
absolute candidate paths. This incident is retained because path-resolution mistakes are part of
the orchestration threat model; it is not silently omitted because the edit was reversible.

## Fresh external advisory attempts

All five configured Anthropic aliases were attempted once through the recorded max-effort runner.
No key value is present in the evidence:

- three Fable 5 responses completed: proof/SMT, floating-point/refinement, and statistical lenses;
- `NINTH_ANTHROPIC_API_KEY` and `EIGT_ANTHROPIC_API_KEY` returned the provider's insufficient-credit
  HTTP 400 response; and
- the three completed calls used 137339 output tokens, including 100885 thinking tokens.

The canonical receipt SHA-256 is
`8f3308ecc873628bd675df3e974593eb130e855e591def8ce25e001fde56327b`; the combined visible-response
SHA-256 is `227214d20e2273c637d5c817250f6d8c8fb50bdeed56ad458a87b40331e8dd6f`.
The responses are advisory attack input. Allegations are accepted only after independent
inspection or a replayable counterexample/proof. Exhausted credit is not treated as a blocker:
native agents and local formal/numerical tools continue.

## Hostile-review adjudication

The historical and fresh allegations have been independently classified in
[`fable5-ksg-rev4-adjudication-20260727.md`](fable5-ksg-rev4-adjudication-20260727.md) and its
machine-readable JSON companion. Their SHA-256 digests are:

```text
19d284f357eaaecdd63580663c184838f6d31b09fac01d4f08c90e177bb4afec  human rendering
0fa2904476cd400720a752e497c8e463a4c54855d1f3091eeae89cb61b4c2919  machine rendering
```

No new bounded-arithmetic-core blocker survived adjudication. The record nevertheless admits
specific hardening: a successor-indexed/recurrence Lean supplement, an all-unique W2 endpoint
regression, precise reciprocal-summand-denominator terminology, an exact shipped-versus-paper KSG
registry, and independent evaluation of SMT mutant models. It rejects, with exact reasons or
counterexamples, a universal `1/(n-1)` nonzero gap, the zero-residue converse, lexicographic sign
from prime exponents, unbridged transfer of a published KSG theorem, and an unproved universal
`28 epsilon` bound. Deferred cvc5, Kani, MPFR/Arb, Gappa/Flocq, statistical, and PID3 routes remain
non-evidence until their stated bridges and mutations exist.

## Fail-closed observation during recovery

An initial targeted Rust build stopped in `pid-core/build.rs`: the committed
`method-catalog.json` digest did not match the embedded software-identity digest. That is an
expected open dependency while the lost catalog/identity closure wave is absent. The build was
not bypassed, and the failed invocation is not a Rust-test pass.

After byte recovery, normal and optimized diagnostic replays of the Z3 obligations, modular
certificate, exact-rational directed enclosure, and claim-only checker matched their recorded
outputs. Lean correctly failed closed because its former temporary Mathlib checkout was absent.
Those diagnostics locate corruption; none is credited as final settled-tree evidence. A pinned
Mathlib rebuild and a new final-byte replay remain required.

## Loss-prevention and evidence-credit policy

1. Long-running scientific candidates use a durable sibling worktree, not a temporary-directory
   worktree.
2. Every coherent edit wave receives an explicit-path alternate-index checkpoint ref and a
   verified bundle in durable adjacent storage.
3. Active model-response files and unrelated ambient changes are excluded from checkpoints until
   they settle and are explicitly admitted.
4. A recovery transcript maps each restored byte to a pushed object, surviving artifact with
   verified digest, generator, or preserved patch.
5. Only verification performed after every writer stops on the final bytes can support GO.
6. Promotion uses an isolated explicit-path staged tree and small unsigned commits. The mixed
   ambient worktree is never staged wholesale.

Recovered dependencies now include the certificate/mutation artifacts, revision-4 claim and
custody packet, catalog/release/identity/ecosystem projections, automation wiring, and both old
and fresh model-review records. Remaining blockers are analytic/formal strengthening and replay,
phase-isolation hardening, the complete settled-tree matrix, isolated staged-tree verification,
and pushed Git receipts.
