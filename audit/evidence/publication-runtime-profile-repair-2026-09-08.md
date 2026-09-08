# Publication runtime and profile repair — 8 September 2026

This successor prevents source-adjacent Python cache writes in the workflow PDF checker and
adds a finite Linux profile for the current 24-page mathematical results guide. It changes no
mathematical statement, estimator, publication source, canonical PDF, or scientific threshold.
The [earlier text-profile milestone](workflow-pdf-text-profile-repair-2026-09-08.md) remains a
record of its exact source and failed production check.

## Workflow cache failure and repair

The earlier full Linux workflow check failed at 05:42:44 UTC. Its final inventory found
`scripts/__pycache__` with a directory mode other than `0555`. The declared source contained no
cache. The outer source and executable hashes were unchanged; the failure concerned the
checker's separate inner snapshot.

The synchronizer self-test imports its adjacent Python module. Isolated Python ignores
`PYTHONDONTWRITEBYTECODE`, while execution as root can create a cache below a mode-`0555`
directory. The earlier retained diagnostic contains the resulting normal and optimized cache
files. The repair puts `-B` in all 36 production Python command vectors and both transitive
Python child vectors. It preserves `-O` where required and leaves the complete source inventory
guard unchanged. [`-I` and `-B` have distinct effects](https://docs.python.org/3.12/using/cmdline.html#cmdoption-I).
The flag prevents automatic cache writes; it does not prohibit arbitrary file writes or reading
an existing cache.

The complete revised shell suite passed 428 controls at 06:18:59 UTC, with empty stderr and
unchanged source bytes. Its twelve new controls cover command placement, optimized execution,
transitive child flags, actual adjacent imports, and rejection of writable or undeclared caches.
The earlier 416 controls retain their separate historical result.

Six focused native Linux cases used the unchanged import prefix and snapshot validator:

| Execution | Automatic cache created | Snapshot validator |
|---|---|---|
| Root, isolated, environment variable only | Yes | Expected rejection |
| Root, isolated, explicit `-B`, normal or optimized | No | Passed |
| Unprivileged, isolated, environment variable only | No; permissions prevented the write | Passed |
| Unprivileged, isolated, explicit `-B`, normal or optimized | No | Passed |

All six cases passed their stated expectations. The unprivileged environment-only case still
reported that automatic bytecode writing was enabled. It therefore cannot justify the
environment-only approach. A direct archive copy failed when it recreated read-only directories
before their children. The successor retained the tar bytes and checked 44 regular-file copies
against the native records. Host-copy permissions and native permissions remain distinct.

The complete revised Linux workflow check passed at 07:06:34 UTC with production cleanup
enabled, empty stderr, and unchanged source and executable inventories. It checked the workflow
PDF and all four SVG/PDF pairs, including the 87 declared color/grayscale page comparisons.
The outer archive retained and rechecked 29 regular source files. Temporary production outputs
were removed by the unchanged cleanup procedure; the retained wrapper output records their
checks. An earlier supervisor launch failed to find its registration before starting any
production wrapper. The corrected registration placement did not change the wrapper or its
acceptance rules. That setup failure remains separate.

## Current results-guide profile

Two full builder invocations produced the same 748,561-byte Linux PDF, SHA-256
`d202d8314d1c9adcb7195414f239eb2e99db6c7c693df147e7ac960ffaf90a24`.
They completed at 05:39:08 and 05:40:38 UTC. Two earlier setup attempts ran no builder and remain
failed. The [frozen capture receipt](mathematical-results-guide-pandoc-3.10.2-hosted-raw-profile-v3.json)
records the exact source, producer, local container, and environment limits.

The canonical and Linux PDFs differ in raw metadata and byte length. Both pass the unchanged
current structure checker. Their complete plain text, layout text, font tables, targets and
navigation agree. All 24 corresponding page images are byte-identical at 120 dpi in color and
grayscale. Selected pages also received direct visual inspection. These observations do not
establish a general rendering or accessibility theorem.

The new profile binds that complete Linux fixture. A candidate must be byte-identical or differ
only in the existing strict duplicated final-trailer identifier payloads. Both inputs must still
pass the unchanged current structure contract and produce equal complete reports. No other
metadata, font, content, object, navigation, or structure normalization is admitted. Historical
23-page v2 files and receipts remain unchanged.

The new raw-profile suite passed all 70 cases in both outer Python modes. The mode-wiring suite
passed 80 controls and 61 hostile mutations in each mode. All four invocations completed between
06:13:08 and 06:13:37 UTC, with empty stderr and unchanged inputs. A floating-point fixture-length
literal is rejected by its exact-type control. Historical-v2 checker, fixture, and receipt
substitutions are rejected by the current mode checks.

## Integration status

The complete exact publication suite passed on the Mac at 07:08:30 UTC. Its 1,382-file source
roster stayed unchanged, and the root review rechecked every source and both output streams.
The final report covers every declared formal paper and exact committed-byte relations. This
local result does not substitute for Linux production or hosted execution.

The first current-guide Linux production check failed at 06:36:08 UTC. Its unprivileged builder
self-test copied a mode-`0444` source into a private fixture, then could not truncate that fixture
at its declared mutation step. The corrected environment keeps the native sources owned by root
with modes `0644`/`0755`. The unprivileged builder still cannot write those sources; it can write
its own copies. All 1,381 source byte sequences are unchanged. The complete corrected production
check passed at 07:20:14 UTC with empty stderr. It rebuilt the same current 24-page Linux PDF
and passed the full wrapper, including the unchanged structure checks and both 70-case profile
tests. The source permissions and four producer identities stayed unchanged. Root review checked
all retained streams and 271 files captured by a read-only observer. That observer does not claim
to capture every temporary file. The original failure and native metadata are retained.

The final source projection and post-commit identity are checked separately. Hosted checks and
main integration were pending at this report's freeze. Their outcomes require exact receipts.

The source critiques used ten routes and fifty named review lenses. Reviewers shared the model
family, repository, dependencies and retained artifacts. These reviews are advisory evidence;
they do not establish independent institutional replication. Focused fixture and checker passes
do not prove mathematical correctness, estimator calibration, application value, or hosted
execution. Machine-specific recovery paths remain in ignored local records.
