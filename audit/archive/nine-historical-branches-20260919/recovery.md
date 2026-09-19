# Recovering the historical branches

The native recovery completed on 19 September 2026 at 19:14:44 UTC; its recorded readback accepted same-host recovery only. The 519,628-byte bundle has SHA-256 `2af43d756dbc5fc1eab97eae57892b47f9af04939b9f601149251be48322e549` and Git blob identity `7df1a590068cb4d986c2fc75031666e45ad483da`. The manifest binds the dated receipt identities, raw object hashes, complete tree-roster hashes, and counts. Its immutable status is `historical_archive_with_local_recovery_evidence`; a later receipt must independently bind publication and retrieval from remote main.

The record covers 142 commands and 284 streams, all 355 retained raw source objects, all 17 unique commit trees, recovery of every one of the 224 missing objects from a P1-only repository, strict fsck, and an empty-repository negative control naming all seven prerequisites. The actual original pack contains 246 objects and uses 101 thin bases reachable from declared prerequisites. Those are observations of this bundle, not a universal transport-size contract.

The baseline is P1 `17bec81e88eda6b7113ed6c47eb0b08830b584b6`. Full positive object closure of the nine tips, minus complete P1 object closure, contains 224 objects. Their history contains 17 non-main commits. The retained source comparison roster has 355 objects, including 131 already reachable from P1. **This is not a required bundle pack or combined traversal count.** The seven prerequisite commits are:

- `172e09f287ae97f55c4cc6933c82fef76265321f`
- `23b69abafb4bfdaab4b2321eb6cee7be7e1cd32e`
- `7c80d48db415279fc4d744eadb1515797606912b`
- `9c97c4eaa28f0dcc74144fd982f6606046b62a92`
- `be862b155d710573ec95356fc1cbe9a96a2b83b9`
- `cb351ad25803be35edd776245a37e24c69a03f3f`
- `da253576a5f76e99633fff4de5cf1118f967b90d`

Use fresh private bare repositories with an empty Git template and a reviewed isolated Git environment. Disallow shallow history, alternates, replacement refs, grafts, unreviewed configuration includes, hooks affecting upload-pack, and partial/promisor object sources. Do not check out or execute archived files.

1. Obtain the exact bundle bytes and verify their manifest SHA-256 and Git blob identity. For a future remote retrieval drill, retrieve the bundle by its exact containing main commit and path into a separate owned location. A same-host copy proves only local recovery.
2. Seed a fresh bare recovery repository with only complete P1 history. Confirm its sole ref is P1 main and its full object inventory is the recorded 8,811 objects. Check all 224 expected absent OIDs individually: every one must be missing before import.
3. Run `git bundle list-heads` and `git --git-dir=<recovery.git> bundle verify <bundle>`. Require precisely the nine manifest refs/tips and the seven prerequisite IDs above. In a separate empty bare repository, verification must fail and identify the missing prerequisites; it must not add objects.
4. Import only the nine explicit `ref:ref` pairs from the manifest with `git --git-dir=<recovery.git> fetch --no-tags --no-recurse-submodules --no-write-fetch-head <bundle> <exact-refspecs>`. Do not fetch from the historical refs to complete this recovery drill.
5. Require recovered refs to be exactly P1 main plus those nine tips. Require the full inventory to be exactly P1's inventory union the 224 absent objects. Compare all 355 retained raw source objects byte for byte, including canonical Git identities and SHA-256, every full path/mode/blob tree roster for the 17 unique commits, and the complete unique commit set and parents. Run `git fsck --full --strict --no-reflogs` and retain raw output.
6. Inspect the bundle header and original pack separately. Every absent object must occur in the original pack; no original object may lie outside P1 plus the 224. Bind the parsed original-entry count to the actual pack header. Any appended thin-pack bases must be reachable from declared prerequisites. Record actual counts without substituting the source comparison roster's size.

The first native attempt stopped before a bundle was created: its frozen assertion equated a union of separate historical traversals (355) with a combined native traversal (246). Independent set readback found that all 224 absent objects were present and all 109 omitted roster objects were already in P1. This remains a failed attempt with no recovery credit. The corrected protocol distinguishes the preservation set, source comparison superset, combined traversal, and actual pack. It does not infer an undocumented internal pruning mechanism or assume a future pack count.

The corrected execution retained the failed attempt and used a separately reviewed preservation predicate. Successful custody does not accept the archived methods, proofs, drafts, or receipts. See [the dispositions](disposition.md).

Git documents the [object traversal](https://git-scm.com/docs/git-rev-list#_object_traversal) and [bundle prerequisite](https://git-scm.com/docs/git-bundle#_object_prerequisites) contracts. A bundle may include objects already present at its destination. The complete recovery checks above establish this archive’s coverage.
