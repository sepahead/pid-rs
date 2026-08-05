# Workflow-PDF Ubuntu TeX-script and font-layout portability corrections - 5 August 2026

## Retained hosted failures

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

The third correction, commit `da6bdfe9237f7fb885a26c9d0f6fa29baf446013`, closed that clean-home
setup defect but exposed a fourth, independent Ubuntu font-layout premise in CI run `31018088910`,
job `92347360785`. The raw job log retrieved through the GitHub job-log API has SHA-256
`370584006a86b28ca2cd5f91b7942201f7b66696ad25fc3bdbbd03fb52c9d868`. Step 9 installed Ubuntu
Noble `lmodern` 2.005-1 and its `fonts-lmodern` 2.005-1 dependency; the log records both packages
being unpacked and configured. All 175 bounded workflow-PDF controls and the first seven ordered
paper validations passed before the mathematical-workflow checker rejected:

```text
mathematical workflow PDF check: required TeX font is unavailable: lmroman10-regular.otf
```

Ubuntu Noble's [package index](https://packages.ubuntu.com/noble/lmodern) separately records that
`lmodern` 2.005-1 depends on `fonts-lmodern` 2.005-1, and the
[`fonts-lmodern` file inventory](https://packages.ubuntu.com/noble/all/fonts-lmodern/filelist)
places the requested file at
`/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf`. The prior checker instead
constructed every Latin Modern OpenType path beneath `/usr/share/texlive/texmf-dist`. This is a
hosted package-layout defect, not an absent-font result, PDF-content discrepancy, TeX compilation
failure, Lean rejection, SxPID failure, or mathematical counterexample. Commit `da6bdfe` and this
run receive no closure credit, although the completed certified-SxPID2 job and the seven preceding
paper checks show that the earlier script-path and Lean-bootstrap corrections reached their intended
lanes.

At `2026-08-05T16:09:34Z`, the enclosing run was still nonterminal: 43 jobs had completed
successfully, this formal-PDF job had failed, and the KSG integer-harmonic/phase-isolation job was
still in progress. Those counts are a timestamped observation, not a terminal exact-head inventory.
The run subsequently completed at `2026-08-05T16:32:13Z` with 44 successful jobs, this one failed
job, and zero cancelled, skipped, or nonterminal jobs. The KSG job `92347360973` completed
successfully one second earlier after its long exact Git phase-envelope step. The terminal successes
do not rescue the formal-PDF failure or give commit `da6bdfe` closure credit. The separate CodeQL
run `31018086368` completed successfully at `2026-08-05T15:02:54Z` with all four jobs successful
and no failure or cancellation; that security-scan result likewise does not repair the publication
gate.

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

The fourth correction leaves the hosted package list, TeX-script normalization, and Lean bootstrap
unchanged. It queries `TEXMFDIST`, `TEXMFROOT`, and the optional Debian packaging variable under the
same clean environment. Upstream Kpathsea 6.4.0 writes a blank line and returns status 1 when that
variable is absent; Bash command substitution removes the trailing line feed before adjudication.
The adjudicator therefore admits only status 0 with a nonempty normalized value or status 1 with an
empty normalized value; every other status/normalized-value combination fails closed. A nonempty
Debian root must be the canonical direct directory `/usr/share/texmf`.

For each of the fifteen literal font filenames, the checker then asks clean-environment
`kpsewhich --must-exist` for the selected path. Every family may use only its filename-specific path
under canonical `TEXMFDIST`; Latin Modern text/mono and Latin Modern Math may additionally use that
same relative path under canonical `/usr/share/texmf`, while Source Sans Pro may not. One Python
process per font opens the selected root and every source component through `O_DIRECTORY` and
`O_NOFOLLOW` descriptors, requires a 1..67108864-byte direct regular leaf, captures it through an
`O_NOFOLLOW|O_NONBLOCK` descriptor, compares name and descriptor identities before and after the
read, and re-walks the full source chain. It creates the private destination through an opened root
descriptor with `O_EXCL`, requires a new single-link regular file, and re-walks the destination chain
after writing. Missing required platform flags fail closed.

This is an exact two-layout selection and bounded byte-capture rule, not a general Kpathsea policy.
It does not authenticate package metadata or font semantics, prove a package installation complete,
exclude privileged mount/filesystem interference, eliminate all mutation races, or make different
TeX toolchains render byte-identically. It changes no mathematical, PID, Lean, or certified-SxPID2
claim.

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

A stable-input local Darwin `--exact` replay of the fourth candidate subsequently passed, including
194/194 current bounded workflow-PDF controls and both same-toolchain builds. It reported these
exact outputs:

| Local exact-pass object | SHA-256 |
|---|---|
| generated PDF | `f372256011d1173a020d39b86cba5ab7959fb07cea09cf1a2b7eeb292a83cafe` |
| dual-render receipt | `847685d91b6a565ba37c077515396e3bb83fb1ed18d295a14b4eb3ebe9bedcaf` |
| executable manifest | `2a58ccb7f06f6a4ee36730e056975e624367cf661751898b562f03001789ad9a` |
| pypdf manifest | `dc0d7ee2d29c666298f5fce601068b2459a4f89057dd42beda343e002b432863` |

This is local same-toolchain evidence for the MacTeX `TEXMFDIST` branch only. It is not Ubuntu,
`TEXMFDEBIAN`, clean-package-installation, cross-toolchain, package-authentication, or hosted closure
evidence.

## Font-correction candidate probes retained without closure credit

An initial optional-overlay draft treated every nonzero status with an empty normalized value as an
absent variable. A clean MacTeX 2024/Kpathsea 6.4.0 query instead returned status 1 and a blank line;
Bash command substitution normalized that trailing line feed to the empty value supplied to the
adjudicator. The overly broad rule was rejected: the final adjudicator admits exactly status 0 with
a nonempty normalized value and status 1 with an empty normalized value. Its five bounded controls
reject status 2/empty, status 1/nonempty, and status 0/empty at that post-substitution interface.
Those same-checker controls do not establish behavior for another Kpathsea implementation.

A manual concurrent-edit probe changed a candidate source during its bounded read and the stable
source-identity check rejected it. A separate hostile probe against an earlier validate-then-reopen
draft replaced an intermediate source directory with a symlink between validation and the absolute
path reopen; the reopen escaped to outside bytes even though `O_NOFOLLOW` protected the leaf. That
demonstration invalidated the draft and motivated the complete descriptor-chain walk and re-walk.
These were interactive local candidate probes without separately hash-bound raw-log receipts, so
they are non-crediting fault observations, not proofs that the final route excludes every race.

The default local Docker store could not supply an Ubuntu container observation. Even the read-only
image inventory failed with `rpc error: code = Unknown` because blob
`sha256:4fbb8e6a8395de5a7550b33509421a2bafbc0aab6c06ba2cef9ebffbc7092d90` produced an
`input/output error` beneath containerd's content store. A separate mount-free `pidrs-noble` Colima
profile launch remained nonterminal before VM/profile creation at the audit cutoff while downloading
its base image. It subsequently terminated at `2026-08-05T18:38:02+02:00` with `unexpected EOF`
after leaving a 220,200,960-byte partial download; the profile never started and no package query or
checker ran. This interactive output has no separately retained hash-bound raw-log receipt. Neither
outcome is Ubuntu validation, and a later successful isolated-profile run would require a distinct
record before it could contribute evidence.

The font-layout correction candidate's exact file digests are:

| Bound object | SHA-256 |
|---|---|
| unchanged complete `.github/workflows/ci.yml` | `fd93c27452fa6b09a9e93b143193a6caeb35e3256e7bfdd839e7b8664e4cd5d0` |
| complete `scripts/README.md` | `9c15eaa9c30718bbcf422c84cc2cae798d17a95754ce3f9419c9e244d002f81d` |
| unchanged complete `justfile` | `39440fdf9d3b9c49b4721771a89ebc759d1e2fcea7f2f6cebb5a45cbae520605` |
| unchanged formal-PDF dispatcher | `975452402a16665ca9347a5523dc01a160985b0e50ee3a26dea788716c09149f` |
| production workflow-PDF checker | `83bc0df3f04ff5849dd047abb6d943b7d773bc136237a0e4f67719f05025118c` |
| workflow-PDF checker self-test | `0821f166d05f9ef645241a59d143aaf5246872452032583b58d0e128d27a5fcb` |
| complete `CHANGELOG.md` | `21289dcd954845009b9a1f170ec3a0925b595886e87cb427c7a60bd66d019231` |
| certified-SxPID2 checker after its sole README rebind | `462095d36a22e79bdf76d6fa249862edf1f5ad9852a33dde39a82801afbfcc09` |

## Required closure

Local source/gate checks cannot reproduce Ubuntu's exact TeX Live layout or hosted x86_64 Lean
bootstrap. A local clean-home Darwin replay was begun but deliberately stopped after the official
530 MiB archive transfer proved too slow and supplies no positive evidence. Credit therefore
requires the relevant local claim and mutation gates plus a new exact-head hosted run in which both
the formal-PDF job and the certified-SxPID2 job finish successfully. Until then this is a correction
candidate, not a closed portability result.
