# Public carrier-digest scanner evidence

This packet projects two initial local reviews and the later CI supplement. It retains the
rejected policy, accepted policy, compact public carrier preimage, decisive rejected-context
results, redacted history metadata, and exact route/lens dispositions. It does not claim
external reviewer custody, complete repository secrecy, or mathematical validation.

Use [review A](review-a.md), [review B](review-b.md), and the [CI supplement](review-b-supplement.md)
for the recorded judgments. [Route and lens dispositions](review-dispositions.md) retains the
exact ten-route and fifty-lens tables. They are review questions with outcomes, not sixty proofs.

[MANIFEST.json](MANIFEST.json) binds the actual public files. Each private original identity has
a corresponding public artifact and an explicit transformation or omission description. A raw
private hash is comparison metadata. It does not make omitted local bytes publicly retrievable
and must not be presented as complete custody. Original machine locators are replaced by role
labels. Contact and commit-message fields are omitted from scanner-report projections; commit,
path, rule, source coordinates, and redacted finding data are retained.

The four decisive inputs are losslessly reconstructed from [carrier-preimage.json](carrier-preimage.json)
and the two templates in [replay.py](replay.py). Preparation compared their exact bytes with
retained input files and recorded hashes. [Rejected results](rejected-v1-cases.json) retains
baseline, rejected-version, and accepted-version outcomes. The full set of temporary fixture
files is omitted. [ci-inline.py](ci-inline.py) retains the exact complete inline CI program, with
its public values assembled in code; [matrix results](matrix-results.json) retains every accepted
case's recorded outcome. A source hash without this reconstruction is not a source-byte archive.

The original private replay command block and unrelated session coordination were removed from
review A. The complete review judgments and all route/lens rows remain. Historical source blobs
are identified by public Git object and commit/path locators in [provenance](provenance.json),
but are not duplicated here. [History results](history-results.json) distinguishes 269 reachable
Git commits from 268 scanner-counted commits and records both independent baseline/candidate
comparisons. A new ref set or later scan is a new observation.

The proposed [CI patch](ci.yml.patch) is an exact retained diff. Its historical full-file preimage
was CI at commit `91d5dbb13130ba89a7c8f2c09b2925fe15286fc5`; it is not intended to be reapplied to
an already repaired checkout. The archived inline is used by an explicit local executable-path
adapter. Run from this packet directory with a reviewed Gitleaks 8.30.1 executable:

```text
python3 -I -S -B replay.py --gitleaks <absolute-reviewed-executable> --decisive
python3 -I -S -B replay.py --gitleaks <absolute-reviewed-executable> --inline
python3 -I -S -B -O replay.py --gitleaks <absolute-reviewed-executable> --inline
```

These commands use fresh temporary directories and return their results. They do not edit the
repository or change history. The local adapter is not GitHub Actions. Hosted acceptance and
mainline ancestry remain separate gates.

[Hosted failure excerpts](hosted-failure-excerpts.json) retains exact selected lines from the
failed PDF download and secret scan. Full logs are omitted. The manifest binds the public
excerpt bytes and records the raw local log identities separately.

[Inline extraction](inline-extraction.json) records twelve blank-line bytes omitted by review B
and retained by the coordinator and public program. The parsed Python ASTs match. The original
review keeps its original extraction hash. The hosted temporary executable literal in the
archived program is part of the exact CI command, not a local machine locator.
