# Proposed portable replay and remaining gates

This adapter has been prepared as source only. It has not been invoked, including in preparation mode. It does not inherit permission, attempt counters or a deadline from any closed scientific campaign. Its source and operational controls need adoption before the commands below are executed.

## Changes and exact reuse

[replay-proposed.py](replay-proposed.py) replaces private preparation/campaign routing with explicit canonical repository, toolchain and new output-stage paths. It stages the exact accepted 24-source graph in a fresh source/build tree. It imports no project-local compiled module and invokes no aggregate build or development-proof route. The [manifest](replay-proposed-v1.json) binds the adapter, exact sources, controls, expected records and documentation; the caller must supply that manifest's digest.

The unchanged [runtime](replay-support/runtime.py) supplies byte snapshots, strict JSON, resource monitoring and child-process handling. The unchanged mean, MGW and probability policies remain separate. Their complete semantic judges and the combined root are copied from the actual accepted run. The new adapter compares the three mean records and the inherited eleven/six arrays with their exact accepted records. It permits only the historical three standard axioms.

The new route removes candidate development, old preparation receipt paths, cached development objects, historical STOP/deadline mutation and pre-candidate claims. It adds a packaging registration, manifest pin, fresh output ledger, host-local tool-byte pins and a separately recorded direct version probe. Its wrong-final-target check additionally requires the actual raw/alias mismatch marker and the first two exact accepted records. The wrong target is the same historical transformation, replacing the final export with a theorem of `True`; no mathematical target is edited.

The `runtime.py` contains unused generic judge/preparation functions because its accepted bytes are retained. This adapter calls only the documented helpers and `Runner(..., preparation=False)`. It never calls the old runtime `main`, `prepare`, or `check_freeze` functions, nor the old candidate campaign wrapper. Exact source reuse is historical control evidence about those original bytes; new routing call sites still need fresh causal controls.

## New registration and limits

Create one new stage beneath `.local/prefix-mgw-mean-public-replay-v1/`. Use [REGISTRATION.template.json](REGISTRATION.template.json) as a schema example, fill the actual UTC start/deadline, owner, reviewed manifest digest and the observed SHA-256 of `bin/lean` and `bin/leanchecker` for the chosen canonical toolchain prefix. The placeholder template is deliberately not a live registration. Freeze the exact `REGISTRATION.json` bytes and pass their digest to every invocation.

Execution additionally requires a separately adopted `CONTROLS_ACCEPTANCE.json` in that stage, bound by its digest in the registration and by the exact adapter/manifest hashes. The [controls-acceptance template](CONTROLS_ACCEPTANCE.template.json) is deliberately pending and fails that guard. Root must replace its placeholders with the actual bounded control evidence and review disposition. Preparation-only staging bypasses this execution guard and grants no proof or control acceptance.

The proposed production matrix has one owner, one active wrapper, an actual 120-minute interval, at most six full invocations, at most 150 compiler/kernel children and at most six direct tool probes. All normal/optimized runs share that ledger and deadline. Four positive passes plus one actual negative run require 123 compiler/kernel children and five version probes. The sixth slot can preserve one operational retry within the original limits, without changing the frozen adapter or proof sources. A `--prepare-only` invocation consumes a slot and is never a proof pass; perform preparation controls under their separately registered controls stage if the retry slot is to remain available.

Each compiler/kernel child retains the original 600-second timeout, clamped to remaining stage time, Lean `-t 0 -M 4096`, a 4 GiB observed process-group RSS threshold, and 4 MiB retained stdout and stderr limits. A direct `lean --version` probe is registered separately and limited to 60 seconds. The pinned dependency helper's read-only Git preflight retains its original per-query timeout; the adapter checks the stage deadline after that preflight and before any compiler/kernel child. This is not a hard wall-clock kill of every helper query. Root should retain an external stage supervisor and verify the expiry-during-preflight control before adoption. Observed RSS is not a hard macOS address-space cap.

The unchanged runtime hashes staged Lean inputs inside its child registration after the adapter's last caller-side deadline check. The check and process launch are not atomic. A source-bound delayed-registration control and the external stage supervisor are material adoption obligations; the caller timeout alone must not be advertised as a hard aggregate deadline. If root resolves this by revising a runtime hook instead, preserve these original utility bytes and bind the new hook/source controls separately.

