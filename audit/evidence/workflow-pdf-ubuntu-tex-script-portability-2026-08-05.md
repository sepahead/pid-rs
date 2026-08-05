# Workflow-PDF Ubuntu TeX-script portability correction - 5 August 2026

## Retained failure

The formal-PDF job for commit `9031230d0ab6e0878fe8b9ba38578a80c9439776` failed in CI run
`31002580047`, job `92294747681`, step 10. The retrieved raw job log has SHA-256
`341df39b8d93231ee1e9ca5c096f3626dc3d8541a44fa38e34a346f6c0cda082`.

The workflow synchronizer, its 13-case normal and optimized self-tests, the 24 log mutations, and
the 25-case render comparator passed. The top-level workflow-PDF hostile suite then expected a
partial publication-lock environment to reach its named rejection. Before that branch, the
production checker resolved `/usr/bin/luaotfload-tool` to
`/usr/share/texlive/texmf-dist/scripts/luaotfload/luaotfload-tool.lua` and correctly rejected the
target because `/usr/share/texlive` was outside its admitted executable roots.

This is a cross-platform command-layout defect in the hosted harness. It is not a mathematical
counterexample, a PDF-content discrepancy, a Lean failure, or evidence that the script bytes were
malicious. The negative result remains non-crediting.

The first correction, commit `b7d30dc0c2a416a8f770becfd56afa10d68b7323`, fixed that admitted-root
failure and made the certified-SxPID2 job green, but exposed a second search-order defect in CI run
`31006771510`, job `92308580575`. The exact raw job log retrieved through the GitHub job-log API has
SHA-256 `fce88481e2e3a8b39e76b4dc457f821195bdee11f814c41a589f6d99b04d5265`.
The first correction placed the byte-identical script in a distinct private subdirectory under
`setup-python` and put that directory first in the supplied path. The checker constructs its safe
path from the directories of resolved commands in command-inventory order. Because ordinary system
commands introduce `/usr/bin` before the later `luaotfload-tool` entry, a nested capture could
resolve the system path before the private copy and rejected:

```text
mathematical workflow PDF check: isolated search path resolves different executable bytes: luaotfload-tool
```

The named partial-publication-lock hostile case consequently could not reach its expected rejection
branch. This is a real nested path-replay portability failure, not a content, mathematics, TeX
compilation, Lean, or SxPID failure. The first correction and its hosted run receive no closure
credit.

The second correction, commit `0ee2fc8885308b0bbefbe72bebb8de99bf6583f6`, closed that nested
resolution defect but exposed a third, independent setup premise in CI run `31009447503`, job
`92317601680`. The raw job log retrieved through the GitHub job-log API has SHA-256
`8a735c39a6ecc03833ca62ecfcbb5f0a468738942c5d9abc65789ce7aceb3fcf`. All 175 bounded workflow-PDF
controls and the first six ordered paper build/cross-toolchain validations passed before the
foundational Lean wrapper rejected this exact stderr from its version probe:

```text
info: downloading https://releases.lean-lang.org/lean4/v4.32.0/lean-4.32.0-linux.tar.zst
info: installing /home/runner/work/_temp/pid-rs-formal-pdf-home/.elan/toolchains/leanprover--lean4---v4.32.0
```

The outer gate deliberately supplied a fresh `HOME`. The wrapper deliberately removes inherited
`ELAN_*` routing before launching the selected `lake` proxy, so the proxy correctly looked in that
clean home's default `.elan` state and found no installed toolchain. Elan then bootstrapped the
tracked release inside the evidence probe. The wrapper's empty-stderr premise correctly failed.
This is a hosted setup/isolation defect, not a theorem rejection, Lean-version mismatch,
PDF-content discrepancy, TeX failure, or mathematical counterexample. Commit `0ee2fc8` and this run
receive no closure credit even though they establish that the preceding TeX resolution correction
reached its intended path.

The exact-head inventory was retained to terminal rather than cancelled by a successor push. CI run
`31009447503` completed at `2026-08-05T14:52:58Z` with 44 successful jobs, this one failed job, and
zero cancelled, skipped, or nonterminal jobs. Its KSG arithmetic/phase-isolation job `92317601574`
completed successfully one second earlier, including the long exact Git phase-envelope step.
CodeQL run `31009446387` completed separately with all four jobs successful and no failure or
cancellation. These outcomes do not rescue the failed PDF job or make the exact head green; they
preserve the failure boundary and show that no unrelated hosted gate was discarded to publish the
next candidate.

## Correction and bounded rationale

The second correction makes the TeX resolution fixed point explicit. The Ubuntu 24.04 job now:

1. resolves `/usr/bin/luaotfload-tool` with the absolute system `readlink`;
2. requires the exact observed canonical TeX Live target above;
3. requires the destination `$pythonLocation/bin/luaotfload-tool` to be absent, including as a
   dangling symlink;
4. creates a same-directory staging file, installs the exact source bytes there with mode 0755,
   compares it with the absolute system `cmp`, and publishes it through GNU `ln -T` without `-f`.
   The link treats the destination as a path rather than traversing a raced directory symlink and
   fails instead of overwriting a destination introduced after the initial check. The job unlinks
   the staging name and compares the published path with the source again; and
