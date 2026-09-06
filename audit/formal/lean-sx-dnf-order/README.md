# DNF and categorical event order

This lane proves the correspondence between redundancy order and reverse DNF implication,
then connects it to categorical equality events. The reflection theorem assumes
that every Boolean equality pattern can occur in the domain. Antichain uniqueness and four
counterexamples explain the role of those assumptions.

Read the [exposition](EXPOSITION.md) for the proof, the [symbol map](SYMBOL_MAP.md) for notation,
and the [theorem table](SOURCE_CORRESPONDENCE.md) for exact premises and Lean names.
[Candidate.lean](Candidate.lean) and [Contract.lean](Contract.lean) are the accepted source bytes.
The [verification record](../../evidence/dnf-order-formal-verification-2026-09-05/RESULTS.md)
preserves the successful checks, failed attempts and judge amendment. The aggregate Lean project
remains a separate baseline.

## Replay the proofs and controls

Use Python 3.11 or newer on a POSIX host with the existing
[Lean 4.33.0 and nine-package pins](../LEAN_4_33_FREEZE_AND_REPLAY.md). The launcher checks and
stages the exact inputs, then invokes the unchanged judge. It does not install dependencies.

Run from the repository root. Each run name must be new:

```bash
dnf_manifest=c011a0e2414dbdf33a2f8374f8a6a40d53c974e1f46f3bb7db3e5c9cb13e9013
python3 -I -S -B audit/formal/lean-sx-dnf-order/replay.py --root . --run-name selected-normal-01 --manifest-sha256 "$dnf_manifest"
python3 -I -S -B -O audit/formal/lean-sx-dnf-order/replay.py --root . --run-name selected-optimized-01 --manifest-sha256 "$dnf_manifest"
python3 -I -S -B audit/formal/lean-sx-dnf-order/replay.py --root . --run-name controls-normal-01 --action self-test --manifest-sha256 "$dnf_manifest"
python3 -I -S -B -O audit/formal/lean-sx-dnf-order/replay.py --root . --run-name controls-optimized-01 --action self-test --manifest-sha256 "$dnf_manifest"
```

Outputs are retained under
`.local/sx-dnf-order-public-replay-v1/<run-name>/judge-v3/runs/replay/`.
Read `receipt.json` for a proof replay or `selftest-receipt.json` for the controls.
`--prepare-only` captures inputs and writes a command plan without running Lean.
`--source cosmetic` applies the previously declared comment-only variant to a proof replay.

The judge checks thirteen complete receiver-free types against raw and alias targets, their
universe parameters and transitive axioms, and the exact public theorem roster. It then runs
`leanchecker --fresh SemanticJudge`. The permitted axioms are `Classical.choice`, `Quot.sound`
and `propext`; each theorem's actual set appears in its result record.

Each Lean command uses `-t 0 -M 4096`, a 600-second timeout and a 4 MiB limit per output stream.
Process-group RSS polling enforces an observed 4 GiB threshold; it is not a hard OS cap on macOS.
The [resource contract](judge-v3/RESOURCE_AND_EXECUTION_CONTRACT.md) states the observation and
cleanup limits. Resource failures are operational outcomes, separate from mathematical rejection.

## Replay the reporting regression

After a selected-source pass, supply its exact receipt digest to the separate repaired-source
helper:

```text
python3 -I -S -B audit/formal/lean-sx-dnf-order/replay.py --root . --run-name reporting-regression-01 --action reporting-regression --accepted-run .local/sx-dnf-order-public-replay-v1/selected-normal-01/judge-v3/runs/replay --accepted-receipt-sha256 <receipt-sha256> --manifest-sha256 c011a0e2414dbdf33a2f8374f8a6a40d53c974e1f46f3bb7db3e5c9cb13e9013
```

The helper restores the exact failed reporting module and requires its thirteen original monad
mismatches. Its identity is separate from the original frozen helper, which still binds the
earlier source. The [history and scope record](../../evidence/dnf-order-formal-verification-2026-09-05/RESULTS.md)
keeps these revisions and their results distinct.

The mathematical result concerns event logic. Numerical atoms, estimators and compiled-code
correspondence need their own proofs or validation.