The caller supplies an already installed pinned toolchain; the adapter installs or downloads nothing. It checks the existing repository toolchain/lake/manifest/helper bytes, nine dependency checkouts and the explicitly added Mathlib `NatInt.lean` import source. Version parsing binds Lean 4.33.0, commit `d8b18978322de05a8f3dba51ef03cf5461676c17`, release build. Host binary hashes are recorded in the new registration, separate from portable version and package-source pins. Fresh project objects are built in this attempt; external dependency caches are still reused under the existing declared trust boundary.

## Commands after review, registration and adoption

Run from the repository root. Here `mean_stage` is the newly registered stage path, `mean_manifest` and `mean_registration` are exact reviewed digests, and `mean_toolchain` is the canonical installed prefix. These names are task-specific shell variables. No command in this proposal was executed.

```text
python3 -I -S -B audit/formal/lean-prefix-mgw-mean/replay-proposed.py --root . --stage "$mean_stage" --manifest-sha256 "$mean_manifest" --registration-sha256 "$mean_registration" --toolchain-prefix "$mean_toolchain"
python3 -I -S -B -O audit/formal/lean-prefix-mgw-mean/replay-proposed.py --root . --stage "$mean_stage" --manifest-sha256 "$mean_manifest" --registration-sha256 "$mean_registration" --toolchain-prefix "$mean_toolchain"
python3 -I -S -B audit/formal/lean-prefix-mgw-mean/replay-proposed.py --root . --stage "$mean_stage" --manifest-sha256 "$mean_manifest" --registration-sha256 "$mean_registration" --toolchain-prefix "$mean_toolchain" --source cosmetic
python3 -I -S -B -O audit/formal/lean-prefix-mgw-mean/replay-proposed.py --root . --stage "$mean_stage" --manifest-sha256 "$mean_manifest" --registration-sha256 "$mean_registration" --toolchain-prefix "$mean_toolchain" --source cosmetic
python3 -I -S -B audit/formal/lean-prefix-mgw-mean/replay-proposed.py --root . --stage "$mean_stage" --manifest-sha256 "$mean_manifest" --registration-sha256 "$mean_registration" --toolchain-prefix "$mean_toolchain" --action wrong-last-target
```

Each positive command must produce `fresh_semantic_kernel_pass`, the exact same ordered three/eleven/six arrays, 25 compiler/kernel children and one separately named version probe. Each negative command must produce `expected_target_rejection`, 23 compiler children, one probe, and the actual last-type mismatch after a same-stage selected-source positive pass. The two earlier mean records are retained; they are not counted as a separate two-proof acceptance. A parser mutation or an early source-policy refusal cannot replace this negative run.

Every attempt stores registration, source preimages/executed bytes, the command plan, environment, bounded streams, child records, captured input buffers, post-run identities and artifact hashes. Partial failures are terminal evidence for that invocation. The new `RESULT.json` means a packaging execution, whereas the historical results under the evidence tree mean their original candidate executions. A rewritten historical path does not create a new pass.

## Adoption sequence

1. Read the exact source/diff inventory, [dependency ownership](DEPENDENCIES.md), adapter and historical projection. Rehash all adopted files. Resolve every missing public dependency link/status explicitly.
2. Adopt a separate bounded controls registration; implement/run the [control matrix](CONTROL_PLAN.md) against these exact adapter bytes in normal and optimized modes. Preserve actual failures and causal errors. No synthetic proof receives mean-proof credit.
3. Review resulting controls and freeze the final adapter/manifest. A source repair changes their hashes and requires a new explicit disposition; it must not be hidden behind an old receipt.
4. Register and run the fixed five-run production matrix above with the selected proof bytes unchanged. Root inspects all three families, wrong-target cause, child cleanup and final source/artifact rehash; it then seals a new packaging acceptance and STOP.
5. Only then update source-index/result/catalog/changelog claims with precise statuses, run the applicable catalog/source/documentation gates, and use the current hosted integration procedure. Historical accepted claims remain separately linked.
6. Build Markdown/PDF and validate the reused SVG through the actual publication pipeline in a later stage. This source proposal supplies no PDF, figure render, font, link-layout or visual QA evidence.
