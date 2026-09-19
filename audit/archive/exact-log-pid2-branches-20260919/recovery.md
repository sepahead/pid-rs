# Recovery contract

The bundle requires the complete reachable history of commit
`855605a2a2098fa82fccb07521bae5cc382fa747`, which was verified reachable from remote main
`959d91e38e5007d9c0f5d0f775ef2cce913680a0`. Later main objects are not an additional
prerequisite. The bundle's SHA-256, Git blob identity and object roster are in `manifest.json`.

Use an explicitly owned, newly empty bare repository. Disable hooks and ambient Git routing;
use no alternates or shared writable objects. Obtain the accepted main history from its verified
remote, then check prerequisite ancestry. Preserve exact commands, tool version, stdout, stderr
and exit codes. The following commands show the required operations; paths are placeholders:

```text
git init --bare recovery.git
git --git-dir=recovery.git fetch --no-tags https://github.com/sepahead/pid-rs.git refs/heads/main:refs/heads/main
git --git-dir=recovery.git merge-base --is-ancestor 855605a2a2098fa82fccb07521bae5cc382fa747 refs/heads/main
git --git-dir=recovery.git bundle verify exact-log-pid2-history-from-855605a.bundle
git --git-dir=recovery.git fetch --no-tags exact-log-pid2-history-from-855605a.bundle refs/heads/sepahead/exact-log-hostile-v1:refs/heads/recovered/exact-log-hostile-v1 refs/heads/sepahead/pid2-rev4-assurance-v1:refs/heads/recovered/pid2-rev4-assurance-v1
git --git-dir=recovery.git fsck --full --strict --no-reflogs
```

Before import, record main refs and complete available-object inventory, and test whether the
three unique commit objects and each of the 75 objects absent from the original main959 baseline
are missing. If a newer main already supplies an object, record its exact main-history successor;
do not manufacture a missing-object result. Verify the bundle's two advertised tip IDs, its one
prerequisite and exactly 97 original packed objects. Native `index-pack --stdin --fix-thin --strict`
and `verify-pack -v` can inspect the pack in an isolated database; the 47 appended delta bases in
the recorded drill all belonged to prerequisite855 history.

After import compare the raw three commits, their tree IDs, path/mode/blob rosters and every one
of the 59 changed file versions against the manifest. Check exact negative receipts and all
three source-state preimages explicitly. Preserve failure statuses and accepted scope probes;
never execute an archived checker or build to establish custody. Record the new object set and
native strict integrity result. Hash equality is an exact-byte check, not authenticity or
scientific validation.

For the separate publication drill, first retrieve the bundle directly by its exact Git blob
from the containing remote-main commit and verify raw size/SHA-256. Reusing the original scratch
file does not test the published recovery route. The current record proves only the prior
same-host native drill. The repository's immutable containing-commit path supplies an authorized
public durable locator after adoption; no additional external store is required for this
already-public history. Remote-main retention is still an operational assumption, not permanent
scholarly preservation.
