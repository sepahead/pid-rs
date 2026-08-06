# Independent review of the C3 post-correction hosted receipt

- **Review finalized:** 6 August 2026 at `2026-08-06T21:02:16Z`
- **Exact subject:** `dbd3984adab1547dccd87690f2e5582b65fbd206`
- **Subject tree / direct parent:** `72b35f9a3ab7eb53878b25e8588806a8908ebb06` /
  `dc50e0afde843ad891ade6660e487083d6112038`
- **Machine receipt:** 27,880 bytes, SHA-256
  `412bd80d1908cb61bc9ce6af9a5be499c69fd04b18c21ddea38999fd82518932`
- **Human receipt:** 16,435 bytes, SHA-256
  `040629b3a7d8bc4fef57ebd02ad5a5b08adb2d3b03b995388656f2528ab99d9c`
- **Disposition:** three separately prompted exact-byte reviews returned **bounded GO**
- **Institutional independence:** not claimed
- **Scientific, security-clean, release, or publication credit:** none

This review binds only the exact receipt bytes and pre-existing subject above. Any receipt edit
invalidates all three dispositions. The reviews were independently derived but share a local
environment and retained inputs; they are not independent scientific experiments.

## Failure-diverse derivations

1. A typed-custody review reconstructed the Git graph, exact delta, workflow/checker/Just
   projections, hosted partitions, serialization, capture pairs, raw index, and acyclic claim
   graph.
2. A security-semantic review tried to falsify the incident boundary, partial-versus-complete
   archive wording, API-versus-log claims, predecessor partitioning, present-versus-historical
   custody, PDF no-churn statement, and cross-PID firewall.
3. An adversarial review independently rehashed Git objects and projections, recomputed all 13
   duplicate API pairs and hosted partitions, parsed the checksummed version-2 index, compared all
   596 entries with the subject tree, and attacked every N001--N018 repair and temporal claim.

All three found no contradiction, unsupported positive implication, or required repair. They
independently confirmed exact CI 45/45 and separate CodeQL 4/4 success at only `dbd3984…`; both
predecessor CI partitions as 43 successes, one failure, and one cancellation; 26 capture JSON
files totalling 1,075,330 bytes; the 2,516-byte manifest; all 13 byte-identical pairs; the fresh
71,800-byte subject index with 596 entries and tree `72b35f9…`; and the absence of either receipt
from the subject tree. The missing historical index remains missing and receives no continuity
credit.

The independently derived pair-only prospective custody is:

```text
tree:             88aa87177d7aa110edbe88195b8447d2e95b5189
JSON blob:        4ab9276e69b72e0b7b3fb6903af2a4c1cc11f8ee  mode 100644
Markdown blob:    46c62b79c4a2ae2d587301f5881fa6cb119eaa2b  mode 100644
sealed index:     /private/tmp/pid-rs-c3-receipt-pair-index.Ne68Ii/index
index bytes:      72056
index mode/links: 0400 / 1
index SHA-256:    24b9e48e3c4feabb1ae4f5393dcb616dbd60a985dc89c4083c3d192a260f8dd4
```

This is local supporting evidence only. The pair-only tree is not the eventual publication tree,
and local modes do not prevent privileged or same-UID mutation.

## N018 and rejected review history

N018 is repaired in structure and prose. `hosted_evidence_capture_boundary` is a top-level sibling
of both hosted-run records. Neither run contains a partial/archive/ZIP field, and the Markdown
explicitly denies attribution of the failed partial CodeQL archive attempt to either run. The
rejected 26,684-byte `c23e115c…` / 15,666-byte `61c3bc4b…` pair remains zero credit; its earlier
bounded GO does not transfer.

No earlier review result was discarded:

- **N014:** the 18,407-byte `fbf079bc…` / 10,402-byte `68845687…` and 21,446-byte
  `a8342386…` / 12,474-byte `95a04694…` requests were invalidated by edits before adjudication.
- **N015:** the 22,113-byte `118e6fd1…` / 13,083-byte `2374679c…` pair received NO-GO for the
  N013 custody contradiction and overbroad provider-state wording; all three additional
  narrowings are now enumerated.
