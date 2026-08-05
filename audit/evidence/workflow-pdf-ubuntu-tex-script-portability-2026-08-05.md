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

## Correction and bounded rationale

The Ubuntu 24.04 job now:

1. resolves `/usr/bin/luaotfload-tool` with the absolute system `readlink`;
2. requires the exact observed canonical TeX Live target above;
3. copies those bytes with mode 0755 into a new private directory under the pinned
   `setup-python` root, which the checker already admits;
4. compares the original and copy byte-for-byte with the absolute system `cmp`; and
5. prepends only that private directory to the subsequently isolated search path.

The production checker therefore executes and captures the copied bytes rather than weakening its
root policy. Its existing executable-custody route also records the script's `env`/`texlua`
interpreter closure, re-resolves commands at multiple checkpoints, and compares admitted executable
manifests before and after use. The copy does not authenticate the distro source, Python root,
kernel, filesystem, or interpreter. It does not make the PDF verifier independent and does not
alter any scientific claim or rendered artifact.

The certified-SxPID2 job, Just recipe, and release-audit slices remain independently frozen. Because
the complete CI workflow and `scripts/README.md` are also custody objects, their new exact digests
must be explicitly re-adjudicated; no blanket or semantic-slice substitution is permitted.

The correction candidate's exact enclosing digests are:

| Bound object | SHA-256 |
|---|---|
| complete `.github/workflows/ci.yml` | `fdabd30ba72121ebd5f53a27615bd145c8356ae598d875add0bd7e150adeee51` |
| complete `scripts/README.md` | `c3d432b769b6e0ef551ca2ad025c13045c051f8c6058c9a203962a913fe6b397` |
| unchanged complete `justfile` | `39440fdf9d3b9c49b4721771a89ebc759d1e2fcea7f2f6cebb5a45cbae520605` |
| unchanged formal-PDF dispatcher | `975452402a16665ca9347a5523dc01a160985b0e50ee3a26dea788716c09149f` |

## Required closure

Local source/gate checks cannot reproduce Ubuntu's exact TeX Live layout. Credit therefore requires
the relevant local claim and mutation gates plus a new exact-head hosted run in which both the
formal-PDF job and the certified-SxPID2 job finish successfully. Until then this is a correction
candidate, not a closed portability result.
