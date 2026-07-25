# Opus 5 adversarial verifier review receipt

## Status

- Claim ID: `SX-CERTIFIED-AVERAGED-PID2-001`
- Review date: 2026-07-24
- Model: `claude-opus-5`
- Invocation: Anthropic Messages API over direct HTTPS
- Tool access: none
- Visible-review disposition: `approve_with_fixes`
- Evidentiary status: advisory only; not formal proof, executable evidence, independent
  reproduction, or source custody

The successful review found no defect that refutes the narrow conditional enclosure claim. It did
find two medium-severity independence and source-binding gaps and ten lower-severity evidence,
documentation, resource, and transport gaps. Every accepted fix is listed below. The review does
not replace the executable verifier, exact-rational logarithm qualification, mutation suite, or
the stated trusted computing base.

## Frozen prompts and supplied context

The frozen prompts are:

- `opus5-verifier-adversarial-prompt.md`, SHA-256
  `1a12352cad2895f2f666a0e62afce26a605a619ec7641bf4655cfac2c72cb4d4`;
- `opus5-verifier-adversarial-retry-prompt.md`, SHA-256
  `860210bb09bf384d234b60b3665eaa0938b131ad3816d6d44649bf1211b96791`.

The API received file contents in memory. It received no credential values and had no filesystem,
shell, browser, or network tools. Raw model reasoning is not retained or treated as evidence.

## Non-secret API receipts

### Full-context attempt

- Response ID: `msg_011CdMHNgqLQKLjAVJXAN6D8`
- HTTP status: 200
- Stop reason: `max_tokens`
- Input tokens: 184,377
- Output tokens: 64,000
- Reported thinking tokens: 64,000
- Visible review text: none
- Context bytes: 450,496
- Raw-response SHA-256: recorded only as prefix `c308e`
- Visible-extraction SHA-256: recorded only as prefix `01ba`
- Context SHA-256: recorded only as prefix `463e`

Only digest prefixes survived the transient receipt for this attempt. They are labeled as prefixes
and are not promoted to full digests. Because the response contained no visible review, this
attempt supplies usage and failure evidence only.

### Focused retry

- Response ID: `msg_011CdMK1ptRAQJPEfEX2pHqa`
- HTTP status: 200
- Stop reason: `end_turn`
- Input tokens: 169,212
- Output tokens: 80,906
- Reported thinking tokens: 74,008
- Context bytes: 414,117
- Raw-response SHA-256:
  `f6c029dac16a4826cd13157b510845794cd6358b7d5218120c794dc01287f5e8`
- Visible-review SHA-256:
  `5780c04817a453774aad7204a50913446fc9c92c5955e35f0c29e6dcde74f38d`
- Context SHA-256:
  `f477191d4d03ea3cb7b13cd3cfc4e7a5b0623d8ae8da2136af0e9006dc994ec2`

Only the focused retry supports the review findings below. The raw API response was retained
outside the repository only long enough to compute its digest and extract the visible findings.

## Positive re-derivations

The visible review independently:

1. reconstructed the two-source source and target-restricted events, the four-node order, and the
   integer Möbius transform;
2. checked the XOR example and direct mutual-information identities;
3. re-derived the rational range reduction, positive atanh series, exact tail bound, and the
   outward fixed-point operations, including negative coefficient endpoint reversal;
4. checked the separately generated `ln(2)` enclosure and subset-containment acceptance rule;
5. confirmed that strict complete-state uniqueness justifies the keyed target
   inclusion--exclusion shortcut; and
6. classified the direct-MI route as non-tautological evidence while classifying `ZM=I` and zeta
   reconstruction as arithmetic self-consistency.

## Findings and accepted corrections

| ID | Finding | Disposition |
|---|---|---|
| F1 | The exhaustive verifier reused the same target-restricted inclusion--exclusion shortcut as the implementation. Replacing the shared target-union count by the maximum branch-target count survived internal checks and XOR. | Fixed. The harness now directly scans rows for all 5,928 cumulative event expressions and kills the retained source mutation. |
| F2 | A rehashed Cargo `[patch]` or source substitution could bypass the intended locked arithmetic source binding. | Fixed. The verifier rejects `[patch]` and `[replace]`, requires the empty standalone workspace table, and pins registry source and checksum for Rug and `gmp-mpfr-sys`. |
| F3 | The mutation corpus lacked the smallest positive interval collapsed to its own downward-rounded lower endpoint. | Fixed. That containment mutation is now a named killed case. |
| F4 | `SourceFileLoader` could consult bytecode-cache behavior rather than prove execution of the exact reviewed source bytes. | Fixed. The harness compiles and executes the exact loaded bytes directly. |
| F5 | Standard output was written without an explicit flush, so a closed pipe could replace the intended exit status during interpreter shutdown. | Fixed. One canonical document is explicitly written and flushed; a transport failure returns status 1 and the closed-output control passes without traceback. |
| F6 | `ZM=I` plus zeta reconstruction is algebraic self-consistency once the matrices are pinned; it is not an independent semantic oracle. | Fixed in the README, claim packet, and assurance paper. Direct row scans and direct-MI formulas carry the independent semantic checks. |
| F7 | The 4,096-row input limit was described as though every such table could be processed, while the cumulative-term ceiling rejects generic tables much earlier. | Fixed. It is now a structural maximum; the retained growing-support witness rejects at 410 rows after transiently reaching 1,640 terms. |
| F8 | The prose mutation inventory did not match the static suite's unsafe-surface coverage. | Fixed. An explicit unsafe-function mutation was added and all inventories now state 34 static mutations. |
| F9 | One structural-evidence count was a literal rather than a mechanically measured result. | Fixed. The harness measures and reports the counts it checks. |
| F10 | The target inclusion--exclusion formula silently depended on complete-state uniqueness. | Fixed. The prerequisite is documented at the input contract and reconstruction step. |
| F11 | Invocation through a symlink could bind a path spelling rather than the real executed source. | Fixed. Source binding uses `realpath`; a symlinked invocation is a retained passing control. |
| F12 | Resource bounds constrain memory-shaped objects and iteration schedules, not execution time; event extraction is quadratic in support rows. | Fixed. The README and assurance paper state the quadratic scan and make no latency, throughput, or denial-of-service-resistance claim. |

## Post-fix evidence

After these changes, the independent qualification:

- reconstructs 11,856 coordinates and 1,482 direct-MI identities over 494 exhaustive tables;
- independently scans 5,928 cumulative event expressions;
- proves 72 live-certificate containments;
- checks 975 exact-rational logarithm enclosures;
- kills 21 semantic mutations, one fixed-point source mutation, one event-extraction source
  mutation, and four cross-artifact binding adversaries;
- rejects six structural adversaries for their intended reasons;
- passes two transport/invocation controls; and
- produces byte-identical CLI output under varied Python hash seeds, both normally and under
  `python3 -O`.

## Residual boundary

The review leaves the declared trusted computing base intact: CPython integer and `Fraction`
semantics, JSON and SHA-256 implementations, the reviewed verifier and logarithm proof, local
filesystem/operating-system behavior, and the scientific transcription from the cited SxPID
definition remain assumptions. The source checks are not an atomic filesystem snapshot,
transparency log, binary attestation, native-library proof, or executable provenance proof.
