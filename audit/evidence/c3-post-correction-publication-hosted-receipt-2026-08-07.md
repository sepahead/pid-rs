# C3 publication-commit hosted receipt

- **Exact subject:** `89055322401fc531aaa3ac7fbfb27304c1ef2634`
- **Subject tree:** `7f1f0b09055dd9eabd33a43cc0ba782a4558c0c0`
- **Direct parent:** `e72c33684331a79a8cfe220fd32cde8d81920f10`
- **CI:** run `31155454637` attempt `1`, `completed` / `success`, 45 jobs
- **Dynamic CodeQL:** run `31155454365` attempt `1`, `completed` / `success`, 4 jobs
- **Disposition:** **bounded exact-subject hosted closure**
- **Machine companion:** `c3-post-correction-publication-hosted-receipt-2026-08-07.json`, 35,193 bytes, SHA-256 `a7eeb570f2d6173a8a32eb91ab6604d352dc92226d963f349771b5e23b7bd055`

The machine companion is the typed authority. This Markdown binds the already frozen JSON in one
direction. The JSON does not hash itself or this Markdown.

## Exact boundary

The receipt describes the pre-existing commit `89055322401fc531aaa3ac7fbfb27304c1ef2634` and the two attempt-specific hosted
runs named above. It also resolves the earlier publication-custody receipt's outer boundary by
binding that commit, its tree and parent, and the two publication-custody blobs already present in
the subject tree. The subject cannot authenticate later receipt bytes. Membership or nonmembership
of the future receipt paths in the subject tree is not adjudicated here. The future receipt-bearing
commit, tree, JSON blob, and Markdown blob therefore remain null in the machine record. A later
external observation may bind them; this receipt makes no claim about that future commit's own CI
or CodeQL and does not require another recursive receipt.

Expected rosters are the pinned 45-name CI set and four-name CodeQL set recorded in the machine
companion. Their counts and names are predicates, not assumed outcomes. The disposition above is
derived from the captured terminal run conclusions, complete reported job pages, actual conclusion
partitions, the receipt's sorted observed-job projections, exact name-set equality, unique job
identities and names, and exact run, attempt, and head equality. A failure, cancellation, skip,
missing job, duplicate, or roster mismatch receives
no all-green transfer. The earlier nongreen CodeQL result on parent
`e72c33684331a79a8cfe220fd32cde8d81920f10` remains a distinct retained negative and is not rewritten by either run here.

## Capture and non-implications

For each commit, run, and job-page endpoint, the supplied `gh` was invoked twice with argv requesting
HTTP GET. Its actual network behavior and remote effects are not established. Matching bytes are
correlated observations, not independent replications, authentication, trusted time, or a
transparency log. API timestamp values are opaque unauthenticated text with no format or chronology
validation. Pagination completeness is only relative to each response's reported
`total_count`. The source, interpreter, `gh` executable, dependencies, credentials, GitHub,
runners, actions, toolchains, operating systems, hardware, and network services are unauthenticated.
The supplied `gh` received `GH_TOKEN`. Exact token bytes were required to be absent from every
captured stdout and stderr before parsing or writing, but that scan cannot exclude partial,
encoded, hashed, encrypted, or otherwise transformed leakage by a malicious or replaced `gh`.
No token-or-derived-value nonretention claim is made.
Bytes returned in stdout and stderr may include descendant writes to inherited streams, but they do
not identify producers or establish complete process-tree observation or containment. Those streams
were fully buffered before the post-return response-byte check, with no streaming byte cap or RSS
hard limit. Other file descriptors, files, IPC, and side effects were not observed. Filesystem
checks do not bind concurrent parent-path
rename or symlink replacement, uid, gid, ACLs, extended attributes, file flags, mount semantics,
remote durability, or crash durability.

No logs, artifacts, SARIF, step counts, test counts, coverage content, SBOM content, alert
inventory, extractor completeness, zero-vulnerability result, security cleanliness, scientific
result, estimator validity, theorem meaning, release readiness, or downstream authorization is
claimed. Nothing transfers among KSG, Ehrlich continuous shared-exclusions PID, categorical
Makkeh--Gutknecht--Wibral SxPID, Williams--Beer `I_min`, fitted quantized PID, project heuristics,
or wrappers.
