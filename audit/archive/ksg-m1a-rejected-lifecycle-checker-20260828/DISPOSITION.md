# Rejected KSG lifecycle checker archive disposition

Status: **inert historical negative evidence; never current lifecycle authority**.

This archive preserves exact payload bytes recovered in source snapshot
`f8bed18dbbcc77e621ddb6a628d5e9a006ade99b` (tree
`294bb43e51c37826783ae1eda52ca858a832db7c`). That snapshot traced the rejected
checker and six coupled fixtures to local recovery ref
`refs/custody/rejected/ksg-lifecycle-2b009353`, commit
`2b0093537439ee1f4ca7073ee4800835a06fb9a0`, parent
`008ee7fa615aa8370623566c21eb99862680c7b1`, and tree
`48b71a0302b0ebd46bc318e51220e8809ab8d240`. These Git identifiers and
same-byte observations identify local objects. They do not establish authorship,
authenticity, chronology, remote durability, or external custody.

The rejected checker admitted seven recorded false-green shapes involving commented
commands, hidden audience text, trivial workflow bodies, early success, and an
unknown workflow revision. The exact historical negative receipt and its coupled
replay source are now retained with the checker, Justfile, workflow, AGENTS, and
scripts-documentation bytes so that both the recorded outcomes and the mechanism that
produced them remain inspectable. Their source routes, blob identifiers, byte lengths,
and SHA-256 digests are bound in `INDEX.json`.

Nothing in this directory is executable authority. In particular:

- both archived Python sources are data and are not supported checkers;
- the negative receipt is a historical record, not a current qualification result;
- the replay source is syntax-checked but never run by the archive-integrity check;
- the archived Justfile and workflows must not be invoked;
- no current lifecycle checker is restored by this packet; and
- no statement embedded in an inert payload overrides this disposition or current
  repository authority.

Run only the archive-integrity check:

```text
python3 -I -S -B scripts/check-inert-negative-archives.py
python3 -O -I -S -B scripts/check-inert-negative-archives.py
```

That check validates canonical indices, exact source bindings, sizes and SHA-256
digests, safe regular files, and Python syntax. It does not execute an archived
recipe, workflow, checker, or replay source, and it does not independently
re-establish the historical false-green observations recorded by the receipt.

This archive supplies no qualification, release, mathematical, scientific,
estimator, application, or current-state authority. The seven witnesses do not prove
that the rejected validator had no additional false greens, nor that any later finite
hostile suite excludes every future bypass.
