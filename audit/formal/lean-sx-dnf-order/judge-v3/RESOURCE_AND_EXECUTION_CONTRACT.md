# Local revision-3 judge execution contract

This judge checks the adopted thirteen receiver-free targets. It supplies no candidate proof.
The contract is the exact `ProposedContract.lean` from the accepted revision-2 proposal. Its
SHA-256 is `569bf11314d02ff599309bfcfa0d80109bf0f121032d5d665e8519513219a5c0`.
`Contract.lean` retains those exact bytes. The mathematical target and the resource controls
have separate authority. This local record does not establish external judge custody.

## Candidate interface

Use a file named `Candidate.lean`. Its only direct import must be `Contract`. Use these commands
at the start, in this order:

```lean
import Contract
set_option autoImplicit false
set_option warningAsError true
namespace PidSxDnfOrderCandidate
```

Declare the thirteen public theorems in the order in `theorem-roster.json`. Close the namespace
with `end PidSxDnfOrderCandidate`. Helpers must be private theorems or lemmas. Explicit universe
commands and ordinary `open` commands are allowed. The lexical guard rejects extra imports,
extra options, unsupported declarations, proof placeholders, added axioms, native proof
shortcuts, and the listed metaprogramming commands. It is a restricted source policy, not a
complete Lean parser or an operating-system sandbox.

Each export must have the complete receiver-free type. The caller must supply no obligation
structure, assumed conclusion, renamed equivalent premise, or other extra premise. A theorem
restricted to `Fin 3` does not satisfy a general source-index target. Finite categorical targets
retain all declared type and instance binders, including unused binders. Targets retain their
original source, value, and target universes.

## Semantic and kernel checks

`JudgeTargets.lean` gives thirteen independent, fully quantified raw propositions.
`JudgeAliases.lean` gives the fully quantified contract views. `ContractJudge.lean` compares each
pair. `JudgeCore.lean` compares each candidate declaration's complete type with the raw target.
Only universe-name permutations are allowed. An extra explicit or implicit receiver remains a
Pi binder and fails. The export must be a theorem. Its actual transitive axiom set must be a
subset of `propext`, `Classical.choice`, and `Quot.sound`. Empty or smaller axiom sets are valid.
The exact public namespace roster must contain thirteen declarations.

`SemanticJudge.lean` also makes twenty-six kernel-typed applications: one raw-target and one
alias-target application per theorem. It emits thirteen JSON records. Each record includes
the complete elaborated type, universe parameters, and actual axiom roster. The Python parser
rejects missing, duplicate, malformed, reordered, or unexpected records. Parser fixtures contain
synthetic text and are never theorem evidence.

The wrapper reuses the exact pinned informative-invariance and finite-convergence preflight
helpers. It checks the Lean version, package manifest, package Git checkouts, and reviewed source
hashes. It records executable hashes and repository observations. It copies and recompiles the
two required project modules into a fresh attempt directory. It excludes the project's compiled
cache from `LEAN_PATH`. The owned build directory comes first, followed by the nine pinned
package cache locations and the reviewed Lean library directory. An unused package cache
location may be absent, as in Lake's own search path. A required missing import fails in Lean.
The reviewed Lean binary directory comes first in `PATH`, including for leanchecker subprocesses.

Every compilation uses `lean -t 0 -M 4096`. The accepted candidate closure must then pass
`leanchecker --fresh SemanticJudge`. The amendment self-test uses one fresh kernel replay
of the combined positive control closure. All project and judge source inputs are captured
and checked for stable identity and bytes. Exact input bytes, output hashes, raw logs, command
vectors, and receipts remain in the attempt directory.

## Resource revision adopted before the candidate, retained unchanged

The original 4 GiB `RLIMIT_AS` operation failed on this macOS host with
`ValueError: current limit exceeds maximum limit`. The corresponding RSS and data-limit
operations also failed. These observations occurred before any candidate ran. The earlier
preparation attempts are retained. They do not show that the unavailable limit held.

The resource replacement adopted in revision 2 remains unchanged:

- Lean compilation receives `-M 4096`, which limits Lean's allocator.
- The wrapper observes total live process-group RSS. It terminates the group after an
  observation exceeds 4 GiB. The nominal interval between observations is 0.1 seconds, plus
  observation time. This allows overshoot between observations. It is not a hard OS memory cap.
- Each compiler or kernel command has a 600-second limit and a 4 MiB limit on each output stream.
- Each command starts a new session. On failure, the wrapper kills that process group and
  checks that no live member remains. A process that leaves this group is outside this control.
