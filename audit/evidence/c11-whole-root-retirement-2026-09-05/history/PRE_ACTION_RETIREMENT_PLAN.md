# Whole C11 retirement candidate

The complete source, recovery endpoint, and fetch-equivalence checks are complete. Root can now assess one whole obsolete clone. No original root, original ref, or C12 configuration was changed by this recovery preparation.

## Verified recovery

The source is clean at `91d954160a7e717ae46b6088175ae52e92570127`, an ancestor of observed remote main `e1a6648ccace699e41b4ffa48c6acd79209a7418`. Its 13 refs, including the tag object and retained archive refs, are preserved exactly. The distinct archived objects are not promoted to accepted science by this action.

The complete private archive contains 1,551 regular files and 260 directories below the source root, totalling 225,191,186 file bytes. It includes Git metadata, target outputs and the Ruff cache. The archive is 101,491,167 bytes with SHA-256 `c90f40228ccbb36123d1a048504faf45c250382339832c31351aacc875048ef7`. Independent extraction matched every selected byte, size, and mode. Both complete manifests have SHA-256 `28308eeab597470e2150f49550ffac8347ccf7f7bcf5688c88c499df2429b7ea`.

The restored repository has the same HEAD, symbolic branch, 13 refs, and clean NUL status. Full native Git fsck passed with no alternates. A separate bare mirror, made without local hardlinks, has the same 13 refs and advertised branch heads. It has no configured origin or dependency on the restored worktree. Its full fsck also passed. The original complete source manifest was equal before and after recovery and again after the fetch probes.

The restored private root itself is mode 0700. The original root's mode 0755 is recorded separately for reconstruction. Exact equality covers the 260 directories below it and all 1,551 regular files. ACLs, owners, extended attributes, and timestamps are not restored or claimed. This is not an atomic filesystem snapshot or off-host durability proof.

## Exact remaining dependency

C12's common Git directory currently configures `c11-source` to the old C11 clone. `FETCH_EQUIVALENCE.json` records the exact current URL, configuration digest, and fetch spec. Two new bare consumers fetched from the original and replacement endpoints with that same `+refs/heads/*:refs/remotes/c11-source/*` mapping. Their four resulting ref identities, including the automatic remote HEAD and tag, match exactly. Both probe object stores passed fsck. C12's original configuration stayed byte-identical.

The persistent replacement endpoint and archive locators are in `LOCATORS.json`. Root must preserve that endpoint while C12 depends on it. The complete original archive and existing verified numerical-r2 bundle remain separate recovery objects.

## Guarded coordinator sequence

1. Read the task, executable custody check, result, final source check, fetch-equivalence result, and logs. Record the selected C11 owner disposition. The latest cwd census found no owner under the original C11 root. Repeat that observation immediately before action. Do not wait for former-agent consent; do retain the C12 and active VM owners.
2. Re-read exact remote main and prove the C11 HEAD remains its ancestor. Recheck the original's complete manifest, HEAD, symbolic branch, 13-ref roster, and clean status. Match the archive and source-manifest hashes. Confirm the restored and bare endpoints remain readable and use no alternates.
3. Capture C12's complete configuration preimage and its current refs/HEAD/status. Verify the current c11-source URL and fetch mapping exactly equal `FETCH_EQUIVALENCE.json`. Change only that local URL to the verified bare replacement endpoint. Keep the fetch mapping unchanged. Use a guarded single-field configuration update under the selected writer disposition. Compare the complete resulting configuration against the one expected URL replacement; stop if any unrelated change appears. Do not fetch into or change C12's load-bearing refs as part of this configuration action.
4. Verify the rebound URL by reading its advertised heads and through a new owned consumer if needed. The original C12 ref roster, HEAD, working bytes and index must remain unchanged. Record the before and after configuration hashes and the exact endpoint identity privately.
5. Retire only the exact original C11 root after those checks pass. A same-filesystem rename into the owned custody area can provide a final reversible boundary before removing the retired original copy. Recheck the manifest after any rename and retain the archive, bare endpoint and receipts. Do not remove C12, its linked worktree, the existing custody stores, or the live VM cwd.
6. Verify the original location is absent, the C12 recovery URL works, and all retained recovery objects are readable. Record the actual action and scoped postchecks. The independent restored worktree and fetch probes are temporary verification subjects, not new active research lanes. Retire them only after their verified outputs and this receipt are retained; keep the archive and the bare endpoint.

All original removal and C12 configuration actions remain root-owned. This packet does not claim they occurred. A public action receipt must use the actual post-action result and omit private locators. No mathematical, KSG, C12 qualification, estimator, or release claim is reopened.
