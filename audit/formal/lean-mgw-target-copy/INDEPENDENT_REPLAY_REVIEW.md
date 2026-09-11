# Independent fixed-source replay review

Source-only review on 2026-09-11. I did not execute Lean, `leanchecker`, or the replay driver.

Reviewed bytes:

- `run-replay.py`: `f9e140af3273fce688e10884b4acb6102912011eb078dc4f93cd9eacc6040801`
- `REPLAY_MANIFEST.json`: `3073730523329d8d0690e229e9f484bb3bc28a6d928e0260b1ea3f69a797114c`
- `REPLAY_SCOPE.md`: `628580c68901d50d8ec83af0757c86ae4e0c581aedbe6d149ce902de58c36ffb`
- `SOURCE_GRAPH.json`: `317b293f4703de7136b47b3ed24bdf4da5238d99e763d63d8a006742ae565077`
- inherited `adapter-v2/runtime.py`: `bd8a9f2272a20422863c9902ce2148d2957471bb958d13949fece923cb6a7f5d`

## Disposition

No remaining source-level blocker was found for registration and native entry of this exact plan.
The registration must bind the exact driver and manifest digests above. Actual execution, outer
return, empty final process observations, the separate post-run process-ownership inspection, and
root review remain required; this review grants no execution or target acceptance.

The fixed graph contains 17 distinct modules in dependency order and 11 distinct candidate/target
pairs. The three exact historical reports contain matching distinct rosters of 4, 5, and 2 targets.
The driver admits exactly 18 fixed commands: 17 source compiles, including all three judge modules,
then `leanchecker --fresh PidMgwTargetCopyCandidate.Bounds`. It starts with empty project source and
object trees, copies every source from a digest-bound canonical single-link input, requires exactly
one new nonempty object per compile, rejects changes to prior objects, and requires the final kernel
call to leave object membership unchanged. Exact judge stdout hashes advance the matched target
count from 0 to 4 to 9 to 11. New acceptance remains zero and root review remains pending.

No command or source is accepted directly from an execution argument. Entry requires exactly an
absolute registration path and its SHA-256; the registration binds this driver and the fixed sibling
manifest. Commands use absolute executable paths and argument vectors without a shell. The manifest
binds the runtime, selected executables, source graph, and all 17 source files. This is integrity
under the separately reviewed registration, not authentication against a party able to replace and
re-register the plan.

The final scope now states the relevant boundaries accurately. Installed external Lean/Mathlib and
package objects, dynamic libraries, Python/OS behavior, and source-to-binary correspondence remain
assumptions rather than captured inputs. Sequential observations are not an atomic snapshot or load
trace. `leanchecker --fresh` replays the non-unsafe, non-partial constants of the loaded Bounds
environment through the same Lean kernel; it is not an independent kernel, does not establish axiom
truth, and does not enforce the project allowlist. The preceding three judge compiles execute the
original `run_cmd` checks and must reproduce the exact full-type/axiom reports.

## Corrected blocking findings

1. The pre-review result always reported `accepted_targets: 0`. The successor separates the
   11-target original scope, exact matched report count, zero new acceptance, and pending root review.
2. The pre-review manifest incorrectly said the replay did not rerun judges. It now distinguishes
   the final fresh checker call from the preceding judge compilations that execute all three judges.
3. The inherited Runner can detect but cannot safely kill an in-group descendant after the command
   leader has been reaped. The manifest and scope now state that exact limitation, require empty
   final observations plus a separate ownership inspection, and make no command-tree termination or
   general containment claim.
4. The pre-review manifest described the fresh replay too broadly. It now records the same-kernel,
   non-unsafe/non-partial constant boundary implemented by `Lean.Environment.replay`.

Only `Snapshot`, `Runner`, and the helpers reached from those classes are used from the inherited
runtime. Its unrelated legacy judge/preparation routines were reviewed as unexecuted by this driver
and receive no evidence credit here.
