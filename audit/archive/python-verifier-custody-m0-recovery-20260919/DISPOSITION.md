# Python custody M0 exact-history recovery

This inert recovery packet preserves the exact historical branch tip
`e16a6915262e8bf2fac1752ff959d9d3733c7a7d`, including its generated registry and
all nineteen modified integration files. The existing [five-payload archive](../python-verifier-custody-m0-20260830/DISPOSITION.md)
retains the design record, documentation, schema, checker and self-test as readable
inert copies. Keep that original archive and its dated omitted-registry statement
unchanged; this separate packet supplies the missing exact-history successor.

The bundle requires commit `eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9` and its
reachable object closure. That prerequisite is an ancestor of retained main commit
`959d91e38e5007d9c0f5d0f775ef2cce913680a0`. The bundle is deliberately incremental;
it cannot restore into an empty repository without the prerequisite history.
INDEX.json binds its byte count, SHA-256, exact commit/tree, every changed blob and
the five readable successors.

Fresh private recovery from accepted-main-only history passed native Git bundle
verification, fetch, exact commit/tree and all 1,046 leaf-entry checks, comparison
of all 25 changed blobs, and full strict fsck. Before recovery the branch commit
and registry object were absent. An empty-repository negative control rejected
verification and unbundle for the missing prerequisite and retained no branch ref
or tip commit. The recovered 5,473,991-byte registry has SHA-256
`ce11224f6fb95246a43dd36c24da57501f3854bf2f667c483f99125d751f016a`.

The bundle preserves the prototype's useful static custody design, rejected
status and negative evidence. Its old catalog entry, launch guidance, generated
source projections and dependency pins remain historical. This packet does not
activate the inventory, establish execution custody, or claim a new scientific
result. No historical checker, self-test or registry generator was executed.

To recover for inspection, use an isolated repository with the prerequisite
history, verify the bundle's INDEX.json byte binding, run `git bundle verify`,
and fetch the bundle's `refs/heads/sepahead/python-custody-m0-v1` into a private
recovery ref. Read recovered files using `git show` or `git cat-file`; recovery
does not require executing their contents.

Branch retirement remains conditional on accepted publication, an independently
retrieved committed copy of this packet, retained prerequisite reachability,
the applicable hosted checks, process ownership and preservation checks, and an
exact expected-old remote-ref lease. This packet alone records no branch deletion.
