# Galadriel recovery contract

Verify the bundle size, SHA-256 and Git blob identity against `manifest.json`. It advertises only
`refs/heads/sepahead/galadriel-placement-guide-v1` at
`75a7acaa3f9432dc323be7e49f5eee1f9af781fd` and requires the complete reachable history of
`718447aa2acc6600a3bdce1d81cda0dba4f4ab3b`. Later main objects are not an extra prerequisite.

Use an explicitly owned, freshly empty bare repository, disable hooks and ambient Git routing,
and use no alternates/shared writable objects. Obtain accepted main history from its verified
remote. These commands describe the native operations; paths are placeholders:

```text
git init --bare recovery.git
git --git-dir=recovery.git fetch --no-tags https://github.com/sepahead/pid-rs.git refs/heads/main:refs/heads/main
git --git-dir=recovery.git merge-base --is-ancestor 718447aa2acc6600a3bdce1d81cda0dba4f4ab3b refs/heads/main
git --git-dir=recovery.git bundle verify galadriel-history-from-718447aa.bundle
git --git-dir=recovery.git fetch --no-tags galadriel-history-from-718447aa.bundle refs/heads/sepahead/galadriel-placement-guide-v1:refs/heads/recovered/galadriel-placement-guide-v1
git --git-dir=recovery.git fsck --full --strict --no-reflogs
```

Record refs and all available objects before import. Test the two branch commits and all 14 objects
absent from the original `959d91e` main baseline; if a later main already supplies one, record that
successor instead of claiming it missing. Inspect the actual bundle prerequisite and its 39 original
pack objects. Native `index-pack --stdin --fix-thin --strict` and `verify-pack -v` can verify the
pack in an isolated database; every appended thin-delta base must be reachable from the prerequisite.

After import compare the two raw commits, tree IDs, complete path/mode/blob rosters and all 23
changed versions against the manifest. Verify the five historical preimages explicitly, including
source-state blob `fbab0fbd5d7b0801e343ae41fb175990b9d799e8`, SHA-256
`4339e31aeb3dc64f5c149cbb989df2bd024b76d0fccd942fbe9e094c44cc4963`.
Run strict integrity checking and preserve exact commands, raw streams, tool/version, timestamps,
exit codes and failures. Never execute a historical script or build to establish custody.

For a publication drill retrieve the bundle directly by its exact Git blob from the containing
remote-main commit. Verify its raw bytes before recovery; reusing the original scratch copy does
not test published recovery. The current immutable receipt covers only the earlier same-host
native drill. A later separate publication/retirement receipt names the actual containing commit,
retrieved blob and results. Main-reachable repository storage is an authorized public recovery
route for this already-public history, without an additional external store approval; its retention
assumptions still do not amount to permanent scholarly preservation or scientific validation.
