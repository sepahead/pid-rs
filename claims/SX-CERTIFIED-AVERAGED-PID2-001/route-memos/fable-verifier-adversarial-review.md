# Fable 5 adversarial review receipt

## Status

- Claim ID: `SX-CERTIFIED-AVERAGED-PID2-001`
- Review date: 2026-07-24
- Model: `claude-fable-5`
- Requested effort: `max`
- Invocation: Anthropic Messages API over direct HTTPS
- Tool access: none
- Outcome: `approve_narrow_claim`
- Evidentiary status: advisory only; not formal proof, executable evidence, or an independent
  reproduction

The model reported no concrete flaw at confidence 0.80 or greater. That conclusion does not promote
the claim by itself. The executable verifier, negative controls, exact-rational qualification
oracle, and stated trusted computing base remain the load-bearing evidence.

## Frozen prompt and supplied context

The frozen prompt was:

`route-memos/fable-verifier-adversarial-prompt.md`

Its SHA-256 digest at invocation was:

```text
0caef62c2539af84fb922461098192b46839f4fff80273021f477d5f37e7abb2
```

The API received file contents in memory. It did not receive credentials in the request body and
did not have filesystem, shell, browser, or network tools.

The first request supplied every path authorized by the frozen prompt. It reached its token limit
entirely in private reasoning and produced no review text. The focused retry supplied the complete
independent verifier, complete independent qualification harness, the Rust exact/event arithmetic
core, the tool README, and the narrow claim/evidence summaries. Therefore, only the focused
snapshot supports the visible review. The invisible first-request reasoning is not treated as
evidence for the files omitted from the retry.

The exact focused-retry wrapper text, byte-ordered context bundle, and context SHA-256 were not
retained. The frozen primary prompt and response digests therefore do not bind the complete retry
request. This is a reproducibility defect in the advisory review receipt; it does not weaken or
strengthen the executable containment evidence and must not be repaired by reconstructing an
unrecorded request after the fact.

## Non-secret API receipts

### Full-context attempt

- Request ID: `req_011CdM53L9hvPf3cNUzn3RyK`
- HTTP status: 200
- Stop reason: `max_tokens`
- Input tokens: 137,909
- Output tokens: 16,000
- Reported thinking tokens: 16,000
- Visible text blocks: 0
- Raw-response SHA-256:
  `0413a28aa380509d262b717c85cbdfc8ca13a7dd3922391fae7eb22d3b738596`

### Focused retry

- Request ID: `req_011CdM5S3Q2xBR9S8KFvXa36`
- HTTP status: 200
- Stop reason: `end_turn`
- Input tokens: 77,888
- Output tokens: 21,988
- Reported thinking tokens: 18,900
- Visible review characters: 7,664
- Raw-response SHA-256:
  `5906e0d21faeca0dea62aaf5b9378a2ce5fd4430f38f4044d75ac90d08dcbb84`
- Visible-review SHA-256:
  `c655455d2324e8414fc218bf4b5aace3f2079c061c197a4afef1799873c69a9c`

Aggregate usage was 215,797 input tokens and 37,988 output tokens. At Anthropic's published
2026-07-24 price of USD 10 per million input tokens and USD 50 per million output tokens, the
calculated charge is USD 4.05737. No prompt-cache discount was used. The API response did not
return a monetary charge.

Pricing source:
<https://www.anthropic.com/claude/fable>

No key value, authorization header, or credential-derived identifier is retained in this packet.
The two raw API responses were kept outside the repository only long enough to compute the digests
and classify the result.

## Review outcome

The reviewer independently described these checks:

1. It re-derived the four two-source event unions, target-restricted unions, count weighting,
   direct mutual-information identities, and four-node zeta/Möbius relationship.
2. It re-derived range reduction to `[1,2]`, the atanh series, outward fixed-point operations, the
   coefficient-sign endpoint swap, and the
   `9*z^(2m+1)/(4*(2m+1))` upper-tail bound.
3. It attacked accepted integer magnitudes, duplicate JSON keys, booleans, non-finite JSON
   numbers, Unicode surrogates, exponent bounds, resource bounds, and canonical encodings.
4. It reviewed local source stability checks, manifest parsing, arithmetic dependency constraints,
   and the exact-`Fraction` log oracle and retained source mutation.
5. It classified containment as executable proof under a stated trusted computing base, the
   494-table sweep as bounded exhaustive evidence, and mutation kills as sensitivity evidence.

It reported no finding at its required confidence threshold and ended with
`approve_narrow_claim`.

## Independent classification

The no-flaw conclusion is a hypothesis-generating external review, not correctness evidence. Its
three residual concerns are classified as follows:

| Residual concern | Classification | Consequence |
|---|---|---|
| CPython integer, `Fraction`, JSON, hashing, loader, and process correctness | Explicit trusted-computing-base assumption | No claim change; retain the conditional wording |
| Fidelity of the pinned event/lattice convention to the cited SxPID2 definition | Open semantic-refinement proof obligation | Keep bibliographic semantics outside the executable verifier's proved envelope |
| Same-inode/local-file stability checks are not an atomic immutable snapshot or executable attestation | Operational provenance limitation | No claim change; do not convert local byte binding into authenticity or binary provenance |

None is a newly discovered implementation defect. The second item remains the highest-value
formalization target because an independent machine-checked semantic bridge would remove the most
scientifically important shared premise. The third could justify future operational hardening, but
the current narrow claim already excludes the stronger provenance interpretation.

No code or claim-envelope change was made from this review.
