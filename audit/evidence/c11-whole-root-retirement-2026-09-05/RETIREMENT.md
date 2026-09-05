# C11 clone retirement and local recovery

The guarded C11 retirement completed at 08:41:35 UTC on 5 September 2026. The
[actual result](ACTUAL_RESULT.json) records the recovery-URL change, the final rename and
removal of the original clone, and removal of three temporary verification copies. The
complete compressed source archive and the independent bare recovery endpoint remain retained.
This is an operational repository action. It changes no scientific, formal, release or exact-C12
lifecycle status.

The [earlier recovery result](history/PRE_ACTION_RECOVERY_RESULT.json) and
[pre-action plan](history/PRE_ACTION_RETIREMENT_PLAN.md) remain exact historical bytes. At that
stage, the original clone had not been removed and the dependent configuration had not changed.
Those old fields describe the earlier stage; they are not the final action result.

## Retained scope

| Item | Recorded result |
|---|---|
| Original C11 HEAD | `91d954160a7e717ae46b6088175ae52e92570127` |
| Observed remote main during the action | `e1a6648ccace699e41b4ffa48c6acd79209a7418` |
| Ancestry check | Original HEAD was an ancestor of that observed main |
| Complete source inventory | 1,551 regular files and 260 directories below the original root |
| Regular file bytes | 225,191,186 |
| Retained compressed archive | 101,491,167 bytes |
| Archive SHA-256 | `c90f40228ccbb36123d1a048504faf45c250382339832c31351aacc875048ef7` |
| Original and restored manifest SHA-256 | `28308eeab597470e2150f49550ffac8347ccf7f7bcf5688c88c499df2429b7ea` |
| Retained bare ref roster | Thirteen refs, including archived objects and the tag object |
| Temporary verification copies removed | One independently restored checkout and two bare fetch probes |

The original inventory included Git metadata, ignored build outputs and the Ruff cache. The
independent restore matched the inventoried file bytes, sizes and modes, and all directory modes
below the root. The restored private root itself used mode 0700; the original root mode 0755
was recorded separately. ACLs, ownership, extended attributes and timestamps were outside the
recovery contract. The archive is local recovery; it is not an off-host durability result.

The [retained ref roster](recovery-refs.tsv) and
[advertised branch heads](recovery-advertised-heads.tsv) preserve the exact observed objects.
Retention of rejected or superseded refs does not promote their contents to accepted results.

## Dependent checkout preservation

C12 used the original C11 clone as its `c11-source` endpoint. The action changed only that
local remote URL to the verified bare replacement. Its fetch mapping remained
`+refs/heads/*:refs/remotes/c11-source/*`. Before the action, two new owned bare consumers fetched
from the old and replacement endpoints and obtained the same four resulting ref identities;
the [fetch-equivalence projection](history/FETCH_EQUIVALENCE.json) records that bounded test.

The [configuration comparison](DEPENDENCY_CHANGE.json) verifies the one-line replacement
against the complete retained preimage and postimage. The action also compared C12 and its
linked checkout before rebinding, after rebinding and after retirement. All three captured
states match: HEAD, branch, refs, status, worktree listing, index digest, and the nonignored file
bytes and modes. The comparison covered 866 paths in C12 and 968 in the linked checkout.
Their ignored caches were outside this configuration-only preservation check.

The action repeated owner, open-file, complete-source, recovery and configuration checks before
the last reversible rename. It then verified the renamed source against the complete inventory
before removal. The retained archive and bare endpoint were checked again after removal. The
[selected command records](SELECTED_COMMANDS.json) retain the ancestry, native Git integrity,
URL update and final recovery observations as portable projections. These observations are
not an atomic snapshot or protection against an unobservable later writer.

## Public projection and actual custody

[MANIFEST.json](MANIFEST.json) binds this public packet except itself. The exact
[actual result](ACTUAL_RESULT.json) has SHA-256
`6e89538426d7eb8ac5d92789ed2dc345159338c24d3a1ecc1c85ef6e8a63bcc2`.
The [retained action inventory](RETAINED_ACTION_INVENTORY.json) is also exact. It identifies
259 files and 2,243,944 bytes in the local action archive; those entries were all independently
read and hash-compared after the action. The
[later read-only observation](POST_ACTION_OBSERVATION.json) also records that the original
location was absent, the bare endpoint was present, and the complete archive digest still matched.

The 259-file inventory is an inventory of retained local evidence. It does not mean that all
259 payloads or the complete source archive are published in this packet. Full configuration
files, machine path lists, tool-environment observations, raw path-bearing snapshots and the
large source archive remain local. Portable projections replace directory prefixes with role
tokens and keep separate original/public hashes. The omitted prefixes cannot be reconstructed
from this packet. A local original hash does not supply complete public custody of omitted bytes.

No action in this record fetched into C12's load-bearing refs, removed C12 or its linked checkout,
changed the completed C12 qualification result, or established a new theorem, estimator,
calibration, deployment, authenticity or external-attestation result.
