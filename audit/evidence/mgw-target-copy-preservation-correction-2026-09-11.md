# Finite target-copy archive preservation correction

The correction restores exact negative evidence and rejects three classes of false acceptance
in the public archive checker. It changes no MGW equation, Lean proposition, accepted proof,
estimator, or runtime API. The scientific object remains finite categorical shared exclusions
from Makkeh, Gutknecht, and Wibral, as specified in the
[theorem note](finite-target-copy-mgw-synergy.md).

## Changed bytes after validation

In commit [`7a25144fef070910547443dd4d03192d99eb1be3`](https://github.com/sepahead/pid-rs/commit/7a25144fef070910547443dd4d03192d99eb1be3),
a whitespace cleanup shortened the inert archive's `Interface.lean.txt` from 8,939 to 8,938
bytes. That edit occurred after validation. The pushed tree therefore failed both the payload
digest check and the self-excluding source-state check, despite a clean Git working tree.

| Object | Bytes | SHA-256 |
|---|---:|---|
| Original and restored Interface payload | 8,939 | `88030fced19ec58e99d92918a7a6830a53415febb0e46373937a812650e3203d` |
| Shortened payload in the cited commit | 8,938 | `7341fe25f9fb740ae709813bac168426f0c85a413acfc16b7779dfd835e4c2a1` |
| Unchanged archive manifest v2 | 118,510 | `0972b3cf26a9aecbf48fb0a706a88675d88db0aa9925929e70f9dc3d83b1004c` |

The restored file equals the retained export byte for byte. Adding precisely one final newline
to the shortened file reproduces that export and the existing manifest hash. Replacing the
manifest's expected hash would have accepted changed evidence instead of restoring it.
The original terminal blank line is an explicit exception to source-code whitespace cleanup.
All checks must run after the last byte edit, including formatting.

## Former checker failures

The former checker is retained at the cited commit. The following observations use isolated
copies with the original Interface payload restored so the unrelated byte defect cannot hide
the acceptance defect. No historical Lean source or driver payload was executed.

| Mutation | Normal Python | Optimized Python | Cause |
|---|---|---|---|
| Replace the manifest schema with an incorrect string | Rejected | Accepted | `assert` was the only schema check and disappears with `-O` |
| Change a failed route's accepted-target count from zero to one | Accepted | Accepted | The checker did not bind the complete manifest or inspect route credit |
| Replace the second artifact entry with a complete copy of the first | Accepted | Accepted | Dictionary construction collapsed the duplicate while a count-only check left one file unbound |

Changing only a path, while retaining the second entry's different digest, was rejected in
both modes. That negative control distinguishes a duplicate-entry omission from an ordinary
payload-hash failure. A passing payload count does not prove a one-to-one inventory.

## Repair and evidence boundary

The [current checker](../../scripts/check-mgw-target-copy-negative-archive-v2.py) uses explicit
conditional rejection, duplicate-key rejection, exact integer checks, unique identifiers and
paths, safe relative inert paths, and a whole-manifest digest. It checks source and diagnostic
associations against raw hash commitments, requires zero theorem credit for every failed route,
rejects symbolic, hardlinked, executable, and special files, and compares the exact set of
payload files with the manifest. Bounded double reads detect file changes during each read;
stable parent directories and a nonconcurrent archive remain assumptions.

The [causal self-test](../../scripts/check-mgw-target-copy-negative-archive-v2-self-test.py)
executes two successful baselines and 34 distinct rejected mutations in both Python modes
(68 rejections). These include the observed missing byte, duplicate inventory entry, optimized
schema bypass, and false theorem-credit cases. Each rejected subprocess must report the
expected reason. The workflow runs both tools in normal and optimized Python.

```text
python3 -I -S -B scripts/check-mgw-target-copy-negative-archive-v2.py
python3 -O -I -S -B scripts/check-mgw-target-copy-negative-archive-v2.py
python3 -I -S -B scripts/check-mgw-target-copy-negative-archive-v2-self-test.py
python3 -O -I -S -B scripts/check-mgw-target-copy-negative-archive-v2-self-test.py
```

These are bounded preservation checks under the stated local filesystem assumptions. The
manifest's raw hashes do not let a public checker reconstruct private path substitutions,
authenticate historical processes, prove what they loaded, or establish mathematical truth.
An owner can coherently change the checker and all commitments; no independent custody follows.
The record does not close the separate publication-builder, replay-review, hosted-mainline,
or SxPID3 program obligations.