- Nonzero status, unexpected output, timeout, memory excess, output excess, and incomplete
  cleanup all prevent acceptance. Resource failures are operational failures, not countermodels.

The self-test uses reduced fixture limits to exercise the same enforcement paths: a 16 MiB RSS
threshold, a 4096-byte output limit, and a 0.5-second timeout with a child process. It records
actual observed memory and group cleanup. It does not allocate 4 GiB merely to test the constant.
The Python entrypoints require isolated mode, no site import, no bytecode writes, and Python
3.11 or later. Both normal and optimized mode must pass.

## Run and preserve an attempt

Run these commands from the integration root. Use new output directories for every attempt.
Substitute the actual paths and hashes; angle-bracket values below are placeholders.

```text
python3 -I -S -B .local/sx-dnf-order-judge-v3-20260905/selftest.py <root> <lane>/runs/<normal-output>
python3 -I -S -B -O .local/sx-dnf-order-judge-v3-20260905/selftest.py <root> <lane>/runs/<optimized-output>
python3 -I -S -B .local/sx-dnf-order-judge-v3-20260905/judge.py <root> <candidate> <lane>/runs/<attempt> --candidate-sha256 <candidate-sha256> --freeze-sha256 <adopted-frozen-json-sha256>
```

The candidate already existed and compiled before revision 3 was prepared. The coordinator must
adopt the exact successor `frozen.json` digest before any amended full replay. The wrapper requires
`frozen_after_candidate_before_replay`, the exact predecessor freeze identity, and the unchanged
candidate identity at amendment. It verifies the adopted digest and every file that it binds. A changed source requires
a new recorded candidate digest. A cosmetic candidate variant must pass the same semantic and
kernel checks after an explicit test rebind; a source hash mismatch alone is not a semantic
mutation result. Repeat candidate acceptance with Python `-O`.

The amendment control result is narrower than candidate acceptance. A complete thirteen-export
candidate existed and compiled before this amendment. The full positive candidate and cosmetic
semantic replays remain pending at successor freeze. The seventy original controls remain; two
reporting smoke controls exercise the actual term-elaboration IO action and the rejected old
command-specific lift. Three custody controls reject false predecessor or chronology metadata. The finite controls are
reviewer fixtures. The five valid wrong-target proofs are also reviewer fixtures. They are not
candidate exports and do not establish a complete candidate result.

## Limits of the local result

This judge does not claim scientific novelty, external independence, priority, software
attestation, source-to-olean authenticity for cached external libraries, estimator calibration,
continuous PID validity, or consumer deployment readiness. The shared workspace is not isolated
from a malicious actor. Before/after file observations are bounded custody evidence, not an
atomic filesystem snapshot. The retained source pins, package preflight, and fresh kernel replay
have distinct roles and must not be described as interchangeable evidence.

## Reporting amendment and complete regression

[AMENDMENT.md](AMENDMENT.md) records the failed predecessor, the two initial reviews, and the
minimal replacement of thirteen command-specific IO lifts by direct IO actions. No target,
axiom restriction, parser rule, source pin, resource bound, or fresh-kernel requirement changes.
The candidate existed before this repair. This revision is not a pre-candidate registration.

After the first complete selected-candidate pass, run the frozen direct regression command:

```text
python3 -I -S -B .local/sx-dnf-order-judge-v3-20260905/reporting-regression.py <accepted-run> <lane>/runs/<regression-output> --accepted-receipt-sha256 <accepted-receipt-sha256> --freeze-sha256 <adopted-frozen-json-sha256>
```

This control verifies the bound positive receipt, thirteen records, fresh-kernel status, source
bytes, compiler identity, and compiled import artifacts. It restores all thirteen original
reporting statements into an exact copy of revision 2's complete semantic module. It requires
thirteen original monad mismatches, no accepted record, and process cleanup. It uses the already
compiled imports from that full positive run and is a direct compiler control, not another full
wrapper invocation. Its local byte binding does not establish external custody.

The campaign deadline remains 08:32:36 UTC on 2026-09-05, with 64 development compilations and
eight full wrapper runs. Two old-judge failures are consumed. Worker selected-candidate normal
and optimized runs use slots 3 and 4; cosmetic runs use slots 5 and 6. Coordinator selected-
candidate normal and optimized acceptance uses slots 7 and 8. Direct reporting compilation
controls are recorded separately. A new failure consumes its registered attempt. The campaign
is not reset by this amendment.
