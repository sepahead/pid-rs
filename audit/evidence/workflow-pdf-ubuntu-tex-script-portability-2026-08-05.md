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

## Correction and bounded rationale

The second correction makes the resolution fixed point explicit. The Ubuntu 24.04 job now:

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

The certified-SxPID2 job, Just recipe, and release-audit slices remain independently frozen. Because
the complete CI workflow and `scripts/README.md` are also custody objects, their new exact digests
must be explicitly re-adjudicated; no blanket or semantic-slice substitution is permitted.

The second correction candidate's exact enclosing digests are:

| Bound object | SHA-256 |
|---|---|
| complete `.github/workflows/ci.yml` | `b83cf45199d2521bc33f034438463200c2717e1c1cf432b56447829c7cf91b7f` |
| complete `scripts/README.md` | `d4cf1a95531fd1c3f6d6c949be9bf5f386964b7a85e53c8717fadb6b976ec0d9` |
| unchanged complete `justfile` | `39440fdf9d3b9c49b4721771a89ebc759d1e2fcea7f2f6cebb5a45cbae520605` |
| unchanged formal-PDF dispatcher | `975452402a16665ca9347a5523dc01a160985b0e50ee3a26dea788716c09149f` |

## Required closure

Local source/gate checks cannot reproduce Ubuntu's exact TeX Live layout. Credit therefore requires
the relevant local claim and mutation gates plus a new exact-head hosted run in which both the
formal-PDF job and the certified-SxPID2 job finish successfully. Until then this is a correction
candidate, not a closed portability result.