- **N016:** the 22,324-byte `0d391668…` / 13,419-byte `d4521990…` pair received one bounded GO
  but lacked a second adjudication because earlier negatives were not retained.
- **N017:** the 24,896-byte `9f3f4eae…` / 14,452-byte `23b2e3c0…` pair received two NO-GOs for
  the missing N015 enumeration and false no-download wording.
- **N018:** the 26,684-byte `c23e115c…` / 15,666-byte `61c3bc4b…` pair received one GO and one
  NO-GO for ambiguous object containment.

Every rejected pair remains zero credit. N001--N013 remain in the reviewed receipts; absence of
an unlisted negative is not claimed.

## Local replay and post-freeze negatives

The isolated receipt validator passed normally and with `-O`. The certified-claim checker passed
normally and with `-O`, and its self-test rejected all 111 mutations in both modes. The documented
catalog, release-scope, review-evidence, and Markdown-math gates passed. Five explicit one-file
gitleaks scans, each using the repository config and `--redact=100`, found no leak across the five
publication paths; that is not a security-clean claim.

Three command-shape negatives receive no validation credit:

1. **C3-PUB-N001:** Catalog, release-scope, and review-evidence were first launched with
   `python3 -I`; all failed before validation because isolated mode excludes their sibling
   `json_schema_subset` module.
   Their documented entry points then passed. This does not weaken the receipt and certified-claim
   verifiers, which deliberately support isolated mode.
2. **C3-PUB-N002:** A `git diff --no-index --check /dev/null <new-file>` probe returned status 1
   because a new file differs from `/dev/null`; its empty diagnostic output was not credited as a
   completed staged-tree whitespace check.
3. **C3-PUB-N003:** The first gitleaks invocation supplied both receipt paths although
   `gitleaks dir` accepts one `[path]`. Its clean exit was not credited as an exact-pair scan. Five
   explicit one-file scans with `--config .gitleaks.toml --redact=100` then passed.

## Rejected full-tree candidate

The first frozen five-path tree, `16743e86c5158445c495e80d63c247cf7f1e5186`, received one
bounded GO and one exact-tree NO-GO. Its sealed index was 72,200 bytes, mode 0400, one link, at
SHA-256 `dc231850097c73791a61871f5241f675663b9f57ba1f0cd81801be187e0db020`.
The GO does not override the NO-GO, and the tree receives no commit or publication credit.

- **C3-PUB-N004:** an unchanged changelog bullet still said a successor hosted run “is required”
  immediately after the new bullet recorded exact successor run `31112402374`. The replacement
  uses historical tense and binds the exact run.
- **C3-PUB-N005:** the resume called N015--N018 four rejected frozen pairs even though N016 is
  typed as superseded. The replacement says three rejected and one superseded pair.
- **C3-PUB-N006:** a reviewer no-index diagnostic accidentally created an empty regular file at
  `/private/tmp/pid-rs-c3-no-write-sink`, verified it as zero bytes, and removed that exact file.
  It changed no repository, candidate, capture, sealed-index, Git, or remote bytes and receives no
  review-method credit.

## Acyclic publication boundary

This document can bind the receipt pair and pair-only prospective tree, but cannot contain the
identity of the larger tree that contains this document, the changelog, and durable resume update.
After every publication file is frozen, independent reviewers must inspect the exact full
alternate-index tree and its delta from live `origin/main`. That external observation may
authorize a commit, but no byte in the commit self-authenticates its resulting commit or tree. A
strict descendant or separately retained external observation is required to record them.

## Non-implications

This GO establishes no GitHub, runner, action, toolchain, operating-system, hardware, or network
authenticity and no log, SARIF, step, test-count, coverage, SBOM, artifact, alert, or extractor
content. It establishes no security cleanliness, credential noncompromise, complete containment,
credential rotation, provider-state nonmutation, remote durability, atomicity, or tamper-proof
storage.

Nothing transfers to KSG estimation, Ehrlich continuous shared-exclusions PID, categorical
Makkeh--Gutknecht--Wibral SxPID, Williams--Beer `I_min`, fitted quantized PID, heuristics, or
wrappers. No theorem, numerical result, statistical claim, PDF content, release readiness, or
downstream authorization is established here.
