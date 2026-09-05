# Historical workflow branch disposition

At 07:43:54 UTC on 5 September 2026, the coordinating owner removed exactly the two local workflow refs below in one transaction. The transaction checked both expected old object IDs. No worktree or remote ref was removed.

| Local ref | Exact tip | Accepted successor |
|---|---|---|
| `refs/heads/codex/integration-20260804` | `bd5ea639e303e2f9d57d13b502dd68d3da6ada73` | `9031230d0ab6e0878fe8b9ba38578a80c9439776` |
| `refs/heads/codex/workflow-publication-20260804` | `1bec7a4fdcf80b4b0b7d5f03d4491bb5f8319709` | `9031230d0ab6e0878fe8b9ba38578a80c9439776` |

The successor is an ancestor of observed remote main `e1a6648ccace699e41b4ffa48c6acd79209a7418`. Each branch has exactly one commit outside that main history. All 28 non-changelog paths in each tip match the successor's bytes and Git modes. Each changelog delta adds the same 13 lines and deletes zero. The added bytes have SHA-256 `d01b5454c28ad4394ecc362b9498d835e1c96a0986acfe0a8779dcf7386713ec`.

The [published preservation account](worktree-and-branch-preservation-2026-08-27.md) already records this succession. The [September-1 ledger](worktree-and-branch-retirement-ledger-2026-09-01.json) and [September-2 custody observation](post-publication-custody-2026-09-02.json) retain their original dated scope. This observation does not rewrite them.

Original histories remain in the complete primary custody bundle: 36,426,597 bytes, SHA-256 `07562762e2a68cffd41f3a44ae76f18fba118802927217f91cf47da5f94259ed`. A fresh read matched these bytes and both advertised tips. The earlier isolated restoration and full fsck passed without alternates. The restored tips and selected reflog objects remain readable. Exact reflog preimages are retained privately. The original differing commits are historical workflow alternatives; their archival disposition grants no new scientific, formal, statistical, implementation, or application credit.

Neither selected branch was checked out. The coordinating owner recorded the selected-ref writer disposition before the transaction. No selected ref lock or open-file owner was observed. Other processes had the repository as their working directory; that observation was retained and was not presented as exclusive operating-system ownership. The expected-old transaction and repeated postchecks bound the selected action. They do not establish the absence of every possible concurrent or future writer.

Both refs were absent after the transaction. The other 61 refs were unchanged. The primary HEAD remained `9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56` on `refs/heads/review/sx-count-event-bridge-r2`. The index, NUL-separated status, and 599 tracked or nonignored paths were unchanged. Those paths contained 28,233,005 bytes.

The custody bundle again matched its recorded hash. Remote main remained `e1a6648ccace699e41b4ffa48c6acd79209a7418`, and the accepted successor remained its ancestor. The transaction output, before and after observations, exact private reflogs, and coordinating disposition remain in local custody. These records omit unlisted ignored content and do not claim a global private-data backup, atomic filesystem snapshot, or independent institutional review.

This action closes two local ref obligations. It does not retire the dirty primary, another worktree, a remote archive, or the remaining scientific work. The pre-action projection and the dated historical ledgers are preserved.
