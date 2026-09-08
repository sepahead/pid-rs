# Mean PDF builder controls

This [archive](mean-pdf-builder-controls-v2.tar) supplies the exact accepted v2 harness, inert tool and required fixtures for the mean exposition's PDF builder. It contains 16 source files and a new source manifest. The [distribution inventory](DISTRIBUTION.json) records every file's bytes, mode and digest. Fixture Markdown stays inside the archive: its relative links are preserved test inputs, not additional publication navigation.

The controls execute the whole builder with inert substitutes for Pandoc, LuaLaTeX and the log checker. They cover exact/check/output dispatch, the cross-toolchain refusal, profile and input rejection, Markdown/TeX correspondence, tool selection, actual nonzero exits and stderr, an intended producer timeout, repeated-output mismatch, source/tool drift and output collisions. Each outer invocation runs 56 cases in each of the builder's normal and optimized modes. Neither inert output bytes nor a matched control establishes a real PDF production, theorem, estimator guarantee or hosted result.

The [original acceptance receipt](ACCEPTANCE.original.json) records 224 matched cases and 532 inert tool starts across normal and optimized outer invocations on 8 September 2026. The source manifest in that receipt bound the original 21-file packet. This smaller distribution has a new manifest and passed its [actual relocated normal/optimized suites](../../../evidence/prefix-mgw-mean-formal-verification-2026-09-08/publication-current/portable-builder-controls/ACCEPTANCE.json): 224 cases and 532 inert tool starts. Root verified every new source copy, stream hash and causal role/timeout path. This later result does not alter the original receipt. The distribution records both original result digests and their completion times. Its copied publication profile retains the earlier historical status prose verbatim; the acceptance receipt records the subsequent original control result.

Preserved failures matter. The first source packet sealed at 09:22:11.314854 UTC, after its 09:21:59.311250 deadline; later work does not make that closure timely. Its first normal control invocation failed after 41 matched rows because a global 0.2-second timeout interrupted the Pandoc version probe before the intended producer. The causal trace check rejected that route, and the optimized invocation was not run. The separately registered v2 revision leaves version probes at 300 seconds, changes only the private Pandoc producer timeout to two seconds and makes that inert producer sleep four seconds. It requires three starts, two completions and the builder's actual timeout receipt. The production builder, publication profile and PDF are unchanged. Original failure-result SHA-256: `439232bc9c40a2bf24174f65d94922c9a2bf4ab56b9499708dfefa3644e82588`; late-source seal SHA-256: `d5213d95abdacaa89c6df31aae43f348159d9f7004118fea3c105e6d78bc9bfd`. Full historical process records remain separately retained; those digests alone do not reproduce them.

For a new run, register a fixed stage of at most 35 minutes before work and retain both outer invocations, failures and streams. Use a canonical POSIX directory under the checkout's ignored `.local`, Python 3.11 or newer, and a direct single-link Python executable and `/bin/sh` target. These are the only execution tools; no real Pandoc, TeX installation or Lean is needed. The Python selected for registration must also run the harness. Before extraction, verify the archive SHA-256 `c989642bb7ef421cc995f2feb7b6a69f91010ff10210d555bc393fca294eb31b` and compare the complete tar inventory with the distribution: exactly 17 regular files and 12 directories, no links, duplicate paths, absolute paths or traversal components. Extract the verified archive with ordinary `tar` into an exclusively created canonical directory. Do not execute or overwrite the public fixture source in place.

```text
tar -tvf audit/formal/lean-prefix-mgw-mean/pdf-controls/mean-pdf-builder-controls-v2.tar
umask 022
mkdir <fresh-canonical-ignored-stage>/source
tar -xf audit/formal/lean-prefix-mgw-mean/pdf-controls/mean-pdf-builder-controls-v2.tar \
  -C <fresh-canonical-ignored-stage>/source
```

Create two new registrations from the [template](REGISTRATION.template.json). Replace the unresolved status with `reviewed_source_ready_for_inert_controls` only after source review. Set actual aware UTC bounds within the registered stage, integer `harness_optimization` to 0 or 1, and the actual SHA-256 values of the resolved Python executable and `/bin/sh`. Keep the fixed builder and new source-manifest pins. Hash each completed registration before invoking the harness; paths passed to `--registration` must be canonical absolute paths.

```text
python3 -I -S -B <materialized-source>/proposal/mean-pdf-builder-controls.py \
  --registration <new-absolute-normal-registration.json> \
  --registration-sha256 <actual-normal-registration-sha256> \
  --output <fresh-canonical-ignored-stage>/normal
python3 -O -I -S -B <materialized-source>/proposal/mean-pdf-builder-controls.py \
  --registration <new-absolute-optimized-registration.json> \
  --registration-sha256 <actual-optimized-registration-sha256> \
  --output <fresh-canonical-ignored-stage>/optimized
```

Keep both result directories intact. An owner must review actual return codes, complete case inventories, causal receipts, streams and source identity before recording relocation acceptance. A timeout, incomplete matrix or failed setup is a failure, not a replacement for an expected rejection. The per-case process-group cleanup is bounded cooperative control, not a sandbox, atomic process census, hard real-time guarantee or guarantee about escaped descendants. Real publication builds, mathematical replay and hosted integration have separate evidence requirements.
