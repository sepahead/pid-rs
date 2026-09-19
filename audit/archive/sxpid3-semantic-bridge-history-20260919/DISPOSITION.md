# Semantic-bridge original history: local recovery recorded 19 September 2026

This immutable archive records a completed local Git recovery. The bundle preserves the five original commits ending at 3960e01dadef70e0dbe6d22aa217b480ab2b1ad0. Its tip tree, 27a89518f34aba3f3005e9e1287189e8e34aa013, exactly matches the tree of accepted-main ancestor ab0c6970050e1b87216fbd0846911143a92c3904. The [manifest](manifest.json) supplies every canonical commit, root-tree and historical blob identity.

The bundle is 409,720 bytes: SHA-256 656d41a059a3b021383b9b94ba9c83d090f56f128666b455e9bd20afa3b6e3f0; canonical Git blob 9a96f89584c5ab9ef92ab74967d03f66bbd8a0d8. It advertises only refs/custody/semantic and declares prerequisite e1a6648ccace699e41b4ffa48c6acd79209a7418. The tested recovery route seeds complete P1 first; an e1a-only minimal-prerequisite recovery was not tested.

## Source dispositions against literal P1

All 31 historical paths and 33 distinct after-blob variants were compared against P1, exactly 17bec81e88eda6b7113ed6c47eb0b08830b584b6. The full map, per-path P1 blob/SHA-256 and every variant are embedded in manifest.json under disposition_comparison. Thirty-one variants are P1-history-reachable; six match its tip exactly. These are dated P1 witnesses, not claims of equality with a later main or integration checkout. The manifest identifies six paths observed with later integration bytes; their old authority roots are not restoration candidates.

The two other variants are superseded workflows. One temporarily puts Program A semantic checks inside the keyed-scalar job. The [keyed workflow](../../../.github/workflows/sxpid3-bounded-keyed-scalar-audit-expressions.yml) and [separate semantic workflow](../../../.github/workflows/sxpid3-program-a-semantic-bridge-v4.yml) retain the useful routes. The second invokes the [catalog checker](../../../scripts/check-method-catalog.py) under isolated Python despite its sibling-module import route; the final invocation corrects that incompatibility. Preserve these drafts as history rather than restoring them.

The [governing source correspondence](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/source-correspondence-v4.md), [decision](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v3.md), [evidence index](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md) and [active semantic checker](../../../scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py) carry stronger typed-equality controls and retained [failure evidence](../../../claims/SX-CERTIFIED-AVERAGED-PID3-001/failures/python-status-type-coercion.md). Historical recovery supplies no reason to restore the weaker checker, earlier publication safeguards or stale catalog pins. Current governing links are navigation; they do not redefine the immutable P1 comparison.

## Recorded recovery and retained failures

An earlier unseeded fetch stopped at its 120-second bound after 120.037 seconds, with return code -9 and no observed surviving group. It earned no tip acceptance. A fresh P1-seeded route later fetched the exact tip once and matched five canonical commits and parents, all five nontruncated API tree rosters, and all 33 exact after-blobs. API JSON was comparison evidence; canonical Git objects were recovered and hashed separately.

The first strict fsck returned exit 8: error: HEAD points to something strange (refs/custody/main). The original driver and failure were preserved. A separate metadata step detached only private HEAD at literal P1; subsequent strict fsck passed with empty streams. No recovered object or scientific source was repaired. A second fresh P1-only repository restored the bundle and rechecked all declared objects with strict fsck. An empty repository rejected the absent prerequisite and still lacked the tip. Exact source-record and command-ledger hashes are in the manifest.

## Concise P1-seeded recovery recipe

Use a fresh bounded private directory, reviewed Git and explicit clean routing/configuration. Disable replacement objects, hooks, automatic maintenance and unapproved transports; retain command statuses and both raw streams. This recipe describes the recorded route and does not authorize execution.

1. Create a fresh empty-template bare repository. Seed only complete literal P1 from a verified accepted-main object source into refs/custody/main; verify that exact SHA and require no shallow, alternate or promisor routing.
2. Require the semantic tip to be absent before import. Check the bundle bytes, SHA-256, Git blob ID, header, sole declared prerequisite and exact advertised ref against the manifest. Verify the bundle in the P1-seeded database.
3. Import only refs/custody/semantic:refs/custody/semantic from the retained bundle. Require the exact tip/tree, five nonmain commits and parent chain; compare the five raw root trees and 33 historical blobs against their declared canonical object IDs, SHA-256 values and sizes.
4. If using the custody namespace, detach private HEAD at literal P1 with update-ref --no-deref; do not point HEAD symbolically outside refs/heads. Run strict full fsck and require exit zero with empty streams. Preserve a missing-prerequisite negative in a separate empty repository.

The native observations were same-host custody evidence. They do not prove source correctness, scientific novelty, hosted execution, independent human review or that every thin-delta base is reachable from the declared prerequisite alone.

## Publication and retirement boundary

At the recorded local recovery, remote-main archive retrieval and branch retirement were still pending. A later dated record must bind the containing accepted-main commit, exact bundle Git blob/SHA-256, verified P1 seed, fresh missing-tip baseline and recovered objects, without using the live historical branch as recovery input. Retirement also requires a fresh exact remote-tip and scoped worktree/process ownership check. This archive alone authorizes no deletion or global filesystem-closure claim.
