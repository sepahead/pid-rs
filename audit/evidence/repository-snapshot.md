# pid-rs 1.0 repository snapshot

This is a human-readable rendering of `repository-snapshot.json`. It records the exact
moving-branch cut used to begin the 1.0 audit. Only `pid-rs` core is claimed; all
downstream repositories are explicitly `not_claimed` and are therefore non-blocking.

Snapshot SHA-256: `b57e506bbf30183c29bea4ff062a3711a3e471400dd91ebbdd8f787152af4b56`

| Repository | Branch | Commit | Tree | Claim status | Clean | Head tags | Releases |
|---|---|---|---|---|---:|---|---:|
| pid-rs | `main` | `3fbb87f14014e5f3704209d7fcc8f4e55f709c10` | `be527883b314d4be936612d1381925d4b06b5d07` | `claimed_core` | yes | none | 0 |
| prisoma | `main` | `0968128062f30da5c04f3f31c23f6ce8e0d95d36` | `d7ee5763cbdc5906c91ff4c82c5fc9a124c6aa84` | `not_claimed` | yes | none | 0 |
| galadriel | `main` | `017c615e3976eae69c3115aeeb74e9fdb50ec15d` | `bc47c9b1053ade871095e5529136145432683c82` | `not_claimed` | yes | none | 0 |
| crebain | `main` | `4c311900ade5668200a48d56fb191be1916b884a` | `55eb96da6d98e65f89b6b84fbb81ee8f53f6cde0` | `not_claimed` | yes | none | 0 |
| haldir | `main` | `1c8862ec93999506c285c0777c82394ebe8ab409` | `357406073f1f117c71eaaa5c910699aa220724e7` | `not_claimed` | yes | none | 0 |

## Interpretation

This snapshot proves repository identity and cleanliness only. It does not prove
mathematical correctness, estimator validity, consumer compatibility, application
validity, operational safety, or publication. A changed `pid-rs` commit requires new
candidate evidence; it does not rewrite this historical audit cut.