5. starts the clean path with `$pythonLocation/bin`, the already admitted directory containing the
   selected `python3`. That directory is therefore also first in the checker's reconstructed safe
   path, independent of the later `luaotfload-tool` inventory position.

The production checker therefore reaches the same copied path before and after nested safe-path
reconstruction, while retaining the original root policy. Its existing executable-custody route
also records the script's `env`/`texlua`
interpreter closure, re-resolves commands at multiple checkpoints, and compares admitted executable
manifests before and after use. The copy does not authenticate the distro source, Python root,
kernel, filesystem, or interpreter. It does not make the PDF verifier independent and does not
alter any scientific claim or rendered artifact.

The third correction keeps the proof check strict and moves tool installation out of the evidence
probe. The job first requires both clean-state paths to be absent and creates each with exclusive,
fail-closed `mkdir` semantics and mode 0700 rather than accepting a pre-existing directory. The two
directory creations are not one atomic set operation. It then:

1. fixes the requested toolchain to `leanprover/lean4:v4.32.0` and requires its newline-terminated
   bytes to equal `audit/formal/lean/lean-toolchain` exactly;
2. invokes the already installed, archive-hash-pinned Elan 4.2.3 launcher under `env -i`, with
   `HOME` and `ELAN_HOME` both rooted in the new gate home and `TMPDIR` rooted in the new gate
   temporary directory, to install that exact named release;
3. rejects a symbolic-link `.elan`, then enters the formal-PDF gate only after installation, again
   with the clean home and its `.elan` state; the hash-pinned Elan proxy directory is first in that
   outer path so a future runner-image `lake` cannot shadow it; and
4. leaves the Lean wrapper's portable version/source-commit parser and empty-stderr requirement
   unchanged.

This separates visible bootstrap diagnostics from the silent evidence observation. The tracked pin
and later exact version/commit check constrain the selected release, but neither the setup command
nor the receipt authenticates Lean's distribution service, archive bytes, the Elan executable after
installation, the runner, loader, operating system, or kernel. The 4.32.0 route is also a historical
runtime pending the separately adjudicated 4.32.2 migration; no result transfers across versions
without a fresh receipt.

The certified-SxPID2 job, Just recipe, and release-audit slices remain independently frozen. Because
the complete CI workflow and `scripts/README.md` are also custody objects, their new exact digests
must be explicitly re-adjudicated; no blanket or semantic-slice substitution is permitted.

## Local replay observations retained without closure credit

The first local aggregate replay in a new isolated checkout passed the 175 workflow-PDF hostile
controls and the first six paper checks, then stopped before the foundational paper because
`audit/formal/lean/.lake/packages` was absent. That is an unmet local provisioning premise, not a
Lean rejection or a paper discrepancy. The checkout's tracked `lean-toolchain`,
`lake-manifest.json`, and `lakefile.toml` bytes did not change.

A direct `lake exe cache get` began cloning the pinned Mathlib checkout but was deliberately
interrupted rather than silently waiting on a slow transfer. A copy-on-write diagnostic copy of an
existing ignored `.lake` tree was then admitted only to test cache contamination behavior. Its
subsequent `lake build` failed because a retained native-object recipe named an obsolete temporary
Lean include prefix and could not find `lean/lean.h`. This is a concrete stale-derived-cache
negative: exact Git revisions alone do not make copied build products portable. The copied cache is
not accepted as a clean Lake build or independent dependency acquisition.

With the copied package checkouts present, the foundational paper/Lean gate and then the complete
nine-paper cross-toolchain aggregate did pass. That bounded result checks the current paper bytes,
the exact tracked manifest/configuration/toolchain bytes, theorem acceptance by the locally
selected Lean implementation, and the PDF structural/pixel contracts. The foundational wrapper
does not authenticate the live dependency package/cache contents or prove their Git
revision/origin/cleanliness. Because the copied derived state failed its own build, this local
result is intentionally not promoted to clean-build, cache-portability, archive-authentication, or
hosted-Linux evidence. The successor hosted job must perform its ordered cache fetch and build
successfully before running the same aggregate.

The third correction candidate's exact enclosing digests are:

| Bound object | SHA-256 |
|---|---|
| complete `.github/workflows/ci.yml` | `fd93c27452fa6b09a9e93b143193a6caeb35e3256e7bfdd839e7b8664e4cd5d0` |
| complete `scripts/README.md` | `674a21030e14f50a15c80c3bff2580a3d17e86290c4bdbce5d4a2edb8b4b08ce` |
| unchanged complete `justfile` | `39440fdf9d3b9c49b4721771a89ebc759d1e2fcea7f2f6cebb5a45cbae520605` |
| unchanged formal-PDF dispatcher | `975452402a16665ca9347a5523dc01a160985b0e50ee3a26dea788716c09149f` |

## Required closure

Local source/gate checks cannot reproduce Ubuntu's exact TeX Live layout or hosted x86_64 Lean
bootstrap. A local clean-home Darwin replay was begun but deliberately stopped after the official
530 MiB archive transfer proved too slow and supplies no positive evidence. Credit therefore
requires the relevant local claim and mutation gates plus a new exact-head hosted run in which both
the formal-PDF job and the certified-SxPID2 job finish successfully. Until then this is a correction
candidate, not a closed portability result.
