# Custody PDF build diagnostics

This record covers the diagnostic observations of 12 September 2026. It concerns publication
tooling and changes no PID definition, theorem, estimator or numerical result. Raw process
records remain in local evidence storage; this public account is
not a complete replay package.

## Failure and cause

The full PDF check returned status 43 at the custody-checker stage. The custody PDF
checker redirected each builder's stdout and stderr into temporary files. A nonzero builder exit
triggered cleanup before the checker forwarded those files. The outer log therefore retained the
exit status but lost the producer's explanation.

A direct invocation of the unchanged builder retained only Pandoc's generic fatal-error message.
A separate diagnostic copy added `--verbose` and kept the same publication inputs. It exposed a
Luaotfload failure while loading its fontloader: no writable cache path was available to the engine.
The named cache directories existed and were writable by the host account.

The private environment put `TEXMFCACHE` in `<run>/tmp/cache` and `TEXMFVAR` in
`<run>/tmp/texmf-var`. Pandoc set its child's `TEXMFOUTPUT` to `<run>/tmp/media-*`. The cache was
outside both allowed private roots. Under the unchanged `openout_any=p` policy, LuaTeX's extended
output-name check also permits paths under `TEXMFVAR` and `TEXMFSYSVAR`. This rule exists to support
Luaotfload caches. Filesystem write permission alone does not establish engine permission.[^1]

Four read-only `kpsewhich --safe-extended-out-name` checks rejected a filename under the original
sibling cache and accepted filenames after aligning the cache with `TEXMFVAR`, aligning
`TEXMFVAR` with the cache, or placing the filename under `TEXMFOUTPUT`. These checks test pathname
admission, not file creation or complete PDF production.

The selected diagnostic environment sets private `TEXMFCACHE` equal to private `TEXMFVAR` and
creates that directory before launch. It changes no global configuration, shell policy,
publication source or PDF comparison rule.

One registered invocation of the unchanged builder then succeeded. The child and outer launcher
returned 0, stderr was empty, and the 182,442-byte PDF matched the tracked artifact byte for byte.
Source, selected native-tool and launcher observations remained equal before and after the run.
This is one-build evidence with a changed working directory and fresh cache. At that observation,
the exact two-build checker and full aggregate remained pending; this diagnostic supplies neither
acceptance.

## Diagnostic retention

At the diagnostic observation, the checker change was a tested proposal and was not installed in
the active checkout. The proposed checker reports the failed build position, labels both captured
streams, forwards their
contents and exits with the builder's original status before cleanup. A first-build failure
prevents the second build. Reporting errors do not replace the captured producer status. Existing
success-path stderr rejection, exact byte comparisons, visual-receipt binding, PDF profile checks
and the unsupported cross-toolchain refusal remain required.

An isolated fixture test of that exact proposal passed 35 controls: 2 accepted cases and 33 hostile
cases, including 19 source-contract mutations. The two added cases fail the first and second builders separately with
status 43. They check both stream markers and labels, invocation counts, absence of acceptance
after failure, and removal of checker scratch. Their constant-byte fixture builder performs no
native PDF production.

## Retained unsuccessful routes and limits

- Repeating the full check without new diagnostics would reproduce the information loss. The
  original failed attempt remains failed.
- Direct nonverbose output was insufficient. Verbose output identified the engine failure; it did
  not establish a successful build or exact reproduction of the original process state.
- A Lua-only probe failed because its requested `lfs.iswritablefile` function was unavailable in
  that mode. An INITEX probe failed at its `directlua` syntax before reaching the intended test.
  Neither result supports a cache-permission conclusion. The documented Kpathsea command replaced
  both probes.
- The diagnostic runs changed their working directory and used fresh caches. Their results cannot
  isolate every environmental difference from the original aggregate.
- The first post-run comparison used an absent undated canonical filename and stopped before
  recording success. The corrected path gave exact byte equality without another builder run.
- No PDF equality tolerance, font profile, security policy or scientific claim was relaxed.

## Evidence identities

| Record | SHA-256 |
|---|---|
| Original aggregate failure result | `3ef821c9056bbcb8071c5f8d862754e5c0d0900a398a12af5e5460faa3f9c146` |
| Direct unchanged-builder failure result | `0bd26919ffb5cf545f42ed42cefb109c2773faf670ddc1cf591c9502ff234707` |
| Verbose diagnostic result | `c9b98b23beb28ccd32df57aae68c7162a77cb20550d1107704f9240f5b6fbe73` |
| Verbose diagnostic stderr | `68f1d0c9a9e016df68f67ca73a64f9d7c088b862d64a7147d5de6c57830caef6` |
| Four Kpathsea pathname checks | `996f4377deb283c64957f6c39b56822367d8756acb8f26385b4582e14927f6d6` |
| Aligned-cache diagnostic result | `7b6627e60b6125f80b4d41bc016365b7a3d12c7dd846ecc8dd85f9567fdb4f55` |
| Root terminal observation and byte comparison | `d2b6129dbea392d6b2a41b883805773f73ab1c8001ccf6e0c75ffe3a79830ebf` |
| Produced and tracked PDF | `d122cec2e2f77cf613a00d28601161cc75a28a93f777700e7919afb4f5fb8550` |
| Isolated fixture result | `65db57e4ff2a84c8630a2e8e4269e1bbcceb9f0c0e176a5c205f4ed649ed0dac` |
| Fixture self-test stdout | `8ba0c86a5b3ef6589d135046acb5951d6465e839e036acbe550835cc193b2ba4` |
| Proposed checker | `df457c854914c10a7dd734509429039698fb41c60587b6a9a6b94fdff6716c55` |
| Proposed self-test | `8dc079f235eacd90793d9d3b4d85dbccf12b297c80d519e943d26e069bee2153` |
| Invalid Lua-only probe result | `918478acf120deabd59d6b1bcfd3145db00c66fa9d0052bb6a8545f53ad93555` |
| Invalid INITEX probe result | `885a32bc4ce237a62a74d327cba799328c447e62c94b6e38e65a1f1b2e8c415d` |

These hashes identify retained records; they do not authenticate execution or prove a broader
claim. The mathematical and numerical acceptance boundaries remain unchanged.

[^1]: Kpathsea manual, [Safe filenames](https://tug.org/texinfohtml/kpathsea.html#Safe-filenames).
    The installed TeX Live 2024 HTML manual was inspected at SHA-256
    `b0dd6d7800c546b2f346d14fc58dab5a8a5d8d37d3010a5271017fc4c6edb1b1`.
